"""Pydantic schemas for Static Application Security Testing (SAST),
dependency vulnerability auditing, and multi-tenant database connection pool metrics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SecuritySeverityEnum(str, Enum):
    """Normalized security severity levels aligned with CVSS v3.1."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class SecurityCategoryEnum(str, Enum):
    """Categorization of static code security vulnerabilities and operational risks."""

    INSECURE_CRYPTO = "INSECURE_CRYPTO"
    SQL_INJECTION = "SQL_INJECTION"
    HARDCODED_SECRET = "HARDCODED_SECRET"
    DANGEROUS_CALL = "DANGEROUS_CALL"
    INSECURE_DESERIALIZATION = "INSECURE_DESERIALIZATION"
    PERMISSIVE_CORS = "PERMISSIVE_CORS"
    DEPENDENCY_VULNERABILITY = "DEPENDENCY_VULNERABILITY"


class SASTFinding(BaseModel):
    """Individual static application security testing finding."""

    rule_id: str = Field(..., description="Unique vulnerability rule identifier, e.g. NIRMAYA-SEC-001")
    category: SecurityCategoryEnum = Field(..., description="Vulnerability category classification")
    severity: SecuritySeverityEnum = Field(..., description="Assessed vulnerability severity")
    file_path: Optional[str] = Field(default=None, description="Source file path where vulnerability was discovered")
    line_number: Optional[int] = Field(default=None, description="1-based source code line number")
    col_offset: Optional[int] = Field(default=None, description="Source code column offset")
    code_snippet: Optional[str] = Field(default=None, description="Offending code fragment")
    message: str = Field(..., description="Human-readable explanation of vulnerability risk")
    remediation: str = Field(..., description="Prescriptive guidance to remediate or refactor code")

    model_config = ConfigDict(from_attributes=True)


class DependencyVulnerability(BaseModel):
    """Vulnerability finding identified within application dependencies."""

    package_name: str = Field(..., description="Name of the affected software package")
    installed_version: str = Field(..., description="Currently installed package version")
    fixed_version: Optional[str] = Field(default=None, description="Minimum recommended secure version")
    cve_id: str = Field(..., description="Common Vulnerabilities and Exposures identifier")
    cvss_score: float = Field(..., ge=0.0, le=10.0, description="CVSS 3.1 base metric score")
    severity: SecuritySeverityEnum = Field(..., description="Vulnerability severity category")
    advisory_title: str = Field(..., description="Concise summary title of the security advisory")
    recommendation: str = Field(..., description="Remediation steps for package resolution")

    model_config = ConfigDict(from_attributes=True)


class SASTScanRequest(BaseModel):
    """Input payload to trigger on-demand SAST inspection."""

    code_snippet: Optional[str] = Field(
        default=None,
        description="Raw Python source code snippet to parse and inspect via AST",
    )
    target_path: Optional[str] = Field(
        default=None,
        description="Relative or absolute path to a file or directory for AST static analysis",
    )
    include_severities: Optional[List[SecuritySeverityEnum]] = Field(
        default=None,
        description="Optional filter restricting report to selected severity tiers",
    )

    model_config = ConfigDict(from_attributes=True)


class DependencyScanRequest(BaseModel):
    """Input payload to trigger dependency vulnerability scanning."""

    requirements_text: Optional[str] = Field(
        default=None,
        description="Raw requirements.txt content or pinned package specifications",
    )
    installed_only: bool = Field(
        default=True,
        description="Whether to scan local active Python environment dependencies",
    )

    model_config = ConfigDict(from_attributes=True)


class SecurityScanReport(BaseModel):
    """Aggregated report of SAST code inspection and dependency vulnerability audits."""

    scan_id: str = Field(..., description="Cryptographically random unique scan execution identifier")
    scanned_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of scan execution",
    )
    target_type: str = Field(..., description="Target type scanned (snippet, file, directory, dependencies)")
    files_scanned: int = Field(default=0, ge=0, description="Total source files evaluated")
    total_findings: int = Field(default=0, ge=0, description="Cumulative count of identified issues")
    critical_count: int = Field(default=0, ge=0, description="Count of critical severity findings")
    high_count: int = Field(default=0, ge=0, description="Count of high severity findings")
    medium_count: int = Field(default=0, ge=0, description="Count of medium severity findings")
    low_count: int = Field(default=0, ge=0, description="Count of low severity findings")
    findings: List[SASTFinding] = Field(default_factory=list, description="List of SAST findings")
    dependency_findings: List[DependencyVulnerability] = Field(
        default_factory=list, description="List of dependency vulnerabilities"
    )
    scan_duration_ms: float = Field(..., ge=0.0, description="Execution duration in milliseconds")
    status: str = Field(..., description="Overall assessment status (PASSED, WARNING, FAILED)")

    model_config = ConfigDict(from_attributes=True)


class TenantContextParams(BaseModel):
    """Session tenant parameters injected into PostgreSQL for Row-Level Security (RLS)."""

    tenant_id: str = Field(..., description="Tenant organization or hospital facility UUID")
    user_id: str = Field(..., description="Authenticated user UUID executing the query")
    jurisdiction_path: str = Field(..., description="LGD hierarchical path string, e.g. india.27.492")
    role: Optional[str] = Field(default=None, description="Active user clinical or administrative role")

    model_config = ConfigDict(from_attributes=True)


class DatabasePoolMetrics(BaseModel):
    """Real-time PostgreSQL connection pool operational telemetry."""

    engine_dialect: str = Field(..., description="Database dialect, e.g. postgresql or sqlite")
    pool_size: int = Field(..., description="Configured steady-state connection pool size")
    max_overflow: int = Field(..., description="Configured maximum connection overflow allowance")
    pool_timeout: int = Field(..., description="Connection acquisition timeout in seconds")
    pool_recycle: int = Field(..., description="Connection recycling lifetime in seconds")
    checked_in_connections: int = Field(..., description="Number of idle connections resting in pool")
    checked_out_connections: int = Field(..., description="Number of connections actively leased")
    total_connections: int = Field(..., description="Total active pool plus overflow connections")
    overflow_connections: int = Field(..., description="Number of overflow connections allocated beyond pool_size")
    utilization_rate_percent: float = Field(
        ..., ge=0.0, le=100.0, description="Current connection pool utilization percentage"
    )
    pre_ping_enabled: bool = Field(..., description="Whether pool pre-ping connectivity check is active")
    status: str = Field(..., description="Operational pool status (HEALTHY, WARNING, SATURATED)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of telemetry capture",
    )

    model_config = ConfigDict(from_attributes=True)
