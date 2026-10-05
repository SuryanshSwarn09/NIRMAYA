"""Pydantic v2 schemas for ClinicalObservation telemetry and vital signs.

Aligned with HL7 FHIR Release 4 Observation resource specifications,
supporting LOINC clinical codes, multi-component panels (e.g. Blood Pressure),
UCUM unit metrics, and automated physiological reference range interpretation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.enums import (
    ObservationCategory,
    ObservationInterpretation,
    ObservationStatus,
)


class ObservationComponentSchema(BaseModel):
    """Sub-measurement component within a compound observation (e.g. Systolic or Diastolic BP)."""

    code_system: str = Field(
        default="http://loinc.org",
        description="Terminology URI (default: LOINC)",
        example="http://loinc.org",
    )
    code_value: str = Field(
        min_length=1,
        max_length=50,
        description="Component LOINC code (e.g. 8480-6 for Systolic BP)",
        example="8480-6",
    )
    code_display: str = Field(
        min_length=1,
        max_length=255,
        description="Component display name",
        example="Systolic blood pressure",
    )
    value_quantity: float = Field(
        description="Quantitative measurement numerical value",
        example=120.0,
    )
    value_unit: str = Field(
        default="mmHg",
        max_length=50,
        description="Human readable unit of measurement",
        example="mmHg",
    )
    value_code: Optional[str] = Field(
        default="mm[Hg]",
        max_length=50,
        description="Standard UCUM unit code",
        example="mm[Hg]",
    )
    interpretation: Optional[ObservationInterpretation] = Field(
        default=None,
        description="Component level interpretation flag",
        example=ObservationInterpretation.NORMAL,
    )
    reference_range_low: Optional[float] = Field(
        default=None,
        description="Lower physiological reference limit for component",
        example=90.0,
    )
    reference_range_high: Optional[float] = Field(
        default=None,
        description="Upper physiological reference limit for component",
        example=120.0,
    )

    model_config = ConfigDict(from_attributes=True)


class ObservationBase(BaseModel):
    """Core observation attributes shared across create and response schemas."""

    status: ObservationStatus = Field(
        default=ObservationStatus.FINAL,
        description="Clinical status of observation (registered | preliminary | final | amended | etc.)",
        example=ObservationStatus.FINAL,
    )
    category: ObservationCategory = Field(
        default=ObservationCategory.VITAL_SIGNS,
        description="Classification category (vital-signs | laboratory | imaging | exam | etc.)",
        example=ObservationCategory.VITAL_SIGNS,
    )
    code_coding_system: str = Field(
        default="http://loinc.org",
        description="Terminology system URI",
        example="http://loinc.org",
    )
    code_value: str = Field(
        min_length=1,
        max_length=50,
        description="Observation LOINC code (e.g. 8867-4 for Heart rate, 85354-9 for Blood pressure)",
        example="8867-4",
    )
    code_display: str = Field(
        min_length=1,
        max_length=255,
        description="Human-readable concept name",
        example="Heart rate",
    )
    effective_date_time: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when measurement was taken (defaults to now if omitted)",
    )
    value_quantity: Optional[float] = Field(
        default=None,
        description="Numerical result for single quantitative observation",
        example=72.0,
    )
    value_unit: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Human-readable unit of measure (e.g. /min, mmHg, %, Cel, kg/m2)",
        example="/min",
    )
    value_system: Optional[str] = Field(
        default="http://unitsofmeasure.org",
        description="Unit system URI (default: UCUM)",
        example="http://unitsofmeasure.org",
    )
    value_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Standard UCUM unit code",
        example="/min",
    )
    value_string: Optional[str] = Field(
        default=None,
        description="Qualitative or categorical textual finding",
        example=None,
    )
    components: Optional[List[ObservationComponentSchema]] = Field(
        default=None,
        description="List of component sub-measurements for compound panels (e.g. Blood Pressure)",
    )
    reference_range_low: Optional[float] = Field(
        default=None,
        description="Lower physiological reference limit",
        example=60.0,
    )
    reference_range_high: Optional[float] = Field(
        default=None,
        description="Upper physiological reference limit",
        example=100.0,
    )
    reference_range_text: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Textual representation of reference range",
        example="60 - 100 /min",
    )
    interpretation: Optional[ObservationInterpretation] = Field(
        default=None,
        description="Interpretation flag (normal | high | low | critically-high | abnormal)",
        example=ObservationInterpretation.NORMAL,
    )
    body_site: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Anatomical site of measurement (e.g. Right arm, Oral)",
        example="Right arm",
    )
    method: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Measurement technique or instrument (e.g. Automated pulse oximetry)",
        example="Automated pulse oximetry",
    )
    note: Optional[str] = Field(
        default=None,
        description="Clinical commentary or diagnostic impression",
        example="Resting pulse measured after 5 minutes of seated relaxation.",
    )

    model_config = ConfigDict(from_attributes=True)


class ObservationCreate(ObservationBase):
    """Payload schema for recording a new observation or vital sign."""

    encounter_id: Optional[str] = Field(
        default=None,
        description="Optional UUID of clinical encounter/appointment in which observation was performed",
        example="c7a1027b-fb8a-442a-aef2-073010b991b1",
    )

    @model_validator(mode="after")
    def validate_and_auto_interpret(self) -> "ObservationCreate":
        """Validate payload integrity and auto-compute interpretation flag if reference limits exist."""
        # 1. Require at least one value representation
        has_qty = self.value_quantity is not None
        has_str = bool(self.value_string and self.value_string.strip())
        has_comps = bool(self.components and len(self.components) > 0)

        if not (has_qty or has_str or has_comps):
            raise ValueError(
                "Observation must contain at least one of value_quantity, value_string, or components"
            )

        # 2. Automated interpretation calculation for single quantitative measurements
        if self.interpretation is None and self.value_quantity is not None:
            val = self.value_quantity
            low = self.reference_range_low
            high = self.reference_range_high

            if low is not None and val < low:
                self.interpretation = ObservationInterpretation.LOW
            elif high is not None and val > high:
                self.interpretation = ObservationInterpretation.HIGH
            elif low is not None or high is not None:
                self.interpretation = ObservationInterpretation.NORMAL

        return self


class ObservationUpdate(BaseModel):
    """Payload schema for updating observation status, interpretation, or notes."""

    status: Optional[ObservationStatus] = Field(
        default=None,
        description="Updated status (e.g. final, amended, cancelled)",
    )
    interpretation: Optional[ObservationInterpretation] = Field(
        default=None,
        description="Updated clinical interpretation",
    )
    note: Optional[str] = Field(
        default=None,
        description="Additional diagnostic note or addendum",
    )

    model_config = ConfigDict(from_attributes=True)


class ObservationResponse(ObservationBase):
    """Full serialized clinical observation entity for API responses."""

    id: str = Field(description="Unique UUID string identifier")
    patient_id: str = Field(description="Foreign key UUID of subject patient")
    encounter_id: Optional[str] = Field(default=None, description="Linked encounter UUID")
    performer_doctor_id: Optional[str] = Field(default=None, description="Recording doctor UUID")
    effective_date_time: datetime = Field(description="UTC timestamp of measurement")
    issued_date_time: datetime = Field(description="UTC timestamp when record was issued")
    created_at: datetime = Field(description="Record creation timestamp")
    updated_at: datetime = Field(description="Last record modification timestamp")

    model_config = ConfigDict(from_attributes=True)


class ObservationFilter(BaseModel):
    """Filter parameters for querying longitudinal patient observations."""

    category: Optional[ObservationCategory] = None
    code_value: Optional[str] = None
    status: Optional[ObservationStatus] = None
    encounter_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class VitalsSummaryResponse(BaseModel):
    """Synthesized clinical vitals dashboard summary with latest patient readings."""

    blood_pressure: Optional[ObservationResponse] = Field(
        default=None,
        description="Most recent Blood Pressure panel (LOINC 85354-9)",
    )
    heart_rate: Optional[ObservationResponse] = Field(
        default=None,
        description="Most recent Heart Rate measurement (LOINC 8867-4)",
    )
    respiratory_rate: Optional[ObservationResponse] = Field(
        default=None,
        description="Most recent Respiratory Rate measurement (LOINC 9279-1)",
    )
    body_temperature: Optional[ObservationResponse] = Field(
        default=None,
        description="Most recent Body Temperature measurement (LOINC 8310-5)",
    )
    oxygen_saturation: Optional[ObservationResponse] = Field(
        default=None,
        description="Most recent SpO2 measurement (LOINC 2708-6)",
    )
    body_mass_index: Optional[ObservationResponse] = Field(
        default=None,
        description="Most recent Body Mass Index measurement (LOINC 39156-5)",
    )
    weight: Optional[ObservationResponse] = Field(
        default=None,
        description="Most recent Body Weight measurement (LOINC 29463-7)",
    )
    height: Optional[ObservationResponse] = Field(
        default=None,
        description="Most recent Body Height measurement (LOINC 8302-2)",
    )
    blood_glucose: Optional[ObservationResponse] = Field(
        default=None,
        description="Most recent Fasting Blood Glucose measurement (LOINC 1558-6)",
    )
    last_recorded_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of most recent measurement across all vitals",
    )

    model_config = ConfigDict(from_attributes=True)
