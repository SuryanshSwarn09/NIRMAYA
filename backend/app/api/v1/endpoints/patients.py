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
