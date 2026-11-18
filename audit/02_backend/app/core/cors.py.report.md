# Audit Report: `backend/app/core/cors.py`

**Path**: `backend/app/core/cors.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 45 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
CORS origin resolution and healthcare compliance HTTP security headers · Risk: **S3 (Low Risk)** · Verdict: **READY-WITH-FIXES** · Functional GIGW 3.0 / healthcare security header generator; CSP contains `'unsafe-inline'` and header dictionary is repeatedly re-allocated per request.

---

## Layer B — Explain It
- **What problem this file solves**: Normalizes allowed cross-origin web domains and defines standard healthcare security headers (CSP, HSTS, X-Frame-Options, Permissions-Policy).
- **How it works step by step**:
  1. `get_allowed_origins()` normalizes URIs in `settings.BACKEND_CORS_ORIGINS` by trimming whitespace and trailing slashes.
  2. `get_security_headers()` constructs a dictionary of 11 standard headers including `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and `Strict-Transport-Security`.
  3. Dynamically adds HSTS header when in production or when `SECURITY_HSTS_SECONDS > 0`.
- **Concepts & patterns used**:
  - *Hardening Headers*: Defends against clickjacking (`DENY`), MIME confusion (`nosniff`), and man-in-the-middle attacks (`HSTS`).
  - *Content Security Policy (CSP)*: Declares trusted origins for scripts, styles, fonts, and API connections.
- **Key lines to read first**:
  - `backend/app/core/cors.py:7-17`: URI normalization logic.
  - `backend/app/core/cors.py:29-37`: Content-Security-Policy string.
- **How to change it safely**:
  - Modifying CSP directives must be tested against Next.js font and style injections to prevent frontend rendering breakage.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `typing.List`, `typing.Dict`, `app.core.config.settings`.
   - **Imported by**: `backend/app/main.py:10` and `backend/app/core/middleware.py:7`.
   - **Public surface**: `get_allowed_origins() -> List[str]`, `get_security_headers() -> Dict[str, str]`.

2. **Security [SEC]**:
   - *CWE-79 / OWASP A03:2021*: CSP includes `'unsafe-inline'` for `script-src` and `style-src` (`lines 31-32`). While necessary for certain frontend SSR hydration setups, nonce-based CSP is preferred in sensitive healthcare contexts.
   - *Positive Security Controls*: Explicit `frame-ancestors 'none'`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Permissions-Policy: geolocation=(), camera=(), microphone=()`.

3. **Code quality [QUAL]**:
   - Clean, focused utility.

4. **AI-generated smells [QUAL]**:
   - None observed.

5. **Performance [PERF]**:
   - `get_security_headers()` constructs a new 11-key dictionary and string concatenations on every single HTTP request via `PerformanceTelemetryMiddleware`. A module-level cached dictionary would avoid allocation overhead.

6. **Error handling & edge cases**:
   - Gracefully handles empty or trailing-slash origins.

7. **Doc accuracy [DOC]**:
   - Matches GIGW 3.0 and OWASP secure header recommendations.

8. **Tests**:
   - Tested in `backend/tests/test_cors_security.py` and `backend/tests/test_health.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-CORS-F01** | **S3** | `[SEC]` | `31-32` | Permissive `script-src 'unsafe-inline'` in CSP | `"script-src 'self' 'unsafe-inline'; "` | Transition to cryptographic nonce-based CSP |
| **BE-CORS-F02** | **S3** | `[PERF]` | `20-45` | Security headers dict re-allocated on every request | `def get_security_headers() -> Dict[str, str]:` | Cache dictionary at module load |

---

## Suggested Patches (NOT Applied)

### Patch BE-CORS-P01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/core/cors.py
+++ b/backend/app/core/cors.py
@@ -2,2 +2,3 @@
 from typing import List, Dict
+from functools import lru_cache
 from app.core.config import settings
@@ -20,2 +21,3 @@ def get_allowed_origins() -> List[str]:
+@lru_cache(maxsize=1)
 def get_security_headers() -> Dict[str, str]:
     """Provide standard security headers for healthcare information compliance."""
```

---

## Verdict
**READY-WITH-FIXES** — Excellent security header coverage; minor optimization and CSP tightening recommended.
