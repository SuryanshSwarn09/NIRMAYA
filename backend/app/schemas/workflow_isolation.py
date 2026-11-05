import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextTypeEnum(str, Enum):
    """Clinical persona context for workflow isolation."""
    SELF = "SELF"
    PEDIATRIC_MINOR = "PEDIATRIC_MINOR"
    GERIATRIC_SENIOR = "GERIATRIC_SENIOR"


class VaccinationStatusEnum(str, Enum):
    """Administration status under India Universal Immunization Programme (UIP)."""
    ADMINISTERED = "ADMINISTERED"
    SCHEDULED = "SCHEDULED"
    OVERDUE = "OVERDUE"


class NutritionalStatusEnum(str, Enum):
    """WHO growth standards nutritional evaluation categories."""
    NORMAL = "NORMAL"
    MODERATE_WASTING = "MODERATE_WASTING"
    SEVERE_WASTING = "SEVERE_WASTING"
    STUNTING = "STUNTING"
    OVERWEIGHT = "OVERWEIGHT"


class FallRiskCategoryEnum(str, Enum):
    """Timed Up and Go (TUG) mobility and fall risk grading."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class DependentContextSummary(BaseModel):
    """Summary of an available patient context for session switching."""
    patient_id: str = Field(..., description="Unique sovereign PatientProfile UUID")
    display_name: str = Field(..., description="Legal demographic name")
    abha_number: Optional[str] = Field("14-XXXX-XXXX-XXXX", description="14-digit ABDM ABHA Number or handle")
    context_type: ContextTypeEnum = Field(..., description="Categorization of clinical context")
    age: int = Field(..., description="Chronological age in years")
    gender: str = Field(..., description="Administrative gender (Male/Female/Other)")
    proxy_relationship_id: Optional[str] = Field(None, description="Active relationship ID if dependent")
    relationship_type: Optional[str] = Field(None, description="Relationship to guardian (e.g. CHILD_MINOR, PARENT_SENIOR)")
    access_scope: Optional[str] = Field(None, description="Permitted proxy delegation scope")
    is_active_context: bool = Field(False, description="Flag indicating if currently active in vault session")
    zero_contamination_isolated: bool = Field(True, description="Certification of boundary isolation")


class PediatricImmunizationMilestone(BaseModel):
    """Individual vaccine dose under National Universal Immunization Programme (UIP)."""
    milestone_id: str = Field(..., description="Unique milestone ID")
    vaccine_code: str = Field(..., description="Standard UIP vaccine identifier (e.g. BCG, OPV-0, PENTA-1)")
    vaccine_name: str = Field(..., description="Full vaccine name")
    target_age_display: str = Field(..., description="Prescribed age milestone (e.g. At Birth, 6 Weeks, 9 Months)")
    status: VaccinationStatusEnum = Field(..., description="Current status")
    dose_number: int = Field(1, ge=1, le=5, description="Dose sequence index")
    administered_date: Optional[str] = Field(None, description="ISO timestamp of administration")
    administered_facility: Optional[str] = Field(None, description="Hospital or clinic name")
    administered_by_hpr: Optional[str] = Field(None, description="Healthcare Professional Registry ID of vaccinator")
    batch_number: Optional[str] = Field(None, description="Vaccine manufacturer lot/batch number")
    adverse_events_reported: bool = Field(False, description="Adverse Event Following Immunization (AEFI) flag")


class PediatricGrowthObservation(BaseModel):
    """Child anthropometric growth telemetry mapped to WHO standards."""
    observation_id: str = Field(..., description="Unique observation ID")
    child_patient_id: str = Field(..., description="Target minor patient UUID")
    age_months: int = Field(..., ge=0, le=216, description="Age in completed months")
    recorded_date: str = Field(..., description="ISO observation date")
    weight_kg: float = Field(..., ge=0.5, le=150.0, description="Body weight in kilograms")
    height_cm: float = Field(..., ge=20.0, le=220.0, description="Stature/height in centimeters")
    head_circumference_cm: Optional[float] = Field(None, ge=15.0, le=70.0, description="Head circumference in centimeters")
    who_weight_percentile: int = Field(..., ge=1, le=99, description="WHO weight-for-age percentile rank")
    who_height_percentile: int = Field(..., ge=1, le=99, description="WHO length/height-for-age percentile rank")
    nutritional_status: NutritionalStatusEnum = Field(..., description="Clinical nutritional status")


class GeriatricAssessmentProfile(BaseModel):
    """Comprehensive Geriatric Assessment (CGA) and polypharmacy evaluation."""
    senior_patient_id: str = Field(..., description="Target senior patient UUID")
    assessed_date: str = Field(..., description="ISO assessment timestamp")
    frailty_score: int = Field(..., ge=0, le=5, description="Fried Frailty Phenotype score (0=Robust, 1-2=Pre-frail, 3-5=Frail)")
    frailty_status: str = Field(..., description="Categorical frailty interpretation")
    fall_risk_category: FallRiskCategoryEnum = Field(..., description="Fall risk severity")
    timed_up_and_go_seconds: float = Field(..., ge=1.0, le=120.0, description="Timed Up and Go (TUG) mobility time in seconds")
    polypharmacy_count: int = Field(..., ge=0, description="Number of concurrent active systemic drugs")
    beers_criteria_alerts: List[Dict[str, str]] = Field(default_factory=list, description="Beers Criteria drug-interaction safety warnings")
    adl_score: int = Field(..., ge=0, le=6, description="Katz Index of Independence in Activities of Daily Living (0=Dependent, 6=Independent)")
    cognitive_screening_result: str = Field(..., description="Cognitive evaluation status (Mini-Cog)")
    caregiver_notes: Optional[str] = Field(None, description="Optional clinical observations from guardian/caregiver")


class WorkflowSwitchRequest(BaseModel):
    """Payload to transition active session to a dependent or personal context."""
    target_patient_id: str = Field(..., description="PatientProfile UUID to switch into")
    requested_by_user_id: str = Field(..., description="Authenticated guardian user ID")


class WorkflowSwitchResponse(BaseModel):
    """Response containing isolated context configuration and allowed views."""
    active_context: DependentContextSummary
    permitted_views: List[str] = Field(..., description="List of segmented EHR view identifiers for this context")
    isolation_session_id: str = Field(..., description="Cryptographic session proof of zero-contamination isolation")
    switched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    zero_contamination_verified: bool = Field(True, description="Enforcement of cross-record boundary isolation")
