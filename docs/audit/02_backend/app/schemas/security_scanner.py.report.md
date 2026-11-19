# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/security_scanner.py`
**Audited Path:** `backend/app/schemas/security_scanner.py`  
**Module:** `backend` | **Subsystem:** Static Application Security Testing (SAST) & Connection Pool Telemetry  
**Severity Classification:** MEDIUM RISK (`[QUAL]` / `[SEC]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/security_scanner.py` defines the Pydantic v2 schemas for NIRMAYA's automated Static Application Security Testing (SAST) engine, third-party dependency vulnerability auditor (aligned with Common Vulnerabilities and Exposures / CVEs and CVSS v3.1 scoring), multi-tenant Row-Level Security (RLS) session context parameters, and real-time PostgreSQL database connection pool telemetry. This module structures:
- Security severity tiers (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`) and vulnerability categories (`INSECURE_CRYPTO`, `SQL_INJECTION`, `HARDCODED_SECRET`, `DANGEROUS_CALL`, `INSECURE_DESERIALIZATION`, `PERMISSIVE_CORS`, `DEPENDENCY_VULNERABILITY`).
- AST-level source code security findings (`SASTFinding`) and dependency advisory descriptors (`DependencyVulnerability`).
- On-demand code and dependency scanning requests (`SASTScanRequest`, `DependencyScanRequest`).
- Comprehensive security audit scan reports (`SecurityScanReport`).
- Multi-tenant PostgreSQL session context parameters for Row-Level Security (`TenantContextParams`).
- Real-time connection pool health, lease tracking, and overflow saturation telemetry (`DatabasePoolMetrics`).

#### 2. Key Components & Class Roster
- `SecuritySeverityEnum` & `SecurityCategoryEnum`: CVSS-aligned severity and category taxonomy.
- `SASTFinding`: Discrete static analysis finding detailing rule ID (e.g. `NIRMAYA-SEC-001`), category, severity, source file path, line number, column offset, offending code snippet, risk message, and prescriptive remediation guidance.
- `DependencyVulnerability`: Dependency finding capturing affected package name, installed version, fixed version, CVE ID, CVSS 3.1 score (`ge=0.0, le=10.0`), severity, and advisory title.
- `SASTScanRequest` & `DependencyScanRequest`: Inspection trigger payloads accepting raw Python code snippets, target file paths, or `requirements.txt` manifests.
- `SecurityScanReport`: Aggregated inspection report compiling scan ID, timestamp, target type, evaluated file counts, severity distribution counts (`critical_count`, `high_count`, `medium_count`, `low_count`), findings lists, and scan duration.
- `TenantContextParams`: PostgreSQL session variables injected for multi-tenant isolation (`tenant_id`, `user_id`, `jurisdiction_path`, `role`).
- `DatabasePoolMetrics`: Operational pool telemetry tracking pool size, max overflow, timeout, recycling intervals, idle vs leased connection counts, and percentage utilization.

---

### Layer B: Plain-Language Developer Walkthrough

Building healthcare software requires constant vigilance against security bugs. A developer might accidentally use a weak encryption function, leave an API secret hardcoded in a configuration file, or import an open-source library that has an unpatched security flaw. Additionally, because NIRMAYA runs as a multi-tenant platform where hundreds of hospitals share the same database, the system must enforce strict Row-Level Security (RLS) so that a doctor in Bihar cannot accidentally see patient records from Maharashtra.

`security_scanner.py` provides the data contracts for these automated defensive shields:
1. It defines how the built-in SAST code scanner analyzes source code: if an engineer writes dangerous code, a `SASTFinding` is generated with the exact file path, line number, and a clear recipe on how to fix it.
2. It audits installed dependencies against the national CVE vulnerability database (`DependencyVulnerability`), alerting developers when a package has a known security advisory and recommending the minimum safe version to upgrade to.
3. When database queries run, `TenantContextParams` safely packages the hospital's tenant ID, user ID, and administrative jurisdiction path (`jurisdiction_path`, e.g. `india.27.492`), guaranteeing that PostgreSQL RLS filters records at the database engine level.
4. Finally, `DatabasePoolMetrics` keeps a continuous pulse on the PostgreSQL connection pool to ensure the database never runs out of connections during peak hospital hours.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **CVSS v3.1 Conformance:** `cvss_score` enforces mathematical bounds `ge=0.0, le=10.0`.
- **AST Diagnostic Precision:** `SASTFinding` includes exact line numbers, column offsets, and code snippets for automated IDE and CI/CD linting integration.
- **RLS Boundary Injection:** `TenantContextParams` provides structured parameters for PostgreSQL `SET LOCAL` session variables.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Missing Regex Validation on LGD Jurisdiction Path (`BE-SCH-SCN-F01`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/security_scanner.py:128`
- **Description:** `TenantContextParams.jurisdiction_path` is declared as an unconstrained `str = Field(..., description="LGD hierarchical path string, e.g. india.27.492")`. In PostgreSQL, this string is injected into the session variable `app.current_jurisdiction_path` and cast to the `ltree` data type for territorial RBAC filtering. If a client supplies a string containing invalid characters (e.g. spaces, special punctuation, or SQL metacharacters), PostgreSQL raises a runtime syntax error or RLS check exception.
- **Impact:** Potential runtime SQL syntax errors or RLS authorization bypass during session setup (CWE-20).
- **Remediation:** Enforce `pattern=r"^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$"` on `jurisdiction_path`.

##### Vulnerability 2: Unvalidated CVE Identifier Format (`BE-SCH-SCN-F02`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/security_scanner.py:55`
- **Description:** `DependencyVulnerability.cve_id` lacks standard Common Vulnerabilities and Exposures pattern validation (`pattern=r"^CVE-\d{4}-\d{4,8}$"`). Malformed or non-standard advisory identifiers pass validation into security reports.
- **Impact:** Inconsistent vulnerability reporting.
- **Remediation:** Add standard CVE regex pattern matching.

##### Vulnerability 3: Connection Pool Metrics Lack Non-Negative Bounds (`BE-SCH-SCN-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/security_scanner.py:138-145`
- **Description:** Integer connection metrics (`pool_size`, `max_overflow`, `checked_in_connections`, `checked_out_connections`, `total_connections`, `overflow_connections`) lack `ge=0` bounds.
- **Impact:** Allows negative connection numbers in database pool telemetry.
- **Remediation:** Enforce `ge=0` on all connection count fields.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-SCN-F01` | S2 | `[QUAL]` | `security_scanner.py:128` | `jurisdiction_path` lacks PostgreSQL ltree format regex validation |
| `BE-SCH-SCN-F02` | S3 | `[QUAL]` | `security_scanner.py:55` | `cve_id` lacks standard CVE format regex validation |
| `BE-SCH-SCN-F03` | S3 | `[QUAL]` | `security_scanner.py:138-145` | Database connection pool counters lack `ge=0` non-negative bounds |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/security_scanner.py
+++ b/backend/app/schemas/security_scanner.py
@@ -53,3 +53,4 @@ class DependencyVulnerability(BaseModel):
     installed_version: str = Field(..., description="Currently installed package version")
     fixed_version: Optional[str] = Field(default=None, description="Minimum recommended secure version")
-    cve_id: str = Field(..., description="Common Vulnerabilities and Exposures identifier")
+    cve_id: str = Field(..., pattern=r"^CVE-\d{4}-\d{4,8}$", description="Common Vulnerabilities and Exposures identifier")
     cvss_score: float = Field(..., ge=0.0, le=10.0, description="CVSS 3.1 base metric score")
@@ -126,3 +127,7 @@ class TenantContextParams(BaseModel):
     user_id: str = Field(..., description="Authenticated user UUID executing the query")
-    jurisdiction_path: str = Field(..., description="LGD hierarchical path string, e.g. india.27.492")
+    jurisdiction_path: str = Field(
+        ...,
+        pattern=r"^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$",
+        description="LGD hierarchical path string, e.g. india.27.492",
+    )
     role: Optional[str] = Field(default=None, description="Active user clinical or administrative role")
@@ -137,7 +142,7 @@ class DatabasePoolMetrics(BaseModel):
     engine_dialect: str = Field(..., description="Database dialect, e.g. postgresql or sqlite")
-    pool_size: int = Field(..., description="Configured steady-state connection pool size")
-    max_overflow: int = Field(..., description="Configured maximum connection overflow allowance")
+    pool_size: int = Field(..., ge=0, description="Configured steady-state connection pool size")
+    max_overflow: int = Field(..., ge=0, description="Configured maximum connection overflow allowance")
     pool_timeout: int = Field(..., description="Connection acquisition timeout in seconds")
     pool_recycle: int = Field(..., description="Connection recycling lifetime in seconds")
-    checked_in_connections: int = Field(..., description="Number of idle connections resting in pool")
-    checked_out_connections: int = Field(..., description="Number of connections actively leased")
-    total_connections: int = Field(..., description="Total active pool plus overflow connections")
-    overflow_connections: int = Field(..., description="Number of overflow connections allocated beyond pool_size")
+    checked_in_connections: int = Field(..., ge=0, description="Number of idle connections resting in pool")
+    checked_out_connections: int = Field(..., ge=0, description="Number of connections actively leased")
+    total_connections: int = Field(..., ge=0, description="Total active pool plus overflow connections")
+    overflow_connections: int = Field(..., ge=0, description="Number of overflow connections allocated beyond pool_size")
     utilization_rate_percent: float = Field(
```
