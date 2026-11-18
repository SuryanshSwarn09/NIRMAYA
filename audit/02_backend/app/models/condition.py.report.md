# Audit Report: `backend/app/models/condition.py`

**Path**: `backend/app/models/condition.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 150 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Longitudinal patient clinical condition and problem list model adhering to HL7 FHIR R4 Condition · Risk: **S3 (Low Risk)** · Verdict: **READY-WITH-FIXES** · Faithful FHIR resource mapping with SNOMED-CT / ICD-10 bindings; missing composite index on `(patient_id, clinical_status)` for fast problem list lookups.

---

## Layer B — Explain It
- **What problem this file solves**: Manages a patient's longitudinal medical problem list, encounter diagnoses, chronic health conditions, and clinical verification states across care facilities.
- **How it works step by step**:
  1. `ClinicalCondition` links to the subject `patient_id` and optionally to an `encounter_id` (Appointment).
  2. Tracks clinical lifecycle (`ACTIVE`, `RELAPSE`, `RESOLVED`, `REMISSION`).
  3. Records verification certainty (`CONFIRMED`, `PROVISIONAL`, `DIFFERENTIAL`).
  4. Stores standardized medical ontology bindings (default SNOMED-CT URI `http://snomed.info/sct`).
  5. Captures anatomical body sites, onset/abatement timestamps, and clinical notes.
- **Concepts & patterns used**:
  - *HL7 FHIR R4 Alignment*: 100% field parity with FHIR `Condition` elements.
  - *Longitudinal Health Record*: Persists conditions independently of discrete encounters.
- **Key lines to read first**:
  - `backend/app/models/condition.py:33-55`: Relational linkage to patient, encounter, and doctor.
  - `backend/app/models/condition.py:57-86`: Clinical status and severity enums.
  - `backend/app/models/condition.py:88-102`: Terminology code, system, and display fields.
- **How to change it safely**:
  - Keep `code_coding_system` standardized to official terminology URIs (SNOMED-CT or ICD-10).

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `sqlalchemy.*`, `app.db.base.Base`, `app.models.enums.*`.
   - **Imported by**: `backend/app/api/v1/endpoints/conditions.py`, `backend/app/fhir/transformers.py`, `backend/app/services/patient_service.py`.
   - **Public surface**: `ClinicalCondition`.

2. **Security [SEC]**:
   - Patient cascade: Deleting a patient profile cascades to their condition history (`CASCADE`).
   - Doctor detachment: Deleting a doctor profile retains the historical diagnosis record (`SET NULL` on `recorded_by_doctor_id`).

3. **Code quality [QUAL]**:
   - Fully typed SQLAlchemy 2.0 mapping.
   - Clean enum definitions preventing invalid medical states.

4. **AI-generated smells [QUAL]**:
   - None observed.

5. **Performance [PERF]**:
   - `patient_id` and `clinical_status` are indexed individually. In clinical practice, nearly all problem-list queries filter by `WHERE patient_id = :p AND clinical_status = 'active'`. A composite index `(patient_id, clinical_status)` significantly optimizes high-throughput OPD queue lookups.

6. **Error handling & edge cases**:
   - Enforces non-null for `patient_id`, `clinical_status`, `verification_status`, and `code_value`.

7. **Doc accuracy [DOC]**:
   - Accurately reflects Month 1 and Month 3 milestone deliverables.

8. **Tests**:
   - Tested in `backend/tests/test_conditions.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-CON-F01** | **S3** | `[PERF]` | `33-62` | Missing composite index on patient problem list status | `patient_id` and `clinical_status` indexed separately | Add `Index("idx_condition_patient_status", "patient_id", "clinical_status")` |
| **BE-CON-F02** | **S4** | `[QUAL]` | `118-122` | Python lambda for timestamp default lacks DB server default | `default=lambda: datetime.now(timezone.utc)` | Add `server_default=func.now()` |

---

## Suggested Patches (NOT Applied)

### Patch BE-CON-P01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/models/condition.py
+++ b/backend/app/models/condition.py
@@ -8,3 +8,3 @@ from typing import TYPE_CHECKING, Optional
-from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
+from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
 from sqlalchemy.orm import Mapped, mapped_column, relationship
@@ -145,2 +145,6 @@ class ClinicalCondition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     )
+
+    __table_args__ = (
+        Index("idx_condition_patient_status", "patient_id", "clinical_status"),
+    )
```

---

## Verdict
**READY-WITH-FIXES** — Production-ready FHIR Condition model; composite indexing recommended for OPD performance.
