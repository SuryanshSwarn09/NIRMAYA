# Audit Report: `backend/app/core/security.py`

**Path**: `backend/app/core/security.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 103 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Cryptographic JWT encoding/decoding and password verification engine · Risk: **S1 (High Risk)** · Verdict: **READY-WITH-FIXES** · Weak single-round SHA-256 password hashing instead of bcrypt/Argon2, timing side-channel in password verification, and permissive JWT fallback keys.

---

## Layer B — Explain It
- **What problem this file solves**: Creates and validates HMAC-SHA256 JWT access tokens for authenticated users, and handles password hashing and verification.
- **How it works step by step**:
  1. `create_access_token` adds `iat`, `exp`, `aud` claims and signs payload using PyJWT and `settings.SECRET_KEY`.
  2. `decode_access_token` attempts decoding against candidate keys (Supabase JWT Secret, core `SECRET_KEY`).
  3. Translates PyJWT internal exceptions (`ExpiredSignatureError`, `InvalidAudienceError`) into clinical `AuthenticationException` domain errors.
  4. `verify_password` hashes input password and checks equality.
- **Concepts & patterns used**:
  - *Dual-Key Verification*: Allows validating both Supabase Auth tokens and NIRMAYA local session tokens.
  - *Fail-Fast Authentication*: Clear, typed exception mapping for expired or invalid tokens.
- **Key lines to read first**:
  - `backend/app/core/security.py:11-32`: JWT generation logic.
  - `backend/app/core/security.py:43-51`: Candidate key resolution list.
  - `backend/app/core/security.py:100-103`: Password hashing implementation.
- **How to change it safely**:
  - Updating token expiration or signing algorithms must be mirrored across frontend and Supabase configurations.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `datetime`, `hashlib`, `jwt`, `app.core.config.settings`, `app.core.exceptions.AuthenticationException`.
   - **Imported by**: `backend/app/core/dependencies.py:14`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/services/auth_service.py`.
   - **Public surface**: `create_access_token`, `decode_access_token`, `verify_password`, `get_password_hash`.

2. **Security [SEC]**:
   - *CWE-328 (Use of Weak Cryptographic Hash) & CWE-916 (Use of Password Hash with Insufficient Computational Effort) / OWASP A02:2021*: Lines 100-103 implement password hashing via `hashlib.sha256(salted).hexdigest()`. Single-round SHA-256 is dangerously fast (>10 billion hashes/sec on modern GPUs) and vulnerable to dictionary and rainbow table cracking. Even though `passlib[bcrypt]` is in `requirements.txt`, bcrypt is NOT used here.
   - *CWE-208 (Observable Timing Discrepancy) / OWASP A02:2021*: Line 97 compares hashes via `return get_password_hash(plain_password) == hashed_password`. Standard Python string equality short-circuits on the first non-matching byte, leaking timing clues. Must use `hmac.compare_digest`.
   - *CWE-321 (Use of Hard-coded Cryptographic Key)*: Lines 49-50 re-add `settings.SUPABASE_JWT_SECRET` unconditionally to `candidate_keys`, validating tokens against the placeholder key if unset.

3. **Code quality [QUAL]**:
   - Exception handling in `decode_access_token` is clear and maps cleanly to domain errors.

4. **AI-generated smells [QUAL]**:
   - `get_password_hash` states in docstring: "Generate a deterministic SHA-256 hash for simulated developer authentication." This prototype shortcut was left in the production security path.

5. **Performance [PERF]**:
   - Fast token generation and verification using PyJWT.

6. **Error handling & edge cases**:
   - Strips `"Bearer "` prefix safely with whitespace tolerance.

7. **Doc accuracy [DOC]**:
   - `README.md` and `docs/` claim Passlib bcrypt hashing, but source actually executes SHA-256.

8. **Tests**:
   - Tested in `backend/tests/test_auth_jwt.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-SEC-F01** | **S1** | `[SEC]` | `100-103` | Broken single-round SHA-256 password hashing | `hashlib.sha256(salted).hexdigest()` | Replace with `bcrypt` / `passlib.context.CryptContext` |
| **BE-SEC-F02** | **S2** | `[SEC]` | `97` | Timing side-channel in string equality | `return get_password_hash(...) == hashed_password` | Use `hmac.compare_digest` |
| **BE-SEC-F03** | **S2** | `[SEC]` | `49-51` | Fallback keys list accepts placeholder Supabase secret | `candidate_keys.append(settings.SUPABASE_JWT_SECRET)` | Strictly filter out placeholder strings |

---

## Suggested Patches (NOT Applied)

### Patch BE-SEC-P01 · risk of change: med · [UNTESTED]
```diff
--- a/backend/app/core/security.py
+++ b/backend/app/core/security.py
@@ -5,2 +5,3 @@ from typing import Any, Dict, Optional
 import hashlib
+import hmac
 import jwt
+from passlib.context import CryptContext
 from app.core.config import settings
@@ -8,2 +9,4 @@ from app.core.exceptions import AuthenticationException
 
+pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
+
@@ -95,8 +98,8 @@ def decode_access_token(
 def verify_password(plain_password: str, hashed_password: str) -> bool:
     """Verify a plain-text password against a hashed representation."""
-    return get_password_hash(plain_password) == hashed_password
+    return pwd_context.verify(plain_password, hashed_password)
 
 
 def get_password_hash(password: str) -> str:
-    """Generate a deterministic SHA-256 hash for simulated developer authentication."""
-    salted = f"{settings.SECRET_KEY}:{password}".encode("utf-8")
-    return hashlib.sha256(salted).hexdigest()
+    """Generate a salted bcrypt hash adhering to healthcare credential storage standards."""
+    return pwd_context.hash(password)
```

---

## Verdict
**READY-WITH-FIXES** — PyJWT decoder is well structured; replacing single-round SHA-256 with standard bcrypt is a critical security fix.
