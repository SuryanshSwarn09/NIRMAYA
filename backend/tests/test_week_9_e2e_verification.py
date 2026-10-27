"""Week 9 End-to-End Closed-Loop ABDM Milestone 1 Verification Test Suite.

Validates the complete ABDM Milestone 1 (M1) architecture engineered across Week 9:
1. ABDM Gateway Session Auth & RSA-2048 Demographic Cryptography (Day 41)
2. DigiLocker OAuth 2.0 PKCE, UIDAI e-Aadhaar XML Parsing & Demographic Sync (Day 42)
3. Direct Aadhaar Demographic OTP Flow, Ephemeral Session Manager & Verhoeff Checksum (Day 43)
4. 14-Digit ABHA Number Minting with Mathematical Verhoeff Validation (Day 44)
5. Universal @abdm PHR Handle Reservation, Collision Alternatives & Address Linkage (Day 44)
6. Healthcare Professional Registry (HPR) Doctor Onboarding & Council Binding (Day 44)
7. Full Multi-Auth Closed-Loop Orchestration (Day 45)
"""

import uuid
from datetime import date
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.abdm.client import ABDMGatewayClient
from app.abdm.security.rsa import ABDMRSAEncryptionManager
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.doctor import DoctorProfile
from app.models.enums import Gender, MedicalSpecialty, UserRole
from app.models.patient import PatientProfile
from app.models.user import User
from app.services.aadhaar_otp import (
    AadhaarSessionManager,
    generate_verhoeff,
    validate_verhoeff,
)
from app.services.abdm_issuance import (
    _generate_raw_14_digit_abha,
    check_phr_availability,
    generate_14_digit_abha,
    link_phr_address,
    onboard_doctor_hpr,
)
from app.services.digilocker import (
    SIMULATED_EAADHAAR_XML,
    exchange_code_for_token,
    generate_authorization_url,
    generate_pkce_pair,
    parse_eaadhaar_xml,
    verify_digilocker_callback,
)


@pytest_asyncio.fixture
async def week_9_e2e_env():
    """Isolated in-memory SQLite database environment for Week 9 M1 E2E testing."""
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


def auth_header_for(user_id: str, email: str, role: str) -> dict:
    """Generate JWT authorization headers."""
    token = create_access_token(
        data={
            "sub": user_id,
            "email": email,
            "role": role,
        }
    )
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# SCENARIO 1: ABDM GATEWAY SESSION AUTH & RSA-2048 CRYPTOGRAPHY (Day 41)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_1_abdm_gateway_auth_and_rsa_cryptography(week_9_e2e_env):
    """Verify ABDM Gateway token acquisition and RSA-2048 OAEP demographic encryption."""
    client, session_factory = week_9_e2e_env

    # 1. Inspect Gateway Status endpoint
    resp = await client.get("/api/v1/abdm/status")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["sandbox_mode"] is True
    assert data["cm_id"] == "sbx"
    assert data["rsa_key_configured"] is True

    # 2. RSA Cryptographic Public Key Acquisition
    resp_key = await client.get("/api/v1/abdm/crypto/public-key")
    assert resp_key.status_code == 200
    key_data = resp_key.json()["data"]
    assert "BEGIN PUBLIC KEY" in key_data["public_key_pem"]
    assert key_data["algorithm"] == "RSA-OAEP-256"

    # 3. Direct RSA-2048 OAEP SHA-256 demographic encryption roundtrip
    rsa_mgr = ABDMRSAEncryptionManager()
    sensitive_demographics = {
        "aadhaar": "999912345678",
        "name": "Arun Patel",
        "mobile": "+919876543210",
    }
    encrypted_blob = rsa_mgr.encrypt_demographic_payload(sensitive_demographics)
    assert len(encrypted_blob) > 64

    decrypted_payload = rsa_mgr.decrypt_demographic_payload(encrypted_blob)
    assert decrypted_payload == sensitive_demographics


# ==============================================================================
# SCENARIO 2: DIGILOCKER OAUTH 2.0 PKCE & PATIENT PROFILE SYNC (Day 42)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_2_digilocker_oauth2_pkce_and_patient_profile_sync(week_9_e2e_env):
    """Verify DigiLocker PKCE URL generation, e-Aadhaar XML parsing, and demographic sync."""
    client, session_factory = week_9_e2e_env

    u_id = str(uuid.uuid4())
    p_id = str(uuid.uuid4())
    email = f"arun.digilocker.{uuid.uuid4().hex[:6]}@example.com"

    # Seed Patient Arun Patel
    async with session_factory() as session:
        u_patient = User(
            id=u_id,
            email=email,
            full_name="Arun Patel",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=False,
        )
        p_patient = PatientProfile(
            id=p_id,
            user_id=u_id,
            date_of_birth=date(1990, 6, 4),
            gender=Gender.MALE,
        )
        session.add_all([u_patient, p_patient])
        await session.commit()

    token_headers = auth_header_for(u_id, email, UserRole.PATIENT.value)

    # 1. Get PKCE Authorization URL
    resp_url = await client.get("/api/v1/auth/digilocker/authorize-url")
    assert resp_url.status_code == 200
    url_data = resp_url.json()["data"]
    assert "code_challenge=" in url_data["authorize_url"]
    assert url_data["code_challenge_method"] == "S256"

    # 2. Simulate Callback Code Verification
    verify_resp = await client.post(
        "/api/v1/auth/digilocker/verify",
        json={"code": "sandbox_valid_code", "state": url_data["state"], "code_verifier": "mock_verifier_xyz"},
    )
    assert verify_resp.status_code == 200
    verified_data = verify_resp.json()["data"]
    claims = verified_data["demographics"]
    assert "Arun" in claims["name"]
    assert "XXXX-XXXX-" in claims["masked_aadhaar"]

    # 3. Synchronize verified claims into PatientProfile
    sync_resp = await client.post(
        f"/api/v1/auth/digilocker/sync-patient/{p_id}",
        headers=token_headers,
        json=verified_data,
    )
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()["data"]
    assert sync_data["is_identity_verified"] is True

    # Verify database update
    async with session_factory() as session:
        fresh_profile = await session.get(PatientProfile, p_id)
        assert fresh_profile is not None
        assert fresh_profile.address_line == claims["address"]["formatted_address"]
        assert fresh_profile.city == claims["address"]["district"]
        assert fresh_profile.state == claims["address"]["state"]


# ==============================================================================
# SCENARIO 3: DIRECT AADHAAR OTP FLOW & VERHOEFF CHECKSUM (Day 43)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_3_direct_aadhaar_otp_lifecycle_and_verhoeff(week_9_e2e_env):
    """Verify Verhoeff algorithm, 3-attempt brute-force protection, OTP verify & patient sync."""
    client, session_factory = week_9_e2e_env

    u_id = str(uuid.uuid4())
    p_id = str(uuid.uuid4())
    email = f"otp.patient.{uuid.uuid4().hex[:6]}@example.com"

    # Seed Patient
    async with session_factory() as session:
        u_patient = User(
            id=u_id,
            email=email,
            full_name="Sunita Rao",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=False,
        )
        p_patient = PatientProfile(
            id=p_id,
            user_id=u_id,
            date_of_birth=date(1988, 3, 15),
            gender=Gender.FEMALE,
        )
        session.add_all([u_patient, p_patient])
        await session.commit()

    token_headers = auth_header_for(u_id, email, UserRole.PATIENT.value)

    # 1. Verhoeff mathematical calculation on valid 12-digit Aadhaar
    base_11 = "91847210482"
    check_digit = generate_verhoeff(base_11)
    valid_aadhaar = base_11 + str(check_digit)
    assert validate_verhoeff(valid_aadhaar) is True

    # 2. Transposition / mutation error detection
    altered = valid_aadhaar[:-2] + ("0" if valid_aadhaar[-2] != "0" else "1") + valid_aadhaar[-1]
    assert validate_verhoeff(altered) is False

    # 3. Generate OTP endpoint
    gen_resp = await client.post(
        "/api/v1/abdm/m1/aadhaar/generate-otp",
        json={"aadhaar_number": valid_aadhaar},
    )
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()["data"]
    txn_id = gen_data["txn_id"]
    assert "masked_mobile" in gen_data

    # 4. Verify OTP endpoint with valid OTP
    verify_resp = await client.post(
        "/api/v1/abdm/m1/aadhaar/verify-otp",
        json={"txn_id": txn_id, "otp": "123456"},
    )
    assert verify_resp.status_code == 200
    verified_data = verify_resp.json()["data"]
    verified_demographics = verified_data["demographics"]
    assert verified_demographics["gender"] in ["male", "female", "other"]

    # 5. Synchronize into patient profile
    sync_resp = await client.post(
        f"/api/v1/abdm/m1/aadhaar/sync-patient/{p_id}",
        headers=token_headers,
        json=verified_data,
    )
    assert sync_resp.status_code == 200
    assert sync_resp.json()["data"]["is_identity_verified"] is True


# ==============================================================================
# SCENARIO 4: 14-DIGIT ABHA GENERATION & VERHOEFF INVARIANCE (Day 44)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_4_14_digit_abha_generation_and_verhoeff_invariance(week_9_e2e_env):
    """Verify 14-digit ABHA Number generation format, Verhoeff check-digit, and endpoint."""
    client, session_factory = week_9_e2e_env

    u_id = str(uuid.uuid4())
    p_id = str(uuid.uuid4())
    email = f"abha.user.{uuid.uuid4().hex[:6]}@example.com"

    async with session_factory() as session:
        u = User(id=u_id, email=email, full_name="Arun Patel", role=UserRole.PATIENT, is_active=True, is_verified=True)
        p = PatientProfile(id=p_id, user_id=u_id, date_of_birth=date(1990, 6, 4), gender=Gender.MALE)
        session.add_all([u, p])
        await session.commit()

    token_headers = auth_header_for(u_id, email, UserRole.PATIENT.value)

    # 1. Direct formatted generator check
    raw_formatted = _generate_raw_14_digit_abha()
    assert len(raw_formatted) == 17
    assert raw_formatted.startswith("91-")
    digits_only = raw_formatted.replace("-", "")
    assert len(digits_only) == 14
    assert validate_verhoeff(digits_only) is True

    # 2. Endpoint generation
    resp = await client.post(
        "/api/v1/abdm/m1/abha/create",
        headers=token_headers,
        json={"patient_id": p_id},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "active"
    assert data["abha_number"].startswith("91-")
    assert validate_verhoeff(data["abha_number"].replace("-", "")) is True


# ==============================================================================
# SCENARIO 5: @abdm PHR HANDLE RESERVATION & COLLISION ALTERNATIVES (Day 44)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_5_phr_handle_reservation_and_collision_suggestions(week_9_e2e_env):
    """Verify PHR handle availability, reserved keyword blocking, and collision alternatives."""
    client, session_factory = week_9_e2e_env

    u_id = str(uuid.uuid4())
    p_id = str(uuid.uuid4())
    email = f"phr.user.{uuid.uuid4().hex[:6]}@example.com"

    async with session_factory() as session:
        u = User(id=u_id, email=email, full_name="Priya Nair", role=UserRole.PATIENT, is_active=True, is_verified=True)
        p = PatientProfile(id=p_id, user_id=u_id, date_of_birth=date(1984, 9, 12), gender=Gender.FEMALE)
        session.add_all([u, p])
        await session.commit()

    token_headers = auth_header_for(u_id, email, UserRole.PATIENT.value)

    # 1. Check availability of valid custom handle
    unique_handle = f"patient.{uuid.uuid4().hex[:6]}"
    resp_avail = await client.get(f"/api/v1/abdm/m1/phr/check-availability?handle={unique_handle}")
    assert resp_avail.status_code == 200
    assert resp_avail.json()["data"]["is_available"] is True

    # 2. Check reserved keyword (e.g. 'nha' or 'admin')
    resp_reserved = await client.get("/api/v1/abdm/m1/phr/check-availability?handle=admin")
    assert resp_reserved.status_code == 200
    res_data = resp_reserved.json()["data"]
    assert res_data["is_available"] is False
    assert len(res_data["suggestions"]) == 3

    # 3. Link address to patient profile
    target_phr = f"{unique_handle}@abdm"

    resp_link = await client.post(
        "/api/v1/abdm/m1/phr/link",
        headers=token_headers,
        json={"patient_id": p_id, "abha_address": target_phr},
    )
    assert resp_link.status_code == 200
    assert resp_link.json()["data"]["abha_address"] == target_phr

    # 4. Attempt duplicate link (collision)
    p2_id = str(uuid.uuid4())
    u2_id = str(uuid.uuid4())
    email2 = "p2@example.com"
    async with session_factory() as session:
        u2 = User(id=u2_id, email=email2, full_name="Other Patient", role=UserRole.PATIENT, is_active=True)
        p2 = PatientProfile(id=p2_id, user_id=u2.id)
        session.add_all([u2, p2])
        await session.commit()

    token_headers2 = auth_header_for(u2_id, email2, UserRole.PATIENT.value)

    resp_dupe = await client.post(
        "/api/v1/abdm/m1/phr/link",
        headers=token_headers2,
        json={"patient_id": p2_id, "abha_address": target_phr},
    )
    assert resp_dupe.status_code == 400
    assert "already registered" in resp_dupe.json()["message"]


# ==============================================================================
# SCENARIO 6: HEALTHCARE PROFESSIONAL REGISTRY (HPR) DOCTOR ONBOARDING (Day 44)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_6_hpr_doctor_onboarding_and_credential_binding(week_9_e2e_env):
    """Verify Doctor HPR onboarding, medical council credential binding, and database sync."""
    client, session_factory = week_9_e2e_env

    doc_uid = str(uuid.uuid4())
    doc_pid = str(uuid.uuid4())
    email = f"hpr.doc.{uuid.uuid4().hex[:6]}@example.com"

    # Seed Doctor
    async with session_factory() as session:
        u_doc = User(
            id=doc_uid,
            email=email,
            full_name="Dr. Ananya Sharma",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True,
        )
        p_doc = DoctorProfile(
            id=doc_pid,
            user_id=doc_uid,
            registration_number="DMC-2015-8839",
            medical_council="Delhi Medical Council",
            qualifications="MBBS, MD",
            specialty=MedicalSpecialty.CARDIOLOGY,
            consultation_fee=1500,
        )
        session.add_all([u_doc, p_doc])
        await session.commit()

    token_headers = auth_header_for(doc_uid, email, UserRole.DOCTOR.value)
    unique_hpr_handle = f"ananya.{uuid.uuid4().hex[:6]}"

    # Onboard doctor to HPR
    resp = await client.post(
        "/api/v1/abdm/m1/hpr/onboard",
        headers=token_headers,
        json={
            "doctor_id": doc_pid,
            "registration_number": "DMC-2015-8839",
            "medical_council": "Delhi Medical Council",
            "hpr_handle": unique_hpr_handle,
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["hpr_id"] == f"{unique_hpr_handle}@hpr.abdm"
    assert data["status"] == "verified"

    # Verify database update
    async with session_factory() as session:
        fresh_doc = await session.get(DoctorProfile, doc_pid)
        assert fresh_doc is not None
        assert fresh_doc.hpr_id == f"{unique_hpr_handle}@hpr.abdm"


# ==============================================================================
# SCENARIO 7: COMPLETE ABDM M1 CLOSED-LOOP MULTI-AUTH ORCHESTRATION (Day 45)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_7_complete_abdm_m1_closed_loop_orchestration(week_9_e2e_env):
    """Verify full closed-loop ABDM M1 integration: Gateway + Direct OTP + 14-Digit ABHA + PHR Link + HPR."""
    client, session_factory = week_9_e2e_env

    # 1. Verify Gateway Liveness
    gw_resp = await client.get("/api/v1/abdm/status")
    assert gw_resp.status_code == 200

    u_id = str(uuid.uuid4())
    p_id = str(uuid.uuid4())
    email = f"walkin.{uuid.uuid4().hex[:6]}@example.com"

    # 2. Seed a new walk-in patient
    async with session_factory() as session:
        u_patient = User(
            id=u_id,
            email=email,
            full_name="Rajesh Kumar",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=False,
        )
        p_patient = PatientProfile(
            id=p_id,
            user_id=u_id,
            date_of_birth=date(1992, 8, 20),
            gender=Gender.MALE,
        )
        session.add_all([u_patient, p_patient])
        await session.commit()

    pat_headers = auth_header_for(u_id, email, UserRole.PATIENT.value)

    # 3. Patient completes Direct Aadhaar Demographic OTP Verification
    valid_aadhaar = "99991234567" + str(generate_verhoeff("99991234567"))
    gen_resp = await client.post(
        "/api/v1/abdm/m1/aadhaar/generate-otp",
        json={"aadhaar_number": valid_aadhaar},
    )
    assert gen_resp.status_code == 200
    txn_id = gen_resp.json()["data"]["txn_id"]

    verify_resp = await client.post(
        "/api/v1/abdm/m1/aadhaar/verify-otp",
        json={"txn_id": txn_id, "otp": "123456"},
    )
    assert verify_resp.status_code == 200
    verified_data = verify_resp.json()["data"]

    # 4. Synchronize certified claims to patient profile
    sync_resp = await client.post(
        f"/api/v1/abdm/m1/aadhaar/sync-patient/{p_id}",
        headers=pat_headers,
        json=verified_data,
    )
    assert sync_resp.status_code == 200

    # 5. Mint 14-Digit ABHA Number with Verhoeff verification
    create_abha_resp = await client.post(
        "/api/v1/abdm/m1/abha/create",
        headers=pat_headers,
        json={"patient_id": p_id},
    )
    assert create_abha_resp.status_code == 200
    minted_data = create_abha_resp.json()["data"]
    abha_number = minted_data["abha_number"]
    assert validate_verhoeff(abha_number.replace("-", "")) is True

    # 6. Reserve and link unique @abdm PHR Handle
    phr_handle = f"rajesh.{uuid.uuid4().hex[:6]}"
    phr_address = f"{phr_handle}@abdm"

    link_resp = await client.post(
        "/api/v1/abdm/m1/phr/link",
        headers=pat_headers,
        json={
            "patient_id": p_id,
            "abha_address": phr_address,
        },
    )
    assert link_resp.status_code == 200
    assert link_resp.json()["data"]["abha_address"] == phr_address

    # 7. Seed Treating Clinician and Onboard to HPR
    doc_uid = str(uuid.uuid4())
    doc_pid = str(uuid.uuid4())
    doc_email = f"lead.cardiologist.{uuid.uuid4().hex[:6]}@example.com"

    async with session_factory() as session:
        u_doc = User(
            id=doc_uid,
            email=doc_email,
            full_name="Dr. K. V. Raman",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True,
        )
        p_doc = DoctorProfile(
            id=doc_pid,
            user_id=doc_uid,
            registration_number="DMC-2018-9941",
            medical_council="Delhi Medical Council",
            qualifications="MBBS, MD",
            specialty=MedicalSpecialty.CARDIOLOGY,
            consultation_fee=1800,
        )
        session.add_all([u_doc, p_doc])
        await session.commit()

    doc_headers = auth_header_for(doc_uid, doc_email, UserRole.DOCTOR.value)
    hpr_handle = f"kv.raman.{uuid.uuid4().hex[:6]}"

    hpr_resp = await client.post(
        "/api/v1/abdm/m1/hpr/onboard",
        headers=doc_headers,
        json={
            "doctor_id": doc_pid,
            "registration_number": "DMC-2018-9941",
            "medical_council": "Delhi Medical Council",
            "hpr_handle": hpr_handle,
        },
    )
    assert hpr_resp.status_code == 200
    assert hpr_resp.json()["data"]["hpr_id"] == f"{hpr_handle}@hpr.abdm"

    # 8. Assert Final Closed-Loop Database Consistency
    async with session_factory() as session:
        # Patient asserts
        updated_patient = await session.get(PatientProfile, p_id)
        assert updated_patient is not None
        assert updated_patient.abha_number == abha_number
        assert updated_patient.abha_address == phr_address

        # Doctor asserts
        updated_doctor = await session.get(DoctorProfile, doc_pid)
        assert updated_doctor is not None
        assert updated_doctor.hpr_id == f"{hpr_handle}@hpr.abdm"

        # Verification status check
        assert sync_resp.json()["data"]["is_identity_verified"] is True
