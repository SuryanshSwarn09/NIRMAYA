"""Automated test suite for ABDM Milestone 1 Direct Aadhaar Demographic OTP Verification.

Verifies:
- Mathematical correctness of Verhoeff checksum algorithm for UIDAI Aadhaar
- In-memory AadhaarSessionManager lifecycle, attempt limit enforcement, and TTL expiry
- Endpoints:
  - POST /api/v1/abdm/m1/aadhaar/generate-otp
  - POST /api/v1/abdm/m1/aadhaar/verify-otp
  - POST /api/v1/abdm/m1/aadhaar/sync-patient/{patient_id}
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.exceptions import AppException
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import Gender, UserRole
from app.models.patient import PatientProfile
from app.models.user import User
from app.services.aadhaar_otp import (
    AadhaarSessionManager,
    aadhaar_session_manager,
    generate_aadhaar_otp,
    generate_verhoeff,
    validate_verhoeff,
    verify_aadhaar_otp,
)


@pytest_asyncio.fixture
async def aadhaar_test_env():
    """Isolated in-memory SQLite database environment for Aadhaar OTP tests."""
    aadhaar_session_manager.clear()

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
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, session_factory

    app.dependency_overrides.clear()
    await engine.dispose()
    aadhaar_session_manager.clear()


def test_verhoeff_checksum_algorithm():
    """Verify that Verhoeff calculation and validation comply with UIDAI Aadhaar specifications."""
    base_11_digits = "91847210482"
    check_digit = generate_verhoeff(base_11_digits)
    assert len(check_digit) == 1
    assert check_digit.isdigit()

    full_aadhaar = base_11_digits + check_digit
    assert len(full_aadhaar) == 12
    assert validate_verhoeff(full_aadhaar) is True

    # Check that altering any single digit invalidates checksum
    altered = full_aadhaar[:-2] + ("0" if full_aadhaar[-2] != "0" else "1") + full_aadhaar[-1]
    assert validate_verhoeff(altered) is False

    # Check non-numeric strings
    assert validate_verhoeff("") is False
    assert validate_verhoeff("abc") is False


def test_aadhaar_session_manager_lifecycle():
    """Verify session creation, OTP verification, and single-use consumption."""
    manager = AadhaarSessionManager(session_ttl_seconds=600, max_attempts=3)
    txn_id, masked_phone, masked_aadhaar = manager.create_session("918472104821")

    assert txn_id.startswith("TXN-AADHAAR-")
    assert masked_aadhaar == "XXXX-XXXX-4821"
    assert "482" in masked_phone

    # Successful verification with standard simulation OTP
    demographics = manager.verify_otp(txn_id, "123456")
    assert demographics.name == "Arun Kumar Patel"
    assert demographics.gender == "male"
    assert demographics.masked_aadhaar == "XXXX-XXXX-4821"
    assert demographics.address.state == "Karnataka"

    # Attempting to re-verify consumed session raises error
    with pytest.raises(AppException) as exc_info:
        manager.verify_otp(txn_id, "123456")
    assert "already been verified and consumed" in str(exc_info.value)


def test_aadhaar_session_attempts_exhaustion():
    """Verify that exceeding 3 failed attempts invalidates the transaction."""
    manager = AadhaarSessionManager(session_ttl_seconds=600, max_attempts=3)
    txn_id, _, _ = manager.create_session("918472104821")

    # 1st wrong attempt
    with pytest.raises(AppException) as exc1:
        manager.verify_otp(txn_id, "000000")
    assert "2 attempts remaining" in str(exc1.value)

    # 2nd wrong attempt
    with pytest.raises(AppException) as exc2:
        manager.verify_otp(txn_id, "000000")
    assert "1 attempt remaining" in str(exc2.value)

    # 3rd wrong attempt - max attempts reached
    with pytest.raises(AppException) as exc3:
        manager.verify_otp(txn_id, "000000")
    assert "Maximum OTP verification attempts exceeded" in str(exc3.value)

    # Session is purged after exhaustion
    with pytest.raises(AppException) as exc4:
        manager.verify_otp(txn_id, "123456")
    assert "expired or not found" in str(exc4.value)


def test_aadhaar_session_ttl_expiry():
    """Verify that sessions expire after TTL duration."""
    manager = AadhaarSessionManager(session_ttl_seconds=600, max_attempts=3)
    txn_id, _, _ = manager.create_session("918472104821")

    # Artificially age the session past TTL (15 minutes ago)
    manager._sessions[txn_id]["created_at"] = datetime.now(timezone.utc) - timedelta(minutes=15)

    with pytest.raises(AppException) as exc:
        manager.verify_otp(txn_id, "123456")
    assert "session has expired" in str(exc.value)


@pytest.mark.asyncio
async def test_endpoint_generate_otp(aadhaar_test_env):
    """Verify POST /api/v1/abdm/m1/aadhaar/generate-otp creates active transaction."""
    client, _ = aadhaar_test_env

    # 1. Valid 12-digit Aadhaar with hyphens
    resp = await client.post(
        "/api/v1/abdm/m1/aadhaar/generate-otp",
        json={"aadhaar_number": "9184-7210-4821"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["txn_id"].startswith("TXN-AADHAAR-")
    assert "482" in data["data"]["masked_mobile"]
    assert data["data"]["expires_in"] == 600

    # 2. Invalid Aadhaar format (less than 12 digits)
    resp_invalid = await client.post(
        "/api/v1/abdm/m1/aadhaar/generate-otp",
        json={"aadhaar_number": "12345"},
    )
    assert resp_invalid.status_code == 422


@pytest.mark.asyncio
async def test_endpoint_verify_otp(aadhaar_test_env):
    """Verify POST /api/v1/abdm/m1/aadhaar/verify-otp returns verified claims."""
    client, _ = aadhaar_test_env

    # 1. Generate OTP
    gen_resp = await client.post(
        "/api/v1/abdm/m1/aadhaar/generate-otp",
        json={"aadhaar_number": "918472104821"},
    )
    assert gen_resp.status_code == 200
    txn_id = gen_resp.json()["data"]["txn_id"]

    # 2. Verify with valid OTP
    verify_resp = await client.post(
        "/api/v1/abdm/m1/aadhaar/verify-otp",
        json={"txn_id": txn_id, "otp": "123456"},
    )
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert data["success"] is True
    result = data["data"]
    assert result["verified"] is True
    assert result["demographics"]["name"] == "Arun Kumar Patel"
    assert result["demographics"]["gender"] == "male"
    assert result["demographics"]["masked_aadhaar"] == "XXXX-XXXX-4821"
    assert result["demographics"]["address"]["pincode"] == "560034"


@pytest.mark.asyncio
async def test_endpoint_sync_patient_identity(aadhaar_test_env):
    """Verify POST /api/v1/abdm/m1/aadhaar/sync-patient/{patient_id} updates patient profile."""
    client, session_factory = aadhaar_test_env

    # 1. Create a patient user and profile in the test database
    patient_user_id = str(uuid.uuid4())
    patient_profile_id = str(uuid.uuid4())

    async with session_factory() as session:
        user = User(
            id=patient_user_id,
            email="arun.aadhaar@example.com",
            full_name="Unverified Name",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=False,
        )
        patient = PatientProfile(
            id=patient_profile_id,
            user_id=patient_user_id,
            gender=Gender.UNKNOWN,
        )
        session.add(user)
        session.add(patient)
        await session.commit()

    # 2. Authenticate as the patient
    token = create_access_token(
        data={"sub": patient_user_id, "role": UserRole.PATIENT.value, "email": "arun.aadhaar@example.com"}
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Generate and verify Aadhaar OTP
    gen_resp = await client.post(
        "/api/v1/abdm/m1/aadhaar/generate-otp",
        json={"aadhaar_number": "918472104821"},
    )
    txn_id = gen_resp.json()["data"]["txn_id"]

    verify_resp = await client.post(
        "/api/v1/abdm/m1/aadhaar/verify-otp",
        json={"txn_id": txn_id, "otp": "123456"},
    )
    verified_data = verify_resp.json()["data"]

    # 4. Synchronize into patient vault
    sync_resp = await client.post(
        f"/api/v1/abdm/m1/aadhaar/sync-patient/{patient_profile_id}",
        json=verified_data,
        headers=headers,
    )
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["success"] is True
    assert sync_data["data"]["patient_id"] == patient_profile_id
    assert sync_data["data"]["name"] == "Arun Kumar Patel"
    assert sync_data["data"]["masked_aadhaar"] == "XXXX-XXXX-4821"
    assert sync_data["data"]["is_identity_verified"] is True
    assert sync_data["data"]["source"] == "aadhaar_otp"

    # 5. Verify database was updated
    async with session_factory() as session:
        updated_patient = await session.get(PatientProfile, patient_profile_id)
        assert updated_patient is not None
        assert updated_patient.gender == Gender.MALE
        assert updated_patient.city == "Bengaluru Urban"
        assert updated_patient.state == "Karnataka"
        assert updated_patient.pincode == "560034"
