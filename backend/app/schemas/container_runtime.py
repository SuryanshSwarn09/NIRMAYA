"""Pydantic v2 schemas for Container Runtime Telemetry, Environment Conformance & OCI Manifests.

Provides structured models for:
- Container execution environment inspection (UID, GID, cgroup memory, OS release)
- CIS Docker Benchmark security context compliance (non-root UID 10001 enforcement)
- Production environment variable security auditing & configuration scoring
- Multi-stage Docker image build specification & layering manifests
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ContainerExecutionMode(str, Enum):
    """Runtime execution environment classification."""

    CONTAINERIZED = "containerized"
    STANDALONE_HOST = "standalone_host"
    TEST_RUNNER = "test_runner"


class SecurityComplianceLevel(str, Enum):
    """CIS Docker security context audit classification."""

    STRICT_NON_ROOT = "strict_non_root"
    STANDARD = "standard"
    WARNING_ROOT = "warning_root"
    NON_COMPLIANT = "non_compliant"


class ContainerRuntimeStatus(BaseModel):
    """Telemetry report describing the running backend container or host process."""

    model_config = ConfigDict(from_attributes=True)

    execution_mode: ContainerExecutionMode = Field(
        ...,
        description="Runtime containerization classification",
    )
    is_container: bool = Field(
        ...,
        description="Whether process is executing inside an OCI container cgroup",
    )
    process_uid: int = Field(
        ...,
        description="Host or container process User ID (must be non-zero in production)",
    )
    process_gid: int = Field(
        ...,
        description="Process Group ID",
    )
    is_non_root: bool = Field(
        ...,
        description="True if running under an unprivileged user (UID != 0)",
    )
    python_version: str = Field(
        ...,
        description="Installed Python runtime version",
    )
    os_platform: str = Field(
        ...,
        description="Host operating system name and architecture",
    )
    hostname: str = Field(
        ...,
        description="Container hostname or system machine identifier",
    )
    allocated_memory_mb: Optional[float] = Field(
        None,
        description="Cgroup memory limit in megabytes if constrained",
    )
    active_workers: int = Field(
        1,
        description="Configured Uvicorn worker concurrency count",
    )
    uptime_seconds: float = Field(
        ...,
        description="Seconds elapsed since process startup",
    )


class ContainerSecurityAudit(BaseModel):
    """Security audit evaluating container compliance against CIS Docker Benchmarks."""

    model_config = ConfigDict(from_attributes=True)

    compliance_level: SecurityComplianceLevel = Field(
        ...,
        description="Overall CIS security context evaluation level",
    )
    is_root: bool = Field(
        ...,
        description="Flag indicating if the process is executing as root (UID 0)",
    )
    uid_assigned: int = Field(
        ...,
        description="Assigned process User ID",
    )
    user_name: str = Field(
        ...,
        description="Configured OS username (e.g. 'nirmaya')",
    )
    read_only_rootfs: bool = Field(
        False,
        description="Whether root filesystem is mounted read-only",
    )
    seccomp_enabled: bool = Field(
        True,
        description="Whether default Docker seccomp filtering is active",
    )
    security_findings: List[str] = Field(
        default_factory=list,
        description="List of detected security findings or compliance advisories",
    )
    cis_benchmark_score_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="CIS benchmark security compliance score percentage",
    )


class EnvironmentVariableCheck(BaseModel):
    """Validation result for an individual runtime environment configuration variable."""

    model_config = ConfigDict(from_attributes=True)

    variable_name: str = Field(
        ...,
        description="Name of the environment variable (e.g. 'DATABASE_URL')",
    )
    is_configured: bool = Field(
        ...,
        description="True if variable is set in the runtime environment",
    )
    is_sensitive: bool = Field(
        ...,
        description="True if variable contains credentials and must be masked",
    )
    masked_value: str = Field(
        ...,
        description="Sanitized value safe for display in administrative dashboards",
    )
    status: str = Field(
        ...,
        description="Status indicator ('PASS', 'WARN_DEFAULT', 'MISSING_OPTIONAL', 'FAIL_REQUIRED')",
    )
    description: str = Field(
        ...,
        description="Human-readable explanation of the variable's purpose",
    )


class EnvironmentConformanceReport(BaseModel):
    """Consolidated environment configuration audit report."""

    model_config = ConfigDict(from_attributes=True)

    conformance_score_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall environment compliance score (100% indicates full production readiness)",
    )
    total_variables_checked: int = Field(
        ...,
        description="Total configuration variables audited",
    )
    compliant_count: int = Field(
        ...,
        description="Count of variables meeting strict production standards",
    )
    warning_count: int = Field(
        ...,
        description="Count of variables using development defaults",
    )
    critical_count: int = Field(
        ...,
        description="Count of required variables missing or insecure",
    )
    status: str = Field(
        ...,
        description="Status classification ('READY_PRODUCTION', 'WARNINGS_PRESENT', 'INSECURE_CONFIGURATION')",
    )
    checks: List[EnvironmentVariableCheck] = Field(
        default_factory=list,
        description="Detailed variable-by-variable validation breakdown",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of environment conformance evaluation",
    )


class DockerStageManifest(BaseModel):
    """Specification describing a single stage in a multi-stage Docker build."""

    model_config = ConfigDict(from_attributes=True)

    stage_name: str = Field(
        ...,
        description="Identifier of build stage (e.g. 'builder' or 'runtime')",
    )
    base_image: str = Field(
        ...,
        description="Base image identifier (e.g. 'python:3.12-alpine')",
    )
    purpose: str = Field(
        ...,
        description="Role of this stage in the container build pipeline",
    )
    approx_layer_count: int = Field(
        ...,
        description="Estimated layer count for this stage",
    )
    cached_artifacts: List[str] = Field(
        default_factory=list,
        description="Key output artifacts or virtual environments produced",
    )


class DockerImageManifest(BaseModel):
    """OCI container image specification and architectural manifest."""

    model_config = ConfigDict(from_attributes=True)

    image_name: str = Field(
        "nirmaya-backend",
        description="Repository name for container image",
    )
    tag: str = Field(
        "v0.4.0",
        description="Target image version tag",
    )
    architectures: List[str] = Field(
        default_factory=lambda: ["linux/amd64", "linux/arm64"],
        description="Supported OCI CPU architectures",
    )
    stages: List[DockerStageManifest] = Field(
        default_factory=list,
        description="Multi-stage build steps",
    )
    target_image_size_mb: float = Field(
        118.5,
        description="Target production compressed image size footprint in megabytes",
    )
    non_root_uid: int = Field(
        10001,
        description="Configured unprivileged system user ID",
    )
    non_root_group: str = Field(
        "nirmaya",
        description="Configured unprivileged system group",
    )
    healthcheck_endpoint: str = Field(
        "/api/v1/health",
        description="Target URL path probed by Docker daemon",
    )
    healthcheck_interval_seconds: int = Field(
        30,
        description="Frequency of healthcheck probe in seconds",
    )
    exposed_ports: List[int] = Field(
        default_factory=lambda: [8000],
        description="TCP ports exposed by container",
    )
    entrypoint_command: str = Field(
        "/app/docker-entrypoint.sh",
        description="Container initialization command",
    )


class FrontendExecutionMode(str, Enum):
    """Next.js frontend runtime execution environment classification."""

    CONTAINERIZED = "containerized"
    STANDALONE_HOST = "standalone_host"
    DEVELOPMENT = "development"
    TEST_RUNNER = "test_runner"


class FrontendContainerStatus(BaseModel):
    """Telemetry report describing the running Next.js frontend container or host process."""

    model_config = ConfigDict(from_attributes=True)

    execution_mode: FrontendExecutionMode = Field(
        ...,
        description="Frontend runtime containerization classification",
    )
    is_container: bool = Field(
        ...,
        description="Whether frontend is executing inside an OCI container cgroup",
    )
    is_standalone: bool = Field(
        True,
        description="Whether Next.js output standalone traced server is active",
    )
    node_version: str = Field(
        ...,
        description="Node.js engine version (e.g. 'v20.18.0')",
    )
    process_uid: int = Field(
        ...,
        description="Host or container process User ID (must be non-zero in production)",
    )
    process_gid: int = Field(
        ...,
        description="Process Group ID",
    )
    is_non_root: bool = Field(
        ...,
        description="True if running under an unprivileged user (UID != 0, e.g. UID 1001 nextjs)",
    )
    memory_rss_mb: float = Field(
        ...,
        description="Resident Set Size memory allocation in megabytes",
    )
    memory_heap_total_mb: float = Field(
        ...,
        description="V8 total heap allocation in megabytes",
    )
    memory_heap_used_mb: float = Field(
        ...,
        description="V8 used heap in megabytes",
    )
    uptime_seconds: float = Field(
        ...,
        description="Seconds elapsed since Next.js server startup",
    )
    static_cache_enabled: bool = Field(
        True,
        description="Whether immutable static caching headers are active for /_next/static",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of telemetry evaluation",
    )


class FrontendDockerManifest(BaseModel):
    """OCI container image specification for Next.js 15 standalone frontend image."""

    model_config = ConfigDict(from_attributes=True)

    image_name: str = Field(
        "nirmaya-frontend",
        description="Repository name for frontend container image",
    )
    tag: str = Field(
        "v0.4.0",
        description="Target image version tag",
    )
    base_image: str = Field(
        "node:20-alpine",
        description="Base Alpine Node.js distribution",
    )
    architectures: List[str] = Field(
        default_factory=lambda: ["linux/amd64", "linux/arm64"],
        description="Supported OCI CPU architectures",
    )
    stages: List[DockerStageManifest] = Field(
        default_factory=list,
        description="Multi-stage build steps (deps, builder, runner)",
    )
    target_image_size_mb: float = Field(
        145.0,
        description="Target production compressed image size footprint in megabytes (< 150MB)",
    )
    non_root_uid: int = Field(
        1001,
        description="Configured unprivileged system user ID (UID 1001 nextjs)",
    )
    non_root_gid: int = Field(
        1001,
        description="Configured unprivileged system group ID (GID 1001 nodejs)",
    )
    non_root_user: str = Field(
        "nextjs",
        description="Configured unprivileged system username",
    )
    non_root_group: str = Field(
        "nodejs",
        description="Configured unprivileged system group name",
    )
    healthcheck_endpoint: str = Field(
        "/api/health",
        description="Target URL path probed by Docker daemon or load balancer",
    )
    healthcheck_interval_seconds: int = Field(
        30,
        description="Frequency of healthcheck probe in seconds",
    )
    exposed_ports: List[int] = Field(
        default_factory=lambda: [3000],
        description="TCP ports exposed by frontend container",
    )
    output_mode: str = Field(
        "standalone",
        description="Next.js output compilation mode",
    )
    cache_control_static: str = Field(
        "public, max-age=31536000, immutable",
        description="Cache-Control header applied to static assets",
    )
    entrypoint_command: str = Field(
        "node server.js",
        description="Next.js standalone production server execution command",
    )


class FrontendSecurityAudit(BaseModel):
    """CIS Docker benchmark evaluation for Next.js frontend container."""

    model_config = ConfigDict(from_attributes=True)

    compliance_level: SecurityComplianceLevel = Field(
        ...,
        description="Overall CIS security context evaluation level",
    )
    is_root: bool = Field(
        ...,
        description="Flag indicating if frontend process is executing as root (UID 0)",
    )
    uid_assigned: int = Field(
        ...,
        description="Assigned process User ID",
    )
    user_name: str = Field(
        ...,
        description="Configured OS username (e.g. 'nextjs')",
    )
    node_env: str = Field(
        "production",
        description="Configured NODE_ENV environment variable",
    )
    read_only_rootfs: bool = Field(
        False,
        description="Whether root filesystem is mounted read-only",
    )
    security_findings: List[str] = Field(
        default_factory=list,
        description="List of detected security findings or compliance advisories",
    )
    cis_benchmark_score_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="CIS benchmark security compliance score percentage",
    )
