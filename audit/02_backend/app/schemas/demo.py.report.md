# Audit Report: backend/app/schemas/demo.py

**Path:** `backend/app/schemas/demo.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 79 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation schemas for the NIRMAYA National Demonstrator interactive sandbox scenarios, execution step telemetry, and technical defense presentation slide deck metadata.
- **Risk Level:** **S3 (Low)**
- **Verdict:** **READY**
- **Single Most Important Finding:** `SlideItem.slide_number` enforces an arbitrary hardcoded upper limit `le=12` alongside `SlideDeckMetadata.total_slides = 12`, preventing slide deck expansion for additional architecture walkthrough or backup slides.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
To showcase NIRMAYA's capabilities to technical evaluators, ministry stakeholders, and academic committees without requiring manual, multi-system setup, the platform includes an interactive sandbox demonstrator. This demonstrator executes end-to-end scenarios (such as an offline rural clinic encounter synchronizing to the national cloud, or an emergency Break-The-Glass override) while verifying cryptographic proofs in real time. It also provides structured slide deck models to power an automated browser-based capstone defense presentation. This file defines the scenario specifications, step telemetry, execution results, and slide deck models.

### How it works, step by step
1. `ScenarioCategoryEnum` classifies the 5 demonstration domains (`CLINICAL_WORKFLOW`, `EMERGENCY_SECURITY`, `EDGE_OFFLINE_SYNC`, `LEGACY_FEDERATION`, `PUBLIC_HEALTH_GOVERNANCE`).
2. `ScenarioExecutionStatus` tracks scenario states (`READY`, `RUNNING`, `SUCCESS`, `FAILED`).
3. `ScenarioStep` and `DemoScenario` specify ordered steps with expected latency thresholds (`expected_duration_ms`) and prerequisites.
4. `ScenarioExecutionResult` records wall-clock execution duration, completed steps, verified clinical/security assertions, and cryptographic proofs.
5. `SlideItem` and `SlideDeckMetadata` structure presentation defense slides with bullet points, ASCII architecture diagrams, and empirical metrics.

### Concepts and patterns used
- *Automated Demonstration Telemetry:* Capturing live execution outputs and asserting cryptographic proofs during guided walkthroughs.
- *Slide-as-Code Presentation Modeling:* Structured JSON-driven slide deck models for academic defenses.
- *Domain-Specific Scenario Categorization:* Aligning demonstrator workflows with core architectural themes.

### Key lines to read first
- `demo.py:7-14`: `ScenarioCategoryEnum` domain classifications.
- `demo.py:24-32`: `ScenarioStep` discrete stage model.
- `demo.py:34-44`: `DemoScenario` full scenario specification.
- `demo.py:46-58`: `ScenarioExecutionResult` verification outcome.
- `demo.py:60-79`: Slide presentation models (`SlideItem`, `SlideDeckMetadata`).

### How to change it safely
When adding new demonstration scenarios, register appropriate categories in `ScenarioCategoryEnum` and ensure `sla_target_ms` reflects realistic latency bounds.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `enum` (Enum), `typing` (Any, Dict, List, Optional), `pydantic` (BaseModel, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/demo_service.py`, `backend/app/api/v1/endpoints/demo.py`.
- **Public Surface:** Enums `ScenarioCategoryEnum`, `ScenarioExecutionStatus`; Models `ScenarioStep`, `DemoScenario`, `ScenarioExecutionResult`, `SlideItem`, `SlideDeckMetadata`.

### 2. Security [SEC]
- **No Sensitive Data Exposure:** Schemas model synthetic sandbox scenarios and academic slide presentations; no live patient PHI or secret credentials are involved.

### 3. Code quality [QUAL]
- **Hardcoded Slide Ceiling (`BE-SCH-DEMO-F01`):** In `SlideItem.slide_number` (line 62), `le=12` restricts the slide index to 12. If additional technical defense slides are appended, schema validation fails.
- **Missing Module Docstring (`BE-SCH-DEMO-F03`):** File begins directly with imports on line 1 without an explanatory module docstring.

### 4. AI-generated-code smells [QUAL]
- Hardcoded author `"Suryansh Swarn"` and institution `"Department of Computer Science & Engineering"` in default field values (lines 74-75) (`BE-SCH-DEMO-F02`).

### 5. Performance [PERF]
- Extremely lightweight; fast serialization for real-time frontend scenario progress bars.

### 6. Error handling & edge cases
- `ScenarioExecutionStatus.FAILED` cleanly captures step failures with structured output.

### 7. Doc accuracy [DOC]
- Aligns with Day 87 national demonstrator scenarios and defense presentation walkthroughs.

### 8. Tests
- Covered by `backend/tests/test_demo.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-DEMO-F01 | S3 | [QUAL] | 62, 77 | Hardcoded 12-slide maximum in slide deck schemas | `le=12` on `slide_number`, `total_slides = 12` | Remove `le=12` or expand upper bound to support appendix slides |
| BE-SCH-DEMO-F02 | S4 | [QUAL] | 74-75 | Hardcoded author and institution in schema defaults | `author: str = "Suryansh Swarn"` | Load presentation metadata from configuration |
| BE-SCH-DEMO-F03 | S4 | [QUAL] | 1 | Missing module-level docstring | File begins directly with imports | Add explanatory module docstring |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-DEMO-F01 · Risk: Low · [UNTESTED]
Allow expandable slide deck sizes by relaxing the upper limit:

```diff
--- a/backend/app/schemas/demo.py
+++ b/backend/app/schemas/demo.py
@@ -60,4 +60,4 @@ class SlideItem(BaseModel):
     """Structured content for a technical defense slide."""
-    slide_number: int = Field(..., ge=1, le=12, description="Sequential slide index")
+    slide_number: int = Field(..., ge=1, le=50, description="Sequential slide index")
     title: str = Field(..., description="Slide headline")
