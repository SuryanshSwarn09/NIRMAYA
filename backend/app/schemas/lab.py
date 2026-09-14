"""Pydantic v2 schemas for DiagnosticLabFacility and ABDM Health Facility Registry."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.enums import LabAccreditation
from app.schemas.user import UserResponse


class DiagnosticLabFacilityBase(BaseModel):
    """Accredited diagnostic facility base attributes and licensing information."""

    facility_name: str = Field(
        min_length=2,
        max_length=255,
        description="Official registered name of the diagnostic testing center",
        examples=["MaxPath Diagnostic Research Laboratories"],
    )
    license_number: str = Field(
        min_length=3,
        max_length=100,
        description="Clinical laboratory operational license number",
        examples=["LAB-KA-2023-9901"],
    )
    accreditation: LabAccreditation = Field(
        default=LabAccreditation.NABL,
        description="Recognized national or international accreditation standard",
    )
    accreditation_number: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Official accreditation certificate identifier",
        examples=["MC-5421"],
    )
    is_nabl_certified: bool = Field(
        default=True,
        description="Flag indicating NABL ISO 15189 compliance status",
    )

    # Administrative & Contact Information
    contact_person: str = Field(
        min_length=2,
        max_length=150,
        description="Chief laboratory administrator or senior pathologist",
        examples=["Dr. Anand Verma"],
    )
    contact_phone: str = Field(
        pattern=r"^\+?[0-9\s\-()]{7,20}$",
        description="Laboratory direct inquiries telephone number",
        examples=["+918012345678"],
    )
    contact_email: EmailStr = Field(
        description="Official electronic mail address for lab reports dispatch",
        examples=["reports@maxpathlabs.com"],
    )

    # Geographic Location
    address_line: str = Field(
        min_length=3,
        max_length=255,
        description="Physical street address and laboratory wing",
        examples=["Sector 4, HSR Layout"],
    )
    city: str = Field(
        min_length=2,
        max_length=100,
        description="City or district of the diagnostic facility",
        examples=["Bengaluru"],
    )
    state: str = Field(
        min_length=2,
        max_length=100,
        description="State or administrative territory",
        examples=["Karnataka"],
    )
    pincode: str = Field(
        pattern=r"^[1-9][0-9]{5}$",
        description="6-digit Indian Postal PIN code",
        examples=["560102"],
    )

    # Capabilities & Testing Catalog
    supported_tests: Optional[str] = Field(
        default=None,
        description="Common diagnostic panels supported (e.g. CBC, Lipid Profile, HbA1c, LFT, KFT)",
    )

    # ABDM Health Facility Registry Identifier
    hfr_id: Optional[str] = Field(
        default=None,
        pattern=r"^IN-[A-Z]{2}-HFR-\d{6}$",
        description="Official ABDM Health Facility Registry ID format: IN-STATE-HFR-XXXXXX",
        examples=["IN-KA-HFR-004521"],
    )


class DiagnosticLabFacilityCreate(DiagnosticLabFacilityBase):
    """Payload for registering an accredited diagnostic laboratory facility."""

    user_id: Optional[str] = Field(
        default=None,
        description="Associated lab administrator user account ID",
    )


class DiagnosticLabFacilityUpdate(BaseModel):
    """Payload for updating facility credentials and contact information."""

    facility_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    license_number: Optional[str] = Field(default=None, min_length=3, max_length=100)
    accreditation: Optional[LabAccreditation] = None
    accreditation_number: Optional[str] = Field(default=None, max_length=100)
    is_nabl_certified: Optional[bool] = None
    contact_person: Optional[str] = Field(default=None, min_length=2, max_length=150)
    contact_phone: Optional[str] = Field(default=None, pattern=r"^\+?[0-9\s\-()]{7,20}$")
    contact_email: Optional[EmailStr] = None
    address_line: Optional[str] = Field(default=None, min_length=3, max_length=255)
    city: Optional[str] = Field(default=None, min_length=2, max_length=100)
    state: Optional[str] = Field(default=None, min_length=2, max_length=100)
    pincode: Optional[str] = Field(default=None, pattern=r"^[1-9][0-9]{5}$")
    supported_tests: Optional[str] = None
    hfr_id: Optional[str] = Field(default=None, pattern=r"^IN-[A-Z]{2}-HFR-\d{6}$")


class DiagnosticLabFacilityResponse(DiagnosticLabFacilityBase):
    """Structured response schema returned for diagnostic laboratory queries."""

    id: str = Field(description="Primary UUID4 key of diagnostic facility")
    user_id: str = Field(description="Associated platform user UUID")
    created_at: datetime = Field(description="Facility creation UTC timestamp")
    updated_at: datetime = Field(description="Facility last modification UTC timestamp")
    user: Optional[UserResponse] = Field(default=None, description="Linked user identity summary")

    model_config = ConfigDict(from_attributes=True)
