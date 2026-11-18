# Audit Report: backend/app/schemas/abdm_m1.py

**Path:** `backend/app/schemas/abdm_m1.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 114 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for ABDM Milestone 1 direct Aadhaar demographic OTP generation, verification, and e-KYC profile synchronization.
- **Risk Level:** **S1 (High)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `AadhaarOtpGenerateRequest.aadhaar_number` is a plain unmasked string; logging request bodies will persist full 12-digit plaintext Aadhaar numbers in server logs, violating the Aadhaar Act 2016 and UIDAI data security regulations.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
To create or link an ABHA (Ayushman Bharat Health Account) ID in Milestone 1, citizens must prove their identity via UIDAI Aadhaar e-KYC. This requires a two-step flow: requesting an OTP sent to the citizen's Aadhaar-linked mobile number, and submitting the received 6-digit OTP to retrieve verified demographic claims (name, gender, DOB, address). This file structures those payloads and enforces digit validation.

### How it works, step by step
1. `AadhaarOtpGenerateRequest` receives the citizen's 12-digit Aadhaar number, stripping whitespace and hyphens via a regex field validator.
2. `AadhaarOtpGenerateResponse` returns a session transaction ID (`txn_id`) and masked mobile confirmation.
3. `AadhaarOtpVerifyRequest` submits the `txn_id` and 6-digit numeric `otp`.
4. `AadhaarOtpVerifyResponse` returns verified e-KYC demographic claims (`AadhaarDemographicData`), including masked Aadhaar (`XXXX-XXXX-4821`) and structured `AadhaarAddress`.
5. `UnifiedIdentitySyncResponse` confirms synchronization of verified demographics into the patient's local `PatientProfile`.

### Concepts and patterns used
- *Two-Step Challenge-Response Authentication:* Decoupled OTP generation and verification transactions.
- *UIDAI Data Minimization:* Returning only masked Aadhaar numbers (`XXXX-XXXX-4821`) in response payloads.
- *Strict Pydantic Field Validation:* Enforcing exact numerical lengths (12 digits for Aadhaar, 6 digits for OTP) before hitting upstream APIs.

### Key lines to read first
- `abdm_m1.py:42-57`: `AadhaarOtpGenerateRequest` and Aadhaar format validator.
- `abdm_m1.py:73-91`: `AadhaarOtpVerifyRequest` and OTP numeric validator.
- `abdm_m1.py:25-40`: `AadhaarDemographicData` verified claims schema.

### How to change it safely
Never allow the full 12-digit Aadhaar number to be returned in response objects; always preserve the masked format in `AadhaarDemographicData`. Always ensure `validate_aadhaar_format` sanitizes hyphens and spaces.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `re`, `typing`, `pydantic` (BaseModel, Field, ConfigDict, field_validator).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/abdm_m1_service.py`, `backend/app/api/v1/endpoints/abdm_m1.py`.
- **Public Surface:** Classes `AadhaarAddress`, `AadhaarDemographicData`, `AadhaarOtpGenerateRequest`, `AadhaarOtpGenerateResponse`, `AadhaarOtpVerifyRequest`, `AadhaarOtpVerifyResponse`, `UnifiedIdentitySyncResponse`.

### 2. Security [SEC]
- **Plaintext Aadhaar Exposure in Logs (CWE-359 / CWE-532 / Aadhaar Act 2016):** `AadhaarOtpGenerateRequest.aadhaar_number` (line 45-48) is a standard `str` field without `repr=False` or `SecretStr`. Under the Aadhaar (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act 2016 and UIDAI Security Regulations, persisting or logging full 12-digit Aadhaar numbers in plaintext log files or tracebacks is a punishable regulatory violation. Masking via `Field(repr=False)` or `SecretStr` is mandatory (`BE-M1-F01`).
- **OTP Exposure in Logs (CWE-532):** `AadhaarOtpVerifyRequest.otp` (lines 77-82) lacks `repr=False`, permitting OTP tokens to leak in debugging or access logs (`BE-M1-F02`).
- **Data Minimization:** `AadhaarDemographicData` correctly restricts output to `masked_aadhaar` (line 31), complying with privacy principles.

### 3. Code quality [QUAL]
- **Missing Verhoeff Checksum Validation (Lines 50-56):** `validate_aadhaar_format` checks that the string contains 12 digits (`^\d{12}$`), but does not evaluate the Verhoeff checksum algorithm (used by UIDAI to detect transposition errors). Invalid Aadhaar numbers will needlessly dispatch OTP requests to upstream gateways (`BE-M1-F03`).
- Clean Pydantic v2 `@field_validator` implementations.

### 4. AI-generated-code smells [QUAL]
- None; the two-step verification models strictly align with UIDAI Aadhaar e-KYC and ABDM M1 specifications.

### 5. Performance [PERF]
- Fast regex evaluations during schema parsing.

### 6. Error handling & edge cases
- `clean = re.sub(r"[\s\-]", "", v.strip())` cleanly handles varied user input formats (e.g. `9184-7210-4821` or `9184 7210 4821`).

### 7. Doc accuracy [DOC]
- Perfectly conforms to Month 3 Day 43 Aadhaar OTP verification specifications.

### 8. Tests
- Covered by `backend/tests/test_abdm_m1.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-M1-F01 | S1 | [SEC] | 45-48 | Plaintext Aadhaar number exposed in string `repr` | `aadhaar_number: str = Field(...)` without `repr=False` | Add `repr=False` to prevent logging full Aadhaar number |
| BE-M1-F02 | S2 | [SEC] | 77-82 | OTP token exposed in string `repr` | `otp: str = Field(...)` without `repr=False` | Add `repr=False` to `otp` Field |
| BE-M1-F03 | S3 | [QUAL] | 50-56 | Missing Verhoeff checksum validation | Only evaluates `^\d{12}$` | Implement Verhoeff algorithm in validator |

---

## Suggested Patches (NOT Applied)

### Patch BE-M1-F01 · Risk: Low · [UNTESTED]
Mask Aadhaar numbers and OTP tokens in string representations to ensure regulatory compliance:

```diff
--- a/backend/app/schemas/abdm_m1.py
+++ b/backend/app/schemas/abdm_m1.py
@@ -47,4 +47,5 @@ class AadhaarOtpGenerateRequest(BaseModel):
         description="12-digit UIDAI Aadhaar number (hyphens and spaces allowed)",
         example="9184 7210 4821",
+        repr=False,
     )
 
@@ -81,4 +82,5 @@ class AadhaarOtpVerifyRequest(BaseModel):
         description="6-digit numeric OTP received on registered mobile",
         example="123456",
+        repr=False,
     )
```

---

## Verdict

**READY-WITH-FIXES** — Excellent e-KYC schema with strong regex sanitization; masking `aadhaar_number` and `otp` in `repr` is essential to meet UIDAI legal compliance.
