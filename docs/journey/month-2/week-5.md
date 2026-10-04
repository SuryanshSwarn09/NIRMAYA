# Week 5: Clinical Problem Lists & Diagnostic Encounters

**Milestone Target:** Launch Phase 2 of NIRMAYA with longitudinal Clinical Problem Lists, Vital Signs and Clinical Observations, Structured SOAP Notes, and Diagnostic Test Results aligned with HL7 FHIR Release 4 and ABDM standards.

---

## Daily Schedule & Commit Breakdown

| Day | Focus Area | Key Deliverables | Status |
|---|---|---|---|
| **Day 21 (Mon)** | Clinical Condition & Problem Lists | `ClinicalCondition` entity, SNOMED-CT / ICD-10 codings, status lifecycles (`active` $\rightarrow$ `resolved`), Alembic migration `0004_conditions_schema`, FHIR R4 `Condition` transformer, REST endpoints, and test suite | **Completed** |
| **Day 22 (Tue)** | Vital Signs & Observations | `ClinicalObservation` model, LOINC / SNOMED vitals engine (BP, HR, SpO2, BMI), value validation & flags, FHIR `Observation` schemas | *Scheduled* |
| **Day 23 (Wed)** | Structured SOAP Clinical Notes | Subjective, Objective, Assessment, Plan (SOAP) clinical encounter documentation, chief complaints, differential diagnoses | *Scheduled* |
| **Day 24 (Thu)** | Diagnostic Lab Orders & Results | Lab test requisition workflows, LOINC diagnostic panels, range interpretation, specimen metadata | *Scheduled* |
| **Day 25 (Fri)** | Week 5 Review & E2E Validation | Cross-service integration tests, clinical workflow validation, doctor EMR encounter review, GitBook docs | *Scheduled* |

---

## Week 5 Architecture Highlights

- **Standardized Terminology Systems:** Full support for SNOMED-CT (`http://snomed.info/sct`), ICD-10 (`http://hl7.org/fhir/sid/icd-10`), and LOINC (`http://loinc.org`).
- **FHIR R4 Condition & Observation Resources:** Bidirectional translation between relational database models and HL7 FHIR Release 4 JSON representations.
- **Longitudinal Patient Vault:** Conditions tracked over time with onset, abatement, verification statuses, and historical problem lists.
- **Granular RBAC Authorization:** Clinical entries securely recorded and modified by verified doctors, with patient self-reporting and view-only permissions.
