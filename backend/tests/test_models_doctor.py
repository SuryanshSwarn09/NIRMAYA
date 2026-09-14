"""Unit tests for DoctorProfile SQLAlchemy 2.0 relational entity and ABDM HPR integration."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.db.base import Base
from app.models.doctor import DoctorProfile
from app.models.enums import MedicalSpecialty, UserRole
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
async def test_create_doctor_profile_with_hpr_id(async_db) -> None:
    """Verify DoctorProfile creation with medical credentials and ABDM HPR ID."""
    async with async_db() as session:
        user = User(
            email="dr.sharma@example.com",
            full_name="Dr. Rajesh Sharma",
            role=UserRole.DOCTOR,
        )
        session.add(user)
        await session.flush()

        doctor = DoctorProfile(
            user_id=user.id,
            registration_number="MCI-123456-A",
            medical_council="Delhi Medical Council",
            specialty=MedicalSpecialty.CARDIOLOGY,
            qualifications="MBBS, MD (Medicine), DM (Cardiology)",
            experience_years=15,
            consultation_fee=1500,
            hospital_affiliation="Apollo Indraprastha Hospital",
            bio="Leading cardiologist specializing in complex coronary interventions.",
            is_available_for_teleconsult=True,
            hpr_id="dr.rajesh@hpr.abdm",
        )
        session.add(doctor)
        await session.commit()

        stmt = select(DoctorProfile).where(DoctorProfile.user_id == user.id)
        persisted = (await session.execute(stmt)).scalar_one()

        assert persisted.id is not None
        assert persisted.registration_number == "MCI-123456-A"
        assert persisted.medical_council == "Delhi Medical Council"
        assert persisted.specialty == MedicalSpecialty.CARDIOLOGY
        assert persisted.qualifications == "MBBS, MD (Medicine), DM (Cardiology)"
        assert persisted.experience_years == 15
        assert persisted.consultation_fee == 1500
        assert persisted.hospital_affiliation == "Apollo Indraprastha Hospital"
        assert persisted.is_available_for_teleconsult is True
        assert persisted.hpr_id == "dr.rajesh@hpr.abdm"
        assert repr(persisted) == f"<DoctorProfile id={persisted.id} user_id={user.id} reg=MCI-123456-A specialty={MedicalSpecialty.CARDIOLOGY}>"


@pytest.mark.asyncio
async def test_doctor_user_bidirectional_relationship(async_db) -> None:
    """Verify bidirectional navigation between User and DoctorProfile."""
    async with async_db() as session:
        user = User(
            email="dr.anita@example.com",
            full_name="Dr. Anita Desai",
            role=UserRole.DOCTOR,
        )
        doctor = DoctorProfile(
            user=user,
            registration_number="MMC-98765-B",
            medical_council="Maharashtra Medical Council",
            specialty=MedicalSpecialty.PEDIATRICS,
            qualifications="MBBS, DCH, MD (Pediatrics)",
            hpr_id="dr.anita@hpr.abdm",
        )
        session.add(user)
        await session.commit()

        query_user = await session.scalar(select(User).where(User.email == "dr.anita@example.com"))
        assert query_user.doctor_profile is not None
        assert query_user.doctor_profile.registration_number == "MMC-98765-B"
        assert query_user.doctor_profile.user.full_name == "Dr. Anita Desai"


@pytest.mark.asyncio
async def test_doctor_profile_cascade_deletion(async_db) -> None:
    """Verify deleting a User cascades to delete the associated DoctorProfile."""
    async with async_db() as session:
        user = User(
            email="dr.temp@example.com",
            full_name="Dr. Temp User",
            role=UserRole.DOCTOR,
        )
        doctor = DoctorProfile(
            user=user,
            registration_number="TEMP-11111",
            medical_council="Karnataka Medical Council",
            specialty=MedicalSpecialty.GENERAL_MEDICINE,
            qualifications="MBBS",
        )
        session.add(user)
        await session.commit()

        user_id = user.id
        doc_id = doctor.id

        await session.delete(user)
        await session.commit()

        remaining_user = await session.scalar(select(User).where(User.id == user_id))
        remaining_doc = await session.scalar(select(DoctorProfile).where(DoctorProfile.id == doc_id))

        assert remaining_user is None
        assert remaining_doc is None


@pytest.mark.asyncio
async def test_duplicate_registration_number_constraint(async_db) -> None:
    """Verify unique constraint on registration_number prevents duplicates."""
    async with async_db() as session:
        u1 = User(email="doc1@example.com", full_name="Doc One")
        u2 = User(email="doc2@example.com", full_name="Doc Two")
        session.add_all([u1, u2])
        await session.flush()

        d1 = DoctorProfile(
            user_id=u1.id,
            registration_number="DUP-REG-001",
            medical_council="Council A",
            specialty=MedicalSpecialty.DERMATOLOGY,
            qualifications="MBBS, MD",
        )
        d2 = DoctorProfile(
            user_id=u2.id,
            registration_number="DUP-REG-001",
            medical_council="Council B",
            specialty=MedicalSpecialty.DERMATOLOGY,
            qualifications="MBBS, MD",
        )
        session.add(d1)
        await session.commit()

        session.add(d2)
        with pytest.raises(IntegrityError):
            await session.commit()


@pytest.mark.asyncio
async def test_duplicate_hpr_id_constraint(async_db) -> None:
    """Verify unique constraint on ABDM HPR ID prevents duplicates."""
    async with async_db() as session:
        u1 = User(email="hpr1@example.com", full_name="Doc HPR 1")
        u2 = User(email="hpr2@example.com", full_name="Doc HPR 2")
        session.add_all([u1, u2])
        await session.flush()

        d1 = DoctorProfile(
            user_id=u1.id,
            registration_number="REG-HPR-1",
            medical_council="Council A",
            specialty=MedicalSpecialty.NEUROLOGY,
            qualifications="MBBS, DM",
            hpr_id="dr.duplicate@hpr.abdm",
        )
        d2 = DoctorProfile(
            user_id=u2.id,
            registration_number="REG-HPR-2",
            medical_council="Council A",
            specialty=MedicalSpecialty.NEUROLOGY,
            qualifications="MBBS, DM",
            hpr_id="dr.duplicate@hpr.abdm",
        )
        session.add(d1)
        await session.commit()

        session.add(d2)
        with pytest.raises(IntegrityError):
            await session.commit()
