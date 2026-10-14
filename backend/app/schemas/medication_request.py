"""Pydantic v2 domain schemas for electronic prescriptions and medication requests.

Aligned with HL7 FHIR Release 4 MedicationRequest resource specifications and ABDM NRCeS Prescription profiles.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AdministrationRoute,
    MedicationRequestStatus,
    MedicationRequestIntent,
    MedicationRequestPriority,
)
from app.schemas.medication import MedicationResponse


class MedicationRequestBase(BaseModel):
    """Base fields for an electronic prescription / medication request."""

    medication_id: str = Field(
        ...,
        description="Foreign key UUID of the catalog medication",
        example="med-metformin-500",
    )
    encounter_id: Optional[str] = Field(
        default=None,
        description="Optional encounter / appointment UUID context",
    )
    intent: MedicationRequestIntent = Field(
        default=MedicationRequestIntent.ORDER,
        description="Prescription clinical intent (proposal, plan, order)",
    )
    priority: MedicationRequestPriority = Field(
        default=MedicationRequestPriority.ROUTINE,
        description="Prescription urgency (routine, urgent, asap, stat)",
    )
    dosage_text: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Complete human-readable patient dosage instructions",
        example="Take 1 tablet orally twice daily with meals for 14 days",
    )
    dose_quantity: Optional[float] = Field(
        default=None,
        ge=0,
        description="Numerical amount of medication per single dose",
        example=500.0,
    )
    dose_unit: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Unit of measurement for the dose",
        example="mg",
    )
    route: Optional[AdministrationRoute] = Field(
        default=AdministrationRoute.ORAL,
        description="Route of administration",
    )
    frequency: Optional[int] = Field(
        default=None,
        ge=1,
        le=24,
        description="Number of times dosage is repeated per period",
        example=2,
    )
    period: Optional[float] = Field(
        default=1.0,
        ge=0.1,
        description="Duration of time over which frequency is measured",
        example=1.0,
    )
    period_unit: Optional[str] = Field(
        default="d",
        max_length=20,
        description="Unit of time for the frequency period ('s', 'min', 'h', 'd', 'wk', 'mo')",
        example="d",
    )
    as_needed: bool = Field(
        default=False,
        description="Whether medication is to be taken PRN (as needed)",
    )
    as_needed_reason: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Condition or trigger for taking medication PRN",
        example="Take for acute headache or pain exceeding VAS 5",
    )
    additional_instructions: Optional[str] = Field(
        default=None,
        description="Supplemental patient guidance",
        example="Take with a full glass of water. Avoid alcohol.",
    )
    dispense_quantity: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total quantity of medication authorized for pharmacy dispense",
        example=28.0,
    )
    dispense_unit: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Unit of measurement for dispense quantity",
        example="tablets",
    )
    expected_supply_duration_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Number of days expected to be covered by the dispensed quantity",
        example=14,
    )
    number_of_repeats_allowed: int = Field(
        default=0,
        ge=0,
        le=12,
        description="Number of authorized refills/repeats",
        example=0,
    )
    validity_period_start: Optional[datetime] = Field(
        default=None,
        description="Start date/time of prescription validity",
    )
    validity_period_end: Optional[datetime] = Field(
        default=None,
        description="Expiration date/time of prescription validity",
    )
    allow_generic_substitution: bool = Field(
        default=True,
        description="Whether pharmacist may substitute therapeutically equivalent bioequivalent generic",
    )
    substitution_reason: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Reason if substitution is disallowed",
        example="Dispense As Written (DAW) - narrow therapeutic index",
    )
    reason_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Clinical indication / diagnosis code (ICD-10 or SNOMED-CT)",
        example="E11.9",
    )
    reason_reference_id: Optional[str] = Field(
        default=None,
        description="Linked ClinicalCondition UUID on patient's problem list",
    )
    note: Optional[str] = Field(
        default=None,
        description="Clinician remarks or internal notes",
    )


class MedicationRequestCreate(MedicationRequestBase):
    """Schema for authoring a new medication prescription."""
    pass


class MedicationRequestUpdate(BaseModel):
    """Schema for updating an unsigned draft medication prescription."""

    medication_id: Optional[str] = None
    encounter_id: Optional[str] = None
    intent: Optional[MedicationRequestIntent] = None
    priority: Optional[MedicationRequestPriority] = None
    dosage_text: Optional[str] = None
    dose_quantity: Optional[float] = None
    dose_unit: Optional[str] = None
    route: Optional[AdministrationRoute] = None
    frequency: Optional[int] = None
    period: Optional[float] = None
    period_unit: Optional[str] = None
    as_needed: Optional[bool] = None
    as_needed_reason: Optional[str] = None
    additional_instructions: Optional[str] = None
    dispense_quantity: Optional[float] = None
    dispense_unit: Optional[str] = None
    expected_supply_duration_days: Optional[int] = None
    number_of_repeats_allowed: Optional[int] = None
    validity_period_start: Optional[datetime] = None
    validity_period_end: Optional[datetime] = None
    allow_generic_substitution: Optional[bool] = None
    substitution_reason: Optional[str] = None
    reason_code: Optional[str] = None
    reason_reference_id: Optional[str] = None
    note: Optional[str] = None


class MedicationRequestSignRequest(BaseModel):
    """Payload for digitally signing and authorizing an e-prescription."""

    signature_notes: Optional[str] = Field(
        default=None,
        description="Optional signing statement or certification remarks",
    )


class MedicationRequestCancelRequest(BaseModel):
    """Payload for cancelling an active prescription."""

    cancellation_reason: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Clinical rationale for discontinuing / cancelling this prescription",
        example="Adverse gastrointestinal reaction; patient switched to linagliptin.",
    )


class MedicationRequestResponse(MedicationRequestBase):
    """Complete domain representation of an electronic prescription."""

    id: str
    patient_id: str
    doctor_id: Optional[str] = None
    status: MedicationRequestStatus
    authored_on: datetime
    is_signed: bool
    signed_at: Optional[datetime] = None
    signature_hash: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Nested catalog medication metadata (if loaded)
    medication: Optional[MedicationResponse] = None

    model_config = ConfigDict(from_attributes=True)


class MedicationRequestFilter(BaseModel):
    """Query filter parameters for listing patient medication requests."""

    status: Optional[MedicationRequestStatus] = None
    is_signed: Optional[bool] = None
    doctor_id: Optional[str] = None
    encounter_id: Optional[str] = None
    reason_code: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
