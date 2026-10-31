"""WebSocket & Distributed Pub/Sub Event Schemas for NIRMAYA.

Defines clinical event types, channel structures, typed payloads, client commands,
and diagnostic metrics models for real-time WebSocket communication.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class WebSocketEventType(str, Enum):
    """Enumeration of standard real-time clinical and system event types."""

    CONNECTION_ACK = "connection.ack"
    HEARTBEAT_PING = "heartbeat.ping"
    HEARTBEAT_PONG = "heartbeat.pong"
    QUEUE_UPDATE = "queue.update"
    QUEUE_CALLED = "queue.called"
    CRITICAL_ALERT = "clinical.critical_alert"
    APPOINTMENT_HOLD = "appointment.hold_update"
    SYSTEM_NOTIFICATION = "system.notification"
    SUBSCRIBE_CHANNEL = "channel.subscribe"
    UNSUBSCRIBE_CHANNEL = "channel.unsubscribe"


class TriageLevel(str, Enum):
    """Clinical triage classification for outpatient department (OPD) queue."""

    EMERGENT = "EMERGENT"      # Immediate attention required (Red)
    URGENT = "URGENT"          # Attention within 15 minutes (Yellow)
    STANDARD = "STANDARD"      # Routine OPD order (Green)
    NON_URGENT = "NON_URGENT"  # Minor / administrative (Blue)


class AlertSeverity(str, Enum):
    """Severity tier for clinical panic-values and patient alerts."""

    PANIC = "PANIC"            # Immediate life-threatening value (e.g., severe hyperkalemia)
    CRITICAL = "CRITICAL"      # Urgent physician intervention required
    WARNING = "WARNING"        # Abnormal threshold requiring monitoring
    INFO = "INFO"              # Clinical information update


class HoldStatus(str, Enum):
    """Status for temporary slot holds in the appointment engine."""

    HELD = "HELD"
    RELEASED = "RELEASED"
    BOOKED = "BOOKED"


# -----------------------------------------------------------------------------
# Channel Naming Utility
# -----------------------------------------------------------------------------

class WebSocketChannel:
    """Canonical channel formatting helpers for Redis Pub/Sub."""

    GLOBAL_EVENTS = "global:events"

    @staticmethod
    def facility_queue(facility_id: str) -> str:
        """Channel for a specific hospital or clinic facility OPD queue."""
        return f"facility:{facility_id}:queue"

    @staticmethod
    def doctor_workspace(doctor_id: str) -> str:
        """Channel for a specific clinician workspace (alerts, consult calls)."""
        return f"doctor:{doctor_id}:workspace"

    @staticmethod
    def patient_vault(patient_id: str) -> str:
        """Channel for a specific patient health vault (records, appointments)."""
        return f"patient:{patient_id}:vault"


# -----------------------------------------------------------------------------
# Typed Event Payloads
# -----------------------------------------------------------------------------

class QueueUpdatePayload(BaseModel):
    """Payload for live OPD patient queue status changes."""

    facilityId: str = Field(description="Facility or clinic identifier")
    queueEntryId: str = Field(description="Unique queue record ID")
    patientId: str = Field(description="Patient profile UUID")
    patientName: str = Field(description="Patient display name")
    tokenNumber: int = Field(description="Daily OPD sequence token number")
    status: str = Field(description="Queue status (e.g. WAITING, IN_TRIAGE, IN_CONSULTATION, COMPLETED)")
    triageLevel: TriageLevel = Field(default=TriageLevel.STANDARD, description="Clinical triage level")
    doctorId: Optional[str] = Field(default=None, description="Attending clinician profile UUID")
    estimatedWaitMinutes: Optional[int] = Field(default=None, description="Estimated wait time in minutes")
    updatedAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of status update",
    )

    model_config = ConfigDict(from_attributes=True)


class CriticalAlertPayload(BaseModel):
    """Payload for critical laboratory panic-values or vitals anomalies."""

    alertId: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique alert identifier",
    )
    patientId: str = Field(description="Patient profile UUID")
    patientName: str = Field(description="Patient display name")
    doctorId: str = Field(description="Target clinician profile UUID")
    severity: AlertSeverity = Field(description="Clinical alert severity")
    category: str = Field(description="Alert category: LAB_PANIC_VALUE, CRITICAL_VITALS, CONTRAINDICATION")
    title: str = Field(description="Short human-readable alert title")
    message: str = Field(description="Clinical narrative and recommended action")
    loincCode: Optional[str] = Field(default=None, description="LOINC code if lab or vital alert")
    observedValue: Optional[str] = Field(default=None, description="Measured clinical value with units")
    referenceRange: Optional[str] = Field(default=None, description="Normal biological reference range")
    actionRequired: bool = Field(default=True, description="Whether immediate action/acknowledgement is needed")
    createdAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of alert creation",
    )

    model_config = ConfigDict(from_attributes=True)


class AppointmentHoldPayload(BaseModel):
    """Payload for slot reservation status broadcasts."""

    slotId: str = Field(description="Doctor slot UUID")
    doctorId: str = Field(description="Clinician profile UUID")
    patientId: Optional[str] = Field(default=None, description="Patient UUID holding the slot")
    status: HoldStatus = Field(description="Slot hold status")
    heldAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when hold was established",
    )
    expiresAt: Optional[str] = Field(
        default=None,
        description="ISO 8601 UTC timestamp when hold expires",
    )

    model_config = ConfigDict(from_attributes=True)


class SystemNotificationPayload(BaseModel):
    """Payload for administrative system-wide notifications."""

    notificationId: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique notification identifier",
    )
    title: str = Field(description="Notification headline")
    message: str = Field(description="Notification body text")
    level: str = Field(default="INFO", description="Severity level: INFO, WARNING, ERROR")
    targetRoles: List[str] = Field(
        default_factory=list,
        description="Role filter if targeted to specific user roles",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp",
    )

    model_config = ConfigDict(from_attributes=True)


class ConnectionAckPayload(BaseModel):
    """Payload returned immediately upon successful WebSocket authentication handshake."""

    connectionId: str = Field(description="Session connection UUID")
    userId: str = Field(description="Authenticated user profile UUID")
    role: str = Field(description="User clinical role (PATIENT, DOCTOR, LAB_TECHNICIAN, ADMIN)")
    subscribedChannels: List[str] = Field(description="Initial auto-subscribed channels")
    heartbeatIntervalSeconds: int = Field(description="Server heartbeat ping interval in seconds")
    serverTime: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Current server ISO 8601 UTC time",
    )

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Base Event Envelope
# -----------------------------------------------------------------------------

class WebSocketBaseEvent(BaseModel):
    """Canonical event envelope delivered over WebSocket channels."""

    eventId: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event UUID",
    )
    eventType: WebSocketEventType = Field(description="Registered clinical or system event type")
    channel: str = Field(description="Channel name event was published to")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC event generation timestamp",
    )
    payload: Dict[str, Any] = Field(description="Structured event payload dictionary")

    model_config = ConfigDict(from_attributes=True)


class ClientCommand(BaseModel):
    """Client command message received over WebSocket stream."""

    action: str = Field(description="Command action: subscribe, unsubscribe, ping, pong")
    channel: Optional[str] = Field(default=None, description="Target channel for subscribe/unsubscribe")
    timestamp: Optional[str] = Field(default=None, description="Client timestamp")

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Management & Diagnostics Models
# -----------------------------------------------------------------------------

class WebSocketMetricsResponse(BaseModel):
    """Diagnostic system metrics for WebSocket gateway and Pub/Sub message bus."""

    activeConnections: int = Field(description="Total connected WebSocket clients")
    activeUsers: int = Field(description="Distinct authenticated users connected")
    totalSubscribedChannels: int = Field(description="Total active channel subscriptions")
    channelSubscribers: Dict[str, int] = Field(description="Mapping of channel name to subscriber count")
    redisConnected: bool = Field(description="Whether Redis Pub/Sub adapter is actively connected")
    adapterMode: str = Field(description="Adapter execution mode: 'REDIS' or 'IN_MEMORY'")
    messagesPublishedTotal: int = Field(description="Lifetime messages published to message bus")
    messagesDeliveredTotal: int = Field(description="Lifetime messages delivered to WebSocket clients")

    model_config = ConfigDict(from_attributes=True)


class AdminBroadcastRequest(BaseModel):
    """Administrative request to publish an event onto a channel."""

    channel: str = Field(description="Destination channel name")
    eventType: WebSocketEventType = Field(description="Event classification")
    payload: Dict[str, Any] = Field(description="Arbitrary event payload")

    model_config = ConfigDict(from_attributes=True)

