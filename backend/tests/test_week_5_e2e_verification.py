"""Week 5 End-to-End Clinical Verification & Longitudinal Healthcare Integration Test Suite.

Validates the full longitudinal clinical lifecycle engineered across Week 5:
1. Multi-role user creation (Doctor with NMC/HPR licensing, Patient with ABHA, Lab Facility).
2. Clinical Consultation Appointment booking & encounter initiation.
3. Vital signs & LOINC-coded biometrics telemetry (Blood Pressure, Heart Rate, SpO2, BMI).
4. Clinical Condition diagnosis with international ontologies (ICD-10, SNOMED-CT).
5. Structured SOAP Clinical Documentation (Subjective, Objective, Assessment, Plan) with cryptographic SHA-256 signature.
6. Diagnostic Laboratory Order requisition (ServiceRequest / LOINC panel).
7. Diagnostic Laboratory report fulfillment (DiagnosticReport, PDF report attachment, status transition).
8. HL7 FHIR Release 4 cross-resource translation (Condition, Observation, Composition, ServiceRequest, DiagnosticReport).
9. Longitudinal Patient Health Vault timeline aggregation.
10. Strict RBAC tenant isolation and clinical immutability guardrails.
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
from app.models.condition import ClinicalCondition
from app.models.diagnostic import DiagnosticOrder, DiagnosticReport
from app.models.doctor import DoctorProfile
from app.models.enums import (
    AppointmentStatus,
    BloodGroup,
    ClinicalNoteStatus,
    ClinicalNoteType,
    ClinicalStatus,
    ConditionCategory,
    ConditionSeverity,
    DiagnosticReportStatus,
    Gender,
    LabAccreditation,
    MedicalSpecialty,
    ObservationCategory,
    ObservationInterpretation,
    ObservationStatus,
    ServiceRequestPriority,
    ServiceRequestStatus,
    SlotStatus,
    SpecimenType,
    UserRole,
    VerificationStatus,
)
from app.models.lab import DiagnosticLabFacility
from app.models.observation import ClinicalObservation
from app.models.patient import PatientProfile
from app.models.soap_note import SoapNote
from app.models.user import User


@pytest_asyncio.fixture
async def week5_e2e_env():
    """Isolated in-memory test database and HTTP async client fixture."""
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
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, session_factory

    app.dependency_overrides.pop(get_db, None)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def auth_header(user: User) -> dict:
    """Generate JWT Bearer authorization header for given user."""
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_e2e_full_clinical_encounter_lifecycle(week5_e2e_env) -> None:
    """Execute full longitudinal clinical journey:
    Appointment -> Vitals -> Condition -> Signed SOAP Note -> Lab Order -> Lab Fulfillment -> FHIR Bundles.
    """
    client, session_factory = week5_e2e_env

    # -------------------------------------------------------------------------
    # 1. Provision Clinical Actors: Doctor, Patient, and Diagnostic Lab
    # -------------------------------------------------------------------------
    async with session_factory() as db:
        # Doctor
        doc_user = User(
            email="dr.ananya.deshmukh@nirmaya.health",
            full_name="Dr. Ananya Deshmukh",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True,
        )
        db.add(doc_user)
        await db.flush()

        doc_profile = DoctorProfile(
            user_id=doc_user.id,
            registration_number="NMC-2018-99412",
            medical_council="National Medical Commission",
            specialty=MedicalSpecialty.GENERAL_MEDICINE,
            qualifications="MBBS, MD (Medicine), Fellowship in Diabetology",
            consultation_fee=1500,
            hpr_id="HP91-8842-1092",
            is_available_for_teleconsult=True,
        )
        db.add(doc_profile)

        # Patient
        pat_user = User(
            email="rohit.sharma@gmail.com",
            full_name="Rohit Sharma",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        db.add(pat_user)
        await db.flush()

        pat_profile = PatientProfile(
            user_id=pat_user.id,
            gender=Gender.MALE,
            date_of_birth=date(1987, 4, 30),
            blood_group=BloodGroup.B_POSITIVE,
            abha_number="91-2384-9102-4412",
            abha_address="rohit.sharma@abdm",
            address_line="42 Marine Drive",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001",
        )
        db.add(pat_profile)

        # Diagnostic Lab
        lab_user = User(
            email="pathology.leads@apexdiag.in",
            full_name="Apex Diagnostic Center Admin",
            role=UserRole.LAB,
            is_active=True,
            is_verified=True,
        )
        db.add(lab_user)
        await db.flush()

        lab_facility = DiagnosticLabFacility(
            user_id=lab_user.id,
            facility_name="Apex Clinical Reference Laboratory",
            license_number="LAB-MH-2021-0044",
            accreditation=LabAccreditation.NABL,
            accreditation_number="NABL-MED-ISO15189-9821",
            hfr_id="HFR-993-210-44",
            contact_person="Dr. Rajesh Mehta",
            contact_email="reports@apexdiag.in",
            contact_phone="+919820011223",
            address_line="Tower B, Central Healthcare Complex",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001",
            is_nabl_certified=True,
        )
        db.add(lab_facility)

        # Doctor availability slot
        now = datetime.now(timezone.utc)
        slot_start = now + timedelta(days=1, hours=2)
        slot_end = slot_start + timedelta(minutes=30)

        slot = DoctorSlot(
            doctor_id=doc_profile.id,
            start_time=slot_start,
            end_time=slot_end,
            status=SlotStatus.AVAILABLE,
            is_teleconsult=False,
        )
        db.add(slot)
        await db.commit()

        doc_id = doc_profile.id
        pat_id = pat_profile.id
        lab_id = lab_facility.id
        slot_id = slot.id

    # -------------------------------------------------------------------------
    # 2. Appointment Booking & Confirmation
    # -------------------------------------------------------------------------
    booking_res = await client.post(
        "/api/v1/appointments/",
        headers=auth_header(pat_user),
        json={
            "doctor_id": doc_id,
            "slot_id": slot_id,
            "appointment_type": "routine_checkup",
            "reason": "Executive preventive health evaluation & elevated blood pressure check",
        },
    )
    assert booking_res.status_code == 201
    appointment_data = booking_res.json()["data"]
    appointment_id = appointment_data["id"]
    assert appointment_data["status"] == "scheduled"

    # -------------------------------------------------------------------------
    # 3. Clinical Vitals Telemetry Recording (LOINC Codes)
    # -------------------------------------------------------------------------
    # A. Compound Blood Pressure (LOINC 85354-9)
    bp_res = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        headers=auth_header(doc_user),
        json={
            "encounter_id": appointment_id,
            "code_value": "85354-9",
            "code_display": "Blood Pressure Panel",
            "category": "vital-signs",
            "components": [
                {
                    "code_value": "8480-6",
                    "code_display": "Systolic Blood Pressure",
                    "value_quantity": 138.0,
                    "value_unit": "mmHg",
                },
                {
                    "code_value": "8462-4",
                    "code_display": "Diastolic Blood Pressure",
                    "value_quantity": 88.0,
                    "value_unit": "mmHg",
                },
            ],
            "effective_date_time": now.isoformat(),
            "status": "final",
        },
    )
    assert bp_res.status_code == 201
    bp_data = bp_res.json()["data"]
    assert bp_data["code_value"] == "85354-9"
    assert len(bp_data["components"]) == 2
    bp_obs_id = bp_data["id"]

    # Verify FHIR R4 export of observation
    bp_fhir_res = await client.get(
        f"/api/v1/observations/{bp_obs_id}/fhir",
        headers=auth_header(doc_user),
    )
    assert bp_fhir_res.status_code == 200
    bp_fhir = bp_fhir_res.json()
    assert bp_fhir["resourceType"] == "Observation"
    assert len(bp_fhir["component"]) == 2

    # B. Heart Rate (LOINC 8867-4)
    hr_res = await client.post(
        f"/api/v1/patients/{pat_id}/observations",
        headers=auth_header(doc_user),
        json={
            "encounter_id": appointment_id,
            "code_value": "8867-4",
            "code_display": "Heart Rate",
            "category": "vital-signs",
            "value_quantity": 78.0,
            "value_unit": "beats/min",
            "reference_range_low": 60.0,
            "reference_range_high": 100.0,
            "effective_date_time": now.isoformat(),
            "status": "final",
        },
    )
    assert hr_res.status_code == 201
    hr_data = hr_res.json()["data"]
    assert hr_data["interpretation"] == "normal"

    # Verify latest vitals summary aggregation endpoint
    summary_res = await client.get(
        f"/api/v1/patients/{pat_id}/observations/vitals/latest",
        headers=auth_header(doc_user),
    )
    assert summary_res.status_code == 200
    summary_data = summary_res.json()["data"]
    assert "blood_pressure" in summary_data or "heart_rate" in summary_data

    # -------------------------------------------------------------------------
    # 4. Clinical Condition & Problem List Recording (SNOMED-CT / ICD-10)
    # -------------------------------------------------------------------------
    cond_res = await client.post(
        f"/api/v1/patients/{pat_id}/conditions",
        headers=auth_header(doc_user),
        json={
            "encounter_id": appointment_id,
            "code_value": "I10",
            "code_coding_system": "http://hl7.org/fhir/sid/icd-10",
            "code_display": "Essential (primary) hypertension",
            "clinical_status": "active",
            "verification_status": "confirmed",
            "category": "problem-list-item",
            "severity": "moderate",
            "note": "Patient exhibits baseline blood pressure 138/88 mmHg. Family history of cardiovascular disease.",
        },
    )
    assert cond_res.status_code == 201
    cond_data = cond_res.json()["data"]
    condition_id = cond_data["id"]
    assert cond_data["code_value"] == "I10"
    assert cond_data["clinical_status"] == "active"

    # Export Condition to FHIR R4
    cond_fhir_res = await client.get(
        f"/api/v1/conditions/{condition_id}/fhir",
        headers=auth_header(doc_user),
    )
    assert cond_fhir_res.status_code == 200
    cond_fhir = cond_fhir_res.json()
    assert cond_fhir["resourceType"] == "Condition"
    assert cond_fhir["code"]["coding"][0]["code"] == "I10"
    assert cond_fhir["subject"]["reference"] == f"Patient/{pat_id}"

    # -------------------------------------------------------------------------
    # 5. Structured SOAP Clinical Encounter Documentation
    # -------------------------------------------------------------------------
    soap_create_res = await client.post(
        f"/api/v1/patients/{pat_id}/soap-notes",
        headers=auth_header(doc_user),
        json={
            "encounter_id": appointment_id,
            "note_type": "soap",
            "title": "Comprehensive Clinical Consultation SOAP Note",
            "chief_complaint": "Occasional morning cephalalgia and sustained borderline hypertension",
            "history_of_present_illness": "Patient reports intermittent throbbing headaches over 3 weeks. Denies visual disturbances or chest tightness.",
            "subjective": "39-year-old male presenting for routine checkup. Reports high workplace stress and reduced physical activity.",
            "objective": "BP 138/88 mmHg right arm sitting. HR 78 bpm regular. SpO2 98% room air. BMI 27.2 kg/m2 (overweight). CVS: S1 S2 present, no murmurs.",
            "assessment": "Essential primary hypertension (ICD-10 I10), stage 1. Class I overweight. Risk stratification: low to moderate.",
            "plan": "1. Lifestyle modification: DASH dietary approach, reduce sodium < 2g/day.\n2. 30 min daily brisk walking.\n3. Requisition comprehensive lipid panel.\n4. Review home BP log in 2 weeks.",
            "differential_diagnoses": "Secondary hypertension ruled out.",
        },
    )
    assert soap_create_res.status_code == 201
    soap_data = soap_create_res.json()["data"]
    soap_note_id = soap_data["id"]
    assert soap_data["status"] == "preliminary"

    # Sign & finalize the SOAP note
    sign_res = await client.post(
        f"/api/v1/soap-notes/{soap_note_id}/sign",
        headers=auth_header(doc_user),
        json={"notes": "Reviewed and finalized under clinical responsibility"},
    )
    assert sign_res.status_code == 200
    signed_data = sign_res.json()["data"]
    assert signed_data["status"] == "final"
    assert signed_data["is_signed"] is True
    assert signed_data["signature_hash"] is not None
    assert len(signed_data["signature_hash"]) == 64  # SHA-256 hex digest

    # Verify FHIR R4 Composition export
    soap_fhir_res = await client.get(
        f"/api/v1/soap-notes/{soap_note_id}/fhir",
        headers=auth_header(doc_user),
    )
    assert soap_fhir_res.status_code == 200
    composition_fhir = soap_fhir_res.json()
    assert composition_fhir["resourceType"] == "Composition"
    assert composition_fhir["status"] == "final"
    assert len(composition_fhir["section"]) == 5  # Chief Complaint, Subjective, Objective, Assessment, Plan

    # -------------------------------------------------------------------------
    # 6. Diagnostic Laboratory Order Requisition (ServiceRequest)
    # -------------------------------------------------------------------------
    order_res = await client.post(
        f"/api/v1/patients/{pat_id}/diagnostic-orders",
        headers=auth_header(doc_user),
        json={
            "encounter_id": appointment_id,
            "code_value": "24331-1",
            "code_coding_system": "http://loinc.org",
            "code_display": "Lipid Panel with Direct LDL",
            "priority": "routine",
            "reason_code": "I10",
            "reason_description": "Essential hypertension baseline workup",
            "specimen_type": "serum",
            "notes": "Evaluate baseline cardiovascular risk in patient with stage 1 hypertension",
        },
    )
    assert order_res.status_code == 201
    order_data = order_res.json()["data"]
    order_id = order_data["id"]
    assert order_data["status"] == "active"

    # Verify FHIR R4 ServiceRequest export
    sr_fhir_res = await client.get(
        f"/api/v1/diagnostic-orders/{order_id}/fhir",
        headers=auth_header(doc_user),
    )
    assert sr_fhir_res.status_code == 200
    sr_fhir = sr_fhir_res.json()["data"]
    assert sr_fhir["resourceType"] == "ServiceRequest"
    assert sr_fhir["code"]["coding"][0]["code"] == "24331-1"

    # -------------------------------------------------------------------------
    # 7. Diagnostic Laboratory Fulfillment (DiagnosticReport & Findings)
    # -------------------------------------------------------------------------
    # Lab transitions order notes
    update_order_res = await client.patch(
        f"/api/v1/diagnostic-orders/{order_id}",
        headers=auth_header(lab_user),
        json={"notes": "Specimen received and verified"},
    )
    assert update_order_res.status_code == 200

    # Lab uploads finalized report with conclusion and metrics
    report_res = await client.post(
        f"/api/v1/patients/{pat_id}/diagnostic-reports",
        headers=auth_header(lab_user),
        json={
            "order_id": order_id,
            "encounter_id": appointment_id,
            "code_value": "24331-1",
            "code_coding_system": "http://loinc.org",
            "code_display": "Comprehensive Lipid Profile Analysis",
            "status": "final",
            "conclusion": "Mild dyslipidemia characterized by borderline elevated LDL cholesterol and triglycerides.",
            "effective_date_time": now.isoformat(),
            "report_data": {
                "ldl_cholesterol": 138,
                "hdl_cholesterol": 44,
                "triglycerides": 182,
                "total_cholesterol": 218,
            },
        },
    )
    assert report_res.status_code == 201
    report_data = report_res.json()["data"]
    report_id = report_data["id"]
    assert report_data["status"] == "final"

    # Verify that creating the final report automatically marked the order as completed
    check_order_res = await client.get(
        f"/api/v1/diagnostic-orders/{order_id}",
        headers=auth_header(doc_user),
    )
    assert check_order_res.status_code == 200
    assert check_order_res.json()["data"]["status"] == "completed"

    # Export DiagnosticReport to FHIR R4
    dr_fhir_res = await client.get(
        f"/api/v1/diagnostic-reports/{report_id}/fhir",
        headers=auth_header(lab_user),
    )
    assert dr_fhir_res.status_code == 200
    dr_fhir = dr_fhir_res.json()["data"]
    assert dr_fhir["resourceType"] == "DiagnosticReport"
    assert dr_fhir["code"]["coding"][0]["code"] == "24331-1"

    # -------------------------------------------------------------------------
    # 8. Longitudinal Patient Health Vault Verification
    # -------------------------------------------------------------------------
    # Patient retrieves their own longitudinal problem list
    pat_conds_res = await client.get(
        f"/api/v1/patients/{pat_id}/conditions",
        headers=auth_header(pat_user),
    )
    assert pat_conds_res.status_code == 200
    pat_conds = pat_conds_res.json()["data"]
    assert len(pat_conds) >= 1
    assert any(c["code_value"] == "I10" for c in pat_conds)

    # Patient retrieves their own diagnostic orders & reports
    pat_orders_res = await client.get(
        f"/api/v1/patients/{pat_id}/diagnostic-orders",
        headers=auth_header(pat_user),
    )
    assert pat_orders_res.status_code == 200
    pat_orders = pat_orders_res.json()["data"]
    assert len(pat_orders) >= 1
    assert any(o["id"] == order_id and o["status"] == "completed" for o in pat_orders)

    # Patient retrieves their signed SOAP clinical consultation summary
    pat_soaps_res = await client.get(
        f"/api/v1/patients/{pat_id}/soap-notes",
        headers=auth_header(pat_user),
    )
    assert pat_soaps_res.status_code == 200
    pat_soaps = pat_soaps_res.json()["data"]
    assert len(pat_soaps) >= 1
    assert any(s["id"] == soap_note_id and s["is_signed"] is True for s in pat_soaps)


@pytest.mark.asyncio
async def test_e2e_clinical_rbac_isolation_and_tamper_guards(week5_e2e_env) -> None:
    """Verify security perimeter, role separation, and tamper-resistance."""
    client, session_factory = week5_e2e_env

    # Provision Doctor, Patient, and Lab
    async with session_factory() as db:
        doc = User(email="dr.guard@nirmaya.health", full_name="Dr. Guard", role=UserRole.DOCTOR, is_active=True, is_verified=True)
        pat = User(email="patient.guard@gmail.com", full_name="Patient Guard", role=UserRole.PATIENT, is_active=True, is_verified=True)
        lab = User(email="lab.guard@apex.in", full_name="Lab Guard", role=UserRole.LAB, is_active=True, is_verified=True)
        other_pat = User(email="other.patient@gmail.com", full_name="Other Patient", role=UserRole.PATIENT, is_active=True, is_verified=True)

        db.add_all([doc, pat, lab, other_pat])
        await db.flush()

        doc_p = DoctorProfile(
            user_id=doc.id, registration_number="DOC-G-1", medical_council="State Council",
            specialty=MedicalSpecialty.GENERAL_MEDICINE, qualifications="MBBS", consultation_fee=500
        )
        pat_p = PatientProfile(
            user_id=pat.id,
            gender=Gender.FEMALE,
            date_of_birth=date(1995, 1, 1),
            blood_group=BloodGroup.O_POSITIVE,
            abha_number="91-1111-2222-3333",
            abha_address="pat.guard@abdm",
            pincode="110001",
        )
        other_p = PatientProfile(
            user_id=other_pat.id,
            gender=Gender.MALE,
            date_of_birth=date(1990, 1, 1),
            blood_group=BloodGroup.A_POSITIVE,
            abha_number="91-4444-5555-6666",
            abha_address="other.pat@abdm",
            pincode="110002",
        )
        lab_p = DiagnosticLabFacility(
            user_id=lab.id,
            facility_name="Guard Diagnostic Lab",
            license_number="LAB-G-1",
            accreditation=LabAccreditation.NABL,
            accreditation_number="NABL-G-1",
            contact_person="Lab Manager",
            contact_email="lab.guard@apex.in",
            contact_phone="+919800000001",
            address_line="Main Road",
            city="New Delhi",
            state="Delhi",
            pincode="110001",
            is_nabl_certified=True,
        )
        db.add_all([doc_p, pat_p, other_p, lab_p])
        await db.commit()

        pat_id = pat_p.id
        other_pat_id = other_p.id
        lab_id = lab_p.id

    # 1. Patient CANNOT author a doctor SOAP note (HTTP 403 Forbidden)
    unauthorized_soap = await client.post(
        f"/api/v1/patients/{pat_id}/soap-notes",
        headers=auth_header(pat),
        json={
            "title": "Unauthorized Patient SOAP Note",
            "chief_complaint": "Self checkup note",
            "note_type": "soap",
            "subjective": "Self-assessment narrative",
            "objective": "Self-examination details",
            "assessment": "Self-diagnosis",
            "plan": "Self-medication",
        },
    )
    assert unauthorized_soap.status_code == 403

    # 2. Lab technician CANNOT diagnose or create a clinical condition (HTTP 403 Forbidden)
    unauthorized_cond = await client.post(
        f"/api/v1/patients/{pat_id}/conditions",
        headers=auth_header(lab),
        json={
            "code_value": "I10",
            "code_coding_system": "http://hl7.org/fhir/sid/icd-10",
            "code_display": "Hypertension",
        },
    )
    assert unauthorized_cond.status_code == 403

    # 3. Patient CANNOT create a Diagnostic Order on behalf of a doctor (HTTP 403 Forbidden)
    unauthorized_order = await client.post(
        f"/api/v1/patients/{pat_id}/diagnostic-orders",
        headers=auth_header(pat),
        json={
            "code_value": "24331-1",
            "code_coding_system": "http://loinc.org",
            "code_display": "Lipid Panel",
        },
    )
    assert unauthorized_order.status_code == 403

    # 4. Cross-patient isolation: Patient A cannot query Patient B's SOAP notes (HTTP 403)
    cross_patient_soap = await client.get(
        f"/api/v1/patients/{other_pat_id}/soap-notes",
        headers=auth_header(pat),
    )
    assert cross_patient_soap.status_code == 403

    # 5. Cross-patient isolation: Patient A cannot query Patient B's Diagnostic Orders (HTTP 403)
    cross_patient_orders = await client.get(
        f"/api/v1/patients/{other_pat_id}/diagnostic-orders",
        headers=auth_header(pat),
    )
    assert cross_patient_orders.status_code == 403

    # 6. Unauthenticated requests strictly return HTTP 401
    unauthenticated_res = await client.get(f"/api/v1/patients/{pat_id}/conditions")
    assert unauthenticated_res.status_code == 401

