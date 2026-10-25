"""Pydantic v2 schemas for DigiLocker OAuth 2.0 & e-Aadhaar verification."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DigiLockerAuthorizeUrlResponse(BaseModel):
    """Payload returning the DigiLocker OAuth2 authorization redirect URL and PKCE state."""

    authorize_url: str = Field(description="Full DigiLocker authorization URL with query parameters")
    state: str = Field(description="Cryptographic CSRF protection state token")
    code_challenge: str = Field(description="RFC 7636 S256 code challenge")
    code_challenge_method: str = Field(default="S256", description="PKCE challenge algorithm")

    model_config = ConfigDict(from_attributes=True)


class DigiLockerCallbackRequest(BaseModel):
    """Payload received from frontend callback containing the authorization code and PKCE verifier."""

    code: str = Field(min_length=1, description="Authorization code returned by DigiLocker")
    state: str = Field(min_length=1, description="CSRF state parameter returned by DigiLocker")
    code_verifier: Optional[str] = Field(
        default=None,
        description="RFC 7636 PKCE code verifier generated during authorization URL creation",
    )


class DigiLockerTokenResponse(BaseModel):
    """Response payload returned by DigiLocker token endpoint /public/oauth2/1/token."""

    access_token: str = Field(description="Bearer access token for DigiLocker API queries")
    expires_in: int = Field(default=3600, description="Token validity window in seconds")
    token_type: str = Field(default="bearer", description="Token scheme")
    scope: str = Field(default="read profile eaadhaar", description="Granted OAuth scopes")
    digilocker_id: Optional[str] = Field(default=None, description="Unique DigiLocker citizen identifier")

    model_config = ConfigDict(from_attributes=True)


class EAadhaarAddress(BaseModel):
    """Structured residential address claims parsed from UIDAI e-Aadhaar XML."""

    care_of: Optional[str] = Field(default=None, description="Care-of or guardian name (C/O, S/O, D/O)")
    house: Optional[str] = Field(default=None, description="House, apartment, or flat number")
    street: Optional[str] = Field(default=None, description="Street or lane name")
    landmark: Optional[str] = Field(default=None, description="Prominent landmark")
    locality: Optional[str] = Field(default=None, description="Locality, sector, or village")
    district: Optional[str] = Field(default=None, description="District or county")
    state: Optional[str] = Field(default=None, description="State or union territory")
    pincode: Optional[str] = Field(default=None, description="6-digit postal code")
    formatted_address: str = Field(description="Synthesized multi-line human readable address")

    model_config = ConfigDict(from_attributes=True)


class EAadhaarDemographics(BaseModel):
    """Full authenticated demographic claims extracted from UIDAI-signed e-Aadhaar document."""

    name: str = Field(description="Legal full name as certified by UIDAI", example="Arun Kumar Patel")
    gender: str = Field(description="Administrative gender: male | female | other", example="male")
    date_of_birth: str = Field(description="Date of birth in YYYY-MM-DD or DD-MM-YYYY format", example="1990-06-04")
    masked_aadhaar: str = Field(description="Last 4 digits masked Aadhaar representation", example="XXXX-XXXX-4821")
    photo_base64: Optional[str] = Field(default=None, description="Base64-encoded JPEG avatar photograph from Aadhaar")
    address: EAadhaarAddress = Field(description="Structured residential address")
    signature_valid: bool = Field(default=True, description="Whether UIDAI X.509 digital signature is cryptographically valid")
    issuer: str = Field(default="UIDAI", description="Issuing authority certificate subject")
    verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of e-Aadhaar verification",
    )

    model_config = ConfigDict(from_attributes=True)


class DigiLockerVerificationResult(BaseModel):
    """Synthesized result of a successful DigiLocker authentication and e-Aadhaar verification."""

    verified: bool = Field(default=True, description="Whether verification succeeded")
    digilocker_id: str = Field(description="DigiLocker unique citizen ID", example="DL-IND-98472109")
    demographics: EAadhaarDemographics = Field(description="Parsed e-Aadhaar demographic claims")
    raw_xml_present: bool = Field(default=True, description="Whether raw UIDAI XML signature is archived")

    model_config = ConfigDict(from_attributes=True)


class DigiLockerSyncPatientResponse(BaseModel):
    """Response returned when linking verified DigiLocker e-Aadhaar demographics to a PatientProfile."""

    patient_id: str = Field(description="UUID string of the updated patient profile")
    digilocker_id: str = Field(description="Linked DigiLocker unique citizen ID")
    masked_aadhaar: str = Field(description="Linked masked Aadhaar representation")
    name: str = Field(description="Synchronized verified legal name")
    is_identity_verified: bool = Field(default=True, description="Verification flag status")
    message: str = Field(default="Patient profile successfully synchronized with verified e-Aadhaar claims")

    model_config = ConfigDict(from_attributes=True)
