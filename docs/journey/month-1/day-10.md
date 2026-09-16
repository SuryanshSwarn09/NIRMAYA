# Day 10: Patient Vault Profile CRUD API, Integration Tests & Week 2 Close

**Date:** September 17, 2026  
**Milestone:** 02-05 (Week 2: Database Schemas & Migrations)  
**Weekly Release:** `v0.1.0-alpha.w2` (Closing Week 2)  
**Focus Area:** Patient Vault Service Layer, REST API CRUD Endpoints, ABDM ABHA Resolution, Paginated Clinical Search, Pydantic v2 Serialization, and End-to-End Test Automation

---

## 1. Objectives

Closing out Week 2 of the NIRMAYA 4-month roadmap, Day 10 builds the first production-grade clinical API surface on top of the relational persistence engine:
1. **Patient Vault Service Layer (`app/services/patient.py`):** Asynchronous domain logic for patient profile onboarding, search queries, pagination calculations, and ABHA identifier conflict checks.
2. **Patient Vault REST API Router (`app/api/v1/endpoints/patients.py`):**
   - `POST /api/v1/patients/`: Onboard patient profiles with clinical demographics and ABDM ABHA handles.
   - `GET /api/v1/patients/`: Paginated patient directory with search across names, emails, ABHA IDs, cities, and blood groups.
   - `GET /api/v1/patients/{patient_id}`: Retrieve detailed clinical demographics and nested user account data by UUID.
   - `GET /api/v1/patients/by-abha/{identifier}`: Interoperable resolution matching 14-digit ABHA IDs or `@abdm` handles.
   - `PUT /api/v1/patients/{patient_id}`: Update demographic, address, or emergency contact information with uniqueness protection.
   - `DELETE /api/v1/patients/{patient_id}`: Remove patient profile and trigger cleanup.
3. **Router Registration (`app/api/v1/router.py`):** Wire `patients.router` under `/api/v1/patients` tagged `["Patient Vault"]`.
4. **Integration Test Automation (`backend/tests/test_api_patients.py`):** Automated tests covering create, duplicate conflict rejection (409), identifier resolution, pagination, filtering, updates, and deletion (elevating backend test coverage to **66 passing tests**).
5. **Week 2 Release Milestone (`v0.1.0-alpha.w2`):** Formalize the completion of Week 2 with release tagging and retrospective documentation.

---

## 2. Engineering Work Completed

### 1. Patient Vault Service Layer (`backend/app/services/patient.py`, `backend/app/services/__init__.py`)
- Created `app/services` module establishing the business logic separation between FastAPI HTTP controllers and SQLAlchemy ORM models.
- Implemented `create_patient_profile()` with defensive checks:
  - Rejects creation if the associated `User` is missing (`404 NOT_FOUND`).
  - Rejects if the `User` already has an active profile (`409 PROFILE_ALREADY_EXISTS`).
  - Validates uniqueness of `abha_number` and `abha_address` (`409 DUPLICATE_ABHA_*`).
- Implemented `get_patient_by_abha()` supporting dual-mode resolution: 14-digit hyphenated ABHA number or `@abdm` handle.
- Implemented `list_patients()` using dynamic query filtering and eager relationship loading (`selectinload(PatientProfile.user)`).
- Implemented `update_patient_profile()` protecting against ABHA collisions during modification.
- Implemented `delete_patient_profile()` with cascade cleanup.

### 2. Patient Vault REST API Router (`backend/app/api/v1/endpoints/patients.py`)
- Built FastAPI router adhering to platform standards:
  - All single entity operations return `APIResponse[PatientProfileResponse]`.
  - Directory listing returns `PaginatedResponse[PatientProfileResponse]` with complete `PaginationMeta` (`total_count`, `page`, `limit`, `total_pages`, `has_next`, `has_prev`).
  - Standard HTTP status codes (201 Created, 200 OK, 404 Not Found, 409 Conflict, 422 Unprocessable Entity).

### 3. API Router Integration (`backend/app/api/v1/router.py`)
- Mounted `patients.router` under `/api/v1/patients` with OpenAPI tag `"Patient Vault"`.

### 4. Integration Test Suite (`backend/tests/test_api_patients.py`)
- Configured isolated async SQLite test client fixture with `get_db` dependency overrides.
- Implemented 8 comprehensive integration test cases:
  1. `test_create_patient_profile_success`: Complete onboarding with clinical demographics and ABHA credentials.
  2. `test_create_patient_duplicate_profile_rejection`: Verification of 409 Conflict on duplicate profile creation.
  3. `test_create_patient_duplicate_abha_rejection`: Verification of 409 Conflict on duplicate ABHA number.
  4. `test_get_patient_by_id_and_not_found`: Successful ID lookup and 404 error envelope validation.
  5. `test_get_patient_by_abha_identifier`: Resolution via both 14-digit number (`91-XXXX-XXXX-XXXX`) and handle (`@abdm`).
  6. `test_list_patients_pagination_and_filtering`: Multi-page navigation, city filtering, blood group filtering (`params={"blood_group": "A+"}`), and text search.
  7. `test_update_patient_profile`: Attribute update verification with untouched field preservation.
  8. `test_delete_patient_profile`: Successful deletion and subsequent 404 verification.

---

## 3. Verification & Build Results

### Automated Pytest Suite (`66/66 tests passing` in 17.15s):
```text
backend\tests\test_api_patients.py::test_create_patient_profile_success PASSED [  1%]
backend\tests\test_api_patients.py::test_create_patient_duplicate_profile_rejection PASSED [  3%]
backend\tests\test_api_patients.py::test_create_patient_duplicate_abha_rejection PASSED [  4%]
backend\tests\test_api_patients.py::test_get_patient_by_id_and_not_found PASSED [  6%]
backend\tests\test_api_patients.py::test_get_patient_by_abha_identifier PASSED [  7%]
backend\tests\test_api_patients.py::test_list_patients_pagination_and_filtering PASSED [  9%]
backend\tests\test_api_patients.py::test_update_patient_profile PASSED   [ 10%]
backend\tests\test_api_patients.py::test_delete_patient_profile PASSED   [ 12%]
backend\tests\test_db_base.py::test_declarative_base_tablename_derivation PASSED [ 13%]
backend\tests\test_db_base.py::test_uuid_primary_key_mixin_schema PASSED [ 15%]
backend\tests\test_db_base.py::test_timestamp_mixin_schema PASSED        [ 16%]
backend\tests\test_db_base.py::test_entity_persistence_with_mixins PASSED [ 18%]
backend\tests\test_db_session.py::test_check_db_health_success_with_sqlite PASSED [ 19%]
backend\tests\test_db_session.py::test_check_db_health_failure_handling PASSED [ 21%]
backend\tests\test_db_session.py::test_get_db_session_generator_lifecycle PASSED [ 22%]
backend\tests\test_db_session.py::test_get_db_session_rollback_on_exception PASSED [ 24%]
backend\tests\test_exceptions.py::test_app_exception_attributes PASSED   [ 25%]
backend\tests\test_exceptions.py::test_entity_not_found_exception PASSED [ 27%]
backend\tests\test_exceptions.py::test_permission_denied_exception PASSED [ 28%]
backend\tests\test_exceptions.py::test_not_found_error_payload_envelope PASSED [ 30%]
backend\tests\test_health.py::test_root_endpoint PASSED                  [ 31%]
backend\tests\test_health.py::test_health_check_payload_structure PASSED [ 33%]
backend\tests\test_health.py::test_database_health_probe_mock_healthy PASSED [ 34%]
backend\tests\test_performance_telemetry_header PASSED                   [ 36%]
backend\tests\test_health.py::test_correlation_id_generation_and_propagation PASSED [ 37%]
backend\tests\test_health.py::test_security_headers_injection PASSED     [ 39%]
backend\tests\test_health.py::test_404_error_envelope_formatting PASSED  [ 40%]
backend\tests\test_meta.py::test_meta_capabilities_endpoint PASSED       [ 42%]
backend\tests\test_migrations.py::test_migration_revision_head PASSED    [ 43%]
backend\tests\test_migrations.py::test_migration_upgrade_and_downgrade_lifecycle PASSED [ 45%]
backend\tests\test_models_doctor.py::test_create_doctor_profile_with_hpr_id PASSED [ 46%]
backend\tests\test_models_doctor.py::test_doctor_user_bidirectional_relationship PASSED [ 48%]
backend\tests\test_models_doctor.py::test_doctor_profile_cascade_deletion PASSED [ 50%]
backend\tests\test_models_doctor.py::test_duplicate_registration_number_constraint PASSED [ 51%]
backend\tests\test_models_doctor.py::test_duplicate_hpr_id_constraint PASSED [ 53%]
backend\tests\test_models_lab.py::test_create_lab_facility_with_hfr_id PASSED [ 54%]
backend\tests\test_models_lab.py::test_lab_user_bidirectional_relationship PASSED [ 56%]
backend\tests\test_models_lab.py::test_lab_facility_cascade_deletion PASSED [ 57%]
backend\tests\test_models_lab.py::test_duplicate_license_number_constraint PASSED [ 59%]
backend\tests\test_models_lab.py::test_duplicate_hfr_id_constraint PASSED [ 60%]
backend\tests\test_models_patient.py::test_create_patient_profile_with_abha PASSED [ 62%]
backend\tests\test_models_patient.py::test_patient_user_bidirectional_relationship PASSED [ 63%]
backend\tests\test_models_patient.py::test_patient_profile_cascade_deletion PASSED [ 65%]
backend\tests\test_models_patient.py::test_duplicate_abha_number_constraint PASSED [ 66%]
backend\tests\test_models_user.py::test_create_user_success PASSED       [ 68%]
backend\tests\test_models_user.py::test_user_unique_email_constraint PASSED [ 69%]
backend\tests\test_models_user.py::test_user_roles_assignment PASSED     [ 71%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_create_validation_success PASSED [ 72%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_invalid_hpr_id PASSED [ 74%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_invalid_experience_and_fee PASSED [ 75%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_response_from_orm PASSED [ 77%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_create_validation_success PASSED [ 78%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_invalid_hfr_id PASSED [ 80%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_invalid_pincode_and_email PASSED [ 81%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_response_from_orm PASSED [ 83%]
backend\tests\test_schemas_patient.py::test_user_create_validation_success PASSED [ 84%]
backend\tests\test_schemas_patient.py::test_user_create_invalid_email_failure PASSED [ 86%]
backend\tests\test_schemas_patient.py::test_patient_profile_abha_validation_success PASSED [ 87%]
backend\tests\test_schemas_patient.py::test_patient_profile_invalid_abha_number PASSED [ 89%]
backend\tests\test_schemas_patient.py::test_patient_profile_invalid_abha_address PASSED [ 90%]
backend\tests\test_schemas_patient.py::test_patient_profile_invalid_pincode PASSED [ 92%]
backend\tests\test_schemas_patient.py::test_patient_profile_response_from_orm PASSED [ 93%]
backend\tests\test_seeder.py::test_seed_database_success PASSED          [ 95%]
backend\tests\test_seeder.py::test_seed_database_idempotent PASSED       [ 96%]
backend\tests\test_seeder.py::test_seed_database_reset_mode PASSED       [ 98%]
backend\tests\test_seeder.py::test_seeded_entities_relationship_integrity PASSED [100%]

============================= 66 passed in 17.15s =============================
```

---

## 4. Key Metrics & Progress

- **Commits Added:** 10 micro-commits
- **Total Repository Commits:** 99
- **Automated Tests:** 66 passed / 0 failed (100% pass rate)
- **API Surface:** Full CRUD `/api/v1/patients/` operational
- **Week 2 Milestone:** **COMPLETED** (`v0.1.0-alpha.w2`)
