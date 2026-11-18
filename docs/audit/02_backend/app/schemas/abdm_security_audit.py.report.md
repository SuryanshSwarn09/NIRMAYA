# Audit Report: backend/app/schemas/abdm_security_audit.py

**Path:** `backend/app/schemas/abdm_security_audit.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 148 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation models for the automated ABDM security penetration testing, consent lifecycle hardening, and compliance verification engine.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `SecurityPenetrationReport.executedAt` is defined as a plain `str` rather than a validated `datetime` object, departing from codebase-wide UTC timestamp conventions and risking malformed timestamp values in audit reports.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Healthcare systems connected to the ABDM network handle sensitive medical data under strict regulatory mandates (DPDP Act 2023, NHA Gateway v0.5 Security Guidelines). To ensure compliance and verify resistance against attack vectors (gateway replays, consent circumvention, scope escalation, crypto tampering, brute force), NIRMAYA includes an automated security penetration testing suite. This file models the test catalog, execution results, domain summaries, and cryptographic report attestations.

### How it works, step by step
1. `PenetrationAttackCategory` enumerates the 5 tested threat vectors: `GATEWAY_REPLAY`, `CONSENT_LIFECYCLE`, `SCOPE_ESCALATION`, `CRYPTOGRAPHIC_INTEGRITY`, and `RATE_LIMIT_BRUTE_FORCE`.
2. `VulnerabilitySeverity` and `DefenseOutcome` categorize vulnerability findings (`BLOCKED_AS_EXPECTED` vs `VULNERABILITY_DETECTED`).
3. `PenetrationVectorItem` catalogues attack definitions, test objectives, and regulatory citations.
4. `PenetrationVectorResult` records granular execution results, elapsed duration, defense outcome, and forensic audit payloads.
5. `SecurityCategorySummary` aggregates defense rates and vulnerability counts per attack category.
6. `SecurityPenetrationReport` packages the full audit dossier, computing an overall defense rate and sealing the results with a SHA-256 cryptographic proof (`securityCertificateProof`).

### Concepts and patterns used
- *String Enum Categorization:* Subclassing `str, Enum` for clean JSON serialization and strict enum membership.
- *Cryptographically Sealed Audit Reports:* Generating a verifiable SHA-256 digest over audit results for non-repudiation.
- *Granular Forensic Telemetry:* Storing test payloads and server defenses in `auditDetails: Dict[str, Any]`.

### Key lines to read first
- `abdm_security_audit.py:15-23`: `PenetrationAttackCategory` enum.
- `abdm_security_audit.py:55-79`: `PenetrationVectorResult` execution result model.
- `abdm_security_audit.py:81-91`: `SecurityCategorySummary` domain metrics.
- `abdm_security_audit.py:93-119`: `SecurityPenetrationReport` sealed report model.
- `abdm_security_audit.py:121-139`: `RunSecurityAuditRequest` execution trigger.

### How to change it safely
When adding new penetration test categories or vectors, update `PenetrationAttackCategory` and ensure all test results set `severity: VulnerabilitySeverity` appropriately.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `enum` (Enum), `typing` (Any, Dict, List, Optional), `pydantic` (BaseModel, Field, ConfigDict).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/abdm_security_audit_service.py`, `backend/app/api/v1/endpoints/abdm_security_audit.py`.
- **Public Surface:** 3 Enums (`PenetrationAttackCategory`, `VulnerabilitySeverity`, `DefenseOutcome`), 6 Pydantic models (`PenetrationVectorItem`, `PenetrationVectorResult`, `SecurityCategorySummary`, `SecurityPenetrationReport`, `RunSecurityAuditRequest`, `SecurityVectorsResponse`).

### 2. Security [SEC]
- **Cryptographic Attestation Proof:** `SecurityPenetrationReport.securityCertificateProof` (line 114-116) enforces inclusion of a SHA-256 digest sealing the report, preventing post-execution tampering.
- **Forensic Detail Segregation:** `PenetrationVectorResult.auditDetails` captures low-level request/response telemetry for compliance review.

### 3. Code quality [QUAL]
- **String Type for Execution Timestamp (`BE-SEC-AUD-F01`):** `SecurityPenetrationReport.executedAt` (line 100) is typed as `str` instead of `datetime`. Other schemas use `datetime` with `timezone.utc`. Using raw string invites unvalidated date strings.
- **Unconstrained Security Status (`BE-SEC-AUD-F02`):** `SecurityPenetrationReport.securityStatus` (line 101) uses raw `str` instead of a typed Enum or `Literal["SECURE_CONFORMING", "VULNERABILITIES_DETECTED"]`.

### 4. AI-generated-code smells [QUAL]
- Hardcoded test facility ID `"IN0410000123"` in default request payload (`BE-SEC-AUD-F03`).

### 5. Performance [PERF]
- Lightweight schema; summary calculations are precomputed by the service layer.

### 6. Error handling & edge cases
- `PenetrationVectorResult.errorDetail` gracefully captures unexpected runtime crashes or timeouts without breaking report compilation.

### 7. Doc accuracy [DOC]
- Aligns with DPDP Act 2023 consent lifecycle and NHA ABDM Gateway security guidelines.

### 8. Tests
- Covered by `backend/tests/test_abdm_security_audit.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SEC-AUD-F01 | S2 | [QUAL] | 100 | Execution timestamp typed as raw string | `executedAt: str = Field(...)` | Use `datetime` with UTC factory |
| BE-SEC-AUD-F02 | S3 | [QUAL] | 101 | Unconstrained security status string | `securityStatus: str = Field(...)` | Use `Literal["SECURE_CONFORMING", "VULNERABILITIES_DETECTED"]` |
| BE-SEC-AUD-F03 | S4 | [QUAL] | 128 | Hardcoded mock facility ID default | `default="IN0410000123"` | Move mock facility ID to test fixtures |

---

## Suggested Patches (NOT Applied)

### Patch BE-SEC-AUD-F01 · Risk: Low · [UNTESTED]
Use standard `datetime` for execution timestamp in audit report:

```diff
--- a/backend/app/schemas/abdm_security_audit.py
+++ b/backend/app/schemas/abdm_security_audit.py
@@ -8,6 +8,7 @@ Conforms to:
 - NIST SP 800-38D (AES-256-GCM AEAD Tag Integrity)
 """
 
+from datetime import datetime, timezone
 from enum import Enum
 from typing import Any, Dict, List, Optional
 from pydantic import BaseModel, Field, ConfigDict
@@ -97,7 +98,10 @@ class SecurityPenetrationReport(BaseModel):
     facilityId: str = Field(description="Target ABDM HIP/HIU Facility ID")
     facilityName: str = Field(description="Target facility organization name")
     environment: str = Field(default="sbx.abdm.gov.in", description="Execution target environment")
-    executedAt: str = Field(description="ISO 8601 UTC timestamp of audit execution")
+    executedAt: datetime = Field(
+        default_factory=lambda: datetime.now(timezone.utc),
+        description="UTC timestamp of audit execution",
+    )
     securityStatus: str = Field(
         description="Audit outcome: SECURE_CONFORMING | VULNERABILITIES_DETECTED"
     )
