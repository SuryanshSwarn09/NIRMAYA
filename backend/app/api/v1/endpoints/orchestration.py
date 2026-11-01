"""FastAPI REST router for Container Orchestration Topology, Caddy Ingress & Health Mesh."""

from typing import Any, Dict, List
from fastapi import APIRouter, Response, status

from app.core.container_security import get_container_security_headers
from app.schemas.orchestration import (
    CaddyProxyRouteConfig,
    ComposeAuditReport,
    HealthMeshStatus,
    OrchestrationTopologyManifest,
)
from app.services.orchestration_service import orchestration_service

router = APIRouter()


@router.get(
    "/topology",
    response_model=OrchestrationTopologyManifest,
    summary="Get multi-service Docker Compose topology",
    description="Inspects the full 5-microservice container topology (backend, frontend, postgres, redis, caddy), network isolation, and volume bindings.",
)
async def get_orchestration_topology(response: Response) -> OrchestrationTopologyManifest:
    """Retrieve full container orchestration manifest."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return orchestration_service.get_orchestration_topology()


@router.get(
    "/compose-audit",
    response_model=ComposeAuditReport,
    summary="Audit docker-compose.yml structural compliance",
    description="Statically parses docker-compose.yml validating all 5 service definitions, healthchecks, networks, volumes, and dependency ordering.",
)
async def audit_docker_compose(response: Response) -> ComposeAuditReport:
    """Perform static compliance audit on docker-compose.yml."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return orchestration_service.audit_docker_compose_file()


@router.get(
    "/caddy-audit",
    response_model=Dict[str, Any],
    summary="Audit Caddyfile ingress reverse proxy configuration",
    description="Verifies TLS 1.3 protocol enforcement, WebSocket upgrade paths, REST multiplexing, and security response headers.",
)
async def audit_caddy_configuration(response: Response) -> Dict[str, Any]:
    """Perform static compliance audit on Caddyfile."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return orchestration_service.audit_caddy_configuration()


@router.get(
    "/routes",
    response_model=List[CaddyProxyRouteConfig],
    summary="Get configured Caddy reverse proxy ingress routes",
    description="Lists all path multiplexing rules, target upstream services, WebSocket flags, and security headers.",
)
async def get_caddy_routes(response: Response) -> List[CaddyProxyRouteConfig]:
    """Retrieve Caddy reverse proxy route configurations."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return orchestration_service.get_caddy_route_configs()


@router.get(
    "/health-mesh",
    response_model=HealthMeshStatus,
    summary="Get multi-service health mesh and latency telemetry",
    description="Aggregates live health status and round-trip probe latency across postgres, redis, backend, frontend, and caddy.",
)
async def get_health_mesh(response: Response) -> HealthMeshStatus:
    """Retrieve multi-service cluster health mesh status."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return orchestration_service.get_health_mesh_status()
