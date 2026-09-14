# Day 8: Provider & Diagnostic Entities: DoctorProfile (HPR) & DiagnosticLabFacility (HFR)

**Date:** September 15, 2026  
**Milestone:** 02-03 (Week 2: Database Schemas & Migrations)  
**Focus Area:** Provider Clinical Credentials, State Medical Council Licensing, ABDM Healthcare Professional Registry (HPR), Diagnostic Center Facilities, NABL/CAP Lab Accreditation, ABDM Health Facility Registry (HFR), Pydantic v2 Schemas, and 100% Test Automation

---

## 1. Objectives

Following the implementation of the core User identity and PatientProfile on Day 7, Day 8 constructs the remaining two pillars of NIRMAYA's tripartite healthcare ecosystem:
1. **Clinical & Accreditation Enums (`app/models/enums.py`):** Define `MedicalSpecialty` (14 clinical specialties aligned with SNOMED-CT / FHIR `PractitionerRole`) and `LabAccreditation` (`NABL`, `CAP`, `ISO 15189`, `State Government Registered`).
2. **Healthcare Provider Entity (`app/models/doctor.py`):** Model doctor clinical credentials, state medical council licensing, qualifications, years of clinical experience, consultation fee, teleconsultation availability, and ABDM Healthcare Professional Registry (`hpr_id` ending in `@hpr.abdm`).
3. **Diagnostic Testing Center Entity (`app/models/lab.py`):** Model accredited diagnostic facilities, NABL ISO 15189 compliance, facility address, administrative contact person, supported diagnostic test catalog, and ABDM Health Facility Registry (`hfr_id` in `IN-STATE-HFR-XXXXXX` format).
4. **Relational Integrity & Cascade Linkage:** Wire bidirectional 1-to-1 relationships between `User` and `DoctorProfile` (`user.doctor_profile`), and between `User` and `DiagnosticLabFacility` (`user.lab_facility`) with `ondelete="CASCADE"`.
5. **Pydantic v2 Domain Schemas (`app/schemas/doctor.py`, `app/schemas/lab.py`):** Strict payload validation for onboarding doctors and laboratories, experience limits, fee validation, regex format validation for HPR and HFR identifiers, and ORM deserialization (`from_attributes=True`).
6. **Automated Pytest Coverage:** Unit test entity persistence, unique constraints, cascade deletion, and schema boundary validation, elevating test suite coverage to **52 passing tests**.

---

## 2. Engineering Work Completed

### 1. Clinical Specialties & Laboratory Accreditations (`backend/app/models/enums.py`)
- Created `MedicalSpecialty` enum (`General Medicine`, `Cardiology`, `Dermatology`, `Pediatrics`, `Orthopedics`, `Neurology`, `Gynecology`, `Oncology`, `Ophthalmology`, `Psychiatry`, `Radiology`, `Pathology`, `ENT`, `Other`).
- Created `LabAccreditation` enum (`NABL`, `CAP`, `ISO 15189`, `State Government Registered`, `Other`).

### 2. Doctor Profile Entity (`backend/app/models/doctor.py`)
- Extends `Base`, `UUIDPrimaryKeyMixin`, and `TimestampMixin`.
- Identity linkage: `user_id` mapped to `user.id` (`unique=True`, `ondelete="CASCADE"`).
- Regulatory licensing: `registration_number` (unique, indexed), `medical_council`.
- Clinical attributes: `specialty` (enum), `qualifications`, `experience_years`, `consultation_fee`, `hospital_affiliation`, `bio`, `is_available_for_teleconsult`.
- ABDM integration: `hpr_id` (unique, indexed, nullable).

### 3. Diagnostic Lab Facility Entity (`backend/app/models/lab.py`)
- Extends `Base`, `UUIDPrimaryKeyMixin`, and `TimestampMixin`.
- Identity linkage: `user_id` mapped to `user.id` (`unique=True`, `ondelete="CASCADE"`).
- Facility licensing: `facility_name` (indexed), `license_number` (unique, indexed).
- Quality standards: `accreditation` (enum), `accreditation_number`, `is_nabl_certified`.
- Location & administration: `contact_person`, `contact_phone`, `contact_email`, `address_line`, `city` (indexed), `state`, `pincode`, `supported_tests`.
- ABDM integration: `hfr_id` (unique, indexed, nullable).

### 4. User Relational Wiring & Exports (`backend/app/models/user.py`, `backend/app/models/__init__.py`)
- Configured bidirectional 1-to-1 relationships on `User`:
  - `user.doctor_profile` <-> `doctor_profile.user`
  - `user.lab_facility` <-> `diagnostic_lab_facility.user`
- Registered and re-exported all entities in `app.models`, automatically discovered by `alembic/env.py`.

### 5. Pydantic v2 Provider & Lab Schemas (`backend/app/schemas/doctor.py`, `app/schemas/lab.py`, `app/schemas/__init__.py`)
- `DoctorProfileBase`, `DoctorProfileCreate`, `DoctorProfileUpdate`, `DoctorProfileResponse`.
  - Enforced HPR regex pattern `^[a-zA-Z0-9._]{3,40}@hpr\.abdm$`.
  - Enforced experience (`0 <= experience_years <= 75`) and non-negative consultation fees.
- `DiagnosticLabFacilityBase`, `DiagnosticLabFacilityCreate`, `DiagnosticLabFacilityUpdate`, `DiagnosticLabFacilityResponse`.
  - Enforced HFR regex pattern `^IN-[A-Z]{2}-HFR-\d{6}$`.
  - Enforced Indian 6-digit PIN code (`^[1-9][0-9]{5}$`) and standard email format (`EmailStr`).

### 6. Automated Pytest Test Coverage (`backend/tests/`)
- `test_models_doctor.py` (5 tests): Verified DoctorProfile persistence, HPR ID indexing, bidirectional relationship navigation, cascade deletion, and unique constraints.
- `test_models_lab.py` (5 tests): Verified DiagnosticLabFacility persistence, HFR ID indexing, relationship navigation, cascade deletion, and unique constraints.
- `test_schemas_doctor_lab.py` (8 tests): Validated Doctor and Lab create schemas, invalid HPR/HFR rejection, PIN code validation, and nested ORM entity response serialization.

---

## 3. Verification & Build Results

### Automated Pytest Suite (`52/52 tests passing` in 14.89s):
```text
backend\tests\test_db_base.py::test_declarative_base_tablename_derivation PASSED [  1%]
backend\tests\test_db_base.py::test_uuid_primary_key_mixin_schema PASSED [  3%]
backend\tests\test_db_base.py::test_timestamp_mixin_schema PASSED        [  5%]
backend\tests\test_db_base.py::test_entity_persistence_with_mixins PASSED [  7%]
backend\tests\test_db_session.py::test_check_db_health_success_with_sqlite PASSED [  9%]
backend\tests\test_db_session.py::test_check_db_health_failure_handling PASSED [ 11%]
backend\tests\test_db_session.py::test_get_db_session_generator_lifecycle PASSED [ 13%]
backend\tests\test_db_session.py::test_get_db_session_rollback_on_exception PASSED [ 15%]
backend\tests\test_exceptions.py::test_app_exception_attributes PASSED   [ 17%]
backend\tests\test_exceptions.py::test_entity_not_found_exception PASSED [ 19%]
backend\tests\test_exceptions.py::test_permission_denied_exception PASSED [ 21%]
backend\tests\test_exceptions.py::test_not_found_error_payload_envelope PASSED [ 23%]
backend\tests\test_health.py::test_root_endpoint PASSED                  [ 25%]
backend\tests\test_health.py::test_health_check_payload_structure PASSED [ 26%]
backend\tests\test_health.py::test_database_health_probe_mock_healthy PASSED [ 28%]
backend\tests\test_health.py::test_performance_telemetry_header PASSED   [ 30%]
backend\tests\test_health.py::test_correlation_id_generation_and_propagation PASSED [ 32%]
backend\tests\test_health.py::test_security_headers_injection PASSED     [ 34%]
backend\tests\test_health.py::test_404_error_envelope_formatting PASSED  [ 36%]
backend\tests\test_meta.py::test_meta_capabilities_endpoint PASSED       [ 38%]
backend\tests\test_models_doctor.py::test_create_doctor_profile_with_hpr_id PASSED [ 40%]
backend\tests\test_models_doctor.py::test_doctor_user_bidirectional_relationship PASSED [ 42%]
backend\tests\test_models_doctor.py::test_doctor_profile_cascade_deletion PASSED [ 44%]
backend\tests\test_models_doctor.py::test_duplicate_registration_number_constraint PASSED [ 46%]
backend\tests\test_models_doctor.py::test_duplicate_hpr_id_constraint PASSED [ 48%]
backend\tests\test_models_lab.py::test_create_lab_facility_with_hfr_id PASSED [ 50%]
backend\tests\test_models_lab.py::test_lab_user_bidirectional_relationship PASSED [ 51%]
backend\tests\test_models_lab.py::test_lab_facility_cascade_deletion PASSED [ 53%]
backend\tests\test_models_lab.py::test_duplicate_license_number_constraint PASSED [ 55%]
backend\tests\test_models_lab.py::test_duplicate_hfr_id_constraint PASSED [ 57%]
backend\tests\test_models_patient.py::test_create_patient_profile_with_abha PASSED [ 59%]
backend\tests\test_models_patient.py::test_patient_user_bidirectional_relationship PASSED [ 61%]
backend\tests\test_models_patient.py::test_patient_profile_cascade_deletion PASSED [ 63%]
backend\tests\test_models_patient.py::test_duplicate_abha_number_constraint PASSED [ 65%]
backend\tests\test_models_user.py::test_create_user_success PASSED       [ 67%]
backend\tests\test_models_user.py::test_user_unique_email_constraint PASSED [ 69%]
backend\tests\test_models_user.py::test_user_roles_assignment PASSED     [ 71%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_create_validation_success PASSED [ 73%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_invalid_hpr_id PASSED [ 75%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_invalid_experience_and_fee PASSED [ 76%]
backend\tests\test_schemas_doctor_lab.py::test_doctor_profile_response_from_orm PASSED [ 78%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_create_validation_success PASSED [ 80%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_invalid_hfr_id PASSED [ 82%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_invalid_pincode_and_email PASSED [ 84%]
backend\tests\test_schemas_doctor_lab.py::test_lab_facility_response_from_orm PASSED [ 86%]
backend\tests\test_schemas_patient.py::test_user_create_validation_success PASSED [ 88%]
backend\tests\test_schemas_patient.py::test_user_create_invalid_email_failure PASSED [ 90%]
backend\tests\test_schemas_patient.py::test_patient_profile_abha_validation_success PASSED [ 92%]
backend\tests\test_schemas_patient.py::test_patient_profile_invalid_abha_number PASSED [ 94%]
backend\tests\test_schemas_patient.py::test_patient_profile_invalid_abha_address PASSED [ 96%]
backend\tests\test_schemas_patient.py::test_patient_profile_invalid_pincode PASSED [ 98%]
backend\tests\test_schemas_patient.py::test_patient_profile_response_from_orm PASSED [100%]

============================= 52 passed in 14.89s =============================
```

---

## 4. Key Metrics & Progress

- **Commits Added:** 10 micro-commits
- **Total Repository Commits:** 78
- **Automated Tests:** 52 passed / 0 failed (100% pass rate)
- **Entities Modeled:** `User`, `PatientProfile`, `DoctorProfile`, `DiagnosticLabFacility`
- **Standards Aligned:** HL7 FHIR R4, ABDM HPR Registry, ABDM HFR Registry, NABL ISO 15189
