"""Integration tests for Digital ABHA ID Card generation and QR cryptographic signature verification."""

import json
from datetime import date
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import BloodGroup, Gender, UserRole
from app.models.patient import PatientProfile
from app.models.user import User


@pytest_asyncio.fixture
async def abha_test_client():
    """Provide an isolated in-memory test database and client for ABHA card tests."""
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


def auth_header_for(user: User) -> dict:
    """Generate authorization headers for a given user model."""
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_generate_abha_card_success(abha_test_client) -> None:
    """Verify GET /api/v1/patients/{patient_id}/abha-card returns signed claims and QR payload."""
    client, session_factory = abha_test_client

    async with session_factory() as session:
        patient_user = User(
            id="usr-arun-01",
            email="arun.patel@example.com",
            full_name="Arun Patel",
            phone_number="+91-9876543210",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        patient_profile = PatientProfile(
            id="pat-arun-01",
            user_id="usr-arun-01",
            gender=Gender.MALE,
            blood_group=BloodGroup.O_POSITIVE,
            date_of_birth=date(1992, 5, 14),
            abha_number="91-8472-1092-4821",
            abha_address="arun.patel@abdm",
            address_line="Flat 402, Shanti Vihar",
            city="New Delhi",
            state="NCT of Delhi",
            pincode="110001",
        )
        session.add(patient_user)
        session.add(patient_profile)
        await session.commit()

    # Request ABHA card
    res = await client.get(
        "/api/v1/patients/pat-arun-01/abha-card",
        headers=auth_header_for(patient_user),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True

    data = body["data"]
    card = data["card_data"]
    assert card["name"] == "Arun Patel"
    assert card["abha_number"] == "91-8472-1092-4821"
    assert card["abha_address"] == "arun.patel@abdm"
    assert card["gender"] == "M"
    assert card["blood_group"] == "O+"
    assert card["date_of_birth"] == "1992-05-14"
    assert card["mobile"] is not None
    assert "*" in card["mobile"]  # Masked

    # Verify signature
    assert data["signature"].startswith("SHA256:")

    # Verify QR payload string
    qr_data = json.loads(data["qr_payload"])
    assert qr_data["hidn"] == "91-8472-1092-4821"
    assert qr_data["hid"] == "arun.patel@abdm"
    assert qr_data["name"] == "Arun Patel"
    assert qr_data["signature"] == data["signature"]


@pytest.mark.asyncio
async def test_verify_abha_qr_valid_payload(abha_test_client) -> None:
    """Verify POST /api/v1/patients/verify-abha-qr validates untampered QR payloads."""
    client, session_factory = abha_test_client

    async with session_factory() as session:
        user = User(
            id="usr-test-01",
            email="tester@example.com",
            full_name="Test Citizen",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        patient = PatientProfile(
            id="pat-test-01",
            user_id="usr-test-01",
            gender=Gender.FEMALE,
            blood_group=BloodGroup.B_POSITIVE,
            date_of_birth=date(1995, 8, 20),
            abha_number="91-2222-3333-4444",
            abha_address="citizen.fem@abdm",
        )
        session.add(user)
        session.add(patient)
        await session.commit()

    # Generate legitimate card
    gen_res = await client.get(
        "/api/v1/patients/pat-test-01/abha-card",
        headers=auth_header_for(user),
    )
    qr_string = gen_res.json()["data"]["qr_payload"]

    # Verify via verification endpoint
    verify_res = await client.post(
        "/api/v1/patients/verify-abha-qr",
        headers=auth_header_for(user),
        json={"qr_string": qr_string},
    )
    assert verify_res.status_code == 200
    v_body = verify_res.json()["data"]
    assert v_body["is_valid"] is True
    assert "verified successfully" in v_body["message"].lower()
    assert v_body["claims"]["hidn"] == "91-2222-3333-4444"


@pytest.mark.asyncio
async def test_verify_abha_qr_detects_tampering(abha_test_client) -> None:
    """Verify POST /api/v1/patients/verify-abha-qr rejects tampered claims."""
    client, session_factory = abha_test_client

    async with session_factory() as session:
        user = User(
            id="usr-test-02",
            email="victim@example.com",
            full_name="Victim User",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        patient = PatientProfile(
            id="pat-test-02",
            user_id="usr-test-02",
            gender=Gender.MALE,
            blood_group=BloodGroup.A_POSITIVE,
            date_of_birth=date(1990, 1, 1),
            abha_number="91-5555-6666-7777",
            abha_address="victim@abdm",
        )
        session.add(user)
        session.add(patient)
        await session.commit()

    gen_res = await client.get(
        "/api/v1/patients/pat-test-02/abha-card",
        headers=auth_header_for(user),
    )
    qr_data = json.loads(gen_res.json()["data"]["qr_payload"])

    # Tamper with the name without re-signing
    qr_data["name"] = "Impostor Attacker"
    tampered_string = json.dumps(qr_data)

    verify_res = await client.post(
        "/api/v1/patients/verify-abha-qr",
        headers=auth_header_for(user),
        json={"qr_string": tampered_string},
    )
    assert verify_res.status_code == 200
    v_body = verify_res.json()["data"]
    assert v_body["is_valid"] is False
    assert "mismatch" in v_body["message"].lower() or "tampered" in v_body["message"].lower()


@pytest.mark.asyncio
async def test_verify_abha_qr_malformed_input(abha_test_client) -> None:
    """Verify POST /api/v1/patients/verify-abha-qr handles malformed inputs gracefully."""
    client, session_factory = abha_test_client

    async with session_factory() as session:
        user = User(
            id="usr-test-03",
            email="tester3@example.com",
            full_name="Tester Three",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

    verify_res = await client.post(
        "/api/v1/patients/verify-abha-qr",
        headers=auth_header_for(user),
        json={"qr_string": "definitely-not-valid-json"},
    )
    assert verify_res.status_code == 200
    v_body = verify_res.json()["data"]
    assert v_body["is_valid"] is False
    assert "not valid json" in v_body["message"].lower()


@pytest.mark.asyncio
async def test_patient_cross_tenant_abha_card_isolation(abha_test_client) -> None:
    """Verify unauthorized patients cannot generate or view other patients' ABHA cards."""
    client, session_factory = abha_test_client

    async with session_factory() as session:
        patient_user_a = User(
            id="usr-patient-a",
            email="patienta@example.com",
            full_name="Patient User A",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        patient_a = PatientProfile(
            id="pat-a",
            user_id="usr-patient-a",
            abha_number="91-0000-1111-2222",
            abha_address="patienta@abdm",
        )
        patient_user_b = User(
            id="usr-patient-b",
            email="patientb@example.com",
            full_name="Patient User B",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        patient_b = PatientProfile(
            id="pat-b",
            user_id="usr-patient-b",
            abha_number="91-3333-4444-5555",
            abha_address="patientb@abdm",
        )
        doctor_user = User(
            id="usr-doctor",
            email="doctor@example.com",
            full_name="Dr. Attending Doctor",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True,
        )
        session.add_all([patient_user_a, patient_a, patient_user_b, patient_b, doctor_user])
        await session.commit()

    # Patient B tries to access Patient A's card -> 403 Forbidden
    res_unauth = await client.get(
        "/api/v1/patients/pat-a/abha-card",
        headers=auth_header_for(patient_user_b),
    )
    assert res_unauth.status_code == 403

    # Attending Doctor accesses Patient A's card -> 200 OK
    res_doctor = await client.get(
        "/api/v1/patients/pat-a/abha-card",
        headers=auth_header_for(doctor_user),
    )
    assert res_doctor.status_code == 200
    assert res_doctor.json()["data"]["card_data"]["abha_address"] == "patienta@abdm"
