"""Pydantic v2 schemas for authentication, token validation, and session claims."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.enums import UserRole
from app.schemas.user import UserResponse


class TokenPayload(BaseModel):
    """Decoded and validated JSON Web Token claims structure."""

    sub: str = Field(description="Subject identifier (Supabase UID or platform user ID)")
    email: Optional[EmailStr] = Field(default=None, description="User account email address")
    role: Optional[str] = Field(default=None, description="Authorization role claim")
    aud: Optional[str] = Field(default=None, description="Intended audience identifier")
    exp: Optional[int] = Field(default=None, description="Expiration timestamp (UNIX epoch)")
    iat: Optional[int] = Field(default=None, description="Issued at timestamp (UNIX epoch)")
    app_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Supabase application level claims and permissions",
    )
    user_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Supabase user profile attributes",
    )


class TokenResponse(BaseModel):
    """Bearer access token issuance payload."""

    access_token: str = Field(description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="HTTP authorization scheme")
    expires_in: int = Field(description="Lifetime of token in seconds")
    user: Optional[UserResponse] = Field(default=None, description="Linked user identity summary")


class TokenVerifyRequest(BaseModel):
    """Payload for verifying an existing JWT token."""

    token: str = Field(description="Bearer token string to inspect")


class TokenVerifyResponse(BaseModel):
    """Result of token signature and expiration verification."""

    valid: bool = Field(description="Flag indicating if token is currently valid and active")
    claims: Optional[Dict[str, Any]] = Field(default=None, description="Decoded JWT claims dictionary")
    subject: Optional[str] = Field(default=None, description="Subject identifier extracted from token")


class AuthContext(BaseModel):
    """Lightweight security context representing the authenticated actor."""

    user_id: str = Field(description="Internal user primary UUID")
    email: str = Field(description="User primary email address")
    role: UserRole = Field(description="Active platform role")
    is_active: bool = Field(default=True, description="Account active status")
    is_verified: bool = Field(default=False, description="Account verification status")
