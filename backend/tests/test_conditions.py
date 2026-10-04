"""Comprehensive unit and integration test suite for Clinical Conditions and Problem Lists.

Validates condition creation, filtering, resolution lifecycles, role-based access control,
and HL7 FHIR Release 4 Condition resource serialization.
"""

from datetime import date, datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.fhir import FHIRCondition, to_fhir_condition
from app.main import app
from app.models.condition import ClinicalCondition
from app.models.doctor import DoctorProfile
from app.models.enums import (
    ClinicalStatus,
    ConditionCategory,
    ConditionSeverity,
    Gender,
    MedicalSpecialty,
    UserRole,
    VerificationStatus,
)
from app.models.patient import PatientProfile
from app.models.user import User


@pytest_asyncio.fixture
async def condition_test_env():
    """Provide isolated in-memory test database and client for condition testing."""
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
    """Generate authorization bearer headers for test user."""
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
    })
    return {"Authorization": f"Bearer {token}"}


async def seed_clinical_actors(session: AsyncSession):
    """Seed patient, doctor, and third-party patient users with profiles."""
    # 1. Patient 1
    u_pat1 = User(
        email="patient1@nirmaya.health",
        full_name="Rajesh Sharma",
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True,
    )
    session.add(u_pat1)
    await session.flush()

    pat1_profile = PatientProfile(
        user_id=u_pat1.id,
        gender=Gender.MALE,
        date_of_birth=date(1985, 4, 12),
        abha_number="91-1234-5678-9001",
        abha_address="rajesh.sharma@abdm",
    )
    session.add(pat1_profile)

    # 2. Patient 2 (unauthorized outsider)
    u_pat2 = User(
        email="patient2@nirmaya.health",
        full_name="Sunita Rao",
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True,
    )
    session.add(u_pat2)
    await session.flush()

    pat2_profile = PatientProfile(
        user_id=u_pat2.id,
        gender=Gender.FEMALE,
        date_of_birth=date(1992, 8, 20),
        abha_number="91-1234-5678-9002",
        abha_address="sunita.rao@abdm",
    )
    session.add(pat2_profile)

    # 3. Doctor
    u_doc = User(
        email="dr.gupta@nirmaya.health",
        full_name="Dr. Anil Gupta",
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=True,
    )
    session.add(u_doc)
    await session.flush()

    doc_profile = DoctorProfile(
        user_id=u_doc.id,
        registration_number="MCI-100201",
        medical_council="Delhi Medical Council",
        specialty=MedicalSpecialty.GENERAL_MEDICINE,
        qualifications="MBBS, MD (General Medicine)",
        experience_years=14,
        consultation_fee=500,
    )
    session.add(doc_profile)

    # 4. Admin
    u_admin = User(
        email="admin@nirmaya.health",
        full_name="System Admin",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    session.add(u_admin)
    await session.commit()

    return {
        "user_pat1": u_pat1,
        "pat1_profile": pat1_profile,
        "user_pat2": u_pat2,
        "pat2_profile": pat2_profile,
        "user_doc": u_doc,
        "doc_profile": doc_profile,
        "user_admin": u_admin,
    }


# ============================================================================
# Unit Tests: Model & FHIR Serialization
# ============================================================================


def test_fhir_condition_transformer_direct():
    """Verify that to_fhir_condition correctly constructs FHIR R4 Condition."""
    cond = ClinicalCondition(
        id="cond-uuid-001",
        patient_id="pat-uuid-001",
        clinical_status=ClinicalStatus.ACTIVE,
        verification_status=VerificationStatus.CONFIRMED,
        category=ConditionCategory.CHRONIC_CONDITION,
        severity=ConditionSeverity.SEVERE,
        code_coding_system="http://snomed.info/sct",
        code_value="38341003",
        code_display="Essential hypertension (disorder)",
        body_site="Cardiovascular system",
        onset_date_time=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
        recorded_date=datetime(2025, 1, 15, 11, 0, tzinfo=timezone.utc),
        note="Patient initiated on ACE inhibitor therapy.",
    )

    fhir_cond: FHIRCondition = to_fhir_condition(cond)

    assert fhir_cond.resourceType == "Condition"
    assert fhir_cond.id == "cond-uuid-001"
    assert fhir_cond.clinicalStatus.coding[0].code == "active"
    assert fhir_cond.verificationStatus.coding[0].code == "confirmed"
    assert fhir_cond.severity.coding[0].code == "24484000"
    assert fhir_cond.severity.coding[0].display == "Severe"
    assert fhir_cond.code.coding[0].code == "38341003"
    assert fhir_cond.code.coding[0].system == "http://snomed.info/sct"
    assert fhir_cond.code.text == "Essential hypertension (disorder)"
    assert fhir_cond.subject.reference == "Patient/pat-uuid-001"
    assert len(fhir_cond.note) == 1
    assert "ACE inhibitor" in fhir_cond.note[0].text


# ============================================================================
# Integration Tests: REST Endpoints
# ============================================================================


@pytest.mark.asyncio
async def test_doctor_records_clinical_condition(condition_test_env):
    """Doctor successfully records a diagnosed condition on a patient's problem list."""
    client, session_factory = condition_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat1_id = actors["pat1_profile"].id
    doc_user = actors["user_doc"]
    headers = auth_header_for(doc_user)

    payload = {
        "clinical_status": "active",
        "verification_status": "confirmed",
        "category": "problem-list-item",
        "severity": "moderate",
        "code_coding_system": "http://snomed.info/sct",
        "code_value": "38341003",
        "code_display": "Essential hypertension",
        "body_site": "Arterial system",
        "onset_date_time": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        "note": "Stage 1 hypertension diagnosed during consultation.",
    }

    res = await client.post(
        f"/api/v1/patients/{pat1_id}/conditions",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["patient_id"] == pat1_id
    assert data["code_value"] == "38341003"
    assert data["clinical_status"] == "active"
    assert data["severity"] == "moderate"
    assert data["recorded_by_doctor_id"] == actors["doc_profile"].id


@pytest.mark.asyncio
async def test_patient_self_reports_condition(condition_test_env):
    """Patient records self-reported condition with unconfirmed verification status."""
    client, session_factory = condition_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat1_id = actors["pat1_profile"].id
    pat1_user = actors["user_pat1"]
    headers = auth_header_for(pat1_user)

    payload = {
        "clinical_status": "active",
        "verification_status": "unconfirmed",
        "category": "problem-list-item",
        "severity": "mild",
        "code_coding_system": "http://snomed.info/sct",
        "code_value": "195967001",
        "code_display": "Asthma",
        "note": "Patient reports childhood wheezing when exposed to dust.",
    }

    res = await client.post(
        f"/api/v1/patients/{pat1_id}/conditions",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["patient_id"] == pat1_id
    assert data["recorded_by_doctor_id"] is None
    assert data["verification_status"] == "unconfirmed"


@pytest.mark.asyncio
async def test_record_condition_unauthorized_patient(condition_test_env):
    """Unauthorized patient is rejected when trying to record on another patient's problem list."""
    client, session_factory = condition_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat1_id = actors["pat1_profile"].id
    pat2_user = actors["user_pat2"]
    headers = auth_header_for(pat2_user)

    payload = {
        "code_value": "38341003",
        "code_display": "Essential hypertension",
    }

    res = await client.post(
        f"/api/v1/patients/{pat1_id}/conditions",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_list_patient_conditions_and_filters(condition_test_env):
    """List conditions and filter by clinical_status and category."""
    client, session_factory = condition_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat1_id = actors["pat1_profile"].id
    doc_user = actors["user_doc"]
    headers = auth_header_for(doc_user)

    # 1. Seed Condition A: Active Chronic Hypertension
    await client.post(
        f"/api/v1/patients/{pat1_id}/conditions",
        json={
            "clinical_status": "active",
            "category": "chronic-condition",
            "severity": "moderate",
            "code_value": "38341003",
            "code_display": "Hypertension",
        },
        headers=headers,
    )

    # 2. Seed Condition B: Resolved Acute Bronchitis
    await client.post(
        f"/api/v1/patients/{pat1_id}/conditions",
        json={
            "clinical_status": "resolved",
            "category": "encounter-diagnosis",
            "severity": "mild",
            "code_value": "10509002",
            "code_display": "Acute bronchitis",
        },
        headers=headers,
    )

    # List all
    res_all = await client.get(
        f"/api/v1/patients/{pat1_id}/conditions",
        headers=headers,
    )
    assert res_all.status_code == 200
    assert res_all.json()["pagination"]["total_count"] == 2

    # Filter active only
    res_active = await client.get(
        f"/api/v1/patients/{pat1_id}/conditions?clinical_status=active",
        headers=headers,
    )
    assert res_active.status_code == 200
    data_active = res_active.json()["data"]
    assert len(data_active) == 1
    assert data_active[0]["code_display"] == "Hypertension"

    # Filter resolved only
    res_resolved = await client.get(
        f"/api/v1/patients/{pat1_id}/conditions?clinical_status=resolved",
        headers=headers,
    )
    assert res_resolved.status_code == 200
    data_resolved = res_resolved.json()["data"]
    assert len(data_resolved) == 1
    assert data_resolved[0]["code_display"] == "Acute bronchitis"


@pytest.mark.asyncio
async def test_update_condition_resolution_lifecycle(condition_test_env):
    """Transition active condition to resolved and ensure abatement timestamp auto-populates."""
    client, session_factory = condition_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat1_id = actors["pat1_profile"].id
    doc_user = actors["user_doc"]
    headers = auth_header_for(doc_user)

    # Create active condition
    post_res = await client.post(
        f"/api/v1/patients/{pat1_id}/conditions",
        json={
            "clinical_status": "active",
            "code_value": "840539006",
            "code_display": "COVID-19 infection",
        },
        headers=headers,
    )
    assert post_res.status_code == 201
    condition_id = post_res.json()["data"]["id"]

    # Patch condition to resolved
    patch_res = await client.patch(
        f"/api/v1/conditions/{condition_id}",
        json={
            "clinical_status": "resolved",
            "note": "Rapid antigen test negative. Full recovery noted.",
        },
        headers=headers,
    )
    assert patch_res.status_code == 200
    data = patch_res.json()["data"]
    assert data["clinical_status"] == "resolved"
    assert data["abatement_date_time"] is not None
    assert "Full recovery" in data["note"]


@pytest.mark.asyncio
async def test_export_condition_fhir_r4(condition_test_env):
    """Export condition through FHIR endpoint and assert standard compliance."""
    client, session_factory = condition_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat1_id = actors["pat1_profile"].id
    doc_user = actors["user_doc"]
    headers = auth_header_for(doc_user)

    # Create condition
    post_res = await client.post(
        f"/api/v1/patients/{pat1_id}/conditions",
        json={
            "clinical_status": "active",
            "verification_status": "confirmed",
            "category": "problem-list-item",
            "severity": "mild",
            "code_coding_system": "http://snomed.info/sct",
            "code_value": "38341003",
            "code_display": "Essential hypertension",
            "note": "Under dietary management.",
        },
        headers=headers,
    )
    cond_id = post_res.json()["data"]["id"]

    # Fetch FHIR Condition
    fhir_res = await client.get(
        f"/api/v1/conditions/{cond_id}/fhir",
        headers=headers,
    )
    assert fhir_res.status_code == 200
    fhir_data = fhir_res.json()

    assert fhir_data["resourceType"] == "Condition"
    assert fhir_data["id"] == cond_id
    assert fhir_data["clinicalStatus"]["coding"][0]["code"] == "active"
    assert fhir_data["verificationStatus"]["coding"][0]["code"] == "confirmed"
    assert fhir_data["code"]["coding"][0]["code"] == "38341003"
    assert fhir_data["code"]["coding"][0]["system"] == "http://snomed.info/sct"
    assert fhir_data["subject"]["reference"] == f"Patient/{pat1_id}"
    assert len(fhir_data["note"]) == 1
    assert "dietary management" in fhir_data["note"][0]["text"]


@pytest.mark.asyncio
async def test_delete_condition_rbac(condition_test_env):
    """Doctors can delete conditions, while patients are forbidden."""
    client, session_factory = condition_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat1_id = actors["pat1_profile"].id
    doc_user = actors["user_doc"]
    pat1_user = actors["user_pat1"]

    # Create condition
    post_res = await client.post(
        f"/api/v1/patients/{pat1_id}/conditions",
        json={
            "clinical_status": "active",
            "code_value": "44054006",
            "code_display": "Type 2 diabetes mellitus",
        },
        headers=auth_header_for(doc_user),
    )
    cond_id = post_res.json()["data"]["id"]

    # 1. Patient attempt to delete -> 403 Forbidden
    del_res_pat = await client.delete(
        f"/api/v1/conditions/{cond_id}",
        headers=auth_header_for(pat1_user),
    )
    assert del_res_pat.status_code == 403

    # 2. Doctor delete -> 200 OK
    del_res_doc = await client.delete(
        f"/api/v1/conditions/{cond_id}",
        headers=auth_header_for(doc_user),
    )
    assert del_res_doc.status_code == 200

    # 3. Subsequent get returns 404
    get_res = await client.get(
        f"/api/v1/conditions/{cond_id}",
        headers=auth_header_for(doc_user),
    )
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_condition_timeline_validation(condition_test_env):
    """Pydantic validation rejects abatement date earlier than onset date."""
    client, session_factory = condition_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat1_id = actors["pat1_profile"].id
    doc_user = actors["user_doc"]
    headers = auth_header_for(doc_user)

    now = datetime.now(timezone.utc)
    invalid_payload = {
        "code_value": "38341003",
        "code_display": "Hypertension",
        "onset_date_time": now.isoformat(),
        "abatement_date_time": (now - timedelta(days=5)).isoformat(),  # 5 days before onset!
    }

    res = await client.post(
        f"/api/v1/patients/{pat1_id}/conditions",
        json=invalid_payload,
        headers=headers,
    )
    assert res.status_code == 422
