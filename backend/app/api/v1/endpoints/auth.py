"""Authentication and session management REST API endpoints."""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.exceptions import AuthenticationException, PermissionDeniedException
from app.core.security import create_access_token, decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    TokenVerifyRequest,
    TokenVerifyResponse,
)
from app.schemas.common import APIResponse
from app.schemas.user import UserResponse

router = APIRouter()


class TestTokenRequest(BaseModel):
    """Payload for generating test JWTs in non-production environments."""

    email: EmailStr = Field(default="arun.patel@example.com", description="User email for token claims")
    sub: str = Field(default="sb-auth-patient-001", description="Subject claim / Supabase UID")
    role: str = Field(default="patient", description="Assigned platform role")
    expires_minutes: Optional[int] = Field(default=60, description="Token validity duration in minutes")


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve authenticated user profile and roles",
    description="Inspects bearer token and returns current user identity, role, and verification status.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserResponse]:
    """Return authenticated caller identity."""
    return APIResponse(
        message="Authenticated user identity retrieved successfully",
        data=UserResponse.model_validate(current_user),
    )


@router.post(
    "/verify",
    response_model=APIResponse[TokenVerifyResponse],
    status_code=status.HTTP_200_OK,
    summary="Verify JWT token signature and claims",
    description="Validates a JWT access token and extracts decoded payload claims.",
)
async def verify_token(
    request: TokenVerifyRequest,
) -> APIResponse[TokenVerifyResponse]:
    """Validate bearer token string without requiring database lookup."""
    try:
        claims = decode_access_token(request.token)
        return APIResponse(
            message="Authentication token is valid and active",
            data=TokenVerifyResponse(
                valid=True,
                claims=claims,
                subject=claims.get("sub"),
            ),
        )
    except AuthenticationException as exc:
        return APIResponse(
            message=exc.message,
            data=TokenVerifyResponse(
                valid=False,
                claims=None,
                subject=None,
            ),
        )


@router.post(
    "/test-token",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate signed test JWT (Dev/Test only)",
    description="Mints a valid signed HMAC-SHA256 JWT access token for integration testing.",
)
async def generate_test_token(
    req: TestTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Generate test JWT token for automated tests and sandbox verification."""
    if settings.is_production:
        raise PermissionDeniedException(
            message="Test token issuance is disabled in production environment",
        )

    expires_delta = timedelta(minutes=req.expires_minutes or 60)
    token_data = {
        "sub": req.sub,
        "email": req.email,
        "role": req.role,
        "app_metadata": {"role": req.role, "provider": "supabase-simulation"},
    }
    access_token = create_access_token(token_data, expires_delta=expires_delta)

    # Attempt to resolve matching user if exists in DB
    user_stmt = select(User).where(User.email == req.email)
    user = (await db.execute(user_stmt)).scalar_one_or_none()

    return APIResponse(
        message="Test authentication token issued successfully",
        data=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(expires_delta.total_seconds()),
            user=UserResponse.model_validate(user) if user else None,
        ),
    )
