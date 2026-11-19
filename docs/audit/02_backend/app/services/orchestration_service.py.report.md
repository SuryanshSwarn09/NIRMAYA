# Codebase Technical Audit Report: `backend/app/services/orchestration_service.py`

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`orchestration_service.py` implements container orchestration topology inspection, static Docker Compose auditing, Caddy reverse proxy configuration auditing, and inter-service health mesh latency telemetry for NIRMAYA. It inspects the 5-node production topology (PostgreSQL 16, Redis 7, FastAPI backend, Next.js 15 frontend, and Caddy 2 reverse proxy), verifies persistent volume mappings and network bridge isolation, validates Caddyfile TLS 1.3 configuration, and produces production readiness compliance scores.

### System Topology & Health Mesh
```
   [ Caddy 2 Ingress Reverse Proxy ] (TLS 1.3, Ports 80/443)
                 |
     +-----------+-----------+
     |                       |
     v                       v
[ Frontend ]            [ Backend ]
(Next.js 15: Port 3000) (FastAPI: Port 8000)
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
           [ PostgreSQL 16 ]        [ Redis 7 ]
           (Port 5432, RLS DB)      (Port 6379, Bus)
```

### Module Metadata & Imports/Exports
- **Module Path:** `backend/app/services/orchestration_service.py`
- **Component Classification:** DevOps, Container Topology & Reverse Proxy Auditor
- **Lines of Code:** 391 LOC
- **Imports:** `datetime`, `logging`, `os`, `time`, `typing`, `app.schemas.orchestration.*`
- **Primary Export:** `orchestration_service` (Global Singleton Instance)

---

## Layer B: Plain-Language Developer Walkthrough

The module provides four inspection and auditing capabilities:
1. **Multi-Service Topology Manifest (`get_orchestration_topology`)**: Returns the formal production topology defining all 5 nodes, internal/exposed ports, persistent volume bindings (`postgres_data`, `redis_data`, `caddy_data`, `caddy_config`), healthcheck probes, and restart policies under the isolated bridge network `nirmaya-net`.
2. **Static Docker Compose Auditing (`audit_docker_compose_file`)**: Reads `docker-compose.yml`, verifying that all 5 services exist, healthcheck dependency chains (`condition: service_healthy`) are declared, persistent storage is mounted, and isolated bridge networks are configured. It computes a compliance score (0–100%).
3. **Static Caddyfile Auditing (`audit_caddy_configuration`)**: Analyzes the root `Caddyfile` for TLS 1.3 parameters, WebSocket route forwarding (`/ws/*`), API route multiplexing (`/api/*`), Next.js application reverse proxying (`/*`), zstd/gzip compression, and enterprise security headers (HSTS, X-Content-Type-Options, X-Frame-Options DENY).
4. **Inter-Service Health Mesh Telemetry (`get_health_mesh_status`)**: Gathers status from the 5 container services, calculating overall mesh health and average latency.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Single Ingress Exposure Invariant
In production deployment, only the Caddy reverse proxy container exposes ports externally (80 and 443). Databases, cache instances, and application containers communicate strictly across the isolated internal `nirmaya-net` bridge network without public port mapping.

### Invariant 2: Healthcheck Dependency Chain
The orchestration topology mandates strict ordering: the backend container cannot start until PostgreSQL and Redis report `service_healthy`; the Caddy ingress proxy cannot start until both frontend and backend report `service_healthy`.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
|---|---|---|---|---|
| `BE-SVC-ORC-F01` | **S1** | `[SEC]` | `backend/app/services/orchestration_service.py:345-385` | Simulated Mock Health Mesh Probes with Hardcoded Static Latencies. `get_health_mesh_status()` constructs hardcoded nodes with static latencies (Postgres 1.2ms, Redis 0.4ms, Backend 2.1ms, Frontend 3.5ms, Caddy 0.8ms) and static `is_healthy=True` without executing real network probes or Docker daemon API inspections, providing false green status even during an active outage. |
| `BE-SVC-ORC-F02` | **S1** | `[SEC]` | `backend/app/services/orchestration_service.py:140-190, 240-290` | Naive Substring Search for Security and Configuration Auditing. `audit_docker_compose_file` and `audit_caddy_configuration` check presence of strings via `"service_healthy" in content` or `"nirmaya-net" in content`. A commented-out line `# nirmaya-net` or `# condition: service_healthy` passes the audit as a valid configuration. |
| `BE-SVC-ORC-F03` | **S2** | `[QUAL]` | `backend/app/services/orchestration_service.py:40-105` | Statically Hardcoded Image Tags (`nirmaya-backend:v0.4.0`, `nirmaya-frontend:v0.4.0`) in Topology Manifest. Out of date with repository version tags (`v1.0.0` / `v1.1.0`). |
| `BE-SVC-ORC-F04` | **S2** | `[QUAL]` | `backend/app/services/orchestration_service.py:130-136` | Arbitrary Relative File Path Resolution (`../../../docker-compose.yml`) Vulnerable to Working Directory Shifts. |
| `BE-SVC-ORC-F05` | **S3** | `[PERF]` | `backend/app/services/orchestration_service.py:145-165` | Synchronous Blocking File I/O (`open().read()`) Inside Async FastAPI Service Layer. |
| `BE-SVC-ORC-F06` | **S4** | `[DOC]` | `backend/app/services/orchestration_service.py:10-18` | Missing Kubernetes Helm Chart and Sovereign Cloud Migration Documentation. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch 1: Dynamic Version Image Tagging (`BE-SVC-ORC-F03`)
```diff
--- a/backend/app/services/orchestration_service.py
+++ b/backend/app/services/orchestration_service.py
@@ -69,3 +69,3 @@ class OrchestrationService:
                 service_name="backend",
                 container_name="nirmaya-backend",
-                image="nirmaya-backend:v0.4.0",
+                image=f"nirmaya-backend:{os.getenv('APP_VERSION', 'v1.1.0')}",
                 exposed_ports=[],
@@ -83,3 +83,3 @@ class OrchestrationService:
                 service_name="frontend",
                 container_name="nirmaya-frontend",
-                image="nirmaya-frontend:v0.4.0",
+                image=f"nirmaya-frontend:{os.getenv('APP_VERSION', 'v1.1.0')}",
                 exposed_ports=[],
```

### Patch 2: Strip YAML/Caddy Comments Before Substring Validation (`BE-SVC-ORC-F02`)
```diff
--- a/backend/app/services/orchestration_service.py
+++ b/backend/app/services/orchestration_service.py
@@ -1,4 +1,5 @@
 import logging
 import os
+import re
 import time
@@ -144,2 +145,4 @@ class OrchestrationService:
             content = f.read()
+        # Strip comment lines to avoid false-positive verification
+        content = re.sub(r"^\s*#.*$", "", content, flags=re.MULTILINE)
```
