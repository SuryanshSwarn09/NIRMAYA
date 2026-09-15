"""Unit tests for asynchronous database seeder service and fixture verification."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.db.base import Base
from app.db.seeder import seed_database
from app.models.doctor import DoctorProfile
from app.models.lab import DiagnosticLabFacility
from app.models.patient import PatientProfile
from app.models.user import User


@pytest.fixture
async def async_db():
    """Provide an isolated in-memory SQLite database sessionmaker for seeder tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_database_success(async_db) -> None:
    """Verify standard execution of seed_database creates all fixtures."""
    async with async_db() as session:
        result = await seed_database(session, reset=False)

        assert result["status"] == "success"
        assert result["users_seeded"] == 10
        assert result["patients_seeded"] == 3
        assert result["doctors_seeded"] == 3
        assert result["labs_seeded"] == 3
        assert result["total_seeded"] == 19

        # Verify persisted counts in database
        user_count = await session.scalar(select(func.count(User.id)))
        patient_count = await session.scalar(select(func.count(PatientProfile.id)))
        doctor_count = await session.scalar(select(func.count(DoctorProfile.id)))
        lab_count = await session.scalar(select(func.count(DiagnosticLabFacility.id)))

        assert user_count == 10
        assert patient_count == 3
        assert doctor_count == 3
        assert lab_count == 3


@pytest.mark.asyncio
async def test_seed_database_idempotent(async_db) -> None:
    """Verify running seed_database multiple times does not create duplicate entries."""
    async with async_db() as session:
        # First execution
        first_run = await seed_database(session, reset=False)
        assert first_run["total_seeded"] == 19

        # Second execution (idempotent run)
        second_run = await seed_database(session, reset=False)
        assert second_run["total_seeded"] == 0
        assert second_run["users_seeded"] == 0
        assert second_run["patients_seeded"] == 0
        assert second_run["doctors_seeded"] == 0
        assert second_run["labs_seeded"] == 0

        # Verify counts remained untouched
        user_count = await session.scalar(select(func.count(User.id)))
        assert user_count == 10


@pytest.mark.asyncio
async def test_seed_database_reset_mode(async_db) -> None:
    """Verify reset=True clears existing entities and freshly re-seeds."""
    async with async_db() as session:
        # Initial seed
        await seed_database(session, reset=False)

        # Reset and re-seed
        reset_result = await seed_database(session, reset=True)
        assert reset_result["was_reset"] is True
        assert reset_result["cleared_stats"]["users_deleted"] == 10
        assert reset_result["cleared_stats"]["patients_deleted"] == 3
        assert reset_result["cleared_stats"]["doctors_deleted"] == 3
        assert reset_result["cleared_stats"]["labs_deleted"] == 3
        assert reset_result["total_seeded"] == 19

        # Verify post-reset counts
        user_count = await session.scalar(select(func.count(User.id)))
        assert user_count == 10


from sqlalchemy.orm import selectinload


@pytest.mark.asyncio
async def test_seeded_entities_relationship_integrity(async_db) -> None:
    """Verify relational navigation and ABDM/HPR/HFR identifier integrity on seeded records."""
    async with async_db() as session:
        await seed_database(session, reset=False)

        # 1. Verify Patient and ABHA linkage
        arun_stmt = (
            select(User)
            .options(selectinload(User.patient_profile))
            .where(User.email == "arun.patel@example.com")
        )
        arun_user = await session.scalar(arun_stmt)
        assert arun_user is not None
        assert arun_user.patient_profile is not None
        assert arun_user.patient_profile.abha_number == "91-1029-3847-5610"
        assert arun_user.patient_profile.abha_address == "arun.patel@abdm"
        assert arun_user.patient_profile.city == "Ahmedabad"

        # 2. Verify Doctor and HPR linkage
        rajesh_stmt = (
            select(User)
            .options(selectinload(User.doctor_profile))
            .where(User.email == "dr.rajesh@nirmaya.health")
        )
        rajesh_user = await session.scalar(rajesh_stmt)
        assert rajesh_user is not None
        assert rajesh_user.doctor_profile is not None
        assert rajesh_user.doctor_profile.hpr_id == "dr.rajesh@hpr.abdm"
        assert rajesh_user.doctor_profile.registration_number == "MCI-2008-14259"
        assert rajesh_user.doctor_profile.consultation_fee == 1500

        # 3. Verify Lab and HFR linkage
        apollo_stmt = (
            select(User)
            .options(selectinload(User.lab_facility))
            .where(User.email == "admin.apollo@diagnostics.example.com")
        )
        apollo_user = await session.scalar(apollo_stmt)
        assert apollo_user is not None
        assert apollo_user.lab_facility is not None
        assert apollo_user.lab_facility.hfr_id == "IN-HR-HFR-001234"
        assert apollo_user.lab_facility.license_number == "DL-LAB-2021-0089"
        assert apollo_user.lab_facility.is_nabl_certified is True
