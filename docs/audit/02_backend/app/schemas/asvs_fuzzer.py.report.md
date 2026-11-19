# Audit Report: backend/app/schemas/asvs_fuzzer.py

**Path:** `backend/app/schemas/asvs_fuzzer.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 149 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation schemas for OWASP Application Security Verification Standard (ASVS) Level 2 compliance evaluation, SQLi/XSS defensive fuzzing benchmarks, and distributed DoS rate-limiting shield telemetry.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `IPJailRecord.ip_address` is defined as a plain string without IP address validation, allowing invalid octets, domain strings, or injected control characters to be recorded into rate-limiting penalty registries.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Healthcare platforms holding electronic medical records must defend against automated injection attacks (SQL injection, Cross-Site Scripting) and high-volume volumetric denial-of-service attempts. To demonstrate compliance with enterprise security standards (OWASP ASVS v4.0.3 Level 2), NIRMAYA incorporates an automated defensive fuzzing engine and a distributed IP penalty box ("IP Jail"). This file structures the test definitions, fuzzing results, compliance scorecards, and rate-limiting shield status reports.

### How it works, step by step
1. `ASVSControlFamily` enumerates the 14 standard OWASP ASVS verification families (`V1_ARCHITECTURE` through `V14_CONFIGURATION`).
2. `ASVSVerificationItem` and `ASVSComplianceReport` model the verification status of individual security controls, calculating overall compliance percentage.
3. `FuzzingAttackType` categorizes adversarial injection vectors (`SQLI_TAUTOLOGY`, `SQLI_UNION`, `XSS_REFLECTED_SCRIPT`, `XSS_SVG_PAYLOAD`, etc.).
4. `FuzzingResultItem` and `FuzzingReport` capture the results of feeding malicious vectors into system parsers, recording whether each payload was blocked or sanitized and assigning a CVSS risk score.
5. `FuzzTestRequest` accepts candidate input strings to test on-demand through the sanitizer engine.
6. `IPJailRecord` tracks malicious host IP addresses placed in temporary isolation, noting infractions, penalty durations, and expiry timestamps.
7. `DoSShieldStatus` summarizes active throttling mode, Redis cluster connectivity, and current active bans.

### Concepts and patterns used
- *OWASP ASVS v4.0.3 Verification:* Categorizing security posture across 14 industry-standard control families.
- *Adversarial Fuzzing Telemetry:* Quantifying input sanitizer effectiveness against known exploit vectors.
- *Defensive Token Bucket & IP Isolation:* Monitoring rate-limit infractions and automated quarantine.

### Key lines to read first
- `asvs_fuzzer.py:11-28`: `ASVSControlFamily` enum.
- `asvs_fuzzer.py:44-64`: `ASVSComplianceReport` summary scorecard.
- `asvs_fuzzer.py:67-78`: `FuzzingAttackType` threat classification.
- `asvs_fuzzer.py:94-110`: `FuzzingReport` effectiveness aggregate model.
- `asvs_fuzzer.py:122-136`: `IPJailRecord` IP isolation tracking.

### How to change it safely
When adding new attack vectors (e.g. LDAP or Command Injection), add corresponding enum entries to `FuzzingAttackType` and ensure `FuzzingResultItem.risk_score` adheres to standard CVSS v3.1 bounds (0.0 to 10.0).

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `enum` (Enum), `typing` (Dict, List, Optional), `pydantic` (BaseModel, ConfigDict, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/asvs_fuzzer_service.py`, `backend/app/api/v1/endpoints/asvs_fuzzer.py`.
- **Public Surface:** Enums `ASVSControlFamily`, `FuzzingAttackType`; Models `ASVSVerificationItem`, `ASVSComplianceReport`, `FuzzingResultItem`, `FuzzingReport`, `FuzzTestRequest`, `IPJailRecord`, `DoSShieldStatus`.

### 2. Security [SEC]
- **Unvalidated IP Address in Ban Registry (`BE-SCH-ASVS-F01`):** In `IPJailRecord.ip_address` (line 125), `ip_address: str` is unconstrained. It should be validated against IPv4/IPv6 syntax (using `ipaddress.ip_address` or regex). Malformed values from spoofed client headers can corrupt Redis key namespaces or database records.
- **Handling of Raw Exploit Payloads (`BE-SCH-ASVS-F03`):** `FuzzingResultItem.payload` (line 84) stores raw malicious script and SQL injection strings. When serialized to frontend administration dashboards, consumer interfaces must escape these strings to prevent secondary reflected XSS within the security console itself.

### 3. Code quality [QUAL]
- **Unconstrained Status Strings (`BE-SCH-ASVS-F02`):** `ASVSVerificationItem.status` (line 37), `ASVSComplianceReport.status` (line 60), `FuzzingReport.status` (line 107), and `DoSShieldStatus.status` (line 147) use raw `str` instead of typed `Literal` or `Enum` types.
- Standard Pydantic v2 `ConfigDict(from_attributes=True)` applied across all models.

### 4. AI-generated-code smells [QUAL]
- None; the schemas provide comprehensive coverage for security compliance verification.

### 5. Performance [PERF]
- The fuzzing report model contains `results: List[FuzzingResultItem]`. Large fuzzing suites (1000+ payloads) will produce substantial payloads; pagination or summary-only views are recommended for large runs.

### 6. Error handling & edge cases
- Bounded float values (`risk_score: ge=0.0, le=10.0`, `compliance_percentage: ge=0.0, le=100.0`) prevent malformed metrics.

### 7. Doc accuracy [DOC]
- Conforms to OWASP ASVS Level 2 guidelines and RFC 5735 IP allocation specs.

### 8. Tests
- Covered by `backend/tests/test_asvs_fuzzer.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-ASVS-F01 | S2 | [SEC] | 125 | Unvalidated IP address format in `IPJailRecord` | `ip_address: str = Field(...)` | Validate using `IPvAnyAddress` or regex |
| BE-SCH-ASVS-F02 | S3 | [QUAL] | 37, 60, 107, 147 | Unconstrained status string fields | Multiple schemas use freeform `status: str` | Use `Literal` or `Enum` for status values |
| BE-SCH-ASVS-F03 | S3 | [QUAL] | 84 | Raw exploit payloads stored unescaped in results | `payload: str = Field(...)` | Document required UI HTML entity escaping |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-ASVS-F01 · Risk: Low · [UNTESTED]
Validate client IP address syntax in `IPJailRecord`:

```diff
--- a/backend/app/schemas/asvs_fuzzer.py
+++ b/backend/app/schemas/asvs_fuzzer.py
@@ -6,4 +6,5 @@
 from enum import Enum
 from typing import Dict, List, Optional
-from pydantic import BaseModel, ConfigDict, Field
+from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress
 
@@ -124,3 +125,3 @@ class IPJailRecord(BaseModel):
 
-    ip_address: str = Field(..., description="Client IP address subject to jail penalty")
+    ip_address: IPvAnyAddress = Field(..., description="Client IP address subject to jail penalty")
     jailed_at: datetime = Field(
