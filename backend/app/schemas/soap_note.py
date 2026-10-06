"""Pydantic v2 domain schemas for structured SOAP clinical notes and encounter documentation.

Aligned with HL7 FHIR Release 4 Composition specifications and standard LOINC narrative sections:
- Chief Complaint (LOINC 10154-3)
- Subjective Narrative (LOINC 61150-9)
- Objective Examination (LOINC 61149-1)
- Assessment & Clinical Evaluation (LOINC 51848-0)
- Plan of Care (LOINC 18776-5)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ClinicalNoteStatus, ClinicalNoteType


class SoapNoteBase(BaseModel):
    """Base domain properties for clinical encounter notes."""

    note_type: ClinicalNoteType = Field(
        default=ClinicalNoteType.SOAP,
        description="Clinical note format and classification",
        example=ClinicalNoteType.SOAP,
    )
    title: str = Field(
        default="Clinical Consultation SOAP Note",
        min_length=3,
        max_length=255,
        description="Clinical note document title",
        example="Cardiology Follow-up SOAP Note",
    )
    chief_complaint: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Primary patient complaint or encounter reason",
        example="Exertional chest tightness and shortness of breath for 3 days",
    )
    subjective: str = Field(
        ...,
        min_length=2,
        description="Patient history, symptoms, onset, and chronological narrative (LOINC 61150-9)",
        example="Patient reports progressive dyspnea on exertion. Denies diaphoresis, nausea, or syncope. Adherent to antihypertensives.",
    )
    objective: str = Field(
        ...,
        min_length=2,
        description="Physical examination observations and vital signs review (LOINC 61149-1)",
        example="BP 138/88 mmHg, HR 74 bpm regular, SpO2 98% room air. Heart sounds S1, S2 present, no murmurs. Lungs clear to auscultation bilaterally.",
    )
    assessment: str = Field(
        ...,
        min_length=2,
        description="Clinical impression, clinical status, and differential diagnoses (LOINC 51848-0)",
        example="1. Essential Hypertension, sub-optimally controlled. 2. Exertional Angina, Canadian Cardiovascular Society Class II.",
    )
    plan: str = Field(
        ...,
        min_length=2,
        description="Management plan, prescriptions, diagnostics, and patient instructions (LOINC 18776-5)",
        example="1. Increase Amlodipine to 10mg daily. 2. Requisition resting 12-lead ECG and Lipid Profile. 3. Follow up in 2 weeks or immediate ED visit if symptoms worsen.",
    )
    primary_diagnosis_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Standard ICD-10 or SNOMED-CT primary diagnosis code",
        example="I10",
    )
    primary_diagnosis_display: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Primary diagnosis human-readable concept display",
        example="Essential (primary) hypertension",
    )
    follow_up_instructions: Optional[str] = Field(
        default=None,
        description="Discharge and follow-up clinical instructions for the patient",
        example="Return for blood pressure check in 14 days with fasting lipid panel results.",
    )


class SoapNoteCreate(SoapNoteBase):
    """Schema for creating a new structured SOAP clinical note."""

    encounter_id: Optional[str] = Field(
        default=None,
        description="Optional encounter / appointment UUID linkage",
        example="c7a18b4e-2f9a-4c91-a1b7-9d62884a86df",
    )
    doctor_id: Optional[str] = Field(
        default=None,
        description="Practitioner doctor profile UUID author (defaults to authenticated clinician)",
        example="doc-ananya-sharma",
    )
    status: Optional[ClinicalNoteStatus] = Field(
        default=ClinicalNoteStatus.PRELIMINARY,
        description="Initial clinical status (defaults to preliminary)",
        example=ClinicalNoteStatus.PRELIMINARY,
    )


class SoapNoteUpdate(BaseModel):
    """Schema for updating an existing preliminary SOAP note before final signature."""

    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    chief_complaint: Optional[str] = Field(default=None, min_length=2, max_length=500)
    subjective: Optional[str] = Field(default=None, min_length=2)
    objective: Optional[str] = Field(default=None, min_length=2)
    assessment: Optional[str] = Field(default=None, min_length=2)
    plan: Optional[str] = Field(default=None, min_length=2)
    primary_diagnosis_code: Optional[str] = Field(default=None, max_length=50)
    primary_diagnosis_display: Optional[str] = Field(default=None, max_length=255)
    follow_up_instructions: Optional[str] = None
    status: Optional[ClinicalNoteStatus] = None


class SoapNoteSignRequest(BaseModel):
    """Schema for signing and finalizing a SOAP clinical note."""

    comments: Optional[str] = Field(
        default=None,
        description="Optional signing remarks or clinical attestation statement",
        example="Electronically attested and approved by Dr. Ananya Sharma",
    )


class SoapNoteResponse(SoapNoteBase):
    """Schema for serializing a complete SOAP clinical note record."""

    id: str = Field(description="Unique note UUID primary key")
    patient_id: str = Field(description="Patient profile UUID foreign key")
    doctor_id: Optional[str] = Field(default=None, description="Author clinician UUID")
    encounter_id: Optional[str] = Field(default=None, description="Encounter appointment UUID")
    status: ClinicalNoteStatus = Field(description="Clinical workflow state")
    is_signed: bool = Field(description="Cryptographic digital signature verification status")
    signed_at: Optional[datetime] = Field(default=None, description="UTC timestamp of signature")
    signature_hash: Optional[str] = Field(default=None, description="SHA-256 cryptographic attestation digest")
    created_at: datetime = Field(description="UTC record creation timestamp")
    updated_at: datetime = Field(description="UTC last modification timestamp")

    model_config = ConfigDict(from_attributes=True)


class SoapNoteFilter(BaseModel):
    """Query filter parameters for clinical encounter notes."""

    status: Optional[ClinicalNoteStatus] = None
    note_type: Optional[ClinicalNoteType] = None
    encounter_id: Optional[str] = None
    is_signed: Optional[bool] = None
