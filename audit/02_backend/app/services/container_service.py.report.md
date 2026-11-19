# Codebase Audit Report: `backend/app/services/container_service.py`

**Audit Target**: `backend/app/services/container_service.py`  
**Subsystem**: Backend - Container Runtime Telemetry & Security Conformance (`backend/app/services/`)  
**File Lines**: 535 LOC  
**Severity Breakdown**: S0: 0 | S1: 1 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `container_service.py` module performs deep host and container inspection for the NIRMAYA backend, auditing process user/group IDs (UID/GID), cgroup memory limits, CIS Docker Benchmark 4.1 security profiles, environment variable hygiene, and multi-stage Docker build manifests.

```
[ Operations Dashboard / Security Auditor ]
                     │
                     ▼
        [ container_service.py ]
   ├── 1. OCI Container & Cgroup Memory Probing (cgroup v1/v2)
   ├── 2. Process UID/GID Verification (CIS Docker Benchmark 4.1)
   ├── 3. Cryptographic Environment Hygiene & Entropy Auditing
   ├── 4. Backend Multi-Stage Docker Manifest (Alpine Python 3.12)
   └── 5. Frontend Standalone Next.js Container & Dockerfile Auditor
                     │
                     ▼
   [ ContainerRuntimeStatus / EnvironmentConformanceReport ]
```

### Import / Export Roster
- **Imports**: `datetime`, `logging`, `os`, `platform`, `sys`, `time`, `typing`, `app.core.config`, `app.schemas.container_runtime`.
- **Exports**: `ContainerService`, `container_service`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Container Detection**: Determines whether the process is executing inside an OCI container by inspecting `/.dockerenv`, `/proc/1/cgroup` (checking for docker/containerd tokens), or explicit environment flags.
2. **Process Privilege Inspection**: Resolves POSIX UID and GID via `os.getuid()` / `os.getgid()`, evaluating compliance against CIS Benchmark 4.1 (verifying non-root execution, ideally UID `10001`).
3. **Environment Hygiene**: Validates sensitive production configuration keys (`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`), ensuring secrets are not set to default strings and mask credentials safely for dashboards.
4. **Multi-Stage Build Specifications**: Returns architectural metadata for both backend (`nirmaya-backend`) and Next.js standalone frontend (`nirmaya-frontend`) images.
5. **Dockerfile Static Analysis**: Evaluates `frontend/Dockerfile` against best practices (multi-stage separation, non-root user creation, healthcheck endpoints).

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Security Context Bypass via Environment Variable Injection
At lines 73–76 in `get_process_uid_gid()`:
```python
env_uid = os.environ.get("NIRMAYA_PROCESS_UID")
env_gid = os.environ.get("NIRMAYA_PROCESS_GID")
if env_uid is not None and env_uid.isdigit():
    return int(env_uid), int(env_gid or "10001")
```
An environment variable override (`NIRMAYA_PROCESS_UID`) is permitted to dictate the effective process UID. If a container is misconfigured to run as root (`UID 0`), an attacker or compromised child process with environment injection privileges can set `NIRMAYA_PROCESS_UID=10001`. This causes `audit_security_context()` to report a 100% green CIS benchmark score (`STRICT_NON_ROOT`), masking active root execution.

### 2. Fabricated Frontend Telemetry
In `get_frontend_runtime_status()` (lines 400–447) and `audit_frontend_security_context()` (lines 448–480), the backend service synthesizes frontend metrics by reading arbitrary mock environment variables (`NIRMAYA_FRONTEND_RSS_MB = "86.4"`, heap total `54.8MB`, heap used `38.2MB`) without connecting to or probing the Next.js process. This provides a misleading claim of multi-container compliance.

### 3. Image Version Drift
`get_build_manifest()` hardcodes `tag="v0.4.0"` and `image_name="nirmaya-backend"`, while current platform releases are at v1.1.0/v1.2.0.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-CNT-F01` | **S1** | `[SEC]` | `backend/app/services/container_service.py:73-76` | `NIRMAYA_PROCESS_UID` environment variable override allows forging non-root UID status, completely bypassing CIS Docker Benchmark root execution detection. |
| `BE-SVC-CNT-F02` | **S2** | `[QUAL]` | `backend/app/services/container_service.py:400-480` | Frontend container status and security audit fabricate memory and compliance metrics using static mock fallbacks without querying the Node.js runtime. |
| `BE-SVC-CNT-F03` | **S3** | `[QUAL]` | `backend/app/services/container_service.py:338-340` | Stale hardcoded version tag `v0.4.0` in build manifest diverges from current production release versions. |
| `BE-SVC-CNT-F04` | **S4** | `[DOC]` | `backend/app/services/container_service.py:500-532` | Dockerfile static parser uses naive substring matching (`USER nextjs in content`) which can yield false positives on commented-out lines. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-CNT-F01`: Enforcing Authentic OS UID Inspection Without Environment Forgery

```diff
--- a/backend/app/services/container_service.py
+++ b/backend/app/services/container_service.py
@@ -70,12 +70,7 @@ class ContainerService:
     def get_process_uid_gid(self) -> Tuple[int, int]:
         """Resolve current process UID and GID with cross-platform fallback."""
-        # Check explicit override (useful for testing and simulated non-root verification)
-        env_uid = os.environ.get("NIRMAYA_PROCESS_UID")
-        env_gid = os.environ.get("NIRMAYA_PROCESS_GID")
-        if env_uid is not None and env_uid.isdigit():
-            return int(env_uid), int(env_gid or "10001")
-
         # POSIX native inspection
         if hasattr(os, "getuid") and hasattr(os, "getgid"):
             return os.getuid(), os.getgid()
```
