"""Unit tests for DiagnosticLabFacility SQLAlchemy 2.0 relational entity and ABDM HFR integration."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.db.base import Base
from app.models.enums import LabAccreditation, UserRole
from app.models.lab import DiagnosticLabFacility
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
async def test_create_lab_facility_with_hfr_id(async_db) -> None:
    """Verify DiagnosticLabFacility creation with accreditation and ABDM HFR ID."""
    async with async_db() as session:
        user = User(
            email="admin@apollo-diagnostics.com",
            full_name="Apollo Diagnostics Admin",
            role=UserRole.LAB,
        )
        session.add(user)
        await session.flush()

        lab = DiagnosticLabFacility(
            user_id=user.id,
            facility_name="Apollo Diagnostics Center",
            license_number="DL-LAB-2024-0987",
            accreditation=LabAccreditation.NABL,
            accreditation_number="NABL-MC-5432",
            is_nabl_certified=True,
            contact_person="Dr. Rajeshwari Swaminathan",
            contact_phone="+919876543210",
            contact_email="care@apollodiagnostics.example.com",
            address_line="Sector 18, Commercial Block B",
            city="Gurugram",
            state="Haryana",
            pincode="122001",
            supported_tests="CBC, Lipid Profile, HbA1c, Thyroid Panel, RT-PCR, Liver Function Test",
            hfr_id="IN0610001234@hfr",
        )
        session.add(lab)
        await session.commit()

        stmt = select(DiagnosticLabFacility).where(DiagnosticLabFacility.user_id == user.id)
        persisted = (await session.execute(stmt)).scalar_one()

        assert persisted.id is not None
        assert persisted.facility_name == "Apollo Diagnostics Center"
        assert persisted.license_number == "DL-LAB-2024-0987"
        assert persisted.accreditation == LabAccreditation.NABL
        assert persisted.accreditation_number == "NABL-MC-5432"
        assert persisted.is_nabl_certified is True
        assert persisted.contact_person == "Dr. Rajeshwari Swaminathan"
        assert persisted.contact_phone == "+919876543210"
        assert persisted.city == "Gurugram"
        assert persisted.state == "Haryana"
        assert persisted.pincode == "122001"
        assert persisted.hfr_id == "IN0610001234@hfr"
        assert repr(persisted) == (
            f"<DiagnosticLabFacility id={persisted.id} user_id={user.id} "
            f"facility=Apollo Diagnostics Center accreditation={LabAccreditation.NABL}>"
        )


@pytest.mark.asyncio
async def test_lab_user_bidirectional_relationship(async_db) -> None:
    """Verify bidirectional navigation between User and DiagnosticLabFacility."""
    async with async_db() as session:
        user = User(
            email="tech@thyrocare-partner.com",
            full_name="Thyrocare Center Head",
            role=UserRole.LAB,
        )
        lab = DiagnosticLabFacility(
            user=user,
            facility_name="Metropolis Diagnostic Hub",
            license_number="MH-LAB-87654",
            accreditation=LabAccreditation.CAP,
            contact_person="Sunil Varma",
            contact_phone="+919811223344",
            contact_email="sunil@metropolis.example.com",
            address_line="Andheri East",
            city="Mumbai",
            state="Maharashtra",
            pincode="400069",
            hfr_id="IN2710009876@hfr",
        )
        session.add(user)
        await session.commit()

        query_user = await session.scalar(select(User).where(User.email == "tech@thyrocare-partner.com"))
        assert query_user.lab_facility is not None
        assert query_user.lab_facility.facility_name == "Metropolis Diagnostic Hub"
        assert query_user.lab_facility.user.full_name == "Thyrocare Center Head"


@pytest.mark.asyncio
async def test_lab_facility_cascade_deletion(async_db) -> None:
    """Verify deleting a User cascades to delete the associated DiagnosticLabFacility."""
    async with async_db() as session:
        user = User(
            email="temp.lab@example.com",
            full_name="Temporary Lab Admin",
            role=UserRole.LAB,
        )
        lab = DiagnosticLabFacility(
            user=user,
            facility_name="Temp Pathology Lab",
            license_number="TEMP-LAB-12345",
            accreditation=LabAccreditation.ISO_15189,
            contact_person="Temp Contact",
            contact_phone="+919000000000",
            contact_email="temp@lab.example.com",
            address_line="Test Road",
            city="Bengaluru",
            state="Karnataka",
            pincode="560001",
        )
        session.add(user)
        await session.commit()

        user_id = user.id
        lab_id = lab.id

        await session.delete(user)
        await session.commit()

        remaining_user = await session.scalar(select(User).where(User.id == user_id))
        remaining_lab = await session.scalar(select(DiagnosticLabFacility).where(DiagnosticLabFacility.id == lab_id))

        assert remaining_user is None
        assert remaining_lab is None


@pytest.mark.asyncio
async def test_duplicate_license_number_constraint(async_db) -> None:
    """Verify unique constraint on license_number prevents duplicates."""
    async with async_db() as session:
        u1 = User(email="lab1@example.com", full_name="Lab One")
        u2 = User(email="lab2@example.com", full_name="Lab Two")
        session.add_all([u1, u2])
        await session.flush()

        l1 = DiagnosticLabFacility(
            user_id=u1.id,
            facility_name="Lab Alpha",
            license_number="DUP-LIC-001",
            accreditation=LabAccreditation.NABL,
            contact_person="Person A",
            contact_phone="+919111111111",
            contact_email="a@alpha.example.com",
            address_line="Alpha Street",
            city="Delhi",
            state="Delhi",
            pincode="110001",
        )
        l2 = DiagnosticLabFacility(
            user_id=u2.id,
            facility_name="Lab Beta",
            license_number="DUP-LIC-001",
            accreditation=LabAccreditation.NABL,
            contact_person="Person B",
            contact_phone="+919222222222",
            contact_email="b@beta.example.com",
            address_line="Beta Street",
            city="Delhi",
            state="Delhi",
            pincode="110001",
        )
        session.add(l1)
        await session.commit()

        session.add(l2)
        with pytest.raises(IntegrityError):
            await session.commit()


@pytest.mark.asyncio
async def test_duplicate_hfr_id_constraint(async_db) -> None:
    """Verify unique constraint on ABDM HFR ID prevents duplicates."""
    async with async_db() as session:
        u1 = User(email="labhfr1@example.com", full_name="Lab HFR 1")
        u2 = User(email="labhfr2@example.com", full_name="Lab HFR 2")
        session.add_all([u1, u2])
        await session.flush()

        l1 = DiagnosticLabFacility(
            user_id=u1.id,
            facility_name="Facility 1",
            license_number="LIC-HFR-1",
            accreditation=LabAccreditation.NABL,
            contact_person="Contact 1",
            contact_phone="+919333333333",
            contact_email="c1@example.com",
            address_line="Road 1",
            city="Chennai",
            state="Tamil Nadu",
            pincode="600001",
            hfr_id="IN3310005555@hfr",
        )
        l2 = DiagnosticLabFacility(
            user_id=u2.id,
            facility_name="Facility 2",
            license_number="LIC-HFR-2",
            accreditation=LabAccreditation.NABL,
            contact_person="Contact 2",
            contact_phone="+919444444444",
            contact_email="c2@example.com",
            address_line="Road 2",
            city="Chennai",
            state="Tamil Nadu",
            pincode="600001",
            hfr_id="IN3310005555@hfr",
        )
        session.add(l1)
        await session.commit()

        session.add(l2)
        with pytest.raises(IntegrityError):
            await session.commit()
