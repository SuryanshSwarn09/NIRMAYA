"""Core cryptographic and JWT security utilities for NIRMAYA platform."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import hashlib
import jwt
from app.core.config import settings
from app.core.exceptions import AuthenticationException


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None,
) -> str:
    """Generate a signed HMAC-SHA256 JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.setdefault("iat", int(now.timestamp()))
    to_encode.setdefault("exp", int(expire.timestamp()))
    if settings.JWT_AUDIENCE:
        to_encode.setdefault("aud", settings.JWT_AUDIENCE)

    signing_key = secret_key or settings.SECRET_KEY
    return jwt.encode(to_encode, signing_key, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(
    token: str,
    verify_aud: bool = True,
) -> Dict[str, Any]:
    """Decode and validate a JWT access token against Supabase or core secret."""
    clean_token = token.strip()
    if clean_token.lower().startswith("bearer "):
        clean_token = clean_token[7:].strip()

    # Determine candidate signature verification keys
    candidate_keys = []
    if settings.SUPABASE_JWT_SECRET and not settings.SUPABASE_JWT_SECRET.startswith("supabase-jwt-secret-placeholder"):
        candidate_keys.append(settings.SUPABASE_JWT_SECRET)
    if settings.SECRET_KEY not in candidate_keys:
        candidate_keys.append(settings.SECRET_KEY)
    if settings.SUPABASE_JWT_SECRET and settings.SUPABASE_JWT_SECRET not in candidate_keys:
        candidate_keys.append(settings.SUPABASE_JWT_SECRET)

    audience = settings.JWT_AUDIENCE if verify_aud else None
    decode_kwargs = {
        "algorithms": [settings.JWT_ALGORITHM],
        "options": {"verify_aud": verify_aud},
    }
    if audience:
        decode_kwargs["audience"] = audience

    last_sig_error = None
    for key in candidate_keys:
        try:
            return jwt.decode(clean_token, key, **decode_kwargs)
        except jwt.InvalidSignatureError as sig_err:
            last_sig_error = sig_err
            continue
        except jwt.ExpiredSignatureError:
            raise AuthenticationException(
                message="Authentication token has expired",
                error_code="TOKEN_EXPIRED",
            )
        except jwt.InvalidAudienceError:
            raise AuthenticationException(
                message="Token audience claim does not match platform identifier",
                error_code="INVALID_AUDIENCE",
            )
        except (jwt.DecodeError, jwt.InvalidTokenError) as exc:
            raise AuthenticationException(
                message=f"Malformed or invalid authentication token: {str(exc)}",
                error_code="INVALID_TOKEN",
            )

    if last_sig_error:
        raise AuthenticationException(
            message="Token signature verification failed",
            error_code="INVALID_SIGNATURE",
        )

    raise AuthenticationException(
        message="Malformed or invalid authentication token",
        error_code="INVALID_TOKEN",
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hashed representation."""
    return get_password_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    """Generate a deterministic SHA-256 hash for simulated developer authentication."""
    salted = f"{settings.SECRET_KEY}:{password}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()
