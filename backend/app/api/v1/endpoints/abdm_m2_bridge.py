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
    AbdmM2AuditReport,
    GatewayAuthInitRequest,
    GatewayAuthOnInitCallback,
    GatewayLinkConfirmRequest,
    GatewayLinkInitRequest,
    GatewayPatientDiscoveryRequest,
    HipBridgeStatusResponse,
    LinkConfirmSimulateRequest,
    LinkConfirmSimulateResponse,
    LinkInitSimulateRequest,
    LinkInitSimulateResponse,
    LinkSessionRepresentation,
    PatientDiscoverySimulateRequest,
    PatientDiscoverySimulateResponse,
    TestPingResponse,
    WebhookEventItem,
)
from app.services.abdm_hip_bridge import (
    dispatch_async_on_init_callback,
    generate_m2_audit_report,
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
from app.services.abdm_linkage import (
    link_session_manager,
    process_and_dispatch_link_confirm,
    process_and_dispatch_link_init,
    simulate_care_context_link_confirm,
    simulate_care_context_link_init,
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


# ----------------------------------------------------------------------------
# ABDM M2 Care Context Linkage Endpoints (/v0.5/links/link/*)
# ----------------------------------------------------------------------------


@router.post(
    "/links/link/init",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Inbound ABDM Gateway Webhook: Initiate Care Context Link Challenge",
    description=(
        "Synchronous HTTP 202 Accepted ingest point for ABDM Gateway /v0.5/links/link/init. "
        "Enforces replay defense (300s timestamp drift), creates a 10-minute OTP challenge, "
        "and schedules asynchronous callback to /v0.5/links/link/on-init."
    ),
)
async def inbound_gateway_link_init(
    payload: GatewayLinkInitRequest,
    background_tasks: BackgroundTasks,
    request_id: Optional[str] = Header(None, alias="REQUEST-ID"),
    timestamp: Optional[str] = Header(None, alias="TIMESTAMP"),
    x_cm_id: Optional[str] = Header("sbx", alias="X-CM-ID"),
) -> Response:
    start_time = time.perf_counter()

    req_id_val = request_id or payload.requestId
    ts_val = timestamp or (payload.timestamp.isoformat() if payload.timestamp else None)

    # 1. Validate headers with replay defense
    valid_req_id, parsed_ts = validate_gateway_headers(
        request_id_header=req_id_val,
        timestamp_header=ts_val,
        x_cm_id_header=x_cm_id,
    )

    # 2. Record initial ingest event in audit store
    event = WebhookEventItem(
        id=str(uuid.uuid4()),
        request_id=valid_req_id,
        event_type="links/link/init",
        status="ACCEPTED",
        latency_ms=0.0,
        received_at=datetime.now(timezone.utc),
        details={
            "cm_id": x_cm_id,
            "patient_id": payload.patient.id,
            "transaction_id": payload.transactionId,
            "care_contexts_count": len(payload.patient.careContexts),
        },
    )
    webhook_audit_store.add_event(event)

    # 3. Schedule asynchronous background linking & callback dispatch
    background_tasks.add_task(
        process_and_dispatch_link_init,
        incoming_request=payload,
        start_time=start_time,
    )

    # 4. Synchronously acknowledge under 200ms
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post(
    "/links/link/confirm",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Inbound ABDM Gateway Webhook: Confirm Care Context Link OTP",
    description=(
        "Synchronous HTTP 202 Accepted ingest point for ABDM Gateway /v0.5/links/link/confirm. "
        "Enforces replay defense (300s timestamp drift), verifies patient OTP token, "
        "and schedules asynchronous callback to /v0.5/links/link/on-confirm."
    ),
)
async def inbound_gateway_link_confirm(
    payload: GatewayLinkConfirmRequest,
    background_tasks: BackgroundTasks,
    request_id: Optional[str] = Header(None, alias="REQUEST-ID"),
    timestamp: Optional[str] = Header(None, alias="TIMESTAMP"),
    x_cm_id: Optional[str] = Header("sbx", alias="X-CM-ID"),
) -> Response:
    start_time = time.perf_counter()

    req_id_val = request_id or payload.requestId
    ts_val = timestamp or (payload.timestamp.isoformat() if payload.timestamp else None)

    # 1. Validate headers with replay defense
    valid_req_id, parsed_ts = validate_gateway_headers(
        request_id_header=req_id_val,
        timestamp_header=ts_val,
        x_cm_id_header=x_cm_id,
    )

    # 2. Record initial ingest event in audit store
    event = WebhookEventItem(
        id=str(uuid.uuid4()),
        request_id=valid_req_id,
        event_type="links/link/confirm",
        status="ACCEPTED",
        latency_ms=0.0,
        received_at=datetime.now(timezone.utc),
        details={
            "cm_id": x_cm_id,
            "link_ref_number": payload.confirmation.linkRefNumber,
        },
    )
    webhook_audit_store.add_event(event)

    # 3. Schedule asynchronous background OTP confirmation & callback dispatch
    background_tasks.add_task(
        process_and_dispatch_link_confirm,
        incoming_request=payload,
        start_time=start_time,
    )

    # 4. Synchronously acknowledge under 200ms
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post(
    "/link/init/simulate",
    response_model=APIResponse[LinkInitSimulateResponse],
    summary="Simulate Inbound ABDM Care Context Link Initiation",
)
async def simulate_link_init_endpoint(
    sim_req: LinkInitSimulateRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[LinkInitSimulateResponse]:
    """Simulate care context linking challenge and OTP generation from clinical cockpit."""
    sim_result = await simulate_care_context_link_init(session=db, sim_req=sim_req)
    return APIResponse(
        success=sim_result.success,
        data=sim_result,
        message=(
            f"Care context link initiation completed: success={sim_result.success} "
            f"(Link Ref: {sim_result.link_ref_number or 'N/A'})"
        ),
    )


@router.post(
    "/link/confirm/simulate",
    response_model=APIResponse[LinkConfirmSimulateResponse],
    summary="Simulate Inbound ABDM Care Context Link OTP Confirmation",
)
async def simulate_link_confirm_endpoint(
    sim_req: LinkConfirmSimulateRequest,
) -> APIResponse[LinkConfirmSimulateResponse]:
    """Simulate citizen OTP verification to link care contexts."""
    sim_result = await simulate_care_context_link_confirm(sim_req=sim_req)
    return APIResponse(
        success=sim_result.success,
        data=sim_result,
        message=(
            f"Care context link confirmation completed: linked={sim_result.linked} "
            f"({len(sim_result.linked_care_contexts)} care contexts linked)"
        ),
    )


@router.get(
    "/link/sessions",
    response_model=APIResponse[List[LinkSessionRepresentation]],
    summary="List Active and Recent ABDM Link Sessions",
)
async def list_link_sessions_endpoint(
    limit: int = 50,
) -> APIResponse[List[LinkSessionRepresentation]]:
    """List recent link challenge sessions with OTP state and remaining attempts."""
    sessions = link_session_manager.list_sessions(limit=limit)
    data = [
        LinkSessionRepresentation(
            link_ref_number=s.link_ref_number,
            transaction_id=s.transaction_id,
            patient_id=s.patient_id,
            patient_name=s.patient_name,
            status=s.status,
            care_contexts_count=len(s.care_contexts),
            created_at=s.created_at,
            expires_at=s.expires_at,
            attempts_remaining=s.attempts_left,
        )
        for s in sessions
    ]
    return APIResponse(
        success=True,
        data=data,
        message=f"Retrieved {len(data)} link sessions",
    )


@router.get(
    "/audit",
    response_model=APIResponse[AbdmM2AuditReport],
    summary="Get ABDM Milestone 2 Integration & Interoperability Audit Report",
)
async def get_m2_audit_endpoint() -> APIResponse[AbdmM2AuditReport]:
    """Compile and return comprehensive ABDM Milestone 2 integration audit metrics."""
    audit_report = generate_m2_audit_report()
    return APIResponse(
        success=True,
        data=audit_report,
        message="ABDM Milestone 2 integration audit metrics compiled successfully",
    )


