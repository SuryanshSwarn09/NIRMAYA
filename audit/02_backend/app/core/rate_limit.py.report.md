# Audit Report: `backend/app/core/rate_limit.py`

**Path**: `backend/app/core/rate_limit.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 195 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Token-bucket rate limiter middleware defending authentication and API routes against brute-force and DoS · Risk: **S1 (High Risk)** · Verdict: **READY-WITH-FIXES** · Client IP spoofing via unverified `X-Forwarded-For` allows complete rate-limit bypass, and unpruned in-memory bucket dictionary causes unbounded memory growth.

---

## Layer B — Explain It
- **What problem this file solves**: Protects endpoints against denial-of-service and credential brute-forcing by enforcing sliding-window request quotas (15 req/min on `/auth`, 60 req/min on `/api/v1`).
- **How it works step by step**:
  1. `TokenBucket` tracks available tokens, replenishing continuously based on elapsed time.
  2. `RateLimiter._get_client_identifier` derives client key from `X-Forwarded-For`, client IP, or bearer token.
  3. `RateLimitingMiddleware` checks token availability before passing request to endpoint.
  4. If exhausted, immediately returns HTTP 429 with standard headers (`Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`).
- **Concepts & patterns used**:
  - *Token Bucket Algorithm*: Allows short bursts while enforcing an average rate limit.
  - *Sliding-Window Replenishment*: Computes token credit mathematically via `time.time() - last_updated`.
- **Key lines to read first**:
  - `backend/app/core/rate_limit.py:22-54`: `TokenBucket` implementation with thread locks.
  - `backend/app/core/rate_limit.py:90-113`: Client identifier resolution.
  - `backend/app/core/rate_limit.py:159-184`: HTTP 429 response generation.
- **How to change it safely**:
  - Changing limits should be done in `backend/app/core/config.py` rather than hardcoding in this file.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `time`, `math`, `threading`, `starlette.middleware`, `app.core.config.settings`.
   - **Imported by**: `backend/app/main.py:15, 57`.
   - **Public surface**: `TokenBucket`, `RateLimiter`, `rate_limiter`, `RateLimitingMiddleware`.

2. **Security [SEC]**:
   - *CWE-290 (Authentication Bypass by Spoofing) / OWASP A07:2021*: Lines 93-95 trust raw `X-Forwarded-For` headers without validating that the upstream connection originates from a trusted reverse proxy (e.g. Caddy/Nginx). An attacker can inject `X-Forwarded-For: 1.2.3.X` with each request to completely bypass rate limiting.
   - *CWE-770 (Uncontrolled Resource Consumption) / OWASP A05:2021*: `RateLimiter._buckets: Dict[str, TokenBucket]` stores buckets in an unbounded in-memory dictionary. There is no TTL purge, expiration thread, or LRU eviction. Generating requests with random IP headers will exhaust server RAM.
   - *Multi-Worker Isolation*: Under multi-process Uvicorn (e.g. 4 workers in `docker-compose.yml:92`), each worker maintains its own isolated memory dictionary.

3. **Code quality [QUAL]**:
   - Thread safety is handled via `threading.Lock()`.
   - Clear exempt path handling (`EXEMPT_PATHS`).

4. **AI-generated smells [QUAL]**:
   - Unused `asyncio` import on line 11.
   - Token fingerprinting on line 105 uses Python's built-in `hash(token)` which is randomized per process restart, causing inconsistencies.

5. **Performance [PERF]**:
   - Thread lock contention under heavy concurrency (thousands of simultaneous requests). In distributed deployments, Redis token buckets (`redis-py`) should replace local dictionary locks.

6. **Error handling & edge cases**:
   - Safely handles missing `request.client` via fallback to `"127.0.0.1"`.

7. **Doc accuracy [DOC]**:
   - Accurately implements rate limiting claims from `docs/architecture/`.

8. **Tests**:
   - Thoroughly tested in `backend/tests/test_rate_limit.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-RAT-F01** | **S1** | `[SEC]` | `93-99` | Client IP spoofing via unvalidated `X-Forwarded-For` header | `forwarded_for.split(",")[0].strip()` | Only trust `X-Forwarded-For` if upstream is verified proxy |
| **BE-RAT-F02** | **S2** | `[PERF]` | `72, 133-140` | Unbounded memory dictionary in `_buckets` (DoS risk) | `self._buckets[bucket_key] = TokenBucket(...)` | Implement periodic cleanup or LRU cache eviction |
| **BE-RAT-F03** | **S3** | `[QUAL]` | `105` | Non-cryptographic Python `hash()` used for token fingerprint | `abs(hash(token)) % 1000000` | Use `hashlib.sha256(token.encode()).hexdigest()[:16]` |

---

## Suggested Patches (NOT Applied)

### Patch BE-RAT-P01 · risk of change: med · [UNTESTED]
```diff
--- a/backend/app/core/rate_limit.py
+++ b/backend/app/core/rate_limit.py
@@ -92,4 +92,5 @@ class RateLimiter:
-        # Check IP address (accounting for reverse proxies)
-        forwarded_for = request.headers.get("X-Forwarded-For")
-        if forwarded_for:
-            client_ip = forwarded_for.split(",")[0].strip()
+        # Strictly rely on direct client socket unless trusted proxy is verified
+        client_ip = request.client.host if request.client else "127.0.0.1"
+        if client_ip in {"127.0.0.1", "::1", "172.18.0.1"}:
+            forwarded_for = request.headers.get("X-Forwarded-For")
+            if forwarded_for:
+                client_ip = forwarded_for.split(",")[0].strip()
```

---

## Verdict
**READY-WITH-FIXES** — Solid token-bucket implementation; requires locking down reverse proxy IP trust and adding bucket memory cleanup.
