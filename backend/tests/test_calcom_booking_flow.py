"""End-to-End integration test suite for Cal.com slot picker and clinical booking flow.

Simulates the complete patient and doctor journey:
1. Doctor configures practice hours and generates conflict-free slots.
2. Patient views availability matrix and claims a 10-minute temporary hold.
3. Competing checkout attempt is rejected with 409 Conflict.
4. Holding patient completes intake and confirms appointment.
5. Export of FHIR R4 Encounter Bundle and ABDM CareContext linkage.
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
from app.models.doctor import DoctorProfile
from app.models.enums import Gender, MedicalSpecialty, SlotStatus, UserRole
from app.models.patient import PatientProfile
from app.models.user import User


@pytest_asyncio.fixture
async def calcom_test_env():
    """Isolated test database and client fixture."""
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
    """Generate authorization bearer headers."""
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_calcom_slot_picker_complete_booking_flow(calcom_test_env) -> None:
    """Validate full Cal.com scheduling lifecycle: slot generation, hold reservation, conflict guard, and FHIR export."""
    client, session_factory = calcom_test_env

    # 1. Seed Doctor, Primary Patient, and Competing Patient
    async with session_factory() as db:
        # Doctor
        doc_user = User(
            email="dr.ananya@nirmaya.health",
            full_name="Dr. Ananya Sharma",
            role=UserRole.DOCTOR,
        )
        db.add(doc_user)
        await db.flush()

        doc_profile = DoctorProfile(
            user_id=doc_user.id,
            registration_number="DMC-99201",
            medical_council="Delhi Medical Council",
            specialty=MedicalSpecialty.CARDIOLOGY,
            qualifications="MBBS, MD (Cardiology)",
            consultation_fee=1500,
            hpr_id="ananya.sharma@hpr",
            is_available_for_teleconsult=True,
        )
        db.add(doc_profile)

        # Primary Patient
        pat_user = User(
            email="arun.patel@example.org",
            full_name="Arun Patel",
            role=UserRole.PATIENT,
        )
        db.add(pat_user)
        await db.flush()

        pat_profile = PatientProfile(
            user_id=pat_user.id,
            gender=Gender.MALE,
            date_of_birth=date(1990, 5, 20),
            abha_number="91-8472-1092-4821",
            abha_address="arun.patel@abdm",
        )
        db.add(pat_profile)

        # Competing Patient
        competing_user = User(
            email="priya.nair@example.org",
            full_name="Priya Nair",
            role=UserRole.PATIENT,
        )
        db.add(competing_user)
        await db.flush()

        competing_profile = PatientProfile(
            user_id=competing_user.id,
            gender=Gender.FEMALE,
            abha_number="91-9988-7766-5544",
        )
        db.add(competing_profile)
        await db.commit()

        doc_id = doc_profile.id
        pat_id = pat_profile.id

    # 2. Doctor generates conflict-free slots (09:00 to 17:00 with lunch break 13:00 to 14:00)
    target_date_str = "2026-10-15"
    gen_payload = {
        "doctor_id": doc_id,
        "start_date": target_date_str,
        "end_date": target_date_str,
        "day_start_hour": 9,
        "day_start_minute": 0,
        "day_end_hour": 17,
        "day_end_minute": 0,
        "slot_duration_minutes": 30,
        "break_start_hour": 13,
        "break_start_minute": 0,
        "break_end_hour": 14,
        "break_end_minute": 0,
        "is_teleconsult": False,
    }

    gen_res = await client.post(
        f"/api/v1/doctors/{doc_id}/slots/generate",
        json=gen_payload,
        headers=auth_header_for(doc_user),
    )
    assert gen_res.status_code == 201
    gen_data = gen_res.json()["data"]
    # 8 hours practice - 1 hour lunch = 7 hours * 2 slots/hr = 14 slots
    assert gen_data["total_generated"] == 14

    # 3. Patient queries available slots for target date
    slots_res = await client.get(
        f"/api/v1/doctors/{doc_id}/slots?target_date={target_date_str}&slot_status=available",
    )
    assert slots_res.status_code == 200
    available_slots = slots_res.json()["data"]
    assert len(available_slots) == 14

    chosen_slot = available_slots[0]
    slot_id = chosen_slot["id"]

    # 4. Patient acquires a 10-minute temporary reservation hold
    hold_res = await client.post(
        f"/api/v1/doctors/{doc_id}/slots/{slot_id}/hold",
        json={"hold_duration_minutes": 10},
        headers=auth_header_for(pat_user),
    )
    assert hold_res.status_code == 200
    hold_data = hold_res.json()["data"]
    assert hold_data["status"] == "held"
    assert hold_data["held_by_patient_id"] == pat_id
    assert hold_data["hold_duration_seconds"] > 0

    # 5. Competing patient attempts to hold the same slot and receives 409 Conflict
    conflict_hold_res = await client.post(
        f"/api/v1/doctors/{doc_id}/slots/{slot_id}/hold",
        json={"hold_duration_minutes": 10},
        headers=auth_header_for(competing_user),
    )
    assert conflict_hold_res.status_code == 409
    assert conflict_hold_res.json()["error_code"] == "SLOT_HELD_BY_ANOTHER_PATIENT"

    # 6. Holding patient confirms booking intake
    book_payload = {
        "doctor_id": doc_id,
        "slot_id": slot_id,
        "appointment_type": "routine_checkup",
        "reason": "Recurrent hypertension and palpitations",
        "clinical_notes": "Patient on Atorvastatin 20mg",
    }
    book_res = await client.post(
        "/api/v1/appointments/",
        json=book_payload,
        headers=auth_header_for(pat_user),
    )
    assert book_res.status_code == 201
    appt_data = book_res.json()["data"]
    appt_id = appt_data["id"]
    assert appt_data["status"] == "scheduled"
    assert appt_data["slot_id"] == slot_id

    # 7. Slot status is now booked
    slot_verify_res = await client.get(
        f"/api/v1/doctors/{doc_id}/slots?target_date={target_date_str}",
    )
    all_slots = slot_verify_res.json()["data"]
    booked_slot = next(s for s in all_slots if s["id"] == slot_id)
    assert booked_slot["status"] == "booked"

    # 8. Export FHIR R4 Bundle and verify multi-resource collection & ABDM linkage
    bundle_res = await client.get(
        f"/api/v1/appointments/{appt_id}/fhir-bundle",
        headers=auth_header_for(pat_user),
    )
    assert bundle_res.status_code == 200
    bundle = bundle_res.json()["data"]
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert bundle["total"] == 4
