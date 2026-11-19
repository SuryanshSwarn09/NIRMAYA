# Codebase Technical Audit Report: `backend/app/services/patient.py`

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`patient.py` implements the Patient Vault business logic service layer for the NIRMAYA healthcare platform. It provides core identity resolution, profile lifecycle management, multi-criteria demographic and clinical querying, and ABDM identifier binding (14-digit ABHA ID and `@abdm` address handle) with database uniqueness guarantees across PostgreSQL `PatientProfile` and `User` entities.

### System Topology & Patient Vault Architecture
```
   [ Citizen Portal / Registration Desk ]
                      |
    (Register / Query / Resolve ABHA)
                      v
   +------------------------------------+
   |           PatientService           |
   +------------------------------------+
   | - ABHA Number / Handle Resolver    |
   | - Multi-Field Demographic Search   |
   | - Uniqueness & Integrity Checks    |
   | - Profile CRUD & Eager User Join   |
   +------------------------------------+
                      |
             (AsyncSession ORM)
                      v
           [( PostgreSQL Database )]
           Tables: `patient_profiles`, `users`
```

### Module Metadata & Imports/Exports
- **Module Path:** `backend/app/services/patient.py`
- **Component Classification:** Core Patient Vault & Identity Service
- **Lines of Code:** 212 LOC
- **Imports:** `typing`, `sqlalchemy.*`, `sqlalchemy.ext.asyncio.AsyncSession`, `app.core.exceptions.*`, `app.models.*`, `app.schemas.patient.*`
- **Primary Exports:** `get_patient_by_id`, `get_patient_by_user_id`, `get_patient_by_abha`, `list_patients`, `create_patient_profile`, `update_patient_profile`, `delete_patient_profile`

---

## Layer B: Plain-Language Developer Walkthrough

The module manages the central patient entity in NIRMAYA:
1. **Identity Resolution**:
   - `get_patient_by_id`: Resolves patient profile by primary key UUID with linked `User` model eagerly loaded.
   - `get_patient_by_user_id`: Links authentication user identity to clinical patient record.
   - `get_patient_by_abha`: Resolves a patient from either their 14-digit ABHA number (`91-XXXX-XXXX-XXXX`) or their `@abdm` address handle.
2. **Longitudinal Patient Search (`list_patients`)**: Executes paginated queries supporting filtering by city, blood group, and free-text queries matching across patient name, email, ABHA number, ABHA handle, or city.
3. **Profile Creation (`create_patient_profile`)**: Verifies that the parent `User` exists, confirms that the user does not already possess an active patient profile (one-to-one constraint), verifies global uniqueness of ABHA number and ABHA handle, and inserts the new `PatientProfile`.
4. **Profile Mutation (`update_patient_profile`)**: Applies updates while preventing ABHA number or handle collisions against other registered patients.
5. **Profile Deletion (`delete_patient_profile`)**: Executes database deletion of the patient record.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: One-to-One User-Patient Binding
A citizen user in the identity system can correspond to at most one clinical `PatientProfile`. Lines 116–122 enforce this invariant by throwing a 409 Conflict if a profile already exists for the given `user_id`.

### Invariant 2: National ABHA Identifier Uniqueness
ABHA numbers and ABHA handles are sovereign identifiers that uniquely reference an individual across India. The service checks both creation and update paths (lines 125–144, 168–188) to guarantee that no two patient profiles share the same ABHA identifier.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
|---|---|---|---|---|
| `BE-SVC-PAT-F01` | **S1** | `[SEC]` | `backend/app/services/patient.py:202-212` | Hard Deletion of Patient Profile Cascades and Destroys Historical Medical Records. `delete_patient_profile()` executes `await db.delete(patient)` directly in PostgreSQL. If the database schema has `CASCADE` deletes, all historical appointments, clinical conditions, lab observations, prescriptions, and dispensations are permanently obliterated. If `RESTRICT` is configured, an unhandled `IntegrityError` (500 Internal Server Error) is thrown. Under the National Medical Commission (NMC) regulations, clinical records must be retained for at least 3 years and cannot be hard deleted. Soft deletion (`is_deleted=True`) is mandatory. |
| `BE-SVC-PAT-F02` | **S1** | `[SEC]` | `backend/app/services/patient.py:165-200` | Unrestricted Profile Mutation Without Patient Ownership Verification (IDOR). `update_patient_profile()` takes any arbitrary `patient_id` and mutates demographics, emergency contacts, or ABHA identifiers without asserting that the calling user owns the profile or has valid administrative/proxy authority. |
| `BE-SVC-PAT-F03` | **S2** | `[QUAL]` | `backend/app/services/patient.py:115-145` | Race Condition in ABHA Uniqueness Check (TOCTOU). `create_patient_profile` performs a `SELECT` query to check if `abha_number` exists, followed by `db.add(patient)`. Without an exclusive lock or relying cleanly on database unique constraints with exception handling, concurrent requests can pass the check and trigger unhandled database `UniqueViolation`. |
| `BE-SVC-PAT-F04` | **S2** | `[PERF]` | `backend/app/services/patient.py:65-80` | Multi-Column `ILIKE` Disjunction Causes Full Table Scans. Searching `User.full_name`, `User.email`, `PatientProfile.abha_number`, `PatientProfile.abha_address`, and `PatientProfile.city` with leading wildcards `%term%` forces unindexed sequential table scans. |
| `BE-SVC-PAT-F05` | **S3** | `[PERF]` | `backend/app/services/patient.py:80-90` | Count Query Performs Full Subquery Table Scan Without Covering Indexes. |
| `BE-SVC-PAT-F06` | **S4** | `[DOC]` | `backend/app/services/patient.py:10-18` | Missing DPDP Act 2023 Section 8 Data Fiduciary Retention & Right to Erasure Regulatory Policy Documentation. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch 1: Enforce Soft Deletion Rather than Hard Deletion (`BE-SVC-PAT-F01`)
```diff
--- a/backend/app/services/patient.py
+++ b/backend/app/services/patient.py
@@ -204,5 +204,8 @@ async def delete_patient_profile(db: AsyncSession, patient_id: str) -> bool:
     patient = await get_patient_by_id(db, patient_id)
     if not patient:
         raise EntityNotFoundException(entity_name="PatientProfile", entity_id=patient_id)
 
-    await db.delete(patient)
+    # Soft delete to preserve historical medical records under NMC regulations
+    patient.is_active = False
+    patient.deleted_at = datetime.now(timezone.utc)
     await db.commit()
     return True
```

### Patch 2: Handle Database UniqueViolation Exception Cleanly (`BE-SVC-PAT-F03`)
```diff
--- a/backend/app/services/patient.py
+++ b/backend/app/services/patient.py
@@ -1,4 +1,5 @@
 from typing import List, Optional, Tuple
+from sqlalchemy.exc import IntegrityError
 from sqlalchemy import func, or_, select
@@ -148,3 +149,6 @@ async def create_patient_profile(
     db.add(patient)
-    await db.commit()
+    try:
+        await db.commit()
+    except IntegrityError:
+        await db.rollback()
+        raise AppException("Patient profile with this user or ABHA already exists", error_code="DUPLICATE_PROFILE", status_code=409)
```
