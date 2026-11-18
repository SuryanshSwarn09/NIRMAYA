# Audit Report: backend/app/schemas/abha_card.py

**Path:** `backend/app/schemas/abha_card.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 73 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation models for ABDM Digital ABHA ID Cards, compact QR code payloads, cryptographic attestations, and QR verification endpoints.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `AbhaCardData` lacks regex and enum validation on primary identity attributes (`abha_number`, `abha_address`, `gender`), permitting malformed demographic data to be issued onto signed digital cards and QR payloads.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Under the Ayushman Bharat Digital Mission (ABDM), every Indian citizen is entitled to a verifiable digital ABHA (Ayushman Bharat Health Account) card. This card displays demographic attributes (name, gender, DOB, address, masked mobile, emergency contact) and includes a compact, scannable QR code. When a hospital or clinic scans the QR code, the system validates the digital signature and automatically registers the patient. This file defines the card data structure, QR code contents, and verification request/response schemas.

### How it works, step by step
1. `AbhaCardData` defines the complete demographic profile printed on the physical/digital card, including 14-digit ABHA number, ABHA address handle, blood group, and emergency contact details.
2. `AbhaQrPayload` defines the compact, canonical claim dictionary embedded inside the 2D QR barcode, sealed with a cryptographic signature.
3. `AbhaCardResponse` bundles the card demographic data, the serialized QR payload string, and issuance timestamp.
4. `AbhaQrVerificationRequest` receives a raw scanned QR string from mobile or desktop scanners.
5. `AbhaQrVerificationResponse` returns whether the scanned QR signature is cryptographically valid alongside the decoded claims.

### Concepts and patterns used
- *Compact Claim Representation:* Using abbreviated field keys (`hidn`, `hid`, `dob`) in `AbhaQrPayload` to minimize QR code matrix density for reliable camera scanning.
- *Cryptographic Attestation:* Digital signatures sealing card claims against forgery.
- *Data Minimization:* Masked phone number and selective demographic claims in QR payloads.

### Key lines to read first
- `abha_card.py:8-34`: `AbhaCardData` full demographic claims.
- `abha_card.py:36-50`: `AbhaQrPayload` compact QR specification.
- `abha_card.py:52-59`: `AbhaCardResponse` API response model.
- `abha_card.py:61-73`: QR verification models (`AbhaQrVerificationRequest`, `AbhaQrVerificationResponse`).

### How to change it safely
When modifying QR payload fields, ensure the keys remain compact to prevent inflating QR density, which impairs optical scanning in low-light or low-resolution camera conditions.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing`, `pydantic` (BaseModel, ConfigDict, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/abha_card_service.py`, `backend/app/api/v1/endpoints/abha_card.py`.
- **Public Surface:** `AbhaCardData`, `AbhaQrPayload`, `AbhaCardResponse`, `AbhaQrVerificationRequest`, `AbhaQrVerificationResponse`.

### 2. Security [SEC]
- **Symmetric vs Asymmetric QR Signature (`BE-ABH-F02`):** `AbhaQrPayload.signature` (line 49) describes an "HMAC-SHA256 signature over canonical claims". HMAC relies on a shared symmetric secret, meaning any offline scanning app would require the master secret key to verify signatures. NHA standards specify asymmetric signatures (RSA-SHA256 or ECDSA) so public keys can be distributed freely for verification.
- **Demographic Privacy:** Mobile numbers are masked (`masked mobile phone number`), preventing mass harvesting of citizen phone numbers from scanned cards.

### 3. Code quality [QUAL]
- **Missing Format Validators on Identity Fields (`BE-ABH-F01`):** `AbhaCardData.abha_number` (line 14) has no pattern validation enforcing the standard 14-digit format `^\d{2}-\d{4}-\d{4}-\d{4}$`. `gender` (line 17) uses `str` instead of `Literal["M", "F", "O"]`.
- **String Types for Timestamps (`BE-ABH-F03`):** `issue_date`, `issued_at`, and `verified_at` are typed as `str` instead of `datetime`.

### 4. AI-generated-code smells [QUAL]
- Clean, focused schema design; compact naming aligns with NHA guidelines.

### 5. Performance [PERF]
- Compact QR payloads keep barcode size small, ensuring rapid camera detection and decode on low-cost Android mobile devices.

### 6. Error handling & edge cases
- `AbhaQrVerificationResponse.is_valid: bool` and `claims: Optional[Dict[str, Any]]` ensure that invalid or corrupt scans return descriptive error messages without exceptions.

### 7. Doc accuracy [DOC]
- Aligns with Day 88 digital ABHA card design specifications.

### 8. Tests
- Covered by `backend/tests/test_abha_card.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-ABH-F01 | S2 | [QUAL] | 14, 17 | Missing validation for ABHA number and gender | `abha_number: str`, `gender: str` without constraints | Add regex pattern for ABHA number and `Literal` for gender |
| BE-ABH-F02 | S2 | [SEC] | 49 | Symmetric HMAC signature on public QR payload | `signature: str = Field(description="HMAC-SHA256...")` | Migrate to asymmetric ECDSA/RSA signature for public verification |
| BE-ABH-F03 | S3 | [QUAL] | 48, 58, 73 | Timestamps typed as raw strings | `issue_date`, `issued_at`, `verified_at` use `str` | Use `datetime` with UTC factory |

---

## Suggested Patches (NOT Applied)

### Patch BE-ABH-F01 · Risk: Low · [UNTESTED]
Add format validation for ABHA number and gender constraints:

```diff
--- a/backend/app/schemas/abha_card.py
+++ b/backend/app/schemas/abha_card.py
@@ -3,7 +3,7 @@
 from datetime import datetime
-from typing import Any, Dict, List, Optional
+from typing import Any, Dict, List, Literal, Optional
 from pydantic import BaseModel, ConfigDict, Field
 
 
 class AbhaCardData(BaseModel):
@@ -14,4 +14,4 @@ class AbhaCardData(BaseModel):
-    abha_number: str = Field(description="14-digit hyphenated ABHA number, e.g. 91-8472-1092-4821")
+    abha_number: str = Field(pattern=r"^\d{2}-\d{4}-\d{4}-\d{4}$", description="14-digit hyphenated ABHA number")
     abha_address: str = Field(description="Health ID handle, e.g. arun.patel@abdm")
     name: str = Field(description="Full legal name of the cardholder")
-    gender: str = Field(description="Gender abbreviation: M, F, or O")
+    gender: Literal["M", "F", "O"] = Field(description="Gender abbreviation: M, F, or O")
