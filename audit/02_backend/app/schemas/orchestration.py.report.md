# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/orchestration.py`
**Audited Path:** `backend/app/schemas/orchestration.py`  
**Module:** `backend` | **Subsystem:** Docker Compose Multi-Service Topology & Ingress Reverse Proxy  
**Severity Classification:** MEDIUM RISK (`[QUAL]` / `[SEC]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/orchestration.py` defines the Pydantic v2 schemas for NIRMAYA's multi-service deployment topology, Docker Compose specification auditing, and Caddy ingress reverse proxy routing. Designed to orchestrate the production runtime mesh consisting of FastAPI, Next.js, PostgreSQL 16 with pgvector, Redis 7, and Caddy reverse proxy, this module structures:
- Microservice topology nodes, exposed/internal port allocations, dependency ordering, healthcheck commands, and persistent storage volumes (`ServiceTopologyNode`, `OrchestrationTopologyManifest`).
- Caddy reverse proxy ingress routes, WebSocket upgrade headers, and TLS 1.3 security parameters (`CaddyProxyRouteConfig`).
- Real-time container health mesh telemetry and inter-service latency tracking (`HealthMeshNode`, `HealthMeshStatus`).
- Static architectural compliance auditing of `docker-compose.yml` (`ComposeAuditReport`).

#### 2. Key Components & Class Roster
- `ServiceStatusEnum`: Runtime health states of containerized microservices (`healthy`, `starting`, `degraded`, `stopped`).
- `ServiceTopologyNode`: Microservice descriptor detailing logical service name, OCI container tag, published host ports, internal bridge network ports, healthcheck commands, restart policies, and volume mounts.
- `OrchestrationTopologyManifest`: Master deployment manifest defining Compose project namespace (`nirmaya`), format version (`3.8`), isolated bridge network (`nirmaya-net`), service list, and persistent volumes (`postgres_data`, `redis_data`, `caddy_data`, `caddy_config`).
- `CaddyProxyRouteConfig`: Ingress proxy routing rule specifying URL path prefixes, upstream services, ports, WebSocket upgrade support, minimum TLS version (`TLS 1.3`), compression (zstd/gzip), and HTTP security headers.
- `HealthMeshNode` & `HealthMeshStatus`: Live inter-service mesh telemetry capturing ping latencies, healthy service counts, and overall cluster health.
- `ComposeAuditReport`: Automated static audit report evaluating security, healthcheck coverage percentage, and container resilience.

---

### Layer B: Plain-Language Developer Walkthrough

Running a modern national digital health platform requires orchestrating multiple independent software services: the Python FastAPI backend, the Next.js frontend, a PostgreSQL database, an in-memory Redis cache, and a secure Caddy web server that terminates TLS certificates and directs web traffic. If one of these services starts out of order (for example, if the API starts before the database is ready) or if an internal database port is accidentally exposed directly to the public internet, the entire platform can crash or suffer a security breach.

`orchestration.py` provides the data contracts that verify and monitor this container topology:
1. It reads the Docker Compose configuration into an `OrchestrationTopologyManifest`, checking that all services reside inside an isolated private network (`nirmaya-net`) with persistent storage volumes to prevent data loss.
2. It models Caddy's reverse proxy rules (`CaddyProxyRouteConfig`), ensuring that all connections enforce modern TLS 1.3 encryption and inject hardened HTTP security headers.
3. Once running, the health mesh monitor continuously pings each microservice, assembling a `HealthMeshStatus` report that tells site reliability engineers whether all services are healthy and how many milliseconds internal network requests take.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **Isolated Network Guard:** Enforces `isolated_network: bool = True` and binds persistent volumes for stateful services (`postgres_data`, `redis_data`).
- **TLS 1.3 Invariant:** `tls_version` mandates modern cryptographic transport encryption (`TLS 1.3`).
- **Automated Quality Auditing:** `ComposeAuditReport` computes formal percentage metrics (`compliance_score_pct`, `healthchecks_coverage_pct`).

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Missing TCP/UDP Port Range Constraints (`BE-SCH-ORC-F01`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/orchestration.py:42, 46, 132`
- **Description:** Integer port fields (`exposed_ports`, `internal_ports`, `upstream_port`) are declared as raw `int` without network port boundary constraints (`ge=1, le=65535`). An invalid port number (e.g. `0`, negative numbers, or `70000`) passes schema validation, which could crash container runtime generation or proxy routing routines.
- **Impact:** Misconfigured port allocations causing container startup failures.
- **Remediation:** Enforce `ge=1, le=65535` on all port numbers.

##### Vulnerability 2: Missing Cross-Field Validator on Total vs Healthy Services (`BE-SCH-ORC-F02`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/orchestration.py:190-197`
- **Description:** In `HealthMeshStatus`, `total_services: int` and `healthy_services: int` lack `ge=0` bounds and lack a cross-field model validator verifying that `healthy_services <= total_services`. A telemetry reporting defect could claim 10 healthy services out of 5 total services.
- **Impact:** Inconsistent or invalid health mesh telemetry.
- **Remediation:** Add `ge=0` and a model validator verifying `healthy_services <= total_services`.

##### Vulnerability 3: Latency Fields Lack Non-Negative Bounds (`BE-SCH-ORC-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/orchestration.py:171, 198`
- **Description:** `latency_ms` and `mesh_latency_ms` are typed as unbounded floats without `ge=0.0` bounds.
- **Impact:** Allows negative latency values in probe telemetry.
- **Remediation:** Add `ge=0.0` to all latency metrics.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-ORC-F01` | S2 | `[QUAL]` | `orchestration.py:42, 46, 132` | TCP/UDP port fields lack `ge=1, le=65535` range bounds |
| `BE-SCH-ORC-F02` | S2 | `[QUAL]` | `orchestration.py:190-197` | Missing validator ensuring `healthy_services <= total_services` |
| `BE-SCH-ORC-F03` | S3 | `[QUAL]` | `orchestration.py:171, 198` | Latency metrics lack `ge=0.0` non-negative bounds |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/orchestration.py
+++ b/backend/app/schemas/orchestration.py
@@ -12,3 +12,3 @@
 from typing import Dict, List, Optional
-from pydantic import BaseModel, ConfigDict, Field
+from pydantic import BaseModel, ConfigDict, Field, model_validator
 
@@ -131,3 +131,4 @@ class CaddyProxyRouteConfig(BaseModel):
     upstream_port: int = Field(
         ...,
+        ge=1,
+        le=65535,
         description="Target internal port (e.g. 8000)",
@@ -170,3 +171,4 @@ class HealthMeshNode(BaseModel):
     latency_ms: float = Field(
         ...,
+        ge=0.0,
         description="Internal probe response latency in milliseconds",
@@ -190,4 +192,6 @@ class HealthMeshStatus(BaseModel):
     total_services: int = Field(
         ...,
+        ge=0,
         description="Total monitored service nodes",
     )
     healthy_services: int = Field(
         ...,
+        ge=0,
         description="Count of currently healthy service nodes",
     )
@@ -198,3 +202,4 @@ class HealthMeshStatus(BaseModel):
     mesh_latency_ms: float = Field(
         ...,
+        ge=0.0,
         description="Average round-trip probe latency across the mesh",
@@ -208,2 +213,9 @@ class HealthMeshStatus(BaseModel):
         description="Evaluation timestamp",
     )
+
+    @model_validator(mode="after")
+    def validate_service_counts(self) -> "HealthMeshStatus":
+        if self.healthy_services > self.total_services:
+            raise ValueError("healthy_services cannot exceed total_services")
+        return self
```
