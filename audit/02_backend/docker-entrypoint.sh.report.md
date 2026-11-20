# Principal Software Engineering Audit: backend/docker-entrypoint.sh

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/docker-entrypoint.sh` is the POSIX container lifecycle bootstrap script executed during startup of the NIRMAYA backend container image. It is responsible for logging process credentials (UID/GID), verifying execution within an unprivileged non-root context according to CIS Docker Benchmark 4.1, conditionally running automated database migrations via the Alembic CLI (`RUN_MIGRATIONS=true`), calculating worker concurrency, and replacing the PID 1 shell process with the target server command via `exec "$@"`. Critical operational flaws include swallowing database migration failures and continuing startup, which leads to silent runtime data corruption and unhandled 500 errors when application models query unmigrated schema columns, as well as calculating a `WORKERS` variable that is never forwarded to the downstream server execution command.

### System Topology & Architectural Invariants
```
             +-------------------------------------------------------+
             |         Container Runtime (Docker / Kubernetes)       |
             +---------------------------+---------------------------+
                                         |
                                         v
             +-------------------------------------------------------+
             |      docker-entrypoint.sh (PID 1 Bootstrap Shell)     |
             |                                                       |
             |  1. UID / GID Inspection & CIS Docker 4.1 Root Check  |
             |  2. RUN_MIGRATIONS Evaluation:                        |
             |     ├─ alembic upgrade head                           |
             |     └─ Fallback warning handler (Non-fatal)           |
             |  3. WEB_CONCURRENCY Calculation                       |
             +---------------------------+---------------------------+
                                         |
                                         | exec "$@" (Process replacement)
                                         v
             +-------------------------------------------------------+
             |     Application Server (uvicorn app.main:app)         |
             +-------------------------------------------------------+
```

### Import / Export Surface Map
- **Upstream Dependencies:**
  - Standard POSIX Shell (`/bin/sh`).
  - Core utilities: `id`, `echo`, `command`.
  - Database CLI: `alembic` (optional, detected via path lookup).
  - Environment Variables: `RUN_MIGRATIONS`, `WEB_CONCURRENCY`.
- **Downstream Consumers:**
  - `backend/Dockerfile`: Configured as container `ENTRYPOINT ["docker-entrypoint.sh"]`.
  - Production container orchestrators (Kubernetes deployments, Docker Compose).
- **Exported Interface:**
  - Container bootstrap lifecycle and signal-preserving execution of CMD parameters (`$@`).

---

## Layer B: Plain-Language Developer Walkthrough

`backend/docker-entrypoint.sh` runs inside the container immediately upon startup before the Python interpreter starts:
1. **Shell Configuration (`set -e`)**: The script instructs the shell to exit immediately if any simple command fails unexpectedly, though this is overridden during migration execution.
2. **Identity Logging & Non-Root Warning (Lines 7-13)**: Outputs the effective user ID and group ID. If `$(id -u)` equals 0 (root), it prints a warning noting that running as root violates CIS Docker Benchmark 4.1. However, it does not abort, allowing root containers to proceed.
3. **Database Migration Execution (Lines 15-25)**: Evaluates `${RUN_MIGRATIONS:-true}`. If enabled and the `alembic` CLI is detected on `PATH`, it executes `alembic upgrade head`. If Alembic exits with an error (e.g., unreachable database, lock timeout, bad migration script), an error handler catches the failure, logs a warning message, and permits the container to continue.
4. **Concurrency Metric (Lines 27-29)**: Assigns `WORKERS="${WEB_CONCURRENCY:-1}"` and logs the calculated worker count to stdout.
5. **PID 1 Process Replacement (Lines 31-32)**: Replaces the shell process with the command passed in arguments via `exec "$@"`. This ensures that signals such as `SIGTERM` and `SIGINT` from Docker or Kubernetes are delivered directly to Uvicorn for graceful connection termination.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Permissive Migration Failure Swallowing (Production Data Corruption Risk)
In lines 19-21:
```sh
alembic upgrade head || {
    echo "[WARNING] Database migration failed or database unreachable; continuing startup..."
}
```
If a database migration fails (due to PostgreSQL connection timeout, syntax errors in an Alembic revision, or missing extension locks), the entrypoint catches the failure and continues execution. When the Uvicorn application server starts, application queries attempting to read new tables or columns trigger immediate database crashes (`UndefinedTable`, `UndefinedColumn`), creating runtime 500 errors and corrupting transaction states. Container entrypoints must fail fast (`exit 1`) when database schema migrations fail.

### Invariant 2: Non-Enforced CIS Docker Benchmark 4.1 Root Check
In lines 11-13:
```sh
if [ "$(id -u)" -eq 0 ]; then
    echo "[WARNING] Running as root inside container violates CIS Docker Benchmark 4.1."
fi
```
The script emits a passive warning when running as root (UID 0), but does not abort execution or switch to a non-root user (e.g. UID 10001 `nirmaya`). In high-security environments subject to DISA STIG or CIS Docker Benchmarks, running with root privileges presents severe privilege escalation risks in the event of a container breakout.

### Invariant 3: Unused Concurrency Parameter
In line 28:
```sh
WORKERS="${WEB_CONCURRENCY:-1}"
echo "[NIRMAYA-CONTAINER] Starting application server with WEB_CONCURRENCY=${WORKERS}..."
exec "$@"
```
The computed `WORKERS` variable is only printed in an echo statement; it is not injected into the final `exec "$@"` command. If the container `CMD` is `uvicorn app.main:app`, it runs as a single worker unless the caller explicitly configured the `--workers` CLI parameter.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-DEP-ENT-F01` | **S1** | `[QUAL]` / `[SEC]` | `docker-entrypoint.sh:19-21` | Alembic migration failure is swallowed with a warning, permitting Uvicorn to start with out-of-date or broken database schemas. |
| `BE-DEP-ENT-F02` | **S2** | `[SEC]` | `docker-entrypoint.sh:11-13` | CIS Docker Benchmark 4.1 root check logs a warning but fails open without enforcing unprivileged user execution. |
| `BE-DEP-ENT-F03` | **S2** | `[QUAL]` | `docker-entrypoint.sh:28-32` | `WORKERS` variable calculated from `WEB_CONCURRENCY` is never passed to `exec "$@"`, defaulting server to single-worker mode. |
| `BE-DEP-ENT-F04` | **S3** | `[DOC]` | `docker-entrypoint.sh:1-5` | Missing documentation regarding required database wait-for-it socket readiness probes before invoking Alembic migrations. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-DEP-ENT-F01-F02`: Fail-Fast on Migration Error & Enforce Non-Root Execution
```diff
--- a/backend/docker-entrypoint.sh
+++ b/backend/docker-entrypoint.sh
@@ -10,7 +10,8 @@
 # Verify unprivileged execution context
 if [ "$(id -u)" -eq 0 ]; then
-    echo "[WARNING] Running as root inside container violates CIS Docker Benchmark 4.1."
+    echo "[ERROR] Running as root inside container violates CIS Docker Benchmark 4.1. Aborting."
+    exit 1
 fi
 
 # Run database schema migrations if enabled
@@ -18,7 +19,8 @@
     if command -v alembic > /dev/null 2>&1; then
-        alembic upgrade head || {
-            echo "[WARNING] Database migration failed or database unreachable; continuing startup..."
-        }
+        alembic upgrade head || {
+            echo "[FATAL] Database migration failed. Halting container startup to prevent schema corruption."
+            exit 1
+        }
     else
```
