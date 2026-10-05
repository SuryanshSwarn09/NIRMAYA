"""Comprehensive unit and integration test suite for Clinical Observations and Vital Signs.

Validates single and multi-component observations (Blood Pressure), LOINC codings,
automatic interpretation calculation, longitudinal filtering, latest vitals summary,
role-based access control, and HL7 FHIR Release 4 Observation resource serialization.
"""

from datetime import date, datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.fhir import FHIRObservation, to_fhir_observation
from app.main import app
from app.models.appointment import Appointment, DoctorSlot
from app.models.doctor import DoctorProfile
from app.models.enums import (
    AppointmentStatus,
    AppointmentType,
    Gender,
    MedicalSpecialty,
    ObservationCategory,
    ObservationInterpretation,
    ObservationStatus,
    SlotStatus,
    UserRole,
)
from app.models.observation import ClinicalObservation
from app.models.patient import PatientProfile
from app.models.user import User
from app.services.observation import calculate_bmi


@pytest_asyncio.fixture
async def obs_test_env():
    """Provide isolated in-memory test database and HTTP client for observation testing."""
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
    """Seed patient, doctor, and second patient users with profiles and encounter."""
    # 1. Patient 1 (Subject)
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

    # 2. Patient 2 (Unauthorized third party)
    u_pat2 = User(
        email="patient2@nirmaya.health",
        full_name="Priya Nair",
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True,
    )
    session.add(u_pat2)
    await session.flush()

    pat2_profile = PatientProfile(
        user_id=u_pat2.id,
        gender=Gender.FEMALE,
        date_of_birth=date(1992, 8, 24),
        abha_number="91-9876-5432-1002",
        abha_address="priya.nair@abdm",
    )
    session.add(pat2_profile)

    # 3. Doctor (Performer)
    u_doc = User(
        email="doctor@nirmaya.health",
        full_name="Dr. Ananya Sharma",
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=True,
    )
    session.add(u_doc)
    await session.flush()

    doc_profile = DoctorProfile(
        user_id=u_doc.id,
        registration_number="DMC-2026-9901",
        medical_council="Delhi Medical Council",
        specialty=MedicalSpecialty.CARDIOLOGY,
        qualifications="MBBS, MD, DM (Cardiology)",
        hpr_id="ananya.sharma@hpr.abdm",
        experience_years=12,
        consultation_fee=1500,
    )
    session.add(doc_profile)
    await session.flush()

    # 4. Clinical Encounter
    start_time = datetime.now(timezone.utc) + timedelta(days=1)
    end_time = start_time + timedelta(minutes=30)
    slot = DoctorSlot(
        doctor_id=doc_profile.id,
        start_time=start_time,
        end_time=end_time,
        status=SlotStatus.BOOKED,
    )
    session.add(slot)
    await session.flush()

    appt = Appointment(
        patient_id=pat1_profile.id,
        doctor_id=doc_profile.id,
        slot_id=slot.id,
        appointment_type=AppointmentType.ROUTINE_CHECKUP,
        status=AppointmentStatus.CONFIRMED,
        scheduled_start=start_time,
        scheduled_end=end_time,
        reason="Hypertension follow-up and vital signs telemetry",
    )
    session.add(appt)
    await session.commit()

    return {
        "user_pat1": u_pat1,
        "patient1": pat1_profile,
        "user_pat2": u_pat2,
        "patient2": pat2_profile,
        "user_doc": u_doc,
        "doctor": doc_profile,
        "encounter": appt,
    }


# ============================================================================
# Unit Tests: BMI Calculator
# ============================================================================


def test_calculate_bmi():
    """Verify BMI calculator handles normal, overweight, and obese thresholds correctly."""
    # Normal: 70kg, 175cm -> 22.9
    bmi, interp = calculate_bmi(70.0, 175.0)
    assert bmi == 22.9
    assert interp == ObservationInterpretation.NORMAL

    # Underweight: 45kg, 170cm -> 15.6
    bmi_under, interp_under = calculate_bmi(45.0, 170.0)
    assert bmi_under == 15.6
    assert interp_under == ObservationInterpretation.LOW

    # Overweight: 85kg, 175cm -> 27.8
    bmi_over, interp_over = calculate_bmi(85.0, 175.0)
    assert bmi_over == 27.8
    assert interp_over == ObservationInterpretation.HIGH

    # Obese: 105kg, 170cm -> 36.3
    bmi_obese, interp_obese = calculate_bmi(105.0, 170.0)
    assert bmi_obese == 36.3
    assert interp_obese == ObservationInterpretation.CRITICALLY_HIGH


# ============================================================================
# Integration Tests: Observation CRUD & Telemetry
# ============================================================================


@pytest.mark.asyncio
async def test_record_single_vital_sign(obs_test_env):
    """Verify recording a single quantitative vital sign (Heart Rate) via REST endpoint."""
    client, session_factory = obs_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])

    payload = {
        "status": "final",
        "category": "vital-signs",
        "code_coding_system": "http://loinc.org",
        "code_value": "8867-4",
        "code_display": "Heart rate",
        "value_quantity": 74.0,
        "value_unit": "/min",
        "value_code": "/min",
        "reference_range_low": 60.0,
        "reference_range_high": 100.0,
        "reference_range_text": "60 - 100 /min",
        "note": "Resting heart rate measured in seated position.",
    }

    resp = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json=payload,
        headers=doc_header,
    )

    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["code_value"] == "8867-4"
    assert data["value_quantity"] == 74.0
    assert data["interpretation"] == "normal"  # Auto-computed by schema validator
    assert data["performer_doctor_id"] == actors["doctor"].id


@pytest.mark.asyncio
async def test_auto_interpretation_calculation(obs_test_env):
    """Verify schema auto-computes HIGH and LOW interpretations based on reference limits."""
    client, session_factory = obs_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])

    # 1. Tachycardia (High Heart Rate: 125 bpm)
    high_payload = {
        "category": "vital-signs",
        "code_value": "8867-4",
        "code_display": "Heart rate",
        "value_quantity": 125.0,
        "value_unit": "/min",
        "reference_range_low": 60.0,
        "reference_range_high": 100.0,
    }
    r_high = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json=high_payload,
        headers=doc_header,
    )
    assert r_high.status_code == 201
    assert r_high.json()["data"]["interpretation"] == "high"

    # 2. Bradycardia (Low Heart Rate: 48 bpm)
    low_payload = {
        "category": "vital-signs",
        "code_value": "8867-4",
        "code_display": "Heart rate",
        "value_quantity": 48.0,
        "value_unit": "/min",
        "reference_range_low": 60.0,
        "reference_range_high": 100.0,
    }
    r_low = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json=low_payload,
        headers=doc_header,
    )
    assert r_low.status_code == 201
    assert r_low.json()["data"]["interpretation"] == "low"


@pytest.mark.asyncio
async def test_record_compound_observation_blood_pressure(obs_test_env):
    """Verify recording a multi-component Blood Pressure panel with systolic and diastolic sub-values."""
    client, session_factory = obs_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])

    bp_payload = {
        "status": "final",
        "category": "vital-signs",
        "code_coding_system": "http://loinc.org",
        "code_value": "85354-9",
        "code_display": "Blood pressure panel with all children optional",
        "body_site": "Right upper arm",
        "method": "Automated oscillometric",
        "components": [
            {
                "code_system": "http://loinc.org",
                "code_value": "8480-6",
                "code_display": "Systolic blood pressure",
                "value_quantity": 134.0,
                "value_unit": "mmHg",
                "value_code": "mm[Hg]",
                "interpretation": "high",
                "reference_range_low": 90.0,
                "reference_range_high": 120.0,
            },
            {
                "code_system": "http://loinc.org",
                "code_value": "8462-4",
                "code_display": "Diastolic blood pressure",
                "value_quantity": 86.0,
                "value_unit": "mmHg",
                "value_code": "mm[Hg]",
                "interpretation": "high",
                "reference_range_low": 60.0,
                "reference_range_high": 80.0,
            },
        ],
        "note": "Stage 1 systolic hypertension documented during routine consult.",
    }

    resp = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json=bp_payload,
        headers=doc_header,
    )

    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["code_value"] == "85354-9"
    assert len(data["components"]) == 2
    assert data["components"][0]["code_value"] == "8480-6"
    assert data["components"][0]["value_quantity"] == 134.0
    assert data["components"][1]["code_value"] == "8462-4"
    assert data["components"][1]["value_quantity"] == 86.0


@pytest.mark.asyncio
async def test_list_patient_observations_with_filtering(obs_test_env):
    """Verify querying longitudinal observations with category and code filtering."""
    client, session_factory = obs_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])

    # Record 1 Heart Rate and 1 SpO2 observation
    await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json={"category": "vital-signs", "code_value": "8867-4", "code_display": "Heart rate", "value_quantity": 72.0, "value_unit": "/min"},
        headers=doc_header,
    )
    await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json={"category": "vital-signs", "code_value": "2708-6", "code_display": "Oxygen saturation", "value_quantity": 98.0, "value_unit": "%"},
        headers=doc_header,
    )

    # 1. Query all
    r_all = await client.get(f"/api/v1/patients/{pat_id}/observations", headers=doc_header)
    assert r_all.status_code == 200
    assert r_all.json()["pagination"]["total_count"] == 2

    # 2. Query filtered by LOINC code 8867-4
    r_hr = await client.get(f"/api/v1/patients/{pat_id}/observations?code_value=8867-4", headers=doc_header)
    assert r_hr.status_code == 200
    assert r_hr.json()["pagination"]["total_count"] == 1
    assert r_hr.json()["data"][0]["code_value"] == "8867-4"


@pytest.mark.asyncio
async def test_get_latest_vitals_summary(obs_test_env):
    """Verify the /vitals/latest endpoint correctly synthesizes the latest reading for each panel."""
    client, session_factory = obs_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])

    # 1. Record an older Heart Rate (80 bpm) and a newer Heart Rate (68 bpm)
    t_old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    t_new = datetime.now(timezone.utc).isoformat()

    await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json={"code_value": "8867-4", "code_display": "Heart rate", "value_quantity": 80.0, "effective_date_time": t_old},
        headers=doc_header,
    )
    await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json={"code_value": "8867-4", "code_display": "Heart rate", "value_quantity": 68.0, "effective_date_time": t_new},
        headers=doc_header,
    )

    # 2. Record SpO2 (99%)
    await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json={"code_value": "2708-6", "code_display": "SpO2", "value_quantity": 99.0, "effective_date_time": t_new},
        headers=doc_header,
    )

    # 3. Call latest vitals endpoint
    resp = await client.get(f"/api/v1/patients/{pat_id}/observations/vitals/latest", headers=doc_header)
    assert resp.status_code == 200
    vitals = resp.json()["data"]

    assert vitals["heart_rate"] is not None
    assert vitals["heart_rate"]["value_quantity"] == 68.0  # Must be newer reading!
    assert vitals["oxygen_saturation"] is not None
    assert vitals["oxygen_saturation"]["value_quantity"] == 99.0
    assert vitals["blood_pressure"] is None  # Not recorded yet
    assert vitals["last_recorded_at"] is not None


@pytest.mark.asyncio
async def test_update_observation_status_and_notes(obs_test_env):
    """Verify updating observation status and diagnostic notes."""
    client, session_factory = obs_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])

    post_resp = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json={"category": "vital-signs", "code_value": "8867-4", "code_display": "Heart rate", "value_quantity": 72.0},
        headers=doc_header,
    )
    obs_id = post_resp.json()["data"]["id"]

    patch_resp = await client.patch(
        f"/api/v1/observations/{obs_id}",
        json={"status": "amended", "note": "Patient re-checked after hydration; resting comfortably."},
        headers=doc_header,
    )

    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["status"] == "amended"
    assert "re-checked after hydration" in patch_resp.json()["data"]["note"]


@pytest.mark.asyncio
async def test_export_hl7_fhir_r4_observation_single(obs_test_env):
    """Verify exporting a quantitative single observation as certified HL7 FHIR R4 JSON."""
    client, session_factory = obs_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])

    post_resp = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json={
            "category": "vital-signs",
            "code_value": "8867-4",
            "code_display": "Heart rate",
            "value_quantity": 72.0,
            "value_unit": "/min",
            "value_code": "/min",
            "reference_range_low": 60.0,
            "reference_range_high": 100.0,
            "reference_range_text": "60 - 100 /min",
        },
        headers=doc_header,
    )
    obs_id = post_resp.json()["data"]["id"]

    fhir_resp = await client.get(f"/api/v1/observations/{obs_id}/fhir", headers=doc_header)
    assert fhir_resp.status_code == 200
    fhir = fhir_resp.json()

    assert fhir["resourceType"] == "Observation"
    assert fhir["id"] == obs_id
    assert fhir["status"] == "final"
    assert fhir["subject"]["reference"] == f"Patient/{pat_id}"
    assert fhir["code"]["coding"][0]["code"] == "8867-4"
    assert fhir["valueQuantity"]["value"] == 72.0
    assert fhir["valueQuantity"]["code"] == "/min"
    assert len(fhir["referenceRange"]) == 1
    assert fhir["referenceRange"][0]["low"]["value"] == 60.0


@pytest.mark.asyncio
async def test_export_hl7_fhir_r4_observation_compound_blood_pressure(obs_test_env):
    """Verify exporting compound Blood Pressure panel as FHIR R4 with component structures."""
    client, session_factory = obs_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])

    post_resp = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json={
            "category": "vital-signs",
            "code_value": "85354-9",
            "code_display": "Blood pressure panel with all children optional",
            "components": [
                {
                    "code_system": "http://loinc.org",
                    "code_value": "8480-6",
                    "code_display": "Systolic blood pressure",
                    "value_quantity": 120.0,
                    "value_unit": "mmHg",
                    "value_code": "mm[Hg]",
                },
                {
                    "code_system": "http://loinc.org",
                    "code_value": "8462-4",
                    "code_display": "Diastolic blood pressure",
                    "value_quantity": 80.0,
                    "value_unit": "mmHg",
                    "value_code": "mm[Hg]",
                },
            ],
        },
        headers=doc_header,
    )
    obs_id = post_resp.json()["data"]["id"]

    fhir_resp = await client.get(f"/api/v1/observations/{obs_id}/fhir", headers=doc_header)
    assert fhir_resp.status_code == 200
    fhir = fhir_resp.json()

    assert fhir["resourceType"] == "Observation"
    assert fhir["code"]["coding"][0]["code"] == "85354-9"
    assert len(fhir["component"]) == 2
    assert fhir["component"][0]["code"]["coding"][0]["code"] == "8480-6"
    assert fhir["component"][0]["valueQuantity"]["value"] == 120.0
    assert fhir["component"][1]["code"]["coding"][0]["code"] == "8462-4"
    assert fhir["component"][1]["valueQuantity"]["value"] == 80.0


@pytest.mark.asyncio
async def test_observation_rbac_security(obs_test_env):
    """Verify role-based security isolation: patients can self-report, but cannot view other patients' data."""
    client, session_factory = obs_test_env
    async with session_factory() as session:
        actors = await seed_clinical_actors(session)

    pat1_id = actors["patient1"].id
    pat1_header = auth_header_for(actors["user_pat1"])
    pat2_header = auth_header_for(actors["user_pat2"])

    # 1. Patient 1 self-reports vitals -> Allowed (201)
    self_report = await client.post(
        f"/api/v1/patients/{pat1_id}/observations",
        json={"category": "vital-signs", "code_value": "8867-4", "code_display": "Heart rate", "value_quantity": 76.0},
        headers=pat1_header,
    )
    assert self_report.status_code == 201

    # 2. Patient 2 attempts to read Patient 1's observations -> Forbidden (403)
    p2_read = await client.get(f"/api/v1/patients/{pat1_id}/observations", headers=pat2_header)
    assert p2_read.status_code == 403

    # 3. Patient 2 attempts to write to Patient 1's observations -> Forbidden (403)
    p2_write = await client.post(
        f"/api/v1/patients/{pat1_id}/observations",
        json={"category": "vital-signs", "code_value": "8867-4", "code_display": "Heart rate", "value_quantity": 90.0},
        headers=pat2_header,
    )
    assert p2_write.status_code == 403

    # 4. Unauthenticated request -> Unauthorized (401)
    unauth = await client.get(f"/api/v1/patients/{pat1_id}/observations")
    assert unauth.status_code == 401
