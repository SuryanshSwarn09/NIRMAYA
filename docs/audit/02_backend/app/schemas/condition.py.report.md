# Audit Report: backend/app/schemas/condition.py

**Path:** `backend/app/schemas/condition.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 172 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for ClinicalCondition problem list management aligned with HL7 FHIR Release 4 Condition resource specifications, supporting SNOMED-CT / ICD-10 diagnostic coding, clinical status lifecycles, and longitudinal problem tracking.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** In `ConditionUpdate.validate_update_timeline`, timeline validation is only executed if *both* `onset_date_time` and `abatement_date_time` are supplied in the update payload; an update providing only an abatement date cannot validate chronological order against the existing record, allowing anachronistic resolution dates to enter patient medical records.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In electronic medical record systems, a patient's "Problem List" is the definitive record of active diagnoses, chronic illnesses (e.g. Type 2 Diabetes, Hypertension), and historical medical conditions. In accordance with HL7 FHIR R4 Condition standards and Indian EHR guidelines, diagnoses must be coded using standard terminologies (SNOMED-CT or ICD-10) and track clinical status lifecycles (`active`, `recurrence`, `remission`, `resolved`) along with verification states (`confirmed`, `provisional`, `differential`). This file defines the models for creating, updating, querying, and serializing patient conditions.

### How it works, step by step
1. `ConditionBase` structures common attributes: `clinical_status`, `verification_status`, `category` (problem-list-item, encounter-diagnosis, chronic-condition), `severity`, terminology codes (`code_value`, `code_display`), anatomical `body_site`, and onset/abatement timestamps.
2. `validate_timeline` in `ConditionBase` enforces that a condition cannot abate before it starts (`abatement_date_time >= onset_date_time`).
3. `ConditionCreate` extends base attributes with an optional `encounter_id` linking the diagnosis to a specific clinical visit.
4. `ConditionUpdate` models partial updates (status transitions, resolution dates, clinical notes).
5. `ConditionResponse` formats the full clinical condition record with timestamps and diagnosing practitioner identity (`recorded_by_doctor_id`).
6. `ConditionFilter` provides query parameter models for searching problem lists by status, category, or encounter.

### Concepts and patterns used
- *HL7 FHIR R4 Condition Resource Alignment:* Strict mapping to FHIR status value sets and terminology concepts.
- *Timeline Cross-Field Validation:* Enforcing that disease resolution cannot precede symptom onset.
- *Standardized Diagnostic Ontologies:* SNOMED-CT URIs (`http://snomed.info/sct`) and ICD-10 coding.

### Key lines to read first
- `condition.py:19-78`: `ConditionBase` shared attributes.
- `condition.py:79-85`: `validate_timeline` chronological constraint check.
- `condition.py:88-96`: `ConditionCreate` creation payload.
- `condition.py:98-141`: `ConditionUpdate` update schema.
- `condition.py:143-164`: `ConditionResponse` full output record.

### How to change it safely
When modifying condition schemas, ensure that all status enums (`ClinicalStatus`, `VerificationStatus`, `ConditionCategory`, `ConditionSeverity`) remain synchronized with `app.models.enums`. Never remove the onset/abatement chronological validator.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing` (Optional), `pydantic` (BaseModel, ConfigDict, Field, model_validator), `app.models.enums` (ClinicalStatus, ConditionCategory, ConditionSeverity, VerificationStatus).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/condition_service.py`, `backend/app/api/v1/endpoints/conditions.py`.
- **Public Surface:** Models `ConditionBase`, `ConditionCreate`, `ConditionUpdate`, `ConditionResponse`, `ConditionFilter`.

### 2. Security & Clinical Integrity [SEC / CLINICAL]
- **Partial Timeline Validation Gap (`BE-SCH-CON-F01`):** In `ConditionUpdate` (lines 135-140), `validate_update_timeline` checks `self.abatement_date_time < self.onset_date_time` only when both fields are provided in the patch payload. In typical REST updates, a clinician sends only `abatement_date_time` (e.g. when marking a condition cured). The service layer must explicitly compare the patch abatement date against the existing database `onset_date_time` to prevent anachronistic timelines.
- **Audit Non-Repudiation:** `ConditionResponse.recorded_by_doctor_id` and `recorded_date` ensure that diagnoses are attributed to certified clinicians.

### 3. Code quality [QUAL]
- **Deprecated `example` Keyword Argument (`BE-SCH-CON-F02`):** `Field(..., example=...)` is used across 10 fields (lines 26, 30, 35, 40, 45, 51, 57, 63, 76, 94). In Pydantic v2, `examples=[...]` or `json_schema_extra` is required.
- **Unvalidated Terminology System URI (`BE-SCH-CON-F03`):** `code_coding_system` (line 42) defaults to `"http://snomed.info/sct"`, but is an unconstrained string without URL validation. Callers can supply arbitrary strings.

### 4. AI-generated-code smells [QUAL]
- None; the schema represents clean, professional FHIR R4 clinical condition modeling.

### 5. Performance [PERF]
- Clean and lightweight; minimal overhead during high-volume problem list lookups.

### 6. Error handling & edge cases
- Bounded strings (`code_value: min_length=1, max_length=50`, `code_display: min_length=1, max_length=255`) ensure valid diagnostic descriptions.

### 7. Doc accuracy [DOC]
- Aligns with HL7 FHIR Condition Resource Specification (R4).

### 8. Tests
- Covered by `backend/tests/test_conditions.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-CON-F01 | S2 | [QUAL] | 135-140 | Update timeline validator bypassed on single-field updates | Checks timeline only if both onset and abatement provided | Enforce service-layer comparison against DB onset date |
| BE-SCH-CON-F02 | S3 | [QUAL] | 26, 30, 35, 40, 45, 51, 57, 63, 76, 94 | Deprecated `example` argument in Pydantic v2 | `Field(..., example="...")` used across 10 fields | Migrate to `examples=["..."]` or `json_schema_extra` |
| BE-SCH-CON-F03 | S3 | [QUAL] | 42 | Unvalidated terminology system URI | `code_coding_system: str` accepts arbitrary text | Validate URI format or restrict to allowed terminology systems |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-CON-F02 · Risk: Low · [UNTESTED]
Migrate deprecated `example` arguments to Pydantic v2 `examples`:

```diff
--- a/backend/app/schemas/condition.py
+++ b/backend/app/schemas/condition.py
@@ -24,3 +24,3 @@ class ConditionBase(BaseModel):
         description="Clinical status of the condition (active | recurrence | relapse | inactive | remission | resolved)",
-        example=ClinicalStatus.ACTIVE,
+        examples=[ClinicalStatus.ACTIVE],
     )
@@ -29,3 +29,3 @@ class ConditionBase(BaseModel):
         description="Verification status (unconfirmed | provisional | differential | confirmed | refuted | entered-in-error)",
-        example=VerificationStatus.CONFIRMED,
+        examples=[VerificationStatus.CONFIRMED],
     )
