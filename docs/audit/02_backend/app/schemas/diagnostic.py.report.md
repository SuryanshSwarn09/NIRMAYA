# Audit Report: backend/app/schemas/diagnostic.py

**Path:** `backend/app/schemas/diagnostic.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 265 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 domain schemas for diagnostic laboratory service requisitions and diagnostic reports aligned with HL7 FHIR Release 4 `ServiceRequest` and `DiagnosticReport` specifications.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** In `DiagnosticReportResponse`, `effective_date_time` is defined as a non-optional required `datetime` field, conflicting with `DiagnosticReportBase.effective_date_time: Optional[datetime] = None`. Reports issued without specimen draw timestamps fail schema validation during response serialization.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In healthcare workflows, diagnostic testing follows a two-stage lifecycle: first, a doctor places a diagnostic requisition or service request (e.g. ordering a Lipid Panel or CBC with clinical urgency and fasting notes); second, the laboratory collects the specimen, analyzes the analytes, and issues an official diagnostic report containing clinical impressions, abnormality flags, structured result metrics, and links to granular observations. This file defines the data contracts for placing orders, tracking order statuses, amending reports, and serializing finalized diagnostic reports according to HL7 FHIR R4 standards.

### How it works, step by step
1. `DiagnosticOrderBase`, `DiagnosticOrderCreate`, and `DiagnosticOrderResponse` model the FHIR `ServiceRequest` lifecycle (intent, priority, LOINC panel code, clinical indications, specimen source).
2. `DiagnosticOrderUpdate` allows laboratories and clinicians to transition order workflow statuses (e.g. active to completed or revoked).
3. `DiagnosticOrderFilter` allows searching diagnostic orders by priority, status, category, or clinical encounter.
4. `DiagnosticReportBase`, `DiagnosticReportCreate`, and `DiagnosticReportResponse` model the FHIR `DiagnosticReport` lifecycle (LOINC report codes, abnormality flags, conclusion narratives, SNOMED conclusion codes, key-value metrics summary).
5. `DiagnosticReportWithObservationsResponse` extends the report model with an embedded list of detailed `ObservationResponse` items representing individual laboratory test parameters.

### Concepts and patterns used
- *HL7 FHIR R4 Alignment:* Mapped to FHIR `ServiceRequest` and `DiagnosticReport` resources.
- *Standard Diagnostic Terminologies:* LOINC coding for lab panels (`http://loinc.org`) and SNOMED-CT for conclusion codes.
- *Embedded Observation Hierarchies:* Linking individual quantitative analyte observations to parent diagnostic panel reports.

### Key lines to read first
- `diagnostic.py:24-84`: `DiagnosticOrderBase` FHIR ServiceRequest model.
- `diagnostic.py:86-104`: `DiagnosticOrderCreate` requisition payload.
- `diagnostic.py:143-201`: `DiagnosticReportBase` FHIR DiagnosticReport schema.
- `diagnostic.py:242-257`: `DiagnosticReportResponse` output record.
- `diagnostic.py:259-265`: `DiagnosticReportWithObservationsResponse` nested panel results.

### How to change it safely
When modifying diagnostic schemas, ensure that all status enums (`ServiceRequestStatus`, `DiagnosticReportStatus`, `ServiceRequestPriority`, `SpecimenType`) remain synchronized with `app.models.enums`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing` (Any, Dict, List, Optional), `pydantic` (BaseModel, ConfigDict, Field), `app.models.enums` (DiagnosticReportStatus, ServiceRequestIntent, ServiceRequestPriority, ServiceRequestStatus, SpecimenType), `app.schemas.observation.ObservationResponse`.
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/diagnostic_service.py`, `backend/app/api/v1/endpoints/diagnostic.py`.
- **Public Surface:** Models `DiagnosticOrderBase`, `DiagnosticOrderCreate`, `DiagnosticOrderUpdate`, `DiagnosticOrderResponse`, `DiagnosticOrderFilter`, `DiagnosticReportBase`, `DiagnosticReportCreate`, `DiagnosticReportUpdate`, `DiagnosticReportResponse`, `DiagnosticReportWithObservationsResponse`.

### 2. Security [SEC]
- **Clinical Data Integrity:** `DiagnosticReportResponse.performer_id` and `issued_date_time` ensure that diagnostic conclusions are cryptographically attributable to certified laboratory pathologists.
- **Access Control Enforcement:** Requisitions and reports link to `patient_id` and `encounter_id`, ensuring strict tenant-isolated data access.

### 3. Code quality [QUAL]
- **Type Nullability Mismatch (`BE-SCH-DIA-F01`):** In `DiagnosticReportBase.effective_date_time` (line 171), the field is `Optional[datetime] = None`. In `DiagnosticReportResponse.effective_date_time` (line 251), it is overridden as non-optional `datetime = Field(...)`. If an existing diagnostic record in the database has a `NULL` effective date (e.g. preliminary imaging orders or historical reports), serializing `DiagnosticReportResponse` crashes with a Pydantic `ValidationError`.
- **Deprecated `example` Keyword Argument (`BE-SCH-DIA-F02`):** `Field(..., example=...)` is used across 24 fields. In Pydantic v2, `examples=[...]` or `json_schema_extra` should be used.

### 4. AI-generated-code smells [QUAL]
- Hardcoded commercial laboratory mock name `performer_name: Optional[str] = "Metropolis Diagnostics & Pathology Lab"` (line 192) in schema default field values (`BE-SCH-DIA-F03`).

### 5. Performance [PERF]
- `DiagnosticReportWithObservationsResponse` eagerly embeds observation items. For high-volume panel orders (e.g. 50-analyte comprehensive metabolic panels), batch serialization performs well due to Pydantic v2's Rust core.

### 6. Error handling & edge cases
- Bounded string lengths (`code_value: min_length=1, max_length=50`, `code_display: min_length=2, max_length=255`) prevent empty or corrupted diagnostic entries.

### 7. Doc accuracy [DOC]
- Conforms to HL7 FHIR Release 4 ServiceRequest and DiagnosticReport specifications.

### 8. Tests
- Covered by `backend/tests/test_diagnostic.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-DIA-F01 | S2 | [QUAL] | 171, 251 | Nullability mismatch on `effective_date_time` in response model | Optional in Base, required in Response | Type as `Optional[datetime]` in `DiagnosticReportResponse` |
| BE-SCH-DIA-F02 | S3 | [QUAL] | 30-102, 150-224 | Deprecated `example` keyword argument in Pydantic v2 | `Field(..., example="...")` used across 24 fields | Migrate to `examples=["..."]` or `json_schema_extra` |
| BE-SCH-DIA-F03 | S4 | [QUAL] | 192 | Hardcoded commercial lab name in schema defaults | `performer_name = "Metropolis..."` | Make default `None` and populate from authenticated facility |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-DIA-F01 · Risk: Low · [UNTESTED]
Harmonize nullability of `effective_date_time` in `DiagnosticReportResponse`:

```diff
--- a/backend/app/schemas/diagnostic.py
+++ b/backend/app/schemas/diagnostic.py
@@ -248,3 +248,3 @@ class DiagnosticReportResponse(DiagnosticReportBase):
     status: DiagnosticReportStatus = Field(description="Report verification status")
-    effective_date_time: datetime = Field(description="Observation timing")
+    effective_date_time: Optional[datetime] = Field(default=None, description="Observation timing")
     issued_date_time: datetime = Field(description="UTC timestamp report was officially issued")
