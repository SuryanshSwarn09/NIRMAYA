"""API Endpoints for ABDM Milestone 3 (M3) Consent Management and Webhooks."""

from datetime import datetime, timezone
import logging
import time
from typing import List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Response, status

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.schemas.common import APIResponse
from app.schemas.abdm_m2_bridge import WebhookEventItem
from app.schemas.abdm_m3_consent import (
    ConsentNotificationPayload,
    ConsentNotificationSimulateRequest,
    ConsentNotificationSimulateResponse,
    ConsentRecordRepresentation,
)
from app.services.abdm_hip_bridge import (
    validate_gateway_headers,
    webhook_audit_store,
)
from app.services.abdm_consent import (
    consent_registry_store,
    process_and_dispatch_consent_notification,
    simulate_consent_notification,
)

logger = logging.getLogger("nirmaya.api.abdm_m3_consent")

router = APIRouter()


@router.post(
    "/consents/hip/notify",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Inbound ABDM Gateway Webhook: Notify HIP of Consent Grant/Revocation",
    description=(
        "Synchronous HTTP 202 Accepted ingest point for ABDM Gateway /v0.5/consents/hip/notify. "
        "Enforces replay defense (300s timestamp drift), verifies consent artefact signature, "
        "stores permissions in Consent Registry, and schedules asynchronous callback to /v0.5/consents/hip/on-notify."
    ),
)
async def inbound_gateway_consent_notify(
    payload: ConsentNotificationPayload,
    background_tasks: BackgroundTasks,
    request_id: Optional[str] = Header(None, alias="REQUEST-ID"),
    timestamp: Optional[str] = Header(None, alias="TIMESTAMP"),
    x_cm_id: Optional[str] = Header("sbx", alias="X-CM-ID"),
) -> Response:
    """Inbound webhook called by ABDM Gateway when patient grants, revokes, or expires consent."""
    start_time = time.perf_counter()

    req_id_val = request_id or payload.requestId
    ts_val = timestamp or (payload.timestamp.isoformat() if payload.timestamp else None)

    # 1. Validate headers with replay protection (300s drift window)
    valid_req_id, parsed_ts = validate_gateway_headers(
        request_id_header=req_id_val,
        timestamp_header=ts_val,
        x_cm_id_header=x_cm_id,
    )

    # 2. Record initial ingest event in audit store
    notification = payload.notification
    event = WebhookEventItem(
        id=str(uuid.uuid4()),
        request_id=valid_req_id,
        event_type="consents/hip/notify",
        status="ACCEPTED",
        latency_ms=0.0,
        received_at=datetime.now(timezone.utc),
        details={
            "cm_id": x_cm_id,
            "consent_id": notification.consentId,
            "status": notification.status,
            "has_artefact": notification.consentArtefact is not None,
        },
    )
    webhook_audit_store.add_event(event)

    # 3. Schedule asynchronous background processing, verification, and on-notify callback dispatch
    background_tasks.add_task(
        process_and_dispatch_consent_notification,
        incoming_request=payload,
        start_time=start_time,
    )

    # 4. Synchronously acknowledge under 200ms
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.get(
    "/consents/{consent_id}",
    response_model=APIResponse[ConsentRecordRepresentation],
    summary="Query Stored Consent Artefact Details by Consent ID",
)
async def get_consent_by_id(consent_id: str) -> APIResponse[ConsentRecordRepresentation]:
    """Retrieve details and active permission scopes for a stored consent artefact."""
    record = consent_registry_store.get_consent(consent_id)
    if not record:
        raise EntityNotFoundException("ConsentArtefact", consent_id)

    return APIResponse(
        success=True,
        data=record,
        message=f"Consent artefact '{consent_id}' retrieved successfully (status: {record.status})",
    )


@router.get(
    "/consents/patient/{patient_id}",
    response_model=APIResponse[List[ConsentRecordRepresentation]],
    summary="Query All Active and Historical Consents for a Patient",
)
async def get_consents_by_patient(patient_id: str) -> APIResponse[List[ConsentRecordRepresentation]]:
    """Retrieve all consent grants registered for a given patient ABHA address."""
    records = consent_registry_store.get_patient_consents(patient_id)
    return APIResponse(
        success=True,
        data=records,
        message=f"Retrieved {len(records)} consent artefact(s) for patient '{patient_id}'",
    )


@router.post(
    "/consents/simulate",
    response_model=APIResponse[ConsentNotificationSimulateResponse],
    summary="Simulate ABDM Consent Notification & Verification",
)
async def simulate_consent(
    sim_req: ConsentNotificationSimulateRequest,
) -> APIResponse[ConsentNotificationSimulateResponse]:
    """Generate and ingest a synthetic ABDM consent notification with signed artefact."""
    sim_response = await simulate_consent_notification(sim_req)
    return APIResponse(
        success=True,
        data=sim_response,
        message=(
            f"Consent notification simulated successfully: consent_id={sim_response.consent_id} "
            f"status={sim_response.status} signature_verified={sim_response.signature_verified}"
        ),
    )


@router.post(
    "/consents/{consent_id}/revoke",
    response_model=APIResponse[ConsentRecordRepresentation],
    summary="Revoke an Existing Consent Artefact",
)
async def revoke_consent(consent_id: str) -> APIResponse[ConsentRecordRepresentation]:
    """Manually revoke an active consent in the registry."""
    updated = consent_registry_store.revoke_consent(consent_id)
    if not updated:
        raise EntityNotFoundException("ConsentArtefact", consent_id)

    return APIResponse(
        success=True,
        data=updated,
        message=f"Consent artefact '{consent_id}' successfully marked as REVOKED",
    )

