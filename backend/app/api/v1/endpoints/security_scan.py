"""REST endpoints for Static Application Security Testing (SAST),
automated dependency vulnerability auditing, and database connection pool telemetry.
"""

import os
from fastapi import APIRouter, HTTPException, Query, status

from app.db.session import get_pool_metrics
from app.schemas.security_scanner import (
    DatabasePoolMetrics,
    DependencyScanRequest,
    SASTScanRequest,
    SecurityScanReport,
)
from app.services.dependency_scanner import dependency_scanner_service
from app.services.security_scanner import security_scanner_service

router = APIRouter()


@router.post(
    "/scan/sast",
    response_model=SecurityScanReport,
    summary="Trigger on-demand AST Static Application Security Testing (SAST)",
    description="Parses Python source code AST to detect insecure cryptography, SQL injection, hardcoded secrets, and dangerous system calls.",
)
def run_sast_scan(request: SASTScanRequest) -> SecurityScanReport:
    """Execute AST-based static application security analysis."""
    if request.code_snippet:
        return security_scanner_service.scan_snippet(
            code_snippet=request.code_snippet,
            file_path="snippet.py",
            include_severities=request.include_severities,
        )

    target_path = request.target_path
    if not target_path:
        # Default to backend app directory relative to project root
        candidate = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        target_path = candidate if os.path.exists(candidate) else "."

    if os.path.isfile(target_path):
        return security_scanner_service.scan_file(
            file_path=target_path,
            include_severities=request.include_severities,
        )
    elif os.path.isdir(target_path):
        return security_scanner_service.scan_directory(
            directory_path=target_path,
            include_severities=request.include_severities,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target path '{target_path}' does not exist on filesystem.",
        )


@router.post(
    "/scan/dependencies",
    response_model=SecurityScanReport,
    summary="Trigger automated dependency vulnerability audit",
    description="Cross-references pinned dependencies or runtime packages against known CVE advisories and calculates CVSS severities.",
)
def run_dependency_scan(request: DependencyScanRequest) -> SecurityScanReport:
    """Execute automated CVE vulnerability scan across requirements or installed packages."""
    if request.requirements_text:
        return dependency_scanner_service.generate_dependency_report(
            requirements_content=request.requirements_text,
            scan_installed=False,
        )
    return dependency_scanner_service.generate_dependency_report(
        scan_installed=request.installed_only
    )


@router.get(
    "/pool/status",
    response_model=DatabasePoolMetrics,
    summary="Retrieve PostgreSQL connection pool operational telemetry",
    description="Inspects active connection count, idle connections, overflow, and pool capacity utilization.",
)
def get_database_pool_status() -> DatabasePoolMetrics:
    """Collect real-time database connection pool telemetry."""
    return get_pool_metrics()
