# Audit Report: `backend/app/core/middleware.py`

**Path**: `backend/app/core/middleware.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 51 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
ASGI middleware suite injecting performance metrics, healthcare security headers, and correlation tracking · Risk: **S3 (Low Risk)** · Verdict: **READY-WITH-FIXES** · Efficient and standard architecture; accepts untrusted inbound `X-Request-ID` without sanitization and re-computes security headers per request.

---

## Layer B — Explain It
- **What problem this file solves**: Automatically measures request duration, injects defensive HTTP headers on every response, ensures every request has a traceable UUID, and emits access audit logs.
- **How it works step by step**:
  1. `CorrelationIdMiddleware`: Inspects inbound `X-Request-ID` header; if absent, generates a new `uuid.uuid4()`. Stores it in `request.state.request_id` and echoes it on outbound response.
  2. `PerformanceTelemetryMiddleware`: Records start time using `time.perf_counter()`.
  3. Executes downstream application handlers via `await call_next(request)`.
  4. Calculates elapsed time and injects `X-Process-Time` (e.g. `1.45ms`).
  5. Injects security headers from `get_security_headers()`.
  6. Emits structured access log via `logger.info` including client IP, path, status, and request ID.
- **Concepts & patterns used**:
  - *Middleware Pipeline*: Wraps the request/response lifecycle in outer decorators.
  - *Distributed Tracing*: Propagates correlation IDs across client-server-database boundaries.
- **Key lines to read first**:
  - `backend/app/core/middleware.py:14-34`: Telemetry dispatch cycle.
  - `backend/app/core/middleware.py:40-51`: Correlation ID dispatch cycle.
- **How to change it safely**:
  - Keep `CorrelationIdMiddleware` outside `PerformanceTelemetryMiddleware` in `main.py` so `request.state.request_id` is available to the telemetry logger.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `time`, `uuid`, `fastapi.Request`, `fastapi.Response`, `starlette.middleware.base.BaseHTTPMiddleware`, `app.core.cors.get_security_headers`, `app.core.logging.logger`.
   - **Imported by**: `backend/app/main.py:11-14`.
   - **Public surface**: `PerformanceTelemetryMiddleware`, `CorrelationIdMiddleware`.

2. **Security [SEC]**:
   - *CWE-20 (Improper Input Validation)*: Lines 42-44 blindly trust the incoming client `X-Request-ID` header. If a client transmits a 50KB payload or CRLF injection characters in `X-Request-ID`, it is echoed back in the response header and stored in server logs. It should validate that the ID matches an alphanumeric/UUID format (regex `^[a-zA-Z0-9\-_]{1,64}$`) or discard and regenerate.
   - *CWE-208 (Timing Side-Channel Information Exposure)*: `X-Process-Time` provides sub-millisecond precision (`f"{process_time_ms:.2f}ms"`). In sensitive cryptographic or authentication routes, exposing exact execution time can facilitate timing attacks.

3. **Code quality [QUAL]**:
   - Clean implementation using Starlette's `BaseHTTPMiddleware`.

4. **AI-generated smells [QUAL]**:
   - None observed.

5. **Performance [PERF]**:
   - Calling `get_security_headers()` inside the middleware loop on line 23 creates repeated dictionary overhead.

6. **Error handling & edge cases**:
   - Safe client IP extraction via `request.client.host if request.client else "unknown"`.

7. **Doc accuracy [DOC]**:
   - Accurately implements telemetry claims made in `docs/architecture/`.

8. **Tests**:
   - Tested in `backend/tests/test_health.py` (`test_telemetry_headers` and `test_correlation_id`).

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-MID-F01** | **S3** | `[SEC]` | `42-45` | Unsanitized inbound `X-Request-ID` accepted and echoed | `request_id = request.headers.get("X-Request-ID")` | Validate alphanumeric/UUID format and enforce <= 64 chars |
| **BE-MID-F02** | **S3** | `[PERF]` | `23-24` | Repeated security header dictionary traversal per request | `for header, value in get_security_headers().items():` | Cache headers in a pre-constructed tuple/dict |

---

## Suggested Patches (NOT Applied)

### Patch BE-MID-P01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/core/middleware.py
+++ b/backend/app/core/middleware.py
@@ -4,2 +4,3 @@ import time
 import uuid
+import re
 from fastapi import Request, Response
@@ -37,2 +38,4 @@ class PerformanceTelemetryMiddleware(BaseHTTPMiddleware):
 
+REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9\-_]{1,64}$")
+
 class CorrelationIdMiddleware(BaseHTTPMiddleware):
@@ -42,3 +45,3 @@ class CorrelationIdMiddleware(BaseHTTPMiddleware):
         request_id = request.headers.get("X-Request-ID")
-        if not request_id:
+        if not request_id or not REQUEST_ID_REGEX.match(request_id):
             request_id = str(uuid.uuid4())
```

---

## Verdict
**READY-WITH-FIXES** — Reliable ASGI middleware; input validation on `X-Request-ID` is recommended to prevent header injection.
