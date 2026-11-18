# Audit Report: `backend/app/models/appointment.py`

**Path**: `backend/app/models/appointment.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 223 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Clinical appointment scheduling and doctor slot models aligned with HL7 FHIR R4 Schedule, Slot, and Appointment · Risk: **S3 (Low Risk)** · Verdict: **READY-WITH-FIXES** · Exceptional concurrency safety via unique constraints; `teleconsultation_url` string length constraint is somewhat tight for signed URLs.

---

## Layer B — Explain It
- **What problem this file solves**: Manages clinician consultation availability, temporary patient reservation holds, and confirmed clinical appointments linking patients, doctors, and diagnostic orders.
- **How it works step by step**:
  1. `DoctorSlot` represents a discrete block of time (`start_time` to `end_time`) for a doctor.
  2. Guarantees no double-booking via `UniqueConstraint("doctor_id", "start_time")`.
  3. Supports temporary locking during checkout via `held_until` and `held_by_patient_id`.
  4. `Appointment` records confirmed or scheduled encounters, linked 1-to-1 with a slot via `uq_appointment_slot_id`.
  5. Cascades access to longitudinal clinical records (`conditions`, `observations`, `soap_notes`, `prescriptions`).
- **Concepts & patterns used**:
  - *Conflict-Free Concurrency*: Enforces mathematical uniqueness at the relational level to prevent race-condition overbooking.
  - *Slot Hold Lifecycle*: Manages temporary reservations with TTL before confirming payment or booking.
- **Key lines to read first**:
  - `backend/app/models/appointment.py:23-81`: `DoctorSlot` model and unique constraint.
  - `backend/app/models/appointment.py:107-141`: `Appointment` model and foreign key bindings.
  - `backend/app/models/appointment.py:194-217`: Clinical relationship cascades.
- **How to change it safely**:
  - Ensure status changes follow the FHIR lifecycle (`SCHEDULED` $\rightarrow$ `CONFIRMED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED`).

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `sqlalchemy.*`, `app.db.base.Base`, `app.models.enums.*`.
   - **Imported by**: `backend/app/api/v1/endpoints/appointments.py`, `backend/app/services/slot_engine.py`, `backend/app/fhir/transformers.py`.
   - **Public surface**: `DoctorSlot`, `Appointment`.

2. **Security [SEC]**:
   - Database-level concurrency guard prevents race-condition double-booking under high request loads.
   - Foreign key cascading: Deleting a patient or doctor cascades cleanly to appointments (`CASCADE`), while canceling an appointment detaches the slot without deleting it (`SET NULL`).

3. **Code quality [QUAL]**:
   - High-quality SQLAlchemy 2.0 type mapping with `Mapped[...]`.
   - Clear string representations (`__repr__`) for logging and debugging.

4. **AI-generated smells [QUAL]**:
   - None observed.

5. **Performance [PERF]**:
   - `start_time` is indexed, but `end_time` is not. Adding a composite index on `(doctor_id, start_time, end_time)` optimizes slot availability queries.

6. **Error handling & edge cases**:
   - Slot ID uniqueness constraint ensures an already-booked slot cannot be attached to a second appointment.

7. **Doc accuracy [DOC]**:
   - Strictly conforms to Month 1 and Month 2 roadmap specifications.

8. **Tests**:
   - Tested in `backend/tests/test_appointments.py` and `backend/tests/test_slots.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-APT-F01** | **S3** | `[PERF]` | `40-48` | Missing composite index on slot start and end boundaries | `start_time` indexed alone; `end_time` unindexed | Add `Index("idx_doctor_slot_window", "doctor_id", "start_time", "end_time")` |
| **BE-APT-F02** | **S3** | `[QUAL]` | `176-179` | String(500) limit for teleconsultation URL may truncate signed tokens | `teleconsultation_url = mapped_column(String(500))` | Switch to `Text` column |
| **BE-APT-F03** | **S4** | `[QUAL]` | `80` | Unique constraint guards exact start time, not partial overlapping spans | `UniqueConstraint("doctor_id", "start_time")` | Rely on `slot_engine` or PostgreSQL range exclude constraint |

---

## Suggested Patches (NOT Applied)

### Patch BE-APT-P01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/models/appointment.py
+++ b/backend/app/models/appointment.py
@@ -176,3 +176,3 @@ class Appointment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     teleconsultation_url: Mapped[Optional[str]] = mapped_column(
-        String(500),
+        Text,
         nullable=True,
     )
```

---

## Verdict
**READY-WITH-FIXES** — Production-grade appointment and scheduling models with excellent concurrency safeguards.
