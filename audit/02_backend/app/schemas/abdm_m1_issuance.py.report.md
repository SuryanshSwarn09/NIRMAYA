# Audit Report: backend/app/schemas/abdm_m1_issuance.py

**Path:** `backend/app/schemas/abdm_m1_issuance.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 126 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for 14-digit ABHA Number issuance, `@abdm` Personal Health Record (PHR) handle reservation, and Healthcare Professional Registry (HPR) onboarding under ABDM Milestone 1.
- **Risk Level:** **S3 (Low)**
- **Verdict:** **READY**
- **Single Most Important Finding:** Entity identifier fields (`patient_id`, `doctor_id`) are typed as plain strings without UUID validation, permitting malformed ID strings to reach service layer handlers.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
After a citizen completes identity verification via Aadhaar, they must be issued an official 14-digit ABHA Number (e.g. `91-8472-1092-4821`) and have the option to reserve a human-friendly personal health handle (e.g. `arun.patel@abdm`). Similarly, medical practitioners need to onboard into the National Healthcare Professional Registry (`@hpr.abdm`). This file manages handle syntax validation, availability queries, and registration payloads.

### How it works, step by step
1. `AbhaNumberCreateRequest` and `AbhaNumberCreateResponse` handle the generation and assignment of the official 14-digit ABHA Number.
2. `PhrAvailabilityResponse` reports whether a requested handle is available and suggests alternatives if taken.
3. `PhrLinkRequest` validates handle syntax (3–32 chars, lowercase, numbers, dots, underscores) and ensures the `@abdm` suffix is attached.
4. `HprOnboardRequest` and `HprOnboardResponse` validate doctor registration numbers, state medical councils, and `@hpr.abdm` practitioner handles.

### Concepts and patterns used
- *Automated Domain Suffixing:* Intelligently appending `@abdm` or `@hpr.abdm` if omitted by user input.
- *Strict Handle Regex Validation:* Guaranteeing uniform namespace compliance before database reservation.
- *ABDM Milestone 1 Integration:* Conforming to National Health Authority (NHA) naming conventions.

### Key lines to read first
- `abdm_m1_issuance.py:19-33`: `AbhaNumberCreateResponse` with formatted 14-digit ABHA.
- `abdm_m1_issuance.py:59-69`: `PhrLinkRequest` and `@field_validator("abha_address")`.
- `abdm_m1_issuance.py:97-107`: `HprOnboardRequest` and `@field_validator("hpr_handle")`.

### How to change it safely
Do not change the handle regex `^[a-z0-9._]{3,32}$` without verifying compatibility with ABDM Gateway handle rules. Always preserve lowercase normalization.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `re`, `datetime`, `typing`, `pydantic` (BaseModel, Field, ConfigDict, field_validator).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/abdm_m1_issuance_service.py`, `backend/app/api/v1/endpoints/abdm_m1.py`.
- **Public Surface:** Classes `AbhaNumberCreateRequest`, `AbhaNumberCreateResponse`, `PhrAvailabilityResponse`, `PhrLinkRequest`, `PhrLinkResponse`, `HprOnboardRequest`, `HprOnboardResponse`.

### 2. Security [SEC]
- **Input Sanitization & Injection Prevention (CWE-20):** Field validators on both `abha_address` and `hpr_handle` enforce strict character whitelisting (`^[a-z0-9._]{3,32}$`) and lowercase normalization, preventing directory traversal, XSS, or header injection via malformed health identifiers.

### 3. Code quality [QUAL]
- **Unconstrained Entity Identifiers (Lines 12, 22, 53, 74, 89, 112):** `patient_id` and `doctor_id` are typed as bare `str` rather than `UUID` or `Field(pattern=...)`, allowing arbitrary non-UUID strings to pass initial schema validation (`BE-ISU-F01`).
- Robust handling of handle suffixes: automatically transforms `arun.patel` into `arun.patel@abdm`.

### 4. AI-generated-code smells [QUAL]
- None; the models display excellent attention to detail regarding ABDM national health handle syntax.

### 5. Performance [PERF]
- Highly efficient regex validation.

### 6. Error handling & edge cases
- Splitting by `@` prior to regex matching gracefully handles inputs provided with or without the `@abdm` / `@hpr.abdm` suffix.

### 7. Doc accuracy [DOC]
- Perfectly conforms to Month 3 Day 44 roadmap specifications.

### 8. Tests
- Covered by `backend/tests/test_abdm_m1.py` and `backend/tests/test_abdm_issuance.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-ISU-F01 | S3 | [QUAL] | 12, 53, 89 | Unvalidated UUID string formats on entity identifiers | `patient_id: str = Field(...)` | Use `UUID4` or add regex pattern constraint |

---

## Suggested Patches (NOT Applied)

### S3 One-Line Fix
- **BE-ISU-F01:** In `AbhaNumberCreateRequest`, `PhrLinkRequest`, and `HprOnboardRequest`, add regex validation or type as `pydantic.UUID4` for `patient_id` and `doctor_id`.

---

## Verdict

**READY** — Pristine, production-ready ABDM Milestone 1 handle reservation and ABHA issuance schema suite.
