"""Unit tests for User SQLAlchemy 2.0 relational entity."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.db.base import Base
from app.models.enums import UserRole
from app.models.user import User


@pytest.fixture
async def async_db():
    """Provide an isolated in-memory SQLite async database engine and sessionmaker."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user_success(async_db) -> None:
    """Verify standard user creation with default PATIENT role and timestamps."""
    async with async_db() as session:
        user = User(
            email="rahul.sharma@example.com",
            full_name="Rahul Sharma",
            phone_number="+919876543210",
        )
        session.add(user)
        await session.commit()

        stmt = select(User).where(User.email == "rahul.sharma@example.com")
        result = await session.execute(stmt)
        persisted = result.scalar_one()

        assert persisted.id is not None
        assert len(persisted.id) == 36
        assert persisted.email == "rahul.sharma@example.com"
        assert persisted.full_name == "Rahul Sharma"
        assert persisted.role == UserRole.PATIENT
        assert persisted.is_active is True
        assert persisted.is_verified is False
        assert persisted.created_at is not None
        assert repr(persisted) == f"<User id={persisted.id} email=rahul.sharma@example.com role={UserRole.PATIENT}>"


@pytest.mark.asyncio
async def test_user_unique_email_constraint(async_db) -> None:
    """Verify duplicate emails raise IntegrityError."""
    async with async_db() as session:
        user1 = User(
            email="duplicate@example.com",
            full_name="User One",
        )
        session.add(user1)
        await session.commit()

    async with async_db() as session:
        user2 = User(
            email="duplicate@example.com",
            full_name="User Two",
        )
        session.add(user2)
        with pytest.raises(IntegrityError):
            await session.commit()


@pytest.mark.asyncio
async def test_user_roles_assignment(async_db) -> None:
    """Verify distinct clinical roles can be assigned to user records."""
    async with async_db() as session:
        doctor = User(
            email="dr.priya@hospital.org",
            full_name="Dr. Priya Patel",
            role=UserRole.DOCTOR,
        )
        lab_tech = User(
            email="tech.anil@diagnostics.com",
            full_name="Anil Kumar",
            role=UserRole.LAB,
        )
        session.add_all([doctor, lab_tech])
        await session.commit()

        doctor_query = await session.scalar(select(User).where(User.email == "dr.priya@hospital.org"))
        lab_query = await session.scalar(select(User).where(User.email == "tech.anil@diagnostics.com"))

        assert doctor_query.role == UserRole.DOCTOR
        assert lab_query.role == UserRole.LAB
