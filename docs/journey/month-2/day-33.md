# Day 33: Milestone 07-03: Problem List & Active Conditions UI

**Date:** October 23, 2026  
**Milestone:** 07-03 (Month 2, Week 7)  
**Executed Micro-Commits (Strict 7-Commit Schedule):**  
1. `36bf7f1: feat(api): expand patient conditions client and snomed-ct terminology mappings`
2. `c2f1541: feat(frontend): implement patient condition card component with snomed and fhir tokens`
3. `6b5590f: feat(frontend): implement condition symptom update and patient self-report modal`
4. `437d569: feat(frontend): create modular patient problems tab with search, status filtering, and stats`
5. `5d65c57: feat(frontend): integrate patient problems tab and live condition data into patient vault`
6. `8536169: test(backend): verify condition api access control, fhir serialization, and filtering`
7. `docs(journey): author day 33 engineering log, update summary, and changelog`

---

## 1. Objectives & Architectural Context

In longitudinal healthcare management, the **Problem List** represents a single source of truth summarizing a patient's diagnosed acute and chronic conditions, comorbidities, active allergies, and long-term health concerns. Following the delivery of the modular Patient Portal Shell (Day 31) and the Interactive Digital ABHA ID Card Generator (Day 32), **Day 33 (Milestone 07-03)** transitions NIRMAYA's clinical condition architecture into an authentic consumer-grade patient experience.

Prior to Day 33, condition records were accessible through a generic dual-view clinical component. Patients lacked intuitive medical explanations, self-care guidance, dual terminology mappings (**SNOMED-CT** & **ICD-10**), severity visual indicators, and a structured mechanism to self-report symptom changes or request clinician follow-up.

Day 33 delivered a patient-facing clinical conditions vault built on the **Cal.com design system** (`calcom-design-system` skill), complete with dual terminology ontologies, interactive severity filtering, dynamic search, symptom progress tracking, and full HL7 FHIR R4 `Condition` serialization.

---

## 2. Engineered Component Architecture

```
e:\nirmaya-side\
├── frontend\src\
│   ├── lib\
│   │   ├── conditions.ts               # SNOMED-CT / ICD-10 dual terminology dictionary & self-care rules
│   │   └── api.ts                      # Enhanced condition retrieval, patching, and FHIR export endpoints
│   ├── components\patient\
│   │   ├── PatientConditionCard.tsx    # Card with dual terminology badges, severity tokens, and care guidelines
│   │   ├── PatientConditionUpdateModal.tsx # Symptom progress intake, trend selector, and physician review flags
│   │   ├── PatientProblemsTab.tsx      # Comprehensive tab view with 4 summary stat cards, search, and filters
│   │   └── index.ts                    # Updated barrel exports
│   └── app\patient\page.tsx            # Live state orchestration, live API sync, and FHIR inspector triggers
└── backend\tests\
    └── test_conditions.py              # 10 automated test suites covering CRUD, RBAC, FHIR R4, and patient updates
```

---

## 3. Clinical Terminology & Semantic Mapping

Under the ABDM and HL7 FHIR R4 guidelines, clinical conditions require standardization against international terminologies. `frontend/src/lib/conditions.ts` establishes a bidirectional ontology mapping between:
- **SNOMED-CT (`http://snomed.info/sct`):** Primary clinical concepts (e.g. `38341003` for *Essential hypertension*, `44054006` for *Type 2 diabetes mellitus*, `55822004` for *Hyperlipidemia*).
- **ICD-10 (`http://hl7.org/fhir/sid/icd-10`):** Diagnostic classification for billing and epidemiology (e.g. `I10`, `E11.9`, `E78.5`).
- **Patient Context & Self-Care Engine:**
  - Plain-language condition summaries removing clinical jargon.
  - Evidence-based self-care advice (e.g. DASH diet for hypertension, annual diabetic foot exams for T2DM, avoidance of NSAIDs for CKD).
  - Explicit clinical monitoring targets (e.g. *"Maintain clinic BP below 130/80 mmHg"*, *"Maintain HbA1c < 7.0%"*).
  - Recommended specialty attribution for care team navigation.

---

## 4. Patient Self-Reporting & Symptom Logging

Patients are active participants in managing chronic conditions. `PatientConditionUpdateModal` provides a HIPAA-compliant self-reporting workflow:
1. **Perceived Severity Assessment:** Patient-reported severity rating (Mild, Moderate, Severe).
2. **Symptom Trajectory Tracking:** Categorization into *Improved*, *Stable / Controlled*, or *Escalating / Worsening*.
3. **Biometric Observations:** Free-text logging of home vitals readings, medication adherence, or side effects.
4. **Physician Review Flag:** Checkbox to flag the record for review during the patient's next scheduled clinical encounter.
5. **Security & RBAC Enforcement:** Backend permissions verify that only the cardholder patient, treating doctor, or system admin can append notes, with cross-tenant unauthorized updates rejected with `403 Forbidden`.

---

## 5. Verification & Test Metrics

1. **Backend Automated Tests:**
   - Ran `backend/.venv/Scripts/pytest.exe tests/test_conditions.py -v`:
     - **10/10 tests passing (100% green)** in 3.55s.
   - Ran full test suite `pytest -q`:
     - **234 / 234 tests passing (100% green)** across all 39 test files in 50.48s.
2. **Frontend Type Check:**
   - Ran `npx tsc --noEmit` in `frontend/`: **0 errors**.
3. **Frontend Production Build:**
   - Ran `npm run build` in `frontend/`:
     - Next.js 15.5.25 compiled successfully in 32.9s.
     - **11/11 static pages generated with 0 errors**.
     - Route `/patient`: 37.1 kB.
4. **Git Discipline:**
   - Strictly **7 micro-commits** authored under `Suryansh Swarn <suryanshswarn@gmail.com>`.
   - **Zero release tags created today** (Alpha tag `v0.2.0-alpha.w7` reserved for Day 35 Week 7 close).
