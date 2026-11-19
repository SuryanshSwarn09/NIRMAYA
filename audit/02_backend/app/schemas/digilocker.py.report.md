# Audit Report: backend/app/schemas/digilocker.py

**Path:** `backend/app/schemas/digilocker.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 98 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for DigiLocker OAuth 2.0 PKCE authorization, token exchange, structured e-Aadhaar XML parsing, and demographic synchronization with patient profiles.
- **Risk Level:** **S1 (High)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `DigiLockerTokenResponse.access_token` and `DigiLockerCallbackRequest.code_verifier` are defined as unmasked strings without `repr=False` or `SecretStr`. Standard logging or exception traces serialize active DigiLocker government OAuth access tokens and PKCE verifiers into plaintext server logs, risking token theft and unauthorized citizen document access (CWE-532 / CWE-312).

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
DigiLocker is India's sovereign digital document repository operated by the Ministry of Electronics and IT (MeitY). To enable seamless, paperless patient registration, NIRMAYA allows citizens to authenticate via DigiLocker using OAuth 2.0 with Proof Key for Code Exchange (PKCE). Upon authorization, NIRMAYA retrieves the citizen's digitally signed e-Aadhaar XML, validates the UIDAI X.509 signature, extracts certified demographic claims (name, gender, date of birth, structured address, photo), and synchronizes them into the patient's sovereign medical vault. This file models the OAuth endpoints, token responses, e-Aadhaar address parsing, and sync confirmations.

### How it works, step by step
1. `DigiLockerAuthorizeUrlResponse` returns the generated OAuth 2.0 authorization URL, cryptographic CSRF `state` token, and RFC 7636 `code_challenge` (S256).
2. `DigiLockerCallbackRequest` receives the authorization code, state parameter, and `code_verifier` from frontend OAuth redirect handlers.
3. `DigiLockerTokenResponse` receives the issued bearer access token, expiration seconds, granted scopes, and citizen `digilocker_id`.
4. `EAadhaarAddress` models structured residential claims (care_of, house, street, locality, district, state, pincode, formatted_address).
5. `EAadhaarDemographics` encapsulates full certified citizen claims including masked Aadhaar (`XXXX-XXXX-4821`), base64 photograph, and UIDAI signature validity.
6. `DigiLockerVerificationResult` and `DigiLockerSyncPatientResponse` structure the final verification result and confirm synchronization into the patient's profile.

### Concepts and patterns used
- *RFC 7636 PKCE OAuth 2.0 Flow:* Secure authorization code flow preventing code interception attacks.
- *UIDAI X.509 Cryptographic Verification:* Tracking digital signature validity of issued government credentials.
- *Data Minimization:* Returning only masked Aadhaar numbers (`XXXX-XXXX-4821`).

### Key lines to read first
- `digilocker.py:8-17`: `DigiLockerAuthorizeUrlResponse` PKCE parameters.
- `digilocker.py:19-28`: `DigiLockerCallbackRequest` authorization callback model.
- `digilocker.py:30-40`: `DigiLockerTokenResponse` bearer token schema.
- `digilocker.py:58-75`: `EAadhaarDemographics` certified identity claims.
- `digilocker.py:88-98`: `DigiLockerSyncPatientResponse` patient sync response.

### How to change it safely
Ensure `access_token` and `code_verifier` are masked using `repr=False`. Always maintain `photo_base64` as an optional field and protect it from log output.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `typing` (Optional), `pydantic` (BaseModel, Field, ConfigDict).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/digilocker_service.py`, `backend/app/api/v1/endpoints/digilocker.py`.
- **Public Surface:** Models `DigiLockerAuthorizeUrlResponse`, `DigiLockerCallbackRequest`, `DigiLockerTokenResponse`, `EAadhaarAddress`, `EAadhaarDemographics`, `DigiLockerVerificationResult`, `DigiLockerSyncPatientResponse`.

### 2. Security & Privacy [SEC]
- **Cleartext OAuth Token & PKCE Secret Exposure (CWE-532 / CWE-312):** `DigiLockerTokenResponse.access_token` (line 33) and `DigiLockerCallbackRequest.code_verifier` (line 24) are plain string fields (`BE-SCH-DLK-F01`). Logging these models writes active OAuth tokens to disk, allowing attackers to access citizens' DigiLocker documents. Adding `repr=False` is mandatory.
- **Biometric Photo In String Repr (`BE-SCH-DLK-F02`):** `EAadhaarDemographics.photo_base64` (line 65) contains raw base64 JPEG biometric data. Logging `EAadhaarDemographics` serializes tens of kilobytes of base64 image data into application logs, causing log bloat and biometric data spill. Adding `repr=False` prevents this.

### 3. Code quality [QUAL]
- **Deprecated `example` Keyword Argument (`BE-SCH-DLK-F03`):** `Field(..., example=...)` is used across lines 61, 62, 63, 64, 81. In Pydantic v2, `examples=[...]` or `json_schema_extra` should be used.
- **Unvalidated Postal Pincode (`BE-SCH-DLK-F04`):** In `EAadhaarAddress.pincode` (line 52), the 6-digit Indian postal code lacks regex pattern validation (`^\d{6}$`).

### 4. AI-generated-code smells [QUAL]
- None; the schemas follow RFC 7636 PKCE standards and official DigiLocker API guidelines.

### 5. Performance [PERF]
- Parsing structured XML demographics into Pydantic models executes in sub-millisecond time.

### 6. Error handling & edge cases
- String bounds (`code: min_length=1`, `state: min_length=1`) in `DigiLockerCallbackRequest` reject empty OAuth callback parameters.

### 7. Doc accuracy [DOC]
- Aligns with MeitY DigiLocker API Specification v2.0 and UIDAI e-Aadhaar guidelines.

### 8. Tests
- Covered by `backend/tests/test_digilocker.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-DLK-F01 | S1 | [SEC] | 24, 33 | OAuth bearer tokens and PKCE verifier exposed in string `repr` | `access_token: str`, `code_verifier: Optional[str]` | Add `repr=False` or wrap with `SecretStr` |
| BE-SCH-DLK-F02 | S2 | [SEC] | 65 | Base64 biometric photograph serialized in string `repr` | `photo_base64: Optional[str]` without `repr=False` | Add `repr=False` to prevent log bloat and PII leak |
| BE-SCH-DLK-F03 | S3 | [QUAL] | 61-64, 81 | Deprecated `example` keyword argument in Pydantic v2 | `Field(..., example="...")` used across 5 fields | Migrate to `examples=["..."]` or `json_schema_extra` |
| BE-SCH-DLK-F04 | S3 | [QUAL] | 52 | Pincode lacks 6-digit regex format validation | `pincode: Optional[str]` without pattern | Add regex pattern `^\d{6}$` |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-DLK-F01 · Risk: Low · [UNTESTED]
Mask DigiLocker OAuth access tokens, PKCE verifiers, and biometric photos in string representations:

```diff
--- a/backend/app/schemas/digilocker.py
+++ b/backend/app/schemas/digilocker.py
@@ -25,2 +25,3 @@ class DigiLockerCallbackRequest(BaseModel):
         description="RFC 7636 PKCE code verifier generated during authorization URL creation",
+        repr=False,
     )
@@ -33,3 +34,3 @@ class DigiLockerTokenResponse(BaseModel):
-    access_token: str = Field(description="Bearer access token for DigiLocker API queries")
+    access_token: str = Field(description="Bearer access token for DigiLocker API queries", repr=False)
     expires_in: int = Field(default=3600, description="Token validity window in seconds")
@@ -65,3 +66,3 @@ class EAadhaarDemographics(BaseModel):
-    photo_base64: Optional[str] = Field(default=None, description="Base64-encoded JPEG avatar photograph from Aadhaar")
+    photo_base64: Optional[str] = Field(default=None, repr=False, description="Base64-encoded JPEG avatar photograph from Aadhaar")
     address: EAadhaarAddress = Field(description="Structured residential address")
