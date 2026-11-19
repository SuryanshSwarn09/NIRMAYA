# Codebase Technical Audit Report: `backend/app/services/observation.py`

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`observation.py` manages the clinical observation and vital signs recording service layer for NIRMAYA. It encapsulates clinical business logic for capturing physiological parameters (blood pressure, heart rate, respiratory rate, body temperature, oxygen saturation, weight, height, fasting blood glucose), calculating Body Mass Index (BMI), evaluating WHO standard physiological reference intervals, querying longitudinal patient telemetry, and synthesizing the single latest vital sign panel for clinical consultation dashboards.

### System Topology & Observation Pipeline
```
   [ Clinician / Nurse / Triage Desk ]
                    |
      (Capture Vitals / Observations)
                    v
   +------------------------------------+
   |         ObservationService         |
   +------------------------------------+
   | - Patient / Doctor / Visit Binding |
   | - BMI Calculator (WHO Standards)   |
   | - Multi-Component JSON Packager    |
   | - Latest Vitals Panel Synthesizer  |
   +------------------------------------+
                    |
           (AsyncSession ORM)
                    v
         [( PostgreSQL Database )]
         Table: `clinical_observations`
```

### Module Metadata & Imports/Exports
- **Module Path:** `backend/app/services/observation.py`
- **Component Classification:** Clinical Observation & Vital Signs Engine
- **Lines of Code:** 301 LOC
- **Imports:** `datetime`, `typing`, `sqlalchemy.*`, `sqlalchemy.ext.asyncio.AsyncSession`, `app.core.exceptions.*`, `app.models.*`, `app.schemas.observation.*`
- **Primary Exports:** `calculate_bmi`, `record_observation`, `get_observation_by_id`, `list_patient_observations`, `get_latest_vitals_summary`, `update_observation`

---

## Layer B: Plain-Language Developer Walkthrough

The module implements vital sign ingestion and longitudinal querying:
1. **BMI Calculation (`calculate_bmi`)**: Computes Body Mass Index from weight (kg) and height (cm):
   $$\text{BMI} = \frac{\text{weight\_kg}}{(\text{height\_cm} / 100)^2}$$
   Assigns categorical interpretations: `LOW` (< 18.5), `NORMAL` (18.5–24.9), `HIGH` (25.0–29.9), or `CRITICALLY_HIGH` (>= 30.0).
2. **Observation Recording (`record_observation`)**: Validates referential integrity (patient exists, encounter belongs to patient, clinician exists). Serializes multi-component observations (e.g. systolic + diastolic blood pressure pairs) into JSON payloads and persists a new `ClinicalObservation` record.
3. **Longitudinal History (`list_patient_observations`)**: Queries historical observations filtered by category, LOINC code, status, encounter, and date ranges with eager-loaded user and encounter models.
4. **Latest Vitals Dashboard Summary (`get_latest_vitals_summary`)**: Gathers the most recent reading across 9 standard clinical parameters (BP, HR, RR, Temp, SpO2, BMI, Weight, Height, Glucose) to display a rapid patient assessment tile.
5. **Observation Mutation (`update_observation`)**: Updates status, interpretation, or clinical notes on existing observation entities.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Multi-Component LOINC Blood Pressure Integrity
Blood pressure observations contain paired systolic and diastolic components linked under LOINC panel `85354-9`. The service structures both values inside `components_data` JSON dictionaries to preserve semantic clinical pairing without splitting measurements into disconnected records.

### Invariant 2: Encounter Patient Ownership Invariant
When recording an observation linked to an encounter (`encounter_id`), the service verifies that the appointment actually belongs to the subject patient (`Appointment.patient_id == patient_id`) at line 91, preventing cross-patient encounter contamination.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
|---|---|---|---|---|
| `BE-SVC-OBS-F01` | **S1** | `[SEC]` | `backend/app/services/observation.py:280-301` | Unrestricted Clinical Observation Mutation without Authorization or Audit Trail. `update_observation` allows modifying status, interpretation, or notes without verifying whether the caller is the performing clinician or has write access to the patient profile (IDOR / clinical tampering). |
| `BE-SVC-OBS-F02` | **S1** | `[SEC]` | `backend/app/services/observation.py:220-275` | N+1 Sequential Database Query Loop for Latest Vitals Summary. `get_latest_vitals_summary` issues 9 separate sequential SQL queries across the network (one per LOINC code) with eager joins, creating latency spikes and potential connection exhaustion under concurrent OPD dashboard requests. |
| `BE-SVC-OBS-F03` | **S2** | `[QUAL]` | `backend/app/services/observation.py:38-66` | BMI Calculation Uses Hardcoded General Adult Cutoffs for All Patients Regardless of Age or Ethnicity. Asian Indian populations have lower WHO BMI thresholds (Overweight >= 23.0, Obese >= 25.0), and pediatric patients require age-and-sex specific CDC/IAP growth percentiles. |
| `BE-SVC-OBS-F04` | **S2** | `[QUAL]` | `backend/app/services/observation.py:108-118` | Missing Numeric Range and Plausibility Validation on Physiological Vitals. Allows negative body weights, heart rates of 0 or 999, temperatures of 200°C, and systolic pressures below diastolic without raising validation errors. |
| `BE-SVC-OBS-F05` | **S3** | `[PERF]` | `backend/app/services/observation.py:180-205` | Subquery Count in `list_patient_observations` Causes Full Subquery Materialization. |
| `BE-SVC-OBS-F06` | **S4** | `[DOC]` | `backend/app/services/observation.py:26-36` | Missing LOINC Coding System URI Documentation (`http://loinc.org`). |

---

## Layer E: Unapplied Unified Diff Patches

### Patch 1: Physiological Plausibility Checks on Vital Signs (`BE-SVC-OBS-F04`)
```diff
--- a/backend/app/services/observation.py
+++ b/backend/app/services/observation.py
@@ -107,4 +107,10 @@ async def record_observation(
+    if payload.value_quantity is not None:
+        if payload.value_quantity < 0:
+            raise ValueError("Vital sign quantity cannot be negative")
+        if payload.code_value == LOINC_HEART_RATE and not (20 <= payload.value_quantity <= 300):
+            raise ValueError("Heart rate outside physiologically plausible range (20-300 bpm)")
+        if payload.code_value == LOINC_BODY_TEMPERATURE and not (25.0 <= payload.value_quantity <= 45.0):
+            raise ValueError("Body temperature outside plausible range (25.0 - 45.0 C)")
     effective_dt = payload.effective_date_time or datetime.now(timezone.utc)
```

### Patch 2: Optimize Vitals Query Using Single Window Query (`BE-SVC-OBS-F02`)
```diff
--- a/backend/app/services/observation.py
+++ b/backend/app/services/observation.py
@@ -235,16 +235,16 @@ async def get_latest_vitals_summary(
-    for code in vitals_codes:
-        stmt = (
-            select(ClinicalObservation)
-            .options(...)
-            .where(
-                ClinicalObservation.patient_id == patient_id,
-                ClinicalObservation.code_value == code,
-            )
-            .order_by(ClinicalObservation.effective_date_time.desc())
-            .limit(1)
-        )
-        obs = await db.scalar(stmt)
+    # Single query fetching latest observation per LOINC code via DISTINCT ON
+    stmt = (
+        select(ClinicalObservation)
+        .distinct(ClinicalObservation.code_value)
+        .where(
+            ClinicalObservation.patient_id == patient_id,
+            ClinicalObservation.code_value.in_(vitals_codes),
+        )
+        .order_by(ClinicalObservation.code_value, ClinicalObservation.effective_date_time.desc())
+    )
+    results = (await db.scalars(stmt)).all()
+    for obs in results:
+        code = obs.code_value
```
