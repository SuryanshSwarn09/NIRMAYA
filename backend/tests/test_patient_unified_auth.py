"""Automated test suite for Unified DigiLocker & Aadhaar OTP Passwordless Patient Gateway.

Verifies:
- One-tap passwordless registration with auto-minted 14-digit ABHA Number and @abdm handle
- Seamless login for existing verified patients without duplicate user creation
- Suggestion 2: Session longevity toggle (30-day extended JWT token vs 24h token)
- Suggestion 1: Active mobile OTP fallback authentication
- Verhoeff check-digit mathematical invariance on auto-minted ABHA numbers
- Database demographic synchronization into PatientProfile and User models
"""

import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import Gender, UserRole
from app.models.patient import PatientProfile
from app.models.user import User
from app.services.aadhaar_otp import validate_verhoeff


@pytest_asyncio.fixture
async def patient_auth_test_env():
    """Isolated in-memory SQLite database environment for passwordless patient auth tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_new_patient_auto_registration_and_auto_abha(patient_auth_test_env):
    """Verify new patient auto-creation, demographic sync, auto-ABHA minting, and 30-day session."""
    client, session_factory = patient_auth_test_env

    email = f"priya.sharma.{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "source": "aadhaar_otp",
        "name": "Priya Sharma",
        "gender": "female",
        "date_of_birth": "1994-08-12",
        "masked_aadhaar": "XXXX-XXXX-9812",
        "mobile_number": "9876543210",
        "email": email,
        "formatted_address": "Flat 402, Lotus Towers, Indiranagar, Bengaluru, Karnataka - 560038",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "pincode": "560038",
        "remember_me": True,
    }

    resp = await client.post("/api/v1/auth/patient/login-or-register", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    result = data["data"]
    assert result["is_new_user"] is True
    assert result["name"] == "Priya Sharma"
    assert result["expires_in_seconds"] == 2592000  # 30 days
    assert result["access_token"] is not None

    # Verify auto-minted 14-digit ABHA Number (Suggestion 3)
    abha_num = result["abha_number"]
    assert abha_num is not None
    assert abha_num.startswith("91-")
    raw_digits = abha_num.replace("-", "")
    assert len(raw_digits) == 14
    assert validate_verhoeff(raw_digits) is True

    # Verify auto-minted @abdm PHR handle
    assert result["abha_address"].endswith("@abdm")

    # Assert database state
    async with session_factory() as session:
        created_user = await session.get(User, result["user_id"])
        assert created_user is not None
        assert created_user.role == UserRole.PATIENT
        assert created_user.is_verified is True
        assert created_user.phone_number == "9876543210"

        created_patient = await session.get(PatientProfile, result["patient_id"])
        assert created_patient is not None
        assert created_patient.gender == Gender.FEMALE
        assert created_patient.city == "Bengaluru Urban"
        assert created_patient.state == "Karnataka"
        assert created_patient.abha_number == abha_num


@pytest.mark.asyncio
async def test_existing_patient_seamless_login(patient_auth_test_env):
    """Verify existing patient logging in gets authenticated without duplicate accounts."""
    client, session_factory = patient_auth_test_env

    email = f"arun.patel.{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "source": "digilocker",
        "name": "Arun Kumar Patel",
        "gender": "male",
        "date_of_birth": "1990-06-04",
        "masked_aadhaar": "XXXX-XXXX-4821",
        "mobile_number": "9184721048",
        "email": email,
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "remember_me": True,
    }

    # First call: Registration
    resp1 = await client.post("/api/v1/auth/patient/login-or-register", json=payload)
    assert resp1.status_code == 200
    res1_data = resp1.json()["data"]
    assert res1_data["is_new_user"] is True
    u_id_1 = res1_data["user_id"]
    p_id_1 = res1_data["patient_id"]
    abha_1 = res1_data["abha_number"]

    # Second call: Login with updated address
    payload["formatted_address"] = "Updated House #12, Koramangala, Bengaluru"
    resp2 = await client.post("/api/v1/auth/patient/login-or-register", json=payload)
    assert resp2.status_code == 200
    res2_data = resp2.json()["data"]
    assert res2_data["is_new_user"] is False
    assert res2_data["user_id"] == u_id_1
    assert res2_data["patient_id"] == p_id_1
    assert res2_data["abha_number"] == abha_1
    assert res2_data["access_token"] is not None

    # Verify updated address in DB
    async with session_factory() as session:
        pat = await session.get(PatientProfile, p_id_1)
        assert pat is not None
        assert pat.address_line == "Updated House #12, Koramangala, Bengaluru"


@pytest.mark.asyncio
async def test_session_longevity_toggle(patient_auth_test_env):
    """Verify remember_me parameter controls 30-day (2,592,000s) vs 24-hour (86,400s) TTL."""
    client, _ = patient_auth_test_env

    # 1. 24-hour session (remember_me = False)
    payload_24h = {
        "source": "aadhaar_otp",
        "name": "Sunita Rao",
        "email": f"sunita.{uuid.uuid4().hex[:6]}@example.com",
        "remember_me": False,
    }
    resp_24h = await client.post("/api/v1/auth/patient/login-or-register", json=payload_24h)
    assert resp_24h.status_code == 200
    assert resp_24h.json()["data"]["expires_in_seconds"] == 86400

    # 2. 30-day session (remember_me = True)
    payload_30d = {
        "source": "aadhaar_otp",
        "name": "Sunita Rao",
        "email": f"sunita.30d.{uuid.uuid4().hex[:6]}@example.com",
        "remember_me": True,
    }
    resp_30d = await client.post("/api/v1/auth/patient/login-or-register", json=payload_30d)
    assert resp_30d.status_code == 200
    assert resp_30d.json()["data"]["expires_in_seconds"] == 2592000


@pytest.mark.asyncio
async def test_mobile_fallback_authentication(patient_auth_test_env):
    """Verify fallback mobile OTP authentication for mismatched SIM cards."""
    client, session_factory = patient_auth_test_env

    phone = "9845012345"
    payload = {
        "mobile_number": phone,
        "otp": "123456",
        "abha_identifier": None,
        "remember_me": True,
    }

    # 1. First mobile login auto-provisions patient
    resp = await client.post("/api/v1/auth/patient/mobile-fallback-login", json=payload)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_new_user"] is True
    assert data["access_token"] is not None
    assert data["abha_number"].startswith("91-")
    assert data["expires_in_seconds"] == 2592000

    # 2. Subsequent mobile login retrieves existing profile
    resp2 = await client.post("/api/v1/auth/patient/mobile-fallback-login", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]
    assert data2["is_new_user"] is False
    assert data2["user_id"] == data["user_id"]
    assert data2["patient_id"] == data["patient_id"]


@pytest.mark.asyncio
async def test_mobile_fallback_invalid_otp(patient_auth_test_env):
    """Verify mobile fallback rejects invalid OTP with 401."""
    client, _ = patient_auth_test_env

    payload = {
        "mobile_number": "9845099999",
        "otp": "999999",  # Invalid OTP
        "remember_me": True,
    }
    resp = await client.post("/api/v1/auth/patient/mobile-fallback-login", json=payload)
    assert resp.status_code == 401
    assert "Invalid or expired" in resp.json()["message"]
