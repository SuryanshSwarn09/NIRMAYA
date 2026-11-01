"""Unit and integration test suite for Docker Compose Multi-Service Topology & Caddy Reverse Proxy.

Verifies:
- docker-compose.yml structural compliance, service definitions, healthchecks, and dependency graphs
- Caddyfile ingress routing, TLS 1.3 protocol enforcement, and WebSocket upgrade forwarding
- .env.production.example cryptographic configuration blueprint
- Orchestration topology inspector, Caddy auditor, and health mesh telemetry
- REST API endpoints under /api/v1/admin/orchestration/*
"""

import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.orchestration import (
    ComposeAuditReport,
    HealthMeshStatus,
    OrchestrationTopologyManifest,
    ServiceStatusEnum,
)
from app.services.orchestration_service import orchestration_service


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide synchronous TestClient for orchestration REST API testing."""
    with TestClient(app) as test_client:
        yield test_client


# -----------------------------------------------------------------------------
# 1. Orchestration Topology & Spec Tests
# -----------------------------------------------------------------------------


def test_orchestration_topology_structure():
    """Verify orchestration topology manifest contains all 5 required services."""
    manifest = orchestration_service.get_orchestration_topology()
    assert isinstance(manifest, OrchestrationTopologyManifest)
    assert manifest.project_name == "nirmaya"
    assert manifest.compose_version == "3.8"
    assert manifest.network_name == "nirmaya-net"
    assert manifest.isolated_network is True
    assert len(manifest.services) == 5

    service_names = [s.service_name for s in manifest.services]
    assert "postgres" in service_names
    assert "redis" in service_names
    assert "backend" in service_names
    assert "frontend" in service_names
    assert "caddy" in service_names

    # Verify volumes
    assert "postgres_data" in manifest.persistent_volumes
    assert "redis_data" in manifest.persistent_volumes
    assert "caddy_data" in manifest.persistent_volumes


def test_health_mesh_telemetry():
    """Verify health mesh status aggregates all 5 nodes and computes average latency."""
    mesh = orchestration_service.get_health_mesh_status()
    assert isinstance(mesh, HealthMeshStatus)
    assert mesh.is_mesh_healthy is True
    assert mesh.total_services == 5
    assert mesh.healthy_services == 5
    assert mesh.mesh_latency_ms > 0
    assert len(mesh.nodes) == 5


def test_caddy_route_configs():
    """Verify configured Caddy route rules include WebSockets, REST API, and Frontend."""
    routes = orchestration_service.get_caddy_route_configs()
    assert len(routes) == 3

    ws_route = next(r for r in routes if r.path_prefix == "/ws/*")
    assert ws_route.upstream_service == "backend"
    assert ws_route.upstream_port == 8000
    assert ws_route.supports_websocket is True
    assert ws_route.tls_version == "TLS 1.3"

    api_route = next(r for r in routes if r.path_prefix == "/api/*")
    assert api_route.upstream_service == "backend"
    assert api_route.upstream_port == 8000
    assert api_route.supports_websocket is False

    fe_route = next(r for r in routes if r.path_prefix == "/*")
    assert fe_route.upstream_service == "frontend"
    assert fe_route.upstream_port == 3000


# -----------------------------------------------------------------------------
# 2. Static File Auditing Tests
# -----------------------------------------------------------------------------


def test_docker_compose_static_audit():
    """Verify static analysis of docker-compose.yml verifies all services and healthchecks."""
    report = orchestration_service.audit_docker_compose_file()
    assert isinstance(report, ComposeAuditReport)
    assert report.is_valid is True
    assert report.compliance_score_pct == 100.0
    assert report.healthchecks_coverage_pct == 100.0
    assert len(report.services_detected) == 5
    assert "nirmaya-net" in report.networks_configured
    assert len(report.volumes_configured) == 4
    assert any("condition: service_healthy" in f for f in report.security_findings)


def test_docker_compose_missing_file_handling():
    """Verify audit_docker_compose_file handles non-existent paths gracefully."""
    report = orchestration_service.audit_docker_compose_file("/missing/docker-compose.yml")
    assert report.is_valid is False
    assert report.compliance_score_pct == 0.0
    assert len(report.services_detected) == 0


def test_caddyfile_static_audit():
    """Verify static analysis of Caddyfile confirms TLS 1.3 and reverse proxy rules."""
    result = orchestration_service.audit_caddy_configuration()
    assert result["exists"] is True
    assert result["compliance_score_pct"] == 100.0
    assert result["has_tls_1_3"] is True
    assert result["has_websocket_routing"] is True
    assert result["has_api_routing"] is True
    assert result["has_frontend_routing"] is True
    assert result["has_compression"] is True
    assert result["has_security_headers"] is True


def test_caddyfile_missing_file_handling():
    """Verify audit_caddy_configuration handles non-existent paths gracefully."""
    result = orchestration_service.audit_caddy_configuration("/missing/Caddyfile")
    assert result["exists"] is False
    assert result["compliance_score_pct"] == 0.0


def test_env_production_example_structure():
    """Verify .env.production.example contains all required environment keys."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    env_example_path = os.path.join(base_dir, ".env.production.example")
    assert os.path.exists(env_example_path)

    with open(env_example_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "POSTGRES_DB=" in content
    assert "POSTGRES_USER=" in content
    assert "POSTGRES_PASSWORD=" in content
    assert "REDIS_PASSWORD=" in content
    assert "SECRET_KEY=" in content
    assert "DOMAIN_NAME=" in content
    assert "CORS_ORIGINS=" in content


# -----------------------------------------------------------------------------
# 3. REST API Endpoint Integration Tests
# -----------------------------------------------------------------------------


def test_rest_api_topology(client: TestClient):
    """Verify GET /api/v1/admin/orchestration/topology returns 200 and full manifest."""
    response = client.get("/api/v1/admin/orchestration/topology")
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "nirmaya"
    assert data["network_name"] == "nirmaya-net"
    assert len(data["services"]) == 5
    assert response.headers.get("X-Security-Standard") is not None


def test_rest_api_compose_audit(client: TestClient):
    """Verify GET /api/v1/admin/orchestration/compose-audit returns 200 and audit."""
    response = client.get("/api/v1/admin/orchestration/compose-audit")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["compliance_score_pct"] == 100.0
    assert len(data["services_detected"]) == 5


def test_rest_api_caddy_audit(client: TestClient):
    """Verify GET /api/v1/admin/orchestration/caddy-audit returns 200 and Caddy audit."""
    response = client.get("/api/v1/admin/orchestration/caddy-audit")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["has_tls_1_3"] is True
    assert data["compliance_score_pct"] == 100.0


def test_rest_api_routes(client: TestClient):
    """Verify GET /api/v1/admin/orchestration/routes returns 200 and route list."""
    response = client.get("/api/v1/admin/orchestration/routes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    paths = [r["path_prefix"] for r in data]
    assert "/ws/*" in paths
    assert "/api/*" in paths


def test_rest_api_health_mesh(client: TestClient):
    """Verify GET /api/v1/admin/orchestration/health-mesh returns 200 and mesh telemetry."""
    response = client.get("/api/v1/admin/orchestration/health-mesh")
    assert response.status_code == 200
    data = response.json()
    assert data["is_mesh_healthy"] is True
    assert data["total_services"] == 5
    assert data["healthy_services"] == 5
    assert len(data["nodes"]) == 5


def test_caddy_websocket_upgrade_contract():
    """Verify WebSocket upgrade contract in Caddy routing rule."""
    routes = orchestration_service.get_caddy_route_configs()
    ws_route = next(r for r in routes if r.path_prefix == "/ws/*")
    assert ws_route.supports_websocket is True
    assert "Strict-Transport-Security" in ws_route.security_headers

