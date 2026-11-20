# Principal Software Engineering Audit: backend/app/services/slot_engine.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/slot_engine.py` implements the core clinical appointment availability and reservation engine for the NIRMAYA platform. It provides deterministic, conflict-free doctor consultation slot computation across specified date ranges, accounting for daily practice hours, mid-day break intervals, teleconsultation flags, and existing bookings. Additionally, it implements pessimistic concurrency control (`SELECT ... FOR UPDATE`) for holding and releasing consultation slots with time-based TTL expiration (`held_until`). Key architectural vulnerabilities include unbounded slot generation ranges enabling database connection starvation and OOM risks, in-memory client-side date filtering in `get_doctor_slots` that loads all historical doctor slots into Python memory, and lack of distributed lock protection during expired hold sweep routines.

### System Topology & Architectural Invariants
```
                  +-------------------------------------------------+
                  |     Doctor Scheduling & Patient Booking API     |
                  |     (app.api.v1.endpoints.appointment / slots)  |
                  +-----------------------+-------------------------+
                                          |
                                          v
                  +-------------------------------------------------+
                  |           SlotEngine (slot_engine.py)           |
                  +-----------------------+-------------------------+
                                          |
                      +-------------------+-------------------+
                      |                                       |
                      v                                       v
         +-------------------------+             +-------------------------+
         | generate_slots_for_     |             | hold_slot() /           |
         | doctor()                |             | release_slot_hold()     |
         | - Verifies DoctorProfile|             | - SELECT FOR UPDATE     |
         | - Iterates date range   |             | - Atomic TTL evaluation |
         | - Skips break bounds    |             | - Sweeps expired holds  |
         | - Batch db.add_all()    |             +-------------------------+
         +-------------------------+                          |
                      |                                       v
                      v                          +-------------------------+
         +-------------------------+             | sweep_expired_holds()   |
         | get_doctor_slots()      |             | - Reverts HELD ->       |
         | - Fetches doctor slots  |             |   AVAILABLE if expired  |
         | - In-memory date filter |             +-------------------------+
         +-------------------------+
```

### Import / Export Surface Map
- **Upstream Dependencies:**
  - `datetime.date`, `datetime.datetime`, `datetime.time`, `datetime.timedelta`, `datetime.timezone`: Temporal range calculations and UTC normalization.
  - `typing.List`, `typing.Optional`, `typing.Set`: Type annotations.
  - `sqlalchemy.and_`, `sqlalchemy.select`: Core query builders.
  - `sqlalchemy.ext.asyncio.AsyncSession`: Asynchronous database interaction.
  - `app.core.exceptions`: `ConflictException`, `EntityNotFoundException`, `PermissionDeniedException`.
  - `app.models.appointment`: `DoctorSlot`.
  - `app.models.doctor`: `DoctorProfile`.
  - `app.models.enums`: `SlotStatus`.
  - `app.schemas.appointment`: `DoctorSlotResponse`, `SlotGenerateRequest`, `SlotGenerateResult`.
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/appointment.py`: Doctor slot generation and patient booking workflows.
- **Exported Interface:**
  - `_normalize_utc(dt)`: Normalizes datetimes to UTC microsecond-zero timestamps.
  - `generate_slots_for_doctor(db, request)`: Idempotent batch generation of consultation slots.
  - `sweep_expired_holds(db, slot_id)`: Reverts expired held slots back to available.
  - `get_doctor_slots(db, doctor_id, ...)`: Retrieves slots with optional filtering.
  - `get_slot_by_id(db, slot_id)`: Single primary key slot lookup.
  - `hold_slot(db, slot_id, patient_id, duration_minutes)`: Atomically reserves a slot using row locks.
  - `release_slot_hold(db, slot_id, patient_id, force_admin)`: Releases a held slot.

---

## Layer B: Plain-Language Developer Walkthrough

The `slot_engine.py` module orchestrates how doctors publish their consultation hours and how patients temporarily hold slots during checkout:
1. **Slot Generation (`generate_slots_for_doctor`)**: A doctor or clinic admin requests slot generation across a date range (`start_date` to `end_date`), specifying slot duration (e.g., 15 minutes), daily start/end hours (e.g., 09:00 to 17:00), and an optional break window (e.g., 13:00 to 14:00). The engine first validates that the doctor profile exists. It queries all existing slot start times for that doctor into a memory `Set[datetime]` to guarantee idempotency. It then steps through each day and generates prospective start and end intervals. If an interval overlaps with the designated break window or already exists in the database, it is skipped. The remaining non-overlapping slots are added to the session via `db.add_all()` and committed.
2. **Expired Hold Sweeping (`sweep_expired_holds`)**: Before availability is returned or a new hold is placed, the engine queries slots whose status is `HELD` and whose `held_until` timestamp has elapsed in UTC. It resets their status to `AVAILABLE` and clears patient metadata.
3. **Pessimistic Hold Locks (`hold_slot`)**: When a patient attempts to reserve a slot, the engine executes `SELECT ... FOR UPDATE` on the slot row. This blocks concurrent checkout attempts. If the slot is already `BOOKED` or held by another patient with an active TTL, a `ConflictException` is raised. Otherwise, the slot is marked `HELD` with a 10-minute expiration window.
4. **Hold Release (`release_slot_hold`)**: A patient abandoning checkout or an administrator can explicitly release the hold, resetting the row back to `AVAILABLE`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Unbounded Date Range in Slot Generation
In `generate_slots_for_doctor` (lines 37-67), the date range calculation:
```python
delta_days = (request.end_date - request.start_date).days + 1
```
has no maximum cap validation. If a malicious client sends `start_date="2026-01-01"` and `end_date="2036-01-01"`, `delta_days` becomes 3,652. With 15-minute slots over 8-hour days, the nested loop generates over 116,000 ORM objects in Python memory. This triggers database connection starvation, out-of-memory worker crashes, and extended table locking.

### Invariant 2: In-Memory Client-Side Slot Filtering
In `get_doctor_slots` (lines 173-211), the SQL query does not filter by `start_time` or `status` in the database:
```python
stmt = (
    select(DoctorSlot)
    .where(DoctorSlot.doctor_id == doctor_id)
    .order_by(DoctorSlot.start_time.asc())
)
all_slots = list((await db.scalars(stmt)).all())
```
All historical slots across years of clinical practice are pulled over the wire into Python memory, where an in-memory `for` loop filters by `target_date`, `start_date`, `end_date`, and `status`. As the practice accumulates thousands of historical slots, this query degrades from $O(1)$ indexed range lookups to an unbounded table scan and memory hog.

### Invariant 3: Single-Node Hold Sweeper vs. Redis Distributed Coordination
`sweep_expired_holds` (lines 140-170) operates purely at the relational database level using standard transactions without a distributed lock (e.g., Redlock). Under horizontal scaling with multiple FastAPI workers, concurrent requests execute simultaneous sweep queries, creating database row lock contention.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SVC-SLT-F01` | **S1** | `[SEC]` / `[PERF]` | `slot_engine.py:62-67` | Unbounded `delta_days` in `generate_slots_for_doctor` allows requesting multi-year slot generation, causing memory exhaustion and worker DoS. |
| `BE-SVC-SLT-F02` | **S1** | `[PERF]` | `slot_engine.py:186-210` | `get_doctor_slots` fetches all lifetime doctor slots into Python memory and filters dates in-memory rather than utilizing SQL `WHERE` clauses. |
| `BE-SVC-SLT-F03` | **S2** | `[PERF]` | `slot_engine.py:140-170` | Uncoordinated `sweep_expired_holds` execution on every availability read triggers excessive database write locks under high concurrent read volume. |
| `BE-SVC-SLT-F04` | **S2** | `[QUAL]` | `slot_engine.py:227` | `duration_minutes` parameter in `hold_slot` lacks upper bound validation; client can request hours of hold time, starving other patients. |
| `BE-SVC-SLT-F05` | **S3** | `[PERF]` | `slot_engine.py:128-129` | Serial `db.refresh(slot)` in loop over all newly generated slots causes $N$ roundtrips after single batch insert. |
| `BE-SVC-SLT-F06` | **S4** | `[DOC]` | `slot_engine.py:1-5` | Missing documentation regarding Cal.com parity and timezone handling for Indian Standard Time (IST / UTC+05:30). |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-SLT-F01-F02`: Date Range Capping & Push-Down SQL Filtering
```diff
--- a/backend/app/services/slot_engine.py
+++ b/backend/app/services/slot_engine.py
@@ -62,6 +62,11 @@
     current_date: date = request.start_date
     delta_days = (request.end_date - request.start_date).days + 1
 
+    if delta_days > 90:
+        raise ConflictException(
+            message="Slot generation range cannot exceed 90 days in a single batch",
+            error_code="SLOT_RANGE_EXCEEDED",
+        )
     slot_delta = timedelta(minutes=request.slot_duration_minutes)
 
     for _ in range(delta_days):
@@ -186,10 +191,24 @@
     stmt = (
         select(DoctorSlot)
         .where(DoctorSlot.doctor_id == doctor_id)
-        .order_by(DoctorSlot.start_time.asc())
     )
+    if target_date:
+        start_dt = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
+        end_dt = datetime.combine(target_date, time.max, tzinfo=timezone.utc)
+        stmt = stmt.where(and_(DoctorSlot.start_time >= start_dt, DoctorSlot.start_time <= end_dt))
+    if start_date:
+        stmt = stmt.where(DoctorSlot.start_time >= datetime.combine(start_date, time.min, tzinfo=timezone.utc))
+    if end_date:
+        stmt = stmt.where(DoctorSlot.start_time <= datetime.combine(end_date, time.max, tzinfo=timezone.utc))
+    if status:
+        stmt = stmt.where(DoctorSlot.status == status)
+    if is_teleconsult is not None:
+        stmt = stmt.where(DoctorSlot.is_teleconsult == is_teleconsult)
+
+    stmt = stmt.order_by(DoctorSlot.start_time.asc())
+    return list((await db.scalars(stmt)).all())
```
