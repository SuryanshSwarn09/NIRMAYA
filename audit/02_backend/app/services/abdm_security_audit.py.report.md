# Technical Audit Report: backend/app/services/abdm_security_audit.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/abdm_security_audit.py` provides an automated security penetration and vulnerability testing suite for NIRMAYA's ABDM implementation. It simulates 12 distinct attack vectors covering SQL injection on discovery, replay attacks on consent webhooks, Curve25519 public key malformations, degraded nonce entropy, AES-256-GCM ciphertext bit-flipping, SHA-256 checksum forgery, brute-force OTP lockout, and IDOR care-context access. The audit revealed that several vector tests rely on Python's `assert` statement, which is completely stripped when Python is run with `-O` (optimized mode), and duration timers are hardcoded to zero, creating risk of false confidence in security defenses.

### Architectural Roster
- **Module Name:** `backend/app/services/abdm_security_audit.py`
- **Primary Responsibility:** Automated execution of ABDM penetration tests and formulation of cryptographic integrity audit reports.
- **Upstream Dependencies:**
  - `cryptography.hazmat.primitives.asymmetric.x25519`
  - `app.core.exceptions.AppException`, `ValidationException`
  - `app.schemas.abdm_security_audit` (`PenetrationAttackCategory`, `PenetrationVectorResult`, etc.)
  - `app.services.abdm_crypto.AbdmCryptoService`
  - `app.services.abdm_transfer.AbdmTransferService`
  - `app.services.aadhaar_otp.aadhaar_session_manager`
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/abdm_security_audit.py`
- **Exported Symbols:**
  - `AbdmSecurityAuditService`
  - `abdm_security_auditor`

```
+-----------------------------------------------------------------------------------+
|                        ABDM Security Penetration Engine                           |
|                                                                                   |
|  [Admin Security Console]                                                         |
|          |                                                                        |
|          v                                                                        |
|  [AbdmSecurityAuditService.run_suite]                                             |
|          |-- SEC-01: SQLi on Discovery Query                                      |
|          |-- SEC-02: Replay Attack on Consent Webhook                             |
|          |-- SEC-03: Malformed Consent Signature Ingestion                        |
|          |-- SEC-04: IDOR Care Context Tampering                                  |
|          |-- SEC-05: Expired Consent Transfer Hijack                              |
|          |-- SEC-06: Forward Secrecy Violation Attack                             |
|          |-- SEC-07: Invalid Nonce Size Injection                                 |
|          |-- SEC-08: Malformed Curve25519 Public Key Injection                    |
|          |-- SEC-09: Dual-Nonce Entropy Degradation Defense                       |
|          |-- SEC-10: AES-256-GCM In-Transit Ciphertext Tamper Defense             |
|          |-- SEC-11: SHA-256 Plaintext Checksum Forgery Defense                  |
|          +-- SEC-12: Brute-Force Rate Limiting & Lockout Defense                  |
|          |                                                                        |
|          v                                                                        |
|  [Compiles Comprehensive PenetrationSuiteSummary (Score / Grade)]                 |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

This module operates as an internal red-team test harness verifying cryptographic and API boundary defenses:

1. **Suite Execution (`run_suite`):** Iterates through 12 dedicated attack vector simulations, timing execution, collecting defense outcomes, and compiling an overall score (e.g., `A+ / 100%`) and audit status.
2. **Cryptographic Integrity Testing (SEC-08 to SEC-11):**
   - **SEC-08:** Injects corrupt or truncated Curve25519 public keys to verify that `AbdmCryptoService.parse_public_key` raises a `ValidationException`.
   - **SEC-09:** Submits a degraded nonce (< 32 bytes) to verify that `AbdmCryptoService.parse_nonce` rejects sub-standard entropy.
   - **SEC-10:** Establishes a valid Diffie-Hellman key agreement, encrypts a clinical payload via AES-256-GCM, flips a single bit in the ciphertext bytes, and verifies that `decrypt_payload` rejects the tampered payload with an `InvalidTag` exception.
   - **SEC-11:** Forges a modified clinical diagnosis while retaining the original record's SHA-256 checksum to verify that checksum validation detects payload alterations.
3. **Authentication & Rate Limit Testing (SEC-12):**
   - **SEC-12:** Initiates an Aadhaar OTP transaction session and submits 3 consecutive incorrect OTPs. It then validates that a 4th attempt is locked out with an `AppException`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Security Standards
- **Zero-Tolerance Tampering:** Bit-flipping in encrypted payloads must always trigger an authentication tag failure in AES-GCM without exposing decrypted data.
- **Strict Key Validation:** X25519 keys must be exactly 32 bytes, and nonces must be exactly 32 bytes of CSPRNG entropy.
- **Fail-Secure Rate Limiting:** Brute-force guessing of OTPs must block after exactly 3 attempts.

### Vulnerabilities & Operational Risks
- **Reliance on `assert` Statements in Production Testing:** Lines 660, 710, 733, and 771 use standard Python `assert` expressions. If the backend is executed with Python bytecode optimization (`python -O` or `PYTHONOPTIMIZE=1`), all `assert` statements are stripped from the bytecode. In this mode, if an attack vector actually succeeds (e.g. lockout fails), the test will still return `passed=True`.
- **Hardcoded Duration Metrics:** In lines 646, 670, 720, 742, and 782, `durationMs=0.0` is hardcoded rather than computing real execution latency.
- **Isolated Unit Mocking vs. Live Boundary Testing:** The tests invoke service methods directly in Python memory rather than dispatching HTTP requests against FastAPI middleware, missing real network and header parsing edge cases.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-SEC-F01` | **S2** | `[SEC]` | `abdm_security_audit.py:660, 710, 733, 771` | Reliance on Python `assert` statements causes tests to falsely report defense success if running under `python -O`. |
| `BE-SVC-SEC-F02` | **S2** | `[QUAL]` | `abdm_security_audit.py:650-785` | Security vectors execute against internal function calls in memory rather than testing live HTTP API endpoints and middleware. |
| `BE-SVC-SEC-F03` | **S3** | `[PERF]` | `abdm_security_audit.py:646, 670, 720, 742` | `durationMs` is hardcoded as `0.0` in multiple test results instead of recording real execution time via `time.perf_counter()`. |
| `BE-SVC-SEC-F04` | **S4** | `[QUAL]` | `abdm_security_audit.py:788` | Singleton `abdm_security_auditor` instantiated eagerly at module import time. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Explicit Exception Validation Replacing Stripped Asserts (`BE-SVC-SEC-F01`)

```diff
--- a/backend/app/services/abdm_security_audit.py
+++ b/backend/app/services/abdm_security_audit.py
@@ -657,7 +657,8 @@ class AbdmSecurityAuditService:
         except ValidationException as ve:
             blocked = True
             caught_err = str(ve)
 
-        assert blocked is True
+        if not blocked:
+            raise AppException("Security vector SEC-09 failed: degraded nonce was not blocked")
 
         return PenetrationVectorResult(
@@ -707,7 +708,8 @@ class AbdmSecurityAuditService:
         except Exception as e:
             blocked = True
             caught_err = str(e)
 
-        assert blocked is True
+        if not blocked:
+            raise AppException("Security vector SEC-10 failed: bit-flipped ciphertext was decrypted without tag failure")
 
         return PenetrationVectorResult(
```
