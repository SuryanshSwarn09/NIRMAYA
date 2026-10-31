"""REST API endpoints for real-time Clinical Alerts and Laboratory Panic-Value Notifications.

Provides diagnostic lab panic evaluation, manual/automated alert dispatching,
clinician workspace feed retrieval, and structured acknowledgement tracking.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.core.exceptions import EntityNotFoundException
from app.schemas.clinical_alerts import (
    AlertAcknowledgeRequest,
    AlertCreateRequest,
    AlertSeverity,
    AlertStatus,
    AlertSummaryStatsResponse,
    ClinicalAlertResponse,
    LabEvaluationRequest,
    LabEvaluationResult,
    LabPanicRule,
)
from app.services.clinical_alerts import clinical_alerts_service

router = APIRouter()


@router.get(
    "/rules/panic",
    response_model=List[LabPanicRule],
    summary="List laboratory panic-value threshold rules",
)
def list_panic_rules() -> List[LabPanicRule]:
    """Retrieves all registered clinical panic-value boundaries and guidance."""
    return clinical_alerts_service.get_panic_rules()


@router.post(
    "/evaluate-lab",
    response_model=LabEvaluationResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate diagnostic laboratory observation for panic values",
)
async def evaluate_lab_observation(
    request: LabEvaluationRequest,
) -> LabEvaluationResult:
    """Evaluates observation against panic limits and dispatches real-time WebSocket alert if triggered."""
    return await clinical_alerts_service.evaluate_lab_observation(request)


@router.post(
    "/publish",
    response_model=ClinicalAlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish clinical notification or panic alert",
)
async def publish_clinical_alert(
    request: AlertCreateRequest,
) -> ClinicalAlertResponse:
    """Creates a clinical alert and broadcasts it to the clinician workspace channel in real-time."""
    return await clinical_alerts_service.create_alert(request)


@router.get(
    "/doctor/{doctor_id}",
    response_model=List[ClinicalAlertResponse],
    summary="Get clinical alerts for clinician",
)
def get_doctor_alerts(
    doctor_id: str,
    alert_status: Optional[AlertStatus] = Query(None, alias="status", description="Filter by status (UNREAD, ACKNOWLEDGED)"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity (PANIC, CRITICAL, WARNING, INFO)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of alerts to return"),
) -> List[ClinicalAlertResponse]:
    """Retrieves descending chronological clinical alerts feed for a clinician."""
    return clinical_alerts_service.get_doctor_alerts(
        doctor_id=doctor_id,
        status=alert_status,
        severity=severity,
        limit=limit,
    )


@router.get(
    "/doctor/{doctor_id}/unread-count",
    summary="Get unread alert count for clinician badge",
)
def get_doctor_unread_count(doctor_id: str) -> dict:
    """Provides rapid unread alert tally for top navigation badge."""
    stats = clinical_alerts_service.get_doctor_stats(doctor_id)
    return {
        "doctorId": doctor_id,
        "unreadCount": stats.unreadCount,
    }


@router.get(
    "/doctor/{doctor_id}/stats",
    response_model=AlertSummaryStatsResponse,
    summary="Get alert summary metrics for clinician dashboard",
)
def get_doctor_alert_stats(doctor_id: str) -> AlertSummaryStatsResponse:
    """Provides breakdown of total, unread, panic, critical, and acknowledged alerts."""
    return clinical_alerts_service.get_doctor_stats(doctor_id)


@router.get(
    "/{alert_id}",
    response_model=ClinicalAlertResponse,
    summary="Get single clinical alert detail",
)
def get_alert_detail(alert_id: str) -> ClinicalAlertResponse:
    """Retrieves full detail and audit history of a clinical alert."""
    try:
        return clinical_alerts_service.get_alert(alert_id)
    except EntityNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post(
    "/{alert_id}/acknowledge",
    response_model=ClinicalAlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Acknowledge critical alert with clinical action",
)
async def acknowledge_alert(
    alert_id: str,
    request: AlertAcknowledgeRequest,
) -> ClinicalAlertResponse:
    """Documents clinician acknowledgement and clinical intervention taken, synchronizing connected clients."""
    try:
        return await clinical_alerts_service.acknowledge_alert(alert_id, request)
    except EntityNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
