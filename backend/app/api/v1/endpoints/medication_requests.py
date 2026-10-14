"""Electronic Prescription and MedicationRequest REST API endpoints for NIRMAYA platform.

Provides secure endpoints for clinical prescription authoring, updating draft orders,
cryptographic SHA-256 digital signing, cancellation, and HL7 FHIR Release 4
MedicationRequest export conforming to ABDM NRCeS profiles.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException
from app.db.session import get_db
from app.fhir import to_fhir_medication_request
from app.fhir.schemas import FHIRMedicationRequest
from app.models.enums import MedicationRequestStatus, UserRole
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.medication_request import (
    MedicationRequestCancelRequest,
    MedicationRequestCreate,
    MedicationRequestFilter,
    MedicationRequestResponse,
    MedicationRequestSignRequest,
    MedicationRequestUpdate,
)
from app.services import (
    cancel_prescription,
    create_prescription,
    get_prescription_by_id,
    list_prescriptions,
    sign_prescription,
    update_prescription,
)
from app.services import doctor as doctor_service
from app.services import patient as patient_service

router = APIRouter()


async def _verify_prescription_read_access(
    db: AsyncSession,
    patient_id: str,
    current_user: User,
) -> None:
    """Verify that current user is authorized to read patient prescriptions."""
    if current_user.role in (UserRole.ADMIN, UserRole.DOCTOR):
        return

    patient = await patient_service.get_patient_by_id(db, patient_id)
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    if patient.user_id != current_user.id:
        raise PermissionDeniedException(
            message="You are not authorized to view this patient's prescriptions."
        )


async def _verify_doctor_write_access(
    db: AsyncSession,
    current_user: User,
) -> Optional[str]:
    """Verify that current user is a practitioner doctor or admin, and resolve doctor_id."""
    if current_user.role == UserRole.ADMIN:
        return None

    if current_user.role != UserRole.DOCTOR:
        raise PermissionDeniedException(
            message="Only verified healthcare providers (doctors) or administrators can author prescriptions."
        )

    doc = await doctor_service.get_doctor_by_user_id(db, current_user.id)
    if not doc:
        raise PermissionDeniedException(message="Doctor clinical credentials profile not found.")
    return doc.id


@router.post(
    "/patients/{patient_id}/prescriptions",
    response_model=APIResponse[MedicationRequestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Author a new electronic prescription",
    description="Allows a practitioner doctor to draft a structured medication prescription for a patient.",
)
async def create_prescription_endpoint(
    patient_id: str,
    payload: MedicationRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor_id = await _verify_doctor_write_access(db, current_user)
    prescription = await create_prescription(
        db=db,
        patient_id=patient_id,
        payload=payload,
        author_doctor_id=doctor_id,
    )
    return APIResponse(
        success=True,
        message="Electronic prescription drafted successfully",
        data=MedicationRequestResponse.model_validate(prescription),
    )


@router.get(
    "/patients/{patient_id}/prescriptions",
    response_model=PaginatedResponse[MedicationRequestResponse],
    summary="List patient electronic prescriptions",
    description="Retrieves chronological prescriptions for a patient with status and signature filters.",
)
async def list_patient_prescriptions_endpoint(
    patient_id: str,
    status_filter: Optional[MedicationRequestStatus] = Query(None, alias="status", description="Filter by prescription status"),
    is_signed: Optional[bool] = Query(None, description="Filter by signed status"),
    doctor_id: Optional[str] = Query(None, description="Filter by prescriber doctor UUID"),
    encounter_id: Optional[str] = Query(None, description="Filter by appointment/encounter UUID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_prescription_read_access(db, patient_id, current_user)

    filters = MedicationRequestFilter(
        status=status_filter,
        is_signed=is_signed,
        doctor_id=doctor_id,
        encounter_id=encounter_id,
    )

    items, total = await list_prescriptions(
        db=db,
        patient_id=patient_id,
        filters=filters,
        page=page,
        limit=limit,
    )

    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return PaginatedResponse(
        success=True,
        message="Patient prescriptions retrieved successfully",
        data=[MedicationRequestResponse.model_validate(p) for p in items],
        pagination=PaginationMeta(
            total_count=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get(
    "/prescriptions/{prescription_id}",
    response_model=APIResponse[MedicationRequestResponse],
    summary="Retrieve an electronic prescription by ID",
    description="Fetches full details of a prescription including dosage, dispense request, and catalog metadata.",
)
async def get_prescription_endpoint(
    prescription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prescription = await get_prescription_by_id(db, prescription_id)
    await _verify_prescription_read_access(db, prescription.patient_id, current_user)

    return APIResponse(
        success=True,
        message="Prescription retrieved successfully",
        data=MedicationRequestResponse.model_validate(prescription),
    )


@router.patch(
    "/prescriptions/{prescription_id}",
    response_model=APIResponse[MedicationRequestResponse],
    summary="Update a draft prescription",
    description="Updates dosage or dispense fields for an unsigned prescription. Signed prescriptions are immutable.",
)
async def update_prescription_endpoint(
    prescription_id: str,
    payload: MedicationRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_doctor_write_access(db, current_user)
    updated = await update_prescription(db, prescription_id, payload)

    return APIResponse(
        success=True,
        message="Prescription updated successfully",
        data=MedicationRequestResponse.model_validate(updated),
    )


@router.post(
    "/prescriptions/{prescription_id}/sign",
    response_model=APIResponse[MedicationRequestResponse],
    summary="Digitally sign and authorize an electronic prescription",
    description="Applies cryptographic SHA-256 seal, transitions status to active, and locks record against modification.",
)
async def sign_prescription_endpoint(
    prescription_id: str,
    payload: Optional[MedicationRequestSignRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor_id = await _verify_doctor_write_access(db, current_user)
    notes = payload.signature_notes if payload else None

    signed = await sign_prescription(
        db=db,
        prescription_id=prescription_id,
        signing_doctor_id=doctor_id,
        signature_notes=notes,
    )

    return APIResponse(
        success=True,
        message="Prescription digitally signed and authorized successfully",
        data=MedicationRequestResponse.model_validate(signed),
    )


@router.post(
    "/prescriptions/{prescription_id}/cancel",
    response_model=APIResponse[MedicationRequestResponse],
    summary="Discontinue / cancel an active prescription",
    description="Marks the prescription as cancelled and records the clinical rationale.",
)
async def cancel_prescription_endpoint(
    prescription_id: str,
    payload: MedicationRequestCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_doctor_write_access(db, current_user)
    cancelled = await cancel_prescription(
        db=db,
        prescription_id=prescription_id,
        cancellation_reason=payload.cancellation_reason,
    )

    return APIResponse(
        success=True,
        message="Prescription cancelled successfully",
        data=MedicationRequestResponse.model_validate(cancelled),
    )


@router.get(
    "/prescriptions/{prescription_id}/fhir",
    response_model=FHIRMedicationRequest,
    summary="Export prescription as HL7 FHIR R4 MedicationRequest",
    description="Serializes the electronic prescription to canonical FHIR R4 JSON conforming to ABDM NRCeS profiles.",
)
async def export_prescription_fhir_endpoint(
    prescription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prescription = await get_prescription_by_id(db, prescription_id)
    await _verify_prescription_read_access(db, prescription.patient_id, current_user)

    return to_fhir_medication_request(prescription)
