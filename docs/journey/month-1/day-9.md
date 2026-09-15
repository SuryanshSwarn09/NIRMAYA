# Day 9: Initial Alembic Migrations, Database Indexes & Synthetic Clinical Fixtures

**Date:** September 16, 2026  
**Milestone:** 02-04 (Week 2: Database Schemas & Migrations)  
**Focus Area:** Alembic Schema Migration Generation, Composite Indexes, Foreign Key Cascade Integrity, Synthetic Healthcare Fixtures (ABHA, HPR, HFR), Idempotent Async Seeder Engine, and CLI Seeding Tooling

---

## 1. Objectives

Following the definition of the four core relational entities (`User`, `PatientProfile`, `DoctorProfile`, `DiagnosticLabFacility`) across Days 7 and 8, Day 9 delivers the persistence infrastructure and synthetic data ecosystem:
1. **Initial Alembic Schema Migration (`0001_initial_core_schema`):** Canonical migration capturing table definitions, types, foreign key cascades (`ondelete="CASCADE"`), unique constraints, and search indexes across all core entities.
2. **Synthetic Clinical Fixtures (`backend/app/db/fixtures.py`):** Authentic Indian healthcare data fixtures compliant with HL7 FHIR R4, ABDM 14-digit ABHA IDs (`91-XXXX-XXXX-XXXX`), Healthcare Professional Registry (`@hpr.abdm`), and Health Facility Registry (`IN-STATE-HFR-XXXXXX`).
3. **Asynchronous Seeder Service (`backend/app/db/seeder.py`):** Idempotent database seeder supporting safe re-runs and transactional reset (`--reset`) clearing entities in reverse dependency order.
4. **CLI Seeder Runner (`scripts/seed-db.py`):** Interactive terminal utility with colored telemetry summaries and pre-flight table initialization options.
5. **System Diagnostic Integration (`scripts/doctor.py`):** Integrated migration revision discovery and seeder CLI presence checks into the pre-flight doctor validator.
6. **Automated Test Coverage:** Unit and integration tests for migration upgrade/downgrade lifecycles and seeder idempotency, elevating backend test coverage to **58 passing tests**.

---

## 2. Engineering Work Completed

### 1. Canonical Alembic Revision (`backend/alembic/versions/2026_09_16_0001_initial_core_schema.py`)
- Created migration `0001_initial_core_schema` with comprehensive `upgrade()` and `downgrade()` methods.
- Supported tables:
  - `user`: Columns for email, full name, phone number, role, Supabase UID, active/verified booleans.
  - `patient_profile`: Demographic attributes, blood group, address, emergency contact, `abha_number` (unique), and `abha_address` (unique).
  - `doctor_profile`: Medical council licensing, specialty, qualifications, experience, fees, teleconsult flag, and `hpr_id` (unique).
  - `diagnostic_lab_facility`: Facility name, licensing, NABL/CAP accreditation, contact details, address, test catalog, and `hfr_id` (unique).
- Configured indexes for fast clinical lookups on `city`, `specialty`, `role`, and unique identifiers.

### 2. Alembic Environment Hardening (`backend/alembic/env.py`, `backend/alembic.ini`)
- Fixed script location pathing to `%(here)s/alembic` to permit CLI invocation from any directory.
- Added support for programmatic and environment variable database URL overrides (`ALEMBIC_DATABASE_URL`).
- Enabled `render_as_batch=True` for SQLite engines, ensuring SQLite test environments handle foreign key modifications gracefully.

### 3. Synthetic Clinical Fixtures (`backend/app/db/fixtures.py`)
- Standardized test fixtures for:
  - 1 System Administrator account (`admin@nirmaya.health`).
  - 3 Patients (Arun Patel, Meera Nair, Priya Sharma) with valid ABHA numbers (`91-1029-3847-5610`, etc.) and `@abdm` handles across Ahmedabad, Kochi, and Bengaluru.
  - 3 Specialist Doctors (Cardiology, Pediatrics, Neurology) with state medical council registration numbers and `@hpr.abdm` handles.
  - 3 Diagnostic Labs (Apollo Diagnostics, Metropolis Healthcare, Thyrocare) with NABL/CAP accreditations and `@hfr` IDs.

### 4. Idempotent Async Seeder Engine (`backend/app/db/seeder.py`)
- `seed_database(session, reset=False)`:
  - Validates existing records by unique email/identifier before insertion.
  - Implements safe rollback and flush points for parent-child relationship linking.
  - Returns detailed telemetry counts of seeded and cleared records.
- `clear_database(session)`:
  - Safely truncates tables in reverse cascade dependency order (`diagnostic_lab_facility` -> `doctor_profile` -> `patient_profile` -> `user`).

### 5. Seeder CLI Runner (`scripts/seed-db.py`)
- Command-line runner supporting:
  - `--reset`: Clears existing records before seeding.
  - `--init-tables`: Auto-initializes schema tables if missing.
  - `--db-url`: Database connection URL override.
  - Colored ANSI execution summaries and diagnostic tips.

### 6. System Diagnostic Validator (`scripts/doctor.py`)
- Added `check_database_migrations_and_seeder()` verifying discovery of active migration revisions and CLI seeder tool presence.

### 7. Automated Test Suite Expansion (`backend/tests/`)
- `test_migrations.py` (2 tests): Verified Alembic head resolution, upgrade table creation, column inspection, and downgrade cleanup.
- `test_seeder.py` (4 tests): Verified seeder insertion counts, idempotency upon consecutive executions, reset mode behavior, and cross-entity relationship navigation with `selectinload`.

---

## 3. Verification & Build Results

### Pre-Flight Doctor Verification (`scripts/doctor.py`):
```text
================================================================
       NIRMAYA System Diagnostic & Pre-Flight Validator         
================================================================

[Python Environment]
  Version: 3.12.0
  Status:  PASS (>= 3.11 compatible)

[Node.js & NPM Toolchain]
  Node.js: v24.13.1 (PASS)

[Backend Dependencies & Venv]
  Venv:    FOUND (E:\NIRMAYA\backend\.venv)
  Package: fastapi      -> INSTALLED
  Package: pydantic     -> INSTALLED
  Package: sqlalchemy   -> INSTALLED
  Package: alembic      -> INSTALLED
  Package: asyncpg      -> INSTALLED
  Package: pytest       -> INSTALLED
  Package: httpx        -> INSTALLED

[Alembic Migrations & Database Seeder]
  Migrations:  1 revision(s) found
    - 2026_09_16_0001_initial_core_schema
  Seeder CLI:  PRESENT (seed-db.py)

----------------------------------------------------------------
[OK] NIRMAYA Pre-Flight Check PASSED! Ready for development.
```

### Full Automated Pytest Suite (`58/58 tests passing` in 16.09s):
```text
backend\tests\test_db_base.py::test_declarative_base_tablename_derivation PASSED [  1%]
backend\tests\test_db_base.py::test_uuid_primary_key_mixin_schema PASSED [  3%]
backend\tests\test_db_base.py::test_timestamp_mixin_schema PASSED        [  5%]
backend\tests\test_db_base.py::test_entity_persistence_with_mixins PASSED [  6%]
backend\tests\test_db_session.py::test_check_db_health_success_with_sqlite PASSED [  8%]
backend\tests\test_db_session.py::test_check_db_health_failure_handling PASSED [ 10%]
backend\tests\test_db_session.py::test_get_db_session_generator_lifecycle PASSED [ 12%]
backend\tests\test_db_session.py::test_get_db_session_rollback_on_exception PASSED [ 13%]
backend\tests\test_exceptions.py::test_app_exception_attributes PASSED   [ 15%]
backend\tests\test_exceptions.py::test_entity_not_found_exception PASSED [ 17%]
backend\tests\test_exceptions.py::test_permission_denied_exception PASSED [ 18%]
backend\tests\test_exceptions.py::test_not_found_error_payload_envelope PASSED [ 20%]
backend\tests\test_health.py::test_root_endpoint PASSED                  [ 22%]
backend\tests\test_health.py::test_health_check_payload_structure PASSED [ 24%]
backend\tests\test_health.py::test_database_health_probe_mock_healthy PASSED [ 25%]
backend\tests\test_health.py::test_performance_telemetry_header PASSED   [ 27%]
backend\tests\test_health.py::test_correlation_id_generation_and_propagation PASSED [ 29%]
backend\tests\test_health.py::test_security_headers_injection PASSED     [ 31%]
backend\tests\test_health.py::test_404_error_envelope_formatting PASSED  [ 32%]
backend\tests\test_meta.py::test_meta_capabilities_endpoint PASSED       [ 34%]
backend\tests\test_migrations.py::test_migration_revision_head PASSED    [ 36%]
backend\tests\test_migrations.py::test_migration_upgrade_and_downgrade_lifecycle PASSED [ 37%]
backend\tests\test_models_doctor.py::test_create_doctor_profile_with_hpr_id PASSED [ 39%]
backend\tests\test_models_doctor.py::test_doctor_user_bidirectional_relationship PASSED [ 41%]
backend\tests\test_models_doctor.py::test_doctor_profile_cascade_deletion PASSED [ 43%]
backend\tests\test_models_doctor.py::test_duplicate_registration_number_constraint PASSED [ 44%]
backend\tests\test_models_doctor.py::test_duplicate_hpr_id_constraint PASSED [ 46%]
backend\tests\test_models_lab.py::test_create_lab_facility_with_hfr_id PASSED [ 48%]
backend\tests\test_models_lab.py::test_lab_user_bidirectional_relationship PASSED [ 50%]
backend\tests\test_models_lab.py::test_lab_facility_cascade_deletion PASSED [ 51%]
backend\tests\test_models_lab.py::test_duplicate_license_number_constraint PASSED [ 53%]
backend\tests\test_models_lab.py::test_duplicate_hfr_id_constraint PASSED [ 55%]
backend\tests\test_models_patient.py::test_create_patient_profile_with_abha PASSED [ 56%]
backend\tests\test_models_patient.py::test_patient_user_bidirectional_relationship PASSED [ 58%]
backend\tests\test_models_patient.py::test_patient_profile_cascade_deletion PASSED [ 60%]
backend\tests\test_models_patient.py::test_duplicate_abha_number_constraint PASSED [ 62%]
backend\tests\test_models_user.py::test_create_user_success PASSED       [ 63%]
backend\tests\test_models_user.py::test_user_unique_email_constraint PASSED [ 65%]
backend\tests\test_models_user.py::test_user_roles_assignment PASSED     [ 67%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_create_validation_success PASSED [ 68%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_invalid_hpr_id PASSED [ 70%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_invalid_experience_and_fee PASSED [ 72%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_response_from_orm PASSED [ 74%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_create_validation_success PASSED [ 75%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_invalid_hfr_id PASSED [ 77%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_invalid_pincode_and_email PASSED [ 79%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_response_from_orm PASSED [ 81%]
backend\tests\test_schemas_patient.py::test_user_create_validation_success PASSED [ 82%]
backend\tests\test_schemas_patient.py::test_user_create_invalid_email_failure PASSED [ 84%]
backend\tests\test_schemas_patient.py::test_patient_profile_abha_validation_success PASSED [ 86%]
backend\tests\test_schemas_patient.py::test_patient_profile_invalid_abha_number PASSED [ 87%]
backend\tests\test_schemas_patient.py::test_patient_profile_invalid_abha_address PASSED [ 89%]
backend\tests\test_schemas_patient.py::test_patient_profile_invalid_pincode PASSED [ 91%]
backend\tests\test_schemas_patient.py::test_patient_profile_response_from_orm PASSED [ 93%]
backend\tests\test_seeder.py::test_seed_database_success PASSED          [ 94%]
backend\tests\test_seeder.py::test_seed_database_idempotent PASSED       [ 96%]
backend\tests\test_seeder.py::test_seed_database_reset_mode PASSED       [ 98%]
backend\tests\test_seeder.py::test_seeded_entities_relationship_integrity PASSED [100%]

============================= 58 passed in 16.09s =============================
```

---

## 4. Key Metrics & Progress

- **Commits Added:** 11 micro-commits
- **Total Repository Commits:** 89
- **Automated Tests:** 58 passed / 0 failed (100% pass rate)
- **Migrations:** Revision `0001_initial_core_schema` verified
- **Seeded Entities:** 10 users, 3 patient profiles, 3 doctor profiles, 3 lab facilities (19 records total)
- **Standards Complied:** HL7 FHIR R4, ABDM ABHA IDs, ABDM HPR Registry, ABDM HFR Registry
