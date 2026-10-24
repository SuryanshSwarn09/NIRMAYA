"""Week 7 End-to-End Closed-Loop Patient Portal & Telemedicine Verification Test Suite.

Validates the full patient self-sovereign health vault and telemedicine experience engineered across Week 7:
1. Multi-Role Provisioning (Subject Patient Arun Patel with ABHA, Treating Clinician Dr. Ananya Sharma,
   Unauthorized Patient Vikram Malhotra, and Clinical Encounter).
2. Digital ABHA ID Card Generation & Cryptographic Vector QR Verification (Milestone 07-02):
   - High-resolution signed identity payload generation.
   - Vector QR payload parsing and cryptographic signature verification.
   - Tampered QR payload rejection guardrails.
3. Longitudinal Problem List & Active Clinical Conditions UI (Milestone 07-03):
   - Dual ontology ingestion (SNOMED-CT primary clinical concepts & ICD-10 diagnostic codes).
   - Patient symptom progress update and self-reporting with clinician encounter review flags.
   - HL7 FHIR Release 4 Condition resource export and canonical validation.
"""

from datetime import date, datetime, timedelta, timezone
import json
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.appointment import Appointment, DoctorSlot
from app.models.condition import ClinicalCondition
from app.models.doctor import DoctorProfile
from app.models.enums import (
    AppointmentStatus,
    AppointmentType,
    BloodGroup,
    ClinicalStatus,
    ConditionCategory,
    ConditionSeverity,
    Gender,
    MedicalSpecialty,
    SlotStatus,
    UserRole,
    VerificationStatus,
)
from app.models.patient import PatientProfile
from app.models.user import User


@pytest_asyncio.fixture
async def week_7_e2e_client():
    """Provide isolated in-memory test database and client for Week 7 E2E verification."""
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


async def seed_week_7_clinical_actors(session: AsyncSession) -> dict:
    """Seed primary patient Arun Patel, clinician Dr. Ananya Sharma, and unauthorized tenant."""
    # 1. Primary Patient: Arun Patel
    u_pat = User(
        id="usr-arun-patel-01",
        email="arun.patel@nirmaya.health",
        full_name="Arun Patel",
        phone_number="+91 98765 43210",
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True,
    )
    session.add(u_pat)
    await session.flush()

    pat_profile = PatientProfile(
        id="pat-arun-patel-01",
        user_id=u_pat.id,
        gender=Gender.MALE,
        date_of_birth=date(1990, 6, 4),
        blood_group=BloodGroup.O_POSITIVE,
        abha_number="91-8472-1092-4821",
        abha_address="arun.patel@abdm",
        address_line="Flat 402, Shanti Vihar",
        city="South Delhi",
        state="NCT of Delhi",
        pincode="110001",
        emergency_contact_name="Pooja Patel",
        emergency_contact_phone="+91 98765 09991",
    )
    session.add(pat_profile)

    # 2. Treating Clinician: Dr. Ananya Sharma
    u_doc = User(
        id="usr-doc-ananya-01",
        email="ananya.sharma@nirmaya.health",
        full_name="Dr. Ananya Sharma",
        phone_number="+91 98111 22334",
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=True,
    )
    session.add(u_doc)
    await session.flush()

    doc_profile = DoctorProfile(
        id="doc-ananya-01",
        user_id=u_doc.id,
        registration_number="DMC-2026-91024",
        medical_council="Delhi Medical Council",
        specialty=MedicalSpecialty.CARDIOLOGY,
        qualifications="MBBS, MD, DM (Cardiology, AIIMS)",
        hpr_id="ananya.sharma@hpr.abdm",
        experience_years=14,
        consultation_fee=1500,
    )
    session.add(doc_profile)
    await session.flush()

    # 3. Unauthorized Tenant: Vikram Malhotra
    u_unauth = User(
        id="usr-vikram-malhotra-01",
        email="vikram.malhotra@nirmaya.health",
        full_name="Vikram Malhotra",
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True,
    )
    session.add(u_unauth)
    await session.flush()

    unauth_profile = PatientProfile(
        id="pat-vikram-malhotra-01",
        user_id=u_unauth.id,
        gender=Gender.MALE,
        date_of_birth=date(1988, 11, 20),
        blood_group=BloodGroup.B_POSITIVE,
        abha_number="91-9988-7766-5544",
        abha_address="vikram.malhotra@abdm",
    )
    session.add(unauth_profile)

    # 4. Scheduled Telemedicine Encounter
    start_time = datetime.now(timezone.utc) + timedelta(days=2)
    end_time = start_time + timedelta(minutes=30)
    slot = DoctorSlot(
        id="slot-telemed-01",
        doctor_id=doc_profile.id,
        start_time=start_time,
        end_time=end_time,
        status=SlotStatus.BOOKED,
    )
    session.add(slot)
    await session.flush()

    appt = Appointment(
        id="appt-telemed-encounter-01",
        patient_id=pat_profile.id,
        doctor_id=doc_profile.id,
        slot_id=slot.id,
        scheduled_start=start_time,
        scheduled_end=end_time,
        status=AppointmentStatus.CONFIRMED,
        appointment_type=AppointmentType.ROUTINE_CHECKUP,
        reason="Quarterly cardiovascular review and blood pressure evaluation",
    )
    session.add(appt)
    await session.commit()

    return {
        "user_patient": u_pat,
        "patient_profile": pat_profile,
        "user_doctor": u_doc,
        "doctor_profile": doc_profile,
        "user_unauth": u_unauth,
        "unauth_profile": unauth_profile,
        "appointment": appt,
    }


# ==============================================================================
# Milestone 07-02: Digital ABHA ID Card & QR Cryptographic Verification
# ==============================================================================

@pytest.mark.asyncio
async def test_week_7_e2e_abha_card_generation_and_crypto_qr_verification(week_7_e2e_client):
    """E2E flow: Fetch authenticated ABHA ID card and verify vector QR payload authenticity."""
    client, session_factory = week_7_e2e_client
    async with session_factory() as session:
        actors = await seed_week_7_clinical_actors(session)

    pat_id = actors["patient_profile"].id
    pat_header = auth_header_for(actors["user_patient"])

    # 1. Fetch digital ABHA ID card
    card_resp = await client.get(f"/api/v1/patients/{pat_id}/abha-card", headers=pat_header)
    assert card_resp.status_code == 200
    card_body = card_resp.json()
    assert card_body["success"] is True

    card_data = card_body["data"]["card_data"]
    assert card_data["name"] == "Arun Patel"
    assert card_data["abha_number"] == "91-8472-1092-4821"
    assert card_data["abha_address"] == "arun.patel@abdm"
    assert card_data["gender"] == "M"
    assert card_data["blood_group"] == "O+"
    assert card_data["state"] == "NCT of Delhi"
    assert card_data["emergency_contact_name"] == "Pooja Patel"

    qr_payload = card_body["data"]["qr_payload"]
    assert qr_payload is not None
    assert len(qr_payload) > 50

    # 2. Cryptographic QR Verification
    verify_resp = await client.post(
        "/api/v1/patients/verify-abha-qr",
        json={"qr_string": qr_payload},
        headers=pat_header,
    )
    assert verify_resp.status_code == 200
    verify_body = verify_resp.json()
    assert verify_body["success"] is True

    verify_data = verify_body["data"]
    assert verify_data["is_valid"] is True
    assert verify_data["claims"]["hidn"] == "91-8472-1092-4821"
    assert verify_data["claims"]["hid"] == "arun.patel@abdm"
    assert verify_data["claims"]["name"] == "Arun Patel"
    assert "verified successfully" in verify_data["message"].lower()


@pytest.mark.asyncio
async def test_week_7_e2e_tampered_abha_qr_payload_rejection(week_7_e2e_client):
    """Verify that forged or altered QR payloads are rejected during cryptographic inspection."""
    client, session_factory = week_7_e2e_client
    async with session_factory() as session:
        actors = await seed_week_7_clinical_actors(session)

    pat_header = auth_header_for(actors["user_patient"])

    # Forged payload with altered name but invalid signature
    forged_qr = json.dumps({
        "hidn": "91-8472-1092-4821",
        "hid": "arun.patel@abdm",
        "name": "Tampered Attacker Name",
        "gender": "M",
        "dob": "1990-06-04",
        "mobile": "+91 98*** **210",
        "signature": "SHA256:0000000000000000000000000000000000000000000000000000000000000000",
    })

    verify_resp = await client.post(
        "/api/v1/patients/verify-abha-qr",
        json={"qr_string": forged_qr},
        headers=pat_header,
    )
    assert verify_resp.status_code == 200
    body = verify_resp.json()
    assert body["success"] is True
    assert body["data"]["is_valid"] is False
    assert "mismatch" in body["data"]["message"].lower() or "tampered" in body["data"]["message"].lower()


# ==============================================================================
# Milestone 07-03: Longitudinal Problem List & Active Clinical Conditions
# ==============================================================================

@pytest.mark.asyncio
async def test_week_7_e2e_problem_list_condition_intake_and_symptom_self_report(week_7_e2e_client):
    """E2E flow: Record SNOMED/ICD condition and submit patient symptom self-report."""
    client, session_factory = week_7_e2e_client
    async with session_factory() as session:
        actors = await seed_week_7_clinical_actors(session)

    pat_id = actors["patient_profile"].id
    doc_header = auth_header_for(actors["user_doctor"])
    pat_header = auth_header_for(actors["user_patient"])

    # 1. Clinician documents Essential Hypertension (SNOMED 38341003, ICD-10 I10)
    cond_resp = await client.post(
        f"/api/v1/patients/{pat_id}/conditions",
        json={
            "clinical_status": "active",
            "verification_status": "confirmed",
            "category": "chronic-condition",
            "severity": "moderate",
            "code_coding_system": "http://snomed.info/sct",
            "code_value": "38341003",
            "code_display": "Essential hypertension (disorder)",
            "note": "Initial baseline diagnosis during comprehensive cardiovascular checkup.",
        },
        headers=doc_header,
    )
    assert cond_resp.status_code == 201
    cond_data = cond_resp.json()["data"]
    cond_id = cond_data["id"]
    assert cond_data["code_value"] == "38341003"
    assert cond_data["clinical_status"] == "active"
    assert cond_data["severity"] == "moderate"

    # 2. Patient logs in and views their active problem list
    list_resp = await client.get(
        f"/api/v1/patients/{pat_id}/conditions?clinical_status=active",
        headers=pat_header,
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]
    assert len(items) >= 1
    assert items[0]["code_value"] == "38341003"

    # 3. Patient self-reports symptom progress update
    update_resp = await client.patch(
        f"/api/v1/conditions/{cond_id}",
        json={
            "severity": "mild",
            "note": "[Patient Self-Report] Blood pressure stable under Amlodipine 5mg. Requesting review at next appointment.",
        },
        headers=pat_header,
    )
    assert update_resp.status_code == 200
    updated_cond = update_resp.json()["data"]
    assert updated_cond["severity"] == "mild"
    assert "Patient Self-Report" in updated_cond["note"]


@pytest.mark.asyncio
async def test_week_7_e2e_condition_fhir_r4_canonical_export(week_7_e2e_client):
    """Verify that recorded chronic conditions export as valid HL7 FHIR R4 Condition resources."""
    client, session_factory = week_7_e2e_client
    async with session_factory() as session:
        actors = await seed_week_7_clinical_actors(session)

    pat_id = actors["patient_profile"].id
    doc_header = auth_header_for(actors["user_doctor"])

    # Document Type 2 Diabetes Mellitus
    cond_resp = await client.post(
        f"/api/v1/patients/{pat_id}/conditions",
        json={
            "clinical_status": "active",
            "verification_status": "confirmed",
            "category": "problem-list-item",
            "severity": "mild",
            "code_coding_system": "http://snomed.info/sct",
            "code_value": "44054006",
            "code_display": "Type 2 diabetes mellitus",
            "onset_date_time": "2024-03-15T00:00:00Z",
        },
        headers=doc_header,
    )
    assert cond_resp.status_code == 201
    cond_id = cond_resp.json()["data"]["id"]

    # Export FHIR R4 Condition
    fhir_resp = await client.get(f"/api/v1/conditions/{cond_id}/fhir", headers=doc_header)
    assert fhir_resp.status_code == 200
    fhir = fhir_resp.json()

    assert fhir["resourceType"] == "Condition"
    assert fhir["id"] == cond_id
    assert fhir["clinicalStatus"]["coding"][0]["code"] == "active"
    assert fhir["verificationStatus"]["coding"][0]["code"] == "confirmed"
    assert fhir["code"]["coding"][0]["code"] == "44054006"
    assert fhir["subject"]["reference"] == f"Patient/{pat_id}"


# ==============================================================================
# Milestone 07-04: LOINC Vitals Telemetry Intake & AHA Physiological Evaluations
# ==============================================================================

@pytest.mark.asyncio
async def test_week_7_e2e_vitals_telemetry_intake_and_loinc_evaluation(week_7_e2e_client):
    """E2E flow: Ingest LOINC multi-component blood pressure and vital signs panel."""
    client, session_factory = week_7_e2e_client
    async with session_factory() as session:
        actors = await seed_week_7_clinical_actors(session)

    pat_id = actors["patient_profile"].id
    pat_header = auth_header_for(actors["user_patient"])
    doc_header = auth_header_for(actors["user_doctor"])

    # 1. Clinician documents Dual-Component Blood Pressure (LOINC 85354-9)
    bp_payload = {
        "status": "final",
        "category": "vital-signs",
        "code_coding_system": "http://loinc.org",
        "code_value": "85354-9",
        "code_display": "Blood pressure panel with all children optional",
        "components": [
            {
                "code_system": "http://loinc.org",
                "code_value": "8480-6",
                "code_display": "Systolic blood pressure",
                "value_quantity": 138.0,
                "value_unit": "mmHg",
                "value_code": "mm[Hg]",
                "reference_range_low": 90.0,
                "reference_range_high": 120.0,
                "interpretation": "high",
            },
            {
                "code_system": "http://loinc.org",
                "code_value": "8462-4",
                "code_display": "Diastolic blood pressure",
                "value_quantity": 88.0,
                "value_unit": "mmHg",
                "value_code": "mm[Hg]",
                "reference_range_low": 60.0,
                "reference_range_high": 80.0,
                "interpretation": "high",
            },
        ],
        "interpretation": "high",
        "body_site": "Right arm",
        "method": "Automated cuff oscillometric",
        "note": "AHA Stage 1 Hypertension reading during telemed pre-flight intake.",
    }
    bp_resp = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json=bp_payload,
        headers=doc_header,
    )
    assert bp_resp.status_code == 201
    bp_data = bp_resp.json()["data"]
    assert bp_data["code_value"] == "85354-9"
    assert len(bp_data["components"]) == 2
    assert bp_data["interpretation"] == "high"

    # 2. Ingest Oxygen Saturation SpO2 (LOINC 2708-6)
    spo2_payload = {
        "status": "final",
        "category": "vital-signs",
        "code_coding_system": "http://loinc.org",
        "code_value": "2708-6",
        "code_display": "Oxygen saturation in Arterial blood by Pulse oximetry",
        "value_quantity": 98.0,
        "value_unit": "%",
        "value_code": "%",
        "reference_range_low": 95.0,
        "reference_range_high": 100.0,
        "interpretation": "normal",
        "method": "Pulse Oximetry",
    }
    spo2_resp = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json=spo2_payload,
        headers=pat_header,
    )
    assert spo2_resp.status_code == 201

    # 3. Ingest Heart Rate (LOINC 8867-4)
    hr_payload = {
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
        "interpretation": "normal",
    }
    hr_resp = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json=hr_payload,
        headers=pat_header,
    )
    assert hr_resp.status_code == 201

    # 4. Fetch Latest Vitals Summary Panel
    summary_resp = await client.get(
        f"/api/v1/patients/{pat_id}/observations/vitals/latest",
        headers=pat_header,
    )
    assert summary_resp.status_code == 200
    summary = summary_resp.json()["data"]
    assert summary["blood_pressure"] is not None
    assert summary["blood_pressure"]["code_value"] == "85354-9"
    assert summary["oxygen_saturation"] is not None
    assert summary["oxygen_saturation"]["value_quantity"] == 98.0
    assert summary["heart_rate"] is not None
    assert summary["heart_rate"]["value_quantity"] == 74.0


@pytest.mark.asyncio
async def test_week_7_e2e_vitals_fhir_r4_observation_export(week_7_e2e_client):
    """Verify that vital sign observations export as canonical HL7 FHIR R4 Observations."""
    client, session_factory = week_7_e2e_client
    async with session_factory() as session:
        actors = await seed_week_7_clinical_actors(session)

    pat_id = actors["patient_profile"].id
    doc_header = auth_header_for(actors["user_doctor"])

    # Create Blood Pressure observation
    bp_resp = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        json={
            "status": "final",
            "category": "vital-signs",
            "code_coding_system": "http://loinc.org",
            "code_value": "85354-9",
            "code_display": "Blood pressure panel with all children optional",
            "components": [
                {
                    "code_system": "http://loinc.org",
                    "code_value": "8480-6",
                    "code_display": "Systolic blood pressure",
                    "value_quantity": 120.0,
                    "value_unit": "mmHg",
                },
                {
                    "code_system": "http://loinc.org",
                    "code_value": "8462-4",
                    "code_display": "Diastolic blood pressure",
                    "value_quantity": 80.0,
                    "value_unit": "mmHg",
                },
            ],
            "interpretation": "normal",
        },
        headers=doc_header,
    )
    assert bp_resp.status_code == 201
    bp_id = bp_resp.json()["data"]["id"]

    # Export FHIR R4 Observation
    fhir_resp = await client.get(f"/api/v1/observations/{bp_id}/fhir", headers=doc_header)
    assert fhir_resp.status_code == 200
    fhir_data = fhir_resp.json()

    assert fhir_data["resourceType"] == "Observation"
    assert fhir_data["id"] == bp_id
    assert fhir_data["status"] == "final"
    assert fhir_data["category"][0]["coding"][0]["code"] == "vital-signs"
    assert fhir_data["code"]["coding"][0]["code"] == "85354-9"
    assert fhir_data["subject"]["reference"] == f"Patient/{pat_id}"
    assert len(fhir_data["component"]) == 2
    assert fhir_data["component"][0]["code"]["coding"][0]["code"] == "8480-6"
    assert fhir_data["component"][0]["valueQuantity"]["value"] == 120.0
    assert fhir_data["component"][1]["code"]["coding"][0]["code"] == "8462-4"
    assert fhir_data["component"][1]["valueQuantity"]["value"] == 80.0


# ==============================================================================
# Milestone 07-05: RBAC & Tenant Isolation Guardrails Across Patient Vault
# ==============================================================================

@pytest.mark.asyncio
async def test_week_7_e2e_patient_vault_cross_tenant_rbac_isolation(week_7_e2e_client):
    """Verify strict multi-tenant boundary: Vikram Malhotra cannot access Arun Patel's records."""
    client, session_factory = week_7_e2e_client
    async with session_factory() as session:
        actors = await seed_week_7_clinical_actors(session)

    arun_pat_id = actors["patient_profile"].id
    unauth_header = auth_header_for(actors["user_unauth"])
    pat_header = auth_header_for(actors["user_patient"])

    # 1. Attempt to view Arun Patel's ABHA ID Card -> 403 Forbidden
    card_resp = await client.get(f"/api/v1/patients/{arun_pat_id}/abha-card", headers=unauth_header)
    assert card_resp.status_code == 403

    # 2. Attempt to list Arun Patel's Problem List Conditions -> 403 Forbidden
    cond_resp = await client.get(f"/api/v1/patients/{arun_pat_id}/conditions", headers=unauth_header)
    assert cond_resp.status_code == 403

    # 3. Attempt to fetch Arun Patel's Vitals Telemetry -> 403 Forbidden
    vitals_resp = await client.get(f"/api/v1/patients/{arun_pat_id}/observations", headers=unauth_header)
    assert vitals_resp.status_code == 403

    # 4. Attempt to fetch Arun Patel's Latest Vitals Summary -> 403 Forbidden
    summary_resp = await client.get(
        f"/api/v1/patients/{arun_pat_id}/observations/vitals/latest",
        headers=unauth_header,
    )
    assert summary_resp.status_code == 403

    # 5. Legitimate Subject Patient Arun Patel has authorized 200 OK access
    auth_card_resp = await client.get(f"/api/v1/patients/{arun_pat_id}/abha-card", headers=pat_header)
    assert auth_card_resp.status_code == 200

