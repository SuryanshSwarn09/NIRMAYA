"""Pydantic v2 schemas for the Universal High-Density National Health Gateway.

Supports multi-modal authentication channels:
1. Aadhaar OTP (Demographic challenge/verify)
2. DigiLocker e-KYC (OAuth2 PKCE claims)
3. ABHA Mobile Fallback (Active SIM verification)
4. Offline Emergency Access (Break-the-glass token minting)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class GatewayUserRole(str, Enum):
    """National health gateway role classes."""
    CITIZEN = "citizen"
    DOCTOR = "doctor"
    LAB = "lab"
    PHARMACY = "pharmacy"


class GatewayAuthChannel(str, Enum):
    """Supported authentication channels for citizen gateway."""
    AADHAAR_OTP = "aadhaar_otp"
    DIGILOCKER = "digilocker"
    ABHA_MOBILE = "abha_mobile"
    OFFLINE_EMERGENCY = "offline_emergency"


class AadhaarOtpChallengeRequest(BaseModel):
    """Payload to initiate an Aadhaar OTP demographic challenge."""
    aadhaar_number: str = Field(
        ...,
        description="12-digit Aadhaar number with or without spaces",
        example="9184 7210 4821",
    )

    model_config = ConfigDict(from_attributes=True)


class AadhaarOtpChallengeResponse(BaseModel):
    """Response returned upon dispatch of Aadhaar OTP challenge."""
    txn_id: str = Field(description="Unique transaction reference for verification")
    masked_mobile: str = Field(description="Masked registered mobile number", example="+91 ******4821")
    expires_in_seconds: int = Field(default=300, description="OTP validity window in seconds")
    message: str = Field(default="OTP sent successfully to Aadhaar-registered mobile.")

    model_config = ConfigDict(from_attributes=True)


class AadhaarOtpVerifyRequest(BaseModel):
    """Payload to verify an Aadhaar OTP demographic challenge."""
    txn_id: str = Field(..., description="Transaction reference from challenge phase")
    otp: str = Field(..., description="6-digit verification code", example="123456")
    remember_me: bool = Field(default=True, description="Whether to issue an extended 30-day session")

    model_config = ConfigDict(from_attributes=True)


class DigiLockerKycAuthRequest(BaseModel):
    """Payload to exchange DigiLocker OAuth2 PKCE authorization code for gateway session."""
    code: str = Field(..., description="Authorization code returned by DigiLocker gateway")
    state: str = Field(..., description="CSRF state parameter")
    code_verifier: str = Field(..., description="PKCE code verifier")
    remember_me: bool = Field(default=True, description="Whether to issue an extended 30-day session")

    model_config = ConfigDict(from_attributes=True)


class AbhaMobileLoginRequest(BaseModel):
    """Payload for active mobile SIM login with optional ABHA identifier lookup."""
    mobile_number: str = Field(..., description="10-digit Indian mobile number", example="9876543210")
    otp: str = Field(..., description="6-digit verification OTP", example="123456")
    abha_identifier: Optional[str] = Field(default=None, description="Optional ABHA address or 14-digit number")
    remember_me: bool = Field(default=True, description="Whether to issue an extended 30-day session")

    model_config = ConfigDict(from_attributes=True)


class EmergencyBypassAuthRequest(BaseModel):
    """Payload to mint a break-the-glass emergency offline session."""
    facility_id: str = Field(..., description="Healthcare facility registry ID (HFR)", example="IN-DL-AIIMS-001")
    clinician_id: str = Field(..., description="Practitioner HPR ID or license number", example="HPR-9921-DR")
    patient_identifier: str = Field(..., description="Patient ABHA, Aadhaar, or temporary trauma token")
    emergency_reason: str = Field(..., description="Clinical justification for emergency bypass")
    triage_level: Literal["red", "yellow"] = Field(
        default="red",
        description="Emergency triage level (red: immediate resuscitation, yellow: urgent)",
    )
    tamper_attestation: str = Field(
        ...,
        description="Signed attestation acknowledging legal audit under National Health Guidelines",
    )

    model_config = ConfigDict(from_attributes=True)


class GatewaySessionResponse(BaseModel):
    """Standardized response returned upon successful authentication via any gateway channel."""
    session_id: str = Field(description="Unique distributed session identifier")
    access_token: str = Field(description="Cryptographic JWT Bearer token")
    token_type: str = Field(default="bearer", description="Token scheme")
    user_role: GatewayUserRole = Field(description="Authenticated national health role")
    auth_channel: GatewayAuthChannel = Field(description="Channel utilized for authentication")
    user_id: str = Field(description="User UUID in NIRMAYA identity registry")
    patient_id: Optional[str] = Field(default=None, description="PatientProfile UUID if role is citizen")
    name: str = Field(description="Certified legal or practitioner full name")
    identifier: str = Field(description="Masked identifier (e.g. XXXX-XXXX-4821 or Dr. Ananya Sharma)")
    abha_number: Optional[str] = Field(default=None, description="14-digit ABHA number if linked")
    abha_address: Optional[str] = Field(default=None, description="Reserved @abdm PHR handle")
    expires_at: datetime = Field(description="ISO timestamp of session expiration")
    is_offline_emergency: bool = Field(default=False, description="Flag indicating break-the-glass emergency session")
    emergency_seal: Optional[str] = Field(default=None, description="Cryptographic SHA-256 seal for emergency sessions")
    message: str = Field(description="Status confirmation message")

    model_config = ConfigDict(from_attributes=True)


class GatewayDeviceSession(BaseModel):
    """Active device session metadata for distributed session tracking and revocation."""
    session_id: str = Field(description="Session UUID")
    user_id: str = Field(description="User UUID")
    user_role: GatewayUserRole = Field(description="Role associated with session")
    auth_channel: GatewayAuthChannel = Field(description="Channel used to establish session")
    device_fingerprint: str = Field(description="Client device fingerprint or hash")
    client_ip: str = Field(description="Client IP address")
    user_agent: str = Field(description="Client browser or application user agent")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(description="Session expiration timestamp")
    is_active: bool = Field(default=True, description="Active status")

    model_config = ConfigDict(from_attributes=True)


class RateShieldMetrics(BaseModel):
    """Telemetry metrics from high-density token-bucket rate limiter shield."""
    capacity_per_second: int = Field(default=50000, description="Engine burst capacity (50,000 req/sec)")
    auth_tier_limit_per_minute: int = Field(default=5, description="Strict anti-brute-force threshold")
    current_active_sessions: int = Field(description="Number of active distributed sessions")
    shield_status: str = Field(default="OPTIMAL", description="Status indicator: OPTIMAL | DEGRADED | SHIELD_ACTIVE")
    telemetry_latency_ms: float = Field(default=1.2, description="Gateway processing overhead in milliseconds")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class SessionRevokeRequest(BaseModel):
    """Payload to revoke an active distributed session."""
    session_id: str = Field(..., description="Session identifier to invalidate")

    model_config = ConfigDict(from_attributes=True)

