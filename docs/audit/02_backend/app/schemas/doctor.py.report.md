# Audit Report: backend/app/schemas/doctor.py

**Path:** `backend/app/schemas/doctor.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 106 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for DoctorProfile management, clinical licensing, consultation fee configuration, and ABDM Healthcare Professional Registry (HPR) onboarding.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** In `DoctorProfileCreate`, `user_id` is optional (`Optional[str] = None`); if invoked during admin provisioning or unauthenticated onboarding workflows, an omitted `user_id` will crash database insert operations due to PostgreSQL `NOT NULL` constraints on `doctor_profiles.user_id`.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Healthcare platforms must ensure that only licensed, credentialed medical practitioners can prescribe medications, sign SOAP clinical notes, and access patient health records. Under the Ayushman Bharat Digital Mission (ABDM), doctors are identified nationally through the Healthcare Professional Registry (HPR) with unique HPR handles (e.g. `dr.priya.patel@hpr.abdm`) and verified state medical council registration numbers. This file defines the data contracts used to create, update, and serialize doctor profiles, consultation fees, and clinical specialties.

### How it works, step by step
1. `DoctorProfileBase` structures core clinical credentials: state medical council registration license number, issuing authority, clinical specialty (`MedicalSpecialty`), academic qualifications, experience years, consultation fee, teleconsultation availability, and ABDM HPR identifier.
2. `DoctorProfileCreate` extends base attributes with an optional `user_id` linking the clinical profile to the authenticated platform user.
3. `DoctorProfileUpdate` defines optional fields for updating practice settings, hospital affiliations, bio, and fees.
4. `DoctorProfileResponse` serializes the finalized doctor profile record, including creation/update timestamps and linked user account metadata (`UserResponse`).

### Concepts and patterns used
- *ABDM HPR Handle Validation:* Enforcing regex format constraints (`^[a-zA-Z0-9._]{3,40}@hpr\.abdm$`) for national healthcare provider handles.
- *Clinical Specialty Mapping:* Standardized `MedicalSpecialty` enum mapping to SNOMED-CT and HL7 FHIR `PractitionerRole`.
- *Modern Pydantic v2 Syntax:* Proper use of `examples=[...]` rather than deprecated `example` arguments.

### Key lines to read first
- `doctor.py:10-71`: `DoctorProfileBase` clinical attributes and HPR regex.
- `doctor.py:73-80`: `DoctorProfileCreate` onboarding payload.
- `doctor.py:82-95`: `DoctorProfileUpdate` profile modification schema.
- `doctor.py:97-106`: `DoctorProfileResponse` query output model.

### How to change it safely
When modifying doctor schemas, ensure any added specialties are registered in `app.models.enums.MedicalSpecialty`. If expanding HPR handle formats, adjust the `hpr_id` regex pattern to support all official ABDM registry suffixes.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing` (Optional), `pydantic` (BaseModel, ConfigDict, Field), `app.models.enums.MedicalSpecialty`, `app.schemas.user.UserResponse`.
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/doctor_service.py`, `backend/app/api/v1/endpoints/doctors.py`.
- **Public Surface:** Models `DoctorProfileBase`, `DoctorProfileCreate`, `DoctorProfileUpdate`, `DoctorProfileResponse`.

### 2. Security [SEC]
- **Practitioner Licensing Integrity:** `registration_number` and `medical_council` ensure that clinical encounters are traceable to certified state medical council licensees.
- **HPR Verification:** `hpr_id` format validation links practitioners to the national ABDM trust registry.

### 3. Code quality [QUAL]
- **Optional Foreign Key in Create Schema (`BE-SCH-DOC-F01`):** In `DoctorProfileCreate` (lines 73-80), `user_id` is typed as `Optional[str] = None`. While the endpoint might inject `current_user.id`, if the schema is reused by administrative provisioning endpoints without authenticated context, omitting `user_id` results in unhandled database 500 errors.
- **Strict HPR Regex Format (`BE-SCH-DOC-F02`):** `pattern=r"^[a-zA-Z0-9._]{3,40}@hpr\.abdm$"` (line 67) rejects valid alternative ABDM HPR handles (e.g. `@hpr` or 14-digit numeric HPR IDs `14-XXXX-XXXX-XXXX`), causing validation failures for legitimate practitioners onboarded under alternative HPR schemes.
- Excellent modern Pydantic v2 adherence (`examples=[...]` on lines 17, 23, 33, 40, 46, 52, 69).

### 4. AI-generated-code smells [QUAL]
- None; the model cleanly adheres to clinical onboarding specifications.

### 5. Performance [PERF]
- Fast, non-blocking model validation; lightweight memory footprint.

### 6. Error handling & edge cases
- Bounded integers (`experience_years: ge=0, le=75`, `consultation_fee: ge=0`) prevent negative or absurd practitioner attributes.

### 7. Doc accuracy [DOC]
- Aligns with National Medical Commission (NMC) registration guidelines and ABDM HPR specifications.

### 8. Tests
- Covered by `backend/tests/test_doctors.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-DOC-F01 | S2 | [QUAL] | 76-79 | `user_id` is optional in create payload | `user_id: Optional[str] = None` | Validate `user_id` or document mandatory endpoint injection |
| BE-SCH-DOC-F02 | S3 | [QUAL] | 67, 94 | HPR regex pattern overly strict | Rejects alternative valid HPR handles like `@hpr` or 14-digit IDs | Broaden regex pattern to `^([a-zA-Z0-9._]{3,40}@(hpr\.abdm|hpr)|\d{2}-\d{4}-\d{4}-\d{4})$` |
| BE-SCH-DOC-F03 | S4 | [QUAL] | 17-69 | Clean Pydantic v2 `examples=[...]` usage | Adheres to modern specification | Best practice reference |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-DOC-F02 · Risk: Low · [UNTESTED]
Broaden HPR handle regex pattern to support all official ABDM formats:

```diff
--- a/backend/app/schemas/doctor.py
+++ b/backend/app/schemas/doctor.py
@@ -66,3 +66,3 @@ class DoctorProfileBase(BaseModel):
     hpr_id: Optional[str] = Field(
         default=None,
-        pattern=r"^[a-zA-Z0-9._]{3,40}@hpr\.abdm$",
+        pattern=r"^([a-zA-Z0-9._]{3,40}@(hpr\.abdm|hpr)|\d{2}-\d{4}-\d{4}-\d{4})$",
         description="Official ABDM Healthcare Professional Registry handle ending in @hpr.abdm",
