"""Patient Vault business logic service layer for NIRMAYA platform."""

from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import AppException, EntityNotFoundException
from app.models.enums import BloodGroup
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.patient import PatientProfileCreate, PatientProfileUpdate


async def get_patient_by_id(db: AsyncSession, patient_id: str) -> Optional[PatientProfile]:
    """Retrieve a single PatientProfile by UUID primary key with linked user loaded."""
    stmt = (
        select(PatientProfile)
        .options(selectinload(PatientProfile.user))
        .where(PatientProfile.id == patient_id)
    )
    return await db.scalar(stmt)


async def get_patient_by_user_id(db: AsyncSession, user_id: str) -> Optional[PatientProfile]:
    """Retrieve a PatientProfile associated with a specific User ID."""
    stmt = (
        select(PatientProfile)
        .options(selectinload(PatientProfile.user))
        .where(PatientProfile.user_id == user_id)
    )
    return await db.scalar(stmt)


async def get_patient_by_abha(db: AsyncSession, identifier: str) -> Optional[PatientProfile]:
    """Resolve a PatientProfile by 14-digit ABHA ID or @abdm address handle."""
    clean_id = identifier.strip()
    stmt = (
        select(PatientProfile)
        .options(selectinload(PatientProfile.user))
        .where(
            or_(
                PatientProfile.abha_number == clean_id,
                PatientProfile.abha_address == clean_id,
            )
        )
    )
    return await db.scalar(stmt)


async def list_patients(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    query: Optional[str] = None,
    city: Optional[str] = None,
    blood_group: Optional[BloodGroup] = None,
) -> Tuple[List[PatientProfile], int]:
    """List and search patient profiles with clinical filters and pagination."""
    base_query = select(PatientProfile).join(PatientProfile.user)
    count_query = select(func.count(PatientProfile.id)).join(PatientProfile.user)

    filters = []

    if city:
        filters.append(PatientProfile.city.ilike(f"%{city.strip()}%"))

    if blood_group:
        filters.append(PatientProfile.blood_group == blood_group)

    if query:
        term = f"%{query.strip()}%"
        filters.append(
            or_(
                User.full_name.ilike(term),
                User.email.ilike(term),
                PatientProfile.abha_number.ilike(term),
                PatientProfile.abha_address.ilike(term),
                PatientProfile.city.ilike(term),
            )
        )

    if filters:
        base_query = base_query.where(*filters)
        count_query = count_query.where(*filters)

    # Get total count matching criteria
    total_count = (await db.scalar(count_query)) or 0

    # Fetch ordered paginated items
    stmt = (
        base_query.options(selectinload(PatientProfile.user))
        .order_by(PatientProfile.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = list((await db.scalars(stmt)).all())

    return items, total_count


async def create_patient_profile(
    db: AsyncSession,
    profile_in: PatientProfileCreate,
    user_id: Optional[str] = None,
) -> PatientProfile:
    """Create and persist a new patient profile with uniqueness guarantees."""
    target_user_id = user_id or profile_in.user_id
    if not target_user_id:
        raise AppException(
            message="A valid user_id is required to create a patient profile",
            error_code="MISSING_USER_ID",
            status_code=400,
        )

    # Verify user identity exists
    user = await db.scalar(select(User).where(User.id == target_user_id))
    if not user:
        raise EntityNotFoundException(entity_name="User", entity_id=target_user_id)

    # Check if user already has an existing patient profile
    existing_user_profile = await get_patient_by_user_id(db, target_user_id)
    if existing_user_profile:
        raise AppException(
            message=f"User '{target_user_id}' already has an active patient profile",
            error_code="PROFILE_ALREADY_EXISTS",
            status_code=409,
        )

    # Verify unique ABHA number
    if profile_in.abha_number:
        stmt = select(PatientProfile).where(PatientProfile.abha_number == profile_in.abha_number)
        if await db.scalar(stmt):
            raise AppException(
                message=f"ABHA number '{profile_in.abha_number}' is already registered",
                error_code="DUPLICATE_ABHA_NUMBER",
                status_code=409,
            )

    # Verify unique ABHA address
    if profile_in.abha_address:
        stmt = select(PatientProfile).where(PatientProfile.abha_address == profile_in.abha_address)
        if await db.scalar(stmt):
            raise AppException(
                message=f"ABHA address '{profile_in.abha_address}' is already registered",
                error_code="DUPLICATE_ABHA_ADDRESS",
                status_code=409,
            )

    # Prepare data and create
    data = profile_in.model_dump(exclude={"user_id"})
    patient = PatientProfile(user_id=target_user_id, **data)
    db.add(patient)
    await db.commit()

    # Re-fetch with loaded user
    return await get_patient_by_id(db, patient.id)  # type: ignore[return-value]


async def update_patient_profile(
    db: AsyncSession,
    patient_id: str,
    update_in: PatientProfileUpdate,
) -> PatientProfile:
    """Update clinical and demographic attributes of an existing patient profile."""
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        raise EntityNotFoundException(entity_name="PatientProfile", entity_id=patient_id)

    update_data = update_in.model_dump(exclude_unset=True)

    # Check ABHA number collision if updating
    if "abha_number" in update_data and update_data["abha_number"] != patient.abha_number:
        stmt = select(PatientProfile).where(
            PatientProfile.abha_number == update_data["abha_number"],
            PatientProfile.id != patient_id,
        )
        if await db.scalar(stmt):
            raise AppException(
                message=f"ABHA number '{update_data['abha_number']}' is already registered to another patient",
                error_code="DUPLICATE_ABHA_NUMBER",
                status_code=409,
            )

    # Check ABHA address collision if updating
    if "abha_address" in update_data and update_data["abha_address"] != patient.abha_address:
        stmt = select(PatientProfile).where(
            PatientProfile.abha_address == update_data["abha_address"],
            PatientProfile.id != patient_id,
        )
        if await db.scalar(stmt):
            raise AppException(
                message=f"ABHA address '{update_data['abha_address']}' is already registered to another patient",
                error_code="DUPLICATE_ABHA_ADDRESS",
                status_code=409,
            )

    for field, value in update_data.items():
        setattr(patient, field, value)

    await db.commit()
    return await get_patient_by_id(db, patient_id)  # type: ignore[return-value]


async def delete_patient_profile(db: AsyncSession, patient_id: str) -> bool:
    """Delete a patient profile by UUID primary key."""
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        raise EntityNotFoundException(entity_name="PatientProfile", entity_id=patient_id)

    await db.delete(patient)
    await db.commit()
    return True
