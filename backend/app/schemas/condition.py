"""Pydantic v2 schemas for ClinicalCondition problem list management.

Aligned with HL7 FHIR Release 4 Condition resource specifications,
supporting SNOMED-CT / ICD-10 diagnostic coding, clinical status lifecycles,
and longitudinal problem tracking.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.enums import (
    ClinicalStatus,
    ConditionCategory,
    ConditionSeverity,
    VerificationStatus,
)


class ConditionBase(BaseModel):
    """Core clinical condition attributes shared across create and response schemas."""

    clinical_status: ClinicalStatus = Field(
        default=ClinicalStatus.ACTIVE,
        description="Clinical status of the condition (active | recurrence | relapse | inactive | remission | resolved)",
        example=ClinicalStatus.ACTIVE,
    )
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.CONFIRMED,
        description="Verification status (unconfirmed | provisional | differential | confirmed | refuted | entered-in-error)",
        example=VerificationStatus.CONFIRMED,
    )
    category: ConditionCategory = Field(
        default=ConditionCategory.PROBLEM_LIST_ITEM,
        description="Condition category (problem-list-item | encounter-diagnosis | chronic-condition)",
        example=ConditionCategory.PROBLEM_LIST_ITEM,
    )
    severity: Optional[ConditionSeverity] = Field(
        default=None,
        description="Subjective severity assessment (mild | moderate | severe)",
        example=ConditionSeverity.MODERATE,
    )
    code_coding_system: str = Field(
        default="http://snomed.info/sct",
        description="URI identifying the terminology system (e.g. SNOMED-CT or ICD-10)",
        example="http://snomed.info/sct",
    )
    code_value: str = Field(
        min_length=1,
        max_length=50,
        description="Clinical terminology code symbol (e.g. 38341003 for Essential Hypertension)",
        example="38341003",
    )
    code_display: str = Field(
        min_length=1,
        max_length=255,
        description="Human-readable concept diagnosis or condition name",
        example="Essential hypertension (disorder)",
    )
    body_site: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Anatomical site or bodily location affected by the condition",
        example="Cardiovascular system",
    )
    onset_date_time: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when condition initially manifested",
    )
    abatement_date_time: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when condition was cured, resolved, or went into remission",
    )
    note: Optional[str] = Field(
        default=None,
        description="Free-text clinical commentary, diagnostic impressions, or patient notes",
        example="Patient reports 3-month history of elevated blood pressure during routine checkups.",
    )

    @model_validator(mode="after")
    def validate_timeline(self) -> "ConditionBase":
        """Verify that abatement date does not precede onset date."""
        if self.onset_date_time and self.abatement_date_time:
            if self.abatement_date_time < self.onset_date_time:
                raise ValueError("abatement_date_time cannot be earlier than onset_date_time")
        return self


class ConditionCreate(ConditionBase):
    """Payload schema for recording a new condition onto a patient's problem list."""

    encounter_id: Optional[str] = Field(
        default=None,
        description="Optional UUID of the clinical encounter/appointment in which condition was diagnosed",
        example="c7a1027b-fb8a-442a-aef2-073010b991b1",
    )


class ConditionUpdate(BaseModel):
    """Payload schema for updating condition status, resolution, or clinical notes."""

    clinical_status: Optional[ClinicalStatus] = Field(
        default=None,
        description="Updated clinical status (e.g. transitioning from active to resolved)",
    )
    verification_status: Optional[VerificationStatus] = Field(
        default=None,
        description="Updated verification status",
    )
    category: Optional[ConditionCategory] = Field(
        default=None,
        description="Updated category classification",
    )
    severity: Optional[ConditionSeverity] = Field(
        default=None,
        description="Updated severity assessment",
    )
    body_site: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Updated anatomical location",
    )
    onset_date_time: Optional[datetime] = Field(
        default=None,
        description="Updated onset date/time",
    )
    abatement_date_time: Optional[datetime] = Field(
        default=None,
        description="Updated abatement / resolution date/time",
    )
    note: Optional[str] = Field(
        default=None,
        description="Appended or updated clinical notes",
    )

    @model_validator(mode="after")
    def validate_update_timeline(self) -> "ConditionUpdate":
        if self.onset_date_time and self.abatement_date_time:
            if self.abatement_date_time < self.onset_date_time:
                raise ValueError("abatement_date_time cannot be earlier than onset_date_time")
        return self


class ConditionResponse(ConditionBase):
    """Response representation of a patient problem list condition."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Unique UUIDv4 condition identifier")
    patient_id: str = Field(description="UUIDv4 of the subject patient")
    encounter_id: Optional[str] = Field(
        default=None,
        description="UUIDv4 of the originating appointment / encounter if applicable",
    )
    recorded_by_doctor_id: Optional[str] = Field(
        default=None,
        description="UUIDv4 of the diagnosing practitioner if recorded by doctor",
    )
    recorded_date: datetime = Field(
        description="UTC timestamp when the condition was recorded into the medical record",
    )
    created_at: datetime = Field(description="System audit creation timestamp")
    updated_at: datetime = Field(description="System audit last update timestamp")


class ConditionFilter(BaseModel):
    """Query parameter filter for querying patient problem lists."""

    clinical_status: Optional[ClinicalStatus] = None
    verification_status: Optional[VerificationStatus] = None
    category: Optional[ConditionCategory] = None
    severity: Optional[ConditionSeverity] = None
    encounter_id: Optional[str] = None
