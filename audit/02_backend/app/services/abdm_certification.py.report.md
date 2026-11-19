# Comprehensive Principal Software Audit & Technical Documentation
# File: `backend/app/services/abdm_certification.py`
# Component: ABDM Sandbox E2E Certification & Regression Test Harness
# Release Version: 1.1.0-RC3 · ABDM / NRCES v4.1 Compliance

---

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/abdm_certification.py` implements an automated end-to-end certification test harness and regression engine verifying conformance against National Health Authority (NHA) ABDM Gateway v0.5 specifications. It automates test execution across Milestone 1 (Verhoeff checksums, Aadhaar OTP lifecycle, 14-digit ABHA minting, PHR handles, HPR registration), Milestone 2 (discovery matching, fuzzy scoring, ambiguity guardrails, care context linking), and Milestone 3 (consent ingestion, Curve25519 key agreements, AES-256-GCM encryption, tamper defense).

### Architectural Role & System Topology
```
           +-----------------------------------------------+
           |     Certification Runner (CLI / Test API)     |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |        AbdmSandboxCertificationService        |
           |             run_certification(...)            |
           +-----------------------------------------------+
                                  |
            +---------------------+---------------------+
            |                     |                     |
            v                     v                     v
+-----------------------+ +--------------------+ +--------------------+
| Milestone 1 Vectors   | | Milestone 2 Vectors| | Milestone 3 Vectors|
| (V-M1-01 to V-M1-05)  | |(V-M2-01 to V-M2-05)| |(V-M3-01 to V-M3-05)|
+-----------------------+ +--------------------+ +--------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |         SandboxCertificationReport            |
           |       (SHA-256 Cryptographic Proof)           |
           +-----------------------------------------------+
```

### Key Import/Export Roster
- **Imports**:
  - `hashlib, base64, logging, re, time, uuid`: Core runtime and crypto digest generation.
  - `CertificationVectorResult, SandboxCertificationReport, ...`: Domain result schemas.
  - Domain service functions from `aadhaar_otp`, `abdm_consent`, `abdm_crypto`, `abdm_discovery`, `abdm_issuance`, `abdm_transfer`.
- **Exports**:
  - `OFFICIAL_VECTOR_CATALOG`: Catalog of 15 official ABDM sandbox test vectors.
  - `AbdmSandboxCertificationService`: Test execution and report generation engine.
  - `abdm_sandbox_certifier`: Singleton service instance.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Vector Catalog Definition**: Formulates 15 official test vectors mapped to NHA specifications spanning M1 (ABHA), M2 (Discovery & Linking), and M3 (Consent & Encrypted Transfer).
2. **Automated Runner (`run_certification`)**: Iterates through requested milestone vectors, records microsecond execution latency, collects assertion counts, compiles pass rates, and seals the final report with an immutable SHA-256 cryptographic certificate proof.
3. **M1 Verifications**: Tests Verhoeff check-digit calculations, Aadhaar OTP simulation sessions, ABHA hyphenated formatting, PHR alias regex compliance, and doctor HPR registration formatting.
4. **M2 Verifications**: Executes Jaro-Winkler phonetic name matching, birth year tolerance scoring, ambiguity guardrail aborts (ABDM Error 1441), and token bindings.
5. **M3 Verifications**: Tests ECDSA signature ingestion, Curve25519 key exchange, dual-nonce XOR entropy extraction, HKDF symmetric key derivation, AES-256-GCM payload encryption, and intentional 1-bit cipher tampering detection.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Synchronous `time.sleep` Stalling Async Event Loops
In line 221:
```python
if mock_network_delay:
    time.sleep(0.015)  # 15ms simulated network hop
```
`run_certification` is defined as a synchronous function (`def run_certification(...)`). When called from an async FastAPI endpoint without offloading to a worker thread via `asyncio.to_thread`, calling `time.sleep` blocks the main asyncio event loop thread for all concurrent users.

### Invariant 2: Synthetic Dummy Assertions in Care Context Linkage
Vectors `V-M2-04` (link init) and `V-M2-05` (link confirm) do not test any actual linkage services:
```python
link_txn = f"link_txn_{uuid.uuid4().hex[:8]}"
assert len(link_txn) > 0
assert len(otp_val) == 6
```
These vectors construct arbitrary strings and assert their length rather than invoking `app.services.abdm_linkage`. This produces synthetic "passed" assertions that mask unverified production code paths.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SVC-CER-F01` | S2 | `[PERF]` | `abdm_certification.py:221` | Synchronous `time.sleep(0.015)` blocks the asyncio event loop thread during execution |
| `BE-SVC-CER-F02` | S2 | `[QUAL]` | `abdm_certification.py:531-566` | Vectors `V-M2-04` and `V-M2-05` use dummy string length assertions instead of testing linkage logic |
| `BE-SVC-CER-F03` | S3 | `[QUAL]` | `abdm_certification.py:352-782` | Bare `assert` statements in test methods are stripped when Python is executed with `-O` flag |
| `BE-SVC-CER-F04` | S3 | `[DOC]` | `abdm_certification.py:770, 793` | Tampered byte index is 5 in execution but reported as index 10 in `requestSummary` |

---

## Layer E: Unapplied Unified Diff Patches for S0–S2 Findings

```diff
--- a/backend/app/services/abdm_certification.py
+++ b/backend/app/services/abdm_certification.py
@@ -10,6 +10,7 @@
 from datetime import datetime, timezone, timedelta
+import asyncio
 import base64
 import hashlib
@@ -218,8 +219,6 @@
         for item in vectors_to_run:
             start_time = time.perf_counter()
-            if mock_network_delay:
-                time.sleep(0.015)  # 15ms simulated network hop
 
             try:
```
