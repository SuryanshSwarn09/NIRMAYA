"""Unit and integration test suite for Next.js 15 frontend containerization and runtime telemetry.

Verifies:
- Next.js standalone output configuration in next.config.ts
- Multi-stage Dockerfile architecture (deps, builder, runner) and CIS 4.1 non-root context (UID 1001)
- Context boundary exclusions in frontend/.dockerignore
- Frontend container runtime telemetry service and configuration auditors
- CIS benchmark scoring and root privilege warning guards
- REST API endpoints under /api/v1/admin/container/frontend/*
- Frontend health check schema specification
"""

import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.container_runtime import (
    FrontendContainerStatus,
    FrontendDockerManifest,
    FrontendExecutionMode,
    FrontendSecurityAudit,
    SecurityComplianceLevel,
)
from app.services.container_service import container_service


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide synchronous TestClient for container REST API testing."""
    with TestClient(app) as test_client:
        yield test_client


# -----------------------------------------------------------------------------
# 1. Frontend Docker Manifest & Spec Tests
# -----------------------------------------------------------------------------


def test_frontend_docker_manifest_structure():
    """Verify frontend Docker manifest contains required multi-stage specifications."""
    manifest = container_service.get_frontend_docker_manifest()
    assert isinstance(manifest, FrontendDockerManifest)
    assert manifest.image_name == "nirmaya-frontend"
    assert manifest.base_image == "node:20-alpine"
    assert manifest.tag == "v0.4.0"
    assert manifest.target_image_size_mb <= 150.0
    assert manifest.non_root_uid == 1001
    assert manifest.non_root_gid == 1001
    assert manifest.non_root_user == "nextjs"
    assert manifest.non_root_group == "nodejs"
    assert manifest.output_mode == "standalone"
    assert manifest.healthcheck_endpoint == "/api/health"
    assert 3000 in manifest.exposed_ports
    assert manifest.entrypoint_command == "node server.js"

    # Verify 3 stages
    stage_names = [s.stage_name for s in manifest.stages]
    assert stage_names == ["deps", "builder", "runner"]


def test_frontend_runtime_status_defaults():
    """Verify default runtime status models unprivileged execution and V8 memory metrics."""
    status = container_service.get_frontend_runtime_status()
    assert isinstance(status, FrontendContainerStatus)
    assert status.is_standalone is True
    assert status.is_non_root is True
    assert status.process_uid == 1001
    assert status.process_gid == 1001
    assert "v20" in status.node_version or "v" in status.node_version
    assert status.memory_rss_mb > 0
    assert status.memory_heap_total_mb > 0
    assert status.memory_heap_used_mb > 0
    assert status.static_cache_enabled is True
    assert status.uptime_seconds >= 0


def test_frontend_security_audit_non_root():
    """Verify CIS benchmark security evaluation achieves 100% compliance when non-root."""
    audit = container_service.audit_frontend_security_context()
    assert isinstance(audit, FrontendSecurityAudit)
    assert audit.compliance_level == SecurityComplianceLevel.STRICT_NON_ROOT
    assert audit.is_root is False
    assert audit.uid_assigned == 1001
    assert audit.user_name == "nextjs"
    assert audit.cis_benchmark_score_pct == 100.0
    assert any("UID 1001" in f for f in audit.security_findings)


def test_frontend_security_audit_root_warning(monkeypatch):
    """Verify security guard detects root privilege and downgrades compliance score."""
    monkeypatch.setenv("NIRMAYA_FRONTEND_UID", "0")
    audit = container_service.audit_frontend_security_context()
    assert audit.is_root is True
    assert audit.uid_assigned == 0
    assert audit.user_name == "root"
    assert audit.compliance_level == SecurityComplianceLevel.WARNING_ROOT
    assert audit.cis_benchmark_score_pct < 60.0
    assert any("Violation of CIS Benchmark 4.1" in f for f in audit.security_findings)


def test_frontend_execution_mode_override(monkeypatch):
    """Verify explicit NIRMAYA_FRONTEND_MODE environment override."""
    monkeypatch.setenv("NIRMAYA_FRONTEND_MODE", "development")
    status = container_service.get_frontend_runtime_status()
    assert status.execution_mode == FrontendExecutionMode.DEVELOPMENT


# -----------------------------------------------------------------------------
# 2. Static Configuration & File Auditing Tests
# -----------------------------------------------------------------------------


def test_frontend_dockerfile_static_audit():
    """Verify static analysis of frontend/Dockerfile checks multi-stage and CIS rules."""
    result = container_service.audit_frontend_dockerfile()
    assert result["exists"] is True
    assert result["is_multi_stage"] is True
    assert "deps" in result["stages_found"]
    assert "builder" in result["stages_found"]
    assert "runner" in result["stages_found"]
    assert result["has_non_root_user"] is True
    assert result["has_healthcheck"] is True
    assert result["has_standalone_copy"] is True
    assert result["compliance_score_pct"] == 100.0


def test_frontend_dockerfile_missing_handling():
    """Verify audit_frontend_dockerfile handles non-existent paths gracefully."""
    result = container_service.audit_frontend_dockerfile("/path/to/missing/Dockerfile")
    assert result["exists"] is False
    assert result["compliance_score_pct"] == 0.0
    assert result["is_multi_stage"] is False


def test_frontend_dockerignore_structure():
    """Verify frontend/.dockerignore excludes sensitive and unneeded directories."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dockerignore_path = os.path.join(base_dir, "frontend", ".dockerignore")
    assert os.path.exists(dockerignore_path)

    with open(dockerignore_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "node_modules" in content
    assert ".next" in content
    assert ".git" in content
    assert ".env" in content


def test_next_config_standalone_setting():
    """Verify frontend/next.config.ts enables standalone output and caching."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    next_config_path = os.path.join(base_dir, "frontend", "next.config.ts")
    assert os.path.exists(next_config_path)

    with open(next_config_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'output: "standalone"' in content or "output: 'standalone'" in content
    assert "poweredByHeader: false" in content
    assert "compress: true" in content
    assert "max-age=31536000, immutable" in content


def test_frontend_health_route_exists():
    """Verify frontend/src/app/api/health/route.ts exists and declares force-dynamic."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    route_path = os.path.join(base_dir, "frontend", "src", "app", "api", "health", "route.ts")
    assert os.path.exists(route_path)

    with open(route_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'export const dynamic = "force-dynamic"' in content
    assert "status: 200" in content
    assert "nirmaya-frontend" in content


# -----------------------------------------------------------------------------
# 3. REST API Endpoint Integration Tests
# -----------------------------------------------------------------------------


def test_rest_api_frontend_status(client: TestClient):
    """Verify GET /api/v1/admin/container/frontend/status returns 200 and telemetry."""
    response = client.get("/api/v1/admin/container/frontend/status")
    assert response.status_code == 200
    data = response.json()
    assert data["is_standalone"] is True
    assert data["process_uid"] == 1001
    assert data["is_non_root"] is True
    assert "memory_rss_mb" in data
    assert "memory_heap_total_mb" in data
    assert "memory_heap_used_mb" in data
    assert response.headers.get("X-Security-Standard") == "CIS-Docker-4.1-Compliant"


def test_rest_api_frontend_manifest(client: TestClient):
    """Verify GET /api/v1/admin/container/frontend/manifest returns 200 and build spec."""
    response = client.get("/api/v1/admin/container/frontend/manifest")
    assert response.status_code == 200
    data = response.json()
    assert data["image_name"] == "nirmaya-frontend"
    assert data["base_image"] == "node:20-alpine"
    assert data["target_image_size_mb"] == 145.0
    assert len(data["stages"]) == 3
    assert data["non_root_uid"] == 1001


def test_rest_api_frontend_security_audit(client: TestClient):
    """Verify GET /api/v1/admin/container/frontend/security-audit returns 200 and score."""
    response = client.get("/api/v1/admin/container/frontend/security-audit")
    assert response.status_code == 200
    data = response.json()
    assert data["compliance_level"] == "strict_non_root"
    assert data["cis_benchmark_score_pct"] == 100.0
    assert data["is_root"] is False
    assert len(data["security_findings"]) >= 3


def test_rest_api_frontend_dockerfile_audit(client: TestClient):
    """Verify GET /api/v1/admin/container/frontend/dockerfile-audit returns 200 and audit."""
    response = client.get("/api/v1/admin/container/frontend/dockerfile-audit")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["is_multi_stage"] is True
    assert data["compliance_score_pct"] == 100.0
    assert data["has_non_root_user"] is True

