"""Pydantic v2 schemas for Day 88: Express 45-Second Doctor Consultation Mode (/doctor).

Defines schemas for:
- Patient drug allergy & contraindication safety profile
- Curated 1-click chief complaint chips (with ICD-10 & SNOMED CT codes)
- 1-click pre-configured medication bundles & plain schedules
- Fast-track atomic encounter submission & live queue advancement
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PatientAllergyItem(BaseModel):
    """Specific verified drug or food allergy entry."""
    substance: str = Field(description="Allergen name (e.g., Penicillin, Sulfa, NSAIDs)", example="Penicillin / Beta-Lactams")
    reaction: str = Field(description="Clinical reaction", example="Anaphylaxis & Bronchospasm")
    severity: str = Field(default="severe", description="mild | moderate | severe | life-threatening", example="severe")
    verification_status: str = Field(default="confirmed", description="confirmed | suspected | refuted")
    recorded_date: str = Field(default="2024-03-15", description="Date allergy recorded (YYYY-MM-DD)")

    model_config = ConfigDict(from_attributes=True)


class PatientAllergyProfile(BaseModel):
    """High-visibility safety banner profile for clinician consultation."""
    patient_id: str = Field(description="Patient Profile UUID")
    patient_name: str = Field(description="Patient full name", example="Arun Kumar Patel")
    has_known_allergies: bool = Field(default=False, description="Whether patient has active drug allergies")
    allergies: List[PatientAllergyItem] = Field(default_factory=list, description="List of recorded allergies")
    contraindications: List[str] = Field(default_factory=list, description="Clinical contraindication guidelines")
    safety_alert_banner: str = Field(
        default="NO KNOWN DRUG ALLERGIES (NKDA)",
        description="High-contrast banner text displayed at top of consultation console",
    )
    is_safe_to_prescribe: bool = Field(default=True, description="Safety clearance flag")

    model_config = ConfigDict(from_attributes=True)


class ChiefComplaintTemplate(BaseModel):
    """1-Click pre-coded chief complaint chip for high-velocity triage."""
    id: str = Field(description="Unique template identifier", example="COMPL-FEVER")
    code: str = Field(description="Short mnemonic code", example="FEVER")
    title: str = Field(description="Clinical condition title", example="Acute Febrile Illness / Viral Fever")
    short_label: str = Field(description="Compact badge label for 1-tap chip", example="Viral Fever")
    icd10_code: str = Field(description="ICD-10 clinical diagnosis code", example="J06.9")
    snomed_ct_code: str = Field(description="SNOMED CT concept identifier", example="105590001")
    typical_duration_days: int = Field(default=3, description="Typical symptomatic duration in days")
    category: str = Field(default="general", description="general | cardio | metabolic | respiratory | pediatric")
    recommended_bundle_id: Optional[str] = Field(default=None, description="Suggested 1-click Rx bundle ID")
    default_advice: str = Field(
        default="Adequate oral hydration, rest, warm saline gargles. Review if fever persists > 3 days.",
        description="Standardized plain-language patient advice",
    )

    model_config = ConfigDict(from_attributes=True)


class QuickPrescriptionItem(BaseModel):
    """Medication line item within an express prescription bundle."""
    medicine_id: str = Field(description="Medication identifier", example="med-pcm-650")
    name: str = Field(description="Brand or formulation name", example="Paracetamol 650mg")
    generic_name: str = Field(description="Active pharmaceutical ingredient", example="Paracetamol")
    dosage_form: str = Field(default="Tablet", description="Tablet | Capsule | Syrup | Drops | Inhaler")
    strength: str = Field(description="Strength concentration", example="650mg")
    morning: bool = Field(default=True, description="Take in morning (breakfast)")
    afternoon: bool = Field(default=False, description="Take in afternoon (lunch)")
    night: bool = Field(default=True, description="Take at night (dinner)")
    frequency_badge: str = Field(default="1-0-1", description="Plain frequency indicator (1-0-1, 1-0-0, 0-0-1, PRN)")
    duration_days: int = Field(default=3, description="Course length in days", example=3)
    instruction: str = Field(default="Take 1 tablet after food with water", description="Plain-language intake instruction")
    allergy_substance_tag: Optional[str] = Field(
        default=None,
        description="Substance category for cross-allergy checks (e.g. penicillin, sulfa, nsaid)",
    )

    model_config = ConfigDict(from_attributes=True)


class PrescriptionBundleTemplate(BaseModel):
    """Complete 1-click prescription regimen bundle for high-frequency complaints."""
    bundle_id: str = Field(description="Bundle identifier", example="BUNDLE-VIRAL-URTI")
    title: str = Field(description="Bundle title", example="Viral Fever & Upper Respiratory Tract Infection (URTI)")
    short_label: str = Field(description="Quick chip label", example="Viral Fever / URTI")
    description: str = Field(description="Clinical intent and guideline context")
    category: str = Field(default="general", description="general | cardio | metabolic | pediatrics | gastrology")
    medications: List[QuickPrescriptionItem] = Field(description="Standardized medication course")
    standard_advice: List[str] = Field(default_factory=list, description="Lifestyle and monitoring recommendations")
    follow_up_days: int = Field(default=5, description="Recommended follow-up interval in days")

    model_config = ConfigDict(from_attributes=True)


class ExpressEncounterSubmitRequest(BaseModel):
    """Atomic submission request for fast-track 45-second OPD encounter completion."""
    patient_id: str = Field(description="Patient Profile UUID")
    doctor_id: str = Field(description="Attending Doctor UUID", example="doc-ananya-sharma")
    doctor_hpr: str = Field(default="ananya.sharma@hpr.abdm", description="Certified ABDM HPR identifier")
    facility_id: str = Field(default="aiims-delhi-01", description="Hospital / OPD Clinic identifier")
    token_number: Optional[str] = Field(default=None, description="Queue token currently being consulted")
    chief_complaints: List[str] = Field(description="Selected complaint tags or text", example=["Viral Fever", "Cough"])
    clinical_diagnosis: str = Field(
        description="Final clinical diagnosis (plain or ICD-10)",
        example="Acute upper respiratory infection [J06.9]",
    )
    icd10_code: Optional[str] = Field(default="J06.9", description="ICD-10 clinical diagnostic code")
    prescribed_medications: List[QuickPrescriptionItem] = Field(
        description="List of medications prescribed in this express encounter",
    )
    clinical_advice: List[str] = Field(default_factory=list, description="Patient advice items")
    follow_up_days: int = Field(default=5, description="Follow-up review in days")
    emergency_escalation: bool = Field(default=False, description="Whether patient requires emergency ward admission")

    model_config = ConfigDict(from_attributes=True)


class ExpressEncounterSubmitResponse(BaseModel):
    """Response returned upon sub-50ms atomic encounter completion and queue advance."""
    encounter_id: str = Field(description="Maligned FHIR Encounter UUID")
    patient_id: str = Field(description="Patient Profile UUID")
    patient_name: str = Field(description="Patient certified full name")
    status: str = Field(default="COMPLETED", description="Encounter status")
    digital_signature_hash: str = Field(description="SHA-256 cryptographic seal of clinical encounter")
    hpr_sign_seal: str = Field(description="Doctor's certified HPR digital signing seal")
    fhir_bundle_id: str = Field(description="ABDM HL7 FHIR R4 Bundle UUID")
    fhir_encounter_uri: str = Field(description="FHIR Encounter canonical URI")
    prescribed_count: int = Field(description="Number of medications prescribed")
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Completion timestamp")
    latency_ms: float = Field(description="End-to-end execution latency in milliseconds")
    next_token_called: Optional[str] = Field(default=None, description="Sequential token of next patient called")
    next_patient_name: Optional[str] = Field(default=None, description="Name of next patient in queue")
    queue_remaining_count: int = Field(default=0, description="Remaining patients in OPD room queue")
    signed_prescription_download_url: str = Field(description="1-Click download URL for signed prescription PDF")

    model_config = ConfigDict(from_attributes=True)
