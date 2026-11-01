import pytest
from httpx import AsyncClient

from app.schemas.benchmark import (
    BenchmarkExportResponse,
    BenchmarkResult,
    BenchmarkRunRequest,
    BenchmarkSubsystemEnum,
    BenchmarkSuiteReport,
    ExportFormatEnum,
    LatencyPercentiles,
    SlaStatusEnum,
    ThroughputMetrics,
)
from app.services.benchmark_service import BenchmarkService, benchmark_service


# =============================================================================
# Unit Tests: Pydantic Schemas & Statistical Analytics
# =============================================================================

def test_benchmark_schemas_instantiation():
    """Verify serialization and validation of core performance benchmark schemas."""
    lat = LatencyPercentiles(
        p50_ms=1.2, p90_ms=2.5, p95_ms=3.1, p99_ms=4.2,
        min_ms=0.5, max_ms=5.0, mean_ms=1.5, std_dev_ms=0.7,
    )
    assert lat.p50_ms == 1.2
    assert lat.p99_ms == 4.2

    tp = ThroughputMetrics(
        total_operations=500, duration_seconds=0.25,
        operations_per_second=2000.0, bytes_processed=1024, mb_per_second=0.004,
    )
    assert tp.operations_per_second == 2000.0

    res = BenchmarkResult(
        benchmark_id="BM-TEST-01",
        subsystem=BenchmarkSubsystemEnum.POSTGRES_POOL_LATENCY,
        name="Test Benchmark",
        description="Testing suite",
        iterations=500,
        concurrency_level=10,
        latency=lat,
        throughput=tp,
        sla_target_p99_ms=5.0,
        sla_target_min_ops=1500.0,
        sla_status=SlaStatusEnum.COMPLIANT,
    )
    assert res.sla_status == SlaStatusEnum.COMPLIANT


def test_quantile_statistical_calculations():
    """Verify exact percentile quantile interpolation and parametric distribution calculations."""
    data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    stats = BenchmarkService.compute_percentiles(data)

    assert stats.min_ms == 1.0
    assert stats.max_ms == 10.0
    assert stats.mean_ms == 5.5
    assert stats.p50_ms == 5.5
    assert stats.p90_ms == 9.1
    assert stats.p95_ms == 9.55
    assert stats.p99_ms == 9.91
    assert stats.std_dev_ms > 2.8


def test_empty_quantile_calculations():
    """Verify graceful zero-initialization for empty latency measurements."""
    stats = BenchmarkService.compute_percentiles([])
    assert stats.p50_ms == 0.0
    assert stats.p99_ms == 0.0
    assert stats.mean_ms == 0.0
    assert stats.std_dev_ms == 0.0


def test_throughput_and_sla_evaluation():
    """Verify operations/sec calculations and SLA classification boundaries."""
    tp = BenchmarkService.compute_throughput(1000, 0.5, 1048576)
    assert tp.operations_per_second == 2000.0
    assert tp.mb_per_second == 2.0

    # 1. Compliant condition
    c1 = BenchmarkService.evaluate_sla(p99_ms=3.5, target_p99_ms=5.0, ops_per_sec=2000.0, target_min_ops=1500.0)
    assert c1 == SlaStatusEnum.COMPLIANT

    # 2. Borderline condition (P99 within 125% of SLA target)
    c2 = BenchmarkService.evaluate_sla(p99_ms=5.8, target_p99_ms=5.0, ops_per_sec=2000.0, target_min_ops=1500.0)
    assert c2 == SlaStatusEnum.BORDERLINE

    # 3. Breached condition (P99 exceeds 125% of target)
    c3 = BenchmarkService.evaluate_sla(p99_ms=7.5, target_p99_ms=5.0, ops_per_sec=2000.0, target_min_ops=1500.0)
    assert c3 == SlaStatusEnum.BREACHED


# =============================================================================
# Unit Tests: Service Engine & Scorecard Inspection
# =============================================================================

def test_benchmark_service_summary():
    """Verify aggregated system performance scorecard metadata."""
    summary = benchmark_service.get_summary()
    assert summary["total_benchmarks"] == 6
    assert summary["overall_sla_compliance_rate"] == 100.0
    assert summary["overall_status"] == "ALL_SYSTEMS_COMPLIANT"
    assert "environment" in summary
    assert "cpu_logical_cores" in summary["environment"]
    assert len(summary["scorecard"]) == 6


def test_benchmark_service_list_and_get_suites():
    """Verify baseline suites enumeration and single subsystem retrieval."""
    suites = benchmark_service.list_suites()
    assert len(suites) == 6

    pg_suite = benchmark_service.get_suite_by_subsystem(BenchmarkSubsystemEnum.POSTGRES_POOL_LATENCY)
    assert pg_suite is not None
    assert pg_suite.sla_target_p99_ms == 5.0
    assert pg_suite.latency.p99_ms < 5.0
    assert pg_suite.sla_status == SlaStatusEnum.COMPLIANT

    crypto_suite = benchmark_service.get_suite_by_subsystem(BenchmarkSubsystemEnum.ABDM_CRYPTO_PIPELINE)
    assert crypto_suite is not None
    assert crypto_suite.sla_target_p99_ms == 4.0


def test_benchmark_exporters():
    """Verify multi-format serialization in JSON, CSV, and IEEE Markdown table formats."""
    json_exp = benchmark_service.export_benchmarks(ExportFormatEnum.JSON)
    assert json_exp.format == ExportFormatEnum.JSON
    assert "BM-01-PG-POOL" in json_exp.content

    csv_exp = benchmark_service.export_benchmarks(ExportFormatEnum.CSV)
    assert csv_exp.format == ExportFormatEnum.CSV
    assert "subsystem,name,iterations" in csv_exp.content
    assert "POSTGRES_POOL_LATENCY" in csv_exp.content

    ieee_exp = benchmark_service.export_benchmarks(ExportFormatEnum.IEEE_MARKDOWN)
    assert ieee_exp.format == ExportFormatEnum.IEEE_MARKDOWN
    assert "# Table IV: Empirical Interoperability & Concurrency Benchmarks" in ieee_exp.content
    assert "| Subsystem Architectural Domain |" in ieee_exp.content


# =============================================================================
# Asynchronous Micro-Benchmark Executions
# =============================================================================

def test_live_micro_benchmark_postgres_pool():
    """Verify execution of PostgreSQL pool and ltree traversal micro-benchmark."""
    res = benchmark_service._benchmark_postgres_pool(iterations=20, concurrency=5)
    assert res.subsystem == BenchmarkSubsystemEnum.POSTGRES_POOL_LATENCY
    assert res.iterations == 20
    assert res.latency.p99_ms >= 0.0
    assert res.throughput.operations_per_second >= 0.0


def test_live_micro_benchmark_redis_lock():
    """Verify execution of Redlock distributed ACID locking micro-benchmark."""
    res = benchmark_service._benchmark_redis_lock(iterations=20, concurrency=4)
    assert res.subsystem == BenchmarkSubsystemEnum.REDIS_LOCK_CONCURRENCY
    assert res.iterations == 20
    assert res.latency.p99_ms >= 0.0


def test_live_micro_benchmark_fhir_bundle():
    """Verify execution of NRCeS HL7 FHIR R4 Bundle serialization micro-benchmark."""
    res = benchmark_service._benchmark_fhir_serialization(iterations=10)
    assert res.subsystem == BenchmarkSubsystemEnum.FHIR_BUNDLE_SERIALIZATION
    assert res.iterations == 10
    assert res.throughput.bytes_processed > 0


def test_live_micro_benchmark_abdm_crypto():
    """Verify Curve25519 ECDH + HKDF + AES-256-GCM AEAD cryptographic micro-benchmark."""
    res = benchmark_service._benchmark_abdm_crypto(iterations=10)
    assert res.subsystem == BenchmarkSubsystemEnum.ABDM_CRYPTO_PIPELINE
    assert res.iterations == 10
    assert res.throughput.bytes_processed > 0


def test_live_micro_benchmark_websocket_fanout():
    """Verify Pub/Sub channel multiplexing and fanout micro-benchmark."""
    res = benchmark_service._benchmark_websocket_fanout(iterations=15, subscribers=25)
    assert res.subsystem == BenchmarkSubsystemEnum.WEBSOCKET_BROADCAST_FANOUT
    assert res.iterations == 15


def test_live_micro_benchmark_e2e_pipeline():
    """Verify end-to-end clinical encounter lifecycle micro-benchmark."""
    res = benchmark_service._benchmark_end_to_end_pipeline(iterations=10)
    assert res.subsystem == BenchmarkSubsystemEnum.END_TO_END_CLINICAL_PIPELINE
    assert res.iterations == 10


# =============================================================================
# Integration Tests: FastAPI REST API Endpoints
# =============================================================================

async def test_api_get_benchmark_summary(client: AsyncClient):
    """Verify GET /api/v1/benchmarks/summary endpoint."""
    resp = await client.get("/api/v1/benchmarks/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_benchmarks"] == 6
    assert data["overall_sla_compliance_rate"] == 100.0
    assert "scorecard" in data
    assert "x-frame-options" in resp.headers


async def test_api_list_benchmark_suites(client: AsyncClient):
    """Verify GET /api/v1/benchmarks/suites endpoint."""
    resp = await client.get("/api/v1/benchmarks/suites")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 6
    subsystems = [s["subsystem"] for s in data]
    assert BenchmarkSubsystemEnum.POSTGRES_POOL_LATENCY.value in subsystems
    assert BenchmarkSubsystemEnum.REDIS_LOCK_CONCURRENCY.value in subsystems


async def test_api_get_suite_by_subsystem(client: AsyncClient):
    """Verify GET /api/v1/benchmarks/suites/{subsystem} endpoint."""
    resp = await client.get(f"/api/v1/benchmarks/suites/{BenchmarkSubsystemEnum.POSTGRES_POOL_LATENCY.value}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["subsystem"] == BenchmarkSubsystemEnum.POSTGRES_POOL_LATENCY.value
    assert data["sla_target_p99_ms"] == 5.0

    # Test 422 for invalid subsystem enum
    resp_invalid = await client.get("/api/v1/benchmarks/suites/NON_EXISTENT_SUBSYSTEM")
    assert resp_invalid.status_code in [404, 422]


async def test_api_run_live_benchmarks(client: AsyncClient):
    """Verify POST /api/v1/benchmarks/run endpoint with custom parameters."""
    payload = {
        "subsystems": [BenchmarkSubsystemEnum.POSTGRES_POOL_LATENCY.value],
        "iterations": 10,
        "concurrency": 2,
        "include_synthetic_load": True,
    }
    resp = await client.post("/api/v1/benchmarks/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_benchmarks_executed"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["subsystem"] == BenchmarkSubsystemEnum.POSTGRES_POOL_LATENCY.value


async def test_api_export_benchmark_results(client: AsyncClient):
    """Verify GET /api/v1/benchmarks/export endpoint with format parameters."""
    resp_json = await client.get("/api/v1/benchmarks/export?format=JSON")
    assert resp_json.status_code == 200
    assert resp_json.json()["format"] == "JSON"

    resp_csv = await client.get("/api/v1/benchmarks/export?format=CSV")
    assert resp_csv.status_code == 200
    assert "subsystem,name,iterations" in resp_csv.json()["content"]

    resp_ieee = await client.get("/api/v1/benchmarks/export?format=IEEE_MARKDOWN")
    assert resp_ieee.status_code == 200
    assert "Table IV" in resp_ieee.json()["content"]
