# Audit Report: backend/app/schemas/abdm.py

**Path:** `backend/app/schemas/abdm.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 84 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for Ayushman Bharat Digital Mission (ABDM) Gateway session authentication, gateway headers, error envelopes, and demographic encryption payloads.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `GatewaySessionRequest.clientSecret` is stored as an unmasked string field without `repr=False` or `SecretStr`, exposing sensitive ABDM Gateway API credentials in plaintext if requests are logged or printed during debugging.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
To exchange health data across India's national health grid, NIRMAYA must authenticate with the National Health Authority (NHA) ABDM Gateway (`/v0.5/sessions`). Every request requires standardized correlation headers (`REQUEST-ID`, `TIMESTAMP`, `X-CM-ID`), standardized error envelopes, and RSA-OAEP demographic encryption payloads. This file defines the exact Pydantic models for these gateway exchanges.

### How it works, step by step
1. `GatewaySessionRequest` packages the facility's `clientId` and `clientSecret` to request a gateway bearer token.
2. `GatewaySessionResponse` parses the returned `accessToken` and token validity window (`expiresIn`).
3. `GatewayHeaderSchema` generates the mandatory correlation metadata (`request_id`, `timestamp`, `x_cm_id`).
4. `GatewayStatusResponse` reports connection health, RSA encryption status, and gateway configuration.
5. `ABDMEncryptionPayload` and `ABDMEncryptedResponse` structure RSA-OAEP encrypted demographic claims.

### Concepts and patterns used
- *ABDM Gateway v0.5 Specification:* Conforming to official NHA data exchange protocols.
- *Distributed Tracing Headers:* UUID correlation matching ABDM gateway distributed tracking.
- *Cryptographic Envelope Pattern:* Encapsulating Base64-encoded RSA-OAEP ciphertext.

### Key lines to read first
- `abdm.py:8-15`: `GatewaySessionRequest` and plain `clientSecret` field.
- `abdm.py:17-25`: `GatewaySessionResponse` bearer token response.
- `abdm.py:40-49`: `GatewayHeaderSchema` distributed tracing headers.
- `abdm.py:76-84`: `ABDMEncryptedResponse` ciphertext envelope.

### How to change it safely
Do not change field names (e.g. `clientId`, `clientSecret`, `accessToken`) to snake_case; the ABDM central gateway strictly requires camelCase naming in JSON payloads.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing`, `pydantic` (BaseModel, Field, ConfigDict).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/abdm_gateway.py`, `backend/app/api/v1/endpoints/abdm.py`.
- **Public Surface:** Classes `GatewaySessionRequest`, `GatewaySessionResponse`, `GatewayErrorDetail`, `GatewayErrorResponse`, `GatewayHeaderSchema`, `GatewayStatusResponse`, `ABDMEncryptionPayload`, `ABDMEncryptedResponse`.

### 2. Security [SEC]
- **Credential Exposure in Logs (CWE-532 / OWASP A09:2021):** `clientSecret` (line 12) is defined as `clientSecret: str = Field(...)`. If an exception occurs or a developer logs the incoming request payload (`logger.info("Session request: %s", request)`), the raw ABDM API client secret is written to application logs in cleartext. In Pydantic v2, sensitive authentication credentials should use `SecretStr` or `Field(repr=False)` (`BE-ABDM-F01`).
- **Token Exposure in Logging (CWE-532):** `GatewaySessionResponse.accessToken` (line 20) is similarly unmasked in string representations (`BE-ABDM-F02`).

### 3. Code quality [QUAL]
- Clean, idiomatic Pydantic v2 models utilizing `ConfigDict(from_attributes=True)` and `default_factory=lambda: datetime.now(timezone.utc)`.
- Explicit field descriptions and realistic example values facilitate auto-generated OpenAPI documentation.

### 4. AI-generated-code smells [QUAL]
- None; exact camelCase conforms to official ABDM sandbox REST API requirements.

### 5. Performance [PERF]
- Minimal schema overhead; lightweight JSON parsing.

### 6. Error handling & edge cases
- `GatewayErrorResponse` cleanly wraps `GatewayErrorDetail` according to the RFC 7807 / ABDM error specification.

### 7. Doc accuracy [DOC]
- Perfectly conforms to Month 3 Day 41 gateway session documentation.

### 8. Tests
- Covered by `backend/tests/test_abdm.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-ABDM-F01 | S2 | [SEC] | 12 | Sensitive client secret unmasked in `repr` | `clientSecret: str = Field(...)` | Use `SecretStr` or add `repr=False` to `Field` |
| BE-ABDM-F02 | S3 | [SEC] | 20 | Gateway access token unmasked in `repr` | `accessToken: str = Field(...)` | Add `repr=False` to `accessToken` Field |

---

## Suggested Patches (NOT Applied)

### Patch BE-ABDM-F01 · Risk: Low · [UNTESTED]
Mask ABDM client credentials in string representations to prevent log leakage:

```diff
--- a/backend/app/schemas/abdm.py
+++ b/backend/app/schemas/abdm.py
@@ -10,4 +10,4 @@ class GatewaySessionRequest(BaseModel):
 
     clientId: str = Field(description="ABDM Registered Client ID", example="SBX_001234")
-    clientSecret: str = Field(description="ABDM Client Secret Key", example="secret_key_placeholder")
+    clientSecret: str = Field(description="ABDM Client Secret Key", example="secret_key_placeholder", repr=False)
 
```

---

## Verdict

**READY-WITH-FIXES** — Compliant ABDM Gateway v0.5 protocol schema; masking `clientSecret` and `accessToken` in `repr` eliminates log exposure vulnerabilities.
