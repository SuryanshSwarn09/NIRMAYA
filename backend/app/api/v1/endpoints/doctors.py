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
