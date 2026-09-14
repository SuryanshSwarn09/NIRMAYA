"""Pydantic v2 schemas for DoctorProfile and ABDM Healthcare Professional Registry."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import MedicalSpecialty
from app.schemas.user import UserResponse


class DoctorProfileBase(BaseModel):
    """Clinical credentials and consultation base attributes for doctors."""

    registration_number: str = Field(
        min_length=3,
        max_length=50,
        description="State Medical Council or National Medical Commission registration license",
        examples=["MCI-2015-48219"],
    )
    medical_council: str = Field(
        min_length=2,
        max_length=100,
        description="Issuing medical council or licensing authority",
        examples=["Karnataka Medical Council"],
    )
    specialty: MedicalSpecialty = Field(
        default=MedicalSpecialty.GENERAL_MEDICINE,
        description="Primary clinical specialty mapped to SNOMED-CT / FHIR PractitionerRole",
    )
    qualifications: str = Field(
        min_length=2,
        max_length=255,
        description="Medical degrees and academic credentials",
        examples=["MBBS, MD (General Medicine)"],
    )
    experience_years: int = Field(
        ge=0,
        le=75,
        default=0,
        description="Cumulative years of active clinical practice",
        examples=[8],
    )
    consultation_fee: int = Field(
        ge=0,
        default=500,
        description="Standard consultation fee in Indian National Rupees (INR)",
        examples=[800],
    )
    hospital_affiliation: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Affiliated hospital, clinic, or healthcare institution",
        examples=["Manipal Hospital, Old Airport Road"],
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Clinical biography, areas of interest, and patient care philosophy",
    )
    is_available_for_teleconsult: bool = Field(
        default=True,
        description="Flag indicating availability for remote digital consultations",
    )

    # ABDM Healthcare Professional Registry Identifier
    hpr_id: Optional[str] = Field(
        default=None,
        pattern=r"^[a-zA-Z0-9._]{3,40}@hpr\.abdm$",
        description="Official ABDM Healthcare Professional Registry handle ending in @hpr.abdm",
        examples=["dr.priya.patel@hpr.abdm"],
    )


class DoctorProfileCreate(DoctorProfileBase):
    """Payload for onboarding a verified healthcare practitioner."""

    user_id: Optional[str] = Field(
        default=None,
        description="Associated user account ID (defaults to authenticated caller)",
    )


class DoctorProfileUpdate(BaseModel):
    """Payload for updating doctor practice credentials and fee settings."""

    registration_number: Optional[str] = Field(default=None, min_length=3, max_length=50)
    medical_council: Optional[str] = Field(default=None, min_length=2, max_length=100)
    specialty: Optional[MedicalSpecialty] = None
    qualifications: Optional[str] = Field(default=None, min_length=2, max_length=255)
    experience_years: Optional[int] = Field(default=None, ge=0, le=75)
    consultation_fee: Optional[int] = Field(default=None, ge=0)
    hospital_affiliation: Optional[str] = Field(default=None, max_length=255)
    bio: Optional[str] = Field(default=None, max_length=2000)
    is_available_for_teleconsult: Optional[bool] = None
    hpr_id: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9._]{3,40}@hpr\.abdm$")


class DoctorProfileResponse(DoctorProfileBase):
    """Structured response schema returned for doctor profile queries."""

    id: str = Field(description="Primary UUID4 key of doctor profile")
    user_id: str = Field(description="Associated platform user UUID")
    created_at: datetime = Field(description="Profile creation UTC timestamp")
    updated_at: datetime = Field(description="Profile last modification UTC timestamp")
    user: Optional[UserResponse] = Field(default=None, description="Linked user identity summary")

    model_config = ConfigDict(from_attributes=True)
