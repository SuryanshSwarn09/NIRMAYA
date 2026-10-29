"""Week 10 End-to-End Closed-Loop ABDM Milestone 2 (M2) Verification Test Suite.

Validates the complete ABDM Milestone 2 HIP architecture engineered across Week 10:
1. Unified Passwordless Patient Gateway & 30-Day Session Longevity (Day 46)
2. Health Information Provider (HIP) Bridge Webhook Ingest & Replay Defense (Day 47)
3. Multi-Tier Patient Discovery, Fuzzy Matcher & Ambiguity Protection (Day 48)
4. Care Context Linkage Protocol, OTP Challenge & Attempt Guardrails (Day 49)
5. Comprehensive M2 Interoperability Audit & Compliance Certification (Day 50)
"""

from datetime import date, datetime, timedelta, timezone
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.doctor import DoctorProfile
from app.models.enums import (
    AppointmentStatus,
    AppointmentType,
    BloodGroup,
    Gender,
    MedicalSpecialty,
    ServiceRequestStatus,
    UserRole,
)
from app.models.appointment import Appointment
from app.models.diagnostic import DiagnosticOrder
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.abdm_m2_bridge import (
    CareContextRepresentation,
    GatewayAuthInitQuery,
    GatewayAuthInitRequest,
    GatewayCareContextRef,
    GatewayLinkConfirmConfirmation,
    GatewayLinkConfirmRequest,
    GatewayLinkInitRequest,
    GatewayLinkPatient,
    GatewayPatientDiscoveryRequest,
    PatientDiscoveryQuery,
)
from app.services.abdm_discovery import (
    calculate_name_similarity,
    remove_honorifics,
)
from app.services.abdm_hip_bridge import (
    generate_m2_audit_report,
    get_bridge_status,
    validate_gateway_headers,
    webhook_audit_store,
)
from app.services.abdm_linkage import (
    confirm_care_context_linking,
    link_session_manager,
    mask_phone_number,
)


@pytest_asyncio.fixture
async def week_10_e2e_env():
    """Isolated in-memory SQLite database environment for Week 10 M2 E2E testing."""
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

    # Seed primary test patient Arun Patel & doctor Dr. Ananya
    async with session_factory() as session:
        # Seed Doctor
        doc_user = User(
            id=str(uuid.uuid4()),
            email="dr.ananya@nirmaya.local",
            full_name="Dr. Ananya Sharma",
            phone_number="+919876543200",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True,
        )
        session.add(doc_user)
        await session.flush()

        doc_profile = DoctorProfile(
            id=str(uuid.uuid4()),
            user_id=doc_user.id,
            registration_number="MCI-12345",
            medical_council="National Medical Commission",
            qualifications="MBBS, MD",
            specialty=MedicalSpecialty.CARDIOLOGY,
            consultation_fee=500.0,
            experience_years=8,
        )
        session.add(doc_profile)
        await session.flush()

        # Seed Patient Arun Patel
        user = User(
            id=str(uuid.uuid4()),
            email="arun.patel@nirmaya.local",
            full_name="Arun Patel",
            phone_number="+919876543210",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.flush()

        profile = PatientProfile(
            id=str(uuid.uuid4()),
            user_id=user.id,
            date_of_birth=date(1985, 4, 12),
            gender=Gender.MALE,
            blood_group=BloodGroup.O_POSITIVE,
            abha_number="91-1029-3847-5610",
            abha_address="arun.patel@abdm",
        )
        session.add(profile)
        await session.flush()

        # Seed clinical encounter
        appt = Appointment(
            patient_id=profile.id,
            doctor_id=doc_profile.id,
            appointment_type=AppointmentType.ROUTINE_CHECKUP,
            status=AppointmentStatus.COMPLETED,
            scheduled_start=datetime.now(timezone.utc),
            scheduled_end=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        session.add(appt)

        # Seed diagnostic laboratory order
        diag_order = DiagnosticOrder(
            patient_id=profile.id,
            code_coding_system="http://loinc.org",
            code_value="24331-1",
            code_display="Lipid Panel Profile",
            status=ServiceRequestStatus.COMPLETED,
        )
        session.add(diag_order)
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, session_factory

    app.dependency_overrides.clear()
    await engine.dispose()


# ==============================================================================
# SCENARIO 1: GATEWAY WEBHOOK INGEST & REPLAY DEFENSE (Day 47)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_1_webhook_ingest_and_replay_defense(week_10_e2e_env):
    """Verify inbound ABDM Gateway webhook validation, replay defense, and 202 Accepted ingest."""
    client, _ = week_10_e2e_env

    req_id = str(uuid.uuid4())
    now_utc_str = datetime.now(timezone.utc).isoformat()
    headers = {
        "REQUEST-ID": req_id,
        "TIMESTAMP": now_utc_str,
        "X-CM-ID": "sbx",
    }
    payload = {
        "requestId": req_id,
        "timestamp": now_utc_str,
        "query": {
            "id": "arun.patel@abdm",
            "purpose": "LINK",
            "authMode": "DIRECT_OTP",
            "requester": {"type": "HIP", "id": "IN0410000123"},
        },
    }

    # 1. Valid webhook ingest -> Synchronous 202 Accepted (No body required per ABDM spec)
    resp = await client.post("/v0.5/users/auth/init", json=payload, headers=headers)
    assert resp.status_code == 202

    # 2. Clock drift violation (>300 seconds stale) -> Rejected HTTP 400
    stale_time_str = (datetime.now(timezone.utc) - timedelta(seconds=360)).isoformat()
    bad_headers = {
        "REQUEST-ID": str(uuid.uuid4()),
        "TIMESTAMP": stale_time_str,
    }
    resp_stale = await client.post("/v0.5/users/auth/init", json=payload, headers=bad_headers)
    assert resp_stale.status_code == 400
    assert "timestamp drift" in resp_stale.json()["message"].lower()

    # 3. Invalid UUID header -> Rejected HTTP 400
    invalid_uuid_headers = {
        "REQUEST-ID": "not-a-valid-uuid",
        "TIMESTAMP": now_utc_str,
    }
    resp_bad_uuid = await client.post(
        "/v0.5/users/auth/init", json=payload, headers=invalid_uuid_headers
    )
    assert resp_bad_uuid.status_code == 400
    assert "not a valid uuid" in resp_bad_uuid.json()["message"].lower()


# ==============================================================================
# SCENARIO 2: MULTI-TIER PATIENT DISCOVERY & AMBIGUITY DEFENSE (Day 48)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_2_patient_discovery_and_ambiguity_defense(week_10_e2e_env):
    """Verify multi-tier patient discovery, fuzzy matching, and ambiguity protection filter."""
    client, _ = week_10_e2e_env

    # 1. Deterministic match on exact ABHA address via simulation endpoint
    sim_resp = await client.post(
        "/api/v1/abdm/m2/bridge/discovery/simulate",
        json={
            "abha_address": "arun.patel@abdm",
            "full_name": "Arun Patel",
            "gender": "M",
            "year_of_birth": 1985,
            "match_threshold": 0.75,
        },
    )
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()["data"]
    assert sim_data["matched"] is True
    assert sim_data["confidence_score"] >= 0.75
    assert len(sim_data["care_contexts"]) >= 1

    # 2. Token-set name similarity with honorific stripping
    cleaned_name = remove_honorifics("shri dr arun kumar patel")
    assert "shri" not in cleaned_name
    assert "dr" not in cleaned_name
    sim_score = calculate_name_similarity("Arun Patel", "Patel Arun")
    assert sim_score >= 0.90

    # 3. Inbound Gateway Discovery Webhook: POST /v0.5/care-contexts/discover
    req_id = str(uuid.uuid4())
    headers = {
        "REQUEST-ID": req_id,
        "TIMESTAMP": datetime.now(timezone.utc).isoformat(),
        "X-CM-ID": "sbx",
    }
    disc_payload = {
        "requestId": req_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hipId": "IN0410000123",
        "patient": {
            "id": "arun.patel@abdm",
            "name": "Arun Patel",
            "gender": "M",
            "yearOfBirth": 1985,
            "verifiedIdentifiers": [
                {"type": "MOBILE", "value": "+919876543210"}
            ],
            "unverifiedIdentifiers": [],
        },
    }
    resp_disc = await client.post(
        "/v0.5/care-contexts/discover", json=disc_payload, headers=headers
    )
    assert resp_disc.status_code == 202


# ==============================================================================
# SCENARIO 3: CARE CONTEXT LINK INITIATION & OTP CHALLENGE (Day 49)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_3_care_context_link_init_and_challenge(week_10_e2e_env):
    """Verify care context link initiation, phone privacy masking, and OTP challenge issuance."""
    client, _ = week_10_e2e_env

    # 1. Privacy phone masking verification
    masked = mask_phone_number("+919876543210")
    assert masked == "+91 ******3210"

    # 2. Inbound Gateway Link Init Webhook: POST /v0.5/links/link/init
    req_id = str(uuid.uuid4())
    headers = {
        "REQUEST-ID": req_id,
        "TIMESTAMP": datetime.now(timezone.utc).isoformat(),
        "X-CM-ID": "sbx",
    }
    link_init_payload = {
        "requestId": req_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "transactionId": str(uuid.uuid4()),
        "patient": {
            "id": "arun.patel@abdm",
            "careContexts": [
                {
                    "referenceNumber": "OPD-ENCOUNTER-101",
                    "display": "General Medicine Consultation",
                },
                {
                    "referenceNumber": "LAB-ORDER-501",
                    "display": "Complete Blood Count & Lipid Panel",
                },
            ],
        },
    }
    resp_init = await client.post(
        "/v0.5/links/link/init", json=link_init_payload, headers=headers
    )
    assert resp_init.status_code == 202

    # 3. Interactive Link Init Simulation Endpoint
    sim_resp = await client.post(
        "/api/v1/abdm/m2/bridge/link/init/simulate",
        json={
            "patient_identifier": "arun.patel@abdm",
            "care_context_references": ["OPD-ENCOUNTER-101"],
        },
    )
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()["data"]
    assert sim_data["success"] is True
    assert sim_data["link_ref_number"] is not None
    assert sim_data["communication_hint"] == "+91 ******3210"
    assert sim_data["otp_sandbox_hint"] is not None


# ==============================================================================
# SCENARIO 4: OTP VERIFICATION, ATTEMPT GUARDRAILS & CONFIRMATION (Day 49)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_4_otp_attempt_guardrails_and_confirmation(week_10_e2e_env):
    """Verify OTP verification attempt counter decrement, brute-force defense, and permanent record linkage."""
    client, _ = week_10_e2e_env

    # 1. Initiate linking session via link_session_manager
    session = link_session_manager.create_session(
        transaction_id=str(uuid.uuid4()),
        patient_profile_id="prof-cardio-01",
        patient_name="Priya Sharma",
        patient_id="priya.sharma@abdm",
        patient_phone="+919876543210",
        care_contexts=[CareContextRepresentation(referenceNumber="OPD-201", display="Cardiology Follow-up")],
        otp="123456",
        ttl_minutes=10,
    )
    link_ref = session.link_ref_number

    # 2. Attempt 1: Invalid OTP -> Decrements attempts remaining from 3 to 2
    wrong_req = GatewayLinkConfirmRequest(
        requestId=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        confirmation=GatewayLinkConfirmConfirmation(
            linkRefNumber=link_ref,
            token="000000",
        ),
    )
    valid_wrong, s_wrong, err_wrong = await confirm_care_context_linking(wrong_req)
    assert valid_wrong is False
    assert s_wrong.attempts_left == 2

    # 3. Attempt 2: Valid OTP -> Session transitions to CONFIRMED
    good_req = GatewayLinkConfirmRequest(
        requestId=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        confirmation=GatewayLinkConfirmConfirmation(
            linkRefNumber=link_ref,
            token="123456",
        ),
    )
    valid_good, s_good, err_good = await confirm_care_context_linking(good_req)
    assert valid_good is True
    assert s_good.status == "CONFIRMED"
    assert len(s_good.care_contexts) == 1

    # 4. Inbound Gateway Link Confirm Webhook: POST /v0.5/links/link/confirm
    new_session = link_session_manager.create_session(
        transaction_id=str(uuid.uuid4()),
        patient_profile_id="prof-lab-02",
        patient_name="Rahul Verma",
        patient_id="rahul.verma@abdm",
        patient_phone="+919876543210",
        care_contexts=[CareContextRepresentation(referenceNumber="LAB-301", display="Biochemistry Panel")],
        otp="654321",
        ttl_minutes=10,
    )

    req_id = str(uuid.uuid4())
    headers = {
        "REQUEST-ID": req_id,
        "TIMESTAMP": datetime.now(timezone.utc).isoformat(),
        "X-CM-ID": "sbx",
    }
    confirm_payload = {
        "requestId": req_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confirmation": {
            "linkRefNumber": new_session.link_ref_number,
            "token": "654321",
        },
    }
    resp_conf = await client.post(
        "/v0.5/links/link/confirm", json=confirm_payload, headers=headers
    )
    assert resp_conf.status_code == 202


# ==============================================================================
# SCENARIO 5: 3-STRIKES BRUTE-FORCE LOCKOUT & EXPIRY DEFENSE (Day 49)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_5_lockouts_and_expiry_defense():
    """Verify 3-strikes brute-force lockout and TTL expiration defense."""
    # 1. 3-Strikes lockout
    session = link_session_manager.create_session(
        transaction_id=str(uuid.uuid4()),
        patient_profile_id="prof-lockout-01",
        patient_name="Arun Patel",
        patient_id="arun.patel@abdm",
        patient_phone="+919876543210",
        care_contexts=[CareContextRepresentation(referenceNumber="OPD-101", display="Consultation")],
        otp="999888",
        ttl_minutes=10,
    )
    ref = session.link_ref_number

    # Strike 1
    v1, s1, e1 = link_session_manager.verify_otp(ref, "111111")
    assert v1 is False
    assert s1.attempts_left == 2

    # Strike 2
    v2, s2, e2 = link_session_manager.verify_otp(ref, "222222")
    assert v2 is False
    assert s2.attempts_left == 1

    # Strike 3 (Final attempt fails)
    v3, s3, e3 = link_session_manager.verify_otp(ref, "333333")
    assert v3 is False
    assert s3.attempts_left == 0
    assert s3.status == "FAILED"

    # Attempt 4 after lockout -> Completely rejected
    v4, s4, e4 = link_session_manager.verify_otp(ref, "999888")
    assert v4 is False
    assert "attempt" in e4.lower() or "lock" in e4.lower() or "failed" in e4.lower()

    # 2. TTL Expiry defense
    exp_session = link_session_manager.create_session(
        transaction_id=str(uuid.uuid4()),
        patient_profile_id="prof-exp-01",
        patient_name="Arun Patel",
        patient_id="arun.patel@abdm",
        patient_phone="+919876543210",
        care_contexts=[CareContextRepresentation(referenceNumber="OPD-101", display="Consultation")],
        otp="123987",
        ttl_minutes=10,
    )
    exp_session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)

    v_exp, s_exp, e_exp = link_session_manager.verify_otp(exp_session.link_ref_number, "123987")
    assert v_exp is False
    assert "expired" in e_exp.lower()


# ==============================================================================
# SCENARIO 6: ABDM M2 AUDIT & CERTIFICATION REPORT (Day 50)
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_scenario_6_abdm_m2_audit_and_certification(week_10_e2e_env):
    """Verify system-wide ABDM Milestone 2 compliance audit metrics and certification status."""
    client, _ = week_10_e2e_env

    # 1. Query the live audit endpoint
    resp = await client.get("/api/v1/abdm/m2/bridge/audit")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True

    audit = body["data"]
    assert audit["hip_id"] == "IN0410000123"
    assert audit["facility_name"] == "NIRMAYA Apex Hospital & Research Institute"
    assert audit["compliance_status"] == "ABDM_M2_CERTIFIED"
    assert audit["certified_milestone"] == "M2: Patient Discovery & Care Context Linkage"
    assert audit["active_listeners_count"] >= 9
    assert "/v0.5/users/auth/init" in audit["active_listeners"]
    assert "/v0.5/care-contexts/discover" in audit["active_listeners"]
    assert "/v0.5/links/link/init" in audit["active_listeners"]
    assert "/v0.5/links/link/confirm" in audit["active_listeners"]
    assert audit["timestamp_clock_drift_guard"] == "Enforced (+/-300s ISO 8601 drift limit)"

    # 2. Verify direct service generation
    direct_report = generate_m2_audit_report()
    assert direct_report.compliance_status == "ABDM_M2_CERTIFIED"
    assert direct_report.hip_id == "IN0410000123"
