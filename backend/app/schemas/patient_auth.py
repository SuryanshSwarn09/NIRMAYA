"""Pydantic v2 schemas for Unified DigiLocker & Aadhaar OTP Passwordless Patient Gateway."""

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class PatientUnifiedAuthRequest(BaseModel):
    """Payload to authenticate or register patient via verified DigiLocker or Aadhaar OTP claims."""

    source: Literal["digilocker", "aadhaar_otp", "mobile_fallback"] = Field(
        description="Verification identity source",
        example="aadhaar_otp",
    )
    name: str = Field(description="Certified legal full name", example="Arun Kumar Patel")
    gender: Optional[str] = Field(default="other", description="Gender: male | female | other")
    date_of_birth: Optional[str] = Field(default=None, description="Date of birth YYYY-MM-DD")
    masked_aadhaar: Optional[str] = Field(
        default=None,
        description="Masked Aadhaar representation (e.g. XXXX-XXXX-4821)",
    )
    mobile_number: Optional[str] = Field(default=None, description="Active mobile number if provided")
    email: Optional[str] = Field(default=None, description="Contact email if provided")

    formatted_address: Optional[str] = Field(default=None, description="Formatted residential address")
    district: Optional[str] = Field(default=None, description="District or City")
    state: Optional[str] = Field(default=None, description="State or Union Territory")
    pincode: Optional[str] = Field(default=None, description="6-digit postal PIN code")

    txn_id: Optional[str] = Field(default=None, description="Session txn_id or verification reference")
    remember_me: bool = Field(default=True, description="Whether to issue an extended 30-day session token")

    model_config = ConfigDict(from_attributes=True)


class PatientMobileFallbackLoginRequest(BaseModel):
    """Payload for patients whose current SIM differs from old Aadhaar-registered SIM."""

    mobile_number: str = Field(description="10-digit Indian mobile number", example="9876543210")
    otp: str = Field(description="6-digit verification OTP", example="123456")
    abha_identifier: Optional[str] = Field(default=None, description="Optional ABHA Number or @abdm handle")
    remember_me: bool = Field(default=True, description="Whether to issue an extended 30-day session token")

    model_config = ConfigDict(from_attributes=True)


class PatientUnifiedAuthResponse(BaseModel):
    """Response returned upon successful passwordless authentication or registration."""

    access_token: str = Field(description="JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token scheme")
    expires_in_seconds: int = Field(description="Token expiry window in seconds (e.g. 2592000 for 30 days)")
    is_new_user: bool = Field(description="Whether a new patient profile was created")

    patient_id: str = Field(description="Unique UUID of PatientProfile")
    user_id: str = Field(description="Unique UUID of User")
    name: str = Field(description="Patient legal name")
    masked_aadhaar: Optional[str] = Field(default=None, description="Masked Aadhaar representation")
    abha_number: Optional[str] = Field(default=None, description="14-digit ABHA Number (91-XXXX-XXXX-XXXX)")
    abha_address: Optional[str] = Field(default=None, description="Reserved @abdm PHR handle")
    message: str = Field(description="Human readable confirmation")

    model_config = ConfigDict(from_attributes=True)
