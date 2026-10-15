"""Comprehensive unit and integration test suite for HL7 FHIR Release 4

Appointment & Encounter Transformers, Collection Bundles, and ABDM CareContext Linkage.
"""

from datetime import date, datetime, timedelta, timezone
import hashlib
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.fhir.transformers import (
    to_abdm_health_information_artifact,
    to_fhir_appointment,
    to_fhir_encounter,
    to_fhir_encounter_bundle,
    to_fhir_medication,
    to_fhir_medication_dispense,
    to_fhir_medication_request,
)
from app.main import app
from app.models.appointment import Appointment, DoctorSlot
from app.models.doctor import DoctorProfile
from app.models.medication import Medication
from app.models.medication_request import MedicationRequest
from app.models.medication_dispense import MedicationDispense
from app.models.enums import (
    AdministrationRoute,
    AppointmentStatus,
    AppointmentType,
    FormularyTier,
    Gender,
    MedicalSpecialty,
    MedicationForm,
    MedicationStatus,
    MedicationRequestStatus,
    MedicationRequestIntent,
    MedicationRequestPriority,
    MedicationDispenseStatus,
    SlotStatus,
    UserRole,
)
from app.models.patient import PatientProfile
from app.models.user import User


@pytest_asyncio.fixture
async def fhir_test_env():
    """Provide isolated in-memory test database and client for FHIR tests."""
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


async def seed_fhir_fixture(session_factory):
    """Seed test doctor, patient, slot, and clinical appointment records."""
    async with session_factory() as db:
        # 1. Doctor
        doc_user = User(
            email="dr.ananya@nirmaya.health",
            full_name="Dr. Ananya Roy",
            role=UserRole.DOCTOR,
        )
        db.add(doc_user)
        await db.flush()

        doc_profile = DoctorProfile(
            user_id=doc_user.id,
            registration_number="KMC-88219-A",
            medical_council="Karnataka Medical Council",
            specialty=MedicalSpecialty.CARDIOLOGY,
            qualifications="MBBS, MD, DM (Cardiology)",
            experience_years=12,
            consultation_fee=1500,
            hpr_id="ananya.roy@hpr",
        )
        db.add(doc_profile)

        # 2. Patient
        pat_user = User(
            email="rahul.sharma@example.org",
            full_name="Rahul Sharma",
            role=UserRole.PATIENT,
        )
        db.add(pat_user)
        await db.flush()

        pat_profile = PatientProfile(
            user_id=pat_user.id,
            gender=Gender.MALE,
            date_of_birth=date(1988, 6, 15),
            abha_number="91-1122-3344-5566",
            abha_address="rahul88@abdm",
        )
        db.add(pat_profile)

        # 3. Third-party Patient (for RBAC tests)
        other_user = User(
            email="priya.nair@example.org",
            full_name="Priya Nair",
            role=UserRole.PATIENT,
        )
        db.add(other_user)
        await db.flush()

        other_profile = PatientProfile(
            user_id=other_user.id,
            gender=Gender.FEMALE,
            abha_number="91-9988-7766-5544",
        )
        db.add(other_profile)

        # 4. Admin User
        admin_user = User(
            email="admin.clinical@nirmaya.health",
            full_name="Clinical Administrator",
            role=UserRole.ADMIN,
        )
        db.add(admin_user)
        await db.flush()

        # 5. Doctor Slot
        start_time = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)
        end_time = datetime(2026, 10, 15, 10, 30, tzinfo=timezone.utc)
        slot = DoctorSlot(
            doctor_id=doc_profile.id,
            start_time=start_time,
            end_time=end_time,
            status=SlotStatus.BOOKED,
            is_teleconsult=False,
        )
        db.add(slot)
        await db.flush()

        # 6. Appointment
        appt = Appointment(
            patient_id=pat_profile.id,
            doctor_id=doc_profile.id,
            slot_id=slot.id,
            appointment_type=AppointmentType.ROUTINE_CHECKUP,
            status=AppointmentStatus.SCHEDULED,
            scheduled_start=start_time,
            scheduled_end=end_time,
            reason="Chest tightness and dyspnea on exertion",
            clinical_notes="Patient reports mild palpitations over past 2 weeks.",
        )
        db.add(appt)
        await db.commit()

        # Load appointment with joined relations
        await db.refresh(appt)
        await db.refresh(doc_profile)
        await db.refresh(pat_profile)

        return {
            "doctor_user": doc_user,
            "doctor": doc_profile,
            "patient_user": pat_user,
            "patient": pat_profile,
            "other_user": other_user,
            "other_patient": other_profile,
            "admin_user": admin_user,
            "slot": slot,
            "appointment": appt,
        }


# ============================================================================
# Pure Unit Tests: Transformer Logic
# ============================================================================


def test_to_fhir_appointment_mapping() -> None:
    """Verify Appointment ORM entity maps cleanly to HL7 FHIR R4 Appointment resource."""
    # Mock Appointment with related doctor and patient
    user_p = User(id="u-p1", full_name="Arun Kumar", email="arun@example.org", role=UserRole.PATIENT)
    pat = PatientProfile(id="p-1", user_id="u-p1", abha_number="91-0000-0000-0001", abha_address="arun@abdm")
    pat.user = user_p

    user_d = User(id="u-d1", full_name="Dr. Sunita Rao", email="sunita@nirmaya.health", role=UserRole.DOCTOR)
    doc = DoctorProfile(id="d-1", user_id="u-d1", registration_number="MCI-12345", specialty=MedicalSpecialty.CARDIOLOGY)
    doc.user = user_d

    start = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 9, 30, tzinfo=timezone.utc)

    appt = Appointment(
        id="appt-uuid-123",
        patient_id="p-1",
        doctor_id="d-1",
        slot_id="slot-uuid-99",
        appointment_type=AppointmentType.ROUTINE_CHECKUP,
        status=AppointmentStatus.SCHEDULED,
        scheduled_start=start,
        scheduled_end=end,
        reason="Annual cardiac checkup",
        clinical_notes="Bring previous lipid profile reports",
    )
    appt.patient = pat
    appt.doctor = doc

    fhir_appt = to_fhir_appointment(appt)

    assert fhir_appt.resourceType == "Appointment"
    assert fhir_appt.id == "appt-uuid-123"
    assert fhir_appt.status == "booked"
    assert fhir_appt.appointmentType.coding[0].code == "ROUTINE"
    assert fhir_appt.reasonCode[0].text == "Annual cardiac checkup"
    assert fhir_appt.start == start
    assert fhir_appt.end == end
    assert fhir_appt.comment == "Bring previous lipid profile reports"
    assert fhir_appt.slot[0].reference == "Slot/slot-uuid-99"

    # Verify participants
    assert len(fhir_appt.participant) == 2
    pat_part = fhir_appt.participant[0]
    assert pat_part.actor.reference == "Patient/p-1"
    assert pat_part.actor.display == "Arun Kumar"
    assert pat_part.type[0].coding[0].code == "SBJ"

    doc_part = fhir_appt.participant[1]
    assert doc_part.actor.reference == "Practitioner/d-1"
    assert doc_part.actor.display == "Dr. Sunita Rao"
    assert doc_part.type[0].coding[0].code == "PPRF"


def test_to_fhir_appointment_all_statuses() -> None:
    """Verify all NIRMAYA AppointmentStatus enums map to valid FHIR R4 appointment statuses."""
    status_expectations = {
        AppointmentStatus.SCHEDULED: "booked",
        AppointmentStatus.CONFIRMED: "booked",
        AppointmentStatus.IN_PROGRESS: "arrived",
        AppointmentStatus.COMPLETED: "fulfilled",
        AppointmentStatus.CANCELLED: "cancelled",
        AppointmentStatus.NO_SHOW: "noshow",
    }

    start = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 9, 30, tzinfo=timezone.utc)

    for nirmaya_st, expected_fhir_st in status_expectations.items():
        appt = Appointment(
            id=f"appt-{nirmaya_st.value}",
            patient_id="p-1",
            doctor_id="d-1",
            appointment_type=AppointmentType.ROUTINE_CHECKUP,
            status=nirmaya_st,
            scheduled_start=start,
            scheduled_end=end,
        )
        fhir_appt = to_fhir_appointment(appt)
        assert fhir_appt.status == expected_fhir_st


def test_to_fhir_encounter_mapping_ambulatory_and_virtual() -> None:
    """Verify Encounter resource maps status, ambulatory class, and virtual class."""
    start = datetime(2026, 11, 1, 14, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 14, 30, tzinfo=timezone.utc)

    # Ambulatory (in-person)
    appt_amb = Appointment(
        id="appt-amb-1",
        patient_id="p-1",
        doctor_id="d-1",
        appointment_type=AppointmentType.FOLLOW_UP,
        status=AppointmentStatus.COMPLETED,
        scheduled_start=start,
        scheduled_end=end,
        reason="Follow-up ECG review",
    )
    enc_amb = to_fhir_encounter(appt_amb)
    assert enc_amb.resourceType == "Encounter"
    assert enc_amb.status == "finished"
    assert enc_amb.class_.code == "AMB"
    assert enc_amb.class_.display == "Ambulatory"
    assert enc_amb.appointment[0].reference == "Appointment/appt-amb-1"
    assert enc_amb.period.start == start

    # Virtual (teleconsultation)
    appt_vr = Appointment(
        id="appt-vr-1",
        patient_id="p-1",
        doctor_id="d-1",
        appointment_type=AppointmentType.TELECONSULTATION,
        status=AppointmentStatus.IN_PROGRESS,
        scheduled_start=start,
        scheduled_end=end,
        reason="Virtual follow-up",
    )
    enc_vr = to_fhir_encounter(appt_vr)
    assert enc_vr.status == "in-progress"
    assert enc_vr.class_.code == "VR"
    assert enc_vr.class_.display == "Virtual"


def test_to_fhir_encounter_all_statuses() -> None:
    """Verify all NIRMAYA AppointmentStatus enums map to valid FHIR R4 encounter statuses."""
    status_expectations = {
        AppointmentStatus.SCHEDULED: "planned",
        AppointmentStatus.CONFIRMED: "planned",
        AppointmentStatus.IN_PROGRESS: "in-progress",
        AppointmentStatus.COMPLETED: "finished",
        AppointmentStatus.CANCELLED: "cancelled",
        AppointmentStatus.NO_SHOW: "entered-in-error",
    }

    start = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 9, 30, tzinfo=timezone.utc)

    for nirmaya_st, expected_enc_st in status_expectations.items():
        appt = Appointment(
            id=f"appt-enc-{nirmaya_st.value}",
            patient_id="p-1",
            doctor_id="d-1",
            appointment_type=AppointmentType.ROUTINE_CHECKUP,
            status=nirmaya_st,
            scheduled_start=start,
            scheduled_end=end,
        )
        enc = to_fhir_encounter(appt)
        assert enc.status == expected_enc_st


def test_to_fhir_encounter_bundle() -> None:
    """Verify multi-resource collection bundle wraps Appointment, Encounter, Patient, and Practitioner."""
    user_p = User(id="u-p1", full_name="Meera Sen", email="meera@example.org")
    pat = PatientProfile(id="p-1", user_id="u-p1", abha_number="91-4455-6677-8899", gender=Gender.FEMALE)
    pat.user = user_p

    user_d = User(id="u-d1", full_name="Dr. K. V. Raman", email="raman@nirmaya.health")
    doc = DoctorProfile(id="d-1", user_id="u-d1", registration_number="TNMC-99001", specialty=MedicalSpecialty.DERMATOLOGY)
    doc.user = user_d

    start = datetime(2026, 11, 2, 11, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 2, 11, 30, tzinfo=timezone.utc)

    appt = Appointment(
        id="appt-bundle-1",
        patient_id="p-1",
        doctor_id="d-1",
        appointment_type=AppointmentType.ROUTINE_CHECKUP,
        status=AppointmentStatus.SCHEDULED,
        scheduled_start=start,
        scheduled_end=end,
    )
    appt.patient = pat
    appt.doctor = doc

    bundle = to_fhir_encounter_bundle(appt)

    assert bundle.resourceType == "Bundle"
    assert bundle.type == "collection"
    assert bundle.total == 4
    assert len(bundle.entry) == 4

    types = [e.resource["resourceType"] for e in bundle.entry]
    assert types == ["Appointment", "Encounter", "Patient", "Practitioner"]

    # Verify Patient ABHA in bundle
    patient_entry = bundle.entry[2].resource
    assert patient_entry["identifier"][0]["value"] == "91-4455-6677-8899"

    # Verify Practitioner registration in bundle
    doc_entry = bundle.entry[3].resource
    assert doc_entry["identifier"][0]["value"] == "TNMC-99001"


def test_to_abdm_health_information_artifact() -> None:
    """Verify ABDM CareContext generation, SHA-256 signature, and bundle integration."""
    user_p = User(id="u-p1", full_name="Devika Pillai")
    pat = PatientProfile(id="p-1", user_id="u-p1", abha_number="91-0000-1111-2222")
    pat.user = user_p

    user_d = User(id="u-d1", full_name="Dr. Rajesh Varma")
    doc = DoctorProfile(id="d-1", user_id="u-d1", registration_number="DMC-33445", specialty=MedicalSpecialty.GENERAL_MEDICINE)
    doc.user = user_d

    appt = Appointment(
        id="f3b145a2-9988-410a-84fb-272cfc991500",
        patient_id="p-1",
        doctor_id="d-1",
        appointment_type=AppointmentType.ROUTINE_CHECKUP,
        status=AppointmentStatus.COMPLETED,
        scheduled_start=datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 11, 3, 10, 30, tzinfo=timezone.utc),
    )
    appt.patient = pat
    appt.doctor = doc

    artifact = to_abdm_health_information_artifact(appt, hip_id="IN010000042")

    assert artifact.careContextReference == "APPT-F3B145A2"
    assert artifact.patientReference == "91-0000-1111-2222"
    assert artifact.hiType == "OPConsultation"
    assert artifact.hipId == "IN010000042"
    assert len(artifact.signature) == 64  # SHA-256 hex string

    # Verify signature matches bundle payload
    bundle_bytes = artifact.bundle.model_dump_json(by_alias=True).encode("utf-8")
    expected_sig = hashlib.sha256(bundle_bytes).hexdigest()
    assert artifact.signature == expected_sig


# ============================================================================
# Integration Tests: FastAPI Endpoints & RBAC Authorization
# ============================================================================


@pytest.mark.asyncio
async def test_api_get_appointment_fhir(fhir_test_env) -> None:
    """Verify GET /api/v1/appointments/{id}/fhir returns valid FHIR Appointment resource."""
    client, session_factory = fhir_test_env
    fixture = await seed_fhir_fixture(session_factory)
    appt = fixture["appointment"]
    patient_user = fixture["patient_user"]

    res = await client.get(
        f"/api/v1/appointments/{appt.id}/fhir",
        headers=auth_header_for(patient_user),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    fhir_data = body["data"]
    assert fhir_data["resourceType"] == "Appointment"
    assert fhir_data["id"] == appt.id
    assert fhir_data["status"] == "booked"
    assert fhir_data["appointmentType"]["coding"][0]["code"] == "ROUTINE"
    assert len(fhir_data["participant"]) == 2


@pytest.mark.asyncio
async def test_api_get_encounter_fhir(fhir_test_env) -> None:
    """Verify GET /api/v1/appointments/{id}/encounter returns valid FHIR Encounter resource."""
    client, session_factory = fhir_test_env
    fixture = await seed_fhir_fixture(session_factory)
    appt = fixture["appointment"]
    doctor_user = fixture["doctor_user"]

    res = await client.get(
        f"/api/v1/appointments/{appt.id}/encounter",
        headers=auth_header_for(doctor_user),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    enc_data = body["data"]
    assert enc_data["resourceType"] == "Encounter"
    assert enc_data["status"] == "planned"
    assert enc_data["class"]["code"] == "AMB"
    assert enc_data["subject"]["reference"] == f"Patient/{fixture['patient'].id}"


@pytest.mark.asyncio
async def test_api_get_encounter_bundle_fhir(fhir_test_env) -> None:
    """Verify GET /api/v1/appointments/{id}/fhir-bundle returns full Collection Bundle."""
    client, session_factory = fhir_test_env
    fixture = await seed_fhir_fixture(session_factory)
    appt = fixture["appointment"]
    patient_user = fixture["patient_user"]

    res = await client.get(
        f"/api/v1/appointments/{appt.id}/fhir-bundle",
        headers=auth_header_for(patient_user),
    )
    assert res.status_code == 200
    bundle = res.json()["data"]
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert bundle["total"] == 4
    assert len(bundle["entry"]) == 4


@pytest.mark.asyncio
async def test_api_link_abdm_consent(fhir_test_env) -> None:
    """Verify POST /api/v1/appointments/{id}/abdm/link-consent returns signed HI artifact."""
    client, session_factory = fhir_test_env
    fixture = await seed_fhir_fixture(session_factory)
    appt = fixture["appointment"]
    patient_user = fixture["patient_user"]

    link_payload = {
        "hip_id": "IN010000099",
        "consent_artifact_id": "consent-uuid-889900",
    }
    res = await client.post(
        f"/api/v1/appointments/{appt.id}/abdm/link-consent",
        json=link_payload,
        headers=auth_header_for(patient_user),
    )
    assert res.status_code == 200
    artifact = res.json()["data"]
    assert artifact["careContextReference"].startswith("APPT-")
    assert artifact["patientReference"] == "91-1122-3344-5566"
    assert artifact["hipId"] == "IN010000099"
    assert artifact["consentArtifactId"] == "consent-uuid-889900"
    assert len(artifact["signature"]) == 64
    assert artifact["bundle"]["resourceType"] == "Bundle"


@pytest.mark.asyncio
async def test_api_fhir_access_control_guards(fhir_test_env) -> None:
    """Verify unauthorized patient receives 403 Forbidden, but Admin is allowed."""
    client, session_factory = fhir_test_env
    fixture = await seed_fhir_fixture(session_factory)
    appt = fixture["appointment"]
    unauthorized_patient = fixture["other_user"]
    admin_user = fixture["admin_user"]

    # 1. Unauthorized patient receives 403
    for path in [f"/api/v1/appointments/{appt.id}/fhir", f"/api/v1/appointments/{appt.id}/encounter", f"/api/v1/appointments/{appt.id}/fhir-bundle"]:
        res = await client.get(path, headers=auth_header_for(unauthorized_patient))
        assert res.status_code == 403

    # 2. Admin can access
    admin_res = await client.get(
        f"/api/v1/appointments/{appt.id}/fhir-bundle",
        headers=auth_header_for(admin_user),
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["data"]["resourceType"] == "Bundle"


def test_to_fhir_medication_transformer() -> None:
    """Verify bidirectional serialization of Medication model into FHIR R4 Medication."""
    med = Medication(
        id="med-metformin-500",
        name="Metformin 500mg Oral Tablet",
        generic_name="Metformin Hydrochloride",
        brand_name="Glucophage",
        rxnorm_code="860975",
        rxnorm_display="Metformin hydrochloride 500 MG Oral Tablet",
        atc_code="A10BA02",
        atc_display="Metformin",
        snomed_code="387048002",
        snomed_display="Metformin hydrochloride",
        form=MedicationForm.TABLET,
        route=AdministrationRoute.ORAL,
        strength="500 mg",
        active_ingredient="Metformin",
        is_prescription_required=True,
        is_controlled_substance=False,
        formulary_tier=FormularyTier.TIER_1_GENERIC,
        status=MedicationStatus.ACTIVE,
    )

    fhir_med = to_fhir_medication(med)

    assert fhir_med.resourceType == "Medication"
    assert fhir_med.id == "med-metformin-500"
    assert fhir_med.status == "active"
    assert len(fhir_med.identifier) == 2
    assert fhir_med.identifier[0].value == "med-metformin-500"
    assert fhir_med.identifier[1].value == "860975"
    assert fhir_med.code.text == "Metformin 500mg Oral Tablet"

    systems = {coding.system for coding in fhir_med.code.coding}
    assert "http://www.nlm.nih.gov/research/umls/rxnorm" in systems
    assert "http://www.whocc.no/atc" in systems
    assert "http://snomed.info/sct" in systems

    assert fhir_med.form is not None
    assert fhir_med.form.text == "Tablet"

    assert fhir_med.ingredient is not None
    assert len(fhir_med.ingredient) == 1
    assert fhir_med.ingredient[0].itemCodeableConcept.text == "Metformin"
    assert fhir_med.ingredient[0].strength["text"] == "500 mg"


def test_to_fhir_medication_request_transformer() -> None:
    """Verify bidirectional serialization of MedicationRequest into FHIR R4 MedicationRequest."""
    med = Medication(
        id="med-atorvastatin-20",
        name="Atorvastatin 20mg Oral Tablet",
        generic_name="Atorvastatin Calcium",
        brand_name="Lipitor",
        rxnorm_code="855332",
        rxnorm_display="Atorvastatin 20 MG Oral Tablet",
        atc_code="C10AA05",
        snomed_code="387584000",
        form=MedicationForm.TABLET,
        route=AdministrationRoute.ORAL,
        strength="20 mg",
        active_ingredient="Atorvastatin",
        is_prescription_required=True,
        formulary_tier=FormularyTier.TIER_1_GENERIC,
        status=MedicationStatus.ACTIVE,
    )

    rx = MedicationRequest(
        id="rx-test-001",
        patient_id="pat-arun-patel",
        doctor_id="doc-ananya-sharma",
        encounter_id="appt-encounter-101",
        medication_id=med.id,
        status=MedicationRequestStatus.ACTIVE,
        intent=MedicationRequestIntent.ORDER,
        priority=MedicationRequestPriority.ROUTINE,
        dosage_text="Take 1 tablet orally once daily at bedtime for 30 days",
        dose_quantity=20.0,
        dose_unit="mg",
        route=AdministrationRoute.ORAL,
        frequency=1,
        period=1.0,
        period_unit="d",
        as_needed=False,
        additional_instructions="Take at bedtime. Avoid grapefruit juice.",
        dispense_quantity=30.0,
        dispense_unit="tablets",
        expected_supply_duration_days=30,
        number_of_repeats_allowed=1,
        validity_period_start=datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc),
        validity_period_end=datetime(2026, 11, 14, 10, 0, tzinfo=timezone.utc),
        allow_generic_substitution=True,
        reason_code="I10",
        reason_reference_id="cond-htn-001",
        note="Primary prevention of cardiovascular events in hypertensive patient.",
        authored_on=datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc),
        is_signed=True,
        signed_at=datetime(2026, 10, 14, 10, 5, tzinfo=timezone.utc),
        signature_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )

    fhir_rx = to_fhir_medication_request(rx, medication=med)

    assert fhir_rx.resourceType == "MedicationRequest"
    assert fhir_rx.id == "rx-test-001"
    assert fhir_rx.status == "active"
    assert fhir_rx.intent == "order"
    assert fhir_rx.priority == "routine"
    assert fhir_rx.meta is not None
    assert "https://nrces.in/ndhm/fhir/r4/StructureDefinition/Prescription" in fhir_rx.meta["profile"]

    # Identifier check
    id_values = [i.value for i in fhir_rx.identifier]
    assert "rx-test-001" in id_values
    assert "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" in id_values

    # Subject & Requester
    assert fhir_rx.subject.reference == "Patient/pat-arun-patel"
    assert fhir_rx.requester.reference == "Practitioner/doc-ananya-sharma"
    assert fhir_rx.encounter.reference == "Encounter/appt-encounter-101"

    # Medication references and codings
    assert fhir_rx.medicationReference.reference == "Medication/med-atorvastatin-20"
    systems = {coding.system for coding in fhir_rx.medicationCodeableConcept.coding}
    assert "http://www.nlm.nih.gov/research/umls/rxnorm" in systems
    assert "http://www.whocc.no/atc" in systems
    assert "http://snomed.info/sct" in systems

    # Dosage Instruction
    assert len(fhir_rx.dosageInstruction) == 1
    dosage = fhir_rx.dosageInstruction[0]
    assert dosage.text == "Take 1 tablet orally once daily at bedtime for 30 days"
    assert dosage.timing["repeat"]["frequency"] == 1
    assert dosage.asNeededBoolean is False
    assert dosage.route.text == "Oral"
    assert dosage.doseAndRate[0]["doseQuantity"]["value"] == 20.0
    assert dosage.doseAndRate[0]["doseQuantity"]["unit"] == "mg"
    assert dosage.additionalInstruction[0].text == "Take at bedtime. Avoid grapefruit juice."

    # Dispense Request
    assert fhir_rx.dispenseRequest is not None
    assert fhir_rx.dispenseRequest.numberOfRepeatsAllowed == 1
    assert fhir_rx.dispenseRequest.quantity["value"] == 30.0
    assert fhir_rx.dispenseRequest.quantity["unit"] == "tablets"
    assert fhir_rx.dispenseRequest.expectedSupplyDuration["value"] == 30

    # Substitution & Reason
    assert fhir_rx.substitution.allowedBoolean is True
    assert fhir_rx.reasonCode[0].text == "I10"
    assert fhir_rx.reasonReference[0].reference == "Condition/cond-htn-001"
    assert fhir_rx.note[0].text == "Primary prevention of cardiovascular events in hypertensive patient."


def test_to_fhir_medication_dispense_transformer():
    """Test transformation of MedicationDispense relational entity into HL7 FHIR R4 MedicationDispense."""
    med = Medication(
        id="med-atorvastatin-20",
        name="Atorvastatin 20mg",
        generic_name="Atorvastatin Calcium",
        brand_name="Lipitor",
        rxnorm_code="859088",
        rxnorm_display="Atorvastatin 20 MG Oral Tablet",
        atc_code="C10AA05",
        atc_display="atorvastatin",
        snomed_code="387584000",
        snomed_display="Atorvastatin-containing product",
        form=MedicationForm.TABLET,
        strength="20 mg",
        active_ingredient="Atorvastatin Calcium",
        status=MedicationStatus.ACTIVE,
    )

    rx = MedicationRequest(
        id="rx-test-001",
        patient_id="pat-arun-patel",
        doctor_id="doc-ananya-sharma",
        encounter_id="appt-encounter-101",
        medication_id="med-atorvastatin-20",
        status=MedicationRequestStatus.ACTIVE,
        intent=MedicationRequestIntent.ORDER,
        priority=MedicationRequestPriority.ROUTINE,
        dosage_text="Take 1 tablet orally once daily at bedtime for 30 days",
    )

    dispense = MedicationDispense(
        id="disp-test-001",
        dispense_number="DISP-2026-00001",
        prescription_id="rx-test-001",
        patient_id="pat-arun-patel",
        medication_id="med-atorvastatin-20",
        dispenser_id="usr-pharm-01",
        status=MedicationDispenseStatus.COMPLETED,
        quantity_dispensed=30.0,
        dispense_unit="tablets",
        days_supply=30,
        lot_number="LOT-2026-A1",
        expiration_date=date(2027, 6, 30),
        when_prepared=datetime(2026, 10, 15, 8, 30, tzinfo=timezone.utc),
        when_handed_over=datetime(2026, 10, 15, 9, 0, tzinfo=timezone.utc),
        was_substituted=True,
        substitution_type="G",
        substitution_reason="Formulary generic equivalent supplied",
        dosage_instruction="Take 1 tablet orally once daily at bedtime with water",
        pharmacist_notes="Verified against DDI safety checks; patient counseled.",
    )

    fhir_dispense = to_fhir_medication_dispense(dispense, medication=med, prescription=rx)

    assert fhir_dispense.resourceType == "MedicationDispense"
    assert fhir_dispense.id == "disp-test-001"
    assert fhir_dispense.status == "completed"
    assert fhir_dispense.meta is not None
    assert "https://nrces.in/ndhm/fhir/r4/StructureDefinition/MedicationDispense" in fhir_dispense.meta["profile"]

    # Identifiers
    id_vals = [i.value for i in fhir_dispense.identifier]
    assert "DISP-2026-00001" in id_vals
    assert "disp-test-001" in id_vals

    # Authorizing prescription & Subject & Performer
    assert fhir_dispense.authorizingPrescription[0].reference == "MedicationRequest/rx-test-001"
    assert fhir_dispense.subject.reference == "Patient/pat-arun-patel"
    assert fhir_dispense.performer[0].actor.reference == "Practitioner/usr-pharm-01"

    # Quantities & Days Supply
    assert fhir_dispense.quantity["value"] == 30.0
    assert fhir_dispense.quantity["unit"] == "tablets"
    assert fhir_dispense.daysSupply["value"] == 30
    assert fhir_dispense.daysSupply["unit"] == "days"

    # Batch Tracking
    assert fhir_dispense.lotNumber == "LOT-2026-A1"
    assert fhir_dispense.expirationDate == "2027-06-30"

    # Substitution
    assert fhir_dispense.substitution.wasSubstituted is True
    assert fhir_dispense.substitution.type.coding[0].code == "G"
    assert fhir_dispense.substitution.reason[0].text == "Formulary generic equivalent supplied"

    # Dosage & Notes
    assert fhir_dispense.dosageInstruction[0].text == "Take 1 tablet orally once daily at bedtime with water"
    assert fhir_dispense.note[0].text == "Verified against DDI safety checks; patient counseled."



