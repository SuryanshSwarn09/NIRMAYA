# Codebase Audit Report: `backend/app/services/condition.py`

**Audit Target**: `backend/app/services/condition.py`  
**Subsystem**: Backend - Clinical Conditions & Problem List Service (`backend/app/services/`)  
**File Lines**: 243 LOC  
**Severity Breakdown**: S0: 0 | S1: 1 | S2: 2 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `condition.py` service manages the patient longitudinal problem list, supporting recording of diagnostic hypotheses, confirmed conditions, clinical status lifecycles (active, recurrence, relapse, inactive, resolved), and linkage to encounters and diagnosing practitioners.

```
[ Doctor Consultation / EMR Workspace ]
                   │
                   ▼ (Diagnosis / Problem List Entry)
        [ condition.py Service ]
   ├── 1. Patient & Encounter Validation
   ├── 2. Diagnosing Doctor Verification
   ├── 3. Status Lifecycle & Abatement Automation
   ├── 4. Problem List Query & Filter Pipeline
   └── 5. Update / Deletion Operations
                   │
                   ▼
     [ PostgreSQL ClinicalCondition Table ]
```

### Import / Export Roster
- **Imports**: `datetime`, `typing`, `sqlalchemy` (`func`, `select`, `ext.asyncio`, `orm.selectinload`), `app.core.exceptions`, `app.models`, `app.schemas.condition`.
- **Exports**: `record_condition()`, `get_condition_by_id()`, `list_patient_conditions()`, `update_condition()`, `delete_condition()`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Recording Diagnoses**: `record_condition()` validates the patient, optional encounter, and recording doctor before persisting a new `ClinicalCondition`. If created with status `RESOLVED` and no abatement timestamp, it automatically stamps the current UTC time.
2. **Retrieval**: `get_condition_by_id()` eager-loads associated `PatientProfile`, `DoctorProfile`, and `Appointment` encounter relationships via `selectinload`.
3. **Problem List Listing**: `list_patient_conditions()` supports filtering by clinical status, verification status, severity, and category, returning paginated results and total counts.
4. **Lifecycle Transitions**: `update_condition()` updates severity, notes, verification, or clinical status, auto-stamping resolution time upon transition to `RESOLVED`.
5. **Deletion**: `delete_condition()` hard-deletes the condition record from PostgreSQL.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Hard Deletion of Clinical Diagnoses (Medicolegal Invariant Violation)
At lines 231–243, `delete_condition()` issues `await db.delete(condition)`. In medical informatics (including ABDM, HL7 FHIR, and ISO 27799), clinical observations and diagnoses must never be physically erased from a database. Hard deletion erases legal history, corrupts prior consultation records, and destroys evidentiary trails required in medical malpractice audits. Conditions entered in error must transition to verification status `ENTERED_IN_ERROR` with soft-deletion rather than hard row removal.

### 2. Missing Authorization Checks on Updates
In `update_condition()`, any caller possessing the `condition_id` can modify clinical notes, change verification status, or mark serious chronic illnesses as resolved without verifying practitioner credentials or doctor-patient assignment (IDOR / Unauthorized Clinical Alteration).

### 3. Unvalidated Terminology Codes
`record_condition()` accepts `code_value` and `code_coding_system` without validating them against the platform's `terminology_validator.py`. A doctor can persist non-standard, malformed, or invalid ICD-10/SNOMED-CT codes that break downstream ABDM FHIR bundle generation.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-CON-F01` | **S1** | `[SEC/MED]` | `backend/app/services/condition.py:231-243` | Hard deletion of clinical conditions via `db.delete()` violates medicolegal record retention and EHR standards; must utilize soft-deletion or `ENTERED_IN_ERROR`. |
| `BE-SVC-CON-F02` | **S2** | `[SEC/QUAL]` | `backend/app/services/condition.py:180-229` | Update operation lacks practitioner authorization checks, enabling unauthorized alterations of patient medical records. |
| `BE-SVC-CON-F03` | **S2** | `[QUAL/MED]` | `backend/app/services/condition.py:72-88` | Condition creation does not validate diagnosis codes against SNOMED-CT / ICD-10 terminology validators. |
| `BE-SVC-CON-F04` | **S3** | `[PERF]` | `backend/app/services/condition.py:113-177` | Dual-query pagination in `list_patient_conditions` lacks composite index optimization for `(patient_id, recorded_date)`. |
| `BE-SVC-CON-F05` | **S4** | `[DOC]` | `backend/app/services/condition.py:1-20` | Missing documentation on FHIR Condition resource mapping and verification status lifecycle rules. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-CON-F01`: Soft-Deletion & Status Inactivation for Medicolegal Compliance

```diff
--- a/backend/app/services/condition.py
+++ b/backend/app/services/condition.py
@@ -231,13 +231,18 @@ async def update_condition(
 async def delete_condition(
     db: AsyncSession,
     condition_id: str,
+    reason: Optional[str] = None,
 ) -> None:
-    """Permanently remove a clinical condition from the problem list."""
+    """Soft-delete or mark clinical condition as entered-in-error for medicolegal safety."""
     condition = await db.scalar(
         select(ClinicalCondition).where(ClinicalCondition.id == condition_id)
     )
     if not condition:
         raise EntityNotFoundException("Condition", condition_id)
 
-    await db.delete(condition)
+    # Transition to entered-in-error instead of physical row erasure
+    condition.verification_status = "entered-in-error"
+    if reason:
+        condition.note = f"{condition.note or ''}\n[REMOVED]: {reason}".strip()
     await db.flush()
```
