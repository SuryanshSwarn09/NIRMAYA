"""Clinical Condition and Problem List API endpoints for NIRMAYA platform.

Provides RESTful management of patient conditions, chronic diseases, problem lists,
and HL7 FHIR Release 4 Condition resource serialization.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException
from app.db.session import get_db
from app.fhir import FHIRCondition, to_fhir_condition
from app.models.condition import ClinicalCondition
from app.models.doctor import DoctorProfile
from app.models.enums import (
    ClinicalStatus,
    ConditionCategory,
    ConditionSeverity,
    UserRole,
    VerificationStatus,
)
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.condition import (
    ConditionCreate,
    ConditionFilter,
    ConditionResponse,
    ConditionUpdate,
)
from app.services import condition as condition_service
from app.services import doctor as doctor_service
from app.services import patient as patient_service

router = APIRouter()


async def _verify_condition_read_access(
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
            message="You are not authorized to view this patient's clinical problem list"
        )


async def _verify_condition_write_access(
    db: AsyncSession,
    patient_id: str,
    current_user: User,
) -> Optional[str]:
    """Verify that current user can record conditions and return doctor_id if doctor."""
    if current_user.role == UserRole.ADMIN:
        return None

    if current_user.role == UserRole.DOCTOR:
        doc = await doctor_service.get_doctor_by_user_id(db, current_user.id)
        return doc.id if doc else None

    # Patient self-report
    patient = await patient_service.get_patient_by_id(db, patient_id)
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    if patient.user_id == current_user.id:
        return None

    raise PermissionDeniedException(
        message="You are not authorized to record clinical conditions for this patient"
    )


# ============================================================================
# Patient Problem List Endpoints
# ============================================================================


@router.post(
    "/patients/{patient_id}/conditions",
    response_model=APIResponse[ConditionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record a new clinical condition",
    description="Adds a diagnosed condition, chronic illness, or problem to a patient's problem list.",
)
async def record_patient_condition(
    patient_id: str,
    payload: ConditionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ConditionResponse]:
    recorder_doctor_id = await _verify_condition_write_access(db, patient_id, current_user)

    condition = await condition_service.record_condition(
        db=db,
        patient_id=patient_id,
        payload=payload,
        recorder_doctor_id=recorder_doctor_id,
    )

    # Fetch with loaded relationships for response
    full_condition = await condition_service.get_condition_by_id(db, condition.id)

    return APIResponse(
        success=True,
        message="Clinical condition recorded successfully",
        data=ConditionResponse.model_validate(full_condition),
    )


@router.get(
    "/patients/{patient_id}/conditions",
    response_model=PaginatedResponse[ConditionResponse],
    summary="List patient condition problem list",
    description="Returns the longitudinal problem list for a patient with optional clinical status and category filters.",
)
async def list_patient_problem_list(
    patient_id: str,
    clinical_status: Optional[ClinicalStatus] = Query(None, description="Filter by clinical status"),
    verification_status: Optional[VerificationStatus] = Query(None, description="Filter by verification status"),
    category: Optional[ConditionCategory] = Query(None, description="Filter by condition category"),
    severity: Optional[ConditionSeverity] = Query(None, description="Filter by severity assessment"),
    encounter_id: Optional[str] = Query(None, description="Filter by encounter UUID"),
    page: int = Query(1, ge=1, description="1-indexed page number"),
    limit: int = Query(20, ge=1, le=100, description="Page size limit"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[ConditionResponse]:
    await _verify_condition_read_access(db, patient_id, current_user)

    filters = ConditionFilter(
        clinical_status=clinical_status,
        verification_status=verification_status,
        category=category,
        severity=severity,
        encounter_id=encounter_id,
    )

    skip = (page - 1) * limit
    conditions, total_count = await condition_service.list_patient_conditions(
        db=db,
        patient_id=patient_id,
        filters=filters,
        skip=skip,
        limit=limit,
    )

    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

    return PaginatedResponse(
        success=True,
        data=[ConditionResponse.model_validate(c) for c in conditions],
        pagination=PaginationMeta(
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


# ============================================================================
# Individual Condition Endpoints
# ============================================================================


@router.get(
    "/conditions/{condition_id}",
    response_model=APIResponse[ConditionResponse],
    summary="Retrieve a clinical condition by ID",
    description="Fetches detailed clinical attributes and status for a specific condition record.",
)
async def get_condition(
    condition_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ConditionResponse]:
    condition = await condition_service.get_condition_by_id(db, condition_id)
    if not condition:
        raise EntityNotFoundException("Condition", condition_id)

    await _verify_condition_read_access(db, condition.patient_id, current_user)

    return APIResponse(
        success=True,
        message="Condition retrieved successfully",
        data=ConditionResponse.model_validate(condition),
    )


@router.patch(
    "/conditions/{condition_id}",
    response_model=APIResponse[ConditionResponse],
    summary="Update condition status or resolution",
    description="Updates clinical status (e.g. resolving a condition), severity, or notes on a problem list item.",
)
async def update_condition_status(
    condition_id: str,
    payload: ConditionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ConditionResponse]:
    condition = await condition_service.get_condition_by_id(db, condition_id)
    if not condition:
        raise EntityNotFoundException("Condition", condition_id)

    # Verify authorization
    await _verify_condition_write_access(db, condition.patient_id, current_user)

    updated = await condition_service.update_condition(
        db=db,
        condition_id=condition_id,
        payload=payload,
    )

    full_updated = await condition_service.get_condition_by_id(db, updated.id)

    return APIResponse(
        success=True,
        message="Condition updated successfully",
        data=ConditionResponse.model_validate(full_updated),
    )


@router.get(
    "/conditions/{condition_id}/fhir",
    response_model=FHIRCondition,
    summary="Export condition as HL7 FHIR R4 Condition resource",
    description="Translates internal NIRMAYA condition record into standardized HL7 FHIR R4 JSON.",
)
async def get_condition_fhir(
    condition_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FHIRCondition:
    condition = await condition_service.get_condition_by_id(db, condition_id)
    if not condition:
        raise EntityNotFoundException("Condition", condition_id)

    await _verify_condition_read_access(db, condition.patient_id, current_user)

    return to_fhir_condition(condition)


@router.delete(
    "/conditions/{condition_id}",
    response_model=APIResponse[dict],
    summary="Delete a condition from problem list",
    description="Permanently removes a condition entry (reserved for Doctors and Admins).",
)
async def delete_condition_entry(
    condition_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[dict]:
    condition = await condition_service.get_condition_by_id(db, condition_id)
    if not condition:
        raise EntityNotFoundException("Condition", condition_id)

    if current_user.role not in (UserRole.ADMIN, UserRole.DOCTOR):
        raise PermissionDeniedException(
            message="Only doctors and administrators may delete condition records"
        )

    await condition_service.delete_condition(db, condition_id)

    return APIResponse(
        success=True,
        message="Condition deleted successfully",
        data={"id": condition_id},
    )
