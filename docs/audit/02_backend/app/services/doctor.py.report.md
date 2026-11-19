# Codebase Audit Report: `backend/app/services/doctor.py`

**Audit Target**: `backend/app/services/doctor.py`  
**Subsystem**: Backend - Doctor Profile & EMR Clinician Directory Service (`backend/app/services/`)  
**File Lines**: 238 LOC  
**Severity Breakdown**: S0: 0 | S1: 2 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `doctor.py` module manages clinician identities, practice credentials, medical council registration uniqueness, ABDM Healthcare Professional Registry (HPR) handles, teleconsultation availability, and clinical specialty directory search.

```
[ Clinician Onboarding / Patient Doctor Directory ]
                       │
                       ▼
             [ doctor.py Service ]
   ├── 1. Clinician Lookup (UUID, User ID, Registration No, HPR ID)
   ├── 2. Multi-Filter Directory Search (Specialty, Teleconsult, Fee, Full-Text)
   ├── 3. Clinician Profile Creation & Identity Uniqueness Enforcement
   ├── 4. Profile Amending & Registration Number Collision Guard
   └── 5. Clinician Profile Deletion Operation
                       │
                       ▼
         [ PostgreSQL DoctorProfile & User Tables ]
```

### Import / Export Roster
- **Imports**: `typing`, `sqlalchemy` (`func`, `or_`, `select`, `ext.asyncio`, `orm.selectinload`), `app.core.exceptions`, `app.models`, `app.schemas.doctor`.
- **Exports**: `get_doctor_by_id()`, `get_doctor_by_user_id()`, `get_doctor_by_registration_number()`, `get_doctor_by_hpr_id()`, `list_doctors()`, `create_doctor_profile()`, `update_doctor_profile()`, `delete_doctor_profile()`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Resolution Methods**: Fetches `DoctorProfile` by database UUID, linked `User.id`, official medical council registration number (e.g. `MCI/12345`), or ABDM Healthcare Professional Registry handle (`hpr_id`).
2. **Directory Search**: `list_doctors()` supports filtering by medical specialty, teleconsultation status, fee ceilings, and full-text keyword matching across doctor names, registration numbers, councils, and hospital affiliations.
3. **Profile Creation**: Ensures a user cannot create multiple doctor profiles, and prevents registration number or HPR handle collisions before persisting the profile.
4. **Updating Credentials**: Validates that changes to registration numbers or HPR handles do not collide with another clinician.
5. **Deletion**: Deletes the doctor profile record.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Unverified Medical Licensing & HPR Attestation
In `create_doctor_profile()` (lines 116–174) and `update_doctor_profile()` (lines 176–225), medical registration numbers and ABDM HPR handles are accepted purely as unverified user-supplied text strings. The service does not integrate with or verify credentials against the National Medical Commission (NMC) National Register or ABDM HPR verification APIs. Any registered user can register as a specialized surgeon, prescribe medications, and perform consultations without credential verification.

### 2. Cascading Data Corruption via Hard Deletion
At lines 227–236:
```python
async def delete_doctor_profile(db: AsyncSession, doctor_id: str) -> bool:
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise EntityNotFoundException(...)
    await db.delete(doctor)
    await db.commit()
    return True
```
Hard deleting a doctor profile causes severe cascading database consequences. All historical appointments (`Appointment.doctor_id`), clinical diagnoses (`ClinicalCondition.recorded_by_doctor_id`), and diagnostic orders (`DiagnosticOrder.doctor_id`) linked to this clinician will either cascade-delete (erasing patient medical history) or trigger foreign key constraint errors (`IntegrityError`). Doctor profiles must use soft deletion (`is_active = False`).

### 3. Missing Authorization on Updates (IDOR)
`update_doctor_profile` and `delete_doctor_profile` do not accept or verify the authenticated caller identity against `doctor.user_id`, enabling any authenticated user to modify fees or delete other physicians' profiles.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-DOC-F01` | **S1** | `[SEC/AUTH]` | `backend/app/services/doctor.py:116-174` | Clinician registration numbers and HPR IDs are persisted without NMC/ABDM registry verification, allowing fraudulent physician claims. |
| `BE-SVC-DOC-F02` | **S1** | `[SEC/MED]` | `backend/app/services/doctor.py:227-236` | Hard deletion of `DoctorProfile` violates EHR retention standards and risks cascading destruction of linked patient consultations and orders. |
| `BE-SVC-DOC-F03` | **S2** | `[SEC]` | `backend/app/services/doctor.py:176-236` | Missing authorization checks allow unauthorized modifications or deletion of doctor profiles (IDOR). |
| `BE-SVC-DOC-F04` | **S3** | `[PERF]` | `backend/app/services/doctor.py:83-93` | 5-way `ilike` disjunction (`or_`) across unindexed text columns produces expensive full table scans during directory searches. |
| `BE-SVC-DOC-F05` | **S4** | `[DOC]` | `backend/app/services/doctor.py:1-20` | Missing documentation regarding NMC National Medical Register electronic signature integration. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-DOC-F01` / `BE-SVC-DOC-F02`: Soft Deletion & Authoritative NMC Verification Gate

```diff
--- a/backend/app/services/doctor.py
+++ b/backend/app/services/doctor.py
@@ -163,8 +163,14 @@ async def create_doctor_profile(
                 error_code="DUPLICATE_HPR_ID",
                 status_code=409,
             )
 
+    # Enforce NMC / ABDM HPR verification in production
+    from app.core.config import settings
+    if settings.ENVIRONMENT == "production":
+        from app.services.abdm_issuance import verify_hpr_doctor_credentials
+        if not await verify_hpr_doctor_credentials(profile_in.registration_number, profile_in.hpr_id):
+            raise AppException("Doctor credentials could not be verified against the National Medical Commission registry.", status_code=400)
+
     # Prepare data and persist
     data = profile_in.model_dump(exclude={"user_id"})
@@ -227,8 +233,9 @@ async def update_doctor_profile(
 async def delete_doctor_profile(db: AsyncSession, doctor_id: str) -> bool:
-    """Delete a doctor profile by UUID primary key."""
+    """Soft-deactivate a doctor profile to preserve medicolegal historical encounters."""
     doctor = await get_doctor_by_id(db, doctor_id)
     if not doctor:
         raise EntityNotFoundException(entity_name="DoctorProfile", entity_id=doctor_id)
 
-    await db.delete(doctor)
+    doctor.is_active = False
     await db.commit()
```
