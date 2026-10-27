"""Pydantic v2 schemas for ABDM Milestone 1 ABHA Number Issuance, PHR Handle & HPR Onboarding."""

import re
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class AbhaNumberCreateRequest(BaseModel):
    """Payload to request issuance of a 14-digit ABHA Number for a verified patient."""

    patient_id: str = Field(description="UUID string of the target patient profile")
    verification_token: Optional[str] = Field(
        default=None,
        description="Optional cryptographic verification token from DigiLocker or Aadhaar OTP flow",
    )


class AbhaNumberCreateResponse(BaseModel):
    """Response returning the newly minted 14-digit ABHA Number."""

    patient_id: str = Field(description="Patient profile UUID")
    abha_number: str = Field(
        description="Official 14-digit ABHA number formatted as 91-XXXX-XXXX-XXXX",
        example="91-8472-1092-4821",
    )
    status: str = Field(default="active", description="Account status: active | suspended | revoked")
    message: str = Field(
        default="Official 14-digit ABHA number successfully generated and linked to patient profile",
        description="Status description",
    )

    model_config = ConfigDict(from_attributes=True)


class PhrAvailabilityResponse(BaseModel):
    """Response returning whether an @abdm handle is available along with alternatives."""

    handle: str = Field(description="The evaluated handle without suffix", example="arun.patel")
    full_address: str = Field(description="Complete ABHA address with @abdm suffix", example="arun.patel@abdm")
    is_available: bool = Field(description="Whether the requested handle is unreserved and available")
    suggestions: List[str] = Field(
        default_factory=list,
        description="List of alternative handle suggestions if requested handle is unavailable",
    )

    model_config = ConfigDict(from_attributes=True)


class PhrLinkRequest(BaseModel):
    """Payload to claim and link an @abdm PHR handle to a patient profile."""

    patient_id: str = Field(description="Patient profile UUID")
    abha_address: str = Field(
        description="Requested PHR handle or complete address with @abdm suffix",
        example="arun.patel@abdm",
    )

    @field_validator("abha_address")
    @classmethod
    def validate_handle_format(cls, v: str) -> str:
        clean = v.strip().lower()
        handle_part = clean.split("@")[0] if "@" in clean else clean
        if not re.match(r"^[a-z0-9._]{3,32}$", handle_part):
            raise ValueError(
                "ABHA PHR handle must be between 3 and 32 characters containing lowercase letters, numbers, dots, or underscores"
            )
        return clean if clean.endswith("@abdm") else f"{clean}@abdm"


class PhrLinkResponse(BaseModel):
    """Response confirming successful reservation and binding of an @abdm PHR handle."""

    patient_id: str = Field(description="Patient profile UUID")
    abha_number: Optional[str] = Field(default=None, description="Linked 14-digit ABHA number")
    abha_address: str = Field(description="Linked official @abdm address handle", example="arun.patel@abdm")
    status: str = Field(default="active", description="PHR address status")
    message: str = Field(
        default="ABHA PHR address successfully reserved and linked to patient profile",
        description="Status message",
    )

    model_config = ConfigDict(from_attributes=True)


class HprOnboardRequest(BaseModel):
    """Payload to onboard an accredited clinician to the ABDM Healthcare Professional Registry."""

    doctor_id: str = Field(description="Doctor profile UUID")
    registration_number: str = Field(description="State Medical Council or NMC registration number")
    medical_council: str = Field(description="Name of registering state medical council or NMC")
    hpr_handle: str = Field(
        description="Requested HPR address handle (with or without @hpr.abdm suffix)",
        example="ananya.sharma@hpr.abdm",
    )

    @field_validator("hpr_handle")
    @classmethod
    def validate_hpr_handle(cls, v: str) -> str:
        clean = v.strip().lower()
        handle_part = clean.split("@")[0] if "@" in clean else clean
        if not re.match(r"^[a-z0-9._]{3,32}$", handle_part):
            raise ValueError(
                "HPR handle must be between 3 and 32 characters containing lowercase letters, numbers, dots, or underscores"
            )
        return clean if clean.endswith("@hpr.abdm") else f"{clean}@hpr.abdm"


class HprOnboardResponse(BaseModel):
    """Response confirming doctor onboarding to ABDM Healthcare Professional Registry."""

    doctor_id: str = Field(description="Doctor profile UUID")
    hpr_id: str = Field(description="Accredited HPR ID", example="ananya.sharma@hpr.abdm")
    registration_number: str = Field(description="Medical council registration number")
    medical_council: str = Field(description="Medical council name")
    status: str = Field(default="verified", description="Credential verification status")
    verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of HPR credential verification",
    )
    message: str = Field(
        default="Clinician successfully onboarded to National Healthcare Professional Registry (HPR)",
        description="Status description",
    )

    model_config = ConfigDict(from_attributes=True)
