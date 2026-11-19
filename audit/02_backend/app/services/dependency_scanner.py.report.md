# Codebase Audit Report: `backend/app/services/dependency_scanner.py`

**Audit Target**: `backend/app/services/dependency_scanner.py`  
**Subsystem**: Backend - Automated Dependency Vulnerability Scanner (`backend/app/services/`)  
**File Lines**: 254 LOC  
**Severity Breakdown**: S0: 0 | S1: 1 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `dependency_scanner.py` module evaluates pinned dependencies in `requirements.txt` or active runtime Python virtual environments against known CVE advisories, calculates CVSS scores, and generates remediation guidance.

```
[ Developer / CI/CD Security Audit ]
                 │
                 ▼
   [ dependency_scanner.py ]
   ├── 1. Requirements File Parsing (regex-based)
   ├── 2. Active Virtualenv Package Enumeration (importlib.metadata)
   ├── 3. Curated Advisory Catalog (10 Curated Vulnerabilities)
   ├── 4. Semantic Version Boundary Evaluation (packaging.version)
   └── 5. Aggregated SecurityScanReport Generation
                 │
                 ▼
   [ SecurityScanReport: PASSED / WARNING / FAILED ]
```

### Import / Export Roster
- **Imports**: `importlib.metadata`, `re`, `time`, `uuid`, `datetime`, `typing`, `packaging.version`, `app.schemas.security_scanner`.
- **Exports**: `DependencyScannerService`, `dependency_scanner_service`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Advisory Registry**: Contains a curated catalog of common CVEs spanning cryptography, pydantic, aiohttp, urllib3, jinja2, sqlparse, requests, and rsa.
2. **Requirements Parsing**: `parse_requirements_text()` scans `requirements.txt` using a regex pattern, mapping package names to pinned versions.
3. **Environment Audit**: `scan_installed_environment()` queries `importlib.metadata.distributions()` to detect the live versions of installed Python packages.
4. **Advisory Matching**: Compares installed package versions against `vulnerable_below` thresholds via PEP 440 version parsing.
5. **Report Generation**: Aggregates findings by severity (Critical, High, Medium, Low) and marks status as `PASSED`, `WARNING`, or `FAILED`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Incomplete Curated CVE Database Creating False Sense of Security
`ADVISORY_DATABASE` (lines 26–127) is a static, hardcoded list containing only 10 CVE entries. Real-world supply-chain security scanners (such as `pip-audit`, OSV, Snyk, or Trivy) query live, continuously updated national vulnerability databases (e.g., PyPI Advisory DB, GitHub Security Advisories, NVD). Because NIRMAYA depends on dozens of packages (FastAPI, Starlette, SQLAlchemy, psycopg2, uvicorn, alembic, etc.), any critical CVE in an unlisted package will be completely ignored, causing the scanner to report a false `PASSED` status.

### 2. Fragile Requirements Parsing Regex
The parser regex `r"^([a-zA-Z0-9_\-\.]+)\s*(?:==|>=|<=|~=)\s*([0-9a-zA-Z\.\-]+)"` fails on common standard pip constructs:
- Environment markers (e.g. `psycopg2-binary==2.9.9; sys_platform != 'win32'`).
- Multiple version constraints (e.g. `pydantic>=2.7.0,<3.0.0`).
- Direct git/URL dependencies and hash verification pins (`--hash=sha256:...`).

### 3. Performance & Scaling
Currently, each installed package iterates linearly over all advisories. While manageable for 10 entries, scaling the catalog will require a hash table keyed by normalized package name.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-DEP-F01` | **S1** | `[SEC]` | `backend/app/services/dependency_scanner.py:26-127` | Advisory catalog is a hardcoded static list of only 10 CVEs with no OSV/PyPI API integration, producing false negative "PASSED" reports for vulnerable dependencies. |
| `BE-SVC-DEP-F02` | **S2** | `[QUAL]` | `backend/app/services/dependency_scanner.py:132-146` | Requirements parser regex does not support environment markers, multi-range bounds, or wheel hashes. |
| `BE-SVC-DEP-F03` | **S3** | `[PERF]` | `backend/app/services/dependency_scanner.py:186-205` | Linear search over advisory list on every package evaluation instead of index lookup by package name. |
| `BE-SVC-DEP-F04` | **S4** | `[DOC]` | `backend/app/services/dependency_scanner.py:1-25` | Missing documentation detailing automated CI/CD security gate thresholds and exit code conventions. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-DEP-F01` / `BE-SVC-DEP-F02`: Indexed Package Lookup & Resilient Requirements Tokenization

```diff
--- a/backend/app/services/dependency_scanner.py
+++ b/backend/app/services/dependency_scanner.py
@@ -131,8 +131,10 @@ class DependencyScannerService:
         """Parse raw requirements.txt text into a dictionary of package_name -> pinned_version."""
         packages: Dict[str, str] = {}
-        line_pattern = re.compile(r"^([a-zA-Z0-9_\-\.]+)\s*(?:==|>=|<=|~=)\s*([0-9a-zA-Z\.\-]+)")
+        # Clean comments and environment markers
         for line in content.splitlines():
-            clean_line = line.strip()
+            clean_line = line.split("#")[0].split(";")[0].strip()
             if not clean_line or clean_line.startswith("#") or clean_line.startswith("-"):
                 continue
+            line_pattern = re.compile(r"^([a-zA-Z0-9_\-\.]+)\s*(?:==|>=|<=|~=)\s*([0-9a-zA-Z\.\-]+)")
```
