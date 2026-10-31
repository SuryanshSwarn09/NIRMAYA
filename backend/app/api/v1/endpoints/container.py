"""FastAPI REST router for Container Runtime Telemetry, Security Auditing & OCI Manifests."""

from fastapi import APIRouter, Depends, Response, status

from app.core.container_security import get_container_security_headers
from app.schemas.container_runtime import (
    ContainerRuntimeStatus,
    ContainerSecurityAudit,
    DockerImageManifest,
    EnvironmentConformanceReport,
)
from app.services.container_service import container_service

router = APIRouter()


@router.get(
    "/status",
    response_model=ContainerRuntimeStatus,
    summary="Get container runtime environment status",
    description="Inspects live container cgroup execution, process UID/GID, memory constraints, and worker concurrency.",
)
async def get_container_status(response: Response) -> ContainerRuntimeStatus:
    """Retrieve runtime process and container telemetry."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return container_service.get_runtime_status()


@router.get(
    "/security-audit",
    response_model=ContainerSecurityAudit,
    summary="Audit CIS Docker Benchmark 4.1 security compliance",
    description="Evaluates process privileges, non-root execution (UID 10001), and container isolation posture.",
)
async def get_container_security_audit(response: Response) -> ContainerSecurityAudit:
    """Audit non-root container security posture."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return container_service.audit_security_context()


@router.get(
    "/manifest",
    response_model=DockerImageManifest,
    summary="Get multi-stage Docker build specification",
    description="Returns the architectural multi-stage Docker image manifest including builder and runtime layer topologies.",
)
async def get_container_manifest(response: Response) -> DockerImageManifest:
    """Retrieve container image layering and build manifest."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return container_service.get_build_manifest()


@router.get(
    "/validate-env",
    response_model=EnvironmentConformanceReport,
    summary="Audit production environment configuration conformance",
    description="Evaluates environment variables against security standards, verifying secret entropy, database hygiene, and Redis connectivity.",
)
@router.post(
    "/validate-env",
    response_model=EnvironmentConformanceReport,
    summary="Audit production environment configuration conformance (POST)",
    description="Evaluates environment variables against security standards, verifying secret entropy, database hygiene, and Redis connectivity.",
    include_in_schema=False,
)
async def validate_environment(response: Response) -> EnvironmentConformanceReport:
    """Perform production environment conformance check."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return container_service.validate_environment()
