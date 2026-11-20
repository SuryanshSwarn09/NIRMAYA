# Principal Software Engineering Audit: backend/app/services/security_scanner.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/security_scanner.py` provides an in-process Static Application Security Testing (SAST) scanner built on Python's native `ast` (Abstract Syntax Tree) module. It inspects source code snippets, standalone files, and directory trees for 5 security rule categories: insecure cryptography (MD5/SHA1), SQL injection in dynamic database calls, hardcoded secrets/API keys, dangerous execution calls (`eval`, `exec`, `subprocess(shell=True)`, `os.system`), and unsafe deserialization (`pickle`, unvalidated `yaml.load`). The scanner operates synchronously in memory with zero external binary dependencies. Critical security and reliability limitations include arbitrary path traversal risks when scanning unconstrained filesystem paths, lack of taint tracking for SQL injection across multi-variable ORM calls, and synchronous filesystem traversals (`os.walk`) that can block the FastAPI async event loop during directory scans.

### System Topology & Architectural Invariants
```
                  +-------------------------------------------------+
                  |      NIRMAYA Security Administration API        |
                  |     (app.api.v1.endpoints.security_scanner)     |
                  +-----------------------+-------------------------+
                                          |
                                          v
                  +-------------------------------------------------+
                  |   SecurityScannerService (security_scanner.py)  |
                  |  - scan_snippet(source_code)                    |
                  |  - scan_file(file_path)                         |
                  |  - scan_directory(directory_path, max_files)    |
                  +-----------------------+-------------------------+
                                          |
                                          v
                  +-------------------------------------------------+
                  |           SASTASTVisitor(ast.NodeVisitor)       |
                  |                                                 |
                  |  [visit_Call]                                   |
                  |   ├─ SEC-001: hashlib.md5/sha1                  |
                  |   ├─ SEC-002: conn.execute(f"...", "%", .format)|
                  |   ├─ SEC-004: eval, exec, subprocess(shell=True)|
                  |   └─ SEC-005: pickle.load, yaml.load            |
                  |                                                 |
                  |  [visit_Assign]                                 |
                  |   └─ SEC-003: SECRET/API_KEY string literals    |
                  +-----------------------+-------------------------+
                                          |
                                          v
                  +-------------------------------------------------+
                  |         Structured SecurityScanReport           |
                  |  (Findings, Severities, Timings, Status)        |
                  +-------------------------------------------------+
```

### Import / Export Surface Map
- **Upstream Dependencies:**
  - `ast`: Python native syntax tree parser and visitor.
  - `os`, `re`, `time`, `uuid`: Path manipulation, regex matching, timing metrics, scan ID generation.
  - `typing.List`, `typing.Optional`, `typing.Tuple`, `typing.Set`: Type hints.
  - `datetime.datetime`, `datetime.timezone`: Timestamp generation.
  - `app.schemas.security_scanner`: `SASTFinding`, `SecurityCategoryEnum`, `SecurityScanReport`, `SecuritySeverityEnum`.
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/security_scanner.py`: Security administration endpoints for automated code hygiene checks and CI/CD pipelines.
- **Exported Interface:**
  - `SASTASTVisitor`: AST visitor parsing syntax nodes for security anti-patterns.
  - `SecurityScannerService`: Orchestration service for snippet, file, and directory scanning.
  - `security_scanner_service`: Global singleton instance.

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/services/security_scanner.py` acts as NIRMAYA's built-in static security auditor. It operates without external CLI dependencies (such as Bandit, Semgrep, or SonarQube), making it suitable for deployment in air-gapped Primary Health Centre (PHC) appliances and restricted Alpine containers.

The scanning pipeline is driven by `SASTASTVisitor`, which subclasses Python's standard `ast.NodeVisitor`:
1. **Function Call Inspection (`visit_Call`)**: Every call node in the Python AST is examined. If the function is `eval`, `exec`, or `__import__`, an immediate critical finding (`NIRMAYA-SEC-004`) is flagged. If the call target is `execute` or `executemany`, `_check_sql_injection` evaluates whether the first argument is an f-string (`ast.JoinedStr`), modulo binary operator (`ast.Mod`), or `str.format()` call (`NIRMAYA-SEC-002`). If the call targets module functions (like `hashlib.md5`, `subprocess.Popen(shell=True)`, `os.system`, `pickle.loads`, or unvalidated `yaml.load`), matching findings are appended to `self.findings`.
2. **Variable Assignment Inspection (`visit_Assign`)**: Target identifiers in variable assignments are checked against `SECRET_VAR_PATTERN` (`SECRET`, `PASSWORD`, `API_KEY`, `AUTH_TOKEN`, etc.). If a match is detected and the assigned value is a string literal of length >= 12 that does not match common placeholder tokens, a high-severity `NIRMAYA-SEC-003` finding is logged.

The `SecurityScannerService` wraps the visitor with three public entrypoints: `scan_snippet` (for raw code buffers), `scan_file` (for single on-disk scripts), and `scan_directory` (which traverses directory trees up to `max_files=250` while ignoring `.git`, `node_modules`, and `.venv`). All findings are aggregated into a `SecurityScanReport` with execution duration and severity tallies.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Arbitrary Filesystem Traversal & Path Invalidation
In `scan_file` (lines 331-380) and `scan_directory` (lines 381-421), `file_path` and `directory_path` are passed directly from callers without canonicalizing paths (`os.path.realpath`) or verifying that the paths reside within an authorized workspace root (`os.path.commonpath`). An authenticated administrator or malicious payload could specify paths such as `/etc/` or `../../../../` to traverse and read arbitrary Python source files on the host filesystem.

### Invariant 2: Surface-Level Pattern Matching Without Taint Tracking
In `_check_sql_injection` (lines 189-243), the scanner only inspects `ast.JoinedStr`, `ast.BinOp(ast.Mod)`, and `ast.Call(format)` passed *directly* as the first argument to `execute()` or `executemany()`. If an application builds a dynamic SQL string in an intermediate variable:
```python
query = f"SELECT * FROM patients WHERE id = '{patient_id}'"
db.execute(text(query))  # or db.execute(query)
```
The first argument to `execute` is an `ast.Name` or `ast.Call(text)`. The scanner fails to detect this critical SQL injection because it lacks data-flow taint tracking and symbol resolution.

### Invariant 3: Blocking Filesystem I/O in Async Loop
In `scan_directory` (lines 381-421), directory traversal uses blocking synchronous calls (`os.walk`, `open().read()`). When invoked from an async FastAPI endpoint, scanning large codebases with dozens of files blocks the Python asyncio event loop, delaying WebSocket broadcasts and incoming patient requests.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SVC-SCN-F01` | **S1** | `[SEC]` | `security_scanner.py:331-421` | Arbitrary path traversal in `scan_file` and `scan_directory` allows scanning host filesystem directories outside workspace boundaries. |
| `BE-SVC-SCN-F02` | **S1** | `[SEC]` | `security_scanner.py:189-243` | SQL injection detection lacks taint tracking; only matches immediate argument AST structures, missing intermediate variable interpolation. |
| `BE-SVC-SCN-F03` | **S2** | `[PERF]` | `security_scanner.py:381-421` | Synchronous `os.walk` and blocking file I/O in `scan_directory` blocks the async event loop during large codebase scans. |
| `BE-SVC-SCN-F04` | **S2** | `[SEC]` | `security_scanner.py:28-31` | Secret regex `SECRET_VAR_PATTERN` misses lower-case/mixed-case variable names or subscript dictionary assignments (`config['api_key'] = ...`). |
| `BE-SVC-SCN-F05` | **S3** | `[QUAL]` | `security_scanner.py:385` | Hardcoded `max_files: int = 250` truncates scanning on large codebases without raising an alert or pagination token. |
| `BE-SVC-SCN-F06` | **S4** | `[DOC]` | `security_scanner.py:69-83` | SAST findings lack CWE/OWASP Top 10 cross-references (e.g., CWE-89 for SQLi, CWE-798 for hardcoded secrets, CWE-327 for broken crypto). |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-SCN-F01`: Workspace Path Confinement & Traversal Shield
```diff
--- a/backend/app/services/security_scanner.py
+++ b/backend/app/services/security_scanner.py
@@ -337,6 +337,13 @@
         start_time = time.perf_counter()
         findings: List[SASTFinding] = []
 
+        # Enforce canonical path verification to prevent path traversal outside project root
+        real_path = os.path.realpath(file_path)
+        workspace_root = os.path.realpath(os.getcwd())
+        if not real_path.startswith(workspace_root):
+            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
+            return self._build_report(target_type="file", files_scanned=0, findings=[], duration_ms=duration_ms, status="ACCESS_DENIED")
+
         if not os.path.isfile(file_path):
             duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
             return self._build_report(
```
