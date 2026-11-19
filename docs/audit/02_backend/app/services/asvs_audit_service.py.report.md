# Technical Audit Report: backend/app/services/asvs_audit_service.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/asvs_audit_service.py` provides an internal compliance self-attestation auditor for the OWASP Application Security Verification Standard (ASVS) v4.0.3 Level 2. It maps platform security mechanisms (Argon2id password hashing, PostgreSQL RLS tenant isolation, Pydantic 2.0 schema typing, AST code scanning, AES-256-GCM AEAD encryption, and SHA-256 Merkle audit ledgers) across 14 ASVS control families. The audit identified that the service is an entirely static attestation scorecard rather than a dynamic audit engine: all 18 included controls are hardcoded with `status="COMPLIANT"`, unconditionally yielding 100% compliance and `"CERTIFIED"` status without probing runtime configuration or live system health.

### Architectural Roster
- **Module Name:** `backend/app/services/asvs_audit_service.py`
- **Primary Responsibility:** Mapping and reporting platform architectural defenses against OWASP ASVS v4.0.3 Level 2 criteria.
- **Upstream Dependencies:**
  - `app.schemas.asvs_fuzzer` (`ASVSComplianceReport`, `ASVSControlFamily`, `ASVSVerificationItem`)
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/asvs_audit.py`
  - System compliance and security monitoring dashboards
- **Exported Symbols:**
  - `ASVSAuditService`
  - `asvs_audit_service`

```
+-----------------------------------------------------------------------------------+
|                        OWASP ASVS v4.0.3 Self-Attestation Auditor                 |
|                                                                                   |
|  [Admin Security Console]                                                         |
|          |                                                                        |
|          v                                                                        |
|  [asvs_audit_service.generate_compliance_report]                                  |
|          |-- 1. Evaluates ASVS_LEVEL2_CONTROLS (18 hardcoded controls)            |
|          |-- 2. Calculates Compliant / Total (Always 18/18 = 100.0%)              |
|          |-- 3. Groups items by ASVSControlFamily                                 |
|          +--> Returns ASVSComplianceReport (Status: CERTIFIED)                    |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

This module serves as a programmatic self-documentation artifact demonstrating architectural alignment with OWASP ASVS Level 2 standards:

1. **Control Family Cataloging (`ASVS_LEVEL2_CONTROLS`):** Defines 18 representative controls mapped across ASVS categories:
   - **V1 Architecture:** Multi-tier architectural boundaries and DPDP Act zero-trust data isolation.
   - **V2 Authentication:** Argon2id key stretching and Aadhaar/Mobile OTP MFA.
   - **V3 Session Management:** Cryptographic JWT tokens with issuer/audience checks.
   - **V4 Access Control:** PostgreSQL Row-Level Security (`SET LOCAL app.current_tenant`).
   - **V5 Input & Output:** Strict Pydantic models, parameterized SQL binding, and XSS sanitization.
   - **V6 Cryptography:** AES-256-GCM AEAD at rest and sequential SHA-256 hash-chain audit ledgers.
   - **V7 Error Logging:** Global exception handlers masking database stack traces.
   - **V8 Data Protection:** Purpose limitation and FHIR R4 de-identification.
   - **V9 Communications:** TLS 1.3, HSTS, and strict security response headers.
   - **V10 Malicious Code:** AST static code analysis.
   - **V11 Business Logic:** Break-The-Glass clinical emergency overrides.
   - **V13 API & Web Services:** HL7 FHIR R4 and ABDM Gateway v0.5 M1/M2/M3 standards.
   - **V14 Configuration:** Token bucket rate limiting and IP jail shields.
2. **Report Compilation (`generate_compliance_report`):** Generates an audit ID, tallies compliant controls, builds a per-family breakdown, and formats an `ASVSComplianceReport`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Compliance Standards
- **OWASP ASVS Level 2 Threshold:** Level 2 applies to applications handling sensitive personal healthcare data and requires verification of deep defense-in-depth controls.
- **Reporting Invariant:** Status must accurately reflect verification outcome: $\ge 95\%$ for `CERTIFIED`, $\ge 80\%$ for `CONDITIONAL`, and $< 80\%$ for `FAILED`.

### Vulnerabilities & Limitations
- **Static Hardcoding Without Runtime Verification:** Every control in `ASVS_LEVEL2_CONTROLS` is initialized with `status="COMPLIANT"`. The service does not dynamically test whether TLS 1.3 is active, whether Argon2id parameters match configuration, or whether database RLS policies are actually enforced.
- **Subset vs. Complete ASVS Specification:** Full OWASP ASVS v4.0.3 Level 2 mandates over 270 individual verification requirements. The 18 controls here represent a high-level summary, which should be explicitly documented to avoid misleading external compliance auditors.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-ASV-F01` | **S2** | `[QUAL]` | `asvs_audit_service.py:23-186, 188-212` | Compliance report is statically hardcoded with all items marked COMPLIANT, giving static 100% certification without dynamic verification. |
| `BE-SVC-ASV-F02` | **S2** | `[DOC]` | `asvs_audit_service.py:23-186` | Curated list of 18 controls covers only a subset of the ~270 requirements in full OWASP ASVS v4.0.3 Level 2. |
| `BE-SVC-ASV-F03` | **S3** | `[QUAL]` | `asvs_audit_service.py:23` | Control status values are immutable in code, preventing integration with CI/CD SAST test pipelines. |
| `BE-SVC-ASV-F04` | **S4** | `[QUAL]` | `asvs_audit_service.py:216` | Global singleton `asvs_audit_service` instantiated at import time. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Explicit Attestation Type Classification (`BE-SVC-ASV-F01`, `BE-SVC-ASV-F02`)

```diff
--- a/backend/app/services/asvs_audit_service.py
+++ b/backend/app/services/asvs_audit_service.py
@@ -204,6 +204,7 @@ class ASVSAuditService:
             asvs_version="4.0.3",
-            target_level="Level 2 (Standard Enterprise Healthcare)",
+            target_level="Level 2 (Representative Curated Architecture Controls - 18 Items)",
             total_controls=total,
             compliant_controls=compliant,
             compliance_percentage=pct,
+            status=f"SELF_ATTESTED_{status_str}",
             family_summaries=family_counts,
```
