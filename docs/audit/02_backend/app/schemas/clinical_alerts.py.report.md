# Audit Report: backend/app/schemas/clinical_alerts.py

**Path:** `backend/app/schemas/clinical_alerts.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 155 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation schemas for NIRMAYA's Clinical Alert and Laboratory Panic-Value subsystem, covering alert categories, severity tiers, critical LOINC thresholds, diagnostic evaluation, and mandatory clinician acknowledgments.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** In `LabPanicRule`, both `panicLow` and `panicHigh` are marked `Optional[float] = None` without a validator ensuring that at least one threshold boundary is specified and that `panicHigh > panicLow` when both exist, allowing vacuous panic rules to be registered that never trigger alerts.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Laboratory panic values (such as severe hypokalemia, acute troponin spikes indicating myocardial infarction, or critical thrombocytopenia) represent immediate life threats requiring emergency clinician intervention. Hospital accreditation mandates that when an automated diagnostic analyzer detects a panic value, a high-priority alert must be immediately pushed to the attending physician, and the physician must document a verifiable clinical action (e.g. "Prescribed IV Calcium, transferred to CCU") to acknowledge the alert. This file structures the panic thresholds, evaluation requests, alerts, and acknowledgment records.

### How it works, step by step
1. `AlertCategory` classifies alerts: `LAB_PANIC_VALUE`, `CRITICAL_VITALS`, `APPOINTMENT_CONFIRMED`, `APPOINTMENT_CANCELLED`, `SLOT_HELD`, `EMERGENCY_BTG_ACCESS`, `SYSTEM_BROADCAST`.
2. `AlertStatus` tracks the lifecycle: `UNREAD`, `ACKNOWLEDGED`, `ESCALATED`, `DISMISSED`.
3. `LabPanicRule` defines numerical panic boundaries (`panicLow`, `panicHigh`) for specific standard LOINC analyte codes.
4. `LabEvaluationRequest` and `LabEvaluationResult` accept measured diagnostic values and evaluate them against active panic rules.
5. `AlertCreateRequest` and `ClinicalAlertResponse` format the dispatch and retrieval of alerts.
6. `AlertAcknowledgeRequest` enforces that a clinician provides a non-empty `clinicalAction` (min length 3 characters) when closing a critical alert.
7. `AlertSummaryStatsResponse` computes dashboard counts (unread, panic, critical, acknowledged) for the clinician interface.

### Concepts and patterns used
- *Standardized Diagnostic Coding:* Standard LOINC codes for clinical analytes.
- *Mandatory Clinical Intervention Documentation:* Non-repudiation of physician acknowledgment for panic values.
- *Tiered Severity Escalation:* Multi-level alert hierarchy (`AlertSeverity`) shared with real-time WebSocket broadcast systems.

### Key lines to read first
- `clinical_alerts.py:16-35`: `AlertCategory` and `AlertStatus` enums.
- `clinical_alerts.py:37-47`: `LabPanicRule` critical threshold schema.
- `clinical_alerts.py:50-77`: `LabEvaluationRequest` and `LabEvaluationResult` models.
- `clinical_alerts.py:99-109`: `AlertAcknowledgeRequest` acknowledgment model.
- `clinical_alerts.py:112-141`: `ClinicalAlertResponse` full alert record.

### How to change it safely
When modifying alert schemas, ensure `AlertSeverity` matches `app.schemas.websocket_events.AlertSeverity`. Never remove the `min_length=3` constraint on `clinicalAction` in `AlertAcknowledgeRequest`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `enum` (Enum), `typing` (Any, Dict, List, Optional), `uuid`, `pydantic` (BaseModel, ConfigDict, Field), `app.schemas.websocket_events.AlertSeverity`.
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/clinical_alerts_service.py`, `backend/app/api/v1/endpoints/clinical_alerts.py`.
- **Public Surface:** Enums `AlertCategory`, `AlertStatus`; Models `LabPanicRule`, `LabEvaluationRequest`, `LabEvaluationResult`, `AlertCreateRequest`, `AlertAcknowledgeRequest`, `ClinicalAlertResponse`, `AlertSummaryStatsResponse`.

### 2. Security & Patient Safety [SEC / CLINICAL]
- **Incomplete Panic Rule Boundaries (`BE-SCH-CALR-F01`):** In `LabPanicRule` (lines 37-47), both `panicLow` and `panicHigh` default to `None`. If a rule is created with neither boundary, evaluation against measured values will always return `isPanic=False`, failing to detect critical patient states.
- **Mandatory Action Enforcement:** `AlertAcknowledgeRequest.clinicalAction` (line 103) strictly enforces `min_length=3`, preventing clinicians from dismissing life-threatening alerts with whitespace or blank submissions.

### 3. Code quality [QUAL]
- **String Types for Timestamps (`BE-SCH-CALR-F02`):** `ClinicalAlertResponse.createdAt` and `acknowledgedAt` are typed as `str` using `isoformat()` rather than `datetime` objects.
- **Unvalidated LOINC Format (`BE-SCH-CALR-F03`):** In `LabPanicRule.loincCode` and `AlertCreateRequest.loincCode`, strings lack regex validation (`^\d{3,5}-\d$`).
- Clean separation between evaluation requests, alert generation, and summary statistics.

### 4. AI-generated-code smells [QUAL]
- None; the schema represents a well-structured clinical alarm and panic value management framework.

### 5. Performance [PERF]
- Compact evaluation models suitable for high-throughput batch evaluation from automated laboratory analyzers.

### 6. Error handling & edge cases
- `AlertAcknowledgeRequest` separates required clinical action from optional ancillary notes.

### 7. Doc accuracy [DOC]
- Aligns with CAP (College of American Pathologists) and NABH laboratory panic-reporting standards.

### 8. Tests
- Covered by `backend/tests/test_clinical_alerts.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-CALR-F01 | S2 | [QUAL] | 43-44 | `LabPanicRule` allows both thresholds to be `None` | `panicLow: Optional[float]`, `panicHigh: Optional[float]` | Add validator requiring at least one threshold and `panicHigh > panicLow` |
| BE-SCH-CALR-F02 | S3 | [QUAL] | 132, 136 | Alert timestamps typed as raw strings | `createdAt: str`, `acknowledgedAt: Optional[str]` | Use `datetime` with UTC factory |
| BE-SCH-CALR-F03 | S3 | [QUAL] | 40, 91 | LOINC code format not validated | `loincCode: str` accepts arbitrary text | Add regex pattern `^\d{3,5}-\d$` |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-CALR-F01 · Risk: Low · [UNTESTED]
Add threshold validation to `LabPanicRule`:

```diff
--- a/backend/app/schemas/clinical_alerts.py
+++ b/backend/app/schemas/clinical_alerts.py
@@ -10,3 +10,3 @@ import uuid
 
-from pydantic import BaseModel, ConfigDict, Field
+from pydantic import BaseModel, ConfigDict, Field, model_validator
 from app.schemas.websocket_events import AlertSeverity
@@ -46,2 +46,10 @@ class LabPanicRule(BaseModel):
 
     model_config = ConfigDict(from_attributes=True)
+
+    @model_validator(mode="after")
+    def validate_thresholds(self) -> "LabPanicRule":
+        if self.panicLow is None and self.panicHigh is None:
+            raise ValueError("At least one of panicLow or panicHigh must be specified")
+        if self.panicLow is not None and self.panicHigh is not None and self.panicHigh <= self.panicLow:
+            raise ValueError("panicHigh must be strictly greater than panicLow")
+        return self
