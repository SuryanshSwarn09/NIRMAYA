"""Structured SOAP Clinical Notes API endpoints for NIRMAYA platform.

Provides RESTful management of patient encounter documentation, clinical progress notes,
tamper-evident digital signatures, and HL7 FHIR Release 4 Composition resource serialization.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException
from app.db.session import get_db
from app.fhir import FHIRComposition, to_fhir_composition
from app.models.enums import ClinicalNoteStatus, ClinicalNoteType, UserRole
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.soap_note import (
    SoapNoteCreate,
    SoapNoteFilter,
    SoapNoteResponse,
    SoapNoteSignRequest,
    SoapNoteUpdate,
)
from app.services import (
    create_soap_note,
    delete_soap_note,
    get_soap_note_by_id,
    list_patient_soap_notes,
    sign_soap_note,
    update_soap_note,
)
from app.services import doctor as doctor_service
from app.services import patient as patient_service

router = APIRouter()


async def _verify_note_read_access(
    db: AsyncSession,
    patient_id: str,
    current_user: User,
) -> None:
    """Verify that current user is authorized to read patient clinical notes."""
    if current_user.role in (UserRole.ADMIN, UserRole.DOCTOR):
        return

    patient = await patient_service.get_patient_by_id(db, patient_id)
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    if patient.user_id != current_user.id:
        raise PermissionDeniedException(
            message="You are not authorized to view this patient's clinical notes"
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
            message="Only verified healthcare providers (doctors) or administrators can author clinical notes."
        )

    doc = await doctor_service.get_doctor_by_user_id(db, current_user.id)
    if not doc:
        raise PermissionDeniedException(message="Doctor clinical credentials profile not found.")
    return doc.id


@router.post(
    "/patients/{patient_id}/soap-notes",
    response_model=APIResponse[SoapNoteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record a new structured SOAP clinical note",
    description="Allows a practitioner doctor to author a SOAP clinical note for a patient encounter.",
)
async def create_patient_soap_note_endpoint(
    patient_id: str,
    payload: SoapNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor_id = await _verify_doctor_write_access(db, current_user)
    note = await create_soap_note(
        db=db,
        patient_id=patient_id,
        payload=payload,
        author_doctor_id=doctor_id,
    )
    return APIResponse(
        success=True,
        message="Structured SOAP clinical note recorded successfully",
        data=SoapNoteResponse.model_validate(note),
    )


@router.get(
    "/patients/{patient_id}/soap-notes",
    response_model=PaginatedResponse[SoapNoteResponse],
    summary="List patient clinical encounter notes",
    description="Retrieves chronological SOAP notes for a patient with status and type filters.",
)
async def list_patient_soap_notes_endpoint(
    patient_id: str,
    note_type: Optional[ClinicalNoteType] = Query(None, description="Filter by note type"),
    note_status: Optional[ClinicalNoteStatus] = Query(None, alias="status", description="Filter by clinical status"),
    encounter_id: Optional[str] = Query(None, description="Filter by appointment/encounter UUID"),
    is_signed: Optional[bool] = Query(None, description="Filter by digital signature status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_note_read_access(db, patient_id, current_user)
    filters = SoapNoteFilter(
        note_type=note_type,
        status=note_status,
        encounter_id=encounter_id,
        is_signed=is_signed,
    )
    offset = (page - 1) * limit
    notes, total = await list_patient_soap_notes(
        db=db,
        patient_id=patient_id,
        filters=filters,
        limit=limit,
        offset=offset,
    )
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedResponse(
        success=True,
        data=[SoapNoteResponse.model_validate(n) for n in notes],
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
    "/soap-notes/{note_id}",
    response_model=APIResponse[SoapNoteResponse],
    summary="Retrieve a single SOAP clinical note",
)
async def get_soap_note_endpoint(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = await get_soap_note_by_id(db, note_id)
    await _verify_note_read_access(db, note.patient_id, current_user)
    return APIResponse(
        success=True,
        message="Clinical note retrieved successfully",
        data=SoapNoteResponse.model_validate(note),
    )


@router.patch(
    "/soap-notes/{note_id}",
    response_model=APIResponse[SoapNoteResponse],
    summary="Update a preliminary SOAP note before signature",
)
async def update_soap_note_endpoint(
    note_id: str,
    payload: SoapNoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_doctor_write_access(db, current_user)
    try:
        updated_note = await update_soap_note(db, note_id, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return APIResponse(
        success=True,
        message="Clinical note updated successfully",
        data=SoapNoteResponse.model_validate(updated_note),
    )


@router.post(
    "/soap-notes/{note_id}/sign",
    response_model=APIResponse[SoapNoteResponse],
    summary="Electronically sign and finalize a SOAP clinical note",
    description="Applies cryptographic SHA-256 digest to lock the document and transitions status to final.",
)
async def sign_soap_note_endpoint(
    note_id: str,
    payload: Optional[SoapNoteSignRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor_id = await _verify_doctor_write_access(db, current_user)
    try:
        signed = await sign_soap_note(
            db=db,
            note_id=note_id,
            payload=payload,
            signing_doctor_id=doctor_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return APIResponse(
        success=True,
        message="Clinical note digitally signed and finalized successfully",
        data=SoapNoteResponse.model_validate(signed),
    )


@router.get(
    "/soap-notes/{note_id}/fhir",
    response_model=FHIRComposition,
    summary="Export clinical note as HL7 FHIR Release 4 Composition",
    description="Serializes the SOAP note into canonical HL7 FHIR R4 Composition resource with LOINC narrative sections.",
)
async def export_soap_note_fhir_endpoint(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = await get_soap_note_by_id(db, note_id)
    await _verify_note_read_access(db, note.patient_id, current_user)
    return to_fhir_composition(note)


@router.delete(
    "/soap-notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete draft clinical note or mark entered-in-error",
)
async def delete_soap_note_endpoint(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_doctor_write_access(db, current_user)
    await delete_soap_note(db, note_id)
    return None
