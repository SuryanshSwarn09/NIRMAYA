# Technical Audit Report: backend/app/services/abha_card.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/abha_card.py` implements the service layer for generating digital ABHA ID cards and cryptographically signing and verifying ABHA QR codes. It extracts demographic and clinical metadata from `PatientProfile` and `User` models, masks telephone numbers according to privacy rules, formats gender and blood group enumerations, serializes compact claims payloads, and generates digital signatures. The audit identified two critical **S1** vulnerabilities: fallback logic creates counterfeit cards with hardcoded dummy ABHA numbers (`"91-8472-1092-4821"`) when a patient has no linked ABHA, and QR signing uses local symmetric HMAC-SHA256 with `settings.SECRET_KEY` instead of NHA's asymmetric PKI infrastructure, preventing interoperability with external healthcare facilities.

### Architectural Roster
- **Module Name:** `backend/app/services/abha_card.py`
- **Primary Responsibility:** ABHA card metadata preparation, QR payload serialization, HMAC-SHA256 signature generation, and QR scan verification.
- **Upstream Dependencies:**
  - `hmac`, `hashlib`, `json`
  - `app.core.config.settings`
  - `app.models.patient.PatientProfile`
  - `app.models.user.User`
  - `app.schemas.abha_card` (`AbhaCardData`, `AbhaCardResponse`, `AbhaQrVerificationResponse`)
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/abha_card.py`
  - Patient portal / mobile client card rendering
- **Exported Symbols:**
  - `compute_abha_signature`
  - `generate_abha_card_data`
  - `verify_abha_qr_payload`

```
+-----------------------------------------------------------------------------------+
|                        ABHA Card & QR Generation Engine                           |
|                                                                                   |
|  [PatientProfile + User]                                                          |
|          |                                                                        |
|          v                                                                        |
|  [generate_abha_card_data]                                                        |
|          |-- Mask mobile number (_mask_mobile_number)                             |
|          |-- Format blood group and gender                                        |
|          |-- Fallback check: patient.abha_number or '91-8472-1092-4821' (BUG)     |
|          |-- Serialize compact QR claims dictionary                               |
|          +--> compute_abha_signature: HMAC-SHA256(SECRET_KEY, claims)            |
|                      |                                                            |
|                      v                                                            |
|          [AbhaCardResponse (Card Data + Signed QR String)]                        |
|                                                                                   |
|  [Scanner / Verification Request]                                                 |
|          |                                                                        |
|          v                                                                        |
|  [verify_abha_qr_payload]                                                         |
|          |-- Validate JSON structure and required keys                            |
|          |-- Recompute HMAC-SHA256 over claims using SECRET_KEY                   |
|          +--> hmac.compare_digest(claimed_sig, expected_sig)                      |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

This module provides the digital health card generation and scanning functionality:

1. **Demographic Normalization:** When a patient views their digital card, `generate_abha_card_data` derives user-facing attributes: masking the phone number (e.g. `987*****10`), translating database blood group enums to clinical representations (`A+`, `O-`), and normalizing gender to single-letter codes (`M`, `F`, `O`, `U`).
2. **Fallback Attribution:** If the patient's `abha_number` or `abha_address` is null, lines 89–90 fall back to a hardcoded placeholder (`"91-8472-1092-4821"` and `"citizen@abdm"`).
3. **Compact QR Claims Formulation:** Formulates a minimized JSON dictionary containing essential demographic identifiers (`hidn`, `hid`, `name`, `gender`, `dob`, `state_name`, `dist_name`, `mobile`, `blood_group`, `issue_date`).
4. **Signature Generation (`compute_abha_signature`):** Strips any existing signature key, canonically sorts the keys with compact separators (`sort_keys=True, separators=(",", ":")`), and computes an HMAC-SHA256 signature using `settings.SECRET_KEY`. It prefixes the signature with `SHA256:`.
5. **QR Code Verification (`verify_abha_qr_payload`):** When a clinician or reception scanner scans an ABHA QR code, this function parses the JSON string, checks for required fields (`hidn`, `hid`, `name`, `gender`, `signature`), recomputes the expected HMAC signature using `settings.SECRET_KEY`, and checks for equality using constant-time `hmac.compare_digest`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Compliance Standards
- **Constant-Time Signature Comparison:** Signatures must be checked using `hmac.compare_digest` to eliminate timing attack side channels.
- **Canonical Serialization:** Claims must be serialized with deterministic sorting and whitespace minimization (`sort_keys=True, separators=(',', ':')`) prior to digest computation.

### Architectural Flaws & Vulnerabilities
- **Counterfeit Card Generation for Unverified Patients:** If a patient profile does not have an active ABHA number, lines 89–90 inject `"91-8472-1092-4821"` and `"citizen@abdm"`. Generating signed official health cards with fictitious ABHA credentials for unverified patients violates healthcare compliance and fraud regulations. A 404 or unverified exception must be raised instead.
- **Symmetric Local Key vs. ABDM National PKI:** ABHA cards are intended to be scanned and verified across hospitals nationwide. Using a local symmetric secret (`settings.SECRET_KEY`) means no external hospital can verify a NIRMAYA-generated QR code (they do not possess NIRMAYA's secret), and NIRMAYA cannot verify cards issued by other hospitals or the official ABHA app (which use NHA's asymmetric RSA/ECDSA private keys).
- **No Signature Expiration or Revocation:** The QR claims include `issue_date`, but `verify_abha_qr_payload` never checks if the card signature has expired or been revoked.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-ABC-F01` | **S1** | `[SEC]` | `abha_card.py:89-90` | Fallback to hardcoded dummy ABHA number (`91-8472-1092-4821`) mints counterfeit signed ABHA cards for patients without verified ABHA credentials. |
| `BE-SVC-ABC-F02` | **S1** | `[SEC]` | `abha_card.py:68-76, 184-188` | QR code signing uses local symmetric HMAC-SHA256 instead of official NHA asymmetric digital signature PKI, breaking national cross-facility interoperability. |
| `BE-SVC-ABC-F03` | **S2** | `[SEC]` | `abha_card.py:143-200` | QR verification lacks timestamp freshness/expiry validation, allowing indefinitely replayable scanned QR credentials. |
| `BE-SVC-ABC-F04` | **S3** | `[QUAL]` | `abha_card.py:19-33` | Phone masking logic falls back to static `"****"` for short phone numbers without structured validation. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Reject Card Generation for Unlinked Profiles (`BE-SVC-ABC-F01`)

```diff
--- a/backend/app/services/abha_card.py
+++ b/backend/app/services/abha_card.py
@@ -10,6 +10,7 @@ from datetime import datetime, timezone
 from typing import Any, Dict, Optional, Tuple
 from app.core.config import settings
+from app.core.exceptions import ValidationException
 from app.models.patient import PatientProfile
 from app.models.user import User
 from app.schemas.abha_card import (
@@ -87,8 +88,12 @@ def generate_abha_card_data(patient: PatientProfile, user: Optional[User] = None
     raw_mobile = user.phone_number if user else None
     masked_mobile = _mask_mobile_number(raw_mobile)
 
-    abha_number = patient.abha_number or "91-8472-1092-4821"
-    abha_address = patient.abha_address or "citizen@abdm"
+    if not patient.abha_number:
+        raise ValidationException("Cannot generate ABHA card: Patient profile does not have a verified ABHA number linked.")
+
+    abha_number = patient.abha_number
+    abha_address = patient.abha_address or f"{abha_number.replace('-', '')}@abdm"
     issue_date = datetime.now(timezone.utc).isoformat()
 
     card_data = AbhaCardData(
```
