# Day 13: Doctor EMR Directory & Clinical Provider Endpoints

**Date:** September 23, 2026  
**Milestone:** 03-03 (Month 1, Week 3, Day 3)  
**Author:** Suryansh Swarn  
**Status:** Completed  

---

## 1. Overview & Architectural Goals

Day 13 expands NIRMAYA's clinical ecosystem to **Healthcare Providers (Doctors)**. Following the implementation of the Patient Vault (Week 2) and the Authentication and RBAC security layer (Days 11 & 12), Milestone 03-03 equips the platform with complete **Doctor EMR Directory** capabilities and **Clinical Provider REST Endpoints**.

In a unified healthcare network, the healthcare practitioner profile serves dual functions:
1. **Public/Patient Consultation Gateway:** Patients and referring clinicians can query registered physicians, filter by clinical specialty (aligned with SNOMED-CT / FHIR PractitionerRole), filter by teleconsultation availability, filter by maximum consultation fee, or perform free-text search across doctor names, hospital affiliations, and medical councils.
2. **National Health Identifier (ABDM HPR) & Licensing Anchor:** Resolving official Ayushman Bharat Digital Mission (ABDM) Healthcare Professional Registry (`@hpr.abdm`) handles and State/National Medical Council registration numbers.

Key deliverables completed today:
1. **Security & Ownership Guard (`verify_doctor_modification_access` in `app/core/dependencies.py`):**
   - Restricts updates and deletions of doctor credentials exclusively to the profile owner (`doctor.user_id == current_user.id`) or an Administrator (`ADMIN` superuser override).
2. **Doctor EMR Business Logic Service (`app/services/doctor.py`):**
   - Lookup queries: `get_doctor_by_id`, `get_doctor_by_user_id`, `get_doctor_by_registration_number`, `get_doctor_by_hpr_id`.
   - Paginated directory search: `list_doctors` supporting clinical filters (`specialty`, `teleconsult_only`, `max_fee`, `query`).
   - Profile mutations: `create_doctor_profile` with collision handling (`PROFILE_ALREADY_EXISTS`, `DUPLICATE_REGISTRATION_NUMBER`, `DUPLICATE_HPR_ID`), `update_doctor_profile`, and `delete_doctor_profile`.
3. **Doctor EMR REST Endpoints (`app/api/v1/endpoints/doctors.py`):**
   - `POST /api/v1/doctors/` — Onboard provider profile, protected by RBAC (`DOCTOR` or `ADMIN` persona only).
   - `GET /api/v1/doctors/` — Paginated directory search with clinical filters and metadata.
   - `GET /api/v1/doctors/by-hpr/{hpr_id}` — ABDM Healthcare Professional Registry handle lookup.
   - `GET /api/v1/doctors/by-reg/{registration_number}` — Medical council license lookup.
   - `GET /api/v1/doctors/{doctor_id}` — Detailed demographic and practice retrieval by UUID.
   - `PUT /api/v1/doctors/{doctor_id}` — Update consultation fees, bio, teleconsult status, hospital affiliation.
   - `DELETE /api/v1/doctors/{doctor_id}` — Remove practitioner profile.
4. **Router Wiring (`app/api/v1/router.py`):**
   - Mounted `doctors.router` under `/api/v1/doctors` tagged as `"Doctor EMR"`.
5. **Comprehensive Automated Test Coverage:**
   - 10 unit tests in `test_doctor_service.py` verifying all query filters, pagination, and collision exceptions.
   - 9 integration tests in `test_api_doctors.py` verifying HTTP status codes (200, 201, 401, 403, 404, 409) across roles.
   - **Total test suite: 109/109 tests passing (100%) in 22.64s.**

---

## 2. Technical Architecture & Endpoint Matrix

### Doctor EMR Endpoint Specifications

| Endpoint | Method | Role Permissions | Description | Response Model |
|---|---|---|---|---|
| `/api/v1/doctors/` | `POST` | `DOCTOR`, `ADMIN` | Onboard verified healthcare practitioner | `APIResponse[DoctorProfileResponse]` (201) |
| `/api/v1/doctors/` | `GET` | All Authenticated | Paginated directory search with clinical filters | `PaginatedResponse[DoctorProfileResponse]` (200) |
| `/api/v1/doctors/by-hpr/{hpr_id}` | `GET` | All Authenticated | ABDM Healthcare Professional Registry lookup | `APIResponse[DoctorProfileResponse]` (200) |
| `/api/v1/doctors/by-reg/{registration_number}` | `GET` | All Authenticated | Medical Council license lookup | `APIResponse[DoctorProfileResponse]` (200) |
| `/api/v1/doctors/{doctor_id}` | `GET` | All Authenticated | Fetch doctor profile by UUID | `APIResponse[DoctorProfileResponse]` (200) |
| `/api/v1/doctors/{doctor_id}` | `PUT` | Owner, `ADMIN` | Update credentials, fees, teleconsult status | `APIResponse[DoctorProfileResponse]` (200) |
| `/api/v1/doctors/{doctor_id}` | `DELETE` | Owner, `ADMIN` | Delete doctor profile | `APIResponse[dict]` (200) |

---

## 3. Micro-Commit Journal (10+ Commits Standard)

Following the disciplined pacing protocol, Day 13 delivered 13 atomic micro-commits locally before batch push:

| # | Commit Hash | Conventional Message | Scope |
|---|---|---|---|
| **1** | `75d0a0e` | `feat(core): add doctor modification access security guard` | Implemented `verify_doctor_modification_access` with admin superuser override in `app/core/dependencies.py`. |
| **2** | `e9f1b28` | `feat(services): implement doctor profile retrieval queries by id reg and hpr` | Added lookups by UUID, user ID, registration number, and ABDM HPR ID in `app/services/doctor.py`. |
| **3** | `f951e19` | `feat(services): implement paginated doctor directory listing with clinical filters` | Implemented `list_doctors` supporting specialty, teleconsult, fee, and text search filters. |
| **4** | `dbc0cb6` | `feat(services): implement doctor profile creation with abdm hpr validation` | Added `create_doctor_profile` with collision checks for user profile, registration, and HPR ID. |
| **5** | `b49db7d` | `feat(services): implement doctor profile update and deletion service operations` | Added `update_doctor_profile`, `delete_doctor_profile`, and exported functions in `services/__init__.py`. |
| **6** | `05fe31c` | `feat(api): create doctor profile onboarding endpoint with rbac guard` | Implemented `POST /api/v1/doctors/` with `DOCTOR` and `ADMIN` role boundary checks. |
| **7** | `ffd4daf` | `feat(api): create doctor directory listing and resolution endpoints` | Implemented `GET /`, `GET /by-hpr/{hpr_id}`, `GET /by-reg/{reg}`, and `GET /{id}` in `endpoints/doctors.py`. |
| **8** | `43d8aed` | `feat(api): create doctor profile update and deletion endpoints` | Implemented `PUT /{id}` and `DELETE /{id}` guarded by `verify_doctor_modification_access`. |
| **9** | `e496cba` | `feat(api): wire doctor router into api v1 router` | Mounted `doctors.router` under prefix `"/doctors"` in `app/api/v1/router.py`. |
| **10** | `6978c09` | `test(services): add comprehensive unit tests for doctor service layer` | Added 10 unit tests in `test_doctor_service.py` covering lookups, filters, updates, and cascades. |
| **11** | `8a035f5` | `test(api): add integration test suite for doctor endpoints and rbac guards` | Added 9 integration tests in `test_api_doctors.py` testing HTTP lifecycles and 401/403/404/409 responses. |
| **12** | *Current* | `docs(journey): log day 13 doctor emr directory and provider endpoints` | Documented provider endpoints, clinical filters, and updated GitBook `SUMMARY.md`. |
| **13** | *Next* | `docs(changelog): record milestone 03-03 doctor emr directory deliverables` | Recorded Milestone 03-03 deliverables in `docs/CHANGELOG.md`. |

---

## 4. Test Verification & Coverage

Running the full pytest test suite verified **109/109 tests passing (100%)**:

```text
backend\tests\test_api_auth.py (6 tests) PASSED               [  5%]
backend\tests\test_api_doctors.py (9 tests) PASSED            [ 13%]
backend\tests\test_api_patients.py (8 tests) PASSED           [ 21%]
backend\tests\test_api_rbac.py (5 tests) PASSED               [ 25%]
backend\tests\test_auth_jwt.py (6 tests) PASSED               [ 31%]
backend\tests\test_db_base.py (4 tests) PASSED                [ 34%]
backend\tests\test_db_session.py (4 tests) PASSED             [ 38%]
backend\tests\test_doctor_service.py (10 tests) PASSED        [ 47%]
backend\tests\test_exceptions.py (4 tests) PASSED             [ 51%]
backend\tests\test_health.py (7 tests) PASSED                 [ 57%]
backend\tests\test_meta.py (1 test) PASSED                    [ 58%]
backend\tests\test_migrations.py (2 tests) PASSED             [ 60%]
backend\tests\test_models_doctor.py (5 tests) PASSED          [ 65%]
backend\tests\test_models_lab.py (5 tests) PASSED             [ 69%]
backend\tests\test_models_patient.py (4 tests) PASSED         [ 73%]
backend\tests\test_models_user.py (3 tests) PASSED            [ 76%]
backend\tests\test_rbac.py (7 tests) PASSED                   [ 82%]
backend\tests\test_schemas_doctor_lab.py (8 tests) PASSED     [ 89%]
backend\tests\test_schemas_patient.py (7 tests) PASSED        [ 96%]
backend\tests\test_seeder.py (4 tests) PASSED                 [100%]

============================ 109 passed in 22.64s =============================
```

---

## 5. Upcoming: Day 14 Preview

With both the Patient Vault and Doctor EMR Directory operational:
- **Milestone 03-04 (Day 14):** Diagnostic Lab Facility Endpoints, Health Facility Registry (ABDM HFR) & Test Catalog Management.
- Exposing `/api/v1/labs` for managing diagnostic centers, NABL accreditations, and lab test offerings.
