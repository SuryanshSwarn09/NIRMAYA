"""Unit tests for PatientProfile SQLAlchemy 2.0 relational entity and ABHA integration."""

from datetime import date
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.db.base import Base
from app.models.enums import BloodGroup, Gender, UserRole
from app.models.patient import PatientProfile
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
async def test_create_patient_profile_with_abha(async_db) -> None:
    """Verify PatientProfile creation with clinical attributes and ABHA identifiers."""
    async with async_db() as session:
        user = User(
            email="arun.patel@example.com",
            full_name="Arun Patel",
            role=UserRole.PATIENT,
        )
        session.add(user)
        await session.flush()

        profile = PatientProfile(
            user_id=user.id,
            date_of_birth=date(1990, 5, 20),
            gender=Gender.MALE,
            blood_group=BloodGroup.O_POSITIVE,
            city="Ahmedabad",
            state="Gujarat",
            pincode="380001",
            emergency_contact_name="Sunita Patel",
            emergency_contact_phone="+919876543211",
            emergency_contact_relation="Spouse",
            abha_number="91-1234-5678-9012",
            abha_address="arun.patel@abdm",
        )
        session.add(profile)
        await session.commit()

        # Query back and verify
        stmt = select(PatientProfile).where(PatientProfile.user_id == user.id)
        persisted = (await session.execute(stmt)).scalar_one()

        assert persisted.id is not None
        assert persisted.date_of_birth == date(1990, 5, 20)
        assert persisted.gender == Gender.MALE
        assert persisted.blood_group == BloodGroup.O_POSITIVE
        assert persisted.abha_number == "91-1234-5678-9012"
        assert persisted.abha_address == "arun.patel@abdm"
        assert repr(persisted) == f"<PatientProfile id={persisted.id} user_id={user.id} abha_address=arun.patel@abdm>"


@pytest.mark.asyncio
async def test_patient_user_bidirectional_relationship(async_db) -> None:
    """Verify bidirectional navigation between User and PatientProfile."""
    async with async_db() as session:
        user = User(
            email="meera.nair@example.com",
            full_name="Meera Nair",
        )
        profile = PatientProfile(
            user=user,
            gender=Gender.FEMALE,
            blood_group=BloodGroup.B_POSITIVE,
            abha_address="meera@abdm",
        )
        session.add(user)
        await session.commit()

        # Query user with profile loaded
        query_user = await session.scalar(select(User).where(User.email == "meera.nair@example.com"))
        assert query_user.patient_profile is not None
        assert query_user.patient_profile.abha_address == "meera@abdm"
        assert query_user.patient_profile.user.full_name == "Meera Nair"


@pytest.mark.asyncio
async def test_patient_profile_cascade_deletion(async_db) -> None:
    """Verify deleting a User cascades to delete the associated PatientProfile."""
    async with async_db() as session:
        user = User(
            email="delete.me@example.com",
            full_name="Temporary User",
        )
        profile = PatientProfile(
            user=user,
            abha_address="temp@abdm",
        )
        session.add(user)
        await session.commit()

        user_id = user.id
        profile_id = profile.id

        # Delete user
        await session.delete(user)
        await session.commit()

        # Confirm both user and profile are gone
        remaining_user = await session.scalar(select(User).where(User.id == user_id))
        remaining_profile = await session.scalar(select(PatientProfile).where(PatientProfile.id == profile_id))

        assert remaining_user is None
        assert remaining_profile is None


@pytest.mark.asyncio
async def test_duplicate_abha_number_constraint(async_db) -> None:
    """Verify unique constraint on ABHA number prevents duplicate health records."""
    async with async_db() as session:
        user1 = User(email="user1@example.com", full_name="User One")
        user2 = User(email="user2@example.com", full_name="User Two")
        session.add_all([user1, user2])
        await session.flush()

        p1 = PatientProfile(user_id=user1.id, abha_number="11-2222-3333-4444")
        p2 = PatientProfile(user_id=user2.id, abha_number="11-2222-3333-4444")
        session.add(p1)
        await session.commit()

        session.add(p2)
        with pytest.raises(IntegrityError):
            await session.commit()
