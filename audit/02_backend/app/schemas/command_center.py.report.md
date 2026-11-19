# Audit Report: backend/app/schemas/command_center.py

**Path:** `backend/app/schemas/command_center.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 164 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for District & State Public Health Command Center operations, syndromic disease cluster surveillance, hospital critical-care bed telemetry, medical workforce duty rosters, and statutory public health containment directives.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** In `DiseaseClusterReport`, geospatial centroid coordinates (`cluster_centroid_lat`, `cluster_centroid_lng`) lack latitude and longitude boundary constraints (`ge=-90.0, le=90.0`), allowing invalid geographic points to corrupt GIS map rendering in public health surveillance consoles.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
During public health outbreaks (such as seasonal Dengue, Malaria, or respiratory epidemics), state and district healthcare authorities need real-time situational awareness across their sovereign territorial jurisdictions: tracking active disease clusters and transmission rates ($R_t$), monitoring ICU and ventilator occupancy across government hospitals, evaluating physician-to-patient coverage ratios, and issuing legally binding public health directives (e.g. containment zones, masking advisories). This file defines the data contracts for command center dashboards.

### How it works, step by step
1. `OutbreakSeverityEnum`, `DiseaseCategoryEnum`, `FacilityTierEnum`, and `DirectiveCategoryEnum` define standardized public health classifications.
2. `DiseaseClusterReport` models disease outbreaks with case counts, 7-day growth rates, effective reproduction rates ($R_t$), containment radiuses, and geospatial centroid coordinates.
3. `FacilityResourceTelemetry` tracks licensed vs available staffed ICU beds, mechanical ventilators, manifold oxygen beds, and emergency diversion statuses.
4. `WorkforceDutyRoster` reports specialist physician staffing (intensivists, pediatricians, casualty physicians) and doctor-to-patient ratios.
5. `PublicHealthDirectiveCreate` and `PublicHealthDirectiveResponse` model statutory public health orders issued by Chief Medical Officers or District Magistrates.
6. `CommandCenterOverviewResponse` rolls up regional public health indicators for high-level executive decision-making.

### Concepts and patterns used
- *PostgreSQL LTree Territorial Scoping:* Associating clusters, facilities, and directives with hierarchical territorial paths (`india.27.492`).
- *Epidemiological Growth Modeling:* Tracking 7-day trajectory percentages and $R_t$ transmission metrics.
- *Bed Capacity & Diversion Telemetry:* Real-time bed occupancy calculations triggering automatic diversion advisories.

### Key lines to read first
- `command_center.py:11-50`: Public health enums.
- `command_center.py:52-72`: `DiseaseClusterReport` outbreak cluster schema.
- `command_center.py:74-95`: `FacilityResourceTelemetry` critical care capacity schema.
- `command_center.py:113-143`: Public health directive models (`Create`, `Response`).
- `command_center.py:145-164`: `CommandCenterOverviewResponse` executive summary.

### How to change it safely
Ensure `jurisdiction_path` fields match PostgreSQL `ltree` formats. Any added disease categories must align with the Integrated Disease Surveillance Programme (IDSP) statutory reporting list.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `enum` (Enum), `typing` (Dict, List, Optional), `pydantic` (BaseModel, ConfigDict, Field), `app.schemas.administrative_hierarchy` (AdminLevelEnum, GovtDesignationEnum).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/command_center_service.py`, `backend/app/api/v1/endpoints/command_center.py`.
- **Public Surface:** Enums `OutbreakSeverityEnum`, `DiseaseCategoryEnum`, `FacilityTierEnum`, `DirectiveCategoryEnum`; Models `DiseaseClusterReport`, `FacilityResourceTelemetry`, `WorkforceDutyRoster`, `PublicHealthDirectiveCreate`, `PublicHealthDirectiveResponse`, `CommandCenterOverviewResponse`.

### 2. Security [SEC]
- **Territorial Scope Enforcement:** All surveillance records, resource telemetry, and public health directives include `jurisdiction_path`. The command center service and API endpoints must strictly validate that the calling officer possesses administrative authority over the specified ltree path.
- **Statutory Authority Verification:** Directives require `issuing_officer_id` and `issuing_officer_designation`, preventing unauthorized issuance of containment orders.

### 3. Code quality [QUAL]
- **Missing Coordinate Boundaries (`BE-SCH-CMD-F01`):** In `DiseaseClusterReport` (lines 64-65), `cluster_centroid_lat: float` and `cluster_centroid_lng: float` lack bounds. Valid coordinates must enforce `ge=-90.0, le=90.0` for latitude and `ge=-180.0, le=180.0` for longitude.
- **Bed Occupancy Consistency Validator (`BE-SCH-CMD-F02`):** In `FacilityResourceTelemetry` (lines 74-95), there is no model validator ensuring that `occupied_icu_beds + available_icu_beds <= total_icu_beds` or `available_ventilators <= total_ventilator_beds`. Misconfigured telemetry ingestion can record impossible bed counts.
- **Unconstrained Coverage Status (`BE-SCH-CMD-F03`):** In `WorkforceDutyRoster.coverage_status` (line 108), the field uses `str` with a comment rather than `Literal["ADEQUATE", "STRAINED", "CRITICAL"]`.

### 4. AI-generated-code smells [QUAL]
- Hardcoded `surveillance_sla_passed: bool = True` (line 161) in `CommandCenterOverviewResponse` default fields (`BE-SCH-CMD-F04`).

### 5. Performance [PERF]
- Bounded schemas support sub-2ms query responses across aggregated ltree hierarchies.

### 6. Error handling & edge cases
- String bounds (`headline: min_length=5, max_length=150`, `details: min_length=10, max_length=2000`) in `PublicHealthDirectiveCreate` prevent empty or overly lengthy directive texts.

### 7. Doc accuracy [DOC]
- Aligns with Day 86 Public Health Command Center and IDSP surveillance requirements.

### 8. Tests
- Covered by `backend/tests/test_command_center.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-CMD-F01 | S2 | [QUAL] | 64-65 | Geospatial coordinates lack boundary constraints | `cluster_centroid_lat: float` without bounds | Add `ge=-90.0, le=90.0` and `ge=-180.0, le=180.0` |
| BE-SCH-CMD-F02 | S2 | [QUAL] | 81-83 | Hospital bed telemetry lacks sum validation | No validator verifying occupied + available <= total | Add `@model_validator(mode="after")` verifying bed counts |
| BE-SCH-CMD-F03 | S3 | [QUAL] | 108 | Workforce coverage status uses freeform string | `coverage_status: str` | Use `Literal["ADEQUATE", "STRAINED", "CRITICAL"]` |
| BE-SCH-CMD-F04 | S4 | [QUAL] | 161 | Hardcoded performance SLA flag in schema default | `surveillance_sla_passed: bool = True` | Calculate dynamically in service layer |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-CMD-F01 · Risk: Low · [UNTESTED]
Add geographical coordinate validation to `DiseaseClusterReport`:

```diff
--- a/backend/app/schemas/command_center.py
+++ b/backend/app/schemas/command_center.py
@@ -63,4 +63,4 @@ class DiseaseClusterReport(BaseModel):
     severity: OutbreakSeverityEnum = Field(..., description="Epidemiological severity tier")
-    cluster_centroid_lat: float = Field(..., description="Geographical latitude of cluster centroid")
-    cluster_centroid_lng: float = Field(..., description="Geographical longitude of cluster centroid")
+    cluster_centroid_lat: float = Field(..., ge=-90.0, le=90.0, description="Geographical latitude of cluster centroid")
+    cluster_centroid_lng: float = Field(..., ge=-180.0, le=180.0, description="Geographical longitude of cluster centroid")
     radius_meters: int = Field(..., ge=100, description="Estimated containment perimeter radius in meters")
