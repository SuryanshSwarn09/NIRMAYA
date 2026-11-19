# Codebase Technical Audit Report: `backend/app/services/license_audit_service.py`

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`license_audit_service.py` functions as NIRMAYA's pre-release Software Bill of Materials (SBOM) generator, license compliance auditing engine, and 16-point architectural invariant integrity scorecard. It inspects and catalogs open-source dependencies across Python (PyPI) and Node.js (npm) ecosystems, ensures 100% adherence to permissive licenses (MIT, Apache-2.0, BSD, ISC), emits NTIA-compliant CycloneDX 1.5 JSON manifests, and verifies production readiness gates prior to sovereign Digital Public Infrastructure (DPI) deployment.

### System Topology & SBOM Architecture
```
   [ NIRMAYA Dependencies ]
   - Python PyPI (20 packages)
   - Node.js npm (9 packages)
                |
                v
  +---------------------------------------+
  |         LicenseAuditService           |
  +---------------------------------------+
  | - Dependency Component Catalog        |
  | - Copyleft Risk Evaluator (GPL Block) |
  | - CycloneDX 1.5 JSON SBOM Exporter    |
  | - 16 System Invariant Telemetry       |
  +---------------------------------------+
        |                     |
        v                     v
  [ License Scorecard ]  [ CycloneDX SBOM ]
  (100% Permissive)      (PURL Standard)
```

### Module Metadata & Imports/Exports
- **Module Path:** `backend/app/services/license_audit_service.py`
- **Component Classification:** Software Supply Chain Security & Pre-Release Compliance
- **Lines of Code:** 587 LOC
- **Imports:** `uuid`, `datetime`, `typing`, `app.schemas.license_audit.*`
- **Primary Export:** `license_audit_service` (Global Singleton Instance)

---

## Layer B: Plain-Language Developer Walkthrough

The service provides automated legal and architectural validation for release engineers:
1. **Dependency Cataloging (`_init_dependency_catalog`)**: Maintains an annotated registry of 29 core packages across backend (FastAPI, SQLModel, asyncpg, cryptography, passlib, argon2-cffi, fhir.resources, orjson) and frontend (Next.js, React, Tailwind CSS, Lucide icons, clsx). Each record captures version, ecosystem, license type, upstream license URL, direct vs. indirect status, and clinical architectural purpose.
2. **License Compliance Scorecard (`get_license_scorecard`)**: Aggregates dependencies by license category, calculates the permissive percentage, and asserts that zero copyleft (GPL, AGPL) components exist in the production runtime. If compliant, it generates a legal sign-off attestation under DPDP Act 2023 and ABDM standards.
3. **CycloneDX 1.5 JSON SBOM Generation (`generate_cyclonedx_sbom`)**: Generates an industry-standard SBOM adhering to NTIA minimum requirements, assigning each component a Package URL (`pkg:pypi/...` or `pkg:npm/...`), license identifier, and application metadata.
4. **Architectural Integrity Scorecard (`_init_system_integrity_checks` & `get_pre_release_audit_report`)**: Tracks 16 critical production invariants (connection pool acquisition latency P99 < 5ms, Redlock zero double-booking, FHIR serialization P99 < 10ms, ABDM Curve25519 ECDH P99 < 4ms, WebSocket 1,000-subscriber fanout P99 < 15ms, Verhoeff checksum validation). If all checks pass and licenses are certified, it outputs `release_readiness="READY_FOR_PRODUCTION_TAG"`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Sovereign DPI Copyleft-Free Mandate
To ensure that Indian national healthcare software can be deployed, scaled, and integrated across central and state government infrastructures without intellectual property encumbrances or copyleft viral license triggers, NIRMAYA strictly enforces:
$$\text{CopyleftCount} = 0 \quad \implies \quad \text{ComplianceStatus} = \text{CERTIFIED}$$
Any detected GPL or AGPL dependency forces status to `NON_COMPLIANT`, gating production build pipelines.

### Invariant 2: NTIA Minimum Elements for SBOM
The CycloneDX output conforms to the United States NTIA and Indian CERT-In guidelines for software transparency: Supplier Name, Component Name, Version String, Other Unique Identifiers (PURL), Relationship Architecture, and License Metadata.

### Invariant 3: P99 Latency & Concurrency Invariants
The 16 integrity checks formalize quantitative SLAs across database connection pooling, distributed locking, cryptographic key exchanges, and real-time streaming, defining the operational baseline for high-throughput public hospital environments.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
|---|---|---|---|---|
| `BE-SVC-LIC-F01` | **S1** | `[SEC]` | `backend/app/services/license_audit_service.py:27-310` | Static Hardcoded Dependency Catalog Completely Disconnected from `pyproject.toml`, `poetry.lock`, and `package.json`. The catalog only lists 29 dependencies with static version numbers (e.g. `fastapi==0.115.0`, `next==15.5.25`), ignoring transitive dependencies and newly added libraries, generating a synthetic SBOM that does not reflect actual installed software packages (false sense of compliance). |
| `BE-SVC-LIC-F02` | **S1** | `[SEC]` | `backend/app/services/license_audit_service.py:315-510` | 16 Pre-Release System Integrity Checks are Hardcoded Static Strings with No Live Benchmark or Telemetry Execution. Invariants like "Zero double-booking across 50 concurrent appointment booking requests" or "P99 < 2.5 ms" return hardcoded static strings ("P99 = 2.18 ms") without performing real health tests, masking regressions. |
| `BE-SVC-LIC-F03` | **S2** | `[QUAL]` | `backend/app/services/license_audit_service.py:535-555` | CycloneDX 1.5 JSON Generator Lacks Cryptographic Component Hashes (SHA-256) and Vulnerability Assessment Data. NTIA minimum elements for SBOM specify package integrity hashes. |
| `BE-SVC-LIC-F04` | **S2** | `[QUAL]` | `backend/app/services/license_audit_service.py:512-534` | Copyleft License Evaluation is Binary on Hardcoded Catalog Flag (`d.copyleft_risk`) without SPDX Expression Parser. Cannot evaluate dual-licensed, AGPL-linked, or MPL-2.0 conditionally permitted packages. |
| `BE-SVC-LIC-F05` | **S3** | `[DOC]` | `backend/app/services/license_audit_service.py:560-580` | Static Version Tagging ("v1.0.0-rc1") Out of Sync with Git SemVer Tagging. |
| `BE-SVC-LIC-F06` | **S4** | `[DOC]` | `backend/app/services/license_audit_service.py:20-25` | Missing Architectural Documentation for CI/CD Pipeline Integration (e.g., GitHub Actions cyclonedx-cli, Syft, or Trivy). |

---

## Layer E: Unapplied Unified Diff Patches

### Patch 1: Add Dynamic SemVer Reading from Git/Environment (`BE-SVC-LIC-F05`)
```diff
--- a/backend/app/services/license_audit_service.py
+++ b/backend/app/services/license_audit_service.py
@@ -1,4 +1,5 @@
 import uuid
+import os
 from datetime import datetime, timezone
 from typing import Any, Dict, List, Optional
@@ -570,3 +571,3 @@ class LicenseAuditService:
         return PreReleaseAuditReport(
             project_name="NIRMAYA",
-            release_candidate="v1.0.0-rc1",
+            release_candidate=os.getenv("NIRMAYA_RELEASE_TAG", "v1.1.0"),
             generated_at=datetime.now(timezone.utc),
```

### Patch 2: Add Component SHA-256 Hash Placeholders in CycloneDX Manifest (`BE-SVC-LIC-F03`)
```diff
--- a/backend/app/services/license_audit_service.py
+++ b/backend/app/services/license_audit_service.py
@@ -548,4 +548,5 @@ class LicenseAuditService:
                     description=d.description,
                     licenses=[{"license": {"id": d.license.value, "url": d.license_url}}],
                     purl=purl,
+                    hashes=[{"alg": "SHA-256", "content": "UNVERIFIED_SOURCE_HASH"}],
                 )
```
