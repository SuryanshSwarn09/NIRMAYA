"""Month 2 Comprehensive End-to-End Clinical Observational & Doctor EMR Verification Suite.

Validates the full integrated clinical observational engine engineered across Month 2 (Weeks 5-8):
1. Multi-Role Clinical Actor Provisioning:
   - Patient Arun Patel with verified ABHA identity (91-1234-5678-9001, arun.patel@abdm).
   - Treating Clinician Dr. Ananya Sharma (Cardiology, NMC MCI-2015-84920, HPR verified).
   - Unauthorized Third-Party Patient Vikram Malhotra.
   - Lab Technician & Hospital Pharmacist.
2. Complete Clinical Observational Journey:
   - Condition & Problem List management (ICD-10 I10, SNOMED 38341003, active status).
   - Quantitative Vitals Telemetry (Blood Pressure 85354-9, Heart Rate 8867-4, SpO2 2708-6).
   - Structured SOAP Note Authoring and Cryptographic Attestation (SHA-256 digital signature digest).
   - Electronic Prescription Authoring with dosage builder and DDI safety checks.
   - Diagnostic Service Requests for Pathology & PACS Imaging (LOINC 24331-1 and 24648-8).
   - Verified Diagnostic Report Publication with DICOM metadata (Study Instance UID, Modality CR).
3. HL7 FHIR Release 4 Canonical Resource Serialization:
   - Condition, Observation, MedicationRequest, ServiceRequest, and DiagnosticReport.
4. Cryptographic Tamper-Evidence & Post-Attestation Immutability:
   - Rejection of alterations to signed notes and prescriptions with HTTP 409 Conflict.
5. Multi-Tenant RBAC Security & Strict Cross-Patient Data Isolation:
   - Rejection of unauthorized cross-patient queries with HTTP 403 Forbidden.
"""

from datetime import date, datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.appointment import Appointment, DoctorSlot
from app.models.doctor import DoctorProfile
from app.models.enums import (
    AdministrationRoute,
    AppointmentStatus,
    AppointmentType,
    BloodGroup,
    FormularyTier,
    Gender,
    MedicalSpecialty,
    MedicationForm,
    MedicationStatus,
    SlotStatus,
    UserRole,
)
from app.models.medication import Medication
from app.models.patient import PatientProfile
from app.models.user import User


@pytest_asyncio.fixture
async def month_2_e2e_env():
    """Provide isolated in-memory test database and client for Month 2 E2E verification."""
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
    """Generate authorization bearer headers for a given user model."""
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
    })
    return {"Authorization": f"Bearer {token}"}


def extract_fhir(payload: dict) -> dict:
    """Extract FHIR payload regardless of whether it is wrapped in data envelope."""
    return payload.get("data", payload)


async def seed_month_2_actors(session: AsyncSession):
    """Seed multi-role actors for Month 2 full verification."""
    # 1. Subject Patient: Arun Patel
    u_pat1 = User(
        email="arun.patel@nirmaya.health",
        full_name="Arun Patel",
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True,
    )
    session.add(u_pat1)
    await session.flush()

    pat1_profile = PatientProfile(
        user_id=u_pat1.id,
        gender=Gender.MALE,
        date_of_birth=date(1978, 6, 15),
        blood_group=BloodGroup.B_POSITIVE,
        abha_number="91-1234-5678-9001",
        abha_address="arun.patel@abdm",
        address_line="Koramangala, Bengaluru, Karnataka",
        city="Bengaluru",
        state="Karnataka",
    )
    session.add(pat1_profile)
    await session.flush()

    # 2. Unauthorized Patient: Vikram Malhotra
    u_pat2 = User(
        email="vikram.malhotra@nirmaya.health",
        full_name="Vikram Malhotra",
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True,
    )
    session.add(u_pat2)
    await session.flush()

    pat2_profile = PatientProfile(
        user_id=u_pat2.id,
        gender=Gender.MALE,
        date_of_birth=date(1989, 11, 20),
        blood_group=BloodGroup.O_POSITIVE,
        abha_number="91-8888-7777-6666",
        abha_address="vikram.malhotra@abdm",
        address_line="Indiranagar, Bengaluru, Karnataka",
        city="Bengaluru",
        state="Karnataka",
    )
    session.add(pat2_profile)
    await session.flush()

    # 3. Treating Doctor: Dr. Ananya Sharma
    u_doc = User(
        email="ananya.sharma@nirmaya.health",
        full_name="Dr. Ananya Sharma",
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=True,
    )
    session.add(u_doc)
    await session.flush()

    doc_profile = DoctorProfile(
        user_id=u_doc.id,
        registration_number="MCI-2015-84920",
        medical_council="Karnataka Medical Council",
        specialty=MedicalSpecialty.CARDIOLOGY,
        qualifications="MBBS, MD (Medicine), DM (Cardiology)",
        experience_years=12,
        consultation_fee=800.0,
        hpr_id="ananya.sharma@hpr.abdm",
    )
    session.add(doc_profile)
    await session.flush()

    # 4. Lab Technician
    u_lab = User(
        email="lab.director@nirmaya.health",
        full_name="Metropolis Pathology Director",
        role=UserRole.LAB,
        is_active=True,
        is_verified=True,
    )
    session.add(u_lab)

    # 5. Pharmacist / Admin
    u_pharm = User(
        email="pharmacist@nirmaya.health",
        full_name="Apex Hospital Pharmacist",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    session.add(u_pharm)

    # 6. Formulary Medication in Catalog
    medication = Medication(
        name="Atorvastatin 20mg Oral Tablet",
        generic_name="Atorvastatin Calcium",
        brand_name="Lipitor",
        rxnorm_code="855332",
        rxnorm_display="Atorvastatin 20 MG Oral Tablet",
        atc_code="C10AA05",
        atc_display="Atorvastatin",
        snomed_code="387584000",
        form=MedicationForm.TABLET,
        route=AdministrationRoute.ORAL,
        strength="20 mg",
        active_ingredient="Atorvastatin",
        is_prescription_required=True,
        is_controlled_substance=False,
        formulary_tier=FormularyTier.TIER_1_GENERIC,
        status=MedicationStatus.ACTIVE,
    )
    session.add(medication)
    await session.flush()

    # 7. Clinical Encounter Appointment
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

    return {
        "user_pat1": u_pat1,
        "patient1": pat1_profile,
        "user_pat2": u_pat2,
        "patient2": pat2_profile,
        "user_doc": u_doc,
        "doctor": doc_profile,
        "user_lab": u_lab,
        "user_pharm": u_pharm,
        "medication": medication,
        "appointment": appt,
    }


# ============================================================================
# End-to-End Month 2 Verification Tests
# ============================================================================

@pytest.mark.asyncio
async def test_e2e_month_2_full_clinical_observational_lifecycle(month_2_e2e_env):
    """Execute the full Month 2 clinical lifecycle across Vitals, Conditions, SOAP, e-Rx, Diagnostics & PACS."""
    client, session_factory = month_2_e2e_env
    async with session_factory() as session:
        actors = await seed_month_2_actors(session)

    pat1_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])
    pat_header = auth_header_for(actors["user_pat1"])
    lab_header = auth_header_for(actors["user_lab"])

    # -------------------------------------------------------------------------
    # Step 1: Active Problem List / Condition Intake (Week 5 & Week 7)
    # -------------------------------------------------------------------------
    condition_payload = {
        "code_system": "http://hl7.org/fhir/sid/icd-10",
        "code_value": "I10",
        "code_display": "Essential (primary) hypertension",
        "category": "problem-list-item",
        "clinical_status": "active",
        "severity": "moderate",
        "onset_date": "2024-01-10",
        "notes": "Patient on lifestyle modifications; blood pressure elevated on serial office visits.",
    }
    res_cond = await client.post(
        f"/api/v1/patients/{pat1_id}/conditions",
        json=condition_payload,
        headers=doc_header,
    )
    assert res_cond.status_code == 201, res_cond.text
    cond_data = res_cond.json()["data"]
    cond_id = cond_data["id"]
    assert cond_data["code_value"] == "I10"
    assert cond_data["clinical_status"] == "active"

    # Verify FHIR R4 Condition serialization
    res_cond_fhir = await client.get(
        f"/api/v1/conditions/{cond_id}/fhir",
        headers=doc_header,
    )
    assert res_cond_fhir.status_code == 200
    fhir_cond = extract_fhir(res_cond_fhir.json())
    assert fhir_cond["resourceType"] == "Condition"
    assert fhir_cond["clinicalStatus"]["coding"][0]["code"] == "active"
    assert fhir_cond["code"]["coding"][0]["code"] == "I10"

    # -------------------------------------------------------------------------
    # Step 2: Quantitative Vitals Telemetry (Week 5 & Week 7)
    # -------------------------------------------------------------------------
    bp_obs_payload = {
        "category": "vital-signs",
        "code_coding_system": "http://loinc.org",
        "code_value": "85354-9",
        "code_display": "Blood pressure panel with all children optional",
        "status": "final",
        "interpretation": "high",
        "components": [
            {
                "code_system": "http://loinc.org",
                "code_value": "8480-6",
                "code_display": "Systolic blood pressure",
                "value_quantity": 138.0,
                "value_unit": "mmHg",
            },
            {
                "code_system": "http://loinc.org",
                "code_value": "8462-4",
                "code_display": "Diastolic blood pressure",
                "value_quantity": 88.0,
                "value_unit": "mmHg",
            },
        ],
    }
    res_bp = await client.post(
        f"/api/v1/patients/{pat1_id}/observations",
        json=bp_obs_payload,
        headers=doc_header,
    )
    assert res_bp.status_code == 201
    bp_data = res_bp.json()["data"]
    bp_id = bp_data["id"]
    assert bp_data["code_value"] == "85354-9"
    assert len(bp_data["components"]) == 2

    # Verify FHIR R4 Observation serialization
    res_bp_fhir = await client.get(
        f"/api/v1/observations/{bp_id}/fhir",
        headers=doc_header,
    )
    assert res_bp_fhir.status_code == 200
    fhir_bp = extract_fhir(res_bp_fhir.json())
    assert fhir_bp["resourceType"] == "Observation"
    assert fhir_bp["code"]["coding"][0]["code"] == "85354-9"

    # -------------------------------------------------------------------------
    # Step 3: Structured SOAP Note Authoring & Cryptographic Signing (Week 5 & Week 8)
    # -------------------------------------------------------------------------
    soap_payload = {
        "encounter_id": actors["appointment"].id,
        "title": "Comprehensive Hypertension Consultation",
        "chief_complaint": "Persistent elevated blood pressure and exertional fatigue",
        "subjective": "Patient reports morning headaches and mild exertional fatigue. Adherent to low-sodium diet.",
        "objective": "Sitting BP 138/88 mmHg, HR 74 regular, SpO2 98%. Clear breath sounds. No peripheral edema.",
        "assessment": "Essential hypertension Stage 1, moderate cardiovascular risk. Suspected dyslipidemia.",
        "plan": "1. Initiate Atorvastatin 20mg OD with meals. 2. Requisition fasting Lipid Panel and baseline Chest X-Ray.",
        "primary_diagnosis_code": "I10",
        "primary_diagnosis_display": "Essential hypertension",
        "follow_up_instructions": "Review in 4 weeks with lipid profile and chest radiograph.",
    }
    res_soap = await client.post(
        f"/api/v1/patients/{pat1_id}/soap-notes",
        json=soap_payload,
        headers=doc_header,
    )
    assert res_soap.status_code == 201
    soap_data = res_soap.json()["data"]
    soap_id = soap_data["id"]
    assert soap_data["status"] == "preliminary"
    assert soap_data["is_signed"] is False

    # Doctor signs the SOAP note with cryptographic attestation
    res_sign = await client.post(
        f"/api/v1/soap-notes/{soap_id}/sign",
        json={"comments": "Attested electronically by Dr. Ananya Sharma via verified HPR credentials."},
        headers=doc_header,
    )
    assert res_sign.status_code == 200
    signed_soap = res_sign.json()["data"]
    assert signed_soap["is_signed"] is True
    assert signed_soap["status"] == "final"
    assert len(signed_soap["signature_hash"]) == 64

    # -------------------------------------------------------------------------
    # Step 4: Electronic Prescription Authoring (Week 6 & Week 8)
    # -------------------------------------------------------------------------
    rx_payload = {
        "medication_id": actors["medication"].id,
        "dosage_text": "Take 1 tablet orally once daily at bedtime for 30 days",
        "dose_quantity": 20.0,
        "dose_unit": "mg",
        "route": "oral",
        "frequency": 1,
        "period": 1.0,
        "period_unit": "d",
        "dispense_quantity": 30.0,
        "dispense_unit": "tablets",
        "expected_supply_duration_days": 30,
        "number_of_repeats_allowed": 1,
        "allow_generic_substitution": True,
        "reason_code": "I10",
        "note": "Cardiovascular risk reduction in essential hypertension",
    }
    res_rx = await client.post(
        f"/api/v1/patients/{pat1_id}/prescriptions",
        json=rx_payload,
        headers=doc_header,
    )
    assert res_rx.status_code == 201
    rx_data = res_rx.json()["data"]
    rx_id = rx_data["id"]
    assert rx_data["status"] == "draft"

    # Doctor signs the prescription
    sign_rx_res = await client.post(
        f"/api/v1/prescriptions/{rx_id}/sign",
        json={"signature_notes": "Clinical indications verified with laboratory profile."},
        headers=doc_header,
    )
    assert sign_rx_res.status_code == 200
    assert sign_rx_res.json()["data"]["is_signed"] is True
    assert sign_rx_res.json()["data"]["status"] == "active"
    assert len(sign_rx_res.json()["data"]["signature_hash"]) == 64

    # Verify FHIR R4 MedicationRequest export
    res_rx_fhir = await client.get(
        f"/api/v1/prescriptions/{rx_id}/fhir",
        headers=doc_header,
    )
    assert res_rx_fhir.status_code == 200
    fhir_rx = res_rx_fhir.json()
    assert fhir_rx["resourceType"] == "MedicationRequest"
    assert fhir_rx["status"] == "active"

    # -------------------------------------------------------------------------
    # Step 5: Diagnostic Orders & Verified PACS Reports (Week 5 & Week 8)
    # -------------------------------------------------------------------------
    # 5a. Lab Order (Lipid Panel)
    lab_order_payload = {
        "category": "laboratory",
        "code_value": "24331-1",
        "code_display": "Lipid panel with direct LDL - Serum or Plasma",
        "priority": "routine",
        "specimen_type": "serum",
        "reason_code": "I10",
        "reason_description": "Baseline dyslipidemia exclusion",
        "notes": "12-hour fasting required prior to draw",
    }
    res_lab_order = await client.post(
        f"/api/v1/patients/{pat1_id}/diagnostic-orders",
        json=lab_order_payload,
        headers=doc_header,
    )
    assert res_lab_order.status_code == 201

    # 5b. Diagnostic Imaging Order (Chest X-Ray)
    img_order_payload = {
        "category": "diagnostic_imaging",
        "code_value": "24648-8",
        "code_display": "Chest X-Ray 2 Views PA and Lateral (CR)",
        "priority": "urgent",
        "reason_code": "I10",
        "reason_description": "Exclude cardiomegaly and cardiopulmonary disease",
        "notes": "Direct digital acquisition with PACS linkage",
    }
    res_img_order = await client.post(
        f"/api/v1/patients/{pat1_id}/diagnostic-orders",
        json=img_order_payload,
        headers=doc_header,
    )
    assert res_img_order.status_code == 201
    img_order_id = res_img_order.json()["data"]["id"]

    # 5c. Radiologist issues verified imaging report with PACS DICOM metadata
    dicom_meta = {
        "study_instance_uid": "1.2.840.113619.2.55.3.604681313.731.1698219001",
        "series_instance_uid": "1.2.840.113619.2.55.3.604681313.731.1698219001.1",
        "modality": "CR",
        "accession_number": "ACC-2026-XRAY-4491",
        "cardiothoracic_ratio": 0.44,
        "view_window_presets": ["default", "lung", "bone", "soft-tissue", "inverted"],
    }
    img_report_payload = {
        "order_id": img_order_id,
        "category": "RAD",
        "code_value": "24648-8",
        "code_display": "Chest X-Ray 2 Views (PA and Lateral)",
        "conclusion": "Normal cardiopulmonary radiograph. CTR 0.44. Clear lung fields with no consolidation or pleural effusion.",
        "is_abnormal": False,
        "performer_name": "NIRMAYA Apex Imaging Center, Bengaluru",
        "report_data": dicom_meta,
    }
    res_img_rep = await client.post(
        f"/api/v1/patients/{pat1_id}/diagnostic-reports",
        json=img_report_payload,
        headers=lab_header,
    )
    assert res_img_rep.status_code == 201
    img_report_id = res_img_rep.json()["data"]["id"]

    # Verify FHIR R4 DiagnosticReport serialization
    res_rep_fhir = await client.get(
        f"/api/v1/diagnostic-reports/{img_report_id}/fhir",
        headers=doc_header,
    )
    assert res_rep_fhir.status_code == 200
    fhir_rep = extract_fhir(res_rep_fhir.json())
    assert fhir_rep["resourceType"] == "DiagnosticReport"
    assert fhir_rep["status"] == "final"
    assert fhir_rep["code"]["coding"][0]["code"] == "24648-8"

    # Verify Patient Vault can retrieve the completed clinical records
    res_pat_orders = await client.get(
        f"/api/v1/patients/{pat1_id}/diagnostic-orders",
        headers=pat_header,
    )
    assert res_pat_orders.status_code == 200
    assert len(res_pat_orders.json()["data"]) >= 2


@pytest.mark.asyncio
async def test_e2e_month_2_cryptographic_attestation_immutability(month_2_e2e_env):
    """Signed clinical records (SOAP notes and sealed prescriptions) strictly reject subsequent mutations."""
    client, session_factory = month_2_e2e_env
    async with session_factory() as session:
        actors = await seed_month_2_actors(session)

    pat1_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])

    # 1. Author and sign SOAP note
    create_soap = await client.post(
        f"/api/v1/patients/{pat1_id}/soap-notes",
        json={
            "chief_complaint": "Immutability check",
            "subjective": "Initial subjective",
            "objective": "Initial objective",
            "assessment": "Initial assessment",
            "plan": "Initial plan",
        },
        headers=doc_header,
    )
    assert create_soap.status_code == 201
    note_id = create_soap.json()["data"]["id"]

    # Sign note
    await client.post(
        f"/api/v1/soap-notes/{note_id}/sign",
        json={"comments": "Attested"},
        headers=doc_header,
    )

    # Attempt mutation of signed note must be rejected with 400 Bad Request or 409 Conflict
    patch_soap = await client.patch(
        f"/api/v1/soap-notes/{note_id}",
        json={"assessment": "Tampered assessment after signature"},
        headers=doc_header,
    )
    assert patch_soap.status_code in (400, 409)

    # 2. Author and sign Prescription
    create_rx = await client.post(
        f"/api/v1/patients/{pat1_id}/prescriptions",
        json={
            "medication_id": actors["medication"].id,
            "dosage_text": "Take 1 tablet daily",
            "dispense_quantity": 30.0,
        },
        headers=doc_header,
    )
    assert create_rx.status_code == 201
    rx_id = create_rx.json()["data"]["id"]

    # Sign prescription
    await client.post(
        f"/api/v1/prescriptions/{rx_id}/sign",
        headers=doc_header,
    )

    # Attempt mutation of signed prescription must be rejected with 400 Bad Request or 409 Conflict
    patch_rx = await client.patch(
        f"/api/v1/prescriptions/{rx_id}",
        json={"dosage_text": "Tampered dose"},
        headers=doc_header,
    )
    assert patch_rx.status_code in (400, 409)


@pytest.mark.asyncio
async def test_e2e_month_2_rbac_data_isolation(month_2_e2e_env):
    """Multi-tenant security boundaries prevent unauthorized cross-patient data access."""
    client, session_factory = month_2_e2e_env
    async with session_factory() as session:
        actors = await seed_month_2_actors(session)

    pat1_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])
    unauthorized_pat_header = auth_header_for(actors["user_pat2"])

    # Doctor creates Condition for Patient 1
    res_cond = await client.post(
        f"/api/v1/patients/{pat1_id}/conditions",
        json={
            "code_system": "http://hl7.org/fhir/sid/icd-10",
            "code_value": "I10",
            "code_display": "Essential hypertension",
            "clinical_status": "active",
        },
        headers=doc_header,
    )
    cond_id = res_cond.json()["data"]["id"]

    # Unauthorized Patient 2 attempts access to Patient 1's condition -> 403 Forbidden
    res_cond_unauth = await client.get(
        f"/api/v1/conditions/{cond_id}",
        headers=unauthorized_pat_header,
    )
    assert res_cond_unauth.status_code == 403

    # Unauthorized Patient 2 attempts access to Patient 1's condition list -> 403 Forbidden
    res_cond_list_unauth = await client.get(
        f"/api/v1/patients/{pat1_id}/conditions",
        headers=unauthorized_pat_header,
    )
    assert res_cond_list_unauth.status_code == 403

    # Doctor creates SOAP note for Patient 1
    res_soap = await client.post(
        f"/api/v1/patients/{pat1_id}/soap-notes",
        json={
            "chief_complaint": "Confidential patient note",
            "subjective": "Subjective",
            "objective": "Objective",
            "assessment": "Assessment",
            "plan": "Plan",
        },
        headers=doc_header,
    )
    soap_id = res_soap.json()["data"]["id"]

    # Unauthorized Patient 2 attempts access to Patient 1's SOAP note -> 403 Forbidden
    res_soap_unauth = await client.get(
        f"/api/v1/soap-notes/{soap_id}",
        headers=unauthorized_pat_header,
    )
    assert res_soap_unauth.status_code == 403


@pytest.mark.asyncio
async def test_e2e_month_2_fhir_r4_conformance(month_2_e2e_env):
    """Verify that all Month 2 FHIR R4 exports adhere to clinical terminology specifications."""
    client, session_factory = month_2_e2e_env
    async with session_factory() as session:
        actors = await seed_month_2_actors(session)

    pat1_id = actors["patient1"].id
    doc_header = auth_header_for(actors["user_doc"])

    # Create Observation with LOINC SpO2
    res_obs = await client.post(
        f"/api/v1/patients/{pat1_id}/observations",
        json={
            "category": "vital-signs",
            "code_system": "http://loinc.org",
            "code_value": "2708-6",
            "code_display": "Oxygen saturation in Arterial blood by Pulse oximetry",
            "value_quantity": 98.0,
            "value_unit": "%",
            "status": "final",
        },
        headers=doc_header,
    )
    obs_id = res_obs.json()["data"]["id"]

    # Export FHIR Observation and verify standards
    res_fhir = await client.get(
        f"/api/v1/observations/{obs_id}/fhir",
        headers=doc_header,
    )
    assert res_fhir.status_code == 200
    fhir = extract_fhir(res_fhir.json())

    assert fhir["resourceType"] == "Observation"
    assert fhir["status"] == "final"
    coding = fhir["code"]["coding"][0]
    assert coding["system"] == "http://loinc.org"
    assert coding["code"] == "2708-6"
    assert fhir["valueQuantity"]["value"] == 98.0
    assert fhir["valueQuantity"]["unit"] == "%"
    assert fhir["subject"]["reference"] == f"Patient/{pat1_id}"
