"""Clinical Alert and Laboratory Panic-Value Schemas for NIRMAYA.

Defines clinical alert categories, severity tiers, lifecycle status,
panic-value threshold models, evaluation requests, and clinician acknowledgment payloads.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.websocket_events import AlertSeverity


class AlertCategory(str, Enum):
    """Classification of clinical notification or panic alert."""

    LAB_PANIC_VALUE = "LAB_PANIC_VALUE"
    CRITICAL_VITALS = "CRITICAL_VITALS"
    APPOINTMENT_CONFIRMED = "APPOINTMENT_CONFIRMED"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    SLOT_HELD = "SLOT_HELD"
    EMERGENCY_BTG_ACCESS = "EMERGENCY_BTG_ACCESS"
    SYSTEM_BROADCAST = "SYSTEM_BROADCAST"


class AlertStatus(str, Enum):
    """Lifecycle status of a clinical alert."""

    UNREAD = "UNREAD"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ESCALATED = "ESCALATED"
    DISMISSED = "DISMISSED"


class LabPanicRule(BaseModel):
    """Clinical threshold rule defining laboratory panic / critical values."""

    loincCode: str = Field(description="LOINC standard observation code")
    testName: str = Field(description="Clinical test / analyte name")
    unit: str = Field(description="Normalized unit of measurement")
    panicLow: Optional[float] = Field(default=None, description="Critical lower boundary triggering PANIC")
    panicHigh: Optional[float] = Field(default=None, description="Critical upper boundary triggering PANIC")
    criticalGuidance: str = Field(description="Clinical guidance / physiological risk narrative")

    model_config = ConfigDict(from_attributes=True)


class LabEvaluationRequest(BaseModel):
    """Diagnostic laboratory observation payload submitted for panic-value evaluation."""

    patientId: str = Field(description="Patient profile UUID")
    patientName: str = Field(description="Patient full display name")
    doctorId: str = Field(description="Ordering or attending clinician UUID")
    facilityId: Optional[str] = Field(default=None, description="Testing laboratory or clinic facility UUID")
    loincCode: str = Field(description="Standard LOINC code for the test")
    testName: str = Field(description="Test / analyte name")
    numericValue: float = Field(description="Measured numerical observation value")
    unit: str = Field(description="Measurement unit")
    referenceRange: Optional[str] = Field(default=None, description="Normal biological reference range")
    specimenSource: Optional[str] = Field(default=None, description="Specimen source (e.g. serum, plasma, arterial blood)")

    model_config = ConfigDict(from_attributes=True)


class LabEvaluationResult(BaseModel):
    """Result of panic-value evaluation for an observation."""

    isPanic: bool = Field(description="Whether the measurement breached panic thresholds")
    severity: AlertSeverity = Field(description="Determined alert severity tier")
    alertGenerated: bool = Field(description="Whether a clinical alert was generated and dispatched")
    alertId: Optional[str] = Field(default=None, description="Created alert UUID if generated")
    ruleMatched: Optional[str] = Field(default=None, description="LOINC or rule identifier matched")
    message: str = Field(description="Clinical outcome summary and guidance")

    model_config = ConfigDict(from_attributes=True)


class AlertCreateRequest(BaseModel):
    """Payload to create and broadcast an arbitrary clinical alert or notification."""

    patientId: str = Field(description="Patient profile UUID")
    patientName: str = Field(description="Patient full display name")
    doctorId: str = Field(description="Target clinician UUID")
    facilityId: Optional[str] = Field(default=None, description="Facility identifier if applicable")
    category: AlertCategory = Field(default=AlertCategory.LAB_PANIC_VALUE, description="Alert category")
    severity: AlertSeverity = Field(default=AlertSeverity.CRITICAL, description="Severity tier")
    title: str = Field(description="Short human-readable headline")
    message: str = Field(description="Clinical description and recommended action")
    loincCode: Optional[str] = Field(default=None, description="LOINC code if applicable")
    observedValue: Optional[str] = Field(default=None, description="Observation value with unit")
    referenceRange: Optional[str] = Field(default=None, description="Biological reference range")
    actionRequired: bool = Field(default=True, description="Whether doctor acknowledgement is required")

    model_config = ConfigDict(from_attributes=True)


class AlertAcknowledgeRequest(BaseModel):
    """Clinician acknowledgment submission for a critical alert."""

    doctorId: str = Field(description="Attending clinician UUID acknowledging the alert")
    clinicalAction: str = Field(
        min_length=3,
        description="Clinical intervention or action taken (e.g. 'Prescribed IV Calcium, transferred to CCU')",
    )
    notes: Optional[str] = Field(default=None, description="Additional clinical notes or rationale")

    model_config = ConfigDict(from_attributes=True)


class ClinicalAlertResponse(BaseModel):
    """Comprehensive clinical alert record."""

    alertId: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique alert record identifier",
    )
    patientId: str = Field(description="Patient profile UUID")
    patientName: str = Field(description="Patient full display name")
    doctorId: str = Field(description="Target clinician UUID")
    facilityId: Optional[str] = Field(default=None, description="Facility identifier")
    category: AlertCategory = Field(description="Alert category")
    severity: AlertSeverity = Field(description="Severity tier")
    status: AlertStatus = Field(default=AlertStatus.UNREAD, description="Current alert lifecycle status")
    title: str = Field(description="Headline summary")
    message: str = Field(description="Clinical narrative")
    loincCode: Optional[str] = Field(default=None, description="Associated LOINC code")
    observedValue: Optional[str] = Field(default=None, description="Observed measurement value")
    referenceRange: Optional[str] = Field(default=None, description="Reference biological range")
    actionRequired: bool = Field(default=True, description="Whether clinician action is required")
    createdAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC creation timestamp",
    )
    acknowledgedAt: Optional[str] = Field(default=None, description="ISO 8601 UTC timestamp of acknowledgement")
    acknowledgedByDoctorId: Optional[str] = Field(default=None, description="Clinician UUID who acknowledged")
    clinicalActionTaken: Optional[str] = Field(default=None, description="Clinical action documented at acknowledgment")

    model_config = ConfigDict(from_attributes=True)


class AlertSummaryStatsResponse(BaseModel):
    """Summary statistics for clinician alert dashboard."""

    doctorId: str = Field(description="Clinician profile UUID")
    totalAlerts: int = Field(description="Total lifetime alerts received")
    unreadCount: int = Field(description="Active unread alerts count")
    panicCount: int = Field(description="Total PANIC tier alerts")
    criticalCount: int = Field(description="Total CRITICAL tier alerts")
    warningCount: int = Field(description="Total WARNING tier alerts")
    infoCount: int = Field(description="Total INFO tier alerts")
    acknowledgedCount: int = Field(description="Total acknowledged alerts")

    model_config = ConfigDict(from_attributes=True)
