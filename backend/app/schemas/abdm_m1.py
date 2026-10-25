"""Pydantic v2 schemas for ABDM Milestone 1 Direct Aadhaar Demographic OTP Verification."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


class AadhaarAddress(BaseModel):
    """Structured residential address claims returned from UIDAI Aadhaar e-KYC."""

    care_of: Optional[str] = Field(default=None, description="Care-of or guardian designation (C/O, S/O, D/O)")
    house: Optional[str] = Field(default=None, description="House or flat number")
    street: Optional[str] = Field(default=None, description="Street or avenue")
    landmark: Optional[str] = Field(default=None, description="Landmark indicator")
    locality: Optional[str] = Field(default=None, description="Locality, sector, or mohalla")
    district: Optional[str] = Field(default=None, description="District or municipal area")
    state: Optional[str] = Field(default=None, description="State or Union Territory")
    pincode: Optional[str] = Field(default=None, description="6-digit postal code")
    formatted_address: str = Field(description="Synthesized multi-line human readable address")

    model_config = ConfigDict(from_attributes=True)


class AadhaarDemographicData(BaseModel):
    """Certified demographic claims extracted from UIDAI Aadhaar e-KYC."""

    name: str = Field(description="Certified legal full name", example="Arun Kumar Patel")
    gender: str = Field(description="Administrative gender: male | female | other", example="male")
    date_of_birth: str = Field(description="Date of birth in YYYY-MM-DD format", example="1990-06-04")
    masked_aadhaar: str = Field(description="Masked Aadhaar representation (last 4 digits only)", example="XXXX-XXXX-4821")
    photo_base64: Optional[str] = Field(default=None, description="Base64 encoded JPEG photograph from UIDAI")
    address: AadhaarAddress = Field(description="Structured residential address")
    verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of cryptographic verification",
    )

    model_config = ConfigDict(from_attributes=True)


class AadhaarOtpGenerateRequest(BaseModel):
    """Request payload to initiate Aadhaar demographic OTP verification."""

    aadhaar_number: str = Field(
        description="12-digit UIDAI Aadhaar number (hyphens and spaces allowed)",
        example="9184 7210 4821",
    )

    @field_validator("aadhaar_number")
    @classmethod
    def validate_aadhaar_format(cls, v: str) -> str:
        clean = re.sub(r"[\s\-]", "", v.strip())
        if not re.match(r"^\d{12}$", clean):
            raise ValueError("Aadhaar number must contain exactly 12 numeric digits")
        return clean


class AadhaarOtpGenerateResponse(BaseModel):
    """Response payload confirming Aadhaar OTP dispatch."""

    txn_id: str = Field(description="Unique transaction ID for the OTP verification session")
    masked_mobile: str = Field(description="Masked phone number where OTP was dispatched", example="XXXX-XXX-482")
    expires_in: int = Field(default=600, description="Session validity window in seconds (10 minutes)")
    message: str = Field(
        default="OTP has been dispatched to the mobile number registered with UIDAI Aadhaar",
        description="User notification text",
    )

    model_config = ConfigDict(from_attributes=True)


class AadhaarOtpVerifyRequest(BaseModel):
    """Request payload to submit the received 6-digit Aadhaar OTP."""

    txn_id: str = Field(min_length=1, description="Transaction ID received from generate-otp")
    otp: str = Field(
        min_length=6,
        max_length=6,
        description="6-digit numeric OTP received on registered mobile",
        example="123456",
    )

    @field_validator("otp")
    @classmethod
    def validate_otp_numeric(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^\d{6}$", clean):
            raise ValueError("OTP must contain exactly 6 numeric digits")
        return clean


class AadhaarOtpVerifyResponse(BaseModel):
    """Response payload containing verified Aadhaar e-KYC demographic claims."""

    verified: bool = Field(default=True, description="Verification status")
    txn_id: str = Field(description="Transaction ID of verified session")
    jwt_token: str = Field(description="Temporary session token confirming Aadhaar verification")
    demographics: AadhaarDemographicData = Field(description="Verified e-KYC demographic claims")

    model_config = ConfigDict(from_attributes=True)


class UnifiedIdentitySyncResponse(BaseModel):
    """Response payload when synchronizing verified Aadhaar/DigiLocker demographics to PatientProfile."""

    patient_id: str = Field(description="UUID string of the updated patient profile")
    name: str = Field(description="Synchronized certified legal name")
    masked_aadhaar: str = Field(description="Linked masked Aadhaar identifier")
    is_identity_verified: bool = Field(default=True, description="Verification flag")
    source: str = Field(default="aadhaar_otp", description="Identity verification provider source")
    message: str = Field(default="Patient profile successfully synchronized with verified Aadhaar identity")

    model_config = ConfigDict(from_attributes=True)
