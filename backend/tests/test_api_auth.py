"""Integration test suite for authentication endpoints, token validation, and current user security dependencies."""

from datetime import timedelta
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import User


@pytest_asyncio.fixture
async def auth_api_client():
    """Provide an isolated in-memory test database and client for auth API tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac, session_factory

    app.dependency_overrides.pop(get_db, None)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_me_success(auth_api_client) -> None:
    """Verify GET /api/v1/auth/me returns the current user profile when valid token provided."""
    client, session_factory = auth_api_client

    # Seed test user
    async with session_factory() as session:
        user = User(
            email="dr.sharma@nirmaya.health",
            full_name="Dr. Alok Sharma",
            role=UserRole.DOCTOR,
            supabase_uid="sb-auth-doctor-001",
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    # Issue access token
    token = create_access_token({
        "sub": "sb-auth-doctor-001",
        "email": "dr.sharma@nirmaya.health",
        "role": "doctor",
    })

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "dr.sharma@nirmaya.health"
    assert body["data"]["full_name"] == "Dr. Alok Sharma"
    assert body["data"]["role"] == "doctor"
    assert body["data"]["supabase_uid"] == "sb-auth-doctor-001"


@pytest.mark.asyncio
async def test_get_me_missing_authorization_header(auth_api_client) -> None:
    """Verify GET /api/v1/auth/me rejects unauthenticated requests with 401 and WWW-Authenticate."""
    client, _ = auth_api_client

    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "AUTHENTICATION_REQUIRED"
    assert "WWW-Authenticate" in response.headers


@pytest.mark.asyncio
async def test_get_me_invalid_token(auth_api_client) -> None:
    """Verify GET /api/v1/auth/me rejects corrupted tokens with 401."""
    client, _ = auth_api_client

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this-is-not-a-valid-token-string"},
    )
    assert response.status_code == 401

    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_get_me_inactive_user(auth_api_client) -> None:
    """Verify GET /api/v1/auth/me returns 403 Forbidden for deactivated accounts."""
    client, session_factory = auth_api_client

    async with session_factory() as session:
        user = User(
            email="inactive.patient@example.com",
            full_name="Deactivated Patient",
            role=UserRole.PATIENT,
            supabase_uid="sb-auth-inactive-001",
            is_active=False,
        )
        session.add(user)
        await session.commit()

    token = create_access_token({
        "sub": "sb-auth-inactive-001",
        "email": "inactive.patient@example.com",
        "role": "patient",
    })

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_verify_token_endpoint(auth_api_client) -> None:
    """Verify POST /api/v1/auth/verify correctly validates active tokens and detects invalid tokens."""
    client, _ = auth_api_client

    # 1. Valid token check
    valid_token = create_access_token({
        "sub": "sb-test-verify-user",
        "email": "verify.user@example.com",
        "role": "patient",
    })
    res_valid = await client.post("/api/v1/auth/verify", json={"token": valid_token})
    assert res_valid.status_code == 200
    body_valid = res_valid.json()
    assert body_valid["data"]["valid"] is True
    assert body_valid["data"]["subject"] == "sb-test-verify-user"
    assert body_valid["data"]["claims"]["email"] == "verify.user@example.com"

    # 2. Expired token check
    expired_token = create_access_token(
        {"sub": "sb-test-expired"},
        expires_delta=timedelta(seconds=-30),
    )
    res_expired = await client.post("/api/v1/auth/verify", json={"token": expired_token})
    assert res_expired.status_code == 200
    body_expired = res_expired.json()
    assert body_expired["data"]["valid"] is False


@pytest.mark.asyncio
async def test_test_token_generation_and_me_roundtrip(auth_api_client) -> None:
    """Verify POST /api/v1/auth/test-token issues a functional JWT usable against /auth/me."""
    client, session_factory = auth_api_client

    # Seed test user
    async with session_factory() as session:
        user = User(
            email="test.roundtrip@nirmaya.health",
            full_name="Roundtrip Tester",
            role=UserRole.PATIENT,
            supabase_uid="sb-auth-roundtrip-001",
            is_active=True,
        )
        session.add(user)
        await session.commit()

    # Request test token
    token_res = await client.post(
        "/api/v1/auth/test-token",
        json={
            "email": "test.roundtrip@nirmaya.health",
            "sub": "sb-auth-roundtrip-001",
            "role": "patient",
            "expires_minutes": 30,
        },
    )
    assert token_res.status_code == 200
    token_body = token_res.json()
    assert token_body["success"] is True
    access_token = token_body["data"]["access_token"]
    assert len(access_token) > 20

    # Consume token on /auth/me
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    me_body = me_res.json()
    assert me_body["data"]["email"] == "test.roundtrip@nirmaya.health"
    assert me_body["data"]["full_name"] == "Roundtrip Tester"
