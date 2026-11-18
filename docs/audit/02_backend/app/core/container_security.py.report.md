# Audit Report: `backend/app/core/container_security.py`

**Path**: `backend/app/core/container_security.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 80 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
CIS Docker Benchmark v1.6.0 compliance utility evaluating container process UID and non-root execution · Risk: **S2 (Medium Risk)** · Verdict: **READY-WITH-FIXES** · Relies on untrusted environment variables before system `getuid()`, and exposes container internal process UIDs in response headers.

---

## Layer B — Explain It
- **What problem this file solves**: Enforces CIS Docker Benchmark Section 4.1 requiring containers to run as unprivileged users (UID 10001 `nirmaya`) rather than root (`UID 0`).
- **How it works step by step**:
  1. Checks if current execution is running as root via `is_running_as_root()`.
  2. Evaluates `NIRMAYA_PROCESS_UID` environment variable or calls `os.getuid()`.
  3. Provides `enforce_container_security_guard()` to abort execution or emit warnings if root privileges are detected in production.
  4. Generates standard audit headers (`X-Container-Runtime`, `X-Process-UID`, `X-Process-User`) via `get_container_security_headers()`.
- **Concepts & patterns used**:
  - *Defense in Depth*: Application-level verification of container boundary hardening.
  - *Non-Root Execution (CIS 4.1)*: Limiting blast radius if container escape occurs.
- **Key lines to read first**:
  - `backend/app/core/container_security.py:24-34`: Implementation of `is_running_as_root()`.
  - `backend/app/core/container_security.py:51-67`: Security guard logic and exception raising.
  - `backend/app/core/container_security.py:70-80`: Response header generation.
- **How to change it safely**:
  - Ensure Windows local development does not crash due to missing `os.getuid` (POSIX only).

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `os`, `logging`, `typing`, `fastapi.HTTPException`, `app.core.config.settings`.
   - **Imported by**: `backend/app/api/v1/endpoints/container.py` and `backend/app/api/v1/endpoints/orchestration.py`.
   - **Public surface**: `is_running_as_root`, `get_container_process_identity`, `enforce_container_security_guard`, `get_container_security_headers`.

2. **Security [SEC]**:
   - *CWE-20 (Improper Input Validation)*: Lines 26-28 inspect `os.environ.get("NIRMAYA_PROCESS_UID")` prior to `os.getuid()`. A compromised or tampered environment variable can fool the application into believing it is non-root when it is actually running as UID 0.
   - *CWE-200 (Information Exposure) / OWASP A01:2021*: Lines 76-80 inject `X-Process-UID` and `X-Process-User` into HTTP response headers, exposing internal infrastructure details to clients.
   - *CWE-276 (Default Permissions)*: Line 51 sets `strict_mode: bool = False` by default; root execution only logs a warning unless explicitly called with `strict_mode=True`.

3. **Code quality [QUAL]**:
   - Good fallback handling for platforms where `os.getuid` does not exist (Windows).
   - Code is concise and well-commented.

4. **AI-generated smells [QUAL]**:
   - Fabricated simulated fallback values (`(OFFICIAL_NON_ROOT_UID, OFFICIAL_NON_ROOT_USER)`) on Windows (lines 47-48) without logging that it is an artificial simulation.

5. **Performance [PERF]**:
   - Lightweight, zero measurable overhead.

6. **Error handling & edge cases**:
   - Gracefully handles non-numeric environment values via `env_uid.isdigit()`.

7. **Doc accuracy [DOC]**:
   - Accurately aligns with CIS Docker Benchmark v1.6.0 Section 4.1 claims.

8. **Tests**:
   - Covered in `backend/tests/test_container_orchestration.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-CSEC-F01** | **S2** | `[SEC]` | `26-32` | Environment variable overrides actual OS UID | `env_uid = os.environ.get("NIRMAYA_PROCESS_UID")` | Query `os.getuid()` first; use env var only as simulated fallback |
| **BE-CSEC-F02** | **S2** | `[SEC]` | `76-80` | Internal UID/User leakage in public HTTP headers | `"X-Process-UID": str(uid)` | Restrict headers to internal admin endpoints only |
| **BE-CSEC-F03** | **S3** | `[SEC]` | `51` | Default `strict_mode = False` makes check advisory | `def enforce_container_security_guard(strict_mode=False)` | Default to `True` when `settings.is_production` |

---

## Suggested Patches (NOT Applied)

### Patch BE-CSEC-P01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/core/container_security.py
+++ b/backend/app/core/container_security.py
@@ -24,8 +24,8 @@ def is_running_as_root() -> bool:
     """Check if current process has root / superuser privileges (UID 0)."""
+    if hasattr(os, "getuid"):
+        return os.getuid() == 0
+
     env_uid = os.environ.get("NIRMAYA_PROCESS_UID")
     if env_uid is not None and env_uid.isdigit():
         return int(env_uid) == 0
-
-    if hasattr(os, "getuid"):
-        return os.getuid() == 0
 
     return False
```

---

## Verdict
**READY-WITH-FIXES** — Valuable container compliance module; requires reversing UID lookup priority to prevent environment spoofing.
