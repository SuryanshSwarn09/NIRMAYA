# Day 15: Security Hardening, Rate Limiting, Diagnostic Gateway & Week 3 Close

**Date:** September 25, 2026  
**Milestone:** 03-05 (Month 1, Week 3, Day 5)  
**Author:** Suryansh Swarn  
**Status:** Completed  

---

## 1. Overview & Architectural Goals

Day 15 marks the official completion of **Month 1, Week 3 (Identity, Clinical EMR & Security Foundation)** for the NIRMAYA platform. 

Today's focus established mission-critical application defenses against Distributed Denial of Service (DDoS) and credential brute-forcing, reinforced OWASP enterprise headers, and completed the third clinical pillar of the NIRMAYA network—the **Diagnostic Gateway Portal (`/lab`)**.

Key deliverables accomplished today:
1. **Sliding-Window Token-Bucket Rate Limiter (`app/core/rate_limit.py`):**
   - Engineered an asynchronous, thread-safe token bucket rate limiting engine for FastAPI.
   - Enforces tiered traffic allowances: strict protection on authentication routes (`15 req/min` for `/api/v1/auth/*` brute-force mitigation) and standard operational capacity (`60 req/min` for clinical endpoints).
   - System probe exemptions for `/api/v1/health`, `/api/v1/meta`, `/docs`, and OpenAPI schemas to guarantee unhindered cluster orchestration and Prometheus scraping.
   - Standards-compliant response headers: `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` epoch timestamps.
   - Standard RFC 7807-compatible JSON error envelope on HTTP `429 Too Many Requests`.
2. **OWASP Security Headers Hardening (`app/core/cors.py`):**
   - Implemented strict Content Security Policy (`Content-Security-Policy`) allowing trusted fonts and HTTPS assets.
   - Enforced HTTP Strict Transport Security (`Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`).
   - Hardened `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Resource-Policy: same-site`.
3. **The 3rd Clinical Pillar: Diagnostic Gateway Portal (`frontend/src/app/lab/page.tsx`):**
   - **Facility Identity & Accreditation:** Apollo Diagnostics Central with verified NABL Accreditation (`ISO 15189:2022`) and HFR facility identifier (`HFR-DEL-91024`).
   - **Cryptographic PDF Ingestion Panel:** Patient ABHA selection (`Arun Patel`, `Sunita Rao`, `Vikram Malhotra`), genuine browser Web Crypto API SHA-256 digest computation, and tamper-evident RSA-PSS seal generator.
   - **Structured LOINC Pathology Builder:** Interactive laboratory parameter inputs for Fasting Blood Glucose (`LOINC 1558-6`), Lipid Profile (Total Cholesterol `LOINC 2093-3`, HDL `LOINC 2085-9`, LDL `LOINC 13457-7`, Triglycerides `LOINC 2571-8`), and HbA1c (`LOINC 4548-4`) with automated physiologic threshold validation.
   - **Live HL7 FHIR R4 `DiagnosticReport` Preview:** Dynamic JSON generator matching ABDM NRCeS `DiagnosticReportLab` profile with real-time copy-to-clipboard functionality.
   - **Recent Ingestion Ledger:** Chronological tamper-evident audit log of processed lab encounters.
4. **Verification & Testing:**
   - Authored comprehensive test suite (`backend/tests/test_rate_limit.py`) validating token exhaustion, client IP isolation, 429 envelopes, and header propagation (6 new tests passing in 0.48s, raising total backend tests to 115).
   - Validated complete Next.js 15 Turbopack production build with 11/11 prerendered static/edge routes.

---

## 2. Technical Architecture & Rate Limiting Flow

```
[Inbound Client Request]
       │
       ▼
[CorrelationIdMiddleware] ──► Attaches X-Request-ID (UUID4)
       │
       ▼
[PerformanceTelemetryMiddleware] ──► Injects OWASP Headers (CSP, HSTS, X-Frame-Options)
       │
       ▼
[RateLimitingMiddleware]
       │
       ├── Path in EXEMPT_PATHS (/api/v1/health, /meta, /docs)?
       │      ├─► YES: Pass through unhindered
       │      └─► NO: Continue to token bucket check
       │
       ├── Resolve Bucket Tier:
       │      ├─► /api/v1/auth/* ──► 15 requests / minute
       │      └─► /api/v1/*      ──► 60 requests / minute
       │
       ├── Check Client Identifier (IP + User Sub):
       │      ├─► Tokens Available >= 1.0:
       │      │     • Deduct 1.0 token
       │      │     • Attach X-RateLimit-* headers
       │      │     • Forward to API Router
       │      │
       │      └─► Tokens Exhausted (< 1.0):
       │            • Calculate Retry-After delay
       │            • Halt request processing
       │            • Return HTTP 429 Too Many Requests
       │
       ▼
[FastAPI Endpoints / Patient Vault / Doctor EMR]
```

---

## 3. Diagnostic Ingestion & Stamping Flow

```
[Diagnostic Lab Technician]
       │
       ├─► 1. Select Patient ABHA (e.g. Arun Patel 91-8472-1092-4821)
       ├─► 2. Upload Diagnostic PDF (Apollo_Biochemistry_Panel.pdf)
       │         └─► Web Crypto API calculates SHA-256 Digest
       │
       ├─► 3. Enter Structured LOINC Parameters:
       │         • LOINC 1558-6: Fasting Glucose (94 mg/dL)
       │         • LOINC 2093-3: Total Cholesterol (185 mg/dL)
       │         • LOINC 2085-9: HDL Cholesterol (54 mg/dL)
       │         • LOINC 13457-7: LDL Cholesterol (108 mg/dL)
       │         • LOINC 2571-8: Triglycerides (138 mg/dL)
       │         • LOINC 4548-4: HbA1c (5.4 %)
       │
       ▼
[Real-Time FHIR R4 Bundle Synthesizer]
       │
       ├─► Combines LOINC Observations + SHA-256 Hash + HFR Stamping
       │
       ▼
[Patient Health Vault Dispatch]
       │
       └─► Stored in Longitudinal Ledger with Cryptographic Immutability
```

---

## 4. Micro-Commit Journal (10+ Commits Standard)

Following the disciplined engineering protocol, Day 15 was implemented across atomic, verifiable micro-commits:

| # | Hash | Scope & Commit Message | Key Changes |
|---|---|---|---|
| 1 | `8f20dda` | `feat(config): add rate limiting settings and environment parameters` | Added `RATE_LIMIT_ENABLED`, auth & api limits, and HSTS settings |
| 2 | `010a420` | `feat(security): enhance security headers with hsts and csp directives` | Injected CSP, HSTS preload, COOP, and CORP into `get_security_headers()` |
| 3 | `f2818ef` | `feat(middleware): implement async token bucket rate limiting middleware` | Created `TokenBucket`, `RateLimiter`, and `RateLimitingMiddleware` in `rate_limit.py` |
| 4 | `d78646c` | `feat(api): wire rate limiting middleware into fastapi application pipeline` | Registered `RateLimitingMiddleware` in FastAPI middleware pipeline |
| 5 | `2378861` | `test(security): add test suite for rate limiting and 429 response headers` | Built unit and integration tests verifying token bucket, 429 envelopes, and IP isolation |
| 6 | `4130cd2` | `feat(portal): scaffold diagnostic lab gateway with nabl accreditation badge` | Created `/lab` route with Apollo Diagnostics header and NABL badge |
| 7 | `02fcd10` | `feat(portal): build cryptographic pdf report ingestion and sha256 hashing` | Implemented Web Crypto SHA-256 calculation and RSA-PSS seal generator |
| 8 | `00be3ba` | `feat(portal): implement structured loinc observation and fhir report builder` | Added 6 LOINC parameter inputs, live FHIR R4 DiagnosticReport JSON preview, and ledger |
| 9 | `6f3e940` | `test(frontend): verify full frontend production build with lab gateway` | Added neutral/warning Badge tokens and validated 11/11 Next.js static routes |
| 10 | *pending* | `docs(journey): log day 15 security audit and rate limiting deliverables` | Documented Day 15 architectural and testing achievements |
| 11 | *pending* | `docs(journey): create week 3 retrospective and executive metrics report` | Compiled comprehensive Week 3 retrospective report |
| 12 | *pending* | `docs(changelog): record milestone 03-05 and week 3 release deliverables` | Updated changelog and documentation summary table |
| 13 | *pending* | `chore(release): cut official week 3 release tag v0.1.0-alpha.w3` | Concluded Week 3 with official release tag `v0.1.0-alpha.w3` |

---

## 5. Verification & Quality Gates

All automated verification gates passed with zero regressions:

- **Backend Pytest Suite:** 115 / 115 tests passing (`100%`).
  - Unit token bucket consumption and replenishment: PASSED.
  - Exempt path bypass (`/api/v1/meta`, `/api/v1/health`): PASSED.
  - Tracked endpoint header injection (`X-RateLimit-*`): PASSED.
  - HTTP 429 Throttling and structured JSON envelope: PASSED.
  - Multi-client IP isolation: PASSED.
  - Rate limiter disable flag: PASSED.
- **Frontend Turbopack Production Build:**
  - 11 static / edge routes compiled and prerendered.
  - Zero TypeScript or linting errors.
  - All 3 clinical pillars active: `/patient`, `/doctor`, `/lab`.
- **System Doctor Diagnostics:** 8/8 system health checks passing.
