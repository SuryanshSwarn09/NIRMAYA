# Audit Report: backend/app/models/patient.py

**Path:** `backend/app/models/patient.py` | **Layer:** Backend (ORM Models) | **Language:** Python 3.12 (SQLAlchemy 2.0) | **LOC:** 165 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Core patient profile model and longitudinal health vault, anchoring clinical demographics, Ayushman Bharat Digital Mission (ABDM) ABHA identity, and clinical history.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** Cascading hard delete (`cascade="all, delete-orphan"`) on all clinical relationships (appointments, conditions, vitals, SOAP notes, lab orders/reports, prescriptions) destroys patient medical history required by NMC and clinical regulations to be preserved for 3–10 years.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In a national healthcare platform, every citizen has a central patient health profile. This entity manages core demographics (DOB, gender, blood group), contact and residential details, emergency contacts, national ABHA digital health identifiers (14-digit ABHA number and `@abdm` address), and serves as the relational anchor for all historical clinical records.

### How it works, step by step
1. `PatientProfile` links 1-to-1 to a platform account in `User` via `user_id`.
2. It captures demographic attributes: `date_of_birth`, `gender`, and `blood_group`.
3. It stores residential data: `city`, `state`, and `pincode`.
4. It records designated emergency contacts (`name`, `phone`, `relation`).
5. It integrates with Ayushman Bharat via unique `abha_number` and `abha_address`.
6. It maintains bidirectional relationships to the patient's entire longitudinal medical history: appointments, held slots, conditions, observations, SOAP notes, diagnostic requisitions/reports, and prescriptions.

### Concepts and patterns used
- *Longitudinal Patient Vault:* Central aggregation of all medical encounters, diagnostic findings, and prescriptions.
- *ABDM ABHA Integration:* Storing canonical ABHA identity tokens for national health exchange.
- *1-to-1 Profile Extension Pattern:* Segregating authentication credentials (`User`) from clinical identity (`PatientProfile`).

### Key lines to read first
- `patient.py:21-33`: `PatientProfile` class and 1-to-1 linkage to `user.id`.
- `patient.py:83-96`: ABDM `abha_number` and `abha_address` fields.
- `patient.py:103-158`: Cascading relationships to clinical records.

### How to change it safely
Do not drop unique constraints on `abha_number` or `abha_address`. When modifying clinical relationships, ensure that foreign key definitions in related models match. Consider implementing soft-deletion (`is_deleted`) to avoid accidental clinical record destruction.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing`, `sqlalchemy` (Date, Enum, ForeignKey, String), `sqlalchemy.orm` (Mapped, mapped_column, relationship), `app.db.base` (Base, TimestampMixin, UUIDPrimaryKeyMixin), `app.models.enums` (BloodGroup, Gender).
- **Imported By:** `backend/app/models/__init__.py`, `backend/app/models/appointment.py`, `backend/app/models/condition.py`, `backend/app/models/diagnostic.py`, `backend/app/models/medication_request.py`, `backend/app/models/medication_dispense.py`, `backend/app/models/observation.py`, `backend/app/models/soap_note.py`, `backend/app/models/user.py`, `backend/app/services/patient_service.py`, `backend/app/api/v1/endpoints/patients.py`.
- **Public Surface:** Class `PatientProfile` (table `patient_profile`).

### 2. Security [SEC]
- **Medical Record Retention Compliance (CWE-404):** Lines 107, 121, 128, 135, 142, 149, 156 configure `cascade="all, delete-orphan"` across all clinical collections. In India, the National Medical Commission (NMC) regulations and Clinical Establishments Act mandate that medical documentation and clinical encounter records be preserved for a minimum of 3 years (inpatient: 10 years). Hard-deleting a patient's profile directly destroys all diagnostic, encounter, and prescription evidence, violating medical compliance laws (`BE-PAT-F01`).
- **Emergency Contact Validation (CWE-20):** `emergency_contact_phone` (`String(20)`) lacks phone number regex validation, allowing invalid contact numbers.

### 3. Code quality [QUAL]
- **Missing Navigation to Proxy Relationships (Lines 102-158):** In `backend/app/models/family_proxy.py`, `PatientProxyRelationship` defines `guardian_patient_id` and `dependent_patient_id`. However, `PatientProfile` declares no corresponding `guardian_proxies` or `dependent_proxies` relationships, forcing developers to write manual queries instead of using idiomatic ORM navigation (`BE-PAT-F02`).
- Excellent use of SQLAlchemy 2.0 type hints and explicit mapped columns.

### 4. AI-generated-code smells [QUAL]
- The uniform application of `cascade="all, delete-orphan"` across all 7 clinical relationships indicates a generic database model prompt that treated patient health data like temporary e-commerce cart items.

### 5. Performance [PERF]
- `user_id`, `city`, `abha_number`, and `abha_address` are indexed.
- Note: Loading a `PatientProfile` with default lazy loading for 7 child collections can cause N+1 overhead if not queried with `selectinload` or explicit joins.

### 6. Error handling & edge cases
- `abha_number` and `abha_address` are nullable, correctly supporting patients who have not yet linked or generated an ABHA ID.

### 7. Doc accuracy [DOC]
- Perfectly aligns with Month 1 Day 7 patient vault documentation.

### 8. Tests
- Covered by `backend/tests/test_patient.py`, `backend/tests/test_appointments.py`, and `backend/tests/test_fhir.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-PAT-F01 | S2 | [SEC] | 104-158 | Hard cascade delete destroys legally required medical records | `cascade="all, delete-orphan"` on 7 clinical relationships | Implement soft-delete (`is_deleted`) or remove delete-orphan cascades |
| BE-PAT-F02 | S2 | [QUAL] | 102-158 | Missing ORM relationship to family proxy access | No `dependents` or `guardians` relationships declared | Add `relationship("PatientProxyRelationship", ...)` |
| BE-PAT-F03 | S3 | [QUAL] | 74-77 | Unvalidated emergency contact phone number | `emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20))` | Add phone format validation |

---

## Suggested Patches (NOT Applied)

### Patch BE-PAT-F02 · Risk: Low · [UNTESTED]
Add bidirectional relationships for family proxy access to `PatientProfile`:

```diff
--- a/backend/app/models/patient.py
+++ b/backend/app/models/patient.py
@@ -17,2 +17,3 @@ if TYPE_CHECKING:
     from app.models.medication_request import MedicationRequest
+    from app.models.family_proxy import PatientProxyRelationship
 
@@ -157,2 +158,16 @@ class PatientProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     )
+
+    # Family proxy access: relationships where this patient is the guardian
+    dependent_proxies: Mapped[List["PatientProxyRelationship"]] = relationship(
+        "PatientProxyRelationship",
+        foreign_keys="PatientProxyRelationship.guardian_patient_id",
+        backref="guardian",
+    )
+
+    # Family proxy access: relationships where this patient is the dependent
+    guardian_proxies: Mapped[List["PatientProxyRelationship"]] = relationship(
+        "PatientProxyRelationship",
+        foreign_keys="PatientProxyRelationship.dependent_patient_id",
+        backref="dependent",
+    )
```

---

## Verdict

**READY-WITH-FIXES** — Central longitudinal patient model; requires soft-deletion safeguards to prevent legal medical record destruction upon profile deletion.
