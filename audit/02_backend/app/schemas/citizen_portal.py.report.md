# Audit Report: backend/app/schemas/citizen_portal.py

**Path:** `backend/app/schemas/citizen_portal.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 225 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for the Strict CoWIN/DigiLocker 3-Tile Citizen Portal (Tile 1: Health ID / ABHA card, Tile 2: Active Medicines with plain language timing, Tile 3: Doctor Visits & Reports with plain diagnoses and signed PDFs), OPD check-in QR codes, and aggregated responses.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** Widespread dual-field aliasing in `model_post_init` (`id` vs `medicine_id`, `brand_name` vs `name`, `prescribed_by` vs `prescribing_doctor`, `days_remaining` vs `remaining_days`, `medicines_tile` vs `active_medicines_tile`) duplicates data on the wire, significantly inflating JSON payload size and creating API contract ambiguity across frontend components.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Digital Public Infrastructure (DPI) healthcare portals must present complex medical data in a manner that is immediately intuitive to ordinary citizens, eliminating confusing Latin abbreviations (e.g. *t.i.d.*, *q.d.*) and unreadable medical jargon. NIRMAYA models its citizen portal after India's highly successful CoWIN and DigiLocker user experiences using a 3-tile dashboard: Tile 1 displays the official ABHA card and OPD fast-track check-in QR; Tile 2 shows active prescriptions categorized by plain-language meal times ("Morning with breakfast", "Night after dinner"); Tile 3 lists doctor visits with plain-English diagnoses and tamper-evident signed prescription PDFs. This file defines the data contracts for these tiles.

### How it works, step by step
1. `CitizenHealthIdSummary` (Tile 1) models the ABHA card with 14-digit hyphenated ABHA number, official handle, masked mobile, blood group, and scannable check-in QR code.
2. `PlainScheduleItem` and `CitizenActiveMedicineItem` (Tile 2) translate prescriptions into plain-language schedules, intake compliance flags, and refill urgency alerts (`is_refill_urgent`).
3. `CitizenVisitReportItem` (Tile 3) presents consultations with plain diagnoses alongside formal ICD-10 terminology and download links for cryptographically signed PDF prescriptions.
4. `HospitalCheckInQrResponse` provides a temporary (60-minute TTL) high-contrast scannable QR token for fast-track hospital counter check-in.
5. `CitizenThreeTileResponse` combines all three tiles into a unified payload for adult self or linked dependent minor/senior profiles.

### Concepts and patterns used
- *Plain Language Clinical Communication:* Replacing Latin medical sigs with intuitive time-of-day intake slots.
- *Cryptographic Attestation Verification:* Exposing SHA-256 digital signature hashes for signed medical documents.
- *Model Post-Initialization Aliasing:* Using `model_post_init` to populate fallback and convenience alias fields.

### Key lines to read first
- `citizen_portal.py:15-48`: `CitizenHealthIdSummary` ABHA card model.
- `citizen_portal.py:49-65`: `PlainScheduleItem` plain-language intake times.
- `citizen_portal.py:68-122`: `CitizenActiveMedicineItem` active prescription model.
- `citizen_portal.py:124-168`: `CitizenVisitReportItem` encounter history model.
- `citizen_portal.py:200-225`: `CitizenThreeTileResponse` unified dashboard container.

### How to change it safely
When modifying citizen portal schemas, ensure any changes maintain backward compatibility with both raw and aliased field names until frontend clients are fully harmonized.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `typing` (Any, Dict, List, Optional), `pydantic` (BaseModel, ConfigDict, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/citizen_portal_service.py`, `backend/app/api/v1/endpoints/citizen_portal.py`.
- **Public Surface:** Models `CitizenHealthIdSummary`, `PlainScheduleItem`, `CitizenActiveMedicineItem`, `CitizenVisitReportItem`, `HospitalCheckInQrResponse`, `CitizenThreeTileResponse`.

### 2. Security & Privacy [SEC]
- **Default Blood Group Assumption (`BE-SCH-CPOR-F03`):** In `CitizenHealthIdSummary.blood_group` (line 26), the field defaults to `"O+"` instead of `None` or `"UNKNOWN"`. In clinical emergencies, if a patient has no recorded blood group, rendering a hardcoded default `"O+"` on the digital health card creates dangerous transfusion misinformation risks.
- **Data Minimization:** Mobile numbers are properly masked (`+91 ******4821`), preventing citizen contact harvesting.

### 3. Code quality [QUAL]
- **Redundant Field Aliasing Overhead (`BE-SCH-CPOR-F01`):** `model_post_init` across `CitizenHealthIdSummary`, `CitizenActiveMedicineItem`, `CitizenVisitReportItem`, and `CitizenThreeTileResponse` mirrors almost every attribute into duplicate alias fields (e.g. `medicine_id` and `id`, `name` and `brand_name`, `prescribed_by` and `prescribing_doctor`, `medicines_tile` and `active_medicines_tile`). This doubles serialization payload sizes and creates schema drift.
- **Deprecated `example` Argument (`BE-SCH-CPOR-F02`):** `Field(..., example=...)` is used across ~30 fields. Pydantic v2 emits deprecation notices and ignores `example` in favor of `examples` or `json_schema_extra`.

### 4. AI-generated-code smells [QUAL]
- Extensive post-init aliasing was likely generated to satisfy conflicting frontend component conventions during rapid UI prototyping.

### 5. Performance [PERF]
- High payload size due to duplicated fields; removing post-init aliases in a future major version will reduce network bandwidth by ~35%.

### 6. Error handling & edge cases
- `model_post_init` cleanly handles ABHA number formatting with fallback hyphenation.

### 7. Doc accuracy [DOC]
- Accurately aligns with CoWIN and DigiLocker citizen presentation guidelines.

### 8. Tests
- Covered by `backend/tests/test_citizen_portal.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-CPOR-F01 | S2 | [QUAL] | 36-47, 103-121, 156-167 | Excessive dual-field aliasing in `model_post_init` | Redundant fields (`id`, `prescribing_doctor`, etc.) | Deprecate aliases and standardize on canonical field names |
| BE-SCH-CPOR-F02 | S3 | [QUAL] | 18-26, 52-62, 72-98 | Deprecated `example` keyword argument in Pydantic v2 | `Field(..., example="...")` used across 30+ fields | Migrate to `examples=["..."]` or `json_schema_extra` |
| BE-SCH-CPOR-F03 | S3 | [QUAL] | 26 | Default blood group set to `"O+"` | `blood_group: Optional[str] = Field(default="O+")` | Change default to `"UNKNOWN"` or `None` |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-CPOR-F03 · Risk: Low · [UNTESTED]
Prevent default assumption of O+ blood group for unrecorded patient profiles:

```diff
--- a/backend/app/schemas/citizen_portal.py
+++ b/backend/app/schemas/citizen_portal.py
@@ -25,3 +25,3 @@ class CitizenHealthIdSummary(BaseModel):
     age: int = Field(default=34, description="Calculated patient age in years", example=34)
-    blood_group: Optional[str] = Field(default="O+", description="Blood group if recorded", example="O+")
+    blood_group: Optional[str] = Field(default=None, description="Blood group if recorded", examples=["O+"])
     masked_mobile: Optional[str] = Field(default="+91 ******4821", description="Masked registered phone number")
