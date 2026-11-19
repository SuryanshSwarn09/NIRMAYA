# Audit Report: backend/app/schemas/benchmark.py

**Path:** `backend/app/schemas/benchmark.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 104 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation schemas for NIRMAYA's architectural performance benchmarking harness, SLA compliance verification, latency distributions, throughput metrics, and multi-format exports (JSON, CSV, IEEE Markdown).
- **Risk Level:** **S3 (Low)**
- **Verdict:** **READY**
- **Single Most Important Finding:** `BenchmarkSuiteReport.overall_sla_compliance_rate` and latency percentile fields lack boundary validation constraints (`ge=0.0`, `le=100.0`), permitting invalid or negative metrics to pass schema validation.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
High-throughput national healthcare platforms must rigorously verify that critical subsystems (PostgreSQL connection pools, Redis locks, FHIR bundle serialization, ABDM cryptographic pipelines, and WebSocket fan-out) satisfy strict latency and throughput Service Level Agreements (SLAs). To support empirical validation and academic publication, NIRMAYA includes an automated benchmark execution harness. This file defines the metrics models, benchmark run requests, consolidated suite scorecards, and publication export schemas.

### How it works, step by step
1. `BenchmarkSubsystemEnum` classifies the 6 critical subsystems evaluated (`POSTGRES_POOL_LATENCY`, `REDIS_LOCK_CONCURRENCY`, `FHIR_BUNDLE_SERIALIZATION`, `ABDM_CRYPTO_PIPELINE`, `WEBSOCKET_BROADCAST_FANOUT`, `END_TO_END_CLINICAL_PIPELINE`).
2. `SlaStatusEnum` categorizes SLA compliance (`COMPLIANT`, `BORDERLINE`, `BREACHED`).
3. `LatencyPercentiles` captures statistical distributions in milliseconds (p50, p90, p95, p99, min, max, mean, std_dev).
4. `ThroughputMetrics` measures operations per second, bytes processed, and megabytes per second.
5. `BenchmarkResult` combines latency, throughput, and target SLA thresholds into a single evaluation record.
6. `BenchmarkRunRequest` specifies test parameters (subsystems, iterations 5–5000, concurrency 1–100, synthetic load flags).
7. `BenchmarkSuiteReport` aggregates all benchmark outcomes alongside host hardware/software telemetry (`system_environment`).
8. `BenchmarkExportResponse` formats results for external reporting in JSON, CSV, or IEEE Markdown format.

### Concepts and patterns used
- *Parametric & Non-Parametric Latency Modeling:* Tracking both standard deviations and high-percentile latency tails (P99).
- *Scientific Publication Serialization:* Supporting IEEE Markdown exports for academic research reporting.
- *Strict Parameter Bounds:* Constraining iteration counts and concurrency factors to prevent server overload during tests.

### Key lines to read first
- `benchmark.py:7-15`: `BenchmarkSubsystemEnum` instrumented subsystems.
- `benchmark.py:31-41`: `LatencyPercentiles` statistical metrics.
- `benchmark.py:43-50`: `ThroughputMetrics` operational throughput schema.
- `benchmark.py:52-68`: `BenchmarkResult` individual subsystem evaluation.
- `benchmark.py:85-98`: `BenchmarkSuiteReport` consolidated performance scorecard.

### How to change it safely
When adding a new benchmarked subsystem, update `BenchmarkSubsystemEnum`. When updating SLA targets, ensure `sla_target_p99_ms` and `sla_target_min_ops` align with architectural thresholds in `app/core/config.py`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `enum` (Enum), `typing` (Any, Dict, List, Optional), `pydantic` (BaseModel, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/benchmark_service.py`, `backend/app/api/v1/endpoints/benchmark.py`.
- **Public Surface:** Enums `BenchmarkSubsystemEnum`, `SlaStatusEnum`, `ExportFormatEnum`; Models `LatencyPercentiles`, `ThroughputMetrics`, `BenchmarkResult`, `BenchmarkRunRequest`, `BenchmarkSuiteReport`, `BenchmarkExportResponse`.

### 2. Security [SEC]
- **No Secret or PHI Exposure:** Schemas strictly model synthetic performance telemetry and system hardware specifications. No credentials or patient identifiers are involved.
- **Resource Exhaustion Guardrails:** `BenchmarkRunRequest` strictly bounds `iterations` (5 to 5000) and `concurrency` (1 to 100), preventing callers from triggering excessive CPU or memory exhaustion.

### 3. Code quality [QUAL]
- **Missing Metric Boundaries (`BE-SCH-BNK-F01` & `BE-SCH-BNK-F02`):** In `BenchmarkSuiteReport.overall_sla_compliance_rate` (line 92), the field is an unconstrained `float` without `ge=0.0, le=100.0`. Similarly, latency fields in `LatencyPercentiles` lack `ge=0.0` non-negative validation constraints.
- **Missing Module Docstring (`BE-SCH-BNK-F03`):** File starts directly with imports on line 1 without a module-level docstring.

### 4. AI-generated-code smells [QUAL]
- Clean, focused schema design specifically tuned for reproducible scientific benchmarking.

### 5. Performance [PERF]
- Fast, non-blocking model validation; lightweight footprint.

### 6. Error handling & edge cases
- Bounded fields in `BenchmarkRunRequest` guarantee valid execution parameters.

### 7. Doc accuracy [DOC]
- Aligns with Day 87 system benchmarking and IEEE publication requirements.

### 8. Tests
- Covered by `backend/tests/test_benchmark.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-BNK-F01 | S3 | [QUAL] | 92-94 | Unconstrained compliance percentage | `overall_sla_compliance_rate: float` without bounds | Add `ge=0.0, le=100.0` |
| BE-SCH-BNK-F02 | S3 | [QUAL] | 33-40 | Latency metrics lack non-negative constraints | `p50_ms: float`, etc. without `ge=0.0` | Add `ge=0.0` to latency fields |
| BE-SCH-BNK-F03 | S4 | [QUAL] | 1 | Missing module-level docstring | File begins directly with imports | Add explanatory module docstring |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-BNK-F01 · Risk: Low · [UNTESTED]
Add boundary constraints to compliance rate:

```diff
--- a/backend/app/schemas/benchmark.py
+++ b/backend/app/schemas/benchmark.py
@@ -91,4 +91,4 @@ class BenchmarkSuiteReport(BaseModel):
     results: List[BenchmarkResult] = Field(default_factory=list)
     overall_sla_compliance_rate: float = Field(
-        ..., description="Percentage of benchmarks compliant with SLA targets"
+        ..., ge=0.0, le=100.0, description="Percentage of benchmarks compliant with SLA targets"
     )
