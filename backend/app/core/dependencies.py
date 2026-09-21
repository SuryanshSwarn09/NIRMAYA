"""FastAPI security dependencies for bearer token validation and user resolution."""

from typing import Optional, Sequence
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import AuthenticationException, PermissionDeniedException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import TokenPayload

oauth2_scheme = HTTPBearer(auto_error=False)


async def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
) -> TokenPayload:
    """Extract and validate bearer token claims from the HTTP Authorization header."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise AuthenticationException(
            message="Authorization bearer token is missing or malformed",
            error_code="AUTHENTICATION_REQUIRED",
        )

    claims = decode_access_token(credentials.credentials)

    sub = claims.get("sub")
    if not sub:
        raise AuthenticationException(
            message="Authentication token missing required subject claim",
            error_code="INVALID_TOKEN",
        )

    return TokenPayload(
        sub=str(sub),
        email=claims.get("email"),
        role=claims.get("role"),
        aud=claims.get("aud"),
        exp=claims.get("exp"),
        iat=claims.get("iat"),
        app_metadata=claims.get("app_metadata"),
        user_metadata=claims.get("user_metadata"),
    )


async def get_current_user(
    payload: TokenPayload = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve active database User entity from validated JWT subject and email claims."""
    conditions = [User.supabase_uid == payload.sub, User.id == payload.sub]
    if payload.email:
        conditions.append(User.email == str(payload.email))

    stmt = (
        select(User)
        .options(
            selectinload(User.patient_profile),
            selectinload(User.doctor_profile),
            selectinload(User.lab_facility),
        )
        .where(or_(*conditions))
    )
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user:
        raise AuthenticationException(
            message="Authenticated user record does not exist in local platform registry",
            error_code="USER_NOT_FOUND",
        )

    if not user.is_active:
        raise PermissionDeniedException(
            message="User account has been deactivated or suspended",
        )

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Verify that the resolved user account is active."""
    if not user.is_active:
        raise PermissionDeniedException(
            message="User account is inactive",
        )
    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Optionally resolve authenticated user, returning None for unauthenticated requests."""
    if not credentials or credentials.scheme.lower() != "bearer":
        return None

    try:
        claims = decode_access_token(credentials.credentials)
        sub = claims.get("sub")
        if not sub:
            return None

        email = claims.get("email")
        conditions = [User.supabase_uid == sub, User.id == sub]
        if email:
            conditions.append(User.email == str(email))

        stmt = (
            select(User)
            .options(
                selectinload(User.patient_profile),
                selectinload(User.doctor_profile),
                selectinload(User.lab_facility),
            )
            .where(or_(*conditions))
        )
        user = (await db.execute(stmt)).scalar_one_or_none()
        if user and user.is_active:
            return user
        return None
    except Exception:
        return None


class RoleChecker:
    """Security dependency enforcing role-based access control with admin superuser override."""

    def __init__(self, allowed_roles: Sequence[UserRole]) -> None:
        self.allowed_roles = list(allowed_roles)

    async def __call__(
        self,
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """Validate that the authenticated actor possesses an authorized role."""
        if current_user.role == UserRole.ADMIN or current_user.role in self.allowed_roles:
            return current_user

        allowed_names = ", ".join([r.value for r in self.allowed_roles])
        raise PermissionDeniedException(
            message=(
                f"Role '{current_user.role.value}' is not authorized to access this health resource. "
                f"Required role(s): {allowed_names}"
            )
        )


def require_role(*allowed_roles: UserRole) -> RoleChecker:
    """Create a RoleChecker dependency for the specified permitted clinical roles."""
    return RoleChecker(allowed_roles)

