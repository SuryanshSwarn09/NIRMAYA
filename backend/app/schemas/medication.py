"""Pydantic v2 domain schemas for the clinical medication catalog and formulary.

Aligned with HL7 FHIR Release 4 Medication resource specifications and ABDM NRCeS profiles.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    MedicationForm,
    AdministrationRoute,
    FormularyTier,
    MedicationStatus,
)


class MedicationBase(BaseModel):
    """Base domain properties for clinical medications and formulary entries."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Clinical medication concept display name",
        example="Metformin 500mg Oral Tablet",
    )
    generic_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Active pharmaceutical generic moiety name",
        example="Metformin Hydrochloride",
    )
    brand_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Proprietary commercial trade name if branded",
        example="Glucophage",
    )
    rxnorm_code: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="NLM RxNorm Concept Unique Identifier (RxCUI)",
        example="860975",
    )
    rxnorm_display: Optional[str] = Field(
        default=None,
        max_length=255,
        description="RxNorm canonical concept display text",
        example="Metformin hydrochloride 500 MG Oral Tablet",
    )
    atc_code: Optional[str] = Field(
        default=None,
        max_length=32,
        description="WHO Anatomical Therapeutic Chemical classification code",
        example="A10BA02",
    )
    atc_display: Optional[str] = Field(
        default=None,
        max_length=255,
        description="WHO-ATC therapeutic classification hierarchy display",
        example="Metformin",
    )
    snomed_code: Optional[str] = Field(
        default=None,
        max_length=64,
        description="SNOMED-CT clinical drug or medicinal product concept code",
        example="387048002",
    )
    snomed_display: Optional[str] = Field(
        default=None,
        max_length=255,
        description="SNOMED-CT preferred concept display",
        example="Metformin hydrochloride",
    )
    form: MedicationForm = Field(
        default=MedicationForm.TABLET,
        description="Dose formulation aligned with SNOMED-CT dose form",
        example=MedicationForm.TABLET,
    )
    route: AdministrationRoute = Field(
        default=AdministrationRoute.ORAL,
        description="Physiological administration route",
        example=AdministrationRoute.ORAL,
    )
    strength: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Quantitative dosage strength specification",
        example="500 mg",
    )
    active_ingredient: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Primary active chemical substance ingredient",
        example="Metformin",
    )
    is_prescription_required: bool = Field(
        default=True,
        description="Whether a licensed practitioner prescription is legally required",
    )
    is_controlled_substance: bool = Field(
        default=False,
        description="Whether the drug is a scheduled narcotic or controlled substance",
    )
    formulary_tier: FormularyTier = Field(
        default=FormularyTier.TIER_1_GENERIC,
        description="Insurance coverage formulary tier",
        example=FormularyTier.TIER_1_GENERIC,
    )
    status: MedicationStatus = Field(
        default=MedicationStatus.ACTIVE,
        description="Availability status aligned with FHIR R4 MedicationStatus",
        example=MedicationStatus.ACTIVE,
    )
    description: Optional[str] = Field(
        default=None,
        description="Pharmacology description and clinical indications summary",
    )
    contraindications_summary: Optional[str] = Field(
        default=None,
        description="Known safety warnings, contraindications, and precautions",
    )
    storage_instructions: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Storage condition requirements (temperature, moisture, light)",
    )
    package_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Packaging metadata and unit counts",
    )


class MedicationCreate(MedicationBase):
    """Payload schema for creating a new medication catalog entry."""

    pass


class MedicationUpdate(BaseModel):
    """Payload schema for updating medication catalog properties."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    generic_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    brand_name: Optional[str] = Field(default=None, max_length=255)
    rxnorm_code: Optional[str] = Field(default=None, min_length=1, max_length=64)
    rxnorm_display: Optional[str] = Field(default=None, max_length=255)
    atc_code: Optional[str] = Field(default=None, max_length=32)
    atc_display: Optional[str] = Field(default=None, max_length=255)
    snomed_code: Optional[str] = Field(default=None, max_length=64)
    snomed_display: Optional[str] = Field(default=None, max_length=255)
    form: Optional[MedicationForm] = None
    route: Optional[AdministrationRoute] = None
    strength: Optional[str] = Field(default=None, min_length=1, max_length=64)
    active_ingredient: Optional[str] = Field(default=None, min_length=2, max_length=255)
    is_prescription_required: Optional[bool] = None
    is_controlled_substance: Optional[bool] = None
    formulary_tier: Optional[FormularyTier] = None
    status: Optional[MedicationStatus] = None
    description: Optional[str] = None
    contraindications_summary: Optional[str] = None
    storage_instructions: Optional[str] = None
    package_info: Optional[Dict[str, Any]] = None


class MedicationResponse(MedicationBase):
    """Response schema representing an individual medication catalog entry."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Canonical platform UUID identifier")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last record modification timestamp")


class MedicationListResponse(BaseModel):
    """Paginated collection response for medication catalog queries."""

    total: int = Field(..., description="Total matching medication records count")
    items: List[MedicationResponse] = Field(..., description="List of medication records")
    limit: int = Field(..., description="Requested page record limit")
    offset: int = Field(..., description="Requested page pagination offset")


class TherapeuticClassSummary(BaseModel):
    """Aggregate breakdown of medications by WHO-ATC therapeutic category."""

    atc_prefix: str = Field(..., description="ATC level 1 or level 2 classification prefix")
    name: str = Field(..., description="Therapeutic system category name")
    medication_count: int = Field(..., description="Number of catalog drugs in this category")
