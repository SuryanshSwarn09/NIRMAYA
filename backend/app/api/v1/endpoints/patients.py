"""Patient Vault API endpoints for managing longitudinal clinical demographics and ABHA identities."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import (
    get_current_user,
    require_clinical_staff,
    verify_patient_access,
    verify_patient_modification_access,
)
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException
from app.db.session import get_db
from app.models.enums import BloodGroup, UserRole
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.patient import (
    PatientProfileCreate,
    PatientProfileResponse,
    PatientProfileUpdate,
)
from app.services import patient as patient_service

router = APIRouter()


@router.post(
    "/",
    response_model=APIResponse[PatientProfileResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Onboard or create a patient clinical profile",
    description="Initializes a patient profile with demographics, contact, and optional ABDM ABHA identifiers.",
)
async def create_patient(
    profile_in: PatientProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientProfileResponse]:
    """Create a new patient clinical profile linked to a user account."""
    target_user_id = current_user.id
    if current_user.role == UserRole.ADMIN and profile_in.user_id:
        target_user_id = profile_in.user_id
    elif profile_in.user_id and profile_in.user_id != current_user.id:
        raise PermissionDeniedException("Cannot create patient profile for another user account")

    patient = await patient_service.create_patient_profile(
        db=db,
        profile_in=profile_in,
        user_id=target_user_id,
    )
    return APIResponse(
        message="Patient profile initialized successfully",
        data=PatientProfileResponse.model_validate(patient),
    )


@router.get(
    "/",
    response_model=PaginatedResponse[PatientProfileResponse],
    summary="List, search, and filter patient directory with pagination",
    description="Retrieve paginated patient profiles filtered by search query, city, or blood group.",
)
async def get_patients(
    page: int = Query(default=1, ge=1, description="1-indexed page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Page limit ceiling"),
    query: Optional[str] = Query(default=None, description="Search across name, email, ABHA, city"),
    city: Optional[str] = Query(default=None, description="Filter by residential city"),
    blood_group: Optional[BloodGroup] = Query(default=None, description="Filter by blood group"),
    current_user: User = Depends(require_clinical_staff),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PatientProfileResponse]:
    """List and search patients with pagination and clinical filters."""
    skip = (page - 1) * limit
    items, total_count = await patient_service.list_patients(
        db=db,
        skip=skip,
        limit=limit,
        query=query,
        city=city,
        blood_group=blood_group,
    )

    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

    return PaginatedResponse(
        data=[PatientProfileResponse.model_validate(p) for p in items],
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
    "/by-abha/{identifier}",
    response_model=APIResponse[PatientProfileResponse],
    summary="Resolve patient clinical profile by ABHA Number or ABHA Address",
    description="ABDM interoperability resolution endpoint matching either 14-digit ABHA ID or @abdm handle.",
)
async def get_patient_by_abha_identifier(
    identifier: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientProfileResponse]:
    """Resolve patient profile by ABHA number or @abdm address."""
    patient = await patient_service.get_patient_by_abha(db, identifier)
    if not patient:
        raise EntityNotFoundException(entity_name="PatientProfile (ABHA)", entity_id=identifier)

    if current_user.role not in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB) and patient.user_id != current_user.id:
        raise PermissionDeniedException(
            message="You do not possess authorization to access this patient's clinical health records",
        )

    return APIResponse(
        message="Patient profile resolved via ABHA identity successfully",
        data=PatientProfileResponse.model_validate(patient),
    )


@router.get(
    "/{patient_id}",
    response_model=APIResponse[PatientProfileResponse],
    summary="Retrieve patient clinical profile by UUID",
    description="Fetches full demographic records and linked user identity by patient UUID.",
)
async def get_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientProfileResponse]:
    """Fetch patient profile by ID enforcing patient ownership or clinical staff privileges."""
    patient = await verify_patient_access(patient_id=patient_id, current_user=current_user, db=db)

    return APIResponse(
        message="Patient profile retrieved successfully",
        data=PatientProfileResponse.model_validate(patient),
    )


@router.put(
    "/{patient_id}",
    response_model=APIResponse[PatientProfileResponse],
    summary="Update patient clinical demographics or contact information",
    description="Updates existing patient attributes, verifying ABHA unique constraints.",
)
async def update_patient(
    patient_id: str,
    update_in: PatientProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientProfileResponse]:
    """Update patient profile fields enforcing owner or administrator authorization."""
    await verify_patient_modification_access(patient_id=patient_id, current_user=current_user, db=db)
    updated = await patient_service.update_patient_profile(
        db=db,
        patient_id=patient_id,
        update_in=update_in,
    )
    return APIResponse(
        message="Patient profile updated successfully",
        data=PatientProfileResponse.model_validate(updated),
    )


@router.delete(
    "/{patient_id}",
    response_model=APIResponse[dict],
    summary="Delete a patient clinical profile",
    description="Removes a patient profile by UUID.",
)
async def delete_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Delete patient profile by ID enforcing owner or administrator authorization."""
    await verify_patient_modification_access(patient_id=patient_id, current_user=current_user, db=db)
    await patient_service.delete_patient_profile(db, patient_id)
    return APIResponse(
        message="Patient profile deleted successfully",
        data={"patient_id": patient_id, "deleted": True},
    )
