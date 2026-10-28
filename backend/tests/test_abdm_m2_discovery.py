"""Tests for ABDM Milestone 2 (M2) Patient Discovery Protocol & Fuzzy Demographic Matcher.

Verifies:
- Text normalization, honorific stripping, Levenshtein edit distance, token overlap
- Demographic scoring (Name similarity, YOB tolerance, Gender alignment)
- Deterministic ABHA Number / Address match
- Mobile-anchored demographic verification
- Pure fuzzy demographic tolerance
- Ambiguity protection against multi-patient collision
- Care Context generation from clinical encounters and orders
- Synchronous HTTP 202 Accepted Gateway ingest endpoint
- Interactive discovery simulation endpoint
"""

from datetime import date, datetime, timedelta, timezone
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.appointment import Appointment
from app.models.diagnostic import DiagnosticOrder
from app.models.doctor import DoctorProfile
from app.models.enums import AppointmentStatus, AppointmentType, BloodGroup, Gender, MedicalSpecialty, ServiceRequestStatus, UserRole
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.abdm_m2_bridge import (
    GatewayPatientDiscoveryRequest,
    PatientDiscoveryQuery,
    PatientDiscoverySimulateRequest,
    PatientIdentifier,
)
from app.services.abdm_discovery import (
    calculate_gender_similarity,
    calculate_name_similarity,
    calculate_yob_similarity,
    discover_patient,
    evaluate_candidate_match,
    levenshtein_distance,
    levenshtein_ratio,
    remove_honorifics,
    resolve_patient_care_contexts,
    simulate_patient_discovery,
)
from app.services.abdm_hip_bridge import webhook_audit_store


# ----------------------------------------------------------------------------
# Test Environment Fixture with In-Memory SQLite
# ----------------------------------------------------------------------------


@pytest_asyncio.fixture
async def discovery_test_env():
    """Isolated in-memory SQLite database environment for discovery tests."""
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


# ----------------------------------------------------------------------------
# 1. Unit Tests: Pure Text, Distance & Demographic Math
# ----------------------------------------------------------------------------


def test_levenshtein_distance_and_ratio():
    assert levenshtein_distance("kitten", "sitting") == 3
    assert levenshtein_distance("", "test") == 4
    assert levenshtein_distance("same", "same") == 0

    assert levenshtein_ratio("Arun", "Arun") == 1.0
    assert levenshtein_ratio("Arun", "Aron") == 0.75
    assert levenshtein_ratio("", "") == 1.0


def test_honorific_stripping():
    assert remove_honorifics("dr arun patel") == "arun patel"
    assert remove_honorifics("shri arun kumar patel") == "arun patel"
    assert remove_honorifics("mrs priya sharma") == "priya sharma"


def test_calculate_name_similarity():
    # Exact match
    assert calculate_name_similarity("Arun Patel", "Arun Patel") == 1.0

    # Inverted order
    assert calculate_name_similarity("Patel Arun", "Arun Patel") == 1.0

    # Case & honorific insensitivity
    assert calculate_name_similarity("Dr. Arun Patel", "arun patel") == 1.0

    # Typo tolerance
    assert calculate_name_similarity("Aron Patel", "Arun Patel") >= 0.75

    # Middle name inclusion
    assert calculate_name_similarity("Arun Kumar Patel", "Arun Patel") >= 0.85

    # Completely different names
    assert calculate_name_similarity("Priya Sharma", "Arun Patel") < 0.30


def test_calculate_yob_and_gender_similarity():
    # YOB
    assert calculate_yob_similarity(1985, 1985) == 1.0
    assert calculate_yob_similarity(1985, 1986) == 0.85
    assert calculate_yob_similarity(1985, 1987) == 0.50
    assert calculate_yob_similarity(1985, 2000) == 0.0
    assert calculate_yob_similarity(1985, None) == 0.5

    # Gender
    assert calculate_gender_similarity(Gender.MALE, "M") == 1.0
    assert calculate_gender_similarity(Gender.MALE, "MALE") == 1.0
    assert calculate_gender_similarity(Gender.FEMALE, "F") == 1.0
    assert calculate_gender_similarity(Gender.MALE, "FEMALE") == 0.0
    assert calculate_gender_similarity(None, "M") == 0.5


# ----------------------------------------------------------------------------
# 2. Candidate Demographic Matcher Tests
# ----------------------------------------------------------------------------


def test_candidate_match_deterministic_abha():
    user = User(
        id=str(uuid.uuid4()),
        full_name="Arun Patel",
        phone_number="+919876543210",
    )
    profile = PatientProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
        date_of_birth=date(1985, 4, 12),
        gender=Gender.MALE,
        abha_number="91-1029-3847-5610",
        abha_address="arun.patel@abdm",
    )

    # Match by ABHA Number
    q1 = PatientDiscoveryQuery(
        id="different@abdm",
        verifiedIdentifiers=[
            PatientIdentifier(type="NDHM_HEALTH_NUMBER", value="91102938475610")
        ],
    )
    score1, breakdown1, matched1 = evaluate_candidate_match(user, profile, q1)
    assert score1 == 1.0
    assert "NDHM_HEALTH_NUMBER" in matched1

    # Match by ABHA Address
    q2 = PatientDiscoveryQuery(
        id="arun.patel@abdm",
        verifiedIdentifiers=[],
    )
    score2, breakdown2, matched2 = evaluate_candidate_match(user, profile, q2)
    assert score2 == 1.0
    assert "ABHA_ADDRESS" in matched2


def test_candidate_match_mobile_and_fuzzy_name():
    user = User(
        id=str(uuid.uuid4()),
        full_name="Arun Patel",
        phone_number="+919876543210",
    )
    profile = PatientProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
        date_of_birth=date(1985, 4, 12),
        gender=Gender.MALE,
        abha_number="91-1029-3847-5610",
        abha_address="arun.patel@abdm",
    )

    # Verified mobile + slight name typo "Aron Patel"
    query = PatientDiscoveryQuery(
        id="random@abdm",
        name="Aron Patel",
        gender="M",
        yearOfBirth=1985,
        verifiedIdentifiers=[
            PatientIdentifier(type="MOBILE", value="+919876543210")
        ],
    )
    score, breakdown, matched = evaluate_candidate_match(user, profile, query)
    assert score >= 0.90
    assert "MOBILE" in matched
    assert "NAME" in matched
    assert "YOB" in matched
    assert "GENDER" in matched
    assert breakdown.match_status == "CONFIRMED"


# ----------------------------------------------------------------------------
# 3. Integration Tests with Database & Care Contexts
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_discover_patient_with_care_contexts(discovery_test_env):
    _, session_factory = discovery_test_env

    async with session_factory() as session:
        # Discover using ABHA address
        query = PatientDiscoveryQuery(
            id="arun.patel@abdm",
            name="Arun Patel",
            gender="M",
            yearOfBirth=1985,
        )

        matched, matched_prof, breakdown, care_contexts, err = await discover_patient(
            session=session,
            query=query,
        )

        assert matched is True
        assert matched_prof is not None
        assert breakdown is not None
        assert breakdown.composite_score >= 0.75
        assert len(care_contexts) >= 2

        # Verify care context formatting
        refs = [cc.referenceNumber for cc in care_contexts]
        assert any(ref.startswith("OPD-ENC-") for ref in refs)
        assert any(ref.startswith("LAB-ORD-") for ref in refs)


@pytest.mark.asyncio
async def test_endpoint_care_contexts_discover_sync_202(discovery_test_env):
    client, _ = discovery_test_env
    req_id = str(uuid.uuid4())
    now_utc = datetime.now(timezone.utc).isoformat()

    payload = {
        "requestId": req_id,
        "timestamp": now_utc,
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

    headers = {
        "REQUEST-ID": req_id,
        "TIMESTAMP": now_utc,
        "X-CM-ID": "sbx",
    }

    # Test root /v0.5 mount
    resp = await client.post("/v0.5/care-contexts/discover", json=payload, headers=headers)
    assert resp.status_code == 202

    # Check webhook audit store recorded ingest
    event = webhook_audit_store.get_event_by_request_id(req_id)
    assert event is not None
    assert event.event_type == "care-contexts/discover"


@pytest.mark.asyncio
async def test_endpoint_discovery_simulate(discovery_test_env):
    client, _ = discovery_test_env
    sim_payload = {
        "full_name": "Arun Patel",
        "mobile": "+919876543210",
        "gender": "M",
        "year_of_birth": 1985,
        "match_threshold": 0.75,
    }

    resp = await client.post(
        "/api/v1/abdm/m2/bridge/discovery/simulate",
        json=sim_payload,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["matched"] is True
    assert data["confidence_score"] >= 0.75
    assert data["patient_name"] == "Arun Patel"
    assert "breakdown" in data
    assert data["callback_payload"] is not None
    assert data["callback_payload"]["patient"] is not None


@pytest.mark.asyncio
async def test_discovery_ambiguity_protection(discovery_test_env):
    _, session_factory = discovery_test_env

    # Seed a second patient with identical name and birth year
    async with session_factory() as session:
        user2 = User(
            id=str(uuid.uuid4()),
            email="arun.patel.2@nirmaya.local",
            full_name="Arun Patel",
            phone_number="+919876543299",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(user2)
        await session.flush()

        profile2 = PatientProfile(
            id=str(uuid.uuid4()),
            user_id=user2.id,
            date_of_birth=date(1985, 4, 12),
            gender=Gender.MALE,
            blood_group=BloodGroup.O_POSITIVE,
            abha_number="91-9999-3847-5610",
            abha_address="arun.patel.2@abdm",
        )
        session.add(profile2)
        await session.commit()

        # Query purely with Name and YOB (no ABHA or mobile) -> should trigger ambiguity protection
        ambiguous_query = PatientDiscoveryQuery(
            id="unknown@abdm",
            name="Arun Patel",
            gender="M",
            yearOfBirth=1985,
            verifiedIdentifiers=[],
        )

        matched, matched_prof, breakdown, care_contexts, err = await discover_patient(
            session=session,
            query=ambiguous_query,
        )

        assert matched is False
        assert matched_prof is None
        assert breakdown.match_status == "AMBIGUOUS"
        assert "Multiple potential patient matches" in err
