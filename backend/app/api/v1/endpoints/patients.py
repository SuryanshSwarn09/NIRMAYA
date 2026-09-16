"""Patient Vault API endpoints for managing longitudinal clinical demographics and ABHA identities."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import EntityNotFoundException
from app.db.session import get_db
from app.models.enums import BloodGroup
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
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientProfileResponse]:
    """Create a new patient clinical profile linked to a user account."""
    patient = await patient_service.create_patient_profile(
        db=db,
        profile_in=profile_in,
        user_id=profile_in.user_id,
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
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientProfileResponse]:
    """Resolve patient profile by ABHA number or @abdm address."""
    patient = await patient_service.get_patient_by_abha(db, identifier)
    if not patient:
        raise EntityNotFoundException(entity_name="PatientProfile (ABHA)", entity_id=identifier)

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
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientProfileResponse]:
    """Fetch patient profile by ID."""
    patient = await patient_service.get_patient_by_id(db, patient_id)
    if not patient:
        raise EntityNotFoundException(entity_name="PatientProfile", entity_id=patient_id)

    return APIResponse(
        message="Patient profile retrieved successfully",
        data=PatientProfileResponse.model_validate(patient),
    )
