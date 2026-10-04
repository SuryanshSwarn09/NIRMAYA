# Month 2: Clinical Data & Observational Engine

**Milestone Target:** Transition NIRMAYA from foundational scheduling and identity into a high-fidelity Clinical Information System (CIS) and Electronic Health Record (EHR) core. Month 2 implements longitudinal patient health records, SNOMED-CT / ICD-10 problem lists, LOINC observational telemetry, structured SOAP clinical notes, diagnostic lab requisitions, and ABDM Milestone 2 data exchange workflows.

---

## 1. Month 2 Architectural Vision

Month 1 successfully established the monorepo foundation, Supabase RBAC authentication, transactional appointment scheduling with ACID row-locking, and HL7 FHIR R4 Encounter bundle export (Milestone v0.1.0).

Month 2 elevates NIRMAYA to handle the clinical core of healthcare delivery:
- **Longitudinal Clinical Problem Lists:** Tracking patient medical conditions across acute, chronic, and resolved states with international standard ontologies (SNOMED-CT and ICD-10).
- **Observational Telemetry Engine:** Ingestion, validation, and historical graphing of vital signs, biometric observations, and laboratory test panels mapped to LOINC codes.
- **Structured SOAP Clinical Documentation:** Enabling clinicians to record Subjective, Objective, Assessment, and Plan notes with direct linkage to problem lists and diagnostic orders.
- **Diagnostic Gateway & Lab Requisition:** Clinician-to-diagnostic center requisition workflows (`ServiceRequest`), accession tracking, and digital report delivery (`DiagnosticReport`).
- **ABDM Milestone 2 Interoperability:** Secure patient health record discovery, consent artifact management, and encrypted data transfer protocols (`FIDELIUS` encryption) linking clinical encounters to Ayushman Bharat Health Accounts (ABHA).

```
+-----------------------------------------------------------------------------------+
|                           MONTH 2 CLINICAL DATA ENGINE                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Week 5: Problem Lists ]  --->  [ Week 6: Observations & Vitals ]               |
|  * SNOMED-CT / ICD-10             * LOINC Coded Vitals (BP, HR, SpO2)             |
|  * Condition Lifecycle            * Reference Ranges & Critical Flags             |
|  * FHIR R4 Condition Engine       * FHIR R4 Observation Transformers              |
|                                                                                   |
|  [ Week 7: SOAP & Labs ]   --->  [ Week 8: ABDM M2 & v0.2.0 ]                    |
|  * Structured SOAP Notes          * Consent Request & Health Data Push/Pull       |
|  * Lab Order Requisitions         * FIDELIUS E2E Encryption Engine                |
|  * Diagnostic Reports             * Month 2 Full Verification & v0.2.0 Release    |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Weekly Roadmap & Schedule

| Week | Title & Focus | Days | Key Deliverables & Interoperability |
|---|---|---|---|
| **Week 5** | Clinical Problem Lists & Diagnostic Encounters | Days 21–25 | `ClinicalCondition` entity, SNOMED-CT / ICD-10 codings, status lifecycles (`active` $\rightarrow$ `resolved`), Alembic migration `0004_conditions_schema`, FHIR R4 `Condition` transformer, REST endpoints, and test suite. |
| **Week 6** | Vital Signs, Clinical Observations & LOINC Panels | Days 26–30 | `ClinicalObservation` model, LOINC / SNOMED vitals engine (BP, HR, SpO2, BMI), value validation & flags, FHIR `Observation` schemas, and patient longitudinal telemetry. |
| **Week 7** | Structured SOAP Clinical Notes & Lab Workflows | Days 31–35 | Subjective, Objective, Assessment, Plan (SOAP) clinical encounter documentation, chief complaints, lab requisition workflows (`ServiceRequest`), and diagnostic results. |
| **Week 8** | ABDM Milestone 2 Interoperability & Month 2 Close | Days 36–40 | ABDM M2 consent artifact validation, CareContext discovery, encrypted data transfer (`FIDELIUS`), full-suite verification, and Milestone `v0.2.0` release. |

---

## 3. Core Standards & Ontologies

1. **SNOMED-CT (`http://snomed.info/sct`):**
   - Clinical terms for medical conditions, findings, complaints, and surgical procedures.
2. **ICD-10 (`http://hl7.org/fhir/sid/icd-10`):**
   - Statistical classification and diagnostic billing codes for longitudinal conditions.
3. **LOINC (`http://loinc.org`):**
   - Standardized universal identifiers for laboratory tests, clinical observations, and vital signs panels.
4. **HL7 FHIR Release 4:**
   - Standardized JSON resources for `Condition`, `Observation`, `ServiceRequest`, `DiagnosticReport`, and `Composition`.
5. **ABDM CareContexts:**
   - Cryptographically linked clinical encounter references associated with each patient's ABHA Address.

---

## 4. Key Metrics & Targets for Month 2

- **Target Micro-Commits:** 200+ disciplined micro-commits (10+ commits/day across Days 21–40).
- **Test Suite Expansion:** Target >200 automated backend tests with 100% pass rate.
- **Zero Schema Drift:** All database changes version-controlled through numbered Alembic migrations.
- **Cal.com SaaS Aesthetic:** Seamless clinical interfaces honoring pure `#ffffff` canvases, crisp `#111111` accents, and responsive typography.
- **Production Milestone:** Release `v0.2.0` tag cleanly on Day 40.
