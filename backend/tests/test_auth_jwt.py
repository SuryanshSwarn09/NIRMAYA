"""Unit test suite for core JWT creation, decoding, expiration, and security utilities."""

from datetime import timedelta
import pytest
from app.core.exceptions import AuthenticationException
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_create_and_decode_valid_token():
    """Verify standard access token roundtrip preservation of claims."""
    payload = {
        "sub": "usr-test-uuid-001",
        "email": "dr.patel@nirmaya.health",
        "role": "doctor",
    }
    token = create_access_token(payload, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded["sub"] == "usr-test-uuid-001"
    assert decoded["email"] == "dr.patel@nirmaya.health"
    assert decoded["role"] == "doctor"
    assert "exp" in decoded
    assert "iat" in decoded


def test_bearer_prefix_stripping():
    """Verify decode_access_token tolerates raw 'Bearer <token>' input strings."""
    payload = {"sub": "usr-prefix-test"}
    token = create_access_token(payload)

    decoded = decode_access_token(f"Bearer {token}")
    assert decoded["sub"] == "usr-prefix-test"


def test_expired_token_raises_exception():
    """Verify tokens whose expiration is in the past raise TOKEN_EXPIRED."""
    payload = {"sub": "usr-expired-test"}
    expired_token = create_access_token(payload, expires_delta=timedelta(seconds=-10))

    with pytest.raises(AuthenticationException) as exc_info:
        decode_access_token(expired_token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "TOKEN_EXPIRED"
    assert "expired" in exc_info.value.message.lower()


def test_tampered_signature_raises_exception():
    """Verify tokens signed with an unauthorized secret key fail signature verification."""
    payload = {"sub": "usr-tamper-test"}
    tampered_token = create_access_token(payload, secret_key="unauthorized-foreign-key-32-chars-long!")

    with pytest.raises(AuthenticationException) as exc_info:
        decode_access_token(tampered_token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "INVALID_SIGNATURE"


def test_malformed_token_raises_exception():
    """Verify completely invalid strings raise INVALID_TOKEN."""
    with pytest.raises(AuthenticationException) as exc_info:
        decode_access_token("this.is.not.a.valid.jwt")

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "INVALID_TOKEN"


def test_password_hashing_and_verification():
    """Verify deterministic password hashing and verification helper."""
    password = "SuperSecretClinicalPassword2026!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert len(hashed) == 64  # SHA-256 hex string

    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
