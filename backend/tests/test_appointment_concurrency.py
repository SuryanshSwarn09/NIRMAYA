"""Comprehensive unit and integration test suite for Slot Booking Concurrency,

ACID Row-Level Locking, and Cal.com-style Held Slot Lifecycle.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.appointment import Appointment, DoctorSlot
from app.models.doctor import DoctorProfile
from app.models.enums import AppointmentStatus, MedicalSpecialty, SlotStatus, UserRole
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.appointment import SlotGenerateRequest
from app.services import slot_engine


@pytest_asyncio.fixture
async def concurrency_test_env():
    """Provide isolated file-based test database and client for true multi-transaction concurrency tests."""
    import os
    import shutil
    import tempfile
    from sqlalchemy import text

    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_concurrency.db").replace("\\", "/")
    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args={"timeout": 30},
    )
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA busy_timeout=5000"))
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

    await engine.dispose()
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


def auth_header_for(user: User) -> dict:
    """Generate authorization bearer headers for test user."""
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
    })
    return {"Authorization": f"Bearer {token}"}


async def seed_concurrency_fixture(session_factory):
    """Seed test doctor and multiple competing patient profiles."""
    async with session_factory() as db:
        # Doctor
        doc_user = User(
            email="dr.concurrency@nirmaya.health",
            full_name="Dr. Vikram Sen",
            role=UserRole.DOCTOR,
        )
        db.add(doc_user)
        await db.flush()

        doc_profile = DoctorProfile(
            user_id=doc_user.id,
            registration_number="DMC-CONCURR-99",
            medical_council="Delhi Medical Council",
            specialty=MedicalSpecialty.NEUROLOGY,
            qualifications="MBBS, DM (Neurology)",
            experience_years=15,
            consultation_fee=1200,
        )
        db.add(doc_profile)

        # 5 Competing Patients
        patients = []
        for i in range(1, 6):
            p_user = User(
                email=f"patient{i}@nirmaya.health",
                full_name=f"Patient {i}",
                role=UserRole.PATIENT,
            )
            db.add(p_user)
            await db.flush()

            p_profile = PatientProfile(
                user_id=p_user.id,
                abha_number=f"91-0000-0000-000{i}",
                abha_address=f"patient{i}@abdm",
            )
            db.add(p_profile)
            patients.append({"user": p_user, "profile": p_profile})

        await db.commit()

        return {
            "doctor_user": doc_user,
            "doctor": doc_profile,
            "patients": patients,
        }


# ============================================================================
# Slot Hold & Release Lifecycle Tests
# ============================================================================


@pytest.mark.asyncio
async def test_slot_hold_success(concurrency_test_env) -> None:
    """Verify patient can place a 10-minute hold on an available slot."""
    client, session_factory = concurrency_test_env
    fixture = await seed_concurrency_fixture(session_factory)
    doctor = fixture["doctor"]
    patient = fixture["patients"][0]

    # Generate 1 slot
    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 1),
            day_start_hour=10,
            day_end_hour=11,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    # Place hold
    res = await client.post(
        f"/api/v1/doctors/{doctor.id}/slots/{slot_id}/hold",
        json={"hold_duration_minutes": 10},
        headers=auth_header_for(patient["user"]),
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["slot_id"] == slot_id
    assert data["status"] == "held"
    assert data["held_by_patient_id"] == patient["profile"].id
    assert data["hold_duration_seconds"] > 550  # ~600 seconds


@pytest.mark.asyncio
async def test_slot_hold_conflict_when_already_held(concurrency_test_env) -> None:
    """Verify second patient receives 409 Conflict when attempting to hold an already held slot."""
    client, session_factory = concurrency_test_env
    fixture = await seed_concurrency_fixture(session_factory)
    doctor = fixture["doctor"]
    p1 = fixture["patients"][0]
    p2 = fixture["patients"][1]

    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 11, 2),
            end_date=date(2026, 11, 2),
            day_start_hour=10,
            day_end_hour=11,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    # Patient 1 holds slot
    res1 = await client.post(
        f"/api/v1/doctors/{doctor.id}/slots/{slot_id}/hold",
        json={"hold_duration_minutes": 10},
        headers=auth_header_for(p1["user"]),
    )
    assert res1.status_code == 200

    # Patient 2 tries to hold same slot
    res2 = await client.post(
        f"/api/v1/doctors/{doctor.id}/slots/{slot_id}/hold",
        json={"hold_duration_minutes": 10},
        headers=auth_header_for(p2["user"]),
    )
    assert res2.status_code == 409
    assert res2.json()["error_code"] == "SLOT_HELD_BY_ANOTHER_PATIENT"


@pytest.mark.asyncio
async def test_slot_release_by_holder(concurrency_test_env) -> None:
    """Verify holder patient can release hold, restoring slot to available for others."""
    client, session_factory = concurrency_test_env
    fixture = await seed_concurrency_fixture(session_factory)
    doctor = fixture["doctor"]
    p1 = fixture["patients"][0]
    p2 = fixture["patients"][1]

    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 11, 3),
            end_date=date(2026, 11, 3),
            day_start_hour=14,
            day_end_hour=15,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    # Patient 1 holds slot
    await client.post(
        f"/api/v1/doctors/{doctor.id}/slots/{slot_id}/hold",
        headers=auth_header_for(p1["user"]),
    )

    # Patient 1 releases hold
    rel_res = await client.post(
        f"/api/v1/doctors/{doctor.id}/slots/{slot_id}/release",
        headers=auth_header_for(p1["user"]),
    )
    assert rel_res.status_code == 200
    assert rel_res.json()["data"]["status"] == "available"

    # Patient 2 can now successfully hold it
    hold2_res = await client.post(
        f"/api/v1/doctors/{doctor.id}/slots/{slot_id}/hold",
        headers=auth_header_for(p2["user"]),
    )
    assert hold2_res.status_code == 200
    assert hold2_res.json()["data"]["held_by_patient_id"] == p2["profile"].id


@pytest.mark.asyncio
async def test_slot_release_unauthorized(concurrency_test_env) -> None:
    """Verify non-holder patient cannot release someone else's hold."""
    client, session_factory = concurrency_test_env
    fixture = await seed_concurrency_fixture(session_factory)
    doctor = fixture["doctor"]
    p1 = fixture["patients"][0]
    p2 = fixture["patients"][1]

    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 11, 4),
            end_date=date(2026, 11, 4),
            day_start_hour=10,
            day_end_hour=11,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    await client.post(
        f"/api/v1/doctors/{doctor.id}/slots/{slot_id}/hold",
        headers=auth_header_for(p1["user"]),
    )

    # Patient 2 attempts release
    rel_res = await client.post(
        f"/api/v1/doctors/{doctor.id}/slots/{slot_id}/release",
        headers=auth_header_for(p2["user"]),
    )
    assert rel_res.status_code == 403


@pytest.mark.asyncio
async def test_convert_held_slot_to_confirmed_appointment(concurrency_test_env) -> None:
    """Verify holder patient can convert their held slot into a confirmed booked appointment."""
    client, session_factory = concurrency_test_env
    fixture = await seed_concurrency_fixture(session_factory)
    doctor = fixture["doctor"]
    p1 = fixture["patients"][0]

    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 11, 5),
            end_date=date(2026, 11, 5),
            day_start_hour=9,
            day_end_hour=10,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    # Place hold
    await client.post(
        f"/api/v1/doctors/{doctor.id}/slots/{slot_id}/hold",
        headers=auth_header_for(p1["user"]),
    )

    # Book the held slot
    book_res = await client.post(
        "/api/v1/appointments/",
        json={"doctor_id": doctor.id, "slot_id": slot_id, "reason": "Follow-up neurological test"},
        headers=auth_header_for(p1["user"]),
    )
    assert book_res.status_code == 201
    appt = book_res.json()["data"]
    assert appt["slot_id"] == slot_id
    assert appt["status"] == "scheduled"

    # Verify slot is BOOKED and hold fields are cleared
    async with session_factory() as db:
        slot = await slot_engine.get_slot_by_id(db, slot_id)
        assert slot.status == SlotStatus.BOOKED
        assert slot.held_until is None
        assert slot.held_by_patient_id is None


@pytest.mark.asyncio
async def test_book_held_slot_by_other_patient_returns_409(concurrency_test_env) -> None:
    """Verify other patient cannot directly book a slot currently held by someone else."""
    client, session_factory = concurrency_test_env
    fixture = await seed_concurrency_fixture(session_factory)
    doctor = fixture["doctor"]
    p1 = fixture["patients"][0]
    p2 = fixture["patients"][1]

    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 11, 6),
            end_date=date(2026, 11, 6),
            day_start_hour=9,
            day_end_hour=10,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    # Patient 1 holds
    await client.post(
        f"/api/v1/doctors/{doctor.id}/slots/{slot_id}/hold",
        headers=auth_header_for(p1["user"]),
    )

    # Patient 2 attempts booking
    book_res = await client.post(
        "/api/v1/appointments/",
        json={"doctor_id": doctor.id, "slot_id": slot_id, "reason": "Attempt takeover"},
        headers=auth_header_for(p2["user"]),
    )
    assert book_res.status_code == 409
    assert book_res.json()["error_code"] == "SLOT_HELD_BY_ANOTHER_PATIENT"


# ============================================================================
# Expired Hold Auto-Sweep Tests
# ============================================================================


@pytest.mark.asyncio
async def test_expired_hold_auto_sweep_on_query(concurrency_test_env) -> None:
    """Verify query for doctor slots automatically sweeps expired holds back to available."""
    client, session_factory = concurrency_test_env
    fixture = await seed_concurrency_fixture(session_factory)
    doctor = fixture["doctor"]
    p1 = fixture["patients"][0]

    # Create slot directly in DB with an already-expired hold timestamp
    async with session_factory() as db:
        slot = DoctorSlot(
            doctor_id=doctor.id,
            start_time=datetime(2026, 11, 7, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 11, 7, 11, 0, tzinfo=timezone.utc),
            status=SlotStatus.HELD,
            held_until=datetime.now(timezone.utc) - timedelta(minutes=5),  # Expired 5 mins ago
            held_by_patient_id=p1["profile"].id,
        )
        db.add(slot)
        await db.commit()
        await db.refresh(slot)
        slot_id = slot.id

    # Query availability slots
    res = await client.get(f"/api/v1/doctors/{doctor.id}/slots?target_date=2026-11-07")
    assert res.status_code == 200
    slots = res.json()["data"]
    assert len(slots) == 1
    assert slots[0]["status"] == "available"
    assert slots[0]["held_until"] is None


@pytest.mark.asyncio
async def test_expired_hold_claimed_by_new_booking(concurrency_test_env) -> None:
    """Verify an expired hold does not block a new patient from booking the slot."""
    client, session_factory = concurrency_test_env
    fixture = await seed_concurrency_fixture(session_factory)
    doctor = fixture["doctor"]
    p1 = fixture["patients"][0]
    p2 = fixture["patients"][1]

    # Create slot held by P1 that expired
    async with session_factory() as db:
        slot = DoctorSlot(
            doctor_id=doctor.id,
            start_time=datetime(2026, 11, 8, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 11, 8, 15, 0, tzinfo=timezone.utc),
            status=SlotStatus.HELD,
            held_until=datetime.now(timezone.utc) - timedelta(minutes=2),
            held_by_patient_id=p1["profile"].id,
        )
        db.add(slot)
        await db.commit()
        await db.refresh(slot)
        slot_id = slot.id

    # Patient 2 books slot (hold has expired)
    book_res = await client.post(
        "/api/v1/appointments/",
        json={"doctor_id": doctor.id, "slot_id": slot_id, "reason": "Booking expired slot"},
        headers=auth_header_for(p2["user"]),
    )
    assert book_res.status_code == 201
    assert book_res.json()["data"]["patient_id"] == p2["profile"].id


# ============================================================================
# High-Contention Parallel Booking Race Condition Test
# ============================================================================


@pytest.mark.asyncio
async def test_parallel_booking_high_contention_race_condition(concurrency_test_env) -> None:
    """Verify that under simultaneous parallel contention, exactly ONE booking succeeds

    and all other concurrent requests receive graceful 409 Conflict envelopes.
    """
    client, session_factory = concurrency_test_env
    fixture = await seed_concurrency_fixture(session_factory)
    doctor = fixture["doctor"]
    patients = fixture["patients"]

    # Generate 1 slot targeted by all 5 patients
    async with session_factory() as db:
        req = SlotGenerateRequest(
            doctor_id=doctor.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 11, 10),
            day_start_hour=9,
            day_end_hour=10,
            slot_duration_minutes=60,
        )
        gen = await slot_engine.generate_slots_for_doctor(db, req)
        slot_id = gen.slots[0].id

    booking_payload = {
        "doctor_id": doctor.id,
        "slot_id": slot_id,
        "reason": "Simultaneous race condition test",
    }

    # Dispatch 5 simultaneous booking requests using asyncio.gather
    tasks = [
        client.post(
            "/api/v1/appointments/",
            json=booking_payload,
            headers=auth_header_for(p["user"]),
        )
        for p in patients
    ]
    responses = await asyncio.gather(*tasks)

    status_codes = [r.status_code for r in responses]

    # Exactly 1 request must succeed with 201 Created
    success_count = status_codes.count(201)
    conflict_count = status_codes.count(409)

    assert success_count == 1, f"Expected exactly 1 success, got: {status_codes}"
    assert conflict_count == 4, f"Expected 4 conflicts, got: {status_codes}"

    # Verify all conflicts returned valid conflict envelopes
    for r in responses:
        if r.status_code == 409:
            err = r.json()
            assert err["error_code"] in ("SLOT_NOT_AVAILABLE", "SLOT_ALREADY_BOOKED", "SLOT_HELD_BY_ANOTHER_PATIENT")

    # Verify database state has exactly 1 appointment
    async with session_factory() as db:
        from sqlalchemy import select, func
        count_stmt = select(func.count()).select_from(Appointment).where(Appointment.slot_id == slot_id)
        total_appts = await db.scalar(count_stmt)
        assert total_appts == 1

        slot = await slot_engine.get_slot_by_id(db, slot_id)
        assert slot.status == SlotStatus.BOOKED
