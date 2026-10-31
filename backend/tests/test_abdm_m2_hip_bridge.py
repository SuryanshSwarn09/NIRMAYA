"""Tests for ABDM Milestone 2 (M2) Health Information Provider (HIP) Bridge Service."""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.abdm_hip_bridge import (
    dispatch_async_on_init_callback,
    validate_gateway_headers,
    webhook_audit_store,
)
from app.schemas.abdm_m2_bridge import GatewayAuthInitQuery


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_inbound_auth_init_202_accepted(async_client: AsyncClient):
    """Verify inbound ABDM Gateway /v0.5/users/auth/init returns HTTP 202 Accepted immediately."""
    req_id = str(uuid.uuid4())
    now_utc = datetime.now(timezone.utc)

    payload = {
        "requestId": req_id,
        "timestamp": now_utc.isoformat(),
        "query": {
            "id": "arun.patel@abdm",
            "purpose": "LINK",
            "authMode": "DIRECT_OTP",
            "requester": {
                "type": "HIP",
                "id": "IN0410000123",
            },
        },
    }

    headers = {
        "REQUEST-ID": req_id,
        "TIMESTAMP": now_utc.isoformat(),
        "X-CM-ID": "sbx",
    }

    # Test root-mounted /v0.5/users/auth/init
    response = await async_client.post("/v0.5/users/auth/init", json=payload, headers=headers)
    assert response.status_code == 202

    # Verify event logged in store
    events = webhook_audit_store.get_events(limit=5)
    matching = [e for e in events if e.request_id == req_id]
    assert len(matching) == 1
    assert matching[0].event_type == "users/auth/init"


@pytest.mark.asyncio
async def test_api_v1_bridge_auth_init(async_client: AsyncClient):
    """Verify /api/v1/abdm/m2/bridge/users/auth/init also returns HTTP 202 Accepted."""
    req_id = str(uuid.uuid4())
    now_utc = datetime.now(timezone.utc)

    payload = {
        "requestId": req_id,
        "timestamp": now_utc.isoformat(),
        "query": {
            "id": "meera.sharma@abdm",
            "purpose": "KYC",
            "authMode": "DEMOGRAPHICS",
        },
    }

    headers = {
        "REQUEST-ID": req_id,
        "TIMESTAMP": now_utc.isoformat(),
        "X-CM-ID": "sbx",
    }

    response = await async_client.post("/api/v1/abdm/m2/bridge/users/auth/init", json=payload, headers=headers)
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_timestamp_drift_replay_protection(async_client: AsyncClient):
    """Verify timestamps drifted >300s (5 minutes) in past or future are rejected (HTTP 400)."""
    req_id = str(uuid.uuid4())
    past_ts = datetime.now(timezone.utc) - timedelta(seconds=400)

    payload = {
        "requestId": req_id,
        "timestamp": past_ts.isoformat(),
        "query": {
            "id": "arun.patel@abdm",
            "purpose": "LINK",
            "authMode": "DIRECT_OTP",
        },
    }

    headers = {
        "REQUEST-ID": req_id,
        "TIMESTAMP": past_ts.isoformat(),
        "X-CM-ID": "sbx",
    }

    response = await async_client.post("/v0.5/users/auth/init", json=payload, headers=headers)
    assert response.status_code == 400
    assert "timestamp drift" in response.json()["message"]


@pytest.mark.asyncio
async def test_invalid_request_id_header(async_client: AsyncClient):
    """Verify non-UUID REQUEST-ID header is rejected with HTTP 400."""
    now_utc = datetime.now(timezone.utc)

    payload = {
        "requestId": "invalid-request-id-not-uuid",
        "timestamp": now_utc.isoformat(),
        "query": {
            "id": "arun.patel@abdm",
            "purpose": "LINK",
            "authMode": "DIRECT_OTP",
        },
    }

    headers = {
        "REQUEST-ID": "not-a-valid-uuid",
        "TIMESTAMP": now_utc.isoformat(),
        "X-CM-ID": "sbx",
    }

    response = await async_client.post("/v0.5/users/auth/init", json=payload, headers=headers)
    assert response.status_code == 400
    assert "not a valid UUID" in response.json()["message"]


@pytest.mark.asyncio
async def test_async_on_init_callback_correlation():
    """Verify asynchronous callback correlation preserves incoming requestId in resp.requestId."""
    incoming_id = str(uuid.uuid4())
    query = GatewayAuthInitQuery(
        id="arun.patel@abdm",
        purpose="LINK",
        authMode="DIRECT_OTP",
    )

    callback = await dispatch_async_on_init_callback(
        incoming_request_id=incoming_id,
        query=query,
        start_time=0.0,
    )

    assert callback.resp.requestId == incoming_id
    assert callback.requestId != incoming_id
    assert callback.auth is not None
    assert callback.auth.mode == "DIRECT_OTP"
    assert callback.auth.transactionId is not None
    assert callback.auth.meta is not None
    assert callback.auth.meta.hint == "+91 ******4821"


@pytest.mark.asyncio
async def test_bridge_status_endpoint(async_client: AsyncClient):
    """Verify GET /api/v1/abdm/m2/bridge/status returns operational telemetry."""
    response = await async_client.get("/api/v1/abdm/m2/bridge/status")
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["status"] == "online"
    assert data["hip_id"] == "IN0410000123"
    assert data["facility_name"] == "NIRMAYA Apex Hospital & Research Institute"
    assert data["cm_id"] == "sbx"
    assert "/v0.5/users/auth/init" in data["active_listeners"]


@pytest.mark.asyncio
async def test_test_ping_simulation(async_client: AsyncClient):
    """Verify POST /api/v1/abdm/m2/bridge/test-ping executes end-to-end 202 + callback."""
    response = await async_client.post("/api/v1/abdm/m2/bridge/test-ping")
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["success"] is True
    assert data["http_status"] == 202
    assert data["callback_dispatched"] is True
    assert data["callback_payload"]["resp"]["requestId"] == data["request_id"]


@pytest.mark.asyncio
async def test_webhook_events_endpoint(async_client: AsyncClient):
    """Verify GET /api/v1/abdm/m2/bridge/events returns the list of ingested events."""
    # Run a test ping first to guarantee at least 1 event exists
    await async_client.post("/api/v1/abdm/m2/bridge/test-ping")

    response = await async_client.get("/api/v1/abdm/m2/bridge/events?limit=10")
    assert response.status_code == 200
    events = response.json()["data"]

    assert isinstance(events, list)
    assert len(events) >= 1
    assert "request_id" in events[0]
    assert "status" in events[0]
    assert "latency_ms" in events[0]
