# Technical Audit Report: backend/app/services/benchmark_service.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/benchmark_service.py` provides the high-throughput performance benchmarking and SLA certification engine for the NIRMAYA platform. It calibrates empirical performance baselines against national Digital Public Infrastructure (DPI) Service Level Agreements (SLAs), measures exact quantiles ($P_{50}, P_{90}, P_{95}, P_{99}$), computes throughput (operations/sec, MB/sec), and exports benchmark scorecards into JSON, CSV, and IEEE Markdown table formats. The audit revealed two critical **S1** vulnerabilities: the database and cache benchmarks (`_benchmark_postgres_pool` and `_benchmark_redis_lock`) do not communicate with PostgreSQL or Redis, executing local in-memory Python operations while reporting sub-5ms SLA compliance, and the `export_benchmarks` endpoint exports only static hardcoded baselines, ignoring real-time benchmark execution results.

### Architectural Roster
- **Module Name:** `backend/app/services/benchmark_service.py`
- **Primary Responsibility:** Empirical performance benchmarking, statistical quantile calculation ($P_{50} \dots P_{99}$), SLA compliance verification, and multi-format benchmark exports.
- **Upstream Dependencies:**
  - `cryptography.hazmat.primitives.asymmetric.x25519`
  - `cryptography.hazmat.primitives.ciphers.aead.AESGCM`
  - `cryptography.hazmat.primitives.kdf.hkdf.HKDF`
  - `app.schemas.benchmark` (`BenchmarkResult`, `BenchmarkSuiteReport`, `LatencyPercentiles`, `ThroughputMetrics`, etc.)
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/benchmarks.py`
  - Academic monograph generation and IEEE manuscript tables
- **Exported Symbols:**
  - `BenchmarkService`
  - `benchmark_service`

```
+-----------------------------------------------------------------------------------+
|                        Performance Benchmarking Engine                            |
|                                                                                   |
|  [Benchmark Client / IEEE Manuscript Pipeline]                                    |
|          |                                                                        |
|          +--> [run_benchmarks(request)]                                           |
|          |         |-- POSTGRES_POOL_LATENCY   --> (MOCK: Python dict loop)       |
|          |         |-- REDIS_LOCK_CONCURRENCY  --> (MOCK: threading.Lock threads)  |
|          |         |-- FHIR_BUNDLE_SERIALIZATION -> (REAL: 10-resource JSON)      |
|          |         |-- ABDM_CRYPTO_PIPELINE     -> (REAL: Curve25519/AES-GCM)     |
|          |         |-- WEBSOCKET_FANOUT        --> (MOCK: in-memory arithmetic)  |
|          |         +-- END_TO_END_PIPELINE     --> (MOCK: string format loop)     |
|          |                                                                        |
|          +--> [compute_percentiles(latencies)] -> P50, P90, P95, P99, Mean, StdDev|
|          |                                                                        |
|          +--> [export_benchmarks(format)]                                         |
|                    +--> [DEFECT: Exports hardcoded baselines only! Ignores runs!] |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

This module provides the empirical measurement harness used to evaluate NIRMAYA's throughput and response times against mission-critical SLAs:

1. **Baseline Scorecard (`_init_baseline_scorecard`):** Initializes calibrated baseline benchmarks across 6 architectural domains:
   - **PostgreSQL Pool Latency:** $P_{99} < 5.0\text{ ms}$ target (Baseline: $3.82\text{ ms}$, $1841.6\text{ ops/s}$).
   - **Distributed Redlock Concurrency:** $P_{99} < 2.5\text{ ms}$ target (Baseline: $2.18\text{ ms}$, $4123.7\text{ ops/s}$).
   - **FHIR Bundle Serialization:** $P_{99} < 10.0\text{ ms}$ target (Baseline: $7.18\text{ ms}$, $784.9\text{ ops/s}$).
   - **ABDM Crypto Pipeline:** $P_{99} < 4.0\text{ ms}$ target (Baseline: $3.12\text{ ms}$, $1459.8\text{ ops/s}$).
   - **WebSocket Fanout:** $P_{99} < 15.0\text{ ms}$ target (Baseline: $11.45\text{ ms}$, $6849.3\text{ ops/s}$).
   - **End-to-End Clinical Pipeline:** $P_{99} < 50.0\text{ ms}$ target (Baseline: $39.4\text{ ms}$, $148.0\text{ ops/s}$).
2. **Statistical Analytics (`compute_percentiles`, `compute_throughput`, `evaluate_sla`):** Implements exact linear interpolation quantile formulas to calculate $P_{50}, P_{90}, P_{95},$ and $P_{99}$ latency, arithmetic mean, and sample standard deviation. It calculates throughput in operations per second and megabytes per second, comparing $P_{99}$ against the SLA target to classify status as `COMPLIANT`, `BORDERLINE`, or `BREACHED`.
3. **Live Execution Harness (`run_benchmarks`):** On request, executes micro-benchmarks for selected subsystems. While the cryptographic and FHIR bundle benchmarks perform genuine computations (executing real X25519 Diffie-Hellman, HKDF-SHA256, and AES-256-GCM AEAD ciphers), the database, cache, and WebSocket benchmarks run synthetic in-memory mocks.
4. **Multi-Format Export (`export_benchmarks`):** Formats benchmark metrics into JSON, CSV, or formatted IEEE LaTeX/Markdown tables for academic publications.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Performance Standards
- **Quantile Monotonicity:** $\text{Min} \le P_{50} \le P_{90} \le P_{95} \le P_{99} \le \text{Max}$.
- **SLA Classification Invariant:** Status is `COMPLIANT` if $P_{99} \le \text{target}$ and $\text{ops/sec} \ge 90\% \text{ of target}$.

### Vulnerabilities & Architectural Flaws
- **Mocking of Underlying Database & Cache Subsystems:**
  - `_benchmark_postgres_pool` (lines 389–432) queries a local Python dictionary `simulated_store = {f"in.gov.state_{i}...": ...}` rather than executing queries against PostgreSQL via `asyncpg`.
  - `_benchmark_redis_lock` (lines 434–480) uses a local Python `threading.Lock()` across OS threads rather than communicating with a Redis server or executing Redlock Lua scripts.
  - Generating compliance reports claiming verified PostgreSQL and Redis SLAs based on in-memory Python operations produces misleading performance metrics.
- **Live Run Decoupling in Exporter:** `export_benchmarks` (lines 799–835) reads exclusively from `self._baselines.values()`. If a user invokes `run_benchmarks` under high load and attempts to export the results, the exporter returns the static pre-cooked baseline dictionary, ignoring live empirical results.
- **Stripped `assert` Statements:** Lines 587 and 648 use `assert len(parsed["entry"]) == 10` and `assert plaintext == payload`. When executed with `python -O`, these assertions are stripped.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-BNK-F01` | **S1** | `[QUAL]` | `benchmark_service.py:389-480` | PostgreSQL and Redis benchmarks execute against in-memory Python dicts and thread locks, generating false SLA compliance claims. |
| `BE-SVC-BNK-F02` | **S1** | `[QUAL]` | `benchmark_service.py:799-835` | `export_benchmarks` ignores dynamic live benchmark results, exclusively exporting static pre-initialized baseline numbers. |
| `BE-SVC-BNK-F03` | **S2** | `[QUAL]` | `benchmark_service.py:676-755` | WebSocket fanout and E2E clinical benchmarks run local arithmetic loops rather than sending network frames or testing real EMR flows. |
| `BE-SVC-BNK-F04` | **S2** | `[QUAL]` | `benchmark_service.py:587, 648` | Integrity checks use Python `assert` statements, which are stripped when executed under `python -O`. |
| `BE-SVC-BNK-F05` | **S3** | `[QUAL]` | `benchmark_service.py:42` | `os.cpu_count()` detection does not respect cgroup CPU quotas in containerized Kubernetes environments. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Explicit Synthetic Mock Attribution in Benchmark Telemetry (`BE-SVC-BNK-F01`)

```diff
--- a/backend/app/services/benchmark_service.py
+++ b/backend/app/services/benchmark_service.py
@@ -417,7 +417,7 @@ class BenchmarkService:
             benchmark_id=f"RUN-PG-{int(time.time())}",
             subsystem=BenchmarkSubsystemEnum.POSTGRES_POOL_LATENCY,
-            name="PostgreSQL Connection Pool & Query Latency",
+            name="PostgreSQL Connection Pool & Query Latency (In-Memory Simulation Mode)",
             description="Real-time execution of connection pool checkout and ltree path resolution",
             iterations=iterations,
             concurrency_level=concurrency,
@@ -430,6 +430,7 @@ class BenchmarkService:
                 f"Iterations: {iterations}, Concurrency: {concurrency}",
                 "Simulated ltree subpath resolution and connection pool checkout",
+                "NOTICE: Benchmark executed against in-memory dictionary; live database probe requires DB harness context.",
             ],
         )
```
