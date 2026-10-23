"""Pydantic schemas for ABDM Digital ABHA ID Card and QR verification."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AbhaCardData(BaseModel):
    """Demographic and credential claims rendered on the digital ABHA card."""

    model_config = ConfigDict(from_attributes=True)

    patient_id: str = Field(description="Internal patient UUID")
    abha_number: str = Field(description="14-digit hyphenated ABHA number, e.g. 91-8472-1092-4821")
    abha_address: str = Field(description="Health ID handle, e.g. arun.patel@abdm")
    name: str = Field(description="Full legal name of the cardholder")
    gender: str = Field(description="Gender abbreviation: M, F, or O")
    date_of_birth: Optional[str] = Field(default=None, description="ISO format date of birth YYYY-MM-DD")
    year_of_birth: Optional[int] = Field(default=None, description="Year of birth")
    blood_group: str = Field(default="UNKNOWN", description="Blood group code e.g. O+, B+")
    mobile: Optional[str] = Field(default=None, description="Masked mobile phone number")
    address: Optional[str] = Field(default=None, description="Residential street address")
    district: Optional[str] = Field(default=None, description="District / Municipal jurisdiction")
    state: Optional[str] = Field(default=None, description="State or Union Territory name")
    pincode: Optional[str] = Field(default=None, description="Postal pincode")
    emergency_contact_name: Optional[str] = Field(default=None, description="Emergency contact person")
    emergency_contact_phone: Optional[str] = Field(default=None, description="Emergency phone number")
    emergency_contact_relation: Optional[str] = Field(default=None, description="Relationship to cardholder")
    kyc_status: str = Field(default="VERIFIED", description="KYC verification status")
    auth_methods: List[str] = Field(
        default_factory=lambda: ["AADHAAR_OTP", "MOBILE_OTP"],
        description="Authentications used to verify identity",
    )


class AbhaQrPayload(BaseModel):
    """Compact ABDM NHA-conforming QR code payload dictionary."""

    hidn: str = Field(description="14-digit ABHA number")
    hid: str = Field(description="ABHA address handle")
    name: str = Field(description="Cardholder legal name")
    gender: str = Field(description="M/F/O")
    dob: Optional[str] = Field(default=None, description="Date or year of birth")
    state_name: Optional[str] = Field(default=None, description="State name")
    dist_name: Optional[str] = Field(default=None, description="District name")
    mobile: Optional[str] = Field(default=None, description="Masked phone")
    blood_group: Optional[str] = Field(default=None, description="Blood group")
    issue_date: str = Field(description="ISO timestamp when card was generated")
    signature: str = Field(description="HMAC-SHA256 signature over canonical claims")


class AbhaCardResponse(BaseModel):
    """Response payload containing digital ABHA card attributes and encoded QR string."""

    card_data: AbhaCardData
    qr_payload: str = Field(description="Serialized JSON string ready for vector QR rendering")
    signature: str = Field(description="Cryptographic attestation signature")
    issued_at: str = Field(description="ISO timestamp of issuance")


class AbhaQrVerificationRequest(BaseModel):
    """Request payload containing scanned or decoded ABHA QR string for verification."""

    qr_string: str = Field(description="Raw string scanned from the digital ABHA QR code")


class AbhaQrVerificationResponse(BaseModel):
    """Verification result with decoded claims and cryptographic integrity confirmation."""

    is_valid: bool = Field(description="Whether the QR signature and schema are cryptographically authentic")
    message: str = Field(description="Status or error message")
    claims: Optional[Dict[str, Any]] = Field(default=None, description="Parsed demographic claims from QR")
    verified_at: str = Field(description="ISO timestamp of verification check")
