# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/health.py`
**Audited Path:** `backend/app/schemas/health.py`  
**Module:** `backend` | **Subsystem:** Health Probes & System Telemetry Schemas  
**Severity Classification:** MEDIUM RISK (`[QUAL]` / `[SEC]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/health.py` provides the Pydantic schemas for NIRMAYA's system liveness, readiness, and telemetry endpoints (`/health`, `/healthz`). Designed for container orchestrators (Kubernetes kubelet probes), cloud load balancers, and DevOps monitoring systems, this module structures:
- Healthcare data standards readiness indicators (`StandardsCompliance`: FHIR R4, ABDM Sandbox, LOINC, SNOMED CT).
- Relational database connection probe metrics (`DatabaseHealth`: status, asyncpg driver, query roundtrip latency, pool size, error diagnostics).
- Top-level enterprise platform health responses (`SystemHealthResponse`: uptime, project metadata, environment, overall cluster health).

#### 2. Key Components & Class Roster
- `StandardsCompliance`: Health standards readiness indicators confirming active compliance with HL7 FHIR Release 4, ABDM sandbox integration, LOINC laboratory terminologies, and SNOMED CT clinical terms.
- `DatabaseHealth`: Database connectivity telemetry reporting probe status (`healthy`, `unreachable`, `degraded`, `not_configured`), driver (`postgresql+asyncpg`), dialect, roundtrip query latency in milliseconds, and active connection pool size.
- `SystemHealthResponse`: Master health envelope bundling overall operational status, project name, version, deployment environment, process uptime in seconds, UTC timestamp, standards compliance, and database diagnostics.

---

### Layer B: Plain-Language Developer Walkthrough

When running a mission-critical national healthcare platform inside Kubernetes or Docker containers, automated watchdogs constantly query the backend to answer two questions: "Is the server alive?" (liveness probe) and "Is the server ready to receive patient traffic?" (readiness probe). If the database crashes or network connectivity to the ABDM gateway drops, the orchestrator needs to know immediately so it can stop routing patient requests to a broken container or automatically restart it.

`health.py` defines the exact structure of this status report:
1. It checks the database connection (`DatabaseHealth`), measuring how many milliseconds it took to execute a test query (`latency_ms`) and how many database connections are currently in use.
2. It confirms whether core clinical standards (`StandardsCompliance`) are ready—such as SNOMED CT ontologies and FHIR R4 transformers.
3. It bundles everything into a `SystemHealthResponse` that tells Kubernetes, cloud monitors, and site reliability engineers (SREs) whether the cluster is healthy, degraded, or unhealthy.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **Literal Type Safety:** `DatabaseHealth.status` employs Pydantic's `Literal["healthy", "unreachable", "degraded", "not_configured"]`, ensuring strictly typed enumeration of database probe states.
- **Uptime Validation:** `uptime_seconds: float = Field(ge=0.0)` guarantees non-negative uptime durations.
- **Modular Sub-probes:** Separates high-level system metadata from infrastructure telemetry (`database`) and domain readiness (`standards`).

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Potential Database Connection String Leakage in Error Diagnostics (`BE-SCH-HLT-F01`)
- **Severity:** S2 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/health.py:26`
- **Description:** `DatabaseHealth.error` is an unbounded `Optional[str]`. If an unhandled database probe failure occurs (e.g. an `asyncpg.PostgresError` or SQLAlchemy `OperationalError`), raw exception messages can include hostnames, internal VPC IP addresses, database user names, or full connection URIs if unformatted. Returning raw database errors in a public or unauthenticated health check endpoint leaks internal network architecture.
- **Impact:** Information disclosure of internal infrastructure details to unauthorized external probes (CWE-209 / CWE-200).
- **Remediation:** Ensure error diagnostics are sanitized, or mark `error` with `repr=False` and restrict detailed errors to internal monitoring scopes.

##### Vulnerability 2: Unbounded Status String in SystemHealthResponse (`BE-SCH-HLT-F02`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/health.py:33`
- **Description:** While `DatabaseHealth.status` uses a strict `Literal` type, `SystemHealthResponse.status` is declared as an open-ended generic `str = Field(default="healthy")`. This allows inconsistent values (`"OK"`, `"UP"`, `"degraded"`, `"HEALTHY"`) to be emitted by different probe handlers, complicating automated alert parsing in Prometheus/Grafana.
- **Impact:** Inconsistent API contract for automated health monitors.
- **Remediation:** Enforce `status: Literal["healthy", "degraded", "unhealthy"]`.

##### Vulnerability 3: Missing Boundary Constraints on Latency and Pool Size (`BE-SCH-HLT-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/health.py:25, 27`
- **Description:** `DatabaseHealth.latency_ms` and `pool_size` lack `ge=0.0` and `ge=0` bounds, allowing negative latency values or negative pool sizes to pass validation.
- **Impact:** Defective boundary validation.
- **Remediation:** Add `ge=0.0` to `latency_ms` and `ge=0` to `pool_size`.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-HLT-F01` | S2 | `[SEC]` | `health.py:26` | Unsanitized `DatabaseHealth.error` risks leaking internal database host/connection details |
| `BE-SCH-HLT-F02` | S3 | `[QUAL]` | `health.py:33` | `SystemHealthResponse.status` uses open-ended `str` instead of strict `Literal` |
| `BE-SCH-HLT-F03` | S3 | `[QUAL]` | `health.py:25, 27` | `latency_ms` and `pool_size` lack non-negative boundary constraints |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/health.py
+++ b/backend/app/schemas/health.py
@@ -2,5 +2,5 @@
-from pydantic import BaseModel, Field
-from datetime import datetime
+from pydantic import BaseModel, ConfigDict, Field
+from datetime import datetime, timezone
 from typing import Optional, Literal
 
 
@@ -19,8 +19,10 @@ class DatabaseHealth(BaseModel):
     status: Literal["healthy", "unreachable", "degraded", "not_configured"] = Field(
         default="healthy", description="Database connection probe status"
     )
     driver: str = Field(default="postgresql+asyncpg", description="Underlying DB driver")
     database_type: Optional[str] = Field(default=None, description="Database dialect (e.g. postgresql, sqlite)")
-    latency_ms: Optional[float] = Field(default=None, description="Roundtrip query latency in milliseconds")
-    error: Optional[str] = Field(default=None, description="Error diagnostics if probe failed")
-    pool_size: Optional[int] = Field(default=None, description="Configured connection pool size")
+    latency_ms: Optional[float] = Field(default=None, ge=0.0, description="Roundtrip query latency in milliseconds")
+    error: Optional[str] = Field(default=None, repr=False, description="Sanitized error diagnostics if probe failed")
+    pool_size: Optional[int] = Field(default=None, ge=0, description="Configured connection pool size")
 
@@ -32,3 +34,3 @@ class SystemHealthResponse(BaseModel):
-    status: str = Field(default="healthy", description="Overall cluster health state")
+    status: Literal["healthy", "degraded", "unhealthy"] = Field(default="healthy", description="Overall cluster health state")
     project: str = Field(default="NIRMAYA")
     full_name: str
     version: str
     environment: str
     uptime_seconds: float = Field(ge=0.0)
-    timestamp: datetime
+    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
     standards: StandardsCompliance
     database: DatabaseHealth
```
