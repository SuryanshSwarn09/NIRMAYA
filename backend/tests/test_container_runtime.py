"""Automated test suite for Multi-Stage Minimal Alpine Dockerfile & Container Runtime Telemetry.

Verifies:
- OCI multi-stage Dockerfile layering (builder vs runtime, CIS Benchmark 4.1 non-root context)
- .dockerignore context boundary exclusions (.venv, __pycache__, .git, secrets)
- Container entrypoint lifecycle script (database migrations, worker concurrency, signal propagation)
- Container runtime status inspection (UID/GID, cgroup limits, Python version)
- CIS Docker Benchmark security context compliance auditing (UID 10001 enforcement)
- Production environment variable conformance validation and credential masking
- FastAPI REST endpoints under /api/v1/admin/container/* with container security headers
"""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.container_security import (
    OFFICIAL_NON_ROOT_UID,
    enforce_container_security_guard,
    get_container_process_identity,
    get_container_security_headers,
    is_running_as_root,
)
from app.main import app
from app.schemas.container_runtime import (
    ContainerExecutionMode,
    SecurityComplianceLevel,
)
from app.services.container_service import container_service


# -----------------------------------------------------------------------------
# 1. Dockerfile Static Architecture & CIS Compliance Tests
# -----------------------------------------------------------------------------

def test_dockerfile_multi_stage_syntax_and_layers():
    """Verify that backend/Dockerfile implements hardened 2-stage minimal Alpine build."""
    dockerfile_path = Path("backend/Dockerfile")
    if not dockerfile_path.exists():
        dockerfile_path = Path("Dockerfile")
    assert dockerfile_path.exists(), "backend/Dockerfile must exist"

    content = dockerfile_path.read_text(encoding="utf-8")

    # Stage 1: Builder
    assert "FROM python:3.12-alpine AS builder" in content
    assert "gcc" in content
    assert "musl-dev" in content
    assert "python -m venv /opt/venv" in content

    # Stage 2: Runtime
    assert "FROM python:3.12-alpine AS runtime" in content
    assert "COPY --from=builder" in content
    assert "/opt/venv" in content

    # CIS Docker 4.1: Non-root user configuration
    assert "addgroup -g 10001 -S nirmaya" in content
    assert "adduser -u 10001 -S -G nirmaya" in content
    assert "USER nirmaya:nirmaya" in content

    # OCI Health Check
    assert "HEALTHCHECK" in content
    assert "--interval=30s" in content
    assert "/api/v1/health" in content

    # Port Exposure and Entrypoint
    assert "EXPOSE 8000" in content
    assert 'ENTRYPOINT ["/app/docker-entrypoint.sh"]' in content


def test_dockerignore_configuration():
    """Verify context exclusions in both root and backend .dockerignore files."""
    for path_str in (".dockerignore", "backend/.dockerignore"):
        p = Path(path_str)
        assert p.exists(), f"{path_str} must exist"
        content = p.read_text(encoding="utf-8")
        assert ".venv" in content
        assert "__pycache__" in content


def test_docker_entrypoint_script_structure():
    """Verify that docker-entrypoint.sh has correct shebang, migration hooks, and exec."""
    entrypoint_path = Path("backend/docker-entrypoint.sh")
    assert entrypoint_path.exists(), "backend/docker-entrypoint.sh must exist"

    content = entrypoint_path.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/sh")
    assert "set -e" in content
    assert "alembic upgrade head" in content
    assert 'exec "$@"' in content


# -----------------------------------------------------------------------------
# 2. Container Service Telemetry & Runtime Inspection Tests
# -----------------------------------------------------------------------------

def test_container_service_runtime_status():
    """Verify container runtime status reporting."""
    status = container_service.get_runtime_status()
    assert status.execution_mode in (
        ContainerExecutionMode.CONTAINERIZED,
        ContainerExecutionMode.STANDALONE_HOST,
    )
    assert isinstance(status.is_container, bool)
    assert isinstance(status.process_uid, int)
    assert isinstance(status.process_gid, int)
    assert len(status.python_version) > 0
    assert len(status.os_platform) > 0
    assert status.uptime_seconds >= 0.0


def test_container_service_cgroup_memory_detection():
    """Verify graceful cgroup memory detection."""
    mem_limit = container_service.get_cgroup_memory_limit_mb()
    # On non-cgroup hosts this returns None gracefully
    if mem_limit is not None:
        assert mem_limit > 0.0


# -----------------------------------------------------------------------------
# 3. CIS Docker Benchmark 4.1 Security Context Auditing Tests
# -----------------------------------------------------------------------------

def test_container_security_audit_non_root(monkeypatch):
    """Verify security audit passes with 100% score under UID 10001."""
    monkeypatch.setenv("NIRMAYA_PROCESS_UID", "10001")
    monkeypatch.setenv("NIRMAYA_PROCESS_GID", "10001")

    audit = container_service.audit_security_context()
    assert audit.compliance_level == SecurityComplianceLevel.STRICT_NON_ROOT
    assert audit.is_root is False
    assert audit.uid_assigned == OFFICIAL_NON_ROOT_UID
    assert audit.user_name == "nirmaya"
    assert audit.cis_benchmark_score_pct == 100.0
    assert any("UID 10001" in finding for finding in audit.security_findings)


def test_container_security_audit_root_warning(monkeypatch):
    """Verify security audit flags root process (UID 0) as security finding."""
    monkeypatch.setenv("NIRMAYA_PROCESS_UID", "0")
    monkeypatch.setenv("NIRMAYA_PROCESS_GID", "0")

    audit = container_service.audit_security_context()
    assert audit.compliance_level == SecurityComplianceLevel.WARNING_ROOT
    assert audit.is_root is True
    assert audit.uid_assigned == 0
    assert audit.user_name == "root"
    assert audit.cis_benchmark_score_pct < 100.0
    assert any("violating CIS Docker" in finding for finding in audit.security_findings)


# -----------------------------------------------------------------------------
# 4. Environment Conformance & Build Manifest Tests
# -----------------------------------------------------------------------------

def test_environment_conformance_validation():
    """Verify production environment variables conformance and credential masking."""
    report = container_service.validate_environment()
    assert report.total_variables_checked >= 4
    assert 0.0 <= report.conformance_score_pct <= 100.0
    assert report.status in ("READY_PRODUCTION", "WARNINGS_PRESENT", "INSECURE_CONFIGURATION")

    var_names = [c.variable_name for c in report.checks]
    assert "SECRET_KEY" in var_names
    assert "DATABASE_URL" in var_names
    assert "RATE_LIMIT_ENABLED" in var_names
    assert "ALGORITHM" in var_names

    # Verify sensitive masking
    secret_check = next(c for c in report.checks if c.variable_name == "SECRET_KEY")
    assert secret_check.is_sensitive is True
    assert "..." in secret_check.masked_value or "******" in secret_check.masked_value


def test_docker_build_manifest():
    """Verify static architectural Docker build manifest."""
    manifest = container_service.get_build_manifest()
    assert manifest.image_name == "nirmaya-backend"
    assert manifest.tag == "v0.4.0"
    assert len(manifest.stages) == 2
    assert manifest.stages[0].stage_name == "builder"
    assert manifest.stages[1].stage_name == "runtime"
    assert manifest.target_image_size_mb < 120.0
    assert manifest.non_root_uid == 10001
    assert manifest.healthcheck_endpoint == "/api/v1/health"
    assert 8000 in manifest.exposed_ports


# -----------------------------------------------------------------------------
# 5. Container Security Policy Guard Tests
# -----------------------------------------------------------------------------

def test_container_security_guard_and_headers(monkeypatch):
    """Verify container security policy guard and dynamic headers."""
    monkeypatch.setenv("NIRMAYA_PROCESS_UID", "10001")
    assert enforce_container_security_guard(strict_mode=False) is True

    headers = get_container_security_headers()
    assert "X-Container-Runtime" in headers
    assert headers["X-Process-UID"] == "10001"
    assert headers["X-Process-User"] == "nirmaya"
    assert headers["X-Security-Standard"] == "CIS-Docker-4.1-Compliant"


# -----------------------------------------------------------------------------
# 6. FastAPI REST Endpoints Integration Tests
# -----------------------------------------------------------------------------

@pytest.fixture
def client():
    """Synchronous test client for container REST endpoints."""
    return TestClient(app)


def test_rest_api_container_status(client: TestClient):
    """Verify GET /api/v1/admin/container/status returns telemetry and security headers."""
    resp = client.get("/api/v1/admin/container/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "execution_mode" in data
    assert "process_uid" in data
    assert "uptime_seconds" in data
    assert "X-Container-Runtime" in resp.headers


def test_rest_api_container_security_audit(client: TestClient):
    """Verify GET /api/v1/admin/container/security-audit returns CIS compliance."""
    resp = client.get("/api/v1/admin/container/security-audit")
    assert resp.status_code == 200
    data = resp.json()
    assert "compliance_level" in data
    assert "cis_benchmark_score_pct" in data
    assert "security_findings" in data


def test_rest_api_container_manifest(client: TestClient):
    """Verify GET /api/v1/admin/container/manifest returns multi-stage build spec."""
    resp = client.get("/api/v1/admin/container/manifest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["image_name"] == "nirmaya-backend"
    assert len(data["stages"]) == 2
    assert data["target_image_size_mb"] < 120.0


def test_rest_api_container_validate_env(client: TestClient):
    """Verify GET and POST /api/v1/admin/container/validate-env audits environment."""
    resp_get = client.get("/api/v1/admin/container/validate-env")
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert "conformance_score_pct" in data_get
    assert data_get["total_variables_checked"] >= 4

    resp_post = client.post("/api/v1/admin/container/validate-env")
    assert resp_post.status_code == 200
    assert resp_post.json()["status"] == data_get["status"]
