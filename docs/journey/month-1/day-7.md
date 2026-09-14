# Day 7: Core Relational Entities: User, Role & Patient Profile with ABHA

**Date:** September 14, 2026  
**Milestone:** 02-02 (Week 2: Database Schemas & Migrations)  
**Focus Area:** Relational Domain Modeling, Clinical Enums, User & PatientProfile Entities, 1-to-1 Cascade Relationships, ABHA Identity Integration, Pydantic v2 Schemas, and Automated Test Coverage

---

## 1. Objectives

Following the establishment of the asynchronous database engine and Alembic scaffold on Day 6, Day 7 implements NIRMAYA's foundational domain entities:
1. **Clinical & Authorization Enums (`app/models/enums.py`):** Define `UserRole` (`patient`, `doctor`, `lab`, `admin`), `Gender` (aligned with HL7 FHIR R4 `http://hl7.org/fhir/administrative-gender`), and `BloodGroup` (ABO/Rh clinical classifications).
2. **User Identity Entity (`app/models/user.py`):** Model user accounts with unique email, full name, phone number, role enum, Supabase Auth integration (`supabase_uid`), and active/verification status.
3. **Patient Clinical Profile (`app/models/patient.py`):** Model longitudinal patient demographics (Date of Birth, Gender, Blood Group, Residential Address, Emergency Contact) and national health identifiers (`abha_number` in `XX-XXXX-XXXX-XXXX` format, and `abha_address` handle in `<username>@abdm` format).
4. **Relational Integrity & Cascade Deletion:** Implement bidirectional 1-to-1 relationships between `User` and `PatientProfile` with foreign key constraints and `ondelete="CASCADE"`.
5. **Pydantic v2 Domain Schemas:** Provide strict validation for user registration, patient profile onboarding, ABHA formatting, and ORM-to-JSON serialization (`from_attributes=True`).
6. **Automated Unit Testing:** Establish tests for entity creation, unique constraints, cascade deletion, and schema validation (expanding the backend test suite to 34 passing tests).

---

## 2. Engineering Work Completed

### 1. Clinical & Authorization Enums (`backend/app/models/enums.py`)
- Created `UserRole` (`PATIENT`, `DOCTOR`, `LAB`, `ADMIN`).
- Created `Gender` (`MALE`, `FEMALE`, `OTHER`, `UNKNOWN`) reflecting HL7 FHIR administrative gender codes.
- Created `BloodGroup` (`A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-`, `unknown`).

### 2. User Relational Entity (`backend/app/models/user.py`)
- Extends `Base`, `UUIDPrimaryKeyMixin`, and `TimestampMixin`.
- Columns: `email` (unique, indexed), `full_name`, `phone_number` (indexed), `role` (enum, indexed), `supabase_uid` (unique, indexed), `is_active`, `is_verified`.
- Bidirectional 1-to-1 relationship to `PatientProfile` with `cascade="all, delete-orphan"`.

### 3. Patient Profile Entity (`backend/app/models/patient.py`)
- Extends `Base`, `UUIDPrimaryKeyMixin`, and `TimestampMixin`.
- Foreign key: `user_id` mapped to `user.id` (`unique=True`, `ondelete="CASCADE"`).
- Clinical demographics: `date_of_birth`, `gender`, `blood_group`.
- Residential address: `address_line`, `city` (indexed), `state`, `pincode`.
- Emergency contact: `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`.
- ABDM identifiers: `abha_number` (17 chars unique, indexed), `abha_address` (100 chars unique, indexed).

### 4. Entity Registration & Alembic Reflection (`backend/app/models/__init__.py`, `backend/alembic/env.py`)
- Re-exported `User`, `PatientProfile`, `UserRole`, `Gender`, and `BloodGroup` in `app.models`.
- Imported `app.models` in `alembic/env.py` ensuring `Base.metadata` immediately reflects both tables during autogenerate and migrations.

### 5. Pydantic v2 Domain Schemas (`backend/app/schemas/user.py`, `app/schemas/patient.py`, `app/schemas/__init__.py`)
- `UserBase`, `UserCreate`, `UserUpdate`, `UserResponse`.
- `PatientProfileBase`, `PatientProfileCreate`, `PatientProfileUpdate`, `PatientProfileResponse`.
- Enforced regex patterns for phone numbers, Indian 6-digit PIN codes (`^[1-9][0-9]{5}$`), 14-digit hyphenated ABHA IDs (`^\d{2}-\d{4}-\d{4}-\d{4}$`), and `@abdm` health handles (`^[a-zA-Z0-9._]{3,30}@abdm$`).

### 6. Automated Pytest Test Coverage (`backend/tests/`)
- `test_models_user.py`: Verified successful User persistence, default `PATIENT` role, unique email enforcement, and role assignment.
- `test_models_patient.py`: Verified PatientProfile creation with ABHA fields, bidirectional navigation (`user.patient_profile` and `profile.user`), cascade deletion, and unique constraint on `abha_number`.
- `test_schemas_patient.py`: Validated payload parsing, invalid email rejection, ABHA format enforcement, pincode constraints, and ORM entity serialization with nested user data.

---

## 3. Verification & Build Results

### Automated Pytest Suite (`34/34 tests passing` in 14.5s):
```text
tests/test_db_base.py (4 tests) .................. PASSED
tests/test_db_session.py (4 tests) ............... PASSED
tests/test_exceptions.py (4 tests) ............... PASSED
tests/test_health.py (7 tests) ................... PASSED
tests/test_meta.py (1 test) ...................... PASSED
tests/test_models_user.py (3 tests) .............. PASSED
tests/test_models_patient.py (4 tests) ........... PASSED
tests/test_schemas_patient.py (7 tests) .......... PASSED

============================= 34 passed in 14.52s =============================
```

### Pre-flight Diagnostic Doctor (`python scripts/doctor.py`):
- All 8 package checks passed (`fastapi`, `pydantic`, `sqlalchemy`, `alembic`, `asyncpg`, `email-validator`, `pytest`, `httpx`).
- 0 warnings, environment verified clean.

---

## 4. Next Daily Milestone: Day 8 (Wed)
- **Focus:** `feat(models): create doctor and diagnostic lab entity models`
- **Scope:** Define SQLAlchemy 2.0 relational models for `DoctorProfile` (medical council registration number, specialty, experience years, consultation fee, bio) and `DiagnosticLabFacility` (NABL accreditation number, facility name, address, contact person), with foreign key relationships and Pydantic v2 schemas.
