"""Unit test suite for Role-Based Access Control (RBAC), guards, and patient resource ownership checks."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.dependencies import (
    RoleChecker,
    require_admin,
    require_clinical_staff,
    require_doctor,
    require_lab,
    require_patient,
    require_role,
    verify_patient_access,
    verify_patient_modification_access,
)
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException
from app.db.base import Base
from app.models.enums import BloodGroup, Gender, UserRole
from app.models.patient import PatientProfile
from app.models.user import User


@pytest_asyncio.fixture
async def async_db_session():
    """Provide an isolated in-memory SQLite async database session for RBAC ownership tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ----------------------------------------------------------------------------
# RoleChecker Unit Tests
# ----------------------------------------------------------------------------


def test_role_checker_initialization():
    """Verify RoleChecker initializes with provided roles."""
    checker = RoleChecker([UserRole.DOCTOR, UserRole.LAB])
    assert checker.allowed_roles == [UserRole.DOCTOR, UserRole.LAB]

    factory_checker = require_role(UserRole.PATIENT)
    assert factory_checker.allowed_roles == [UserRole.PATIENT]


@pytest.mark.asyncio
async def test_role_checker_allows_matching_role():
    """Verify RoleChecker permits user possessing the exact target role."""
    checker = RoleChecker([UserRole.DOCTOR])
    user = User(
        id="usr-doc-1",
        email="dr.doc@nirmaya.health",
        full_name="Dr. Doc",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    result = await checker(current_user=user)
    assert result == user


@pytest.mark.asyncio
async def test_role_checker_admin_superuser_override():
    """Verify RoleChecker automatically permits admin users regardless of specified roles."""
    checker = RoleChecker([UserRole.PATIENT])
    admin_user = User(
        id="usr-admin-1",
        email="admin@nirmaya.health",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    result = await checker(current_user=admin_user)
    assert result == admin_user


@pytest.mark.asyncio
async def test_role_checker_raises_403_for_unauthorized_role():
    """Verify RoleChecker rejects unauthorized roles with 403 PermissionDeniedException."""
    checker = RoleChecker([UserRole.DOCTOR, UserRole.LAB])
    patient_user = User(
        id="usr-pat-1",
        email="patient@nirmaya.health",
        full_name="Patient User",
        role=UserRole.PATIENT,
        is_active=True,
    )
    with pytest.raises(PermissionDeniedException) as exc_info:
        await checker(current_user=patient_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.error_code == "FORBIDDEN"
    assert "doctor" in exc_info.value.message
    assert "lab" in exc_info.value.message


# ----------------------------------------------------------------------------
# Preconfigured Role Guards
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preconfigured_role_guards():
    """Test standard clinical guards against all four core user roles."""
    patient = User(id="p1", email="p@h.org", full_name="P", role=UserRole.PATIENT, is_active=True)
    doctor = User(id="d1", email="d@h.org", full_name="D", role=UserRole.DOCTOR, is_active=True)
    lab = User(id="l1", email="l@h.org", full_name="L", role=UserRole.LAB, is_active=True)
    admin = User(id="a1", email="a@h.org", full_name="A", role=UserRole.ADMIN, is_active=True)

    # require_patient: permits PATIENT and ADMIN
    assert await require_patient(patient) == patient
    assert await require_patient(admin) == admin
    with pytest.raises(PermissionDeniedException):
        await require_patient(doctor)
    with pytest.raises(PermissionDeniedException):
        await require_patient(lab)

    # require_doctor: permits DOCTOR and ADMIN
    assert await require_doctor(doctor) == doctor
    assert await require_doctor(admin) == admin
    with pytest.raises(PermissionDeniedException):
        await require_doctor(patient)
    with pytest.raises(PermissionDeniedException):
        await require_doctor(lab)

    # require_lab: permits LAB and ADMIN
    assert await require_lab(lab) == lab
    assert await require_lab(admin) == admin
    with pytest.raises(PermissionDeniedException):
        await require_lab(patient)
    with pytest.raises(PermissionDeniedException):
        await require_lab(doctor)

    # require_admin: permits ADMIN only
    assert await require_admin(admin) == admin
    with pytest.raises(PermissionDeniedException):
        await require_admin(patient)
    with pytest.raises(PermissionDeniedException):
        await require_admin(doctor)
    with pytest.raises(PermissionDeniedException):
        await require_admin(lab)

    # require_clinical_staff: permits DOCTOR, LAB, and ADMIN
    assert await require_clinical_staff(doctor) == doctor
    assert await require_clinical_staff(lab) == lab
    assert await require_clinical_staff(admin) == admin
    with pytest.raises(PermissionDeniedException):
        await require_clinical_staff(patient)


# ----------------------------------------------------------------------------
# Resource Ownership & Access Verification Tests
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_patient_access_ownership_and_roles(async_db_session: AsyncSession):
    """Verify read access enforcement based on patient ownership and clinical roles."""
    user1 = User(id="u1", email="u1@h.org", full_name="User 1", role=UserRole.PATIENT, is_active=True)
    user2 = User(id="u2", email="u2@h.org", full_name="User 2", role=UserRole.PATIENT, is_active=True)
    doc = User(id="u3", email="u3@h.org", full_name="Doc 3", role=UserRole.DOCTOR, is_active=True)
    lab = User(id="u4", email="u4@h.org", full_name="Lab 4", role=UserRole.LAB, is_active=True)
    admin = User(id="u5", email="u5@h.org", full_name="Admin 5", role=UserRole.ADMIN, is_active=True)

    patient_profile = PatientProfile(
        id="pat-profile-001",
        user_id="u1",
        gender=Gender.MALE,
        blood_group=BloodGroup.O_POSITIVE,
    )
    async_db_session.add_all([user1, user2, doc, lab, admin, patient_profile])
    await async_db_session.commit()

    # 1. Owner can access
    p = await verify_patient_access("pat-profile-001", user1, async_db_session)
    assert p.id == "pat-profile-001"

    # 2. Other patient cannot access
    with pytest.raises(PermissionDeniedException) as exc_info:
        await verify_patient_access("pat-profile-001", user2, async_db_session)
    assert exc_info.value.status_code == 403

    # 3. Doctor can access
    p_doc = await verify_patient_access("pat-profile-001", doc, async_db_session)
    assert p_doc.id == "pat-profile-001"

    # 4. Lab can access
    p_lab = await verify_patient_access("pat-profile-001", lab, async_db_session)
    assert p_lab.id == "pat-profile-001"

    # 5. Admin can access
    p_admin = await verify_patient_access("pat-profile-001", admin, async_db_session)
    assert p_admin.id == "pat-profile-001"

    # 6. Non-existent patient raises EntityNotFoundException
    with pytest.raises(EntityNotFoundException) as exc_404:
        await verify_patient_access("non-existent-id", admin, async_db_session)
    assert exc_404.value.status_code == 404


@pytest.mark.asyncio
async def test_verify_patient_modification_access(async_db_session: AsyncSession):
    """Verify write/delete authorization: only profile owner or admin may modify."""
    user1 = User(id="u1", email="u1@h.org", full_name="User 1", role=UserRole.PATIENT, is_active=True)
    user2 = User(id="u2", email="u2@h.org", full_name="User 2", role=UserRole.PATIENT, is_active=True)
    doc = User(id="u3", email="u3@h.org", full_name="Doc 3", role=UserRole.DOCTOR, is_active=True)
    admin = User(id="u5", email="u5@h.org", full_name="Admin 5", role=UserRole.ADMIN, is_active=True)

    patient_profile = PatientProfile(
        id="pat-profile-002",
        user_id="u1",
        gender=Gender.FEMALE,
        blood_group=BloodGroup.A_POSITIVE,
    )
    async_db_session.add_all([user1, user2, doc, admin, patient_profile])
    await async_db_session.commit()

    # 1. Owner can modify
    p = await verify_patient_modification_access("pat-profile-002", user1, async_db_session)
    assert p.id == "pat-profile-002"

    # 2. Other patient cannot modify
    with pytest.raises(PermissionDeniedException) as exc_user2:
        await verify_patient_modification_access("pat-profile-002", user2, async_db_session)
    assert exc_user2.value.status_code == 403

    # 3. Doctor cannot modify demographic profile directly
    with pytest.raises(PermissionDeniedException) as exc_doc:
        await verify_patient_modification_access("pat-profile-002", doc, async_db_session)
    assert exc_doc.value.status_code == 403

    # 4. Admin can modify
    p_admin = await verify_patient_modification_access("pat-profile-002", admin, async_db_session)
    assert p_admin.id == "pat-profile-002"

    # 5. Non-existent profile raises 404
    with pytest.raises(EntityNotFoundException) as exc_404:
        await verify_patient_modification_access("non-existent-id", admin, async_db_session)
    assert exc_404.value.status_code == 404
