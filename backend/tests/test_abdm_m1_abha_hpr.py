"""Automated test suite for ABDM Milestone 1 ABHA Issuance, PHR Handle & HPR Onboarding.

Verifies:
- 14-digit ABHA number generation format, Verhoeff check-digit mathematical validity
- PHR handle syntax, reserved keyword detection, and collision suggestions
- Patient profile database binding for abha_number and abha_address
- Doctor Healthcare Professional Registry (HPR) onboarding and duplicate conflict defense
- Endpoints:
  - POST /api/v1/abdm/m1/abha/create
  - GET  /api/v1/abdm/m1/phr/check-availability
  - POST /api/v1/abdm/m1/phr/link
  - POST /api/v1/abdm/m1/hpr/onboard
"""

import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.doctor import DoctorProfile
from app.models.enums import MedicalSpecialty, UserRole
from app.models.patient import PatientProfile
from app.models.user import User
from app.services.aadhaar_otp import validate_verhoeff
from app.services.abdm_issuance import _generate_raw_14_digit_abha


@pytest_asyncio.fixture
async def issuance_test_env():
    """Isolated in-memory SQLite database environment for ABHA issuance tests."""
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


def test_raw_14_digit_abha_generation_and_verhoeff():
    """Verify generated ABHA numbers strictly match 91-XXXX-XXXX-XXXX and pass Verhoeff validation."""
    for _ in range(10):
        formatted = _generate_raw_14_digit_abha()
        assert len(formatted) == 17  # 14 digits + 3 hyphens
        assert formatted.startswith("91-")

        parts = formatted.split("-")
        assert len(parts) == 4
        assert len(parts[0]) == 2
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4

        raw_digits = formatted.replace("-", "")
        assert len(raw_digits) == 14
        assert raw_digits.isdigit()
        assert validate_verhoeff(raw_digits) is True


@pytest.mark.asyncio
async def test_endpoint_abha_create_lifecycle(issuance_test_env):
    """Verify POST /api/v1/abdm/m1/abha/create generates and saves 14-digit ABHA number."""
    client, session_factory = issuance_test_env

    # 1. Create a patient in test database
    patient_user_id = str(uuid.uuid4())
    patient_profile_id = str(uuid.uuid4())

    async with session_factory() as session:
        user = User(
            id=patient_user_id,
            email="patient.test@example.com",
            full_name="Arun Patel",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        patient = PatientProfile(
            id=patient_profile_id,
            user_id=patient_user_id,
        )
        session.add(user)
        session.add(patient)
        await session.commit()

    token = create_access_token(
        data={"sub": patient_user_id, "role": UserRole.PATIENT.value, "email": "patient.test@example.com"}
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Issue 14-digit ABHA number
    resp = await client.post(
        "/api/v1/abdm/m1/abha/create",
        json={"patient_id": patient_profile_id},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    first_abha = data["data"]["abha_number"]
    assert first_abha.startswith("91-")
    assert len(first_abha) == 17

    # 3. Verify in database
    async with session_factory() as session:
        p = await session.get(PatientProfile, patient_profile_id)
        assert p is not None
        assert p.abha_number == first_abha

    # 4. Calling again returns the existing ABHA number (idempotent)
    resp2 = await client.post(
        "/api/v1/abdm/m1/abha/create",
        json={"patient_id": patient_profile_id},
        headers=headers,
    )
    assert resp2.status_code == 200
    assert resp2.json()["data"]["abha_number"] == first_abha


@pytest.mark.asyncio
async def test_endpoint_phr_availability(issuance_test_env):
    """Verify GET /api/v1/abdm/m1/phr/check-availability evaluates availability and suggests alternatives."""
    client, _ = issuance_test_env

    # 1. Available handle
    resp = await client.get("/api/v1/abdm/m1/phr/check-availability?handle=unique.patel")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["handle"] == "unique.patel"
    assert data["full_address"] == "unique.patel@abdm"
    assert data["is_available"] is True

    # 2. Reserved handle
    resp_res = await client.get("/api/v1/abdm/m1/phr/check-availability?handle=admin")
    assert resp_res.status_code == 200
    data_res = resp_res.json()["data"]
    assert data_res["is_available"] is False
    assert len(data_res["suggestions"]) > 0

    # 3. Invalid syntax (less than 3 chars)
    resp_inv = await client.get("/api/v1/abdm/m1/phr/check-availability?handle=a")
    assert resp_inv.status_code == 200
    assert resp_inv.json()["data"]["is_available"] is False


@pytest.mark.asyncio
async def test_endpoint_phr_link_and_collision(issuance_test_env):
    """Verify POST /api/v1/abdm/m1/phr/link binds handle and rejects duplicate claims."""
    client, session_factory = issuance_test_env

    # Create two patients
    p1_uid, p1_pid = str(uuid.uuid4()), str(uuid.uuid4())
    p2_uid, p2_pid = str(uuid.uuid4()), str(uuid.uuid4())

    async with session_factory() as session:
        u1 = User(id=p1_uid, email="p1@example.com", full_name="Patient One", role=UserRole.PATIENT, is_active=True, is_verified=True)
        u2 = User(id=p2_uid, email="p2@example.com", full_name="Patient Two", role=UserRole.PATIENT, is_active=True, is_verified=True)
        pat1 = PatientProfile(id=p1_pid, user_id=p1_uid)
        pat2 = PatientProfile(id=p2_pid, user_id=p2_uid)
        session.add_all([u1, u2, pat1, pat2])
        await session.commit()

    token1 = create_access_token(data={"sub": p1_uid, "role": UserRole.PATIENT.value, "email": "p1@example.com"})
    token2 = create_access_token(data={"sub": p2_uid, "role": UserRole.PATIENT.value, "email": "p2@example.com"})

    # Patient 1 links handle
    resp1 = await client.post(
        "/api/v1/abdm/m1/phr/link",
        json={"patient_id": p1_pid, "abha_address": "arun.kumar@abdm"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert resp1.status_code == 200
    assert resp1.json()["data"]["abha_address"] == "arun.kumar@abdm"

    # Verify availability is now False
    avail_resp = await client.get("/api/v1/abdm/m1/phr/check-availability?handle=arun.kumar")
    assert avail_resp.json()["data"]["is_available"] is False
    assert len(avail_resp.json()["data"]["suggestions"]) > 0

    # Patient 2 tries to link same handle -> rejected
    resp2 = await client.post(
        "/api/v1/abdm/m1/phr/link",
        json={"patient_id": p2_pid, "abha_address": "arun.kumar@abdm"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp2.status_code == 400
    assert "already registered" in resp2.json()["message"]


@pytest.mark.asyncio
async def test_endpoint_hpr_onboard_and_duplicate_check(issuance_test_env):
    """Verify POST /api/v1/abdm/m1/hpr/onboard registers doctor with Healthcare Professional Registry."""
    client, session_factory = issuance_test_env

    doc1_uid, doc1_pid = str(uuid.uuid4()), str(uuid.uuid4())
    doc2_uid, doc2_pid = str(uuid.uuid4()), str(uuid.uuid4())

    async with session_factory() as session:
        u1 = User(id=doc1_uid, email="d1@example.com", full_name="Dr. Ananya Sharma", role=UserRole.DOCTOR, is_active=True, is_verified=True)
        u2 = User(id=doc2_uid, email="d2@example.com", full_name="Dr. Rajesh Varma", role=UserRole.DOCTOR, is_active=True, is_verified=True)
        doc1 = DoctorProfile(id=doc1_pid, user_id=doc1_uid, registration_number="DMC-91024", medical_council="Delhi Medical Council", qualifications="MBBS, MD", specialty=MedicalSpecialty.CARDIOLOGY)
        doc2 = DoctorProfile(id=doc2_pid, user_id=doc2_uid, registration_number="KMC-48190", medical_council="Karnataka Medical Council", qualifications="MBBS, MD", specialty=MedicalSpecialty.DERMATOLOGY)
        session.add_all([u1, u2, doc1, doc2])
        await session.commit()

    token1 = create_access_token(data={"sub": doc1_uid, "role": UserRole.DOCTOR.value, "email": "d1@example.com"})
    token2 = create_access_token(data={"sub": doc2_uid, "role": UserRole.DOCTOR.value, "email": "d2@example.com"})

    # Doctor 1 onboards with HPR ID
    resp1 = await client.post(
        "/api/v1/abdm/m1/hpr/onboard",
        json={
            "doctor_id": doc1_pid,
            "registration_number": "DMC-91024",
            "medical_council": "Delhi Medical Council",
            "hpr_handle": "ananya.sharma",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()["data"]
    assert data1["hpr_id"] == "ananya.sharma@hpr.abdm"
    assert data1["status"] == "verified"

    # Verify in DB
    async with session_factory() as session:
        d = await session.get(DoctorProfile, doc1_pid)
        assert d is not None
        assert d.hpr_id == "ananya.sharma@hpr.abdm"

    # Doctor 2 tries to onboard with the same HPR ID -> rejected
    resp2 = await client.post(
        "/api/v1/abdm/m1/hpr/onboard",
        json={
            "doctor_id": doc2_pid,
            "registration_number": "KMC-48190",
            "medical_council": "Karnataka Medical Council",
            "hpr_handle": "ananya.sharma@hpr.abdm",
        },
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp2.status_code == 400
    assert "already assigned" in resp2.json()["message"]
