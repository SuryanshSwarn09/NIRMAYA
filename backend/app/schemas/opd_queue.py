"""OPD Consultation Queue Schemas for NIRMAYA.

Defines queue lifecycle states, clinical triage classifications, patient check-in
requests, room calling models, queue statistics, and response envelopes.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.websocket_events import TriageLevel


class QueueStatus(str, Enum):
    """Clinical lifecycle states for outpatient consultation queue."""

    WAITING = "WAITING"
    CALLED = "CALLED"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    ABSENT = "ABSENT"
    CANCELLED = "CANCELLED"


# -----------------------------------------------------------------------------
# Queue Record Models
# -----------------------------------------------------------------------------

class OPDQueueEntry(BaseModel):
    """Granular record for a patient registered in a facility's daily OPD queue."""

    queueId: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique queue record UUID",
    )
    facilityId: str = Field(description="Healthcare facility identifier")
    tokenNumber: int = Field(description="Sequential daily OPD token number")
    patientId: str = Field(description="Patient profile UUID")
    patientName: str = Field(description="Patient display name")
    patientAbha: Optional[str] = Field(default=None, description="14-digit ABHA number if linked")
    patientPhone: Optional[str] = Field(default=None, description="Contact phone number")
    doctorId: Optional[str] = Field(default=None, description="Assigned clinician profile UUID")
    doctorName: Optional[str] = Field(default=None, description="Assigned clinician display name")
    status: QueueStatus = Field(default=QueueStatus.WAITING, description="Current queue status")
    triageLevel: TriageLevel = Field(default=TriageLevel.STANDARD, description="Clinical triage level")
    chiefComplaint: Optional[str] = Field(default=None, description="Primary clinical symptom or reason for visit")
    roomNumber: Optional[str] = Field(default=None, description="Consultation room / cubicle number")
    estimatedWaitMinutes: Optional[int] = Field(default=None, description="Estimated wait time in minutes")
    checkInTime: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of patient arrival/check-in",
    )
    calledTime: Optional[str] = Field(default=None, description="ISO 8601 UTC timestamp when patient was called")
    consultationStartTime: Optional[str] = Field(default=None, description="ISO 8601 UTC consultation start time")
    completedTime: Optional[str] = Field(default=None, description="ISO 8601 UTC timestamp when consultation ended")
    notes: Optional[str] = Field(default=None, description="Administrative or nursing notes")

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Request Payloads
# -----------------------------------------------------------------------------

class QueueCheckInRequest(BaseModel):
    """Payload to register and check in an arriving patient at the OPD desk."""

    facilityId: str = Field(description="Facility identifier")
    patientId: str = Field(description="Patient profile UUID")
    patientName: str = Field(description="Patient display name")
    patientAbha: Optional[str] = Field(default=None, description="14-digit ABHA number")
    patientPhone: Optional[str] = Field(default=None, description="Contact phone number")
    doctorId: Optional[str] = Field(default=None, description="Target clinician profile UUID")
    doctorName: Optional[str] = Field(default=None, description="Target clinician display name")
    triageLevel: TriageLevel = Field(default=TriageLevel.STANDARD, description="Initial triage level")
    chiefComplaint: Optional[str] = Field(default=None, description="Reason for visit")
    notes: Optional[str] = Field(default=None, description="Reception or intake notes")

    model_config = ConfigDict(from_attributes=True)


class QueueTriageUpdateRequest(BaseModel):
    """Payload for nurse or triage officer to update patient urgency."""

    triageLevel: TriageLevel = Field(description="Updated clinical triage classification")
    estimatedWaitMinutes: Optional[int] = Field(default=None, description="Adjusted wait time estimate")
    notes: Optional[str] = Field(default=None, description="Triage observation notes")

    model_config = ConfigDict(from_attributes=True)


class QueueCallPatientRequest(BaseModel):
    """Payload for attending doctor to summon patient into consulting room."""

    doctorId: str = Field(description="Clinician profile UUID calling the patient")
    doctorName: Optional[str] = Field(default=None, description="Clinician display name")
    roomNumber: str = Field(description="Consulting room / cubicle number (e.g. 'Room 3')")

    model_config = ConfigDict(from_attributes=True)


class QueueStatusUpdateRequest(BaseModel):
    """Payload to transition queue status (e.g. IN_CONSULTATION, COMPLETED, ABSENT)."""

    status: QueueStatus = Field(description="Target queue lifecycle state")
    roomNumber: Optional[str] = Field(default=None, description="Room number if applicable")
    notes: Optional[str] = Field(default=None, description="Completion or transition notes")

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Response Envelopes
# -----------------------------------------------------------------------------

class OPDQueueResponse(BaseModel):
    """Facility OPD queue listing with breakdown counts."""

    facilityId: str = Field(description="Facility identifier")
    totalEntries: int = Field(description="Total patient entries registered today")
    waitingCount: int = Field(description="Patients currently waiting")
    inConsultationCount: int = Field(description="Patients actively in consultation")
    completedCount: int = Field(description="Consultations completed today")
    entries: List[OPDQueueEntry] = Field(description="List of queue entries matching query")

    model_config = ConfigDict(from_attributes=True)


class QueueStatsResponse(BaseModel):
    """Summary statistics for facility OPD queue monitoring."""

    facilityId: str = Field(description="Facility identifier")
    activeTokens: int = Field(description="Total active tokens in queue today")
    waitingCount: int = Field(description="Patients waiting")
    urgentCount: int = Field(description="Urgent triage patients")
    emergentCount: int = Field(description="Emergent/critical triage patients")
    averageWaitMinutes: int = Field(description="Current estimated average wait time")
    completedToday: int = Field(description="Total patients attended and completed")

    model_config = ConfigDict(from_attributes=True)
