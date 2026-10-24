# Day 34: Milestone 07-04: Vitals Telemetry & Observational Charts

**Date:** October 24, 2026  
**Milestone:** 07-04 (Month 2, Week 7)  
**Executed Micro-Commits (Strict 8-Commit Schedule):**  
1. `47a2063: feat(frontend): install recharts and implement loinc clinical observation definitions`
2. `37c1df4: feat(frontend): implement interactive blood pressure dual-series area chart`
3. `12b370f: feat(frontend): implement multi-metric vitals telemetry charts for spo2, heart rate, and bmi`
4. `f0dfc63: feat(frontend): create unified patient vitals telemetry dashboard component`
5. `5f0adcd: feat(frontend): enhance biometric logging modal with instant loinc clinical interpretation`
6. `b97dbba: feat(frontend): integrate interactive vitals telemetry into patient health vault`
7. `c41b4f1: test(backend): verify vital signs observational telemetry api and fhir serialization`
8. `docs(journey): author day 34 engineering log, update summary, and changelog`

---

## 1. Objectives & Architectural Context

Longitudinal physiological telemetry forms the bedrock of preventive healthcare, proactive chronic disease management, and clinical decision support. Following the modular decomposition of the Patient Health Vault (Day 31), the interactive digital ABHA ID card generator with QR verification (Day 32), and the longitudinal problem list (Day 33), **Day 34 (Milestone 07-04)** delivers comprehensive biometric vitals telemetry and interactive observational charts.

Prior to Day 34, vitals records were presented in a simple static 4-card grid without temporal trend visualization, clinical threshold references (e.g. AHA/ACC hypertension guidelines), or multi-metric observational telemetry.

Day 34 transforms the patient experience by integrating `recharts` 3.10.1 within a clean **Cal.com design system** (`calcom-design-system` skill) aesthetic:
- Dual-series interactive AreaChart for Systolic and Diastolic Blood Pressure with AHA reference guidelines (Hypertensive Crisis 180 mmHg, Stage 2 140 mmHg, Elevated 120 mmHg, Normal 80 mmHg).
- Dynamic multi-metric telemetry charts for Resting Heart Rate (`8867-4`), Blood Oxygen Saturation (SpO2, `2708-6`), Body Mass Index & Weight (`39156-5`, `29463-7`), and Body Temperature (`8310-5`).
- Live biometric intake modal calculating instant LOINC clinical interpretations with stage evaluation badges and self-care recommendations.
- Interactive time-series filtering (`7D`, `30D`, `90D`, `All`) and full HL7 FHIR R4 `Observation` JSON inspection.

---

## 2. Engineered Component Architecture

```
e:\nirmaya-side\
├── frontend\src\
│   ├── lib\
│   │   └── vitals.ts                   # LOINC code registry, clinical evaluators (AHA BP, Pulse, SpO2, BMI, Temp) & types
│   ├── components\patient\
│   │   ├── BloodPressureChart.tsx      # Dual-series Recharts AreaChart with AHA reference lines and time-range filters
│   │   ├── VitalsMetricChart.tsx       # Configurable telemetry chart engine for Heart Rate, SpO2, BMI, and Temperature
│   │   ├── PatientVitalsTelemetry.tsx  # Unified vitals telemetry dashboard with quick stat cards, charts, and audit table
│   │   ├── PatientModals.tsx           # Enhanced biometric logging modal with live LOINC interpretation box
│   │   ├── PatientRecordsTab.tsx       # Embedded PatientVitalsTelemetry into Section 1 of the Records tab
│   │   ├── PatientOverviewTab.tsx      # Live telemetry snapshot cards with LOINC badges and status pills
│   │   └── index.ts                    # Updated barrel exports
│   └── app\patient\page.tsx            # Longitudinal 7-day time series state, dynamic metrics bar, and API sync
└── backend\tests\
    └── test_observations.py            # Automated tests verifying LOINC coding, FHIR R4 serialization, and RBAC
```

---

## 3. LOINC Standards & Clinical Evaluation Engine

All biometric telemetry is standardized against international clinical observation terminologies:
- **LOINC `85354-9` (Blood Pressure Panel):** Systolic (`8480-6`) and Diastolic (`8462-4`). Evaluated against the **AHA/ACC 2017 Guidelines**:
  - *Normal:* Systolic < 120 and Diastolic < 80 mmHg.
  - *Elevated:* Systolic 120–129 and Diastolic < 80 mmHg.
  - *Stage 1 Hypertension:* Systolic 130–139 or Diastolic 80–89 mmHg.
  - *Stage 2 Hypertension:* Systolic ≥ 140 or Diastolic ≥ 90 mmHg.
  - *Hypertensive Crisis:* Systolic > 180 or Diastolic > 120 mmHg.
- **LOINC `8867-4` (Heart Rate):** Normal resting adult baseline (60–100 bpm), bradycardia (< 60 bpm), and tachycardia (> 100 bpm).
- **LOINC `2708-6` (Oxygen Saturation, SpO2):** Optimal arterial oxygenation (≥ 95%), mild hypoxia (90–94%), and severe hypoxemia (< 90%).
- **LOINC `39156-5` (BMI) & `29463-7` (Weight):** Dynamic BMI calculation from weight (kg) and height (cm), categorized into Underweight (< 18.5), Normal (18.5–24.9), Overweight (25–29.9), and Obese (≥ 30).
- **LOINC `8310-5` (Body Temperature):** Normal thermal baseline (97.8°F–99.0°F), low-grade fever (> 99.0°F), pyrexia (> 100.4°F), and hyperpyrexia (> 103°F).

---

## 4. Live Biometric Intake & FHIR Observation Synchronization

When patients self-report biometric vitals through the enhanced `PatientModals`:
1. **Real-time Feedback:** As numbers are keyed in, the evaluation engine immediately computes the clinical stage, category, and recommendation guideline.
2. **Local State Update:** Both the latest observation record and the longitudinal time-series dataset are updated instantly for zero-latency UI reactivity.
3. **FHIR R4 Observation Generation:** The intake triggers an asynchronous POST to `/api/v1/patients/{patient_id}/observations`, generating compliant HL7 FHIR R4 `Observation` resources with code, effectiveDateTime, valueQuantity, and sub-components.
4. **Header Metrics Reactivity:** `PatientMetricsBar` dynamically evaluates the most recent telemetry to display current blood pressure, SpO2, and clinical abnormal/normal status.

---

## 5. Verification & Test Metrics

1. **Backend Automated Tests:**
   - Ran `backend/.venv/Scripts/pytest.exe tests/test_observations.py -v`:
     - **11/11 tests passing (100% green)** in 3.06s.
   - Ran full test suite `pytest -q`:
     - **234 / 234 tests passing (100% green)** across all 39 test files in 63.18s.
2. **Frontend Type Check:**
   - Ran `npx tsc --noEmit` in `frontend/`: **0 errors**.
3. **Frontend Production Build:**
   - Ran `npm run build` in `frontend/`:
     - Next.js 15.5.25 compiled successfully in 66s.
     - **11/11 static pages generated with 0 errors**.
     - Route `/patient`: 157 kB (First load JS: 284 kB).
4. **Git Discipline:**
   - Strictly **8 micro-commits** authored under `Suryansh Swarn <suryanshswarn@gmail.com>`.
   - **Zero release tags created today** (Alpha tag `v0.2.0-alpha.w7` reserved for Day 35 Week 7 close).
