# Codebase Audit Report: `backend/app/services/digilocker.py`

**Audit Target**: `backend/app/services/digilocker.py`  
**Subsystem**: Backend - DigiLocker OAuth 2.0 PKCE & UIDAI e-Aadhaar Verification (`backend/app/services/`)  
**File Lines**: 370 LOC  
**Severity Breakdown**: S0: 0 | S1: 2 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `digilocker.py` module integrates NIRMAYA with the Government of India's DigiLocker platform, implementing RFC 7636 PKCE OAuth 2.0 authorization, token exchange, UIDAI e-Aadhaar XML retrieval, XML digital signature verification, and automated patient demographic synchronization.

```
[ Citizen Browser / App ]
           │
           ▼ (OAuth2 PKCE Redirect)
   [ DigiLocker Gateway ]
           │
           ▼ (Callback with Auth Code & State)
   [ digilocker.py Service ]
   ├── 1. RFC 7636 PKCE Pair Generation (S256 code_challenge)
   ├── 2. Authorization URL & CSRF Token Builder
   ├── 3. Token Exchange (Code + Verifier -> Bearer Token)
   ├── 4. e-Aadhaar Encrypted XML Ingestion
   ├── 5. XML Digital Signature & Demographic Parser (Poi/Poa/UidData)
   └── 6. PatientProfile & User Synchronization
           │
           ▼
   [ PostgreSQL PatientProfile / Identity Verified ]
```

### Import / Export Roster
- **Imports**: `base64`, `hashlib`, `secrets`, `urllib.parse`, `datetime`, `typing`, `xml.etree.ElementTree`, `httpx`, `sqlalchemy.ext.asyncio`, `app.core.config`, `app.models`, `app.schemas.digilocker`, `app.services.patient`.
- **Exports**: `generate_pkce_pair()`, `generate_authorization_url()`, `exchange_code_for_token()`, `fetch_eaadhaar_xml()`, `parse_eaadhaar_xml()`, `verify_digilocker_callback()`, `sync_patient_profile()`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Authorization Initiation**: `generate_authorization_url()` generates a cryptographically random PKCE `code_verifier` (64 bytes) and SHA-256 `code_challenge`, constructing the OAuth redirect URL to DigiLocker with scopes `read profile eaadhaar`.
2. **Token Exchange**: `exchange_code_for_token()` sends the authorization code and PKCE verifier to DigiLocker's token endpoint to receive a short-lived Bearer access token.
3. **e-Aadhaar Fetch**: `fetch_eaadhaar_xml()` calls DigiLocker's e-Aadhaar endpoint to download the official digitally signed XML certificate.
4. **Demographic Parsing**: `parse_eaadhaar_xml()` parses the XML DOM, extracting citizen name, gender, date of birth, masked Aadhaar (`XXXX-XXXX-4821`), photo avatar, and structured address.
5. **Patient Sync**: `sync_patient_profile()` updates the patient's record in PostgreSQL and marks `is_identity_verified = True`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Trivial XML Digital Signature Bypass (Unverified e-Aadhaar Claims)
At line 259 in `parse_eaadhaar_xml()`:
```python
signature_valid = sig is not None
```
The service evaluates digital signature validity purely by checking if the `<Signature>` XML tag exists. It performs zero cryptographic verification of the RSA-SHA256 signature (`<SignatureValue>`) against the UIDAI root X.509 certificate. Any adversary or malicious third party can submit forged XML payloads containing fictitious demographic data and a dummy `<Signature>` element, tricking the platform into marking fraudulent citizen identities as government-verified!

### 2. Hardcoded Prefix Authentication Bypasses in Production
At lines 111 and 162:
```python
if settings.DIGILOCKER_SIMULATION_MODE or code.startswith("mock_") or code.startswith("test_"):
    return DigiLockerTokenResponse(...)

if settings.DIGILOCKER_SIMULATION_MODE or access_token.startswith("mock_") or access_token.startswith("test_"):
    return SIMULATED_EAADHAAR_XML
```
Even if `DIGILOCKER_SIMULATION_MODE` is disabled (`False`) in production, any caller passing a code or token starting with `"mock_"` or `"test_"` bypasses all authentic DigiLocker API communication and receives simulated identity claims for "Arun Kumar Patel".

### 3. Ephemeral PKCE Verifier Loss
In `generate_authorization_url()`, the `code_verifier` is generated and returned, but it is not saved to Redis or session cookies alongside the `state` parameter. If the client fails to preserve and resend the verifier on callback, the exchange cannot succeed cleanly without falling back to simulator modes.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-DLK-F01` | **S1** | `[SEC/CRYPTO]` | `backend/app/services/digilocker.py:259` | XML digital signature check only tests for presence of `<Signature>` tag without RSA-SHA256 mathematical verification against UIDAI X.509 root, enabling forged identity claims. |
| `BE-SVC-DLK-F02` | **S1** | `[SEC/AUTH]` | `backend/app/services/digilocker.py:111, 162` | `code.startswith("mock_")` and `access_token.startswith("mock_")` bypasses live DigiLocker APIs in production deployments regardless of configuration. |
| `BE-SVC-DLK-F03` | **S2** | `[SEC/AUTH]` | `backend/app/services/digilocker.py:68-98` | PKCE `code_verifier` is not bound to server-side session state or Redis, weakening OAuth2 PKCE interception defense. |
| `BE-SVC-DLK-F04` | **S3** | `[QUAL]` | `backend/app/services/digilocker.py:30-53` | Static simulated e-Aadhaar XML template embedded directly in Python source code. |
| `BE-SVC-DLK-F05` | **S4** | `[DOC]` | `backend/app/services/digilocker.py:1-28` | Missing documentation on DPDP Act 2023 Section 6 explicit consent notice formatting for DigiLocker document pulls. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-DLK-F01` / `BE-SVC-DLK-F02`: Strict Production Gate and Cryptographic Signature Verification

```diff
--- a/backend/app/services/digilocker.py
+++ b/backend/app/services/digilocker.py
@@ -111,7 +111,7 @@ async def exchange_code_for_token(code: str, code_verifier: Optional[str] = Non
     """
-    if settings.DIGILOCKER_SIMULATION_MODE or code.startswith("mock_") or code.startswith("test_"):
+    if settings.DIGILOCKER_SIMULATION_MODE and settings.ENVIRONMENT != "production":
         return DigiLockerTokenResponse(
             access_token=f"mock_dl_bearer_{secrets.token_hex(16)}",
             expires_in=3600,
@@ -256,7 +256,12 @@ def parse_eaadhaar_xml(xml_content: str) -> EAadhaarDemographics:
         formatted_address=formatted_address,
     )
 
-    signature_valid = sig is not None
+    # Enforce authentic XML-DSig signature verification
+    signature_valid = False
+    if sig is not None:
+        from app.services.abdm_crypto import verify_xmldsig_signature
+        signature_valid = verify_xmldsig_signature(xml_content, root)
 
     return EAadhaarDemographics(
```
