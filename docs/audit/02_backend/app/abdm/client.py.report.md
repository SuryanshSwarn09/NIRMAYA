# Principal Software Engineering Audit: backend/app/abdm/client.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/abdm/client.py` provides the asynchronous HTTP client implementation for connecting to the National Health Authority (NHA) ABDM Gateway. It handles client credentials authentication (`POST /v0.5/sessions`), caches Bearer JWT tokens with a 60-second preemptive safety renewal buffer, formats mandatory NHA dispatch headers (`X-CM-ID`, `REQUEST-ID`, `TIMESTAMP`), and provides an ephemeral simulation mode for sandbox resilience and offline testing. Critical architectural vulnerabilities include hardcoded heuristic checks that automatically bypass live NHA Sandbox APIs when real sandbox client IDs (starting with `"SBX_"`) are used, silent fallback to counterfeit synthetic JWT tokens on network errors that masks genuine connectivity outages, and lack of concurrency locking during token refresh (thundering herd risk).

### System Topology & Architectural Invariants
```
                  +-----------------------------------------------+
                  |          ABDM Clinical Services & Endpoints   |
                  +-----------------------+-----------------------+
                                          |
                                          v
                  +-----------------------------------------------+
                  |      ABDMGatewayClient (abdm/client.py)       |
                  |                                               |
                  |  - get_session_token(force_refresh)           |
                  |  - is_token_valid (60s buffer check)          |
                  |  - build_gateway_headers(token, request_id)   |
                  |  - get_gateway_status()                       |
                  +-----------------------+-----------------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
                        v                                   v
          +---------------------------+       +---------------------------+
          | Live NHA ABDM Gateway     |       | Synthetic Simulation Mode |
          | (/v0.5/sessions via HTTPX)|       | (_generate_simulated_token|
          | - Bearer JWT Acquisition  |       |  "sbx_jwt_<uuid>")        |
          +---------------------------+       +---------------------------+
```

### Import / Export Surface Map
- **Upstream Dependencies:**
  - `httpx`: Asynchronous HTTP client library.
  - `logging`: Diagnostic logging under logger `"nirmaya.abdm.client"`.
  - `uuid`: Request ID and mock token generation.
  - `datetime.datetime`, `datetime.timedelta`, `datetime.timezone`: Temporal calculations.
  - `app.core.config.settings`: Configuration parameters (`ABDM_GATEWAY_URL`, `ABDM_CLIENT_ID`, `ABDM_CLIENT_SECRET`, `ABDM_CM_ID`, `ABDM_REQUEST_TIMEOUT_SECONDS`, `ABDM_SANDBOX_ENABLED`).
  - `app.abdm.security.rsa.get_abdm_encryption_manager`: Cryptographic key readiness checks.
  - `app.schemas.abdm`: `GatewaySessionResponse`, `GatewayStatusResponse`.
- **Downstream Consumers:**
  - `backend/app/services/abdm_*.py`: Direct consumers for dispatching ABDM consent requests, discovery queries, and health document transfers.
- **Exported Interface:**
  - `ABDMGatewayClient`: High-level asynchronous gateway client class.
  - `get_abdm_gateway_client`: Singleton accessor function.

---

## Layer B: Plain-Language Developer Walkthrough

The `backend/app/abdm/client.py` module acts as the outbound HTTP communication bridge between NIRMAYA and the central NHA ABDM Gateway:
1. **Token Lifecycle (`get_session_token`, `is_token_valid`)**: When NIRMAYA needs to send an API request to the central gateway (e.g. to discover a patient's ABHA or notify consent approval), it calls `get_session_token()`. If a previously fetched Bearer token exists and has more than 60 seconds of validity remaining, it is reused. If the token is expired or missing, it issues an HTTP POST to `/v0.5/sessions` with `clientId` and `clientSecret`.
2. **Sandbox Simulation Mode**: If credentials match heuristic test strings or if `ABDM_SANDBOX_ENABLED` is set and `clientId` starts with `"SBX_"`, the client bypasses the network and generates a synthetic string `sbx_jwt_<hex>`, allowing the application to operate in offline environments.
3. **Gateway Dispatch Headers (`build_gateway_headers`)**: ABDM requires strict correlation headers on every payload: `Authorization: Bearer <token>`, `X-CM-ID` (Consent Manager ID), `REQUEST-ID` (UUID tracing), `TIMESTAMP` (ISO 8601 UTC string), `Content-Type: application/json`.
4. **Diagnostic Status (`get_gateway_status`)**: Reports connection status, gateway URL, sandbox flag, token expiration remaining seconds, and whether RSA encryption keys are loaded.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Legitimate NHA Sandbox Client IDs Bypassed by Heuristic
In lines 78-81:
```python
is_mock_creds = self.client_id.startswith("SBX_") or "placeholder" in self.client_secret
if settings.ABDM_SANDBOX_ENABLED and is_mock_creds:
    return self._generate_simulated_token(expires_in=3600)
```
The National Health Authority officially assigns developer client IDs starting with `"SBX_"` (e.g., `SBX_001234`) for developers connecting to the *real* live NHA Sandbox environment (`https://dev.abdm.gov.in/gateway`). By intercepting any `client_id` starting with `"SBX_"` and generating an in-memory simulated token, the client makes it impossible to perform live sandbox certification testing because it intercepts and simulates the session call instead of talking to NHA servers.

### Invariant 2: Silent Fallback to Counterfeit Tokens on Connection Failure
In lines 100-110:
```python
else:
    logger.warning(f"ABDM Gateway /v0.5/sessions returned HTTP {res.status_code}... Falling back to sandbox simulation token.")
    return self._generate_simulated_token(expires_in=1800)
except Exception as exc:
    logger.warning(f"Connection to ABDM Gateway failed ({exc}). Operating in sandbox simulation mode.")
    return self._generate_simulated_token(expires_in=1800)
```
When an HTTP request to the live ABDM Gateway fails (e.g., network partition, bad client secret, NHA downtime), the client silently issues a fake token (`sbx_jwt_...`) rather than raising an exception. Consequently, downstream calls to live ABDM endpoints fail with baffling 401 Unauthorized errors from the remote gateway, disguising the original network or authentication issue.

### Invariant 3: Thundering Herd Concurrency Race Condition on Token Renewal
`get_session_token()` is an async method without an `asyncio.Lock()`. If 50 concurrent incoming clinical transactions discover that the cached token has expired, all 50 coroutines independently fire simultaneous POST `/v0.5/sessions` requests to the NHA gateway. This triggers NHA rate-limiting shields and exhausts local socket connections.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-ABDM-CLI-F01` | **S1** | `[SEC]` / `[QUAL]` | `app/abdm/client.py:78-81` | Heuristic check (`client_id.startswith("SBX_")`) intercepts legitimate NHA sandbox credentials and prevents live sandbox testing. |
| `BE-ABDM-CLI-F02` | **S1** | `[SEC]` / `[QUAL]` | `app/abdm/client.py:100-110` | Silent fallback to synthetic fake token on HTTP/network errors masks gateway authentication failures and causes cascading 401 errors. |
| `BE-ABDM-CLI-F03` | **S2** | `[PERF]` | `app/abdm/client.py:60-100` | Token renewal lacks an `asyncio.Lock()`, triggering thundering herd connection storms to the NHA gateway upon token expiration. |
| `BE-ABDM-CLI-F04` | **S3** | `[QUAL]` | `app/abdm/client.py:133` | Hardcoded `.000Z` timestamp string formatting ignores microsecond precision on timestamps. |
| `BE-ABDM-CLI-F05` | **S4** | `[DOC]` | `app/abdm/client.py:1-8` | Missing documentation regarding NHA Gateway Error Response format (`{"error": {"code": ..., "message": ...}}`). |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-ABDM-CLI-F01-F03`: Token Lock & Remove Heuristic Sandbox Bypass
```diff
--- a/backend/app/abdm/client.py
+++ b/backend/app/abdm/client.py
@@ -10,6 +10,7 @@
 import logging
 import uuid
+import asyncio
 from datetime import datetime, timedelta, timezone
 from typing import Any, Dict, Optional
 
@@ -42,6 +43,7 @@
         self._access_token: Optional[str] = None
         self._token_expires_at: Optional[datetime] = None
+        self._lock = asyncio.Lock()
 
     @property
     def is_token_valid(self) -> bool:
@@ -69,18 +71,19 @@
         if not force_refresh and self.is_token_valid and self._access_token:
             return self._access_token
 
+        async with self._lock:
+            if not force_refresh and self.is_token_valid and self._access_token:
+                return self._access_token
+
         logger.info("Requesting fresh ABDM Gateway session token from /v0.5/sessions")
         payload = {
             "clientId": self.client_id,
             "clientSecret": self.client_secret,
         }
 
-        # Handle local dev / test mock credentials gracefully
-        is_mock_creds = self.client_id.startswith("SBX_") or "placeholder" in self.client_secret
-        if settings.ABDM_SANDBOX_ENABLED and is_mock_creds:
+        if settings.ABDM_SIMULATION_MODE:
             return self._generate_simulated_token(expires_in=3600)
 
         try:
```
