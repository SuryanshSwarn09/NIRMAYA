"""Pydantic v2 schemas for ABDM (Ayushman Bharat Digital Mission) Gateway interoperability."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class GatewaySessionRequest(BaseModel):
    """Payload sent to ABDM Gateway /v0.5/sessions to request an access token."""

    clientId: str = Field(description="ABDM Registered Client ID", example="SBX_001234")
    clientSecret: str = Field(description="ABDM Client Secret Key", example="secret_key_placeholder")

    model_config = ConfigDict(from_attributes=True)


class GatewaySessionResponse(BaseModel):
    """Response payload returned by ABDM Gateway /v0.5/sessions."""

    accessToken: str = Field(description="Bearer JWT access token for gateway API calls")
    expiresIn: int = Field(default=3600, description="Token validity window in seconds", example=3600)
    tokenType: str = Field(default="bearer", description="Token authentication scheme", example="bearer")

    model_config = ConfigDict(from_attributes=True)


class GatewayErrorDetail(BaseModel):
    """Detailed error object returned by ABDM Gateway APIs."""

    code: int = Field(description="ABDM error code", example=1000)
    message: str = Field(description="Human readable error description", example="Invalid client credentials")


class GatewayErrorResponse(BaseModel):
    """Standard RFC / ABDM error envelope."""

    error: GatewayErrorDetail


class GatewayHeaderSchema(BaseModel):
    """Standardized metadata headers required by ABDM Gateway endpoints."""

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the outbound gateway dispatch",
    )
    request_id: str = Field(description="Unique UUID string for distributed tracing")
    x_cm_id: str = Field(default="sbx", description="Target Consent Manager ID (e.g. sbx)")


class GatewayStatusResponse(BaseModel):
    """Synthesized status reporting ABDM Gateway connectivity and encryption health."""

    status: str = Field(description="Connection state: connected | degraded | disconnected", example="connected")
    gateway_url: str = Field(description="Configured ABDM Gateway endpoint", example="https://dev.abdm.gov.in/gateway")
    cm_id: str = Field(description="Target Consent Manager ID", example="sbx")
    sandbox_mode: bool = Field(description="Whether ABDM Sandbox mode is active", example=True)
    is_authenticated: bool = Field(description="Whether a valid session token is currently cached", example=True)
    token_expiry_seconds: Optional[int] = Field(default=None, description="Remaining validity of cached session token")
    rsa_key_configured: bool = Field(description="Whether RSA demographic encryption key is loaded", example=True)
    last_verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of status check",
    )


class ABDMEncryptionPayload(BaseModel):
    """Payload schema for testing or executing demographic RSA encryption."""

    demographic_data: Dict[str, Any] = Field(
        description="Key-value demographic dictionary (e.g. name, gender, yearOfBirth)",
        example={"name": "Arun Patel", "gender": "M", "yearOfBirth": 1988},
    )


class ABDMEncryptedResponse(BaseModel):
    """Encrypted ciphertext response conforming to ABDM RSA-OAEP specifications."""

    encrypted_data: str = Field(description="Base64-encoded RSA-OAEP encrypted ciphertext")
    key_algorithm: str = Field(default="RSA-OAEP-256", description="Cryptographic algorithm applied")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of encryption operation",
    )
