"""Unit test suite for Doctor EMR service layer, clinical queries, and uniqueness validation."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.exceptions import AppException, EntityNotFoundException
from app.db.base import Base
from app.models.enums import MedicalSpecialty, UserRole
from app.models.user import User
from app.schemas.doctor import DoctorProfileCreate, DoctorProfileUpdate
from app.services.doctor import (
    create_doctor_profile,
    delete_doctor_profile,
    get_doctor_by_hpr_id,
    get_doctor_by_id,
    get_doctor_by_registration_number,
    get_doctor_by_user_id,
    list_doctors,
    update_doctor_profile,
)


@pytest_asyncio.fixture
async def async_db_session():
    """Provide an isolated in-memory SQLite async database session for doctor service unit tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_doctor_profile_success(async_db_session: AsyncSession):
    """Verify standard doctor profile creation with full credentials and ABDM HPR linkage."""
    user = User(
        id="usr-doc-001",
        email="dr.alok@nirmaya.health",
        full_name="Dr. Alok Verma",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    async_db_session.add(user)
    await async_db_session.commit()

    payload = DoctorProfileCreate(
        user_id=user.id,
        registration_number="KMC-2012-98745",
        medical_council="Karnataka Medical Council",
        specialty=MedicalSpecialty.CARDIOLOGY,
        qualifications="MBBS, MD, DM (Cardiology)",
        experience_years=12,
        consultation_fee=1200,
        hospital_affiliation="Narayana Institute of Cardiac Sciences",
        bio="Interventional cardiologist with focus on preventive cardiology.",
        is_available_for_teleconsult=True,
        hpr_id="dr.alok.verma@hpr.abdm",
    )

    doctor = await create_doctor_profile(async_db_session, payload)
    assert doctor.id is not None
    assert doctor.user_id == user.id
    assert doctor.registration_number == "KMC-2012-98745"
    assert doctor.specialty == MedicalSpecialty.CARDIOLOGY
    assert doctor.consultation_fee == 1200
    assert doctor.hpr_id == "dr.alok.verma@hpr.abdm"
    assert doctor.user is not None
    assert doctor.user.full_name == "Dr. Alok Verma"


@pytest.mark.asyncio
async def test_create_doctor_missing_user_id(async_db_session: AsyncSession):
    """Verify creating a doctor profile without target user_id raises 400 MISSING_USER_ID."""
    payload = DoctorProfileCreate(
        user_id=None,
        registration_number="REG-111",
        medical_council="Delhi Medical Council",
        qualifications="MBBS",
    )
    with pytest.raises(AppException) as exc_info:
        await create_doctor_profile(async_db_session, payload, user_id=None)
    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "MISSING_USER_ID"


@pytest.mark.asyncio
async def test_create_doctor_nonexistent_user(async_db_session: AsyncSession):
    """Verify creating a doctor profile for a non-existent user raises 404 EntityNotFoundException."""
    payload = DoctorProfileCreate(
        user_id="non-existent-user-id",
        registration_number="REG-222",
        medical_council="Maharashtra Medical Council",
        qualifications="MBBS",
    )
    with pytest.raises(EntityNotFoundException) as exc_info:
        await create_doctor_profile(async_db_session, payload)
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "NOT_FOUND"


@pytest.mark.asyncio
async def test_create_doctor_duplicate_profile_for_user(async_db_session: AsyncSession):
    """Verify a user cannot have more than one active doctor profile (409 Conflict)."""
    user = User(id="u-doc-dup", email="doc.dup@h.org", full_name="Dr. Dup", role=UserRole.DOCTOR, is_active=True)
    async_db_session.add(user)
    await async_db_session.commit()

    payload1 = DoctorProfileCreate(
        user_id=user.id,
        registration_number="REG-DUP-1",
        medical_council="KMC",
        qualifications="MBBS",
    )
    await create_doctor_profile(async_db_session, payload1)

    payload2 = DoctorProfileCreate(
        user_id=user.id,
        registration_number="REG-DUP-2",
        medical_council="KMC",
        qualifications="MD",
    )
    with pytest.raises(AppException) as exc_info:
        await create_doctor_profile(async_db_session, payload2)
    assert exc_info.value.status_code == 409
    assert exc_info.value.error_code == "PROFILE_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_create_doctor_duplicate_registration_number(async_db_session: AsyncSession):
    """Verify reusing an existing Medical Council registration number raises 409 Conflict."""
    u1 = User(id="u1", email="u1@h.org", full_name="D1", role=UserRole.DOCTOR, is_active=True)
    u2 = User(id="u2", email="u2@h.org", full_name="D2", role=UserRole.DOCTOR, is_active=True)
    async_db_session.add_all([u1, u2])
    await async_db_session.commit()

    p1 = DoctorProfileCreate(user_id=u1.id, registration_number="SHARED-REG-101", medical_council="KMC", qualifications="MBBS")
    await create_doctor_profile(async_db_session, p1)

    p2 = DoctorProfileCreate(user_id=u2.id, registration_number="SHARED-REG-101", medical_council="MMC", qualifications="MS")
    with pytest.raises(AppException) as exc_info:
        await create_doctor_profile(async_db_session, p2)
    assert exc_info.value.status_code == 409
    assert exc_info.value.error_code == "DUPLICATE_REGISTRATION_NUMBER"


@pytest.mark.asyncio
async def test_create_doctor_duplicate_hpr_id(async_db_session: AsyncSession):
    """Verify reusing an existing ABDM HPR handle raises 409 Conflict."""
    u1 = User(id="u1", email="u1@h.org", full_name="D1", role=UserRole.DOCTOR, is_active=True)
    u2 = User(id="u2", email="u2@h.org", full_name="D2", role=UserRole.DOCTOR, is_active=True)
    async_db_session.add_all([u1, u2])
    await async_db_session.commit()

    p1 = DoctorProfileCreate(user_id=u1.id, registration_number="REG-R1", medical_council="KMC", qualifications="MBBS", hpr_id="dr.shared@hpr.abdm")
    await create_doctor_profile(async_db_session, p1)

    p2 = DoctorProfileCreate(user_id=u2.id, registration_number="REG-R2", medical_council="KMC", qualifications="MS", hpr_id="dr.shared@hpr.abdm")
    with pytest.raises(AppException) as exc_info:
        await create_doctor_profile(async_db_session, p2)
    assert exc_info.value.status_code == 409
    assert exc_info.value.error_code == "DUPLICATE_HPR_ID"


@pytest.mark.asyncio
async def test_get_doctor_lookups(async_db_session: AsyncSession):
    """Verify retrieval by UUID, user ID, registration number, and ABDM HPR ID."""
    user = User(id="u-lookup", email="lookup@h.org", full_name="Dr. Lookup", role=UserRole.DOCTOR, is_active=True)
    async_db_session.add(user)
    await async_db_session.commit()

    p = DoctorProfileCreate(
        user_id=user.id,
        registration_number="REG-LOOKUP-99",
        medical_council="Tamil Nadu Medical Council",
        specialty=MedicalSpecialty.PEDIATRICS,
        qualifications="MBBS, DCH",
        hpr_id="dr.lookup@hpr.abdm",
    )
    doc = await create_doctor_profile(async_db_session, p)

    # 1. By ID
    by_id = await get_doctor_by_id(async_db_session, doc.id)
    assert by_id is not None
    assert by_id.id == doc.id

    # 2. By User ID
    by_user = await get_doctor_by_user_id(async_db_session, user.id)
    assert by_user is not None
    assert by_user.id == doc.id

    # 3. By Registration Number
    by_reg = await get_doctor_by_registration_number(async_db_session, "REG-LOOKUP-99")
    assert by_reg is not None
    assert by_reg.id == doc.id

    # 4. By HPR ID
    by_hpr = await get_doctor_by_hpr_id(async_db_session, "dr.lookup@hpr.abdm")
    assert by_hpr is not None
    assert by_hpr.id == doc.id


@pytest.mark.asyncio
async def test_list_doctors_with_clinical_filters(async_db_session: AsyncSession):
    """Verify paginated doctor listing with filters for specialty, teleconsultation, fee, and query."""
    u1 = User(id="u1", email="d1@h.org", full_name="Dr. Meera Nambiar", role=UserRole.DOCTOR, is_active=True)
    u2 = User(id="u2", email="d2@h.org", full_name="Dr. Rohan Seth", role=UserRole.DOCTOR, is_active=True)
    u3 = User(id="u3", email="d3@h.org", full_name="Dr. Sunita Rao", role=UserRole.DOCTOR, is_active=True)
    async_db_session.add_all([u1, u2, u3])
    await async_db_session.commit()

    await create_doctor_profile(
        async_db_session,
        DoctorProfileCreate(
            user_id=u1.id,
            registration_number="R-CARD-1",
            medical_council="KMC",
            specialty=MedicalSpecialty.CARDIOLOGY,
            qualifications="MD",
            experience_years=15,
            consultation_fee=1500,
            hospital_affiliation="Fortis Bannerghatta",
            is_available_for_teleconsult=True,
            hpr_id="dr.meera@hpr.abdm",
        ),
    )
    await create_doctor_profile(
        async_db_session,
        DoctorProfileCreate(
            user_id=u2.id,
            registration_number="R-DERM-1",
            medical_council="MMC",
            specialty=MedicalSpecialty.DERMATOLOGY,
            qualifications="DDVL",
            experience_years=8,
            consultation_fee=700,
            hospital_affiliation="Skin Clinic Pune",
            is_available_for_teleconsult=False,
            hpr_id="dr.rohan@hpr.abdm",
        ),
    )
    await create_doctor_profile(
        async_db_session,
        DoctorProfileCreate(
            user_id=u3.id,
            registration_number="R-CARD-2",
            medical_council="KMC",
            specialty=MedicalSpecialty.CARDIOLOGY,
            qualifications="DM",
            experience_years=5,
            consultation_fee=600,
            hospital_affiliation="Apollo Hospital",
            is_available_for_teleconsult=True,
            hpr_id="dr.sunita@hpr.abdm",
        ),
    )

    # 1. Specialty filter
    cards, total_cards = await list_doctors(async_db_session, specialty=MedicalSpecialty.CARDIOLOGY)
    assert total_cards == 2
    assert len(cards) == 2
    assert all(d.specialty == MedicalSpecialty.CARDIOLOGY for d in cards)

    # 2. Teleconsult only
    tele, total_tele = await list_doctors(async_db_session, teleconsult_only=True)
    assert total_tele == 2
    assert all(d.is_available_for_teleconsult is True for d in tele)

    # 3. Max fee filter
    affordable, total_aff = await list_doctors(async_db_session, max_fee=800)
    assert total_aff == 2
    assert all(d.consultation_fee <= 800 for d in affordable)

    # 4. Search query
    searched, total_s = await list_doctors(async_db_session, query="Fortis")
    assert total_s == 1
    assert searched[0].user.full_name == "Dr. Meera Nambiar"

    # 5. Pagination
    p1, total_all = await list_doctors(async_db_session, skip=0, limit=2)
    assert total_all == 3
    assert len(p1) == 2
    p2, _ = await list_doctors(async_db_session, skip=2, limit=2)
    assert len(p2) == 1


@pytest.mark.asyncio
async def test_update_doctor_profile(async_db_session: AsyncSession):
    """Verify updating doctor credentials, fees, and handling collision checks."""
    u1 = User(id="u-upd-1", email="u1@h.org", full_name="Dr. One", role=UserRole.DOCTOR, is_active=True)
    u2 = User(id="u-upd-2", email="u2@h.org", full_name="Dr. Two", role=UserRole.DOCTOR, is_active=True)
    async_db_session.add_all([u1, u2])
    await async_db_session.commit()

    d1 = await create_doctor_profile(
        async_db_session,
        DoctorProfileCreate(user_id=u1.id, registration_number="REG-A", medical_council="KMC", qualifications="MBBS", hpr_id="dr.one@hpr.abdm"),
    )
    await create_doctor_profile(
        async_db_session,
        DoctorProfileCreate(user_id=u2.id, registration_number="REG-B", medical_council="KMC", qualifications="MD", hpr_id="dr.two@hpr.abdm"),
    )

    # Successful update
    upd = await update_doctor_profile(
        async_db_session,
        d1.id,
        DoctorProfileUpdate(consultation_fee=1500, bio="Updated bio", is_available_for_teleconsult=False),
    )
    assert upd.consultation_fee == 1500
    assert upd.bio == "Updated bio"
    assert upd.is_available_for_teleconsult is False

    # Collision on registration number
    with pytest.raises(AppException) as exc_reg:
        await update_doctor_profile(async_db_session, d1.id, DoctorProfileUpdate(registration_number="REG-B"))
    assert exc_reg.value.status_code == 409
    assert exc_reg.value.error_code == "DUPLICATE_REGISTRATION_NUMBER"

    # Collision on HPR ID
    with pytest.raises(AppException) as exc_hpr:
        await update_doctor_profile(async_db_session, d1.id, DoctorProfileUpdate(hpr_id="dr.two@hpr.abdm"))
    assert exc_hpr.value.status_code == 409
    assert exc_hpr.value.error_code == "DUPLICATE_HPR_ID"

    # Non-existent doctor
    with pytest.raises(EntityNotFoundException):
        await update_doctor_profile(async_db_session, "non-existent-id", DoctorProfileUpdate(consultation_fee=100))


@pytest.mark.asyncio
async def test_delete_doctor_profile(async_db_session: AsyncSession):
    """Verify deleting a doctor profile and 404 for non-existent doctor."""
    user = User(id="u-del", email="del@h.org", full_name="Dr. Delete", role=UserRole.DOCTOR, is_active=True)
    async_db_session.add(user)
    await async_db_session.commit()

    doc = await create_doctor_profile(
        async_db_session,
        DoctorProfileCreate(user_id=user.id, registration_number="REG-DEL", medical_council="KMC", qualifications="MBBS"),
    )

    del_res = await delete_doctor_profile(async_db_session, doc.id)
    assert del_res is True

    # Subsequent fetch returns None
    assert await get_doctor_by_id(async_db_session, doc.id) is None

    # Deleting non-existent doctor raises 404
    with pytest.raises(EntityNotFoundException):
        await delete_doctor_profile(async_db_session, doc.id)
