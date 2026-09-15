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
