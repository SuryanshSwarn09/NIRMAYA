"""Pydantic v2 domain schemas for Clinical Decision Support (CDS) Safety Engine.

Provides models for drug-drug interaction alerts, allergy cross-reactivity warnings,
condition contraindications, and clinician override audits.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CDSAlertType, CDSSeverity


class SafetyAlert(BaseModel):
    """Individual clinical decision support safety alert."""

    model_config = ConfigDict(from_attributes=True)

    rule_id: str = Field(
        ...,
        description="Unique rule code or standard catalog ID (e.g. 'DDI-001', 'ALLERGY-BETA-LACTAM')",
    )
    alert_type: CDSAlertType = Field(
        ...,
        description="Type of clinical alert: drug-drug, drug-allergy, or drug-condition",
    )
    severity: CDSSeverity = Field(
        ...,
        description="Severity tier: critical, major, or moderate",
    )
    title: str = Field(
        ...,
        description="Human-readable warning title",
    )
    offending_entity: str = Field(
        ...,
        description="The interacting drug, allergen, or clinical condition that triggered this rule",
    )
    mechanism: str = Field(
        ...,
        description="Clinical / pharmacological mechanism of the adverse interaction",
    )
    recommendation: str = Field(
        ...,
        description="Actionable clinical guidance and alternative management recommendation",
    )


class SafetyCheckRequest(BaseModel):
    """Payload for initiating a pre-prescription safety check."""

    model_config = ConfigDict(from_attributes=True)

    medication_id: str = Field(
        ...,
        description="UUID of the candidate medication to evaluate",
    )
    patient_id: Optional[str] = Field(
        None,
        description="UUID of the patient whose longitudinal record will be evaluated",
    )
    dosage_text: Optional[str] = Field(
        None,
        description="Optional dosage specification for context",
    )
    supplemental_allergies: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional ad-hoc or reported allergies to cross-reference (e.g. ['Penicillin', 'Sulfa'])",
    )
    supplemental_conditions: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional ad-hoc conditions or diagnoses to evaluate (e.g. ['Chronic Kidney Disease'])",
    )


class SafetyCheckResponse(BaseModel):
    """Consolidated safety check evaluation report."""

    model_config = ConfigDict(from_attributes=True)

    passed: bool = Field(
        ...,
        description="True if zero critical contraindications or severe life-threatening alerts are present",
    )
    has_critical_alerts: bool = Field(
        ...,
        description="True if one or more critical alerts were triggered",
    )
    has_major_alerts: bool = Field(
        ...,
        description="True if one or more major alerts were triggered",
    )
    has_moderate_alerts: bool = Field(
        ...,
        description="True if one or more moderate alerts were triggered",
    )
    total_alerts: int = Field(
        ...,
        description="Total number of active alerts detected",
    )
    requires_override: bool = Field(
        ...,
        description="True if clinician must provide explicit clinical override documentation to proceed",
    )
    candidate_medication_name: str = Field(
        ...,
        description="Full clinical name of the evaluated candidate medication",
    )
    candidate_generic_name: str = Field(
        ...,
        description="Generic pharmacological name of candidate medication",
    )
    alerts: List[SafetyAlert] = Field(
        default_factory=list,
        description="Ranked list of detected safety alerts (Critical first, then Major, then Moderate)",
    )


class ClinicianOverrideRequest(BaseModel):
    """Payload for submitting a clinical override when prescribing flagged medications."""

    model_config = ConfigDict(from_attributes=True)

    override_reason: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Clinical rationale justifying why benefit outweighs the flagged interaction risk",
    )
    overridden_by_doctor_id: str = Field(
        ...,
        description="UUID of the clinician authorizing this override",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of clinical override",
    )
