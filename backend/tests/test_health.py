"""Unit test suite for health check endpoint, telemetry, and security headers."""

from unittest.mock import patch
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Verify root discovery endpoint metadata."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "NIRMAYA" in data["message"]
    assert data["version"] == "0.1.0"
    assert "HL7 FHIR R4" in data["standards"]


@pytest.mark.asyncio
async def test_health_check_payload_structure(client: AsyncClient):
    """Verify that /api/v1/health returns valid APIResponse[SystemHealthResponse]."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()

    # Verify Envelope
    assert payload["success"] is True
    assert "NIRMAYA Health Interoperability Node is operational" in payload["message"]

    # Verify Health Telemetry
    data = payload["data"]
    assert data["status"] in ["healthy", "degraded"]
    assert data["project"] == "NIRMAYA"
    assert data["environment"] == "development"
    assert data["uptime_seconds"] >= 0.0

    # Verify Standards Compliance
    standards = data["standards"]
    assert standards["fhir_version"] == "R4"
    assert standards["abdm_sandbox"] is True
    assert standards["loinc_mapped"] is True
    assert standards["snomed_ct_ready"] is True

    # Verify Database Indicator structure
    db_telemetry = data["database"]
    assert db_telemetry["status"] in ["healthy", "unreachable", "degraded"]
    assert db_telemetry["driver"] in ["asyncpg", "aiosqlite", "relational"]


@pytest.mark.asyncio
async def test_database_health_probe_mock_healthy(client: AsyncClient):
    """Verify health endpoint output when database probe returns healthy."""
    mock_probe = {
        "status": "healthy",
        "latency_ms": 0.85,
        "database_type": "postgresql",
        "error": None,
    }
    with patch("app.api.v1.endpoints.health.check_db_health", return_value=mock_probe):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["status"] == "healthy"
        assert payload["data"]["database"]["status"] == "healthy"
        assert payload["data"]["database"]["latency_ms"] == 0.85
        assert payload["data"]["database"]["database_type"] == "postgresql"
        assert payload["data"]["database"]["error"] is None


@pytest.mark.asyncio
async def test_performance_telemetry_header(client: AsyncClient):
    """Verify that X-Process-Time is injected by telemetry middleware."""
    response = await client.get("/api/v1/health")
    assert "X-Process-Time" in response.headers
    assert response.headers["X-Process-Time"].endswith("ms")


@pytest.mark.asyncio
async def test_correlation_id_generation_and_propagation(client: AsyncClient):
    """Verify X-Request-ID generation and propagation for clinical audit logging."""
    # Case 1: Automatic UUID generation
    response1 = await client.get("/api/v1/health")
    assert "X-Request-ID" in response1.headers
    generated_id = response1.headers["X-Request-ID"]
    assert len(generated_id) > 10

    # Case 2: Client supplied trace ID propagation
    custom_trace_id = "trace-patient-audit-9999"
    response2 = await client.get(
        "/api/v1/health",
        headers={"X-Request-ID": custom_trace_id},
    )
    assert response2.headers["X-Request-ID"] == custom_trace_id
    assert response2.json()["request_id"] == custom_trace_id


@pytest.mark.asyncio
async def test_security_headers_injection(client: AsyncClient):
    """Verify enterprise healthcare security headers on API responses."""
    response = await client.get("/api/v1/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_404_error_envelope_formatting(client: AsyncClient):
    """Verify that unhandled routes return structured ErrorResponse JSON."""
    response = await client.get("/api/v1/non-existent-clinical-path")
    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error_code"] == "HTTP_404"
    assert "timestamp" in payload
