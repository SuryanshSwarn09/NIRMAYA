# Technical Audit Report: backend/app/services/appointment.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/appointment.py` provides the clinical appointment lifecycle management service for NIRMAYA, aligned with the HL7 FHIR R4 Appointment standard. It coordinates slot reservations, enforces row-level concurrency locking (`with_for_update()`) on `DoctorSlot` records, manages status transitions (`SCHEDULED`, `COMPLETED`, `CANCELLED`, `NO_SHOW`), and automatically replenishes cancelled slots. The audit identified an **S1** double-booking vulnerability for walk-in appointments (where non-slot bookings lack overlap detection against existing commitments) and an **S2** status transition flaw where state updates lack Finite State Machine (FSM) enforcement.

### Architectural Roster
- **Module Name:** `backend/app/services/appointment.py`
- **Primary Responsibility:** Appointment booking, slot locking, concurrency conflict prevention, status transitions, and appointment querying.
- **Upstream Dependencies:**
  - `sqlalchemy.ext.asyncio.AsyncSession`
  - `app.core.exceptions.AppException`, `ConflictException`, `EntityNotFoundException`
  - `app.models.appointment.Appointment`, `DoctorSlot`
  - `app.models.doctor.DoctorProfile`
  - `app.models.patient.PatientProfile`
  - `app.models.enums.AppointmentStatus`, `SlotStatus`
  - `app.services.slot_engine.sweep_expired_holds`
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/appointments.py`
  - OPD Queue and Express Consultation workflows
- **Exported Symbols:**
  - `book_appointment`
  - `get_appointment_by_id`
  - `list_appointments`
  - `update_appointment_status`

```
+-----------------------------------------------------------------------------------+
|                        Clinical Appointment Booking Engine                        |
|                                                                                   |
|  [Patient / Receptionist]                                                         |
|          |                                                                        |
|          v                                                                        |
|  [book_appointment(patient_id, payload)]                                          |
|          |-- 1. Validate PatientProfile & DoctorProfile exist                     |
|          |-- 2. If slot_id provided:                                              |
|          |       |- sweep_expired_holds(slot_id)                                  |
|          |       |- SELECT DoctorSlot ... WITH FOR UPDATE (Exclusive Lock)        |
|          |       |- Check BOOKED, BLOCKED, HELD status & Patient ID               |
|          |       |- Transition slot to BOOKED                                     |
|          |-- 3. If slot_id NOT provided (Walk-in):                                |
|          |       |- Validate scheduled_start and scheduled_end                    |
|          |       |- [VULN: Missing overlap check against doctor schedule!]        |
|          |-- 4. INSERT INTO appointments & commit transaction                     |
|          +--> Catch IntegrityError -> ConflictException (Concurrency guard)       |
|                                                                                   |
|  [Lifecycle Updates: update_appointment_status]                                   |
|          |-- If CANCELLED -> Automatically restore slot to AVAILABLE              |
|          +--> [VULN: Allows arbitrary invalid state transitions e.g. DONE->SCHED] |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

This module governs how patients schedule consultations with healthcare providers:

1. **Slot-Based Appointment Booking (`book_appointment`):** When booking a formal slot, the service verifies that the patient and doctor exist. It triggers `sweep_expired_holds` to release any stale temporary holds. Crucially, it queries the `DoctorSlot` using `.with_for_update()`, acquiring an exclusive row-level database lock. It verifies that the slot belongs to the requested doctor and is neither already booked, blocked, nor held by another citizen. It sets the slot status to `BOOKED` and commits the new `Appointment`.
2. **Walk-In / Ad-Hoc Booking:** If no slot ID is supplied (e.g. for emergency walk-ins), the service reads `scheduled_start` and `scheduled_end` directly from the payload.
3. **Appointment Retrieval & Filtering (`list_appointments`):** Supports filtering appointments by patient, doctor, status, and start date intervals with total counts and pagination. Joins doctor, patient, and slot details using SQLAlchemy's async `selectinload`.
4. **Status Lifecycle Transitions (`update_appointment_status`):** Updates the appointment status (e.g. `COMPLETED`, `CANCELLED`). If cancelled, it re-queries the associated `DoctorSlot` under an exclusive lock and resets its status to `AVAILABLE`, clearing any hold metadata so other patients can immediately claim it.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Concurrency Specifications
- **ACID Double-Booking Prevention:** A single `DoctorSlot` must never be assigned to more than one active appointment. This is guarded via `with_for_update()` and `IntegrityError` rollback.
- **Slot Replenishment Invariant:** An appointment cancelled prior to occurrence must replenish the associated slot to `AVAILABLE`.

### Flaws & Vulnerabilities
- **Walk-In Schedule Overlap Blindspot:** When booking without a `slot_id` (lines 145–154), the service verifies that `scheduled_start` and `scheduled_end` are non-null, but performs *zero query checks* against existing appointments for that doctor. Multiple walk-in appointments can be booked at the exact same hour and minute for the same doctor, leading to overlapping clinic schedules and doctor over-subscription.
- **Missing Finite State Machine (FSM) Validation:** `update_appointment_status` permits any arbitrary status change. For example, a consultation already marked `COMPLETED` can be reverted to `SCHEDULED`, or a `CANCELLED` appointment can be marked `COMPLETED` without re-booking a slot.
- **SQLAlchemy Boolean Filter:** Line 224 passes `True` as a filter expression (`and_(*filters) if filters else True`). Certain database drivers emit deprecation warnings or unoptimized query plans for raw boolean values in `WHERE` clauses.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-APP-F01` | **S1** | `[QUAL]` | `appointment.py:145-154` | Ad-hoc walk-in bookings without slots bypass overlap collision detection, allowing overlapping double-bookings for doctors. |
| `BE-SVC-APP-F02` | **S2** | `[QUAL]` | `appointment.py:250-286` | Status transition lacks Finite State Machine validation, permitting illegal lifecycle jumps (e.g., COMPLETED to SCHEDULED). |
| `BE-SVC-APP-F03` | **S2** | `[QUAL]` | `appointment.py:250-290` | Lack of atomic rescheduling functionality prevents moving an existing appointment to a new slot. |
| `BE-SVC-APP-F04` | **S3** | `[QUAL]` | `appointment.py:224` | `where_clause = and_(*filters) if filters else True` uses raw boolean `True` in SQLAlchemy `where()`, risking query optimizer anomalies. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Walk-In Overlap Detection & FSM Guard (`BE-SVC-APP-F01`, `BE-SVC-APP-F02`)

```diff
--- a/backend/app/services/appointment.py
+++ b/backend/app/services/appointment.py
@@ -150,6 +150,22 @@ async def book_appointment(
                 error_code="MISSING_SCHEDULE_TIMES",
                 status_code=400,
             )
+        # Verify no overlapping appointments exist for this doctor
+        overlap_stmt = select(Appointment).where(
+            Appointment.doctor_id == payload.doctor_id,
+            Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]),
+            Appointment.scheduled_start < payload.scheduled_end,
+            Appointment.scheduled_end > payload.scheduled_start,
+        )
+        existing_overlap = await db.scalar(overlap_stmt)
+        if existing_overlap:
+            raise ConflictException(
+                message="Doctor already has an overlapping appointment during this time window",
+                error_code="DOCTOR_SCHEDULE_CONFLICT",
+            )
         scheduled_start = payload.scheduled_start
         scheduled_end = payload.scheduled_end
```
