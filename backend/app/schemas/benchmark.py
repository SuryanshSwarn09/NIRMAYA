from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BenchmarkSubsystemEnum(str, Enum):
    """Core NIRMAYA architectural subsystems instrumented for performance."""
    POSTGRES_POOL_LATENCY = "POSTGRES_POOL_LATENCY"
    REDIS_LOCK_CONCURRENCY = "REDIS_LOCK_CONCURRENCY"
    FHIR_BUNDLE_SERIALIZATION = "FHIR_BUNDLE_SERIALIZATION"
    ABDM_CRYPTO_PIPELINE = "ABDM_CRYPTO_PIPELINE"
    WEBSOCKET_BROADCAST_FANOUT = "WEBSOCKET_BROADCAST_FANOUT"
    END_TO_END_CLINICAL_PIPELINE = "END_TO_END_CLINICAL_PIPELINE"


class SlaStatusEnum(str, Enum):
    """SLA fulfillment status based on P99 latency and throughput thresholds."""
    COMPLIANT = "COMPLIANT"
    BORDERLINE = "BORDERLINE"
    BREACHED = "BREACHED"


class ExportFormatEnum(str, Enum):
    """Supported export serialization formats for benchmark reports."""
    JSON = "JSON"
    CSV = "CSV"
    IEEE_MARKDOWN = "IEEE_MARKDOWN"


class LatencyPercentiles(BaseModel):
    """Empirical latency percentiles and parametric statistical distributions in milliseconds."""
    p50_ms: float = Field(..., description="50th percentile (median) latency in ms")
    p90_ms: float = Field(..., description="90th percentile latency in ms")
    p95_ms: float = Field(..., description="95th percentile latency in ms")
    p99_ms: float = Field(..., description="99th percentile latency in ms")
    min_ms: float = Field(..., description="Minimum recorded latency in ms")
    max_ms: float = Field(..., description="Maximum recorded latency in ms")
    mean_ms: float = Field(..., description="Arithmetic mean latency in ms")
    std_dev_ms: float = Field(..., description="Standard deviation of latency distribution in ms")


class ThroughputMetrics(BaseModel):
    """Empirical throughput and bandwidth processing metrics."""
    total_operations: int = Field(..., description="Total completed benchmark iterations")
    duration_seconds: float = Field(..., description="Total elapsed wall-clock execution time in seconds")
    operations_per_second: float = Field(..., description="Calculated operational throughput (ops/sec)")
    bytes_processed: int = Field(default=0, description="Total payload bytes processed")
    mb_per_second: float = Field(default=0.0, description="Payload throughput in megabytes per second")


class BenchmarkResult(BaseModel):
    """Detailed benchmark evaluation result for an individual subsystem."""
    benchmark_id: str = Field(..., description="Unique benchmark execution identifier")
    subsystem: BenchmarkSubsystemEnum
    name: str = Field(..., description="Descriptive benchmark name")
    description: str = Field(..., description="Detailed description of workload characteristics")
    iterations: int = Field(..., description="Number of iterations executed")
    concurrency_level: int = Field(..., description="Simultaneous concurrent execution threads/tasks")
    latency: LatencyPercentiles
    throughput: ThroughputMetrics
    sla_target_p99_ms: float = Field(..., description="Target SLA threshold for P99 latency in ms")
    sla_target_min_ops: float = Field(..., description="Target SLA minimum throughput in ops/sec")
    sla_status: SlaStatusEnum = Field(..., description="Evaluated SLA fulfillment state")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    telemetry_notes: List[str] = Field(default_factory=list, description="Subsystem-specific runtime notes")


class BenchmarkRunRequest(BaseModel):
    """Request payload to trigger on-demand synthetic or empirical benchmark execution."""
    subsystems: Optional[List[BenchmarkSubsystemEnum]] = Field(
        None, description="Optional subset of subsystems to benchmark; executes all if omitted"
    )
    iterations: int = Field(
        default=100, ge=5, le=5000, description="Number of test iterations to execute per benchmark"
    )
    concurrency: int = Field(
        default=10, ge=1, le=100, description="Concurrency factor for simulated caller contention"
    )
    include_synthetic_load: bool = Field(
        default=True, description="Whether to include synthetic data load variations"
    )


class BenchmarkSuiteReport(BaseModel):
    """Consolidated system performance scorecard across all evaluated subsystems."""
    suite_id: str = Field(..., description="Unique suite report identifier")
    system_environment: Dict[str, Any] = Field(
        default_factory=dict, description="Host OS, CPU cores, Python version, and memory telemetry"
    )
    results: List[BenchmarkResult] = Field(default_factory=list)
    overall_sla_compliance_rate: float = Field(
        ..., description="Percentage of benchmarks compliant with SLA targets"
    )
    total_benchmarks_executed: int = Field(default=0)
    total_operations_executed: int = Field(default=0)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BenchmarkExportResponse(BaseModel):
    """Formatted benchmark data payload for reporting and publication."""
    format: ExportFormatEnum
    content: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
