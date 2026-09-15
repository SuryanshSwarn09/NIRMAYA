"""Asynchronous database seeder service for NIRMAYA.

Performs idempotent synthetic clinical fixture generation and optional database reset.
"""

from typing import Any, Dict
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.fixtures import (
    ADMIN_FIXTURE,
    DOCTOR_FIXTURES,
    LAB_FIXTURES,
    PATIENT_FIXTURES,
)


async def clear_database(session: AsyncSession) -> Dict[str, int]:
    """Truncate all core entities in reverse foreign key order."""
    from app.models.doctor import DoctorProfile
    from app.models.lab import DiagnosticLabFacility
    from app.models.patient import PatientProfile
    from app.models.user import User

    labs_deleted = (await session.execute(delete(DiagnosticLabFacility))).rowcount or 0
    doctors_deleted = (await session.execute(delete(DoctorProfile))).rowcount or 0
    patients_deleted = (await session.execute(delete(PatientProfile))).rowcount or 0
    users_deleted = (await session.execute(delete(User))).rowcount or 0
    await session.commit()

    return {
        "users_deleted": users_deleted,
        "patients_deleted": patients_deleted,
        "doctors_deleted": doctors_deleted,
        "labs_deleted": labs_deleted,
    }


async def seed_database(session: AsyncSession, reset: bool = False) -> Dict[str, Any]:
    """Seed the database with standardized synthetic clinical fixtures.

    Args:
        session: Active asynchronous SQLAlchemy database session.
        reset: If True, clear existing core entity records before seeding.

    Returns:
        Summary dictionary containing counts of entities seeded or existing.
    """
    from app.models.doctor import DoctorProfile
    from app.models.lab import DiagnosticLabFacility
    from app.models.patient import PatientProfile
    from app.models.user import User

    cleared_stats = {}
    if reset:
        cleared_stats = await clear_database(session)

    seeded_users = 0
    seeded_patients = 0
    seeded_doctors = 0
    seeded_labs = 0

    # 1. Admin User
    admin_stmt = select(User).where(User.email == ADMIN_FIXTURE["email"])
    existing_admin = (await session.execute(admin_stmt)).scalar_one_or_none()
    if not existing_admin:
        admin_user = User(**ADMIN_FIXTURE)
        session.add(admin_user)
        seeded_users += 1

    # 2. Patients & Clinical Demographics
    for p in PATIENT_FIXTURES:
        user_stmt = select(User).where(User.email == p["user"]["email"])
        user = (await session.execute(user_stmt)).scalar_one_or_none()
        if not user:
            user = User(**p["user"])
            session.add(user)
            seeded_users += 1

        await session.flush()

        profile_stmt = select(PatientProfile).where(PatientProfile.user_id == user.id)
        profile = (await session.execute(profile_stmt)).scalar_one_or_none()
        if not profile:
            profile = PatientProfile(user_id=user.id, **p["profile"])
            session.add(profile)
            seeded_patients += 1

    # 3. Doctors & Clinical Credentials
    for d in DOCTOR_FIXTURES:
        user_stmt = select(User).where(User.email == d["user"]["email"])
        user = (await session.execute(user_stmt)).scalar_one_or_none()
        if not user:
            user = User(**d["user"])
            session.add(user)
            seeded_users += 1

        await session.flush()

        doc_stmt = select(DoctorProfile).where(DoctorProfile.user_id == user.id)
        doctor = (await session.execute(doc_stmt)).scalar_one_or_none()
        if not doctor:
            doctor = DoctorProfile(user_id=user.id, **d["profile"])
            session.add(doctor)
            seeded_doctors += 1

    # 4. Diagnostic Lab Facilities
    for lab_item in LAB_FIXTURES:
        user_stmt = select(User).where(User.email == lab_item["user"]["email"])
        user = (await session.execute(user_stmt)).scalar_one_or_none()
        if not user:
            user = User(**lab_item["user"])
            session.add(user)
            seeded_users += 1

        await session.flush()

        lab_stmt = select(DiagnosticLabFacility).where(DiagnosticLabFacility.user_id == user.id)
        facility = (await session.execute(lab_stmt)).scalar_one_or_none()
        if not facility:
            facility = DiagnosticLabFacility(user_id=user.id, **lab_item["facility"])
            session.add(facility)
            seeded_labs += 1

    await session.commit()

    return {
        "status": "success",
        "was_reset": reset,
        "cleared_stats": cleared_stats,
        "users_seeded": seeded_users,
        "patients_seeded": seeded_patients,
        "doctors_seeded": seeded_doctors,
        "labs_seeded": seeded_labs,
        "total_seeded": seeded_users + seeded_patients + seeded_doctors + seeded_labs,
    }
