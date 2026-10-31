"""OPD Consultation Queue Service Engine for NIRMAYA.

Manages daily facility patient queues, sequential token generation, triage classifications,
consulting room assignments, and automated real-time WebSocket event dissemination.
"""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.core.exceptions import EntityNotFoundException, ValidationException
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
from app.schemas.websocket_events import (
    QueueUpdatePayload,
    TriageLevel,
    WebSocketChannel,
    WebSocketEventType,
)
from app.services.websocket_manager import ws_manager

logger = logging.getLogger("nirmaya.queue")


class OpdQueueService:
    """Thread-safe OPD Queue management engine with automated event dispatch."""

    def __init__(self) -> None:
        # facility_id -> {queue_id: OPDQueueEntry}
        self._queues: Dict[str, Dict[str, OPDQueueEntry]] = {}
        # facility_id -> current token counter
        self._token_counters: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._seed_default_queues()

    def _seed_default_queues(self) -> None:
        """Seed realistic initial patient queue entries for demonstration and tests."""
        facility_id = "IN0410000123"
        self._token_counters[facility_id] = 3
        now = datetime.now(timezone.utc).isoformat()

        entries = [
            OPDQueueEntry(
                queueId="queue-seed-01",
                facilityId=facility_id,
                tokenNumber=1,
                patientId="pat-arun-patel-01",
                patientName="Arun Patel",
                patientAbha="91-8472-1092-4821",
                patientPhone="+91 98765 43210",
                doctorId="doc-test-001",
                doctorName="Dr. Ananya Sharma",
                status=QueueStatus.WAITING,
                triageLevel=TriageLevel.STANDARD,
                chiefComplaint="Quarterly cardiovascular review and blood pressure evaluation",
                estimatedWaitMinutes=10,
                checkInTime=now,
            ),
            OPDQueueEntry(
                queueId="queue-seed-02",
                facilityId=facility_id,
                tokenNumber=2,
                patientId="pat-priya-nair-02",
                patientName="Priya Nair",
                patientAbha="91-9988-7766-5544",
                patientPhone="+91 98123 45678",
                doctorId="doc-test-001",
                doctorName="Dr. Ananya Sharma",
                status=QueueStatus.WAITING,
                triageLevel=TriageLevel.URGENT,
                chiefComplaint="Episodes of exertional palpitations and morning dizziness",
                estimatedWaitMinutes=5,
                checkInTime=now,
            ),
            OPDQueueEntry(
                queueId="queue-seed-03",
                facilityId=facility_id,
                tokenNumber=3,
                patientId="pat-rajesh-kumar-03",
                patientName="Rajesh Kumar",
                patientAbha="91-3322-1100-4455",
                patientPhone="+91 98450 11223",
                doctorId="doc-test-001",
                doctorName="Dr. Ananya Sharma",
                status=QueueStatus.CALLED,
                triageLevel=TriageLevel.EMERGENT,
                chiefComplaint="Acute retrosternal chest discomfort radiating to left jaw",
                roomNumber="Room 1",
                checkInTime=now,
                calledTime=now,
            ),
        ]

        self._queues[facility_id] = {e.queueId: e for e in entries}

    def _find_entry_and_facility(self, queue_id: str) -> tuple[Optional[str], Optional[OPDQueueEntry]]:
        """Locate queue entry and containing facility ID."""
        for fac_id, entries in self._queues.items():
            if queue_id in entries:
                return fac_id, entries[queue_id]
        return None, None

    async def check_in_patient(self, req: QueueCheckInRequest) -> OPDQueueEntry:
        """Register and check in an arriving patient, assigning the next daily token number."""
        async with self._lock:
            fac_id = req.facilityId
            if fac_id not in self._token_counters:
                self._token_counters[fac_id] = 0
            self._token_counters[fac_id] += 1
            token_num = self._token_counters[fac_id]

            if fac_id not in self._queues:
                self._queues[fac_id] = {}

            # Estimate initial wait time based on triage
            wait_est = 5 if req.triageLevel == TriageLevel.EMERGENT else (15 if req.triageLevel == TriageLevel.URGENT else 30)

            entry = OPDQueueEntry(
                queueId=str(uuid.uuid4()),
                facilityId=fac_id,
                tokenNumber=token_num,
                patientId=req.patientId,
                patientName=req.patientName,
                patientAbha=req.patientAbha,
                patientPhone=req.patientPhone,
                doctorId=req.doctorId,
                doctorName=req.doctorName,
                status=QueueStatus.WAITING,
                triageLevel=req.triageLevel,
                chiefComplaint=req.chiefComplaint,
                estimatedWaitMinutes=wait_est,
                checkInTime=datetime.now(timezone.utc).isoformat(),
                notes=req.notes,
            )
            self._queues[fac_id][entry.queueId] = entry

        logger.info(f"[OPDQueue] Patient {entry.patientName} checked in at facility {fac_id} with token #{token_num} (triage={entry.triageLevel})")

        # Broadcast update to facility channel
        await ws_manager.broadcast_event(
            channel=WebSocketChannel.facility_queue(fac_id),
            event_type=WebSocketEventType.QUEUE_UPDATE,
            payload=entry.model_dump(),
        )

        # Also broadcast to doctor workspace if doctor assigned
        if req.doctorId:
            await ws_manager.broadcast_event(
                channel=WebSocketChannel.doctor_workspace(req.doctorId),
                event_type=WebSocketEventType.QUEUE_UPDATE,
                payload=entry.model_dump(),
            )

        return entry

    async def update_triage(self, queue_id: str, req: QueueTriageUpdateRequest) -> OPDQueueEntry:
        """Update clinical triage level and adjust wait time estimate."""
        async with self._lock:
            fac_id, entry = self._find_entry_and_facility(queue_id)
            if not entry or not fac_id:
                raise EntityNotFoundException("OPDQueueEntry", queue_id)

            entry.triageLevel = req.triageLevel
            if req.estimatedWaitMinutes is not None:
                entry.estimatedWaitMinutes = req.estimatedWaitMinutes
            if req.notes:
                entry.notes = f"{entry.notes or ''} | Triage Note: {req.notes}".strip(" |")

        logger.info(f"[OPDQueue] Token #{entry.tokenNumber} triage updated to {entry.triageLevel}")

        await ws_manager.broadcast_event(
            channel=WebSocketChannel.facility_queue(fac_id),
            event_type=WebSocketEventType.QUEUE_UPDATE,
            payload=entry.model_dump(),
        )
        if entry.doctorId:
            await ws_manager.broadcast_event(
                channel=WebSocketChannel.doctor_workspace(entry.doctorId),
                event_type=WebSocketEventType.QUEUE_UPDATE,
                payload=entry.model_dump(),
            )

        return entry

    async def call_patient(self, queue_id: str, req: QueueCallPatientRequest) -> OPDQueueEntry:
        """Doctor calls patient token into a specific consulting room."""
        async with self._lock:
            fac_id, entry = self._find_entry_and_facility(queue_id)
            if not entry or not fac_id:
                raise EntityNotFoundException("OPDQueueEntry", queue_id)

            entry.status = QueueStatus.CALLED
            entry.doctorId = req.doctorId
            if req.doctorName:
                entry.doctorName = req.doctorName
            entry.roomNumber = req.roomNumber
            entry.calledTime = datetime.now(timezone.utc).isoformat()

        logger.info(f"[OPDQueue] Token #{entry.tokenNumber} ({entry.patientName}) called into {req.roomNumber} by {entry.doctorName or req.doctorId}")

        # Broadcast QUEUE_CALLED event
        await ws_manager.broadcast_event(
            channel=WebSocketChannel.facility_queue(fac_id),
            event_type=WebSocketEventType.QUEUE_CALLED,
            payload=entry.model_dump(),
        )
        await ws_manager.broadcast_event(
            channel=WebSocketChannel.doctor_workspace(req.doctorId),
            event_type=WebSocketEventType.QUEUE_CALLED,
            payload=entry.model_dump(),
        )

        return entry

    async def update_status(self, queue_id: str, req: QueueStatusUpdateRequest) -> OPDQueueEntry:
        """Advance queue entry lifecycle (IN_CONSULTATION, COMPLETED, ABSENT, CANCELLED)."""
        async with self._lock:
            fac_id, entry = self._find_entry_and_facility(queue_id)
            if not entry or not fac_id:
                raise EntityNotFoundException("OPDQueueEntry", queue_id)

            entry.status = req.status
            if req.roomNumber:
                entry.roomNumber = req.roomNumber
            if req.notes:
                entry.notes = f"{entry.notes or ''} | {req.notes}".strip(" |")

            now = datetime.now(timezone.utc).isoformat()
            if req.status == QueueStatus.IN_CONSULTATION and not entry.consultationStartTime:
                entry.consultationStartTime = now
            elif req.status == QueueStatus.COMPLETED and not entry.completedTime:
                entry.completedTime = now

        logger.info(f"[OPDQueue] Token #{entry.tokenNumber} status transitioned to {entry.status}")

        await ws_manager.broadcast_event(
            channel=WebSocketChannel.facility_queue(fac_id),
            event_type=WebSocketEventType.QUEUE_UPDATE,
            payload=entry.model_dump(),
        )
        if entry.doctorId:
            await ws_manager.broadcast_event(
                channel=WebSocketChannel.doctor_workspace(entry.doctorId),
                event_type=WebSocketEventType.QUEUE_UPDATE,
                payload=entry.model_dump(),
            )

        return entry

    def get_facility_queue(
        self,
        facility_id: str,
        status_filter: Optional[QueueStatus] = None,
        doctor_id: Optional[str] = None,
    ) -> OPDQueueResponse:
        """Query active facility OPD queue with optional status and doctor filters."""
        facility_records = list(self._queues.get(facility_id, {}).values())

        # Sort primarily by triage urgency (EMERGENT > URGENT > STANDARD > NON_URGENT) and token
        triage_order = {
            TriageLevel.EMERGENT: 0,
            TriageLevel.URGENT: 1,
            TriageLevel.STANDARD: 2,
            TriageLevel.NON_URGENT: 3,
        }

        filtered = facility_records
        if status_filter:
            filtered = [e for e in filtered if e.status == status_filter]
        if doctor_id:
            filtered = [e for e in filtered if e.doctorId == doctor_id]

        # Active waiting sorted by triage urgency, others by token
        def sort_key(e: OPDQueueEntry):
            is_active = e.status in [QueueStatus.WAITING, QueueStatus.CALLED]
            return (0 if is_active else 1, triage_order.get(e.triageLevel, 2), e.tokenNumber)

        sorted_entries = sorted(filtered, key=sort_key)

        waiting_count = sum(1 for e in facility_records if e.status in [QueueStatus.WAITING, QueueStatus.CALLED])
        in_consultation_count = sum(1 for e in facility_records if e.status == QueueStatus.IN_CONSULTATION)
        completed_count = sum(1 for e in facility_records if e.status == QueueStatus.COMPLETED)

        return OPDQueueResponse(
            facilityId=facility_id,
            totalEntries=len(facility_records),
            waitingCount=waiting_count,
            inConsultationCount=in_consultation_count,
            completedCount=completed_count,
            entries=sorted_entries,
        )

    def get_queue_entry(self, queue_id: str) -> Optional[OPDQueueEntry]:
        """Fetch single queue entry by ID."""
        _, entry = self._find_entry_and_facility(queue_id)
        return entry

    def get_queue_stats(self, facility_id: str) -> QueueStatsResponse:
        """Compute live operational queue statistics."""
        entries = list(self._queues.get(facility_id, {}).values())
        waiting_entries = [e for e in entries if e.status in [QueueStatus.WAITING, QueueStatus.CALLED]]

        urgent_count = sum(1 for e in waiting_entries if e.triageLevel == TriageLevel.URGENT)
        emergent_count = sum(1 for e in waiting_entries if e.triageLevel == TriageLevel.EMERGENT)
        completed_today = sum(1 for e in entries if e.status == QueueStatus.COMPLETED)

        avg_wait = 0
        if waiting_entries:
            total_est = sum(e.estimatedWaitMinutes or 15 for e in waiting_entries)
            avg_wait = total_est // len(waiting_entries)

        return QueueStatsResponse(
            facilityId=facility_id,
            activeTokens=len(entries),
            waitingCount=len(waiting_entries),
            urgentCount=urgent_count,
            emergentCount=emergent_count,
            averageWaitMinutes=avg_wait,
            completedToday=completed_today,
        )


# Global singleton instance
opd_queue_service = OpdQueueService()
