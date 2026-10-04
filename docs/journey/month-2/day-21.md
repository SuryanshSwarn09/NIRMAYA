# Day 21: Milestone 05-01: Clinical Condition & Problem List Schemas

**Date:** October 5, 2026  
**Milestone:** 05-01  
**Primary Commit:** `fdfa75c: test(conditions): add unit and integration test suite for condition management and fhir export`

---

## 1. Objectives

Day 21 kicks off **Month 2** of Project NIRMAYA, initiating **Milestone 05: Clinical Conditions, Observations, SOAP Notes & Lab Integration**. The primary objective was establishing the longitudinal clinical problem list infrastructure, enabling practitioners and patients to record, query, update, and resolve diagnosed conditions using international clinical terminology systems (SNOMED-CT and ICD-10) with full HL7 FHIR Release 4 Condition resource serialization.

---

## 2. Engineering Work Completed

### Clinical Condition Enums & Status Lifecycles
- Defined HL7 FHIR R4 aligned enumerations in `backend/app/models/enums.py`:
  - `ClinicalStatus`: `active`, `recurrence`, `relapse`, `inactive`, `remission`, `resolved` (`http://terminology.hl7.org/CodeSystem/condition-clinical`).
  - `VerificationStatus`: `unconfirmed`, `provisional`, `differential`, `confirmed`, `refuted`, `entered-in-error` (`http://terminology.hl7.org/CodeSystem/condition-ver-status`).
  - `ConditionCategory`: `problem-list-item`, `encounter-diagnosis`, `chronic-condition` (`http://terminology.hl7.org/CodeSystem/condition-category`).
  - `ConditionSeverity`: `mild`, `moderate`, `severe` (mapped to SNOMED-CT concepts `255604002`, `6736007`, `24484000`).

### Relational Entity Model & Alembic Migration
- Created `ClinicalCondition` SQLAlchemy 2.0 entity in `backend/app/models/condition.py`:
  - Foreign key to `patient_profile.id` (`ondelete="CASCADE"`).
  - Optional linkage to `appointment.id` (`encounter_id`, `ondelete="SET NULL"`).
  - Optional recorder doctor `doctor_profile.id` (`ondelete="SET NULL"`).
  - Codings: `code_coding_system`, `code_value`, `code_display`, `body_site`.
  - Clinical timeline: `onset_date_time`, `abatement_date_time`, `recorded_date`.
- Created Alembic database migration `2026_10_05_0004_conditions_schema.py` (`down_revision = "0003_slot_concurrency_and_hold_fields"`).
- Updated `backend/tests/test_migrations.py` to assert new migration head and verify table schema.

### Pydantic v2 Domain Schemas
- Implemented `ConditionCreate`, `ConditionUpdate`, `ConditionResponse`, and `ConditionFilter` in `backend/app/schemas/condition.py`.
- Added timeline cross-field validators ensuring `abatement_date_time >= onset_date_time`.

### HL7 FHIR Release 4 Serialization
- Defined `FHIRCondition` and `FHIRAnnotation` models in `backend/app/fhir/schemas.py`.
- Implemented `to_fhir_condition` transformer in `backend/app/fhir/transformers.py`, mapping relational condition entities to canonical FHIR R4 `Condition` JSON with complete terminology codings, status codes, and clinical annotations.

### Service Layer & REST API Endpoints
- Implemented `backend/app/services/condition.py` handling condition recording, status updates (auto-setting UTC abatement timestamps on condition resolution), filtering, and deletion.
- Mounted REST endpoints in `backend/app/api/v1/endpoints/conditions.py`:
  - `POST /api/v1/patients/{patient_id}/conditions`: Record new condition onto patient's problem list.
  - `GET /api/v1/patients/{patient_id}/conditions`: Retrieve paginated problem list with status/category filters.
  - `GET /api/v1/conditions/{condition_id}`: Retrieve detailed condition record.
  - `PATCH /api/v1/conditions/{condition_id}`: Update condition status, severity, or notes.
  - `GET /api/v1/conditions/{condition_id}/fhir`: Export condition as HL7 FHIR R4 Condition resource.
  - `DELETE /api/v1/conditions/{condition_id}`: Delete condition (restricted to doctors and admins).

### Concurrency Hardening & Appointment Stability
- Hardened `Appointment` model with an explicit table-level `UniqueConstraint("slot_id")` and resolved SQLAlchemy 1-to-1 displacement in `book_appointment`, ensuring deterministic concurrency resolution under high contention.

---

## 3. Verification & Outcome

- **Unit & Integration Suite:** 9 dedicated tests in `backend/tests/test_conditions.py` passing 100%.
- **Full Backend Suite:** 160 tests passing across all 29 test suites in 21.58s (100% pass rate).
- **Alembic Migrations:** Clean upgrade to head `0004_conditions_schema` and downgrade verified.
