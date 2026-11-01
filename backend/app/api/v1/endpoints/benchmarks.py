from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query, Response, status

from app.schemas.benchmark import (
    BenchmarkExportResponse,
    BenchmarkResult,
    BenchmarkRunRequest,
    BenchmarkSubsystemEnum,
    BenchmarkSuiteReport,
    ExportFormatEnum,
)
from app.services.benchmark_service import benchmark_service
from app.core.container_security import get_container_security_headers

router = APIRouter(prefix="/benchmarks", tags=["Performance Benchmarks"])


@router.get(
    "/summary",
    summary="Get System Performance & Interoperability Scorecard",
    description="Returns aggregate performance metrics, host environment telemetry, and SLA compliance scorecard.",
    response_model=Dict[str, Any],
)
async def get_benchmark_summary(response: Response) -> Dict[str, Any]:
    """Retrieve top-level performance scorecard across all evaluated subsystems."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return benchmark_service.get_summary()


@router.get(
    "/suites",
    summary="List All Calibrated Subsystem Benchmark Suites",
    description="Returns verified baseline benchmark results across database, cache, crypto, and messaging subsystems.",
    response_model=List[BenchmarkResult],
)
async def list_benchmark_suites(response: Response) -> List[BenchmarkResult]:
    """Retrieve full catalog of baseline benchmark metrics."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return benchmark_service.list_suites()


@router.get(
    "/suites/{subsystem}",
    summary="Get Detailed Benchmark Results for Subsystem",
    description="Returns detailed latency percentiles, throughput metrics, and SLA status for an individual subsystem.",
    response_model=BenchmarkResult,
)
async def get_suite_by_subsystem(subsystem: BenchmarkSubsystemEnum, response: Response) -> BenchmarkResult:
    """Retrieve detailed benchmark telemetry for a specific architectural subsystem."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    result = benchmark_service.get_suite_by_subsystem(subsystem)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark suite for subsystem '{subsystem.value}' not found",
        )
    return result


@router.post(
    "/run",
    summary="Execute Live On-Demand Performance Benchmarks",
    description="Executes synthetic or empirical micro-benchmarks with custom iterations and concurrency levels.",
    response_model=BenchmarkSuiteReport,
)
async def run_live_benchmarks(request: BenchmarkRunRequest, response: Response) -> BenchmarkSuiteReport:
    """Trigger live execution of requested subsystem benchmarks and return aggregated performance report."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return await benchmark_service.run_benchmarks(request)


@router.get(
    "/export",
    summary="Export Benchmark Results",
    description="Exports calibrated system benchmarks in JSON, CSV, or IEEE Table Markdown format.",
    response_model=BenchmarkExportResponse,
)
async def export_benchmark_results(
    response: Response,
    format: ExportFormatEnum = Query(ExportFormatEnum.JSON, description="Output serialization format"),
) -> BenchmarkExportResponse:
    """Generate structured export payload for documentation and academic publication."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return benchmark_service.export_benchmarks(format)
