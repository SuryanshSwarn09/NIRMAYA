# Day 24: Milestone 05-04: Diagnostic Lab Orders & Results (Service Requisitions & DiagnosticReport)

**Date:** October 7, 2026  
**Milestone:** 05-04  
**Primary Commit:** `c41bcec: feat(frontend): integrate diagnostic order pad and lab reports viewer in portals`

---

## 1. Objectives

Day 24 advances Milestone 05 with the implementation of **Diagnostic Lab Orders & Results (Service Requisitions & DiagnosticReport)**. In modern clinical workflows, the diagnostic loop connects the attending clinician ordering laboratory investigations to the diagnostic laboratory processing specimens and publishing verified reports:
1. **Clinician Diagnostic Orders (`ServiceRequest`):** Formal requisitions for clinical laboratory procedures (e.g. Fasting Lipid Panel LOINC `24331-1`, Hemoglobin A1c LOINC `4548-4`, Complete Blood Count LOINC `58410-2`), complete with specimen directives, fasting prerequisites, priority levels, and clinical indications.
2. **Pathology Results Documentation (`DiagnosticReport`):** Official laboratory reports aggregating quantitative observations, specimen metadata, pathologist clinical conclusions, and ICD-10 diagnostic coding (`E78.5`).
3. **Observation Linkage & Automated Abnormal Evaluation:** Dynamic association of calibrated quantitative and qualitative `Observation` entities with automated evaluation of abnormal physiological parameters (`HIGH`, `LOW`, `CRITICALLY_HIGH`, `CRITICALLY_LOW`, `ABNORMAL`).
4. **Requisition Lifecycle Automation:** Automatic fulfillment of the initiating `DiagnosticOrder` (`status = completed`) upon publication of a verified `DiagnosticReport`.

The engineering goals for Day 24 were:
1. Define comprehensive diagnostic enums and database models for diagnostic orders and diagnostic reports with bidirectional relationships to patients, doctors, appointments, and observations.
2. Generate and verify database schema migrations with Alembic (`0007_diagnostics_schema`) using SQLite batch mode for foreign-key consistency.
3. Build bidirectional serialization into HL7 FHIR Release 4 `ServiceRequest` and `DiagnosticReport` resources conforming to ABDM NRCeS profiles.
4. Implement a robust service layer with transactional order lifecycle progression and automated abnormal range evaluation.
5. Expose REST endpoints supporting creation, paginated listing, partial updates, and FHIR export for orders and reports.
6. Build a complete unit and integration test suite verifying authorization, abnormal auto-flagging, order fulfillment, and FHIR generation.
7. Integrate the diagnostic ordering and reports engine across doctor, lab, and patient portals in Next.js 15.

---

## 2. Engineering Work Completed

### Diagnostic Enums & Domain Models
- Added diagnostic enums to `backend/app/models/enums.py`:
  - `ServiceRequestStatus`: `draft`, `active`, `on-hold`, `revoked`, `completed`, `entered-in-error`, `unknown`.
  - `ServiceRequestIntent`: `proposal`, `plan`, `directive`, `order`, `original-order`, `reflex-order`, `filler-order`, `instance-order`, `option`.
  - `ServiceRequestPriority`: `routine`, `urgent`, `asap`, `stat`.
  - `DiagnosticReportStatus`: `registered`, `partial`, `preliminary`, `final`, `amended`, `corrected`, `appended`, `cancelled`, `entered-in-error`, `unknown`.
  - `SpecimenType`: `blood`, `serum`, `plasma`, `urine`, `saliva`, `csf`, `biopsy`, `swab`, `other`.
- Created SQLAlchemy entities in `backend/app/models/diagnostic.py`:
  - `DiagnosticOrder`: Models doctor lab requisitions (`diagnostic_order`), linking `patient_id`, `doctor_id`, and `encounter_id` with LOINC coding (`code_system`, `code_value`, `code_display`), `specimen_type`, `fasting_required`, and `clinical_notes`.
  - `DiagnosticReport`: Models published pathology reports (`diagnostic_report`), linking `patient_id`, `order_id`, `encounter_id`, `performer_doctor_id`, conclusion narrative, ICD-10 coding (`coded_diagnosis_icd10`), and `is_abnormal` flag.
  - Added `report_id` foreign key on `ClinicalObservation` with bidirectional `report` and `observations` relationship.

### Database Migration (`0007_diagnostics_schema`)
- Generated Alembic migration `backend/alembic/versions/2026_10_07_0007_diagnostics_schema.py` (`down_revision = "0006_soap_notes_schema"`).
- Implemented SQLite `batch_alter_table` on `clinical_observation` to safely introduce foreign key `report_id` without SQLite table reconstruction locks.
- Updated migration integrity tests in `backend/tests/test_migrations.py` validating head `0007_diagnostics_schema` across upgrade and downgrade lifecycles.

### Pydantic v2 Schemas & Validation
- Created schemas in `backend/app/schemas/diagnostic.py`:
  - `DiagnosticOrderCreate`, `DiagnosticOrderUpdate`, `DiagnosticOrderResponse`.
  - `DiagnosticReportCreate` (supporting `observation_ids`), `DiagnosticReportUpdate`, `DiagnosticReportResponse` (with nested `ClinicalObservationResponse` array).

### HL7 FHIR Release 4 Transformers
- Extended `backend/app/fhir/schemas.py` with `FHIRServiceRequest` and `FHIRDiagnosticReport`.
- Implemented transformers in `backend/app/fhir/transformers.py`:
  - `to_fhir_service_request`: Transforms `DiagnosticOrder` into FHIR R4 `ServiceRequest` resource with LOINC coding, priority, requester reference, subject reference, specimen metadata, and NRCeS StructureDefinition profile.
  - `to_fhir_diagnostic_report`: Transforms `DiagnosticReport` into FHIR R4 `DiagnosticReport` resource with `basedOn` ServiceRequest references, performer reference, subject reference, conclusion narrative, and nested `result` observation references.

### Service Layer & Automated Business Logic
- Implemented `DiagnosticService` in `backend/app/services/diagnostic.py`:
  - **Automated Abnormal Evaluation:** Evaluates all linked observations upon report creation; if any observation has interpretation `HIGH`, `LOW`, `CRITICALLY_HIGH`, `CRITICALLY_LOW`, or `ABNORMAL`, sets `report.is_abnormal = True`.
  - **Requisition Lifecycle Automation:** If a report references an initiating `order_id`, automatically updates the corresponding order's status to `ServiceRequestStatus.COMPLETED`.
  - **Observation Ownership Verification:** Ensures linked observation IDs belong strictly to the target patient.

### REST API Endpoints
- Mounted `backend/app/api/v1/endpoints/diagnostics.py`:
  - `POST /api/v1/patients/{patient_id}/diagnostic-orders`: Create doctor lab order.
  - `GET /api/v1/patients/{patient_id}/diagnostic-orders`: Query patient orders with status, priority, and encounter filters.
  - `GET /api/v1/diagnostic-orders/{order_id}`: Retrieve single order.
  - `PATCH /api/v1/diagnostic-orders/{order_id}`: Update order priority, status, or clinical notes.
  - `GET /api/v1/diagnostic-orders/{order_id}/fhir`: Export order as HL7 FHIR R4 `ServiceRequest` JSON.
  - `POST /api/v1/patients/{patient_id}/diagnostic-reports`: Create and publish diagnostic report linking observation IDs.
  - `GET /api/v1/patients/{patient_id}/diagnostic-reports`: Query patient reports with status, abnormal flag, and encounter filters.
  - `GET /api/v1/diagnostic-reports/{report_id}`: Retrieve single report with populated observations.
  - `GET /api/v1/diagnostic-reports/{report_id}/fhir`: Export report as HL7 FHIR R4 `DiagnosticReport` JSON.

### Next.js 15 Frontend Integration
- Updated `frontend/src/lib/api.ts` with diagnostic data models (`DiagnosticOrder`, `DiagnosticOrderCreate`, `DiagnosticReport`, `DiagnosticReportCreate`, enums) and typed client methods.
- **Doctor EMR Portal (`frontend/src/app/doctor/page.tsx`):**
  - Integrated Diagnostic Lab Requisition Pad (ServiceRequest) alongside SOAP notes and prescriptions.
  - Preloaded LOINC test catalogue (Lipid Panel `24331-1`, HbA1c `4548-4`, CBC `58410-2`, Creatinine & eGFR `38483-4`).
  - Added order priority selector, specimen options, fasting toggle, clinical indication input, and interactive HL7 FHIR `ServiceRequest` modal preview.
- **Diagnostic Lab Portal (`frontend/src/app/lab/page.tsx`):**
  - Added "Requisitions Queue" tab displaying pending clinician orders.
  - Added "Fulfill in LOINC Builder" action which prepopulates patient ABHA, test parameters, and links `order_id` into the generated report.
  - Linked `basedOn` ServiceRequest references in the live FHIR `DiagnosticReport` bundle.
- **Patient Health Vault (`frontend/src/app/patient/page.tsx`):**
  - Added "Diagnostic Lab Reports & Requisitions" card with dual-tab switcher (Reports vs Orders).
  - Displays pathologist conclusion, ICD-10 coding (`E78.5`), and calibrated observations with abnormal range badges.
  - Embedded FHIR R4 `DiagnosticReport` and `ServiceRequest` inspection modals.
- Validated with Next.js Turbopack: 11/11 routes prerendered with 0 errors.

---

## 3. Verification & Outcome

- **Diagnostic Test Suite:** 9/9 dedicated tests passing in `backend/tests/test_diagnostics.py` verifying order requisitions, report generation, observation linkage, abnormal auto-flagging, order fulfillment, and FHIR export.
- **Full Backend Suite:** 188 tests passing across 32 test files in 28.80s (100% pass rate).
- **Alembic Head Verification:** `0007_diagnostics_schema` verified in migration test suite.
- **Frontend Turbopack Build:** Clean production build with all 11 routes compiling without errors.
