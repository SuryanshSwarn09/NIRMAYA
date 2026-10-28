"""API Endpoints for ABDM Milestone 2 (M2) Health Information Provider (HIP) Bridge."""

from datetime import datetime, timezone
import logging
import time
from typing import List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import APIResponse
from app.schemas.abdm_m2_bridge import (
    GatewayAuthInitRequest,
    GatewayAuthOnInitCallback,
    GatewayPatientDiscoveryRequest,
    HipBridgeStatusResponse,
    PatientDiscoverySimulateRequest,
    PatientDiscoverySimulateResponse,
    TestPingResponse,
    WebhookEventItem,
)
from app.services.abdm_hip_bridge import (
    dispatch_async_on_init_callback,
    get_bridge_status,
    get_recent_webhook_events,
    simulate_gateway_test_ping,
    validate_gateway_headers,
    webhook_audit_store,
)
from app.services.abdm_discovery import (
    process_and_dispatch_discovery,
    simulate_patient_discovery,
)

logger = logging.getLogger("nirmaya.api.abdm_m2_bridge")

router = APIRouter()



@router.post(
    "/users/auth/init",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Inbound ABDM Gateway Webhook: Initiate Patient Auth",
    description=(
        "Synchronous HTTP 202 Accepted ingest point for ABDM Gateway /v0.5/users/auth/init. "
        "Enforces replay defense (300s timestamp drift) and schedules asynchronous callback to /v0.5/users/auth/on-init."
    ),
)
async def inbound_gateway_auth_init(
    payload: GatewayAuthInitRequest,
    background_tasks: BackgroundTasks,
    request_id: Optional[str] = Header(None, alias="REQUEST-ID"),
    timestamp: Optional[str] = Header(None, alias="TIMESTAMP"),
    x_cm_id: Optional[str] = Header("sbx", alias="X-CM-ID"),
) -> Response:
    start_time = time.perf_counter()

    # Fallback to payload properties if headers not provided directly by client
    req_id_val = request_id or payload.requestId
    ts_val = timestamp or (payload.timestamp.isoformat() if payload.timestamp else None)

    # 1. Validate headers with replay protection
    valid_req_id, parsed_ts = validate_gateway_headers(
        request_id_header=req_id_val,
        timestamp_header=ts_val,
        x_cm_id_header=x_cm_id,
    )

    # 2. Record initial ingest event in audit store
    event = WebhookEventItem(
        id=str(uuid.uuid4()),
        request_id=valid_req_id,
        event_type="users/auth/init",
        status="ACCEPTED",
        latency_ms=0.0,
        received_at=datetime.now(timezone.utc),
        details={
            "cm_id": x_cm_id,
            "patient_id": payload.query.id,
            "auth_mode": payload.query.authMode,
            "purpose": payload.query.purpose,
        },
    )
    webhook_audit_store.add_event(event)

    # 3. Schedule asynchronous background callback to ABDM Gateway (/v0.5/users/auth/on-init)
    background_tasks.add_task(
        dispatch_async_on_init_callback,
        incoming_request_id=valid_req_id,
        query=payload.query,
        start_time=start_time,
    )

    # 4. Synchronously acknowledge under 200ms
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.get(
    "/status",
    response_model=APIResponse[HipBridgeStatusResponse],
    summary="Get HIP Bridge Telemetry & Node Health",
)
async def get_hip_bridge_status() -> APIResponse[HipBridgeStatusResponse]:
    """Retrieve telemetry report on the registered Health Information Provider (HIP) node."""
    bridge_telemetry = get_bridge_status()
    return APIResponse(
        success=True,
        data=bridge_telemetry,
        message="HIP Bridge node telemetry retrieved successfully",
    )


@router.get(
    "/events",
    response_model=APIResponse[List[WebhookEventItem]],
    summary="Get Recent Inbound Webhook Audit Events",
)
async def list_webhook_events(limit: int = 50) -> APIResponse[List[WebhookEventItem]]:
    """Retrieve recent inbound ABDM Gateway webhook events and response latencies."""
    events = get_recent_webhook_events(limit=limit)
    return APIResponse(
        success=True,
        data=events,
        message=f"Retrieved {len(events)} recent webhook audit records",
    )


@router.post(
    "/test-ping",
    response_model=APIResponse[TestPingResponse],
    summary="Simulate Inbound ABDM Gateway Webhook Ping",
)
async def trigger_gateway_test_ping() -> APIResponse[TestPingResponse]:
    """Trigger an end-to-end simulated Gateway webhook ping to verify 202 Accepted and async callback."""
    test_result = await simulate_gateway_test_ping()
    return APIResponse(
        success=True,
        data=test_result,
        message="Gateway webhook test ping completed successfully",
    )


@router.post(
    "/care-contexts/discover",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Inbound ABDM Gateway Webhook: Discover Patient Care Contexts",
    description=(
        "Synchronous HTTP 202 Accepted ingest point for ABDM Gateway /v0.5/care-contexts/discover. "
        "Enforces replay defense (300s timestamp drift) and schedules asynchronous fuzzy matching "
        "and callback to /v0.5/care-contexts/on-discover."
    ),
)
async def inbound_gateway_care_contexts_discover(
    payload: GatewayPatientDiscoveryRequest,
    background_tasks: BackgroundTasks,
    request_id: Optional[str] = Header(None, alias="REQUEST-ID"),
    timestamp: Optional[str] = Header(None, alias="TIMESTAMP"),
    x_cm_id: Optional[str] = Header("sbx", alias="X-CM-ID"),
) -> Response:
    start_time = time.perf_counter()

    req_id_val = request_id or payload.requestId
    ts_val = timestamp or (payload.timestamp.isoformat() if payload.timestamp else None)

    # 1. Validate headers with replay protection
    valid_req_id, parsed_ts = validate_gateway_headers(
        request_id_header=req_id_val,
        timestamp_header=ts_val,
        x_cm_id_header=x_cm_id,
    )

    # 2. Record initial ingest event in audit store
    event = WebhookEventItem(
        id=str(uuid.uuid4()),
        request_id=valid_req_id,
        event_type="care-contexts/discover",
        status="ACCEPTED",
        latency_ms=0.0,
        received_at=datetime.now(timezone.utc),
        details={
            "cm_id": x_cm_id,
            "patient_id": payload.patient.id,
            "patient_name": payload.patient.name,
            "hip_id": payload.hipId,
            "verified_identifiers_count": len(payload.patient.verifiedIdentifiers),
        },
    )
    webhook_audit_store.add_event(event)

    # 3. Schedule asynchronous background discovery and callback dispatch
    background_tasks.add_task(
        process_and_dispatch_discovery,
        incoming_request=payload,
        start_time=start_time,
    )

    # 4. Synchronously acknowledge under 200ms
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post(
    "/discovery/simulate",
    response_model=APIResponse[PatientDiscoverySimulateResponse],
    summary="Simulate Patient Discovery with Fuzzy Demographic Matching",
)
async def simulate_discovery(
    sim_req: PatientDiscoverySimulateRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientDiscoverySimulateResponse]:
    """Test demographic matching, typo tolerance, confidence score, and care context discovery."""
    sim_result = await simulate_patient_discovery(session=db, sim_req=sim_req)
    return APIResponse(
        success=True,
        data=sim_result,
        message=(
            f"Patient discovery completed: matched={sim_result.matched} "
            f"({sim_result.confidence_score * 100:.1f}% confidence)"
        ),
    )

