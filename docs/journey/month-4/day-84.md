# Day 84: Pediatric and Geriatric Workflow Isolation with Cal.com Dependent Switcher

**Milestone:** 17-04  
**Theme:** Week 17: Dependent & Family Health Proxy and Zero-Contamination Architecture  
**Status:** **COMPLETED** (820 Tests Passing across 48 Modules, 100% Green)

---

## Executive Summary

Today marks **Day 84**, delivering **Milestone 17-04: Pediatric and Geriatric Workflow Isolation with Cal.com Dependent Switcher**. Following the zero-contamination relational architecture (Day 81), ABDM Child-ABHA generation protocols (Day 82), and guardian consent delegation interceptors (Day 83), today's milestone operationalizes clinical workflow isolation and dynamic EHR view segmentation across the patient portal.

Under **Section 9 of the Indian Digital Personal Data Protection (DPDP) Act 2023**, processing dependent minors' and senior citizens' health records requires strict operational separation from adult guardian profiles. Without workflow isolation, clinical observations risk cross-contamination, causing pediatric growth charts to mingle with adult cardiovascular telemetry or geriatric polypharmacy reviews.

NIRMAYA addresses this with a Cal.com-inspired **Dependent Context Switcher** and dynamic **EHR View Segmentation Engine**:
1. **Cal.com Dependent Switcher:** A minimalist segment switcher embedded in the patient vault header allowing 1-click toggling between Personal Vault (Self), Child Minor (Pediatric), and Senior Parent (Geriatric) personas.
2. **Pediatric Workflow Isolation:** Segregated clinical view displaying the India **Universal Immunization Programme (UIP)** timeline (BCG, OPV, Pentavalent, Rotavirus, PCV, MR, and DPT boosters) alongside WHO growth percentile tracking (Weight, Height, Head Circumference Z-scores).
3. **Geriatric Workflow Isolation:** Segregated senior care view displaying the **Comprehensive Geriatric Assessment (CGA)**, Beers Criteria polypharmacy audits, Timed Up and Go (TUG) fall risk scoring, and Katz Activities of Daily Living (ADL) functional independence indices.
4. **Zero-Contamination Boundary Enforcement:** Cryptographic isolation sessions (`iso-sess-<uuid>`) and custom HTTP headers (`X-Dependent-Context-Isolated: true`) guarantee that pediatric notes and senior medication regimens never bleed into guardian personal records.

---

## Key Deliverables & Architectural Implementation

### 1. Pydantic Schemas & Domain Models

Authored in [`backend/app/schemas/workflow_isolation.py`](file:///e:/nirmaya-side/backend/app/schemas/workflow_isolation.py) and exported in [`backend/app/schemas/__init__.py`](file:///e:/nirmaya-side/backend/app/schemas/__init__.py):
- `ContextTypeEnum`: Clinical persona categorization (`SELF`, `PEDIATRIC_MINOR`, `GERIATRIC_SENIOR`).
- `VaccinationStatusEnum`: UIP immunization milestone lifecycle states (`ADMINISTERED`, `SCHEDULED`, `OVERDUE`).
- `NutritionalStatusEnum`: WHO child growth standard evaluations (`NORMAL`, `MODERATE_WASTING`, `SEVERE_WASTING`, `STUNTING`, `OVERWEIGHT`).
- `FallRiskCategoryEnum`: Timed Up and Go (TUG) mobility grading (`LOW`, `MODERATE`, `HIGH`).
- `DependentContextSummary`: Switchable patient context summary with legal demographic name, ABHA number, age, relationship type, and access scope.
- `PediatricImmunizationMilestone`: Vaccination dose specification under India UIP with dose number, administration date, facility, and batch number.
- `PediatricGrowthObservation`: Anthropometric growth telemetry mapped against WHO percentile curves.
- `GeriatricAssessmentProfile`: CGA evaluation covering Fried Frailty Phenotype (0-5), Beers Criteria safety alerts, Katz ADL score (0-6), and Mini-Cog screening.
- `WorkflowSwitchRequest` & `WorkflowSwitchResponse`: Context switching payload returning permitted views and cryptographic session proofs.

### 2. Workflow Isolation & View Segmentation Service

Implemented in [`backend/app/services/workflow_isolation_service.py`](file:///e:/nirmaya-side/backend/app/services/workflow_isolation_service.py):
- **Context Discovery Engine:** Aggregates primary personal vault and verified family proxy dependents via [`FamilyProxyService`](file:///e:/nirmaya-side/backend/app/services/family_proxy_service.py). Automatically classifies dependents into pediatric (< 18) or geriatric (>= 60) contexts.
- **Dynamic View Segmentation:** Emits customized UI view identifiers tailored to the active clinical persona (`PEDIATRIC_IMMUNIZATION_TIMELINE` for minors; `COMPREHENSIVE_GERIATRIC_ASSESSMENT` for seniors; `OVERVIEW` for self).
- **India Universal Immunization Programme (UIP) Store:** Seeds and manages the national vaccination schedule from birth zero doses to 5-year boosters.
- **Comprehensive Geriatric Assessment (CGA) Store:** Manages multi-morbidity profiles, Beers Criteria drug warnings, and fall risk telemetry.
- **Zero-Contamination Session Manager:** Provisions tamper-evident isolation session tokens and prevents cross-profile record contamination.

### 3. FastAPI REST Endpoints (`/api/v1/patients/proxy/workflow/*`)

Authored in [`backend/app/api/v1/endpoints/workflow_isolation.py`](file:///e:/nirmaya-side/backend/app/api/v1/endpoints/workflow_isolation.py) and mounted in [`backend/app/api/v1/router.py`](file:///e:/nirmaya-side/backend/app/api/v1/router.py):
- `GET /api/v1/patients/proxy/workflow/contexts`: Enumerate available clinical personas for authenticated user.
- `POST /api/v1/patients/proxy/workflow/switch`: Transition active session context and return permitted segmented views.
- `GET /api/v1/patients/proxy/workflow/pediatric/{child_id}/immunizations`: Fetch India UIP vaccination schedule.
- `POST /api/v1/patients/proxy/workflow/pediatric/{child_id}/immunizations`: Record vaccination administration (HTTP 201).
- `GET /api/v1/patients/proxy/workflow/pediatric/{child_id}/growth`: Fetch WHO percentile growth trajectory.
- `GET /api/v1/patients/proxy/workflow/geriatric/{senior_id}/assessment`: Fetch Comprehensive Geriatric Assessment and polypharmacy data.
- `POST /api/v1/patients/proxy/workflow/geriatric/{senior_id}/assessment`: Update geriatric clinical metrics.

### 4. Cal.com Design System Frontend Components

Implemented in [`frontend/src/components/patient/`](file:///e:/nirmaya-side/frontend/src/components/patient/) and mounted in [`frontend/src/app/patient/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/patient/page.tsx):
- **`CalcomDependentSwitcher.tsx`:** Minimalist dropdown controller with hairline borders (`#e5e7eb`), avatar icons, persona badges (`PEDIATRIC`, `GERIATRIC`, `PERSONAL`), and active zero-contamination assurance callouts.
- **`PediatricImmunizationTimeline.tsx`:** National UIP vaccination schedule with dose status pills (`ADMINISTERED` in `emerald`, `SCHEDULED` in `neutral`), batch numbers, and WHO growth percentile cards.
- **`GeriatricCareAssessmentCard.tsx`:** Multi-card dashboard displaying Fried Frailty score, Timed Up & Go fall risk meter, Beers Criteria polypharmacy alerts, and Katz ADL scorecard.
- **Dynamic Context Pivoting:** When a pediatric minor is active, the patient vault renders child immunizations and suppresses adult cardiology telemetry. When a senior parent is active, it renders the geriatric assessment and suppresses pediatric charts.

---

## Verification & Empirical Metrics

- **Day 84 Test Suite:** 29 dedicated unit and integration tests in [`backend/tests/test_workflow_isolation.py`](file:///e:/nirmaya-side/backend/tests/test_workflow_isolation.py) passing in 1.15s.
- **Full Cumulative Backend Test Suite:** 820 tests passing across 48 modules with zero errors and 100% green status.
- **Frontend Compilation:** Next.js 15 production build compiled and prerendered 13/13 static and dynamic routes cleanly.
- **Design Tokens:** Strict Cal.com monochrome palette (`#ffffff`, `#f9fafb`, `#e5e7eb`, `#111111`), valid badge variants, zero emojis, zero em dashes.
