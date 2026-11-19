# Audit Report: backend/app/schemas/cds.py

**Path:** `backend/app/schemas/cds.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 137 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 domain schemas for NIRMAYA's Clinical Decision Support (CDS) Safety Engine, governing real-time drug-drug interaction (DDI) alerts, allergy cross-reactivity warnings, disease contraindications, and clinician override audits.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `SafetyCheckRequest.patient_id` is optional without a requirement for supplemental clinical context; if omitted, pre-prescription safety checks execute against zero patient history, creating false-negative safety clearances where life-threatening contraindications go undetected.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Prescription errors—such as prescribing a medication that fatally interacts with another drug the patient is currently taking, or prescribing an antibiotic to which the patient has a documented severe allergy—are major causes of preventable hospital morbidity. NIRMAYA's Clinical Decision Support (CDS) engine evaluates candidate prescriptions against the patient's active medication list, historical allergies, and chronic diagnoses. When an adverse interaction is detected, it returns structured alerts with pharmacological mechanisms and alternative recommendations. If a clinician must proceed regardless, it requires a documented clinical override. This file structures the alerts, check requests, evaluation responses, and override audits.

### How it works, step by step
1. `SafetyAlert` models an individual clinical alert, detailing its `rule_id`, `alert_type` (drug-drug, drug-allergy, drug-condition), `severity` (critical, major, moderate), `title`, `offending_entity`, pharmacological `mechanism`, and actionable `recommendation`.
2. `SafetyCheckRequest` submits a candidate `medication_id` to evaluate, optionally linking the patient's longitudinal record via `patient_id` or providing ad-hoc supplemental allergies/conditions.
3. `SafetyCheckResponse` returns whether the evaluation passed, boolean flags for alert tiers (`has_critical_alerts`, `has_major_alerts`, `has_moderate_alerts`), whether explicit clinician override documentation is required (`requires_override`), and a ranked list of active `alerts`.
4. `ClinicianOverrideRequest` structures the clinician's justified clinical rationale when proceeding with flagged medications, capturing doctor identity and UTC timestamp.

### Concepts and patterns used
- *Graded Clinical Alert Severity:* Stratifying risks into critical (contraindicated), major, and moderate tiers.
- *Mandatory Clinical Override Documentation:* Requiring non-empty clinical justification (`override_reason`) before high-risk prescriptions can be signed.
- *Pharmacological Mechanism Transparency:* Delivering clear clinical rationale alongside warnings to support physician decision-making.

### Key lines to read first
- `cds.py:14-47`: `SafetyAlert` alert definition.
- `cds.py:49-74`: `SafetyCheckRequest` pre-prescription payload.
- `cds.py:76-117`: `SafetyCheckResponse` evaluation report.
- `cds.py:119-137`: `ClinicianOverrideRequest` override documentation model.

### How to change it safely
When modifying CDS schemas, ensure `CDSAlertType` and `CDSSeverity` enums in `app/models/enums.py` match. Never remove the length bounds (`min_length=5, max_length=1000`) on `override_reason`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `typing` (List, Optional), `pydantic` (BaseModel, ConfigDict, Field), `app.models.enums` (CDSAlertType, CDSSeverity).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/cds_service.py`, `backend/app/api/v1/endpoints/cds.py`.
- **Public Surface:** Models `SafetyAlert`, `SafetyCheckRequest`, `SafetyCheckResponse`, `ClinicianOverrideRequest`.

### 2. Security & Patient Safety [SEC / CLINICAL]
- **Silent Incomplete Safety Check Risk (`BE-SCH-CDS-F01`):** In `SafetyCheckRequest` (lines 49-74), `patient_id` is marked `Optional[str] = None`. While ad-hoc checks between two drugs are useful in laboratory testing, in clinical prescribing, if `patient_id` is omitted and supplemental lists are empty, the engine checks nothing and returns `passed=True`. Prescribers relying on this result may assume the patient has no contraindications when in reality no patient data was ever checked. A model validator should flag requests that provide neither `patient_id` nor supplemental records.
- **Audit Traceability of Clinical Overrides (`BE-SCH-CDS-F02`):** In `ClinicianOverrideRequest` (lines 119-137), there is no field identifying the specific `rule_id` or `alert_id` being overridden, nor the `medication_request_id` being authorized. Without these correlation IDs, clinical overrides cannot be forensically audited back to specific safety rules.

### 3. Code quality [QUAL]
- **Unvalidated Rule Code Syntax (`BE-SCH-CDS-F03`):** In `SafetyAlert.rule_id` (line 19), `rule_id: str` is unconstrained without regex pattern validation. Standardized catalog codes (e.g. `DDI-WARFARIN-NSAIDS`) should follow a uniform alphanumeric pattern.
- Clean use of `from_attributes=True` across all models.

### 4. AI-generated-code smells [QUAL]
- None; the schemas follow established CDS hooks and safety engine design principles.

### 5. Performance [PERF]
- Concise payload structure ensures low-latency execution during real-time electronic prescribing workflows.

### 6. Error handling & edge cases
- Bounded string constraints on `override_reason` (`min_length=5, max_length=1000`) ensure clinicians cannot submit blank or single-character overrides to bypass alerts.

### 7. Doc accuracy [DOC]
- Aligns with clinical decision support best practices and Indian EHR standards.

### 8. Tests
- Covered by `backend/tests/test_cds.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-CDS-F01 | S2 | [QUAL] | 58-73 | Incomplete clinical context permitted in `SafetyCheckRequest` | `patient_id` is optional; no validation ensuring clinical context exists | Add validator requiring `patient_id` or supplemental history |
| BE-SCH-CDS-F02 | S3 | [QUAL] | 119-137 | Missing audit correlation IDs in `ClinicianOverrideRequest` | No `rule_id` or `medication_request_id` fields | Add explicit correlation fields for override auditing |
| BE-SCH-CDS-F03 | S3 | [QUAL] | 19-22 | Unvalidated `rule_id` format in `SafetyAlert` | `rule_id: str` accepts arbitrary text | Add regex pattern constraint |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-CDS-F02 · Risk: Low · [UNTESTED]
Add correlation identifiers to `ClinicianOverrideRequest` for forensic auditability:

```diff
--- a/backend/app/schemas/cds.py
+++ b/backend/app/schemas/cds.py
@@ -124,4 +124,12 @@ class ClinicianOverrideRequest(BaseModel):
     override_reason: str = Field(
         ...,
         min_length=5,
         max_length=1000,
         description="Clinical rationale justifying why benefit outweighs the flagged interaction risk",
     )
+    rule_id: Optional[str] = Field(
+        default=None,
+        description="Identifier of the specific CDS rule or alert being overridden",
+    )
+    medication_request_id: Optional[str] = Field(
+        default=None,
+        description="UUID of the associated medication request",
+    )
     overridden_by_doctor_id: str = Field(
