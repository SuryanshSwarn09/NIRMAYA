# Day 59: Milestone 12-04 - Consent Revocation, Expired Consent & Security Penetration Testing Engine

**Milestone:** 12-04 (Month 3, Week 12 / ABDM Security Hardening & Penetration Testing)  
**Author:** Suryansh Swarn (`suryanshswarn@gmail.com`)  
**Status:** Completed & Verified (438/438 Tests Passing)  

---

## 1. Executive Summary

Day 59 delivers **Milestone 12-04 (Consent Revocation, Expired Consent & Security Penetration Testing Engine)** of the NIRMAYA 80-Day Engineering Lifecycle.

Under India's Digital Personal Data Protection (DPDP) Act 2023 and the National Health Authority (NHA) ABDM Gateway v0.5 Data Flow Specification, patient consent is dynamic, granular, and revocable at will. A production health information network must withstand active malicious attempts—ranging from replay attacks to in-transit payload tampering—while enforcing real-time revocation semantics even when transactions are mid-flight.

Day 59 formalizes the security and penetration testing framework of NIRMAYA by delivering:
1. **Dynamic Mid-Flight Revocation Guardrail:**
   - When a citizen revokes consent during health data flow (after ephemeral Curve25519 key exchange has established a cryptographic session, but before health data dispatch), [`AbdmTransferService`](file:///e:/nirmaya-side/backend/app/services/abdm_transfer.py) intercepts the state transition, immediately purges the derived symmetric key from [`CryptoSessionStore`](file:///e:/nirmaya-side/backend/app/services/abdm_crypto.py), and aborts transfer with ABDM status rejection.
2. **Expired Consent Automatic Lifecycle Transition:**
   - The instant `dataEraseAt` or the consented date window elapses, the consent record automatically transitions to `EXPIRED`. Any subsequent data request or key exchange attempt is strictly blocked.
3. **Gateway Anti-Replay Defense Engine:**
   - Enforces strict timestamp drift validation ($|now - ts| \le 300\text{s}$) and introduces a thread-safe [`RequestIdReplayCache`](file:///e:/nirmaya-side/backend/app/services/abdm_hip_bridge.py) preventing duplicate `requestId` replay attacks.
4. **Cryptographic & AEAD Integrity Barriers:**
   - Defends against malformed Curve25519 public keys, degraded nonces ($< 32$ bytes), AES-256-GCM in-transit ciphertext bit-flipping (caught via AEAD authentication tag verification), and forged SHA-256 plaintext checksums.
5. **Brute-Force Rate Limiting & Account Lockout:**
   - Enforces a 3-attempt brute-force guardrail on Aadhaar demographic OTP verification sessions before triggering automatic session destruction.
6. **REST API Gateway Endpoints ([`backend/app/api/v1/endpoints/abdm_security_audit.py`](file:///e:/nirmaya-side/backend/app/api/v1/endpoints/abdm_security_audit.py)):**
   - Mounted in [`backend/app/api/v1/router.py`](file:///e:/nirmaya-side/backend/app/api/v1/router.py) under `/abdm/security`:
     - `POST /api/v1/abdm/security/audit/run`: Executes automated penetration attack vectors across all 5 security categories.
     - `GET /api/v1/abdm/security/audit/report`: Retrieves the latest security penetration report sealed with SHA-256 proof.
     - `GET /api/v1/abdm/security/audit/vectors`: Catalogs all 12 registered penetration attack scenarios.
7. **Comprehensive Test Suite ([`backend/tests/test_abdm_security_penetration.py`](file:///e:/nirmaya-side/backend/tests/test_abdm_security_penetration.py)):**
   - 12 unit and integration tests asserting defense behavior across all attack categories.
   - **438/438 backend tests passing (100% green in 57.20s)** across all 24 test suites.
   - Clean Next.js 15.5.25 production build with 13/13 static routes generated without errors.

---

## 2. Catalog of 12 Automated Penetration Attack Vectors

| Vector ID | Category | Attack Scenario | Expected Security Defense | Status |
|---|---|---|---|---|
| `SEC-01` | Gateway Replay | Inbound webhook timestamp drift $> \pm 300\text{s}$ | Request rejected with 400 ValidationException stating drift exceeds threshold | `BLOCKED` |
| `SEC-02` | Gateway Replay | Replayed request with duplicate `requestId` UUID | Request detected in replay cache and rejected with ValidationException | `BLOCKED` |
| `SEC-03` | Consent Lifecycle | Consent revoked mid-flight between key exchange and data push | Active crypto session purged; data push aborted with authorization error | `BLOCKED` |
| `SEC-04` | Consent Lifecycle | Data transfer attempted after consent `dataEraseAt` expired | Auto-transition to `EXPIRED`; health record transfer request blocked | `BLOCKED` |
| `SEC-05` | Scope Escalation | HIU requests care context not authorized in consent artefact | Care context filter blocks unconsented clinical encounters | `BLOCKED` |
| `SEC-06` | Scope Escalation | HIU requests `hiType` (e.g. `DiagnosticReport`) not granted in consent | HI-type filter blocks unauthorized clinical document category | `BLOCKED` |
| `SEC-07` | Scope Escalation | HIU requests clinical records outside consented `dateRange` | Date range boundary filter blocks out-of-bounds records | `BLOCKED` |
| `SEC-08` | Crypto Integrity | HIU submits malformed Curve25519 public key (corrupt length/encoding) | Key parser raises ValidationException; key agreement aborted | `BLOCKED` |
| `SEC-09` | Crypto Integrity | HIU submits degraded all-zero or truncated nonce ($< 32$ bytes) | Nonce validation rejects weak entropy product | `BLOCKED` |
| `SEC-10` | AEAD Integrity | Ciphertext byte flipped or corrupted in transit | AES-256-GCM AEAD tag check fails (`InvalidTag`); decryption rejected | `BLOCKED` |
| `SEC-11` | AEAD Integrity | Tampered clinical payload with forged SHA-256 checksum | Checksum validator detects disparity between payload and digest | `BLOCKED` |
| `SEC-12` | Brute Force | Attacker attempts $> 3$ invalid OTPs against transaction session | Session invalidated, attempts locked, rate-limit enforced | `BLOCKED` |

---

## 3. Architecture & Security Defense Flow

```
                      POST /api/v1/abdm/security/audit/run
                                        │
                                        ▼
                         [AbdmSecurityAuditService]
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            ▼                           ▼                           ▼
    Category 1: Replay        Category 2: Consent         Category 3: Scope
   ─────────────────────     ─────────────────────       ─────────────────────
   • SEC-01: Drift > 300s    • SEC-03: Mid-Flight Rev    • SEC-05: Care Context
   • SEC-02: Dup Request-ID  • SEC-04: Expired Consent   • SEC-06: HI-Type Scope
            │                           │                • SEC-07: Date Boundaries
            │                           │                           │
            └───────────────────────────┼───────────────────────────┘
                                        │
            ┌───────────────────────────┴───────────────────────────┐
            ▼                                                       ▼
    Category 4: Crypto & AEAD                              Category 5: Brute Force
   ───────────────────────────                            ─────────────────────────
   • SEC-08: Malformed X25519 Key                         • SEC-12: OTP Max Attempts
   • SEC-09: Degraded Nonce (<32B)                                  │
   • SEC-10: AES-256-GCM Bit-Flip                                   │
   • SEC-11: Checksum Forgery                                       │
            │                                                       │
            └───────────────────────────┬───────────────────────────┘
                                        │
                                        ▼
                          Compile Security Metrics
                  (Vulnerabilities: 0, Defense Rate: 100%)
                                        │
                                        ▼
                      Generate SHA-256 Security Proof
                 SHA-256(reportId : facilityId : 100.0 : 12 : 0)
                                        │
                                        ▼
                         [SecurityPenetrationReport]
                         Status: SECURE_CONFORMING
```

---

## 4. Verification & Testing Benchmark

The dedicated security penetration suite is located in [`backend/tests/test_abdm_security_penetration.py`](file:///e:/nirmaya-side/backend/tests/test_abdm_security_penetration.py).

```
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0
collected 12 items

backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationEngine::test_run_full_security_penetration_suite PASSED [  8%]
backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationEngine::test_selective_category_gateway_replay PASSED [ 16%]
backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationEngine::test_selective_category_consent_lifecycle PASSED [ 25%]
backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationEngine::test_selective_category_scope_escalation PASSED [ 33%]
backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationEngine::test_selective_category_cryptographic_integrity PASSED [ 41%]
backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationEngine::test_selective_category_rate_limit PASSED [ 50%]
backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationEngine::test_get_latest_cached_report PASSED [ 58%]
backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationEngine::test_vector_catalog_metadata PASSED [ 66%]
backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationAPI::test_api_run_full_audit PASSED [ 75%]
backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationAPI::test_api_run_selective_categories PASSED [ 83%]
backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationAPI::test_api_get_latest_report PASSED [ 91%]
backend/tests/test_abdm_security_penetration.py::TestAbdmSecurityPenetrationAPI::test_api_get_vector_catalog PASSED [100%]

======================== 12 passed, 1 warning in 0.34s ========================
```

**Full Backend Regression Benchmark:**  
`438 passed, 3 warnings in 57.20s (100% green)` across all 24 test suites.

**Frontend Production Build Benchmark:**  
`npm --prefix frontend run build` exited with code 0; all 13/13 static routes generated successfully.

---

## 5. Next Steps

With Day 59 successfully delivered, engineering advances to **Day 60: Milestone 12-05 - Month 3 Retrospective, Documentation Finalization & Milestone Release v0.3.0** (cutting release tag `v0.3.0`, updating master documentation monographs, and concluding Month 3).

