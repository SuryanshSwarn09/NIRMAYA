# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/license_audit.py`
**Audited Path:** `backend/app/schemas/license_audit.py`  
**Module:** `backend` | **Subsystem:** Software Bill of Materials (SBOM) & Open-Source License Audit Gate  
**Severity Classification:** MEDIUM RISK (`[QUAL]` / `[SEC]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/license_audit.py` defines the Pydantic schemas for NIRMAYA's automated Software Bill of Materials (SBOM) generation, open-source license compliance gate, and release readiness integrity auditing. Implemented to guarantee zero viral copyleft contamination (e.g. GPL/AGPL) and enforce enterprise legal certifications across Python (PyPI) and Node.js (npm) dependency trees, this module formalizes:
- Normalized license taxonomy (`MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `Python-2.0`, `CC-BY-4.0`, `Other Permissive`, `Copyleft (GPL/AGPL)`).
- Dependency catalog entries and risk scorecards (`DependencyComponentItem`, `LicenseSummaryScorecard`).
- Formal architectural invariant and Service Level Agreement (SLA) verification checks (`SystemIntegrityCheckItem`, `IntegrityCheckStatusEnum`).
- Machine-readable Software Bill of Materials conforming to the international CycloneDX v1.5 standard (`CycloneDXManifest`, `CycloneDXMetadata`, `CycloneDXComponent`).
- Consolidated release readiness scorecards for production promotion gates (`PreReleaseAuditReport`).

#### 2. Key Components & Class Roster
- `LicenseTypeEnum`: Standardized open-source licensing classification separating permissive licenses from copyleft risks.
- `DependencyEcosystemEnum`: Runtime package repositories (`Python (PyPI)`, `Node.js (npm)`).
- `ComplianceStatusEnum`: Legal certification verdicts (`CERTIFIED`, `NON_COMPLIANT`).
- `IntegrityCheckStatusEnum`: Subsystem SLA verification state (`PASSED`, `WARNING`, `FAILED`).
- `DependencyComponentItem`: Granular third-party dependency descriptor detailing name, pinned semantic version, package ecosystem, normalized license, authoritative license URL, copyleft risk flag, and architectural role.
- `LicenseSummaryScorecard`: Aggregated legal metrics tracking total dependency count, permissive proportion percentage, license distribution breakdown, and formal zero-contamination legal sign-off text.
- `SystemIntegrityCheckItem`: Empirical verification result confirming critical system invariants (e.g., PostgreSQL connection pool sizing, cache hit SLAs, cryptographic test coverage).
- `CycloneDXManifest`: Authoritative CycloneDX 1.5 JSON SBOM specification with serial numbers, metadata, tools, and component PURL references.
- `PreReleaseAuditReport`: Production release sign-off gate aggregating license scorecards and subsystem checks into a final verdict (`READY_FOR_PRODUCTION_TAG`).

---

### Layer B: Plain-Language Developer Walkthrough

When developing a national-scale public digital infrastructure platform for healthcare, compliance and software supply-chain security are paramount. If an engineer inadvertently imports a library licensed under a viral copyleft license (such as AGPL-3.0), government and enterprise legal teams might argue that the entire national infrastructure must be open-sourced under the same terms or face copyright infringement lawsuits. Furthermore, modern cybersecurity regulations require systems to maintain an automated Software Bill of Materials (SBOM) so that when a vulnerability (like Log4j) is discovered, operators can instantly identify if any component is affected.

`license_audit.py` provides the data contracts for NIRMAYA's automated compliance gate:
1. Every dependency across both backend and frontend is scanned and categorized into a `DependencyComponentItem`.
2. A `LicenseSummaryScorecard` verifies that 100% of production dependencies use business-friendly permissive licenses (such as MIT, Apache-2.0, or BSD).
3. The system generates an internationally recognized `CycloneDXManifest` (v1.5 standard) complete with Package URLs (PURLs), which can be ingested by government cybersecurity scanners.
4. Before any release candidate is tagged, `PreReleaseAuditReport` confirms that all automated architectural and cryptographic tests pass with zero license violations.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **CycloneDX 1.5 Specification:** Implements the official CycloneDX schema structure (`bomFormat="CycloneDX"`, `specVersion="1.5"`, `serialNumber`, `metadata`, `components`).
- **Bounded Compliance Percentages:** `permissive_percentage` enforces mathematical range bounds `ge=0.0, le=100.0`.
- **Zero-Contamination Signoff:** `legal_signoff_attestation` mandates formal legal attestation text in the audit payload.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Missing Invariant Validation on Total vs Passed Checks (`BE-SCH-LIC-F01`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/license_audit.py:109-111`
- **Description:** In `PreReleaseAuditReport`, fields `total_checks_passed: int`, `total_checks_count: int`, and `all_checks_passed: bool` are parsed without cross-field validation. A buggy report generator could submit `total_checks_passed = 50` while `total_checks_count = 30`, or declare `all_checks_passed = True` even when `total_checks_passed < total_checks_count`.
- **Impact:** Compromises the integrity of the automated release gate sign-off.
- **Remediation:** Add a `@model_validator(mode="after")` enforcing that `total_checks_passed <= total_checks_count` and that `all_checks_passed == (total_checks_passed == total_checks_count)`.

##### Vulnerability 2: Plain String for License URLs (`BE-SCH-LIC-F02`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/license_audit.py:45`
- **Description:** `DependencyComponentItem.license_url` is declared as an unconstrained `str` rather than `HttpUrl` or `AnyHttpUrl`.
- **Impact:** Malformed or broken URLs could pass validation into the generated SBOM.
- **Remediation:** Declare `license_url: HttpUrl`.

##### Vulnerability 3: Missing CycloneDX PURL and Serial Number Format Constraints (`BE-SCH-LIC-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/license_audit.py:81, 95`
- **Description:** `CycloneDXComponent.purl` lacks standard Package URL prefix validation (`pattern=r"^pkg:[a-zA-Z0-9_-]+/.*"`), and `serialNumber` lacks standard UUID URN validation (`pattern=r"^urn:uuid:[0-9a-fA-F-]{36}$"`).
- **Impact:** Generated CycloneDX manifests may be rejected by third-party SBOM ingest engines.
- **Remediation:** Add regex pattern constraints on `purl` and `serialNumber`.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-LIC-F01` | S2 | `[QUAL]` | `license_audit.py:109-111` | Missing validator ensuring `total_checks_passed <= total_checks_count` |
| `BE-SCH-LIC-F02` | S3 | `[QUAL]` | `license_audit.py:45` | `license_url` uses plain string rather than `HttpUrl` |
| `BE-SCH-LIC-F03` | S3 | `[QUAL]` | `license_audit.py:81, 95` | `purl` and `serialNumber` lack standard CycloneDX format regex checks |
| `BE-SCH-LIC-F04` | S3 | `[QUAL]` | `license_audit.py:39, 51, 63, 101` | Missing `ConfigDict(from_attributes=True)` across audit models |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/license_audit.py
+++ b/backend/app/schemas/license_audit.py
@@ -2,5 +2,5 @@
 from datetime import datetime, timezone
 from enum import Enum
 from typing import Any, Dict, List, Optional
-from pydantic import BaseModel, Field
+from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
 
 
@@ -43,3 +43,3 @@ class DependencyComponentItem(BaseModel):
     license: LicenseTypeEnum = Field(..., description="Normalized open-source license")
-    license_url: str = Field(..., description="Link to authoritative license text or registry")
+    license_url: HttpUrl = Field(..., description="Link to authoritative license text or registry")
     copyleft_risk: bool = Field(default=False, description="Flag indicating viral/copyleft licensing risk")
@@ -79,3 +79,8 @@ class CycloneDXComponent(BaseModel):
     licenses: List[Dict[str, Any]]
-    purl: str
+    purl: str = Field(
+        ...,
+        pattern=r"^pkg:[a-zA-Z0-9_\-\.\/]+",
+        description="Package URL conforming to standard specifications",
+    )
 
@@ -93,3 +98,8 @@ class CycloneDXManifest(BaseModel):
     specVersion: str = Field(default="1.5")
-    serialNumber: str
+    serialNumber: str = Field(
+        ...,
+        pattern=r"^urn:uuid:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
+        description="Unique URN UUID serial identifier for this BOM document",
+    )
     version: int = Field(default=1)
@@ -107,4 +117,13 @@ class PreReleaseAuditReport(BaseModel):
     integrity_checks: List[SystemIntegrityCheckItem]
-    total_checks_passed: int
-    total_checks_count: int
+    total_checks_passed: int = Field(..., ge=0)
+    total_checks_count: int = Field(..., ge=0)
     all_checks_passed: bool
+
+    @model_validator(mode="after")
+    def validate_checks_consistency(self) -> "PreReleaseAuditReport":
+        if self.total_checks_passed > self.total_checks_count:
+            raise ValueError("total_checks_passed cannot exceed total_checks_count")
+        if self.all_checks_passed != (self.total_checks_passed == self.total_checks_count):
+            raise ValueError("all_checks_passed boolean flag inconsistent with counts")
+        return self
```
