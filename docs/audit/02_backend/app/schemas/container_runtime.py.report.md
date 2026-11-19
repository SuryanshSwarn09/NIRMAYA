# Audit Report: backend/app/schemas/container_runtime.py

**Path:** `backend/app/schemas/container_runtime.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 452 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for Container Runtime Telemetry, CIS Docker Benchmark Security Auditing, Environment Variable Conformance, and OCI Multi-Stage Image Manifests for both FastAPI backend and Next.js frontend containers.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** In `EnvironmentVariableCheck.masked_value`, the field is defined as a plain string without `repr=False`. If environment inspection services experience edge-case masking failures, serializing `EnvironmentVariableCheck` models in exception traces or debug logs will disclose sensitive production database passwords or API secrets in cleartext (CWE-532 / CWE-312).

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Deploying national healthcare software into production requires strict operational conformance: processes must never execute as `root` (UID 0), containers must enforce non-root UID 10001 (backend) and UID 1001 (Next.js), root filesystems should be mounted read-only, cgroup memory limits must be continuously monitored, and environment variables must be audited to ensure production configurations don't accidentally fall back to insecure local defaults. This file provides the structured data models to inspect, audit, score, and serialize container runtime security posture and OCI image specifications.

### How it works, step by step
1. `ContainerExecutionMode` and `FrontendExecutionMode` classify the runtime environment (`containerized`, `standalone_host`, `development`, `test_runner`).
2. `SecurityComplianceLevel` classifies CIS Docker security audit outcomes (`strict_non_root`, `standard`, `warning_root`, `non_compliant`).
3. `ContainerRuntimeStatus` and `FrontendContainerStatus` report live process telemetry: process UID/GID, non-root flag, Python/Node versions, allocated cgroup memory, active workers, RSS/heap memory, and uptime.
4. `ContainerSecurityAudit` and `FrontendSecurityAudit` score process security against CIS benchmarks (evaluating UID assignment, read-only rootfs, seccomp filters, and producing a percentage compliance score).
5. `EnvironmentVariableCheck` and `EnvironmentConformanceReport` audit all environment variables, verifying whether required variables are configured, marking sensitive secrets, computing masked display strings, and calculating an overall production readiness score (`conformance_score_pct`).
6. `DockerStageManifest`, `DockerImageManifest`, and `FrontendDockerManifest` define OCI multi-stage build specifications (base images, layers, compressed size targets, non-root user/group configs, health check probes).

### Concepts and patterns used
- *CIS Docker Benchmark Compliance:* Validating unprivileged process execution (UID 10001 backend, UID 1001 frontend).
- *Automated Environment Configuration Scoring:* Auditing environment variables for insecure fallback defaults.
- *OCI Image Manifest Specification:* Modeling multi-stage Alpine Linux container build stages and cache artifacts.

### Key lines to read first
- `container_runtime.py:33-82`: `ContainerRuntimeStatus` live container inspection model.
- `container_runtime.py:84-123`: `ContainerSecurityAudit` CIS benchmark evaluation.
- `container_runtime.py:125-154`: `EnvironmentVariableCheck` credential inspection schema.
- `container_runtime.py:156-195`: `EnvironmentConformanceReport` configuration scorecard.
- `container_runtime.py:284-341`: `FrontendContainerStatus` Next.js runtime telemetry.
- `container_runtime.py:343-412`: `FrontendDockerManifest` OCI standalone manifest.

### How to change it safely
When auditing new environment variables, register them in `backend/app/core/container_security.py` and ensure sensitive variables are explicitly marked with `is_sensitive=True`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `enum` (Enum), `typing` (Dict, List, Optional), `pydantic` (BaseModel, ConfigDict, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/core/container_security.py`, `backend/app/api/v1/endpoints/container_runtime.py`.
- **Public Surface:** Enums `ContainerExecutionMode`, `SecurityComplianceLevel`, `FrontendExecutionMode`; Models `ContainerRuntimeStatus`, `ContainerSecurityAudit`, `EnvironmentVariableCheck`, `EnvironmentConformanceReport`, `DockerStageManifest`, `DockerImageManifest`, `FrontendContainerStatus`, `FrontendDockerManifest`, `FrontendSecurityAudit`.

### 2. Security [SEC]
- **Potential Secret Leakage via String Repr (CWE-532 / CWE-312):** In `EnvironmentVariableCheck.masked_value` (line 142), the field is an unmasked plain `str` (`BE-SCH-CRUN-F01`). While the service layer masks secrets (e.g. `postgresql://***:***@localhost:5432/nirmaya`), defense-in-depth requires adding `repr=False` to `masked_value` so that any upstream masking error or partial unmasking cannot leak credentials into log files.
- **Root Process Execution Auditing:** `ContainerSecurityAudit.is_root` and `process_uid` ensure immediate detection if a container process inadvertently starts as UID 0.

### 3. Code quality [QUAL]
- **Unconstrained Status Classifications (`BE-SCH-CRUN-F02`):** In `EnvironmentVariableCheck.status` (line 146) and `EnvironmentConformanceReport.status` (line 183), status values are documented as strings (`'PASS'`, `'WARN_DEFAULT'`, `'READY_PRODUCTION'`, etc.) rather than typed `Enum` or `Literal` types.
- Strict Pydantic v2 percentage constraints (`ge=0.0, le=100.0`) on `cis_benchmark_score_pct` and `conformance_score_pct`.

### 4. AI-generated-code smells [QUAL]
- Hardcoded static image tags (`tag: str = "v0.4.0"` on lines 234, 353) and static target image sizes (`target_image_size_mb: float = 118.5` and `145.0`) embedded as default field values (`BE-SCH-CRUN-F03`).

### 5. Performance [PERF]
- Telemetry models are evaluated on-demand during administrative health checks; negligible runtime overhead.

### 6. Error handling & edge cases
- `allocated_memory_mb: Optional[float] = None` cleanly handles unconstrained host environments where cgroup memory limits are not enforced.

### 7. Doc accuracy [DOC]
- Conforms to CIS Docker Benchmark v1.6.0 and NIST SP 800-190 container security guidelines.

### 8. Tests
- Covered by `backend/tests/test_container_runtime.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-CRUN-F01 | S2 | [SEC] | 142-145 | `masked_value` in environment check lacks `repr=False` | `masked_value: str = Field(...)` | Add `repr=False` to prevent credential exposure in logs |
| BE-SCH-CRUN-F02 | S3 | [QUAL] | 146, 183 | Status classification fields use freeform strings | `status: str` with docstring examples | Convert to `Enum` or `Literal` |
| BE-SCH-CRUN-F03 | S4 | [QUAL] | 234, 246, 353, 369 | Hardcoded version tags and image sizes in default schema values | `tag = "v0.4.0"`, `target_image_size_mb = 118.5` | Drive version tags and sizes from build metadata |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-CRUN-F01 · Risk: Low · [UNTESTED]
Add `repr=False` to `EnvironmentVariableCheck.masked_value`:

```diff
--- a/backend/app/schemas/container_runtime.py
+++ b/backend/app/schemas/container_runtime.py
@@ -142,4 +142,5 @@ class EnvironmentVariableCheck(BaseModel):
     masked_value: str = Field(
         ...,
         description="Sanitized value safe for display in administrative dashboards",
+        repr=False,
     )
