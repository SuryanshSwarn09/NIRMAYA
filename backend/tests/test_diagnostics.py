"""Comprehensive unit and integration test suite for Diagnostic Lab Orders and Reports.

Validates:
1. Clinician diagnostic test requisition (ServiceRequest).
2. RBAC rules (patients cannot order tests).
3. Diagnostic order query, filtering, and updates.
4. FHIR R4 ServiceRequest export.
5. Diagnostic report issuance fulfilling an order (status completed transition).
6. Linking clinical observations to reports with automated abnormal evaluation.
7. FHIR R4 DiagnosticReport serialization with result references.
8. Cross-patient data isolation and access control.
"""

from datetime import date, datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.fhir import to_fhir_diagnostic_report, to_fhir_service_request
from app.main import app
from app.models.appointment import Appointment, DoctorSlot
from app.models.diagnostic import DiagnosticOrder, DiagnosticReport
from app.models.doctor import DoctorProfile
from app.models.enums import (
    AppointmentStatus,
    AppointmentType,
    DiagnosticReportStatus,
    Gender,
    MedicalSpecialty,
    ObservationCategory,
    ObservationInterpretation,
    ObservationStatus,
    ServiceRequestPriority,
    ServiceRequestStatus,
    SlotStatus,
    SpecimenType,
    UserRole,
)
from app.models.observation import ClinicalObservation
from app.models.patient import PatientProfile
from app.models.user import User


@pytest_asyncio.fixture
async def diagnostic_test_env():
    """Provide isolated in-memory SQLite database and HTTP client for diagnostic tests."""
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


async def seed_diagnostic_actors(session: AsyncSession):
    """Seed patient 1, patient 2, doctor, and lab technician."""
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
    await session.flush()

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
    await session.flush()

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

    # 4. Lab Technician
    u_lab = User(
        email="lab@nirmaya.health",
        full_name="Sanjay Pathak (Lab Tech)",
        role=UserRole.LAB,
        is_active=True,
        is_verified=True,
    )
    session.add(u_lab)

    # 5. Appointment Encounter
    slot_time = datetime.now(timezone.utc) + timedelta(days=1)
    slot = DoctorSlot(
        doctor_id=doc_profile.id,
        start_time=slot_time,
        end_time=slot_time + timedelta(minutes=30),
        status=SlotStatus.BOOKED,
    )
    session.add(slot)
    await session.flush()

    appt = Appointment(
        patient_id=pat1_profile.id,
        doctor_id=doc_profile.id,
        slot_id=slot.id,
        status=AppointmentStatus.COMPLETED,
        appointment_type=AppointmentType.ROUTINE_CHECKUP,
        scheduled_start=slot_time,
        scheduled_end=slot_time + timedelta(minutes=30),
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
        "appointment": appt,
    }


# ============================================================================
# Test Cases
# ============================================================================

@pytest.mark.asyncio
async def test_doctor_create_diagnostic_order(diagnostic_test_env):
    """Doctor requisitions a lipid panel test for a patient."""
    client, session_factory = diagnostic_test_env
    async with session_factory() as session:
        actors = await seed_diagnostic_actors(session)

    pat = actors["patient1"]
    doc_user = actors["user_doc"]
    appt = actors["appointment"]

    payload = {
        "code_value": "24331-1",
        "code_display": "Lipid panel with direct LDL - Serum or Plasma",
        "category": "laboratory",
        "priority": "routine",
        "specimen_type": "serum",
        "reason_code": "I10",
        "reason_description": "Hypertension surveillance and dyslipidemia evaluation",
        "notes": "12-hour fasting required",
        "encounter_id": appt.id,
    }

    res = await client.post(
        f"/api/v1/patients/{pat.id}/diagnostic-orders",
        json=payload,
        headers=auth_header_for(doc_user),
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["code_value"] == "24331-1"
    assert data["status"] == "active"
    assert data["priority"] == "routine"
    assert data["doctor_id"] == actors["doctor"].id


@pytest.mark.asyncio
async def test_patient_cannot_create_diagnostic_order(diagnostic_test_env):
    """Patient cannot requisition clinical diagnostic orders (RBAC check)."""
    client, session_factory = diagnostic_test_env
    async with session_factory() as session:
        actors = await seed_diagnostic_actors(session)

    pat = actors["patient1"]
    pat_user = actors["user_pat1"]

    payload = {
        "code_value": "4548-4",
        "code_display": "Hemoglobin A1c/Hemoglobin.total in Blood",
    }

    res = await client.post(
        f"/api/v1/patients/{pat.id}/diagnostic-orders",
        json=payload,
        headers=auth_header_for(pat_user),
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_and_list_patient_diagnostic_orders(diagnostic_test_env):
    """Retrieve and list orders with pagination and filters."""
    client, session_factory = diagnostic_test_env
    async with session_factory() as session:
        actors = await seed_diagnostic_actors(session)
        pat = actors["patient1"]
        doc = actors["doctor"]

        # Seed two orders
        ord1 = DiagnosticOrder(
            patient_id=pat.id,
            doctor_id=doc.id,
            code_value="24331-1",
            code_display="Lipid panel",
            status=ServiceRequestStatus.ACTIVE,
            priority=ServiceRequestPriority.ROUTINE,
        )
        ord2 = DiagnosticOrder(
            patient_id=pat.id,
            doctor_id=doc.id,
            code_value="4548-4",
            code_display="HbA1c",
            status=ServiceRequestStatus.COMPLETED,
            priority=ServiceRequestPriority.URGENT,
        )
        session.add_all([ord1, ord2])
        await session.commit()
        order_id = ord1.id

    # Get single order
    res = await client.get(
        f"/api/v1/diagnostic-orders/{order_id}",
        headers=auth_header_for(actors["user_doc"]),
    )
    assert res.status_code == 200
    assert res.json()["data"]["id"] == order_id

    # List orders with status filter
    res = await client.get(
        f"/api/v1/patients/{pat.id}/diagnostic-orders?status=active",
        headers=auth_header_for(actors["user_pat1"]),
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["code_value"] == "24331-1"


@pytest.mark.asyncio
async def test_update_diagnostic_order_status(diagnostic_test_env):
    """Clinician or lab updates priority and status of order."""
    client, session_factory = diagnostic_test_env
    async with session_factory() as session:
        actors = await seed_diagnostic_actors(session)
        order = DiagnosticOrder(
            patient_id=actors["patient1"].id,
            doctor_id=actors["doctor"].id,
            code_value="58410-2",
            code_display="Complete blood count (CBC)",
            status=ServiceRequestStatus.ACTIVE,
            priority=ServiceRequestPriority.ROUTINE,
        )
        session.add(order)
        await session.commit()
        order_id = order.id

    res = await client.patch(
        f"/api/v1/diagnostic-orders/{order_id}",
        json={"priority": "stat", "status": "on-hold", "notes": "Specimen hemolyzed, recollecting"},
        headers=auth_header_for(actors["user_lab"]),
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["priority"] == "stat"
    assert data["status"] == "on-hold"


@pytest.mark.asyncio
async def test_export_diagnostic_order_fhir(diagnostic_test_env):
    """Export diagnostic order as HL7 FHIR Release 4 ServiceRequest."""
    client, session_factory = diagnostic_test_env
    async with session_factory() as session:
        actors = await seed_diagnostic_actors(session)
        order = DiagnosticOrder(
            patient_id=actors["patient1"].id,
            doctor_id=actors["doctor"].id,
            code_value="24331-1",
            code_display="Lipid panel with direct LDL",
            status=ServiceRequestStatus.ACTIVE,
            priority=ServiceRequestPriority.ROUTINE,
        )
        session.add(order)
        await session.commit()
        order_id = order.id

    res = await client.get(
        f"/api/v1/diagnostic-orders/{order_id}/fhir",
        headers=auth_header_for(actors["user_pat1"]),
    )
    assert res.status_code == 200
    fhir = res.json()["data"]
    assert fhir["resourceType"] == "ServiceRequest"
    assert fhir["id"] == order_id
    assert fhir["status"] == "active"
    assert fhir["code"]["coding"][0]["code"] == "24331-1"
    assert fhir["subject"]["reference"] == f"Patient/{actors['patient1'].id}"


@pytest.mark.asyncio
async def test_issue_diagnostic_report_fulfilling_order(diagnostic_test_env):
    """Lab fulfills an order and issues diagnostic report, marking order completed."""
    client, session_factory = diagnostic_test_env
    async with session_factory() as session:
        actors = await seed_diagnostic_actors(session)
        order = DiagnosticOrder(
            patient_id=actors["patient1"].id,
            doctor_id=actors["doctor"].id,
            code_value="24331-1",
            code_display="Lipid panel with direct LDL",
            status=ServiceRequestStatus.ACTIVE,
        )
        session.add(order)
        await session.commit()
        order_id = order.id

    payload = {
        "order_id": order_id,
        "code_value": "24331-1",
        "code_display": "Lipid panel with direct LDL - Serum or Plasma",
        "conclusion": "Total Cholesterol borderline elevated. HDL satisfactory.",
        "is_abnormal": True,
        "report_data": {
            "total_cholesterol": 215,
            "hdl": 50,
            "ldl": 138,
            "triglycerides": 135,
        },
    }

    res = await client.post(
        f"/api/v1/patients/{actors['patient1'].id}/diagnostic-reports",
        json=payload,
        headers=auth_header_for(actors["user_lab"]),
    )
    assert res.status_code == 201
    rep_data = res.json()["data"]
    assert rep_data["order_id"] == order_id
    assert rep_data["is_abnormal"] is True
    assert rep_data["status"] == "final"

    # Verify order was marked completed
    async with session_factory() as session:
        updated_order = await session.get(DiagnosticOrder, order_id)
        assert updated_order.status == ServiceRequestStatus.COMPLETED


@pytest.mark.asyncio
async def test_issue_diagnostic_report_with_linked_observations(diagnostic_test_env):
    """Create observations, link to report, verify abnormal flag and retrieval."""
    client, session_factory = diagnostic_test_env
    async with session_factory() as session:
        actors = await seed_diagnostic_actors(session)
        pat = actors["patient1"]

        # Create 2 observations (one abnormal, one normal)
        obs1 = ClinicalObservation(
            patient_id=pat.id,
            category=ObservationCategory.LABORATORY,
            code_value="2093-3",
            code_display="Cholesterol [Mass/volume] in Serum or Plasma",
            value_quantity=225.0,
            value_unit="mg/dL",
            interpretation=ObservationInterpretation.HIGH,
            status=ObservationStatus.FINAL,
        )
        obs2 = ClinicalObservation(
            patient_id=pat.id,
            category=ObservationCategory.LABORATORY,
            code_value="2085-9",
            code_display="HDL Cholesterol in Serum or Plasma",
            value_quantity=52.0,
            value_unit="mg/dL",
            interpretation=ObservationInterpretation.NORMAL,
            status=ObservationStatus.FINAL,
        )
        session.add_all([obs1, obs2])
        await session.commit()
        obs_ids = [obs1.id, obs2.id]

    payload = {
        "code_value": "24331-1",
        "code_display": "Lipid panel",
        "observation_ids": obs_ids,
        "conclusion": "Elevated total cholesterol",
    }

    res = await client.post(
        f"/api/v1/patients/{pat.id}/diagnostic-reports",
        json=payload,
        headers=auth_header_for(actors["user_doc"]),
    )
    assert res.status_code == 201
    report_id = res.json()["data"]["id"]
    # Should automatically detect abnormal observation
    assert res.json()["data"]["is_abnormal"] is True

    # Retrieve report with observations
    res = await client.get(
        f"/api/v1/diagnostic-reports/{report_id}",
        headers=auth_header_for(actors["user_pat1"]),
    )
    assert res.status_code == 200
    report_details = res.json()["data"]
    assert len(report_details["observations"]) == 2
    assert report_details["observations"][0]["value_quantity"] in (225.0, 52.0)


@pytest.mark.asyncio
async def test_export_diagnostic_report_fhir(diagnostic_test_env):
    """Export diagnostic report as HL7 FHIR Release 4 DiagnosticReport."""
    client, session_factory = diagnostic_test_env
    async with session_factory() as session:
        actors = await seed_diagnostic_actors(session)
        pat = actors["patient1"]
        report = DiagnosticReport(
            patient_id=pat.id,
            code_value="24331-1",
            code_display="Lipid panel",
            conclusion="Normal lipid profile",
            status=DiagnosticReportStatus.FINAL,
        )
        session.add(report)
        await session.commit()
        report_id = report.id

    res = await client.get(
        f"/api/v1/diagnostic-reports/{report_id}/fhir",
        headers=auth_header_for(actors["user_pat1"]),
    )
    assert res.status_code == 200
    fhir = res.json()["data"]
    assert fhir["resourceType"] == "DiagnosticReport"
    assert fhir["id"] == report_id
    assert fhir["status"] == "final"
    assert fhir["code"]["coding"][0]["code"] == "24331-1"
    assert fhir["conclusion"] == "Normal lipid profile"


@pytest.mark.asyncio
async def test_patient_cross_tenant_access_isolation(diagnostic_test_env):
    """Patient 2 cannot access Patient 1's diagnostic orders or reports."""
    client, session_factory = diagnostic_test_env
    async with session_factory() as session:
        actors = await seed_diagnostic_actors(session)
        order = DiagnosticOrder(
            patient_id=actors["patient1"].id,
            doctor_id=actors["doctor"].id,
            code_value="24331-1",
            code_display="Lipid panel",
        )
        report = DiagnosticReport(
            patient_id=actors["patient1"].id,
            code_value="24331-1",
            code_display="Lipid panel",
        )
        session.add_all([order, report])
        await session.commit()
        order_id = order.id
        report_id = report.id

    # Patient 2 attempts order access
    res = await client.get(
        f"/api/v1/diagnostic-orders/{order_id}",
        headers=auth_header_for(actors["user_pat2"]),
    )
    assert res.status_code == 403

    # Patient 2 attempts report access
    res = await client.get(
        f"/api/v1/diagnostic-reports/{report_id}",
        headers=auth_header_for(actors["user_pat2"]),
    )
    assert res.status_code == 403
