"""FastAPI REST router for Container Runtime Telemetry, Security Auditing & OCI Manifests."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, Response, status

from app.core.container_security import get_container_security_headers
from app.schemas.container_runtime import (
    ContainerRuntimeStatus,
    ContainerSecurityAudit,
    DockerImageManifest,
    EnvironmentConformanceReport,
    FrontendContainerStatus,
    FrontendDockerManifest,
    FrontendSecurityAudit,
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


# -----------------------------------------------------------------------------
# Frontend Next.js Standalone Container Telemetry Endpoints
# -----------------------------------------------------------------------------


@router.get(
    "/frontend/status",
    response_model=FrontendContainerStatus,
    summary="Get Next.js frontend container runtime status",
    description="Inspects Node.js version, process UID (non-root UID 1001), V8 heap memory, RSS, and uptime.",
)
async def get_frontend_container_status(response: Response) -> FrontendContainerStatus:
    """Retrieve frontend runtime and container telemetry."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return container_service.get_frontend_runtime_status()


@router.get(
    "/frontend/manifest",
    response_model=FrontendDockerManifest,
    summary="Get Next.js frontend multi-stage Docker build specification",
    description="Returns the architectural multi-stage Docker manifest for Next.js standalone container (deps, builder, runner).",
)
async def get_frontend_container_manifest(response: Response) -> FrontendDockerManifest:
    """Retrieve frontend container build manifest."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return container_service.get_frontend_docker_manifest()


@router.get(
    "/frontend/security-audit",
    response_model=FrontendSecurityAudit,
    summary="Audit Next.js frontend CIS Docker security compliance",
    description="Evaluates non-root user UID 1001 (nextjs), NODE_ENV production conformance, and static asset caching policies.",
)
async def get_frontend_security_audit(response: Response) -> FrontendSecurityAudit:
    """Audit frontend non-root container security posture."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return container_service.audit_frontend_security_context()


@router.get(
    "/frontend/dockerfile-audit",
    response_model=Dict[str, Any],
    summary="Audit frontend Dockerfile static compliance",
    description="Statically parses frontend/Dockerfile verifying multi-stage build, non-root nextjs user, and OCI healthcheck.",
)
async def get_frontend_dockerfile_audit(response: Response) -> Dict[str, Any]:
    """Statically verify frontend Dockerfile configuration."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return container_service.audit_frontend_dockerfile()
