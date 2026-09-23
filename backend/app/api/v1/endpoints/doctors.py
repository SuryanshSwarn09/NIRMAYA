"""Doctor EMR API endpoints for managing healthcare provider credentials and directory."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import (
    get_current_user,
    verify_doctor_modification_access,
)
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException
from app.db.session import get_db
from app.models.enums import MedicalSpecialty, UserRole
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.doctor import (
    DoctorProfileCreate,
    DoctorProfileResponse,
    DoctorProfileUpdate,
)
from app.services import doctor as doctor_service

router = APIRouter()


@router.post(
    "/",
    response_model=APIResponse[DoctorProfileResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Onboard or register a doctor clinical profile",
    description="Initializes a practitioner profile with licensing credentials, medical specialty, consultation fees, and optional ABDM HPR identifier.",
)
async def create_doctor(
    profile_in: DoctorProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DoctorProfileResponse]:
    """Create a new doctor clinical profile linked to a user account."""
    if current_user.role not in (UserRole.DOCTOR, UserRole.ADMIN):
        raise PermissionDeniedException(
            message=f"Role '{current_user.role.value}' is not authorized to register as a healthcare provider"
        )

    target_user_id = current_user.id
    if current_user.role == UserRole.ADMIN and profile_in.user_id:
        target_user_id = profile_in.user_id
    elif profile_in.user_id and profile_in.user_id != current_user.id:
        raise PermissionDeniedException(
            message="Cannot create doctor profile for another user account"
        )

    doctor = await doctor_service.create_doctor_profile(
        db=db,
        profile_in=profile_in,
        user_id=target_user_id,
    )
    return APIResponse(
        message="Doctor profile initialized successfully",
        data=DoctorProfileResponse.model_validate(doctor),
    )


@router.get(
    "/",
    response_model=PaginatedResponse[DoctorProfileResponse],
    summary="List, search, and filter doctor directory with pagination",
    description="Retrieve paginated doctor profiles filtered by clinical specialty, teleconsultation availability, maximum consultation fee, or text query.",
)
async def get_doctors(
    page: int = Query(default=1, ge=1, description="1-indexed page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Page limit ceiling"),
    query: Optional[str] = Query(default=None, description="Search across name, registration, council, hospital, HPR"),
    specialty: Optional[MedicalSpecialty] = Query(default=None, description="Filter by clinical medical specialty"),
    teleconsult_only: Optional[bool] = Query(default=None, description="Filter doctors offering teleconsultations"),
    max_fee: Optional[int] = Query(default=None, ge=0, description="Ceiling filter on consultation fee in INR"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[DoctorProfileResponse]:
    """List and search doctors with clinical filters and pagination."""
    skip = (page - 1) * limit
    items, total_count = await doctor_service.list_doctors(
        db=db,
        skip=skip,
        limit=limit,
        query=query,
        specialty=specialty,
        teleconsult_only=teleconsult_only,
        max_fee=max_fee,
    )

    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

    return PaginatedResponse(
        data=[DoctorProfileResponse.model_validate(d) for d in items],
        pagination=PaginationMeta(
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get(
    "/by-hpr/{hpr_id}",
    response_model=APIResponse[DoctorProfileResponse],
    summary="Resolve doctor clinical profile by ABDM HPR handle",
    description="ABDM interoperability resolution endpoint matching @hpr.abdm handle.",
)
async def get_doctor_by_hpr_identifier(
    hpr_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DoctorProfileResponse]:
    """Resolve doctor profile by ABDM HPR handle."""
    doctor = await doctor_service.get_doctor_by_hpr_id(db, hpr_id)
    if not doctor:
        raise EntityNotFoundException(entity_name="DoctorProfile (HPR)", entity_id=hpr_id)

    return APIResponse(
        message="Doctor profile resolved via ABDM HPR identity successfully",
        data=DoctorProfileResponse.model_validate(doctor),
    )


@router.get(
    "/by-reg/{registration_number}",
    response_model=APIResponse[DoctorProfileResponse],
    summary="Resolve doctor clinical profile by Medical Council registration number",
    description="Licensing resolution endpoint matching state or national medical council license.",
)
async def get_doctor_by_reg_number(
    registration_number: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DoctorProfileResponse]:
    """Resolve doctor profile by Medical Council registration number."""
    doctor = await doctor_service.get_doctor_by_registration_number(db, registration_number)
    if not doctor:
        raise EntityNotFoundException(
            entity_name="DoctorProfile (Registration)",
            entity_id=registration_number,
        )

    return APIResponse(
        message="Doctor profile resolved via registration license successfully",
        data=DoctorProfileResponse.model_validate(doctor),
    )


@router.get(
    "/{doctor_id}",
    response_model=APIResponse[DoctorProfileResponse],
    summary="Retrieve doctor clinical profile by UUID",
    description="Fetches full practitioner credentials, affiliation, and linked user identity by doctor UUID.",
)
async def get_doctor(
    doctor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DoctorProfileResponse]:
    """Fetch doctor profile by ID."""
    doctor = await doctor_service.get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise EntityNotFoundException(entity_name="DoctorProfile", entity_id=doctor_id)

    return APIResponse(
        message="Doctor profile retrieved successfully",
        data=DoctorProfileResponse.model_validate(doctor),
    )


@router.put(
    "/{doctor_id}",
    response_model=APIResponse[DoctorProfileResponse],
    summary="Update doctor practice credentials, fees, and consultation details",
    description="Updates existing doctor attributes, verifying unique registration and HPR constraints.",
)
async def update_doctor(
    doctor_id: str,
    update_in: DoctorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DoctorProfileResponse]:
    """Update doctor profile fields enforcing owner or administrator authorization."""
    await verify_doctor_modification_access(doctor_id=doctor_id, current_user=current_user, db=db)
    updated = await doctor_service.update_doctor_profile(
        db=db,
        doctor_id=doctor_id,
        update_in=update_in,
    )
    return APIResponse(
        message="Doctor profile updated successfully",
        data=DoctorProfileResponse.model_validate(updated),
    )


@router.delete(
    "/{doctor_id}",
    response_model=APIResponse[dict],
    summary="Delete a doctor clinical profile",
    description="Removes a doctor profile by UUID primary key.",
)
async def delete_doctor(
    doctor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Delete doctor profile by ID enforcing owner or administrator authorization."""
    await verify_doctor_modification_access(doctor_id=doctor_id, current_user=current_user, db=db)
    await doctor_service.delete_doctor_profile(db, doctor_id)
    return APIResponse(
        message="Doctor profile deleted successfully",
        data={"doctor_id": doctor_id, "deleted": True},
    )


