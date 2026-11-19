# Codebase Technical Audit Report: `backend/app/services/national_gateway_service.py`

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`national_gateway_service.py` implements the Universal High-Density National Health Gateway for the NIRMAYA sovereign health network. It serves as the single unified ingress entrypoint across four multi-modal authentication channels: Aadhaar demographic OTP verification, DigiLocker OAuth2 PKCE e-KYC claims, active mobile SIM ABHA lookup, and offline emergency Break-The-Glass (BTG) access with SHA-256 tamper-evident sealing. It incorporates anti-brute-force rate limiting and distributed session device tracking with multi-device revocation.

### System Topology & Authentication Ingress
```
     [ Citizen / Clinician / Emergency Terminal ]
                          |
   +---------------------------------------------+
   |           NationalGatewayService            |
   +---------------------------------------------+
   | Channel 1: Aadhaar OTP Challenge & Verify   |
   | Channel 2: DigiLocker Certified e-KYC (PKCE)|
   | Channel 3: ABHA Mobile SIM & Handle Lookup  |
   | Channel 4: Offline BTG Tamper-Sealed Access |
   +---------------------------------------------+
   | - Rate Shield & Anti-Brute Force Tracker    |
   | - Distributed Device Session Management     |
   | - Instant Multi-Device Revocation Guard     |
   +---------------------------------------------+
                          |
           (RS256 / HS256 Bearer Token)
                          v
         [ Unified GatewaySessionResponse ]
```

### Module Metadata & Imports/Exports
- **Module Path:** `backend/app/services/national_gateway_service.py`
- **Component Classification:** Unified National Health Gateway & Multi-Channel Auth
- **Lines of Code:** 523 LOC
- **Imports:** `hashlib`, `time`, `uuid`, `datetime`, `typing`, `app.core.config.settings`, `app.core.security.create_access_token`, `app.schemas.national_gateway.*`
- **Primary Export:** `national_gateway_service` (Global Singleton Instance)

---

## Layer B: Plain-Language Developer Walkthrough

The gateway unifies four distinct entry channels:
1. **Channel 1 (Aadhaar Demographic OTP)**:
   - `initiate_aadhaar_challenge`: Validates 12-digit format, applies sliding-window rate limit (max 5 attempts per 60s), generates an in-memory challenge with a masked mobile descriptor, and returns transaction ID `txn_id`.
   - `verify_aadhaar_otp`: Compares submitted OTP, verifies temporal expiry (300s window), generates a session UUID, mints a signed JWT access token, and registers a `GatewayDeviceSession`.
2. **Channel 2 (DigiLocker e-KYC)**:
   - `verify_digilocker_kyc`: Accepts OAuth2 code and PKCE code verifier, constructs certified demographic claims, mints an access token, and tracks the device fingerprint.
3. **Channel 3 (ABHA Mobile SIM Fallback)**:
   - `verify_abha_mobile`: Validates 10-digit Indian mobile format, verifies OTP, and issues an authenticated session bound to the citizen's ABHA handle.
4. **Channel 4 (Offline Emergency Break-The-Glass)**:
   - `mint_emergency_bypass_session`: Requires legal attestation, facility ID, clinician ID, and triage severity. Computes a deterministic SHA-256 emergency seal:
     $$\text{Seal} = \text{SHA-256}(\text{facility\_id} \parallel \text{clinician\_id} \parallel \text{patient\_id} \parallel \text{reason} \parallel \text{triage} \parallel \text{timestamp})$$
     Mints a strictly bounded 4-hour doctor token and records the event in an emergency audit ledger.
5. **Distributed Session Control**: Supports retrieving active sessions, listing unexpired sessions by user, revoking single sessions, and global emergency revocation (`revoke_all_sessions`).

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Multi-Device Emergency Revocation
To defend against compromised mobile devices or credential theft, calling `revoke_all_sessions(user_id)` instantly flags all distributed device sessions for that identity as inactive, invalidating downstream token bearer checks.

### Invariant 2: Cryptographic BTG Tamper Sealing
Emergency break-the-glass actions bypass standard citizen consent under DPDP Act 2023 Section 9 medical emergency provisions. The service guarantees non-repudiation by sealing the clinical context into a SHA-256 hash stamped directly into the JWT token and stored in the forensic audit ledger.

### Invariant 3: Anti-Brute-Force Sliding Window
The rate shield enforces a sliding 60-second window:
$$N_{\text{failed\_attempts}}(IP, \text{identifier}) < 5$$
Exceeding 5 failures locks further attempts with an explicit `retry_after_seconds` penalty backoff.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
|---|---|---|---|---|
| `BE-SVC-NGW-F01` | **S1** | `[SEC]` | `backend/app/services/national_gateway_service.py:145-155, 330-340` | Hardcoded Static OTP `"123456"` for Aadhaar and Mobile Authentication Bypass. In both `initiate_aadhaar_challenge` and `verify_abha_mobile`, the OTP is hardcoded to `"123456"`, allowing anyone to authenticate as any citizen or mobile subscriber by typing `123456`. |
| `BE-SVC-NGW-F02` | **S1** | `[SEC]` | `backend/app/services/national_gateway_service.py:34-45` | Volatile In-Memory Session, Challenge, and Emergency BTG Storage. Device sessions, revoked tokens, and emergency break-the-glass audit logs are stored in plain dictionaries without Redis or PostgreSQL persistence; server restarts clear all active sessions and wipe emergency incident audit logs. |
| `BE-SVC-NGW-F03` | **S2** | `[SEC]` | `backend/app/services/national_gateway_service.py:375-430` | Offline Break-The-Glass Session Grants Doctor Access Without Validating Clinician Credentials Against HPR / NMC Registry. Any caller providing a string `clinician_id` and `tamper_attestation` receives an authenticated 4-hour doctor token. |
| `BE-SVC-NGW-F04` | **S2** | `[QUAL]` | `backend/app/services/national_gateway_service.py:250-290` | Mock DigiLocker Demographics Hardcodes "Arun Kumar Patel" for All Users. Any DigiLocker OAuth code produces the identical synthetic persona. |
| `BE-SVC-NGW-F05` | **S3** | `[PERF]` | `backend/app/services/national_gateway_service.py:480-515` | Linear Scan Across All Sessions for User-Specific Revocation. Loops through all sessions rather than maintaining a user-to-session index. |
| `BE-SVC-NGW-F06` | **S4** | `[DOC]` | `backend/app/services/national_gateway_service.py:18-24` | Missing Claims Documentation for 50,000 req/sec Burst Capacity SLA (Hardware sizing, Redis cluster topology, eBPF / XDP bypass). |

---

## Layer E: Unapplied Unified Diff Patches

### Patch 1: Enforce Dynamic Cryptographic OTP Generation (`BE-SVC-NGW-F01`)
```diff
--- a/backend/app/services/national_gateway_service.py
+++ b/backend/app/services/national_gateway_service.py
@@ -1,4 +1,5 @@
 import hashlib
+import secrets
 import time
 import uuid
@@ -148,3 +149,3 @@ class NationalGatewayService:
             "masked_aadhaar": f"XXXX-XXXX-{last4}",
-            "otp": "123456",
+            "otp": f"{secrets.randbelow(900000) + 100000}",
             "expires_at": time.time() + 300,
```

### Patch 2: Add User-Indexed Map for Instant Session Revocation (`BE-SVC-NGW-F05`)
```diff
--- a/backend/app/services/national_gateway_service.py
+++ b/backend/app/services/national_gateway_service.py
@@ -35,3 +35,4 @@ class NationalGatewayService:
         self._sessions: Dict[str, GatewayDeviceSession] = {}
+        self._user_sessions: Dict[str, List[str]] = {}
         self._session_responses: Dict[str, GatewaySessionResponse] = {}
@@ -216,4 +217,6 @@ class NationalGatewayService:
         self._sessions[session_id] = device_session
+        self._user_sessions.setdefault(user_id, []).append(session_id)
 
@@ -504,5 +507,7 @@ class NationalGatewayService:
     def revoke_all_sessions(self, user_id: str) -> int:
         """Revoke all active sessions for a user (Emergency global sign-out)."""
-        for s in self._sessions.values():
-            if s.user_id == user_id and s.is_active and s.expires_at > now:
+        session_ids = self._user_sessions.get(user_id, [])
+        for sid in session_ids:
+            s = self._sessions.get(sid)
+            if s and s.is_active and s.expires_at > now:
```
