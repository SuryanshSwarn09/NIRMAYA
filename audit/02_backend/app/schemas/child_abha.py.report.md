# Audit Report: backend/app/schemas/child_abha.py

**Path:** `backend/app/schemas/child_abha.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 84 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation models for Child-ABHA issuance (Day 84 minor patient onboarding), guardian Aadhaar OTP challenges, DigiLocker birth certificate verification, and HL7 FHIR R4 `RelatedPerson` representation.
- **Risk Level:** **S1 (High)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `ChildAbhaOtpRequest.guardian_aadhaar_number` and `ChildAbhaRegistrationRequest.otp_code` are defined as unmasked strings without `repr=False` or `SecretStr`. Logging these requests exposes 12-digit guardian Aadhaar numbers and active OTP tokens in server logs, violating UIDAI regulations and DPDP Act 2023 Sec 9 (CWE-532 / CWE-359).

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Under Indian healthcare regulations and the Digital Personal Data Protection (DPDP) Act 2023, minor children cannot independently consent to processing personal health data. To create an Ayushman Bharat Health Account (ABHA) for a child, a verified legal parent or guardian must authenticate using their own Aadhaar OTP, furnish verifiable consent attestation, provide the child's birth certificate (verified via DigiLocker), and bind a sovereign proxy relationship (`RelatedPerson`). This file structures the OTP challenge payloads, registration models, DigiLocker verification proofs, and FHIR proxy records.

### How it works, step by step
1. `ChildGenderEnum` aligns gender categories with HL7 FHIR and ABDM standards (`MALE`, `FEMALE`, `OTHER`).
2. `ChildAbhaOtpRequest` receives the verified guardian's patient profile ID, 12-digit Aadhaar number, and statutory consent attestation boolean.
3. `ChildAbhaOtpResponse` returns a transient transaction ID (`transaction_id`) and masked mobile confirmation (`XXXXXX4821`).
4. `ChildAbhaRegistrationRequest` submits the 6-digit OTP code alongside the child's legal name, gender, birth date (`child_dob_iso`), and optional DigiLocker certificate URI.
5. `ChildAbhaRegistrationResponse` returns the issued 14-digit ABHA number, ABHA handle, proxy relationship ID, verification document SHA-256 fingerprint, and offline QR code payload.
6. `DigiLockerDocumentVerificationRequest` and `Response` model the verification handshake with DigiLocker certificate authorities.
7. `FhirRelatedPersonRepresentation` structures the proxy authority as an HL7 FHIR R4 `RelatedPerson` resource.

### Concepts and patterns used
- *DPDP Act 2023 Section 9 Minor Protections:* Explicit guardian consent attestation and zero-contamination record isolation.
- *Two-Step Challenge-Response:* Decoupled OTP generation and verification flows.
- *HL7 FHIR R4 RelatedPerson:* Mapping guardian proxy authority to standardized FHIR role codes (`PRN`, `MTH`, `FTH`, `GUARD`).

### Key lines to read first
- `child_abha.py:15-20`: `ChildAbhaOtpRequest` guardian authentication.
- `child_abha.py:30-41`: `ChildAbhaRegistrationRequest` minor registration payload.
- `child_abha.py:43-55`: `ChildAbhaRegistrationResponse` issued credential model.
- `child_abha.py:74-84`: `FhirRelatedPersonRepresentation` FHIR proxy mapping.

### How to change it safely
Ensure `guardian_aadhaar_number` and `otp_code` are masked using `repr=False`. When verifying birth dates, enforce that the child is strictly under 18 years of age at registration time.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `enum` (Enum), `typing` (Any, Dict, List, Optional), `uuid`, `pydantic` (BaseModel, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/child_abha_service.py`, `backend/app/api/v1/endpoints/child_abha.py`.
- **Public Surface:** Enum `ChildGenderEnum`; Models `ChildAbhaOtpRequest`, `ChildAbhaOtpResponse`, `ChildAbhaRegistrationRequest`, `ChildAbhaRegistrationResponse`, `DigiLockerDocumentVerificationRequest`, `DigiLockerDocumentVerificationResponse`, `FhirRelatedPersonRepresentation`.

### 2. Security [SEC]
- **Plaintext Guardian Aadhaar & OTP Exposure (CWE-359 / CWE-532):** In `ChildAbhaOtpRequest.guardian_aadhaar_number` (line 18) and `ChildAbhaRegistrationRequest.otp_code` (line 33), fields lack `repr=False` (`BE-SCH-CABH-F01`). Request logging will persist full 12-digit Aadhaar numbers and live OTPs in application log stores, violating UIDAI security mandates.
- **Zero-Contamination Record Isolation:** `ChildAbhaRegistrationResponse.zero_contamination_isolated` reinforces the architectural guarantee that the child's medical record is created in a sovereign, independent vault separate from the guardian.

### 3. Code quality [QUAL]
- **Unvalidated Date String for Minor DOB (`BE-SCH-CABH-F02`):** In `ChildAbhaRegistrationRequest.child_dob_iso` (line 37), the field is typed as `str` rather than `date`. Although the docstring states "must be < 18 years", no validator exists to parse the ISO string or verify that `(date.today() - dob).days < 18 * 365`.
- **Unvalidated Document Hash Format (`BE-SCH-CABH-F03`):** In `ChildAbhaRegistrationResponse.verification_document_hash` (line 51) and `DigiLockerDocumentVerificationResponse.document_sha256` (line 68), SHA-256 strings have no regex check (`^[a-fA-F0-9]{64}$`).
- **Missing Module Docstring (`BE-SCH-CABH-F04`):** File starts directly with imports on line 1 without a module docstring.

### 4. AI-generated-code smells [QUAL]
- Clean, focused schema design adhering to ABDM Day 84 specification.

### 5. Performance [PERF]
- Fast, non-blocking model validation; lightweight memory footprint.

### 6. Error handling & edge cases
- `expires_in_seconds: int = Field(600)` clearly defines the OTP challenge expiration window.

### 7. Doc accuracy [DOC]
- Aligns with Day 84 Child-ABHA issuance specification and NRCeS HL7 FHIR guidelines.

### 8. Tests
- Covered by `backend/tests/test_child_abha.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-CABH-F01 | S1 | [SEC] | 18, 33 | Plaintext Aadhaar and OTP exposed in string `repr` | `guardian_aadhaar_number: str`, `otp_code: str` | Add `repr=False` to prevent log leakage |
| BE-SCH-CABH-F02 | S2 | [QUAL] | 37 | Child DOB typed as raw string without minor age enforcement | `child_dob_iso: str` without validation | Type as `date` and add validator checking age < 18 |
| BE-SCH-CABH-F03 | S3 | [QUAL] | 51, 68 | SHA-256 document fingerprints lack regex validation | `verification_document_hash: str` without pattern | Add regex pattern `^[a-f0-9]{64}$` |
| BE-SCH-CABH-F04 | S4 | [QUAL] | 1 | Missing module-level docstring | File begins directly with imports | Add explanatory module docstring |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-CABH-F01 · Risk: Low · [UNTESTED]
Mask guardian Aadhaar number and OTP code in string representations:

```diff
--- a/backend/app/schemas/child_abha.py
+++ b/backend/app/schemas/child_abha.py
@@ -17,3 +17,3 @@ class ChildAbhaOtpRequest(BaseModel):
     guardian_patient_id: str = Field(..., description="Unique ID of verified guardian patient profile")
-    guardian_aadhaar_number: str = Field(..., min_length=12, max_length=12, description="12-digit Aadhaar number of parent/guardian")
+    guardian_aadhaar_number: str = Field(..., min_length=12, max_length=12, description="12-digit Aadhaar number of parent/guardian", repr=False)
     guardian_consent_attestation: bool = Field(..., description="Verifiable consent attestation under DPDP Act 2023 Sec 9")
@@ -32,3 +32,3 @@ class ChildAbhaRegistrationRequest(BaseModel):
     transaction_id: str = Field(..., description="Transaction ID returned from OTP challenge")
-    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
+    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code", repr=False)
     guardian_patient_id: str = Field(..., description="Unique ID of guardian patient profile")
