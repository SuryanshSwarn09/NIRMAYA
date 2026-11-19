# Audit Report: backend/app/schemas/auth.py

**Path:** `backend/app/schemas/auth.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 58 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for JWT token decoding, bearer token issuance, token verification, and session authentication context.
- **Risk Level:** **S1 (High)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `TokenResponse.access_token` and `TokenVerifyRequest.token` are standard string fields without `repr=False` or `SecretStr`. Standard logging or exception telemetry printing these models exposes active JWT bearer tokens in plaintext, enabling session hijacking (CWE-532 / CWE-312).

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In NIRMAYA's stateless API architecture, client sessions and user identities are verified via JSON Web Tokens (JWTs) issued by the authentication service or Supabase. To ensure that downstream route handlers and security dependencies receive validated claims, this file defines the schemas that parse decoded token payloads, package newly issued bearer tokens, handle token verification requests, and construct the internal `AuthContext` representing the authenticated caller.

### How it works, step by step
1. `TokenPayload` unpacks the standard RFC 7519 JWT claims (`sub`, `email`, `role`, `aud`, `exp`, `iat`) and Supabase metadata dictionaries (`app_metadata`, `user_metadata`).
2. `TokenResponse` packages a signed JWT access token, its authorization scheme (`bearer`), expiration seconds, and linked user identity for API responses.
3. `TokenVerifyRequest` accepts an arbitrary JWT token string to test validity.
4. `TokenVerifyResponse` returns confirmation of token validity along with the extracted subject and claims dictionary.
5. `AuthContext` provides a clean, typed security context passed into route dependencies, identifying the user's primary UUID, verified email, platform role, and active status.

### Concepts and patterns used
- *RFC 7519 JWT Claims Representation:* Standard claims (`sub`, `exp`, `iat`, `aud`) alongside application-level metadata.
- *Security Context Dependency Injection:* `AuthContext` acts as the uniform identity container across all authenticated endpoints.
- *Role-Based Authorization:* Linking identity tokens directly to platform roles (`UserRole`).

### Key lines to read first
- `auth.py:9-26`: `TokenPayload` claim specifications.
- `auth.py:28-35`: `TokenResponse` token issuance model.
- `auth.py:37-49`: Token verification models (`TokenVerifyRequest`, `TokenVerifyResponse`).
- `auth.py:51-58`: `AuthContext` security context schema.

### How to change it safely
Ensure `access_token` and `token` are masked using `repr=False`. When adding new roles or claims, synchronize `UserRole` in `app.models.enums` and ensure `TokenPayload.role` maps to `UserRole`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `typing` (Any, Dict, Optional), `pydantic` (BaseModel, EmailStr, Field), `app.models.enums.UserRole`, `app.schemas.user.UserResponse`.
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/core/dependencies.py`, `backend/app/services/auth_service.py`, `backend/app/api/v1/endpoints/auth.py`.
- **Public Surface:** Models `TokenPayload`, `TokenResponse`, `TokenVerifyRequest`, `TokenVerifyResponse`, `AuthContext`.

### 2. Security [SEC]
- **Plaintext Bearer Token Exposure in Logs (CWE-532 / CWE-312):** In `TokenResponse.access_token` (line 31) and `TokenVerifyRequest.token` (line 40), signed JWTs are plain `str` fields (`BE-SCH-ATH-F01`). When request/response payloads are serialized in debug logs or error traces, high-privilege bearer tokens are written to disk in cleartext. Masking via `Field(..., repr=False)` or `SecretStr` is required.
- **Unvalidated Role Claims in Token Payload (`BE-SCH-ATH-F02`):** In `TokenPayload.role` (line 14), the role is typed as `Optional[str]` rather than `Optional[UserRole]`. In contrast, `AuthContext.role` (line 56) strictly enforces `UserRole`. If an unvalidated string passes through `TokenPayload`, invalid or unrecognized role strings may bypass early validation and fail unexpectedly deeper in authorization middleware.

### 3. Code quality [QUAL]
- **Inconsistent Email Typing (`BE-SCH-ATH-F03`):** In `TokenPayload.email`, the field is typed as `Optional[EmailStr]`, but in `AuthContext.email` (line 55), it is typed as plain `str`. Both should use `EmailStr` for uniform RFC 5322 validation.
- Clean and concise model structure.

### 4. AI-generated-code smells [QUAL]
- None; the authentication schemas follow standard FastAPI / Pydantic patterns.

### 5. Performance [PERF]
- Minimal memory footprint; instantaneous validation suitable for high-throughput authentication gateways.

### 6. Error handling & edge cases
- All claims in `TokenPayload` other than `sub` are marked `Optional`, ensuring resilient token parsing even when third-party OAuth providers omit optional claims.

### 7. Doc accuracy [DOC]
- Conforms to OAuth 2.0 Bearer Token (RFC 6750) and JWT (RFC 7519) specifications.

### 8. Tests
- Covered by `backend/tests/test_auth.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-ATH-F01 | S1 | [SEC] | 31, 40 | JWT bearer access tokens exposed in string `repr` | `access_token: str`, `token: str` | Add `repr=False` or wrap with `SecretStr` |
| BE-SCH-ATH-F02 | S2 | [SEC] | 14 | Unvalidated role claim string in `TokenPayload` | `role: Optional[str] = Field(...)` | Type as `Optional[UserRole]` |
| BE-SCH-ATH-F03 | S3 | [QUAL] | 55 | Email typed as raw string in `AuthContext` | `email: str` in AuthContext vs `EmailStr` in TokenPayload | Use `EmailStr` consistently |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-ATH-F01 · Risk: Low · [UNTESTED]
Mask JWT access tokens in string representations to prevent logging active sessions:

```diff
--- a/backend/app/schemas/auth.py
+++ b/backend/app/schemas/auth.py
@@ -30,3 +30,3 @@ class TokenResponse(BaseModel):
 
-    access_token: str = Field(description="Signed JWT access token")
+    access_token: str = Field(description="Signed JWT access token", repr=False)
     token_type: str = Field(default="bearer", description="HTTP authorization scheme")
@@ -39,3 +39,3 @@ class TokenVerifyRequest(BaseModel):
 
-    token: str = Field(description="Bearer token string to inspect")
+    token: str = Field(description="Bearer token string to inspect", repr=False)
 
