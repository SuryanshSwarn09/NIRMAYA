"""Pydantic v2 domain schemas for Pharmacy Medication Dispense and Fulfillment.

Aligned with HL7 FHIR Release 4 MedicationDispense resource specifications and ABDM NRCeS profiles.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MedicationDispenseStatus
from app.schemas.medication import MedicationResponse


class MedicationDispenseBase(BaseModel):
    """Base fields for recording a pharmaceutical dispensation."""

    quantity_dispensed: float = Field(
        ...,
        gt=0,
        description="Amount of medication dispensed to patient",
        example=30.0,
    )
    dispense_unit: str = Field(
        default="units",
        max_length=50,
        description="Unit of measurement for the dispensed quantity (e.g. 'tablets', 'capsules', 'ml')",
        example="tablets",
    )
    days_supply: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Estimated duration of treatment days covered by this dispensation",
        example=30,
    )
    lot_number: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Manufacturer batch or lot identification number for safety recall traceability",
        example="LOT-2026-X99",
    )
    expiration_date: Optional[date] = Field(
        default=None,
        description="Batch manufacturer expiration date (YYYY-MM-DD)",
        example="2027-12-31",
    )
    when_prepared: Optional[datetime] = Field(
        default=None,
        description="Timestamp when medication was packaged, counted, or prepared (UTC)",
    )
    when_handed_over: Optional[datetime] = Field(
        default=None,
        description="Timestamp when medication was handed over to patient or delivery agent (UTC)",
    )
    was_substituted: bool = Field(
        default=False,
        description="Whether a generic or formulary brand substitution was performed",
    )
    substitution_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="HL7 v3 substanceAdminSubstitution code (e.g. 'G' for generic, 'TE' for therapeutic equivalent)",
        example="G",
    )
    substitution_reason: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Clinical or administrative justification for generic substitution",
        example="Brand out of stock; bioequivalent generic dispensed per prescriber approval",
    )
    dosage_instruction: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Patient administration instructions verified or updated at dispensing time",
        example="Take 1 tablet orally twice daily with meals",
    )
    pharmacist_notes: Optional[str] = Field(
        default=None,
        description="Pharmacist notes, counseling details, or fulfillment comments",
        example="Patient counseled on GI tolerability; take with food.",
    )


class MedicationDispenseCreate(MedicationDispenseBase):
    """Payload to create and fulfill a medication dispensation against an active prescription."""

    prescription_id: str = Field(
        ...,
        description="Foreign key UUID of the authorizing active MedicationRequest prescription",
        example="rx-550e8400-e29b-41d4-a716-446655440000",
    )
    medication_id: Optional[str] = Field(
        default=None,
        description="Optional drug UUID if substituting with generic; defaults to prescribed medication_id if omitted",
        example="med-metformin-500",
    )
    status: MedicationDispenseStatus = Field(
        default=MedicationDispenseStatus.COMPLETED,
        description="Initial lifecycle status (completed, in-progress, preparation)",
    )
    status_reason: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Reason if status is not completed (e.g. declined, stopped, cancelled)",
    )


class MedicationDispenseUpdate(BaseModel):
    """Payload to update an in-progress or active dispensation record."""

    status: Optional[MedicationDispenseStatus] = Field(
        default=None,
        description="Updated fulfillment status",
    )
    status_reason: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Reason for status change",
    )
    when_handed_over: Optional[datetime] = Field(
        default=None,
        description="Recorded handover time",
    )
    pharmacist_notes: Optional[str] = Field(
        default=None,
        description="Additional pharmacist counseling or fulfillment notes",
    )


class MedicationDispenseResponse(MedicationDispenseBase):
    """Response representation of a pharmacy dispensation."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(
        ...,
        description="Primary UUID of this dispensation record",
    )
    dispense_number: str = Field(
        ...,
        description="Human-readable unique business tracking identifier (e.g. DISP-2026-00001)",
    )
    prescription_id: str = Field(
        ...,
        description="UUID of the authorizing MedicationRequest prescription",
    )
    patient_id: str = Field(
        ...,
        description="UUID of the patient receiving the medication",
    )
    medication_id: str = Field(
        ...,
        description="UUID of the catalog medication dispensed",
    )
    dispenser_id: Optional[str] = Field(
        default=None,
        description="UUID of the dispensing pharmacist or clinician user",
    )
    status: MedicationDispenseStatus = Field(
        ...,
        description="Current fulfillment status",
    )
    status_reason: Optional[str] = Field(
        default=None,
        description="Status reason if declined, stopped, or cancelled",
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp (UTC)",
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp (UTC)",
    )
    # Enriched context fields
    medication_name: Optional[str] = Field(
        default=None,
        description="Human-readable brand/generic name of the dispensed medication",
    )
    patient_name: Optional[str] = Field(
        default=None,
        description="Full name of patient",
    )
    dispenser_name: Optional[str] = Field(
        default=None,
        description="Full name of dispensing pharmacist or practitioner",
    )
    medication: Optional[MedicationResponse] = Field(
        default=None,
        description="Full pharmaceutical catalog details of the dispensed drug",
    )


class MedicationDispenseFilter(BaseModel):
    """Query filter parameters for listing pharmacy dispensations."""

    patient_id: Optional[str] = Field(
        default=None,
        description="Filter by patient UUID",
    )
    prescription_id: Optional[str] = Field(
        default=None,
        description="Filter by authorizing prescription UUID",
    )
    status: Optional[MedicationDispenseStatus] = Field(
        default=None,
        description="Filter by dispense lifecycle status",
    )
    lot_number: Optional[str] = Field(
        default=None,
        description="Filter by batch lot number (case-insensitive substring)",
    )
    skip: int = Field(
        default=0,
        ge=0,
        description="Pagination offset",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Pagination limit",
    )
