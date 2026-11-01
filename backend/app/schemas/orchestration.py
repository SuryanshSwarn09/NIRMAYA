"""Pydantic v2 schemas for Docker Compose Multi-Service Topology & Caddy Reverse Proxy.

Provides structured models for:
- Multi-service topology nodes (FastAPI, Next.js, PostgreSQL 16, Redis 7, Caddy)
- Docker Compose specification auditing and dependency ordering
- Caddy reverse proxy routing rules and TLS 1.3 security parameters
- Real-time container health mesh and inter-service latency tracking
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ServiceStatusEnum(str, Enum):
    """Runtime health status of an orchestrated container service."""

    HEALTHY = "healthy"
    STARTING = "starting"
    DEGRADED = "degraded"
    STOPPED = "stopped"


class ServiceTopologyNode(BaseModel):
    """Specification and runtime telemetry for a single container service in the topology."""

    model_config = ConfigDict(from_attributes=True)

    service_name: str = Field(
        ...,
        description="Logical service identifier in docker-compose.yml (e.g. 'backend')",
    )
    container_name: str = Field(
        ...,
        description="Assigned OCI container name (e.g. 'nirmaya-api')",
    )
    image: str = Field(
        ...,
        description="Docker image identifier or build context tag",
    )
    exposed_ports: List[int] = Field(
        default_factory=list,
        description="Ports published to the host machine",
    )
    internal_ports: List[int] = Field(
        default_factory=list,
        description="Ports exposed only inside the isolated Docker network",
    )
    depends_on: List[str] = Field(
        default_factory=list,
        description="Service dependencies with healthy status prerequisites",
    )
    healthcheck_command: str = Field(
        ...,
        description="Command executed to determine service health",
    )
    healthcheck_interval_seconds: int = Field(
        30,
        description="Probe frequency in seconds",
    )
    volumes: List[str] = Field(
        default_factory=list,
        description="Volume mounts and persistent storage paths",
    )
    restart_policy: str = Field(
        "unless-stopped",
        description="Container failure recovery policy",
    )
    status: ServiceStatusEnum = Field(
        ServiceStatusEnum.HEALTHY,
        description="Current runtime health classification",
    )


class OrchestrationTopologyManifest(BaseModel):
    """Architectural manifest defining the full multi-service Docker Compose deployment."""

    model_config = ConfigDict(from_attributes=True)

    project_name: str = Field(
        "nirmaya",
        description="Compose project namespace",
    )
    compose_version: str = Field(
        "3.8",
        description="Docker Compose file format specification",
    )
    network_name: str = Field(
        "nirmaya-net",
        description="Isolated bridge network interconnecting all services",
    )
    isolated_network: bool = Field(
        True,
        description="Whether inter-container communication is restricted to an isolated bridge",
    )
    services: List[ServiceTopologyNode] = Field(
        default_factory=list,
        description="List of orchestrated service definitions",
    )
    persistent_volumes: List[str] = Field(
        default_factory=lambda: ["postgres_data", "redis_data", "caddy_data", "caddy_config"],
        description="Named persistent volumes preventing data loss across restarts",
    )
    restart_policy: str = Field(
        "unless-stopped",
        description="Global service restart policy",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Evaluation timestamp",
    )


class CaddyProxyRouteConfig(BaseModel):
    """Specification for an ingress reverse proxy route managed by Caddy."""

    model_config = ConfigDict(from_attributes=True)

    route_id: str = Field(
        ...,
        description="Identifier of the routing rule",
    )
    path_prefix: str = Field(
        ...,
        description="URL path pattern matched by Caddy (e.g. '/api/*')",
    )
    upstream_service: str = Field(
        ...,
        description="Target internal hostname (e.g. 'backend')",
    )
    upstream_port: int = Field(
        ...,
        description="Target internal port (e.g. 8000)",
    )
    supports_websocket: bool = Field(
        False,
        description="Whether HTTP/1.1 Upgrade headers are forwarded for real-time WebSockets",
    )
    tls_version: str = Field(
        "TLS 1.3",
        description="Configured minimum TLS encryption standard",
    )
    compression_enabled: bool = Field(
        True,
        description="Whether zstd and gzip response encoding is active",
    )
    security_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Enterprise HTTP security headers injected on response",
    )


class HealthMeshNode(BaseModel):
    """Live probe telemetry for an individual microservice node."""

    model_config = ConfigDict(from_attributes=True)

    service_name: str = Field(
        ...,
        description="Target microservice name",
    )
    is_healthy: bool = Field(
        ...,
        description="True if service passed last healthcheck probe",
    )
    status: str = Field(
        ...,
        description="Detailed status string (e.g. 'PASS (HTTP 200)' or 'PONG')",
    )
    latency_ms: float = Field(
        ...,
        description="Internal probe response latency in milliseconds",
    )
    last_probe_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last successful probe",
    )


class HealthMeshStatus(BaseModel):
    """Aggregated health status across the entire multi-service mesh."""

    model_config = ConfigDict(from_attributes=True)

    is_mesh_healthy: bool = Field(
        ...,
        description="True if all critical service nodes are healthy",
    )
    total_services: int = Field(
        ...,
        description="Total monitored service nodes",
    )
    healthy_services: int = Field(
        ...,
        description="Count of currently healthy service nodes",
    )
    mesh_latency_ms: float = Field(
        ...,
        description="Average round-trip probe latency across the mesh",
    )
    nodes: List[HealthMeshNode] = Field(
        default_factory=list,
        description="Node-by-node probe telemetry breakdown",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Evaluation timestamp",
    )


class ComposeAuditReport(BaseModel):
    """Static and structural compliance audit of docker-compose.yml."""

    model_config = ConfigDict(from_attributes=True)

    is_valid: bool = Field(
        ...,
        description="True if compose file satisfies all structural requirements",
    )
    compliance_score_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Orchestration security and resilience score percentage",
    )
    services_detected: List[str] = Field(
        default_factory=list,
        description="Names of services discovered in compose specification",
    )
    networks_configured: List[str] = Field(
        default_factory=list,
        description="Configured Docker networks",
    )
    volumes_configured: List[str] = Field(
        default_factory=list,
        description="Configured named persistent volumes",
    )
    healthchecks_coverage_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of services with active healthcheck definitions",
    )
    security_findings: List[str] = Field(
        default_factory=list,
        description="List of security observations and compliance findings",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Evaluation timestamp",
    )
