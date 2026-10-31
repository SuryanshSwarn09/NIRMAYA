"""OPD Consultation Queue REST API Endpoints for NIRMAYA.

Provides clinical queue management endpoints for:
- Patient reception check-in and token issuance
- Nursing triage priority updates
- Clinician patient summon calls to specific consulting rooms
- Consultation lifecycle status transitions
- Real-time queue queries and operational statistics
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.exceptions import EntityNotFoundException
from app.schemas.opd_queue import (
    OPDQueueEntry,
    OPDQueueResponse,
    QueueCallPatientRequest,
    QueueCheckInRequest,
    QueueStatsResponse,
    QueueStatus,
    QueueStatusUpdateRequest,
    QueueTriageUpdateRequest,
)
from app.services.opd_queue import opd_queue_service

logger = logging.getLogger("nirmaya.queue.api")

router = APIRouter()


@router.post(
    "/check-in",
    response_model=OPDQueueEntry,
    status_code=status.HTTP_201_CREATED,
    summary="Register and check in arriving patient at OPD desk",
)
async def check_in_patient(request: QueueCheckInRequest) -> OPDQueueEntry:
    """Assigns sequential token number and broadcasts queue.update event."""
    return await opd_queue_service.check_in_patient(request)


@router.get(
    "/facility/{facility_id}",
    response_model=OPDQueueResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve active facility OPD queue",
)
def get_facility_queue(
    facility_id: str,
    status_filter: Optional[QueueStatus] = Query(default=None, alias="status", description="Filter by queue status"),
    doctor_id: Optional[str] = Query(default=None, description="Filter by assigned clinician UUID"),
) -> OPDQueueResponse:
    """Returns active OPD queue sorted by triage urgency and sequential token."""
    return opd_queue_service.get_facility_queue(
        facility_id=facility_id,
        status_filter=status_filter,
        doctor_id=doctor_id,
    )


@router.get(
    "/entry/{queue_id}",
    response_model=OPDQueueEntry,
    status_code=status.HTTP_200_OK,
    summary="Fetch single OPD queue record by ID",
)
def get_queue_entry(queue_id: str) -> OPDQueueEntry:
    """Fetch details of a single queue entry."""
    entry = opd_queue_service.get_queue_entry(queue_id)
    if not entry:
        raise EntityNotFoundException("OPDQueueEntry", queue_id)
    return entry


@router.put(
    "/{queue_id}/triage",
    response_model=OPDQueueEntry,
    status_code=status.HTTP_200_OK,
    summary="Update patient clinical triage classification",
)
async def update_patient_triage(
    queue_id: str,
    request: QueueTriageUpdateRequest,
) -> OPDQueueEntry:
    """Updates triage level and broadcasts real-time queue.update event."""
    return await opd_queue_service.update_triage(queue_id, request)


@router.post(
    "/{queue_id}/call",
    response_model=OPDQueueEntry,
    status_code=status.HTTP_200_OK,
    summary="Clinician summons patient into consulting room",
)
async def call_patient_to_room(
    queue_id: str,
    request: QueueCallPatientRequest,
) -> OPDQueueEntry:
    """Sets status to CALLED and broadcasts queue.called event with room number."""
    return await opd_queue_service.call_patient(queue_id, request)


@router.put(
    "/{queue_id}/status",
    response_model=OPDQueueEntry,
    status_code=status.HTTP_200_OK,
    summary="Transition queue lifecycle status",
)
async def update_queue_status(
    queue_id: str,
    request: QueueStatusUpdateRequest,
) -> OPDQueueEntry:
    """Advances status (IN_CONSULTATION, COMPLETED, ABSENT, CANCELLED) and broadcasts update."""
    return await opd_queue_service.update_status(queue_id, request)


@router.get(
    "/facility/{facility_id}/stats",
    response_model=QueueStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve facility OPD operational throughput metrics",
)
def get_facility_queue_stats(facility_id: str) -> QueueStatsResponse:
    """Calculates active tokens, triage urgency distribution, and average wait time."""
    return opd_queue_service.get_queue_stats(facility_id)
