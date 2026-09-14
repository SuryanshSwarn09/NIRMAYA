"""Pydantic v2 schemas for PatientProfile and ABDM ABHA identifiers."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import BloodGroup, Gender
from app.schemas.user import UserResponse


class PatientProfileBase(BaseModel):
    """Clinical demographics and national health identity base attributes."""

    date_of_birth: Optional[date] = Field(
        default=None,
        description="Patient date of birth for age and pediatric calculations",
        examples=["1994-08-15"],
    )
    gender: Gender = Field(
        default=Gender.UNKNOWN,
        description="Administrative gender aligned with HL7 FHIR R4",
    )
    blood_group: BloodGroup = Field(
        default=BloodGroup.UNKNOWN,
        description="ABO/Rh clinical blood group classification",
    )

    # Residential & Geographic Information
    address_line: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Street address or residential landmark",
    )
    city: Optional[str] = Field(
        default=None,
        max_length=100,
        description="City or district of residence",
        examples=["Bengaluru"],
    )
    state: Optional[str] = Field(
        default=None,
        max_length=100,
        description="State or administrative territory",
        examples=["Karnataka"],
    )
    pincode: Optional[str] = Field(
        default=None,
        pattern=r"^[1-9][0-9]{5}$",
        description="6-digit Indian Postal PIN code",
        examples=["560001"],
    )

    # Emergency Contact
    emergency_contact_name: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Full name of designated emergency contact",
    )
    emergency_contact_phone: Optional[str] = Field(
        default=None,
        pattern=r"^\+?[0-9\s\-()]{7,20}$",
        description="Direct telephone number for emergency contact",
    )
    emergency_contact_relation: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Relationship to patient (e.g. Spouse, Parent, Sibling)",
    )

    # Ayushman Bharat Digital Mission (ABDM) Identifiers
    abha_number: Optional[str] = Field(
        default=None,
        pattern=r"^\d{2}-\d{4}-\d{4}-\d{4}$",
        description="14-digit ABDM ABHA Number formatted as XX-XXXX-XXXX-XXXX",
        examples=["12-3456-7890-1234"],
    )
    abha_address: Optional[str] = Field(
        default=None,
        pattern=r"^[a-zA-Z0-9._]{3,30}@abdm$",
        description="Ayushman Bharat Health Account handle ending with @abdm",
        examples=["rahul.sharma@abdm"],
    )


class PatientProfileCreate(PatientProfileBase):
    """Payload for initializing or onboarding a patient profile."""

    user_id: Optional[str] = Field(
        default=None,
        description="Target user ID to bind profile (defaults to authenticated caller)",
    )


class PatientProfileUpdate(BaseModel):
    """Payload for updating existing patient clinical and contact details."""

    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    blood_group: Optional[BloodGroup] = None
    address_line: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    pincode: Optional[str] = Field(default=None, pattern=r"^[1-9][0-9]{5}$")
    emergency_contact_name: Optional[str] = Field(default=None, max_length=150)
    emergency_contact_phone: Optional[str] = Field(default=None, pattern=r"^\+?[0-9\s\-()]{7,20}$")
    emergency_contact_relation: Optional[str] = Field(default=None, max_length=50)
    abha_number: Optional[str] = Field(default=None, pattern=r"^\d{2}-\d{4}-\d{4}-\d{4}$")
    abha_address: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9._]{3,30}@abdm$")


class PatientProfileResponse(PatientProfileBase):
    """Structured response payload returned for patient profiles."""

    id: str = Field(description="Primary UUID4 key of patient profile")
    user_id: str = Field(description="Associated platform user UUID")
    created_at: datetime = Field(description="Profile creation UTC timestamp")
    updated_at: datetime = Field(description="Profile last modification UTC timestamp")
    user: Optional[UserResponse] = Field(default=None, description="Linked user identity summary")

    model_config = ConfigDict(from_attributes=True)
