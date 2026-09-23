"""Doctor EMR business logic service layer for NIRMAYA platform."""

from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import AppException, EntityNotFoundException
from app.models.doctor import DoctorProfile
from app.models.enums import MedicalSpecialty
from app.models.user import User
from app.schemas.doctor import DoctorProfileCreate


async def get_doctor_by_id(db: AsyncSession, doctor_id: str) -> Optional[DoctorProfile]:
    """Retrieve a single DoctorProfile by UUID primary key with linked user loaded."""
    stmt = (
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.id == doctor_id)
    )
    return await db.scalar(stmt)


async def get_doctor_by_user_id(db: AsyncSession, user_id: str) -> Optional[DoctorProfile]:
    """Retrieve a DoctorProfile associated with a specific User ID."""
    stmt = (
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.user_id == user_id)
    )
    return await db.scalar(stmt)


async def get_doctor_by_registration_number(
    db: AsyncSession,
    registration_number: str,
) -> Optional[DoctorProfile]:
    """Resolve a DoctorProfile by Medical Council registration number."""
    clean_reg = registration_number.strip()
    stmt = (
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.registration_number == clean_reg)
    )
    return await db.scalar(stmt)


async def get_doctor_by_hpr_id(db: AsyncSession, hpr_id: str) -> Optional[DoctorProfile]:
    """Resolve a DoctorProfile by official ABDM Healthcare Professional Registry handle."""
    clean_hpr = hpr_id.strip()
    stmt = (
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.hpr_id == clean_hpr)
    )
    return await db.scalar(stmt)


async def list_doctors(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    query: Optional[str] = None,
    specialty: Optional[MedicalSpecialty] = None,
    teleconsult_only: Optional[bool] = None,
    max_fee: Optional[int] = None,
) -> Tuple[List[DoctorProfile], int]:
    """List and search doctor directory with clinical filters and pagination."""
    base_query = select(DoctorProfile).join(DoctorProfile.user)
    count_query = select(func.count(DoctorProfile.id)).join(DoctorProfile.user)

    filters = []

    if specialty:
        filters.append(DoctorProfile.specialty == specialty)

    if teleconsult_only is True:
        filters.append(DoctorProfile.is_available_for_teleconsult.is_(True))

    if max_fee is not None:
        filters.append(DoctorProfile.consultation_fee <= max_fee)

    if query:
        search_pattern = f"%{query.strip()}%"
        filters.append(
            or_(
                User.full_name.ilike(search_pattern),
                DoctorProfile.registration_number.ilike(search_pattern),
                DoctorProfile.medical_council.ilike(search_pattern),
                DoctorProfile.hospital_affiliation.ilike(search_pattern),
                DoctorProfile.hpr_id.ilike(search_pattern),
            )
        )

    if filters:
        base_query = base_query.where(*filters)
        count_query = count_query.where(*filters)

    # Execute count
    total_count = await db.scalar(count_query) or 0

    # Execute paginated fetch with eager-loaded user
    stmt = (
        base_query
        .options(selectinload(DoctorProfile.user))
        .order_by(DoctorProfile.experience_years.desc(), DoctorProfile.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return items, total_count


async def create_doctor_profile(
    db: AsyncSession,
    profile_in: DoctorProfileCreate,
    user_id: Optional[str] = None,
) -> DoctorProfile:
    """Create and persist a new doctor profile with registration and HPR uniqueness checks."""
    target_user_id = user_id or profile_in.user_id
    if not target_user_id:
        raise AppException(
            message="A valid user_id is required to create a doctor profile",
            error_code="MISSING_USER_ID",
            status_code=400,
        )

    # Verify user identity exists
    user = await db.scalar(select(User).where(User.id == target_user_id))
    if not user:
        raise EntityNotFoundException(entity_name="User", entity_id=target_user_id)

    # Check if user already has an existing doctor profile
    existing_user_profile = await get_doctor_by_user_id(db, target_user_id)
    if existing_user_profile:
        raise AppException(
            message=f"User '{target_user_id}' already has an active doctor profile",
            error_code="PROFILE_ALREADY_EXISTS",
            status_code=409,
        )

    # Verify unique registration number
    stmt_reg = select(DoctorProfile).where(
        DoctorProfile.registration_number == profile_in.registration_number.strip()
    )
    if await db.scalar(stmt_reg):
        raise AppException(
            message=f"Registration number '{profile_in.registration_number}' is already registered",
            error_code="DUPLICATE_REGISTRATION_NUMBER",
            status_code=409,
        )

    # Verify unique HPR ID if provided
    if profile_in.hpr_id:
        clean_hpr = profile_in.hpr_id.strip()
        stmt_hpr = select(DoctorProfile).where(DoctorProfile.hpr_id == clean_hpr)
        if await db.scalar(stmt_hpr):
            raise AppException(
                message=f"HPR ID '{profile_in.hpr_id}' is already registered",
                error_code="DUPLICATE_HPR_ID",
                status_code=409,
            )

    # Prepare data and persist
    data = profile_in.model_dump(exclude={"user_id"})
    doctor = DoctorProfile(user_id=target_user_id, **data)
    db.add(doctor)
    await db.commit()

    # Re-fetch with loaded user
    return await get_doctor_by_id(db, doctor.id)  # type: ignore[return-value]


