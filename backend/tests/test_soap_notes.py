"""Comprehensive unit and integration test suite for Structured SOAP Clinical Notes.

Validates:
1. Practitioner doctor SOAP note authoring.
2. RBAC enforcement (patients cannot author clinical notes).
3. Longitudinal patient SOAP notes retrieval with filters & pagination.
4. Preliminary note updates.
5. Digital signature attestation with SHA-256 tamper-evident digest.
6. Immutability guarantee (signed notes cannot be modified).
7. HL7 FHIR Release 4 Composition serialization with LOINC narrative sections.
8. Deletion lifecycles (purge draft vs enter-in-error for signed notes).
"""

from datetime import date, datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.fhir import to_fhir_composition
from app.main import app
from app.models.appointment import Appointment, DoctorSlot
from app.models.doctor import DoctorProfile
from app.models.enums import (
    AppointmentStatus,
    AppointmentType,
    ClinicalNoteStatus,
    ClinicalNoteType,
    Gender,
    MedicalSpecialty,
    SlotStatus,
    UserRole,
)
from app.models.patient import PatientProfile
from app.models.soap_note import SoapNote
from app.models.user import User


@pytest_asyncio.fixture
async def soap_test_env():
    """Provide isolated in-memory SQLite database and HTTP client for SOAP note tests."""
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


async def seed_soap_actors(session: AsyncSession):
    """Seed patient, doctor, unauthorized patient, and encounter appointment."""
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

    # 3. Doctor (Clinician Author)
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
        status=AppointmentStatus.COMPLETED,
        scheduled_start=start_time,
        scheduled_end=end_time,
    )
    session.add(appt)
    await session.commit()

    return u_pat1, pat1_profile, u_pat2, pat2_profile, u_doc, doc_profile, appt


@pytest.mark.asyncio
async def test_create_soap_note_by_doctor(soap_test_env):
    """Doctor can author a structured SOAP clinical note for a patient encounter."""
    client, session_factory = soap_test_env
    async with session_factory() as session:
        u_pat1, pat1, _, _, u_doc, doc, appt = await seed_soap_actors(session)

    payload = {
        "encounter_id": appt.id,
        "note_type": "soap",
        "title": "Cardiology Follow-up SOAP Note",
        "chief_complaint": "Exertional dyspnea and retrosternal heaviness for 4 days",
        "subjective": "Patient reports shortness of breath climbing 2 flights of stairs. No orthopnea or PND.",
        "objective": "BP 138/88 mmHg, HR 74 bpm regular, SpO2 98% room air. Clear breath sounds bilaterally.",
        "assessment": "1. Exertional Angina CCS Class II. 2. Stage 1 Essential Hypertension.",
        "plan": "1. Increase Amlodipine to 10mg daily. 2. Order resting 12-lead ECG and Lipid Profile. 3. Review in 2 weeks.",
        "primary_diagnosis_code": "I20.9",
        "primary_diagnosis_display": "Angina pectoris, unspecified",
        "follow_up_instructions": "Review in Cardiology OPD in 14 days with ECG tracing.",
    }

    res = await client.post(
        f"/api/v1/patients/{pat1.id}/soap-notes",
        json=payload,
        headers=auth_header_for(u_doc),
    )
    assert res.status_code == 201, res.text
    data = res.json()["data"]

    assert data["patient_id"] == pat1.id
    assert data["doctor_id"] == doc.id
    assert data["encounter_id"] == appt.id
    assert data["chief_complaint"] == payload["chief_complaint"]
    assert data["status"] == "preliminary"
    assert data["is_signed"] is False
    assert data["signature_hash"] is None


@pytest.mark.asyncio
async def test_patient_cannot_author_soap_note(soap_test_env):
    """Patients cannot author clinical encounter notes (RBAC 403 Forbidden)."""
    client, session_factory = soap_test_env
    async with session_factory() as session:
        u_pat1, pat1, _, _, _, _, appt = await seed_soap_actors(session)

    payload = {
        "encounter_id": appt.id,
        "chief_complaint": "Mild headache",
        "subjective": "Headache since morning",
        "objective": "No fever",
        "assessment": "Tension headache",
        "plan": "Rest and hydration",
    }

    res = await client.post(
        f"/api/v1/patients/{pat1.id}/soap-notes",
        json=payload,
        headers=auth_header_for(u_pat1),
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_soap_note_access_control(soap_test_env):
    """Patient and Doctor can read the note, but unauthorized third-party receives 403."""
    client, session_factory = soap_test_env
    async with session_factory() as session:
        u_pat1, pat1, u_pat2, _, u_doc, doc, appt = await seed_soap_actors(session)

    # 1. Author note as doctor
    create_res = await client.post(
        f"/api/v1/patients/{pat1.id}/soap-notes",
        json={
            "encounter_id": appt.id,
            "chief_complaint": "Routine health evaluation",
            "subjective": "Asymptomatic, feeling well.",
            "objective": "BP 120/80 mmHg, HR 72 bpm.",
            "assessment": "Normal cardiovascular exam.",
            "plan": "Continue healthy lifestyle habits.",
        },
        headers=auth_header_for(u_doc),
    )
    note_id = create_res.json()["data"]["id"]

    # 2. Patient 1 can read
    res_pat1 = await client.get(f"/api/v1/soap-notes/{note_id}", headers=auth_header_for(u_pat1))
    assert res_pat1.status_code == 200

    # 3. Doctor can read
    res_doc = await client.get(f"/api/v1/soap-notes/{note_id}", headers=auth_header_for(u_doc))
    assert res_doc.status_code == 200

    # 4. Patient 2 is unauthorized (403)
    res_pat2 = await client.get(f"/api/v1/soap-notes/{note_id}", headers=auth_header_for(u_pat2))
    assert res_pat2.status_code == 403


@pytest.mark.asyncio
async def test_list_patient_soap_notes_with_filters(soap_test_env):
    """Query patient SOAP notes with pagination and status filters."""
    client, session_factory = soap_test_env
    async with session_factory() as session:
        u_pat1, pat1, _, _, u_doc, doc, appt = await seed_soap_actors(session)

    # Create 2 notes
    await client.post(
        f"/api/v1/patients/{pat1.id}/soap-notes",
        json={
            "chief_complaint": "Visit 1",
            "subjective": "S1",
            "objective": "O1",
            "assessment": "A1",
            "plan": "P1",
        },
        headers=auth_header_for(u_doc),
    )
    await client.post(
        f"/api/v1/patients/{pat1.id}/soap-notes",
        json={
            "chief_complaint": "Visit 2",
            "subjective": "S2",
            "objective": "O2",
            "assessment": "A2",
            "plan": "P2",
        },
        headers=auth_header_for(u_doc),
    )

    list_res = await client.get(
        f"/api/v1/patients/{pat1.id}/soap-notes?page=1&limit=10",
        headers=auth_header_for(u_pat1),
    )
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["pagination"]["total_count"] == 2
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_update_preliminary_soap_note(soap_test_env):
    """Doctor can update preliminary note content before signing."""
    client, session_factory = soap_test_env
    async with session_factory() as session:
        _, pat1, _, _, u_doc, _, _ = await seed_soap_actors(session)

    create_res = await client.post(
        f"/api/v1/patients/{pat1.id}/soap-notes",
        json={
            "chief_complaint": "Draft Complaint",
            "subjective": "Initial subjective notes",
            "objective": "Initial objective findings",
            "assessment": "Initial impression",
            "plan": "Initial care plan",
        },
        headers=auth_header_for(u_doc),
    )
    note_id = create_res.json()["data"]["id"]

    patch_res = await client.patch(
        f"/api/v1/soap-notes/{note_id}",
        json={
            "chief_complaint": "Updated Complaint with additional symptoms",
            "plan": "Amended prescription: Metoprolol 25mg BD",
        },
        headers=auth_header_for(u_doc),
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()["data"]
    assert updated_data["chief_complaint"] == "Updated Complaint with additional symptoms"
    assert "Metoprolol" in updated_data["plan"]


@pytest.mark.asyncio
async def test_sign_and_finalize_soap_note(soap_test_env):
    """Doctor electronically signs SOAP note, generating tamper-evident digest and final status."""
    client, session_factory = soap_test_env
    async with session_factory() as session:
        _, pat1, _, _, u_doc, _, _ = await seed_soap_actors(session)

    create_res = await client.post(
        f"/api/v1/patients/{pat1.id}/soap-notes",
        json={
            "chief_complaint": "Chest pressure on exertion",
            "subjective": "Pain radiates to left arm",
            "objective": "BP 142/90, HR 80",
            "assessment": "Suspected CAD",
            "plan": "Coronary angiogram advised",
        },
        headers=auth_header_for(u_doc),
    )
    note_id = create_res.json()["data"]["id"]

    # Sign the note
    sign_res = await client.post(
        f"/api/v1/soap-notes/{note_id}/sign",
        json={"comments": "Attested electronically by Dr. Ananya Sharma via HPR verification."},
        headers=auth_header_for(u_doc),
    )
    assert sign_res.status_code == 200
    signed_data = sign_res.json()["data"]

    assert signed_data["is_signed"] is True
    assert signed_data["status"] == "final"
    assert signed_data["signed_at"] is not None
    assert signed_data["signature_hash"] is not None
    assert len(signed_data["signature_hash"]) == 64  # SHA-256 hex digest length


@pytest.mark.asyncio
async def test_cannot_modify_signed_soap_note(soap_test_env):
    """Digitally signed notes are immutable and reject subsequent modifications."""
    client, session_factory = soap_test_env
    async with session_factory() as session:
        _, pat1, _, _, u_doc, _, _ = await seed_soap_actors(session)

    create_res = await client.post(
        f"/api/v1/patients/{pat1.id}/soap-notes",
        json={
            "chief_complaint": "Acute appendicitis evaluation",
            "subjective": "Right lower quadrant abdominal pain",
            "objective": "Tenderness at McBurney's point",
            "assessment": "Acute appendicitis",
            "plan": "Urgent appendectomy",
        },
        headers=auth_header_for(u_doc),
    )
    note_id = create_res.json()["data"]["id"]

    # Sign the note
    await client.post(
        f"/api/v1/soap-notes/{note_id}/sign",
        json={"comments": "Attested"},
        headers=auth_header_for(u_doc),
    )

    # Attempt modification -> should fail with 400 Bad Request
    patch_res = await client.patch(
        f"/api/v1/soap-notes/{note_id}",
        json={"plan": "Changed my mind: medical management instead"},
        headers=auth_header_for(u_doc),
    )
    assert patch_res.status_code == 400
    res_json = patch_res.json()
    err_msg = res_json.get("message") or res_json.get("detail") or patch_res.text
    assert "immutable" in err_msg.lower()


@pytest.mark.asyncio
async def test_export_soap_note_fhir_composition(soap_test_env):
    """Exporting clinical note yields canonical HL7 FHIR Release 4 Composition resource."""
    client, session_factory = soap_test_env
    async with session_factory() as session:
        u_pat1, pat1, _, _, u_doc, doc, appt = await seed_soap_actors(session)

    create_res = await client.post(
        f"/api/v1/patients/{pat1.id}/soap-notes",
        json={
            "encounter_id": appt.id,
            "title": "Comprehensive Clinical Consultation",
            "chief_complaint": "Persistent fatigue and palpitations",
            "subjective": "Fatigue exacerbated by moderate exercise.",
            "objective": "Thyroid gland non-tender, resting tachycardia.",
            "assessment": "1. Thyrotoxicosis workup. 2. Sinus Tachycardia.",
            "plan": "Order Free T3, Free T4, TSH. Start Propranolol 20mg BD.",
        },
        headers=auth_header_for(u_doc),
    )
    note_id = create_res.json()["data"]["id"]

    # Sign note
    await client.post(f"/api/v1/soap-notes/{note_id}/sign", headers=auth_header_for(u_doc))

    fhir_res = await client.get(
        f"/api/v1/soap-notes/{note_id}/fhir",
        headers=auth_header_for(u_pat1),
    )
    assert fhir_res.status_code == 200
    composition = fhir_res.json()

    assert composition["resourceType"] == "Composition"
    assert composition["id"] == note_id
    assert composition["status"] == "final"
    assert composition["subject"]["reference"] == f"Patient/{pat1.id}"
    assert composition["encounter"]["reference"] == f"Encounter/{appt.id}"
    assert composition["author"][0]["reference"] == f"Practitioner/{doc.id}"

    # Verify 5 structured narrative sections
    sections = composition["section"]
    assert len(sections) == 5

    section_titles = [s["title"] for s in sections]
    assert section_titles == ["Chief Complaint", "Subjective", "Objective", "Assessment", "Plan"]

    # Verify LOINC section codes
    loinc_codes = [s["code"]["coding"][0]["code"] for s in sections]
    assert loinc_codes == ["10154-3", "61150-9", "61149-1", "51848-0", "18776-5"]

    # Verify XHTML generated narrative
    for s in sections:
        assert s["text"]["status"] == "generated"
        assert "<div xmlns=\"http://www.w3.org/1999/xhtml\">" in s["text"]["div"]


@pytest.mark.asyncio
async def test_delete_draft_vs_signed_soap_note(soap_test_env):
    """Deleting a draft note purges it; deleting a signed note marks it entered-in-error."""
    client, session_factory = soap_test_env
    async with session_factory() as session:
        _, pat1, _, _, u_doc, _, _ = await seed_soap_actors(session)

    # 1. Draft note
    d_res = await client.post(
        f"/api/v1/patients/{pat1.id}/soap-notes",
        json={
            "chief_complaint": "Draft to be deleted",
            "subjective": "Subj",
            "objective": "Obj",
            "assessment": "Assess",
            "plan": "Plan",
        },
        headers=auth_header_for(u_doc),
    )
    draft_id = d_res.json()["data"]["id"]

    # Delete draft -> purged
    del_draft = await client.delete(f"/api/v1/soap-notes/{draft_id}", headers=auth_header_for(u_doc))
    assert del_draft.status_code == 204

    check_draft = await client.get(f"/api/v1/soap-notes/{draft_id}", headers=auth_header_for(u_doc))
    assert check_draft.status_code == 404

    # 2. Signed note
    s_res = await client.post(
        f"/api/v1/patients/{pat1.id}/soap-notes",
        json={
            "chief_complaint": "Signed note to be withdrawn",
            "subjective": "Subj",
            "objective": "Obj",
            "assessment": "Assess",
            "plan": "Plan",
        },
        headers=auth_header_for(u_doc),
    )
    signed_id = s_res.json()["data"]["id"]
    await client.post(f"/api/v1/soap-notes/{signed_id}/sign", headers=auth_header_for(u_doc))

    # Delete signed -> marked entered-in-error
    del_signed = await client.delete(f"/api/v1/soap-notes/{signed_id}", headers=auth_header_for(u_doc))
    assert del_signed.status_code == 204

    check_signed = await client.get(f"/api/v1/soap-notes/{signed_id}", headers=auth_header_for(u_doc))
    assert check_signed.status_code == 200
    assert check_signed.json()["data"]["status"] == "entered-in-error"
