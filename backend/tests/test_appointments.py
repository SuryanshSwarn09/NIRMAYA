"""Comprehensive integration and unit test suite for Doctor Slots and Clinical Appointments."""

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
from app.models.enums import AppointmentStatus, AppointmentType, MedicalSpecialty, SlotStatus, UserRole
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.appointment import SlotGenerateRequest
from app.services import appointment as appointment_service
from app.services import slot_engine


@pytest_asyncio.fixture
async def appt_test_env():
    """Provide isolated in-memory test database and client for appointment and slot testing."""
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


async def seed_doctor_and_patient(session_factory):
    """Seed test doctor, patient, and third-party user."""
    async with session_factory() as db:
        # Doctor user & profile
        doc_user = User(
            email="dr.sharma@nirmaya.health",
            full_name="Dr. Rajesh Sharma",
            role=UserRole.DOCTOR,
        )
        db.add(doc_user)
        await db.flush()

        doc_profile = DoctorProfile(
            user_id=doc_user.id,
            registration_number="DMC-10101",
            medical_council="Delhi Medical Council",
            specialty=MedicalSpecialty.CARDIOLOGY,
            qualifications="MBBS, MD",
            experience_years=12,
            consultation_fee=800,
        )
        db.add(doc_profile)

        # Patient user & profile
        pat_user = User(
            email="aarav.patel@nirmaya.health",
            full_name="Aarav Patel",
            role=UserRole.PATIENT,
        )
        db.add(pat_user)
        await db.flush()

        pat_profile = PatientProfile(
            user_id=pat_user.id,
            abha_number="91-1234-5678-9012",
            abha_address="aarav@abdm",
        )
        db.add(pat_profile)

        # Another third-party patient
        other_user = User(
            email="priya.verma@nirmaya.health",
            full_name="Priya Verma",
            role=UserRole.PATIENT,
        )
        db.add(other_user)
        await db.flush()

        other_profile = PatientProfile(
            user_id=other_user.id,
            abha_number="91-9876-5432-1098",
            abha_address="priya@abdm",
        )
        db.add(other_profile)

        await db.commit()

        return {
            "doctor_user": doc_user,
            "doctor": doc_profile,
            "patient_user": pat_user,
            "patient": pat_profile,
            "other_user": other_user,
            "other_patient": other_profile,
        }


# ============================================================================
# Slot Engine Unit & Service Tests
# ============================================================================


@pytest.mark.asyncio
async def test_slot_engine_generates_correct_slot_count(appt_test_env) -> None:
    """Verify slot engine creates exact expected slots for working hours."""
    _, session_factory = appt_test_env
    seed = await seed_doctor_and_patient(session_factory)
    doctor = seed["doctor"]

    async with session_factory() as db:
        # 09:00 to 12:00 = 3 hours = 6 slots (30 min each)
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 1),
            day_start_hour=9,
            day_start_minute=0,
            day_end_hour=12,
            day_end_minute=0,
            slot_duration_minutes=30,
        )
        result = await slot_engine.generate_slots_for_doctor(db, req)
        assert result.total_generated == 6
        assert result.total_skipped_existing == 0
        assert len(result.slots) == 6


@pytest.mark.asyncio
async def test_slot_engine_excludes_break_window(appt_test_env) -> None:
    """Verify slot engine excludes candidate slots falling inside lunch break."""
    _, session_factory = appt_test_env
    seed = await seed_doctor_and_patient(session_factory)
    doctor = seed["doctor"]

    async with session_factory() as db:
        # 09:00 to 13:00 (4h = 8 slots), break 11:00 to 12:00 (1h = 2 slots) -> 6 slots
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 10, 2),
            end_date=date(2026, 10, 2),
            day_start_hour=9,
            day_start_minute=0,
            day_end_hour=13,
            day_end_minute=0,
            slot_duration_minutes=30,
            break_start_hour=11,
            break_start_minute=0,
            break_end_hour=12,
            break_end_minute=0,
        )
        result = await slot_engine.generate_slots_for_doctor(db, req)
        assert result.total_generated == 6
        # Ensure no slot starts at 11:00 or 11:30
        for slot in result.slots:
            assert slot.start_time.hour not in [11]


@pytest.mark.asyncio
async def test_slot_engine_is_idempotent(appt_test_env) -> None:
    """Verify running slot generator twice avoids duplicates and skips existing."""
    _, session_factory = appt_test_env
    seed = await seed_doctor_and_patient(session_factory)
    doctor = seed["doctor"]

    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 10, 5),
            end_date=date(2026, 10, 5),
            day_start_hour=9,
            day_start_minute=0,
            day_end_hour=11,
            day_end_minute=0,
            slot_duration_minutes=30,
        )
        first_run = await slot_engine.generate_slots_for_doctor(db, req)
        assert first_run.total_generated == 4

        # Second run should skip all 4 existing
        second_run = await slot_engine.generate_slots_for_doctor(db, req)
        assert second_run.total_generated == 0
        assert second_run.total_skipped_existing == 4


# ============================================================================
# API Endpoints: Slot Availability & Generation
# ============================================================================


@pytest.mark.asyncio
async def test_api_get_slots_endpoint(appt_test_env) -> None:
    """Verify GET /api/v1/doctors/{id}/slots returns available slots."""
    client, session_factory = appt_test_env
    seed = await seed_doctor_and_patient(session_factory)
    doctor = seed["doctor"]

    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 10, 10),
            end_date=date(2026, 10, 10),
            day_start_hour=10,
            day_end_hour=12,
            slot_duration_minutes=30,
        )
        await slot_engine.generate_slots_for_doctor(db, req)

    response = await client.get(f"/api/v1/doctors/{doctor.id}/slots?target_date=2026-10-10")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 4


@pytest.mark.asyncio
async def test_api_generate_slots_unauthorized(appt_test_env) -> None:
    """Verify patients or other users cannot generate slots for a doctor."""
    client, session_factory = appt_test_env
    seed = await seed_doctor_and_patient(session_factory)
    doctor = seed["doctor"]
    patient_user = seed["patient_user"]

    payload = {
        "doctor_id": doctor.id,
        "start_date": "2026-10-15",
        "end_date": "2026-10-15",
        "day_start_hour": 9,
        "day_end_hour": 11,
        "slot_duration_minutes": 30,
    }
    response = await client.post(
        f"/api/v1/doctors/{doctor.id}/slots/generate",
        json=payload,
        headers=auth_header_for(patient_user),
    )
    assert response.status_code == 403


# ============================================================================
# Appointment Booking & Concurrency Lifecycle Tests
# ============================================================================


@pytest.mark.asyncio
async def test_book_appointment_success(appt_test_env) -> None:
    """Verify patient can book an available slot, locking slot to BOOKED."""
    client, session_factory = appt_test_env
    seed = await seed_doctor_and_patient(session_factory)
    doctor = seed["doctor"]
    patient = seed["patient"]
    patient_user = seed["patient_user"]

    # Generate 1 slot
    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 10, 20),
            end_date=date(2026, 10, 20),
            day_start_hour=9,
            day_end_hour=10,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    # Book via API
    booking_payload = {
        "doctor_id": doctor.id,
        "slot_id": slot_id,
        "appointment_type": "routine_checkup",
        "reason": "Annual cardiovascular checkup",
    }
    res = await client.post(
        "/api/v1/appointments/",
        json=booking_payload,
        headers=auth_header_for(patient_user),
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    appt_data = body["data"]
    assert appt_data["doctor_id"] == doctor.id
    assert appt_data["patient_id"] == patient.id
    assert appt_data["status"] == "scheduled"
    assert appt_data["slot_id"] == slot_id
    assert appt_data["doctor_name"] == "Dr. Rajesh Sharma"

    # Verify slot is now BOOKED in database
    async with session_factory() as db:
        slot = await slot_engine.get_slot_by_id(db, slot_id)
        assert slot is not None
        assert slot.status == SlotStatus.BOOKED


@pytest.mark.asyncio
async def test_book_already_booked_slot_returns_409_conflict(appt_test_env) -> None:
    """Verify double-booking same slot returns 409 Conflict."""
    client, session_factory = appt_test_env
    seed = await seed_doctor_and_patient(session_factory)
    doctor = seed["doctor"]
    patient_user = seed["patient_user"]
    other_user = seed["other_user"]

    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 10, 21),
            end_date=date(2026, 10, 21),
            day_start_hour=9,
            day_end_hour=10,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    booking_payload = {
        "doctor_id": doctor.id,
        "slot_id": slot_id,
        "reason": "First booking",
    }
    # First booking succeeds
    res1 = await client.post(
        "/api/v1/appointments/",
        json=booking_payload,
        headers=auth_header_for(patient_user),
    )
    assert res1.status_code == 201

    # Second booking for same slot by other patient yields 409 Conflict
    res2 = await client.post(
        "/api/v1/appointments/",
        json=booking_payload,
        headers=auth_header_for(other_user),
    )
    assert res2.status_code == 409
    body = res2.json()
    assert body["error_code"] == "SLOT_NOT_AVAILABLE"


@pytest.mark.asyncio
async def test_cancel_appointment_replenishes_slot(appt_test_env) -> None:
    """Verify cancelling appointment frees up the associated slot back to AVAILABLE."""
    client, session_factory = appt_test_env
    seed = await seed_doctor_and_patient(session_factory)
    doctor = seed["doctor"]
    patient_user = seed["patient_user"]

    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 10, 22),
            end_date=date(2026, 10, 22),
            day_start_hour=14,
            day_end_hour=15,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    # Book appointment
    book_res = await client.post(
        "/api/v1/appointments/",
        json={"doctor_id": doctor.id, "slot_id": slot_id, "reason": "General check"},
        headers=auth_header_for(patient_user),
    )
    appt_id = book_res.json()["data"]["id"]

    # Cancel appointment
    cancel_res = await client.patch(
        f"/api/v1/appointments/{appt_id}/status",
        json={"status": "cancelled", "cancellation_reason": "Patient conflict"},
        headers=auth_header_for(patient_user),
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "cancelled"

    # Verify slot is back to AVAILABLE
    async with session_factory() as db:
        slot = await slot_engine.get_slot_by_id(db, slot_id)
        assert slot is not None
        assert slot.status == SlotStatus.AVAILABLE


@pytest.mark.asyncio
async def test_doctor_progresses_appointment_lifecycle(appt_test_env) -> None:
    """Verify doctor can progress appointment status: scheduled -> in_progress -> completed."""
    client, session_factory = appt_test_env
    seed = await seed_doctor_and_patient(session_factory)
    doctor = seed["doctor"]
    doctor_user = seed["doctor_user"]
    patient_user = seed["patient_user"]

    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 10, 25),
            end_date=date(2026, 10, 25),
            day_start_hour=10,
            day_end_hour=11,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    book_res = await client.post(
        "/api/v1/appointments/",
        json={"doctor_id": doctor.id, "slot_id": slot_id, "reason": "Heart palpitations"},
        headers=auth_header_for(patient_user),
    )
    appt_id = book_res.json()["data"]["id"]

    # Doctor starts consultation
    start_res = await client.patch(
        f"/api/v1/appointments/{appt_id}/status",
        json={"status": "in_progress", "clinical_notes": "Patient seated, BP 120/80"},
        headers=auth_header_for(doctor_user),
    )
    assert start_res.status_code == 200
    assert start_res.json()["data"]["status"] == "in_progress"

    # Doctor completes consultation
    finish_res = await client.patch(
        f"/api/v1/appointments/{appt_id}/status",
        json={"status": "completed", "clinical_notes": "Prescribed beta-blockers, follow up in 2 weeks"},
        headers=auth_header_for(doctor_user),
    )
    assert finish_res.status_code == 200
    assert finish_res.json()["data"]["status"] == "completed"
    assert "beta-blockers" in finish_res.json()["data"]["clinical_notes"]


@pytest.mark.asyncio
async def test_appointment_authorization_isolation(appt_test_env) -> None:
    """Verify third-party patient cannot view or modify someone else's appointment."""
    client, session_factory = appt_test_env
    seed = await seed_doctor_and_patient(session_factory)
    doctor = seed["doctor"]
    patient_user = seed["patient_user"]
    other_user = seed["other_user"]

    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 10, 28),
            end_date=date(2026, 10, 28),
            day_start_hour=9,
            day_end_hour=10,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    book_res = await client.post(
        "/api/v1/appointments/",
        json={"doctor_id": doctor.id, "slot_id": slot_id, "reason": "Private consultation"},
        headers=auth_header_for(patient_user),
    )
    appt_id = book_res.json()["data"]["id"]

    # Other patient tries to view
    view_res = await client.get(
        f"/api/v1/appointments/{appt_id}",
        headers=auth_header_for(other_user),
    )
    assert view_res.status_code == 403

    # Other patient tries to cancel
    mod_res = await client.patch(
        f"/api/v1/appointments/{appt_id}/status",
        json={"status": "cancelled"},
        headers=auth_header_for(other_user),
    )
    assert mod_res.status_code == 403
