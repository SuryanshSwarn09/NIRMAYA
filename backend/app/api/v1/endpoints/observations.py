"""Clinical Observation and Vital Signs API endpoints for NIRMAYA platform.

Provides RESTful management of patient vital signs, biometric observations,
LOINC diagnostic panels, and HL7 FHIR Release 4 Observation resource serialization.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException
from app.db.session import get_db
from app.fhir import FHIRObservation, to_fhir_observation
from app.models.enums import (
    ObservationCategory,
    ObservationStatus,
    UserRole,
)
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.observation import (
    ObservationCreate,
    ObservationFilter,
    ObservationResponse,
    ObservationUpdate,
    VitalsSummaryResponse,
)
from app.services import doctor as doctor_service
from app.services import observation as observation_service
from app.services import patient as patient_service

router = APIRouter()


async def _verify_observation_read_access(
    db: AsyncSession,
    patient_id: str,
    current_user: User,
) -> None:
    """Verify that current user is authorized to read patient clinical records."""
    if current_user.role in (UserRole.ADMIN, UserRole.DOCTOR):
        return

    patient = await patient_service.get_patient_by_id(db, patient_id)
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    if patient.user_id != current_user.id:
        raise PermissionDeniedException(
            message="You are not authorized to view this patient's clinical observations"
        )


async def _verify_observation_write_access(
    db: AsyncSession,
    patient_id: str,
    current_user: User,
) -> Optional[str]:
    """Verify write permission and resolve doctor_id if recorded by clinician."""
    if current_user.role == UserRole.ADMIN:
        return None

    if current_user.role == UserRole.DOCTOR:
        doc = await doctor_service.get_doctor_by_user_id(db, current_user.id)
        return doc.id if doc else None

    # Patient self-measurement / self-reporting (e.g. home blood pressure or wearable telemetry)
    patient = await patient_service.get_patient_by_id(db, patient_id)
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    if patient.user_id == current_user.id:
        return None

    raise PermissionDeniedException(
        message="You are not authorized to record clinical observations for this patient"
    )


# ============================================================================
# Patient Observation Endpoints
# ============================================================================


@router.post(
    "/patients/{patient_id}/observations",
    response_model=APIResponse[ObservationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record a new clinical observation or vital sign",
    description="Records a quantitative vital sign, multi-component panel (e.g. Blood Pressure), or observation.",
)
async def record_patient_observation(
    patient_id: str,
    payload: ObservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ObservationResponse]:
    performer_doctor_id = await _verify_observation_write_access(db, patient_id, current_user)

    observation = await observation_service.record_observation(
        db=db,
        patient_id=patient_id,
        payload=payload,
        performer_doctor_id=performer_doctor_id,
    )

    full_obs = await observation_service.get_observation_by_id(db, observation.id)

    return APIResponse(
        success=True,
        message="Clinical observation recorded successfully",
        data=ObservationResponse.model_validate(full_obs),
    )


@router.get(
    "/patients/{patient_id}/observations",
    response_model=PaginatedResponse[ObservationResponse],
    summary="List patient clinical observations and vitals",
    description="Returns longitudinal observations for a patient with optional category, code, and date filters.",
)
async def list_patient_observations(
    patient_id: str,
    category: Optional[ObservationCategory] = Query(None, description="Filter by category (e.g. vital-signs)"),
    code_value: Optional[str] = Query(None, description="Filter by LOINC code (e.g. 8867-4)"),
    status: Optional[ObservationStatus] = Query(None, description="Filter by observation status"),
    encounter_id: Optional[str] = Query(None, description="Filter by encounter UUID"),
    start_date: Optional[datetime] = Query(None, description="Filter observations on or after UTC datetime"),
    end_date: Optional[datetime] = Query(None, description="Filter observations on or before UTC datetime"),
    page: int = Query(1, ge=1, description="1-indexed page number"),
    limit: int = Query(20, ge=1, le=100, description="Page size limit"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[ObservationResponse]:
    await _verify_observation_read_access(db, patient_id, current_user)

    filters = ObservationFilter(
        category=category,
        code_value=code_value,
        status=status,
        encounter_id=encounter_id,
        start_date=start_date,
        end_date=end_date,
    )

    skip = (page - 1) * limit
    observations, total_count = await observation_service.list_patient_observations(
        db=db,
        patient_id=patient_id,
        filters=filters,
        skip=skip,
        limit=limit,
    )

    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

    return PaginatedResponse(
        success=True,
        data=[ObservationResponse.model_validate(o) for o in observations],
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
    "/patients/{patient_id}/observations/vitals/latest",
    response_model=APIResponse[VitalsSummaryResponse],
    summary="Get latest patient vitals summary",
    description="Returns the single most recent reading for each standard vital sign (BP, HR, SpO2, Temp, BMI, etc.).",
)
async def get_patient_latest_vitals(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[VitalsSummaryResponse]:
    await _verify_observation_read_access(db, patient_id, current_user)

    summary = await observation_service.get_latest_vitals_summary(db, patient_id)

    return APIResponse(
        success=True,
        message="Latest vitals retrieved successfully",
        data=summary,
    )


# ============================================================================
# Individual Observation Endpoints
# ============================================================================


@router.get(
    "/observations/{observation_id}",
    response_model=APIResponse[ObservationResponse],
    summary="Retrieve a clinical observation by ID",
    description="Fetches detailed clinical attributes and metrics for a specific observation record.",
)
async def get_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ObservationResponse]:
    observation = await observation_service.get_observation_by_id(db, observation_id)
    if not observation:
        raise EntityNotFoundException("Clinical observation", observation_id)

    await _verify_observation_read_access(db, observation.patient_id, current_user)

    return APIResponse(
        success=True,
        message="Observation retrieved successfully",
        data=ObservationResponse.model_validate(observation),
    )


@router.patch(
    "/observations/{observation_id}",
    response_model=APIResponse[ObservationResponse],
    summary="Update observation status, interpretation, or notes",
    description="Updates status (e.g. final to amended), clinical interpretation, or diagnostic notes.",
)
async def update_observation_record(
    observation_id: str,
    payload: ObservationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ObservationResponse]:
    observation = await observation_service.get_observation_by_id(db, observation_id)
    if not observation:
        raise EntityNotFoundException("Clinical observation", observation_id)

    await _verify_observation_write_access(db, observation.patient_id, current_user)

    updated = await observation_service.update_observation(
        db=db,
        observation_id=observation_id,
        payload=payload,
    )

    full_updated = await observation_service.get_observation_by_id(db, updated.id)

    return APIResponse(
        success=True,
        message="Observation updated successfully",
        data=ObservationResponse.model_validate(full_updated),
    )


@router.get(
    "/observations/{observation_id}/fhir",
    response_model=FHIRObservation,
    summary="Export observation as HL7 FHIR R4 Observation resource",
    description="Translates internal NIRMAYA observation record into standardized HL7 FHIR R4 JSON.",
)
async def get_observation_fhir(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FHIRObservation:
    observation = await observation_service.get_observation_by_id(db, observation_id)
    if not observation:
        raise EntityNotFoundException("Clinical observation", observation_id)

    await _verify_observation_read_access(db, observation.patient_id, current_user)

    return to_fhir_observation(observation)
