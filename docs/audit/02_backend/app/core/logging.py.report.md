# Audit Report: `backend/app/core/logging.py`

**Path**: `backend/app/core/logging.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 38 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Structured clinical logging configuration with correlation ID formatting and Uvicorn noise suppression · Risk: **S3 (Low Risk)** · Verdict: **READY-WITH-FIXES** · Functional standardized logging; formats timestamps at render time rather than record creation, and silences Uvicorn pre-middleware access logs.

---

## Layer B — Explain It
- **What problem this file solves**: Replaces unstructured print statements with unified, audit-compliant log lines format `[timestamp UTC] [LEVEL] [req:correlation_id] logger_name: message`.
- **How it works step by step**:
  1. Defines `ClinicalLogFormatter` extracting `record.request_id` if present.
  2. Sets up `logger = logging.getLogger("nirmaya")` with `StreamHandler(sys.stdout)`.
  3. Throttles noisy external library loggers (`uvicorn.access` set to `WARNING`).
  4. Automatically initializes and exports singleton `logger`.
- **Concepts & patterns used**:
  - *Correlation Tracing*: Attaches `[req:<id>]` to all logs emitted during an HTTP lifecycle.
  - *Stream Logging*: Follows 12-Factor App methodology by routing logs to `stdout`.
- **Key lines to read first**:
  - `backend/app/core/logging.py:9-17`: Custom formatter implementation.
  - `backend/app/core/logging.py:20-35`: Logger configuration setup function.
- **How to change it safely**:
  - Ensure any custom log calls pass `extra={"request_id": request_id}` to take advantage of correlation tracking.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `logging`, `sys`, `datetime.timezone`.
   - **Imported by**: `backend/app/core/middleware.py`, `backend/app/core/__init__.py`, and various endpoints.
   - **Public surface**: `ClinicalLogFormatter`, `setup_clinical_logging`, `logger`.

2. **Security [SEC]**:
   - Sanitization: Logs string representations directly without checking for CRLF log injection (CWE-117). If user input is passed directly to `logger.info`, an attacker could inject newline characters to spoof audit entries.

3. **Code quality [QUAL]**:
   - Clean, concise standard library implementation.
   - Guard `if not logger.handlers:` prevents duplicate handlers during hot-reload.

4. **AI-generated smells [QUAL]**:
   - Hardcoded logger throttling values.

5. **Performance [PERF]**:
   - Synchronous stdout stream writing. For extremely high-throughput production (10k+ req/sec), an asynchronous non-blocking queue handler is recommended.

6. **Error handling & edge cases**:
   - Defaults missing `request_id` to `"-"`.

7. **Doc accuracy [DOC]**:
   - Matches claims in `docs/architecture/` regarding audit trace formatting.

8. **Tests**:
   - Covered in `backend/tests/test_health.py` and `backend/tests/test_logging.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-LOG-F01** | **S3** | `[SEC]` | `17` | Potential log injection via unsanitized message newlines | `return f"... {record.name}: {message}"` | Strip `\r\n` from unformatted log messages (CWE-117) |
| **BE-LOG-F02** | **S3** | `[QUAL]` | `13` | Timestamp generated at format time rather than record creation | `timestamp = datetime.now(timezone.utc)...` | Use `datetime.fromtimestamp(record.created, timezone.utc)` |
| **BE-LOG-F03** | **S3** | `[QUAL]` | `32` | Complete suppression of `uvicorn.access` hides syntax errors | `logging.getLogger("uvicorn.access").setLevel(logging.WARNING)` | Keep INFO level in staging/dev |

---

## Suggested Patches (NOT Applied)

### Patch BE-LOG-P01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/core/logging.py
+++ b/backend/app/core/logging.py
@@ -13,4 +13,4 @@ class ClinicalLogFormatter(logging.Formatter):
     def format(self, record: logging.LogRecord) -> str:
-        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
+        timestamp = datetime.fromtimestamp(record.created, timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
         request_id = getattr(record, "request_id", "-")
         log_level = record.levelname.ljust(8)
-        message = super().format(record)
+        message = super().format(record).replace("\r", "").replace("\n", " ")
         return f"[{timestamp} UTC] [{log_level}] [req:{request_id}] {record.name}: {message}"
```

---

## Verdict
**READY-WITH-FIXES** — Lightweight and effective; minor timestamp alignment and newline sanitization recommended.
