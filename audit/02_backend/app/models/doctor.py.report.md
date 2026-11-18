# Audit Report: backend/app/models/doctor.py

**Path:** `backend/app/models/doctor.py` | **Layer:** Backend (ORM Models) | **Language:** Python 3.12 (SQLAlchemy 2.0) | **LOC:** 150 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Relational persistence model for healthcare practitioners, capturing licensing credentials, medical specialties, consultation parameters, and ABDM Healthcare Professional Registry (HPR) identifiers.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `DoctorProfile.appointments` specifies `cascade="all, delete-orphan"`, which will wipe out patients' clinical consultation history if a doctor's profile is deleted in SQLAlchemy, directly contradicting the underlying DB schema (`ondelete="SET NULL"`).

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
To operate a clinical consultation network, the system needs a comprehensive profile for medical practitioners that links their core authentication identity (`User`) with regulatory credentials (state medical council registration, medical specialty, qualifications) and operational booking preferences (consultation fees, slot definitions, teleconsult availability).

### How it works, step by step
1. `DoctorProfile` links 1-to-1 to a record in `User` via `user_id`.
2. It enforces uniqueness on `registration_number` and stores the issuing `medical_council`.
3. Clinical classification is stored in `specialty` via `MedicalSpecialty` enum.
4. It captures consultation logistics: `consultation_fee`, `hospital_affiliation`, and `is_available_for_teleconsult`.
5. It integrates with India's Ayushman Bharat Digital Mission via the unique `hpr_id` (Healthcare Professional Registry ID).
6. It maintains bidirectional relationships to schedule slots, appointments, diagnosed conditions, observations, SOAP notes, diagnostic orders/reports, and medication prescriptions.

### Concepts and patterns used
- *1-to-1 Profile Extension Pattern:* Segregating authentication credentials (`User`) from clinical credentials (`DoctorProfile`).
- *National Registry Integration:* Supporting ABDM HPR identification.
- *Domain Hub Pattern:* Acting as the clinical authority root for encounters, prescriptions, and notes.

### Key lines to read first
- `doctor.py:19-30`: `DoctorProfile` definition and 1-to-1 linkage to `user.id`.
- `doctor.py:33-43`: Regulatory licensing fields (`registration_number`, `medical_council`).
- `doctor.py:81-87`: ABDM `hpr_id` field.
- `doctor.py:103-107`: Dangerous `cascade="all, delete-orphan"` on `appointments`.

### How to change it safely
When modifying fields, ensure that any changes to `specialty` stay in sync with `app.models.enums.MedicalSpecialty`. Do not alter the unique constraint on `registration_number` or `user_id` as they prevent duplicate provider accounts.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `typing` (TYPE_CHECKING, List, Optional), `sqlalchemy` (Boolean, Enum, ForeignKey, Integer, String, Text), `sqlalchemy.orm` (Mapped, mapped_column, relationship), `app.db.base` (Base, TimestampMixin, UUIDPrimaryKeyMixin), `app.models.enums` (MedicalSpecialty).
- **Imported By:** `backend/app/models/__init__.py`, `backend/app/models/appointment.py`, `backend/app/models/condition.py`, `backend/app/models/diagnostic.py`, `backend/app/models/soap_note.py`, `backend/app/models/medication_request.py`, `backend/app/services/doctor_service.py`.
- **Public Surface:** Class `DoctorProfile` (table `doctor_profile`).

### 2. Security [SEC]
- **Clinical Data Purge Risk (CWE-404):** `DoctorProfile.appointments` (lines 103-107) has `cascade="all, delete-orphan"`. If a doctor profile is deleted through SQLAlchemy session, all patient appointment encounters with that doctor are deleted as orphans. In contrast, `appointment.py:46` correctly specifies `ondelete="SET NULL"`. Encounter histories are critical medical evidence and must never be cascade deleted (`BE-DOC-F01`).
- **Missing ABDM HPR Verification Status:** While `hpr_id` is stored, there is no corresponding `hpr_verified: Mapped[bool]` flag, allowing doctors to self-assert an HPR ID without cryptographic proof or verification tracking.

### 3. Code quality [QUAL]
- **Missing Numerical Check Constraints:**
  - `consultation_fee` (lines 62-66) has no minimum check constraint (`consultation_fee >= 0`), allowing negative values (`BE-DOC-F02`).
  - `experience_years` (lines 55-59) has no boundary checks (`0 <= experience_years <= 80`), permitting unrealistic or negative inputs (`BE-DOC-F03`).
- Clean usage of SQLAlchemy 2.0 type-annotated attributes with `Mapped[...]`.

### 4. AI-generated-code smells [QUAL]
- `DoctorSlot` relationship (line 99) and `Appointment` relationship (line 106) both use `cascade="all, delete-orphan"` via copy-paste, failing to recognize that while doctor schedule slots belong exclusively to the doctor, appointments belong jointly to the patient and the clinic.

### 5. Performance [PERF]
- `registration_number` and `hpr_id` are unique and properly indexed.
- `specialty` is indexed for fast provider search filtering by medical department.

### 6. Error handling & edge cases
- If `user` is deleted, `DoctorProfile` cascades (`ondelete="CASCADE"` on line 26). This is standard for 1-to-1 profile tables.
- All non-essential clinical relationships (`recorded_conditions`, `performed_observations`, `authored_soap_notes`, `diagnostic_orders`, `authored_prescriptions`) correctly omit delete cascades, preserving historical records.

### 7. Doc accuracy [DOC]
- Conforms to Phase 2/3 EMR requirements and doctor scheduling workflows.

### 8. Tests
- Covered by `backend/tests/test_doctor.py`, `backend/tests/test_appointment.py`, and `backend/tests/test_soap_notes.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-DOC-F01 | S2 | [QUAL] | 103-107 | Cascade delete purges patient appointment history | `appointments: Mapped[...] = relationship(..., cascade="all, delete-orphan")` | Remove `cascade="all, delete-orphan"` from appointments relationship |
| BE-DOC-F02 | S3 | [QUAL] | 62-66 | No non-negative check on consultation fee | `consultation_fee: Mapped[int] = mapped_column(...)` | Add `CheckConstraint("consultation_fee >= 0")` |
| BE-DOC-F03 | S3 | [QUAL] | 55-59 | No range validation on experience years | `experience_years: Mapped[int] = mapped_column(...)` | Add `CheckConstraint("experience_years >= 0 AND experience_years <= 80")` |

---

## Suggested Patches (NOT Applied)

### Patch BE-DOC-F01 · Risk: Low · [UNTESTED]
Prevent deletion of historical appointments upon doctor profile removal:

```diff
--- a/backend/app/models/doctor.py
+++ b/backend/app/models/doctor.py
@@ -103,5 +103,4 @@ class DoctorProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     appointments: Mapped[List["Appointment"]] = relationship(
         "Appointment",
         back_populates="doctor",
-        cascade="all, delete-orphan",
     )
```

### S3 One-Line Fixes
- **BE-DOC-F02:** In `__table_args__`, add `CheckConstraint("consultation_fee >= 0", name="chk_doctor_fee_positive")`.
- **BE-DOC-F03:** In `__table_args__`, add `CheckConstraint("experience_years >= 0 AND experience_years <= 80", name="chk_doctor_exp_range")`.

---

## Verdict

**READY-WITH-FIXES** — Solid practitioner credentials model; removing the orphan cascade on appointments is required to protect patient clinical records.
