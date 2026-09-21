# Day 12: Role-Based Access Control (RBAC) & Security Guards

**Date:** September 22, 2026  
**Milestone:** 03-02 (Month 1, Week 3, Day 2)  
**Author:** Suryansh Swarn  
**Status:** Completed  

---

## 1. Overview & Architectural Goals

Day 12 expands upon Day 11's authentication and JWT foundation by engineering a strict, fine-grained **Role-Based Access Control (RBAC)** architecture and **Patient Resource Ownership Security Guards** across NIRMAYA's clinical layers.

In an interoperable healthcare ecosystem (spanning patients, medical practitioners, diagnostic centers, and platform administrators), authentication alone is insufficient. Health records are subject to strict privacy and regulatory boundaries (DISHA, ABDM, HIPAA). Actors must only access resources appropriate for their clinical duties:
- **Patients** must only view and modify their own longitudinal records.
- **Doctors** require clinical read access across patient records for diagnostic consultations, but cannot arbitrarily delete or mutate basic patient account identities without administrative consent.
- **Diagnostic Labs** require clinical read access to correlate test orders and verify specimen identities, but cannot alter core demographic records.
- **Administrators** possess superuser override capabilities for system maintenance, compliance auditing, and emergency break-glass interventions.

Key deliverables completed today:
1. **Configurable RBAC Dependency Factory (`RoleChecker` & `require_role`):**
   - High-performance FastAPI security dependency enforcing role checks on active actors.
   - Built-in **Admin Superuser Override** granting administrators seamless access across clinical pillars.
   - Standardized `403 FORBIDDEN` (`PermissionDeniedException`) responses detailing permitted role sets upon authorization failures.
2. **Pre-configured Role Guards (`app/core/dependencies.py`):**
   - `require_patient`: Permits Patient and Admin actors.
   - `require_doctor`: Permits Doctor and Admin actors.
   - `require_lab`: Permits Diagnostic Lab and Admin actors.
   - `require_admin`: Strictly limited to Admin actors.
   - `require_clinical_staff`: Unified guard permitting Doctors, Labs, and Admins.
3. **Resource Ownership & Clinical Verification (`verify_patient_access` & `verify_patient_modification_access`):**
   - Read access guard verifying patient ownership (`patient.user_id == current_user.id`) or clinical staff privilege (`DOCTOR`, `LAB`, `ADMIN`).
   - Write/delete mutation guard restricting profile modifications exclusively to the profile owner or an administrator.
4. **RBAC Diagnostic Endpoints (`/api/v1/auth/roles/*`):**
   - `/roles/patient-only`
   - `/roles/doctor-only`
   - `/roles/lab-only`
   - `/roles/admin-only`
   - `/roles/clinical-staff-only`
5. **Patient Vault Endpoint Hardening (`app/api/v1/endpoints/patients.py`):**
   - `POST /` — Authenticated creation, preventing non-admins from creating profiles for other users.
   - `GET /` — Protected by `require_clinical_staff` to prevent bulk demographic scraping by patients.
   - `GET /{patient_id}` & `GET /by-abha/{identifier}` — Protected by ownership and clinical staff checks.
   - `PUT /{patient_id}` & `DELETE /{patient_id}` — Protected by owner/admin mutation checks.
6. **Comprehensive Automated Testing:**
   - 7 unit tests in `test_rbac.py` for `RoleChecker`, admin override, and resource ownership checks.
   - 5 integration tests in `test_api_rbac.py` verifying all 4 roles across diagnostic role routes.
   - 8 updated integration tests in `test_api_patients.py` with Bearer tokens and 403 boundary assertions.
   - **Total test suite: 90/90 tests passing (100%) in under 20 seconds.**

---

## 2. Technical Architecture & Permission Matrix

### Clinical Permission Matrix

| Endpoint / Action | Method | Patient | Doctor | Diagnostic Lab | Admin |
|---|---|:---:|:---:|:---:|:---:|
| **Auth Diagnostic: Patient Only** | `GET /auth/roles/patient-only` |  Allowed | ❌ 403 | ❌ 403 |  Override |
| **Auth Diagnostic: Doctor Only** | `GET /auth/roles/doctor-only` | ❌ 403 |  Allowed | ❌ 403 |  Override |
| **Auth Diagnostic: Lab Only** | `GET /auth/roles/lab-only` | ❌ 403 | ❌ 403 |  Allowed |  Override |
| **Auth Diagnostic: Admin Only** | `GET /auth/roles/admin-only` | ❌ 403 | ❌ 403 | ❌ 403 |  Allowed |
| **Auth Diagnostic: Clinical Staff** | `GET /auth/roles/clinical-staff-only` | ❌ 403 |  Allowed |  Allowed |  Override |
| **Patient Profile: Create** | `POST /patients/` |  (Own ID) | ❌ 403 (other) | ❌ 403 (other) |  (Any ID) |
| **Patient Directory: List / Search** | `GET /patients/` | ❌ 403 |  Allowed |  Allowed |  Allowed |
| **Patient Profile: Read by ID** | `GET /patients/{id}` |  (Own only) |  (Clinical) |  (Clinical) |  Allowed |
| **Patient Profile: Read by ABHA** | `GET /patients/by-abha/{id}` |  (Own only) |  (Clinical) |  (Clinical) |  Allowed |
| **Patient Profile: Update** | `PUT /patients/{id}` |  (Own only) | ❌ 403 | ❌ 403 |  Allowed |
| **Patient Profile: Delete** | `DELETE /patients/{id}` |  (Own only) | ❌ 403 | ❌ 403 |  Allowed |

---

## 3. Micro-Commit Journal (10+ Commits Standard)

Following the disciplined pacing protocol, Day 12 delivered 13 atomic micro-commits locally before batch push:

| # | Commit Hash | Conventional Message | Scope |
|---|---|---|---|
| **1** | `2d5b173` | `feat(core): implement role checker security dependency factory` | Implemented `RoleChecker` and `require_role` with admin superuser override in `app/core/dependencies.py`. |
| **2** | `57278f1` | `feat(core): define role specific guards for patient doctor lab and admin` | Added pre-configured role guards (`require_patient`, `require_doctor`, `require_lab`, `require_admin`, `require_clinical_staff`). |
| **3** | `f3be6a6` | `feat(core): add resource ownership verification helper for patient profiles` | Added `verify_patient_access` and `verify_patient_modification_access` helpers. |
| **4** | `8012a0e` | `feat(api): add rbac role test endpoints to auth router` | Added 5 diagnostic role test endpoints under `/api/v1/auth/roles/*`. |
| **5** | `2e8bb93` | `feat(api): protect patient profile creation with authentication guard` | Enforced caller authentication and user_id binding in `POST /api/v1/patients/`. |
| **6** | `71335d9` | `feat(api): protect patient directory listing with clinical staff guard` | Restrained `GET /api/v1/patients/` to clinical staff (`DOCTOR`, `LAB`, `ADMIN`). |
| **7** | `ac9946c` | `feat(api): protect patient profile retrieval with ownership and clinical guard` | Guarded `GET /{id}` and `GET /by-abha/{id}` with ownership and clinical privilege checks. |
| **8** | `e3ee0c5` | `feat(api): protect patient update and deletion with owner admin guard` | Restricted `PUT` and `DELETE` on patient profiles to profile owner and administrators. |
| **9** | `c124ef9` | `test(core): add unit tests for role checker and permission hierarchies` | Added 7 unit tests in `test_rbac.py` for guards, admin bypass, and ownership helpers. |
| **10** | `76d3673` | `test(api): add integration tests for role boundaries and 403 forbidden responses` | Added 5 integration tests in `test_api_rbac.py` verifying all 4 roles across role test endpoints. |
| **11** | `2b2a49a` | `test(api): update patient vault integration tests with rbac bearer auth` | Updated 8 integration tests in `test_api_patients.py` with Bearer tokens and 403 boundary assertions. |
| **12** | *Current* | `docs(journey): log day 12 rbac deliverables and permission matrices` | Documented permission matrix, role boundaries, and updated GitBook `SUMMARY.md`. |
| **13** | *Next* | `docs(changelog): record milestone 03-02 rbac security guards` | Recorded Milestone 03-02 deliverables in `docs/CHANGELOG.md`. |

---

## 4. Test Verification & Coverage

Running the full pytest test suite verified **90/90 tests passing (100%)**:

```text
backend\tests\test_api_auth.py (6 tests) PASSED               [  6%]
backend\tests\test_api_patients.py (8 tests) PASSED           [ 15%]
backend\tests\test_api_rbac.py (5 tests) PASSED               [ 21%]
backend\tests\test_auth_jwt.py (6 tests) PASSED               [ 27%]
backend\tests\test_db_base.py (4 tests) PASSED                [ 32%]
backend\tests\test_db_session.py (4 tests) PASSED             [ 36%]
backend\tests\test_exceptions.py (4 tests) PASSED             [ 41%]
backend\tests\test_health.py (7 tests) PASSED                 [ 48%]
backend\tests\test_meta.py (1 test) PASSED                    [ 50%]
backend\tests\test_migrations.py (2 tests) PASSED             [ 52%]
backend\tests\test_models_doctor.py (5 tests) PASSED          [ 57%]
backend\tests\test_models_lab.py (5 tests) PASSED             [ 63%]
backend\tests\test_models_patient.py (4 tests) PASSED         [ 67%]
backend\tests\test_models_user.py (3 tests) PASSED            [ 71%]
backend\tests\test_rbac.py (7 tests) PASSED                   [ 78%]
backend\tests\test_schemas_doctor_lab.py (8 tests) PASSED     [ 87%]
backend\tests\test_schemas_patient.py (7 tests) PASSED        [ 95%]
backend\tests\test_seeder.py (4 tests) PASSED                 [100%]

============================= 90 passed in 19.37s =============================
```

---

## 5. Upcoming: Day 13 Preview

With authentication and RBAC firmly secured:
- **Milestone 03-03 (Day 13):** Doctor EMR Directory & Clinical Provider Endpoints.
- Exposing `/api/v1/doctors` for querying registered healthcare providers, filtering by medical specialty, HPR ID verification, and consultation fee tracking.
