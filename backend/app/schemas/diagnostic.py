"""Pydantic v2 domain schemas for diagnostic lab orders and diagnostic reports.

Aligned with HL7 FHIR Release 4 ServiceRequest and DiagnosticReport specifications.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    DiagnosticReportStatus,
    ServiceRequestIntent,
    ServiceRequestPriority,
    ServiceRequestStatus,
    SpecimenType,
)
from app.schemas.observation import ObservationResponse


# ============================================================================
# Diagnostic Order Schemas (FHIR ServiceRequest)
# ============================================================================

class DiagnosticOrderBase(BaseModel):
    """Base domain properties for clinical diagnostic service requests."""

    intent: ServiceRequestIntent = Field(
        default=ServiceRequestIntent.ORDER,
        description="Clinical intent of the request",
        example=ServiceRequestIntent.ORDER,
    )
    priority: ServiceRequestPriority = Field(
        default=ServiceRequestPriority.ROUTINE,
        description="Clinical urgency / turnaround priority",
        example=ServiceRequestPriority.ROUTINE,
    )
    category: str = Field(
        default="laboratory",
        max_length=100,
        description="Service category (e.g. laboratory, diagnostic_imaging, pathology)",
        example="laboratory",
    )
    code_coding_system: str = Field(
        default="http://loinc.org",
        description="Diagnostic terminology system URI",
        example="http://loinc.org",
    )
    code_value: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Standard LOINC diagnostic panel/test code",
        example="24331-1",
    )
    code_display: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Human-readable concept name for the diagnostic order",
        example="Lipid panel with direct LDL - Serum or Plasma",
    )
    reason_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional ICD-10 or SNOMED-CT clinical indication code",
        example="I10",
    )
    reason_description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Clinical rationale or indication summary",
        example="Routine hyperlipidemia and cardiovascular risk monitoring",
    )
    specimen_type: Optional[SpecimenType] = Field(
        default=None,
        description="Specimen source (e.g. serum, whole_blood, urine)",
        example=SpecimenType.SERUM,
    )
    notes: Optional[str] = Field(
        default=None,
        description="Special laboratory preparation or clinician notes",
        example="12-hour fasting required prior to specimen collection",
    )


class DiagnosticOrderCreate(DiagnosticOrderBase):
    """Schema for placing a new diagnostic order / requisition."""

    doctor_id: Optional[str] = Field(
        default=None,
        description="Ordering clinician UUID (defaults to authenticated doctor)",
        example="doc-ananya-sharma",
    )
    encounter_id: Optional[str] = Field(
        default=None,
        description="Optional encounter / appointment UUID linkage",
        example="c7a18b4e-2f9a-4c91-a1b7-9d62884a86df",
    )
    status: Optional[ServiceRequestStatus] = Field(
        default=ServiceRequestStatus.ACTIVE,
        description="Initial workflow status (defaults to active)",
        example=ServiceRequestStatus.ACTIVE,
    )


class DiagnosticOrderUpdate(BaseModel):
    """Schema for updating an existing diagnostic order."""

    priority: Optional[ServiceRequestPriority] = None
    status: Optional[ServiceRequestStatus] = None
    notes: Optional[str] = None
    reason_description: Optional[str] = None


class DiagnosticOrderResponse(DiagnosticOrderBase):
    """Schema for serializing a diagnostic order record."""

    id: str = Field(description="Unique order UUID primary key")
    patient_id: str = Field(description="Patient profile UUID foreign key")
    doctor_id: Optional[str] = Field(default=None, description="Ordering clinician UUID")
    encounter_id: Optional[str] = Field(default=None, description="Encounter appointment UUID")
    status: ServiceRequestStatus = Field(description="Order workflow status")
    created_at: datetime = Field(description="UTC order creation timestamp")
    updated_at: datetime = Field(description="UTC last modification timestamp")

    model_config = ConfigDict(from_attributes=True)


class DiagnosticOrderFilter(BaseModel):
    """Filter parameters for querying diagnostic orders."""

    status: Optional[ServiceRequestStatus] = None
    priority: Optional[ServiceRequestPriority] = None
    category: Optional[str] = None
    code_value: Optional[str] = None
    encounter_id: Optional[str] = None


# ============================================================================
# Diagnostic Report Schemas (FHIR DiagnosticReport)
# ============================================================================

class DiagnosticReportBase(BaseModel):
    """Base domain properties for clinical diagnostic reports."""

    category: str = Field(
        default="LAB",
        max_length=100,
        description="Service category code (e.g. LAB, MB, CH, RAD)",
        example="LAB",
    )
    code_coding_system: str = Field(
        default="http://loinc.org",
        description="Terminology coding system URI",
        example="http://loinc.org",
    )
    code_value: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Standard LOINC diagnostic report code",
        example="24331-1",
    )
    code_display: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Diagnostic report display title",
        example="Lipid panel with direct LDL - Serum or Plasma",
    )
    effective_date_time: Optional[datetime] = Field(
        default=None,
        description="Clinically relevant time of specimen draw or exam",
    )
    conclusion: Optional[str] = Field(
        default=None,
        description="Clinical interpretation and conclusion narrative",
        example="Mild elevation in LDL cholesterol; total cholesterol borderline high. Suggest dietary modification and statin surveillance.",
    )
    conclusion_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional SNOMED conclusion code",
        example="13644009",
    )
    is_abnormal: bool = Field(
        default=False,
        description="Flag indicating one or more abnormal test metrics in this report",
        example=True,
    )
    performer_name: Optional[str] = Field(
        default="Metropolis Diagnostics & Pathology Lab",
        max_length=255,
        description="Performing diagnostic facility or laboratory organization display name",
        example="Metropolis Diagnostics & Pathology Lab",
    )
    report_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Key-value metrics snapshot summary (e.g. {'total_cholesterol': 210, 'hdl': 48, 'ldl': 136})",
    )


class DiagnosticReportCreate(DiagnosticReportBase):
    """Schema for issuing a new diagnostic report."""

    order_id: Optional[str] = Field(
        default=None,
        description="Diagnostic order UUID that this report fulfills",
        example="ord-8912-4211",
    )
    encounter_id: Optional[str] = Field(
        default=None,
        description="Clinical encounter / appointment UUID",
        example="c7a18b4e-2f9a-4c91-a1b7-9d62884a86df",
    )
    performer_id: Optional[str] = Field(
        default=None,
        description="Attending pathologist / practitioner doctor UUID",
        example="doc-ananya-sharma",
    )
    status: Optional[DiagnosticReportStatus] = Field(
        default=DiagnosticReportStatus.FINAL,
        description="Report verification status (defaults to final)",
        example=DiagnosticReportStatus.FINAL,
    )
    observation_ids: Optional[List[str]] = Field(
        default_factory=list,
        description="List of ClinicalObservation UUIDs linked as individual results",
    )


class DiagnosticReportUpdate(BaseModel):
    """Schema for updating or amending a diagnostic report."""

    status: Optional[DiagnosticReportStatus] = None
    conclusion: Optional[str] = None
    conclusion_code: Optional[str] = None
    is_abnormal: Optional[bool] = None
    report_data: Optional[Dict[str, Any]] = None


class DiagnosticReportResponse(DiagnosticReportBase):
    """Schema for serializing a complete diagnostic report record."""

    id: str = Field(description="Unique report UUID primary key")
    patient_id: str = Field(description="Patient profile UUID foreign key")
    order_id: Optional[str] = Field(default=None, description="Diagnostic order UUID")
    encounter_id: Optional[str] = Field(default=None, description="Encounter appointment UUID")
    performer_id: Optional[str] = Field(default=None, description="Pathologist/practitioner UUID")
    status: DiagnosticReportStatus = Field(description="Report verification status")
    effective_date_time: datetime = Field(description="Observation timing")
    issued_date_time: datetime = Field(description="UTC timestamp report was officially issued")
    created_at: datetime = Field(description="UTC record creation timestamp")
    updated_at: datetime = Field(description="UTC last modification timestamp")

    model_config = ConfigDict(from_attributes=True)


class DiagnosticReportWithObservationsResponse(DiagnosticReportResponse):
    """Schema for serializing a diagnostic report along with linked observation results."""

    observations: List[ObservationResponse] = Field(
        default_factory=list,
        description="Detailed observation results linked to this diagnostic panel",
    )
