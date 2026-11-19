# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/national_gateway.py`
**Audited Path:** `backend/app/schemas/national_gateway.py`  
**Module:** `backend` | **Subsystem:** Universal High-Density National Health Gateway & Multi-Channel Auth  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/national_gateway.py` defines the canonical Pydantic v2 schemas for NIRMAYA's Universal High-Density National Health Gateway. Operating as the sovereign front door for citizens, clinicians, diagnostic labs, and pharmacies, this module orchestrates multi-modal national identity verification conforming to Indian Digital Public Infrastructure (DPI) guidelines:
- Multi-modal authentication channels: Aadhaar OTP (`AadhaarOtpChallengeRequest`, `AadhaarOtpVerifyRequest`), DigiLocker e-KYC OAuth2 PKCE (`DigiLockerKycAuthRequest`), ABHA Mobile active SIM lookup (`AbhaMobileLoginRequest`), and offline emergency override (`EmergencyBypassAuthRequest`).
- Distributed session management, JWT bearer tokens, and session revocations (`GatewaySessionResponse`, `GatewayDeviceSession`, `SessionRevokeRequest`).
- High-density token-bucket rate limiting telemetry (`RateShieldMetrics`, burst capacity: 50,000 req/sec).

#### 2. Key Components & Class Roster
- `GatewayUserRole`: Core national health roles (`citizen`, `doctor`, `lab`, `pharmacy`).
- `GatewayAuthChannel`: Authentication mechanisms (`aadhaar_otp`, `digilocker`, `abha_mobile`, `offline_emergency`).
- `AadhaarOtpChallengeRequest` & `AadhaarOtpChallengeResponse`: Demographic challenge initiation generating unique transaction UUIDs (`txn_id`) and masked mobile numbers.
- `AadhaarOtpVerifyRequest`: Demographic challenge verification matching 6-digit OTP codes with optional 30-day extended session toggles.
- `DigiLockerKycAuthRequest`: Exchange envelope for DigiLocker OAuth2 PKCE authorization codes, CSRF states, and code verifiers.
- `AbhaMobileLoginRequest`: Active mobile SIM OTP verification with optional ABHA identifier lookup.
- `EmergencyBypassAuthRequest`: High-urgency Break-The-Glass offline session minting with triage level indicators (`red` for immediate resuscitation, `yellow` for urgent) and mandatory legal audit attestations.
- `GatewaySessionResponse`: Master authentication response returning JWT access tokens, user roles, user UUID, patient profile ID, certified names, ABHA numbers, handles, and emergency cryptographic seals.
- `GatewayDeviceSession`: Distributed device session descriptor tracking fingerprints, client IP, browser user agent, and expiration timestamps.
- `RateShieldMetrics`: Telemetry from the 50,000 req/sec token-bucket rate-limiting shield.

---

### Layer B: Plain-Language Developer Walkthrough

In India, a national digital health platform must accommodate a diverse population: some citizens have smartphones with DigiLocker, others only have feature phones connected to Aadhaar SMS, rural patients may only have an ABHA card, and unconscious trauma victims arriving at an emergency bay require instant life-saving bypass access.

`national_gateway.py` acts as the grand entrance hall for all these users:
1. If a patient uses Aadhaar, they submit an `AadhaarOtpChallengeRequest`. The system sends an OTP to their UIDAI-registered phone and returns a transaction ID. The patient verifies with an `AadhaarOtpVerifyRequest`.
2. If they prefer DigiLocker, `DigiLockerKycAuthRequest` handles the secure OAuth2 PKCE handshake.
3. If an emergency doctor needs to access an unconscious trauma patient immediately, `EmergencyBypassAuthRequest` mints an emergency session under strict legal audit logging.
4. Regardless of which door the user walks through, the gateway delivers a uniform `GatewaySessionResponse` containing their cryptographic JWT bearer token, national health role (citizen, doctor, lab), and linked ABHA address.
5. In the background, `RateShieldMetrics` protects the entire platform from distributed denial-of-service (DDoS) and credential stuffing attacks by enforcing a 50,000 requests-per-second rate shield.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **Multi-Modal Identity Harmonization:** Normalizes diverse authentication flows into a unified `GatewaySessionResponse` contract.
- **Break-The-Glass Forensic Accountability:** `EmergencyBypassAuthRequest` requires `tamper_attestation` and issues `emergency_seal` SHA-256 digests.
- **Pydantic v2 Best Practices:** Implements `model_config = ConfigDict(from_attributes=True)` uniformly across all gateway models.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Aadhaar Number and OTP Cleartext Exposure in String Repr (`BE-SCH-GW-F01`)
- **Severity:** S1 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/national_gateway.py:34, 56, 75`
- **Description:** `AadhaarOtpChallengeRequest.aadhaar_number` and `otp` in `AadhaarOtpVerifyRequest` and `AbhaMobileLoginRequest` are declared as plain unmasked `str` fields without `repr=False` or `SecretStr`. When authentication payloads are logged by HTTP middleware, debug tracers, or exception handlers, citizen 12-digit Aadhaar numbers and live 6-digit one-time passwords are leaked in plaintext into server logs.
- **Impact:** Critical violation of Aadhaar Act 2016 regulations and credential interception risk (CWE-532 / CWE-359).
- **Remediation:** Annotate `aadhaar_number` and `otp` with `repr=False` or wrap in `SecretStr`.

##### Vulnerability 2: Active Access Token and PKCE Verifier Leaked in String Repr (`BE-SCH-GW-F02`)
- **Severity:** S1 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/national_gateway.py:66, 103`
- **Description:** `DigiLockerKycAuthRequest.code_verifier` and `GatewaySessionResponse.access_token` are declared as plain strings without `repr=False`. Printing session responses or authentication requests dumps active JWT bearer tokens and PKCE cryptographic verifiers into log pipelines.
- **Impact:** Session hijacking and bearer token theft (CWE-532 / CWE-312).
- **Remediation:** Mark `code_verifier` and `access_token` with `repr=False`.

##### Vulnerability 3: Missing Indian Mobile Number Pattern Validation (`BE-SCH-GW-F03`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/national_gateway.py:74`
- **Description:** `AbhaMobileLoginRequest.mobile_number` is typed as an unconstrained `str = Field(..., description="10-digit Indian mobile number")`. While the description states 10 digits, there is no regex pattern constraint enforcing standard Indian mobile number rules (`pattern=r"^[6-9]\d{9}$"`). Malformed phone numbers or non-numeric strings pass validation.
- **Impact:** Malformed SMS gateway dispatches and database pollution.
- **Remediation:** Add `pattern=r"^[6-9]\d{9}$"` and `min_length=10, max_length=10`.

##### Vulnerability 4: Client IP Address Lacks Strict IP Validation (`BE-SCH-GW-F04`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/national_gateway.py:128`
- **Description:** `GatewayDeviceSession.client_ip` is typed as a generic `str` rather than `IPvAnyAddress`.
- **Impact:** Allows invalid IP strings or log-injection content in active session rosters.
- **Remediation:** Declare `client_ip: IPvAnyAddress`.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-GW-F01` | S1 | `[SEC]` | `national_gateway.py:34, 56, 75` | 12-digit Aadhaar number and live OTP tokens unmasked in string `repr` |
| `BE-SCH-GW-F02` | S1 | `[SEC]` | `national_gateway.py:66, 103` | Active JWT access token and PKCE code verifier unmasked in string `repr` |
| `BE-SCH-GW-F03` | S2 | `[QUAL]` | `national_gateway.py:74` | `mobile_number` lacks 10-digit Indian mobile regex pattern validation |
| `BE-SCH-GW-F04` | S3 | `[QUAL]` | `national_gateway.py:128` | `client_ip` uses plain string rather than `IPvAnyAddress` |
| `BE-SCH-GW-F05` | S3 | `[QUAL]` | `national_gateway.py:115` | `emergency_seal` lacks 64-character hex regex validation |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/national_gateway.py
+++ b/backend/app/schemas/national_gateway.py
@@ -10,7 +10,7 @@ from datetime import datetime, timezone
 from enum import Enum
 from typing import Dict, List, Literal, Optional
-from pydantic import BaseModel, ConfigDict, Field
+from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress
 
 
@@ -34,4 +34,5 @@ class AadhaarOtpChallengeRequest(BaseModel):
     aadhaar_number: str = Field(
         ...,
+        repr=False,
         description="12-digit Aadhaar number with or without spaces",
         example="9184 7210 4821",
@@ -56,3 +57,3 @@ class AadhaarOtpVerifyRequest(BaseModel):
     txn_id: str = Field(..., description="Transaction reference from challenge phase")
-    otp: str = Field(..., description="6-digit verification code", example="123456")
+    otp: str = Field(..., repr=False, description="6-digit verification code", example="123456")
     remember_me: bool = Field(default=True, description="Whether to issue an extended 30-day session")
@@ -66,3 +67,3 @@ class DigiLockerKycAuthRequest(BaseModel):
     state: str = Field(..., description="CSRF state parameter")
-    code_verifier: str = Field(..., description="PKCE code verifier")
+    code_verifier: str = Field(..., repr=False, description="PKCE code verifier")
     remember_me: bool = Field(default=True, description="Whether to issue an extended 30-day session")
@@ -74,4 +75,7 @@ class AbhaMobileLoginRequest(BaseModel):
     mobile_number: str = Field(
         ...,
+        pattern=r"^[6-9]\d{9}$",
+        min_length=10,
+        max_length=10,
         description="10-digit Indian mobile number",
         example="9876543210",
     )
-    otp: str = Field(..., description="6-digit verification OTP", example="123456")
+    otp: str = Field(..., repr=False, description="6-digit verification OTP", example="123456")
     abha_identifier: Optional[str] = Field(default=None, description="Optional ABHA address or 14-digit number")
@@ -103,3 +107,3 @@ class GatewaySessionResponse(BaseModel):
     session_id: str = Field(description="Unique distributed session identifier")
-    access_token: str = Field(description="Cryptographic JWT Bearer token")
+    access_token: str = Field(repr=False, description="Cryptographic JWT Bearer token")
     token_type: str = Field(default="bearer", description="Token scheme")
@@ -115,3 +119,8 @@ class GatewaySessionResponse(BaseModel):
     is_offline_emergency: bool = Field(default=False, description="Flag indicating break-the-glass emergency session")
-    emergency_seal: Optional[str] = Field(default=None, description="Cryptographic SHA-256 seal for emergency sessions")
+    emergency_seal: Optional[str] = Field(
+        default=None,
+        pattern=r"^[a-fA-F0-9]{64}$",
+        min_length=64,
+        max_length=64,
+        description="Cryptographic SHA-256 seal for emergency sessions",
+    )
     message: str = Field(description="Status confirmation message")
@@ -128,3 +137,3 @@ class GatewayDeviceSession(BaseModel):
     device_fingerprint: str = Field(description="Client device fingerprint or hash")
-    client_ip: str = Field(description="Client IP address")
+    client_ip: IPvAnyAddress = Field(description="Client IP address")
     user_agent: str = Field(description="Client browser or application user agent")
```
