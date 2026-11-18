# Audit Report: `backend/app/core/exceptions.py`

**Path**: `backend/app/core/exceptions.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 177 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Custom clinical domain exception hierarchy and standardized FastAPI global exception handlers · Risk: **S2 (Medium Risk)** · Verdict: **READY-WITH-FIXES** · Global 500 handler fails to log unhandled server exceptions, causing silent production failures, and leaks internal exception text when `DEBUG` is true.

---

## Layer B — Explain It
- **What problem this file solves**: Replaces generic unhandled HTTP errors with consistent, machine-readable JSON envelopes (`success: false`, `error_code`, `message`, `timestamp`, `request_id`).
- **How it works step by step**:
  1. Declares `AppException` base class inheriting from Python's built-in `Exception`.
  2. Implements domain-specific subclasses: `EntityNotFoundException` (404), `PermissionDeniedException` (403), `AuthenticationException` (401), `ConflictException` (409), `ValidationException` (400).
  3. `register_exception_handlers(app)` binds four handlers: `AppException`, `RequestValidationError` (422), `StarletteHTTPException`, and a catch-all `Exception` (500).
  4. Injects active `request_id` from `request.state` into every error response for correlation.
- **Concepts & patterns used**:
  - *Standardized Error Envelope*: Assures all frontend API consumers receive a predictable error shape.
  - *Correlation Tracing*: Attaches `request_id` to trace client errors directly to backend logs.
- **Key lines to read first**:
  - `backend/app/core/exceptions.py:12-27`: `AppException` definition.
  - `backend/app/core/exceptions.py:102-121`: Handling of domain exceptions.
  - `backend/app/core/exceptions.py:164-177`: Global 500 handler.
- **How to change it safely**:
  - Subclass `AppException` for new errors; never raise raw `HTTPException` directly in services.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `fastapi.Request`, `fastapi.responses.JSONResponse`, `starlette.exceptions.HTTPException`, `app.schemas.common.ErrorDetail`.
   - **Imported by**: Mounted in `backend/app/main.py:48` and imported across endpoints and services.
   - **Public surface**: `AppException`, `EntityNotFoundException`, `PermissionDeniedException`, `AuthenticationException`, `ConflictException`, `ValidationException`, `register_exception_handlers`.

2. **Security [SEC]**:
   - *CWE-778 (Insufficient Logging) / OWASP A09:2021 Security Logging and Monitoring Failures*: In `global_exception_handler` (`lines 165-177`), unhandled exceptions produce an HTTP 500 response, but there is NO `logger.exception(exc)` or `logger.error(...)` statement. Crashes occur silently without backend stack trace logs.
   - *CWE-209 (Information Exposure Through Error Message) / OWASP A05:2021*: Line 173 returns `details: [{"message": str(exc)}] if app.debug else []`. Coupled with `DEBUG = True` by default in `config.py`, raw database error strings and internal trace details leak to client responses.

3. **Code quality [QUAL]**:
   - Clean, well-structured exception inheritance.
   - Good conversion of Pydantic validation errors in `validation_exception_handler` (lines 124-147).

4. **AI-generated smells [QUAL]**:
   - Omitting `logger.exception` inside a catch-all `except Exception` handler is a classic AI omission pattern where response generation is prioritized over operational logging.

5. **Performance [PERF]**:
   - Minimal overhead; formatting occurs only on error paths.

6. **Error handling & edge cases**:
   - Handles missing `request_id` gracefully via `getattr(request.state, "request_id", None)`.

7. **Doc accuracy [DOC]**:
   - Aligns with API documentation claims regarding uniform error envelopes.

8. **Tests**:
   - Tested in `backend/tests/test_exceptions.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-EXC-F01** | **S2** | `[QUAL]` | `165-177` | Uncaught 500 exceptions are not logged | `async def global_exception_handler(request: Request, exc: Exception):` (no logger call) | Add `logger.exception("Unhandled server exception: %s", exc, extra={"request_id": request_id})` |
| **BE-EXC-F02** | **S2** | `[SEC]` | `173` | Error message string leaked when `app.debug` is True | `"details": [{"message": str(exc)}] if app.debug else []` | Suppress raw exception strings in production |

---

## Suggested Patches (NOT Applied)

### Patch BE-EXC-P01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/core/exceptions.py
+++ b/backend/app/core/exceptions.py
@@ -8,2 +8,3 @@ from typing import Optional, List
 from datetime import datetime, timezone
+from app.core.logging import logger
 from app.schemas.common import ErrorDetail
@@ -166,2 +167,3 @@ def register_exception_handlers(app):
         request_id = getattr(request.state, "request_id", None)
+        logger.exception("Internal Server Error [req:%s]: %s", request_id, exc, extra={"request_id": request_id})
         return JSONResponse(
```

---

## Verdict
**READY-WITH-FIXES** — Excellent envelope structure; adding logging for uncaught 500 errors is essential for production observability.
