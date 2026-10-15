"""Pharmacy Medication Dispense REST API endpoints for NIRMAYA platform.

Provides secure endpoints for fulfilling active e-prescriptions, generic substitutions,
batch lot tracking, dispensation queries, and HL7 FHIR Release 4 export.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException
from app.db.session import get_db
from app.fhir import to_fhir_medication_dispense
from app.fhir.schemas import FHIRMedicationDispense
from app.models.enums import MedicationDispenseStatus, UserRole
from app.models.medication_dispense import MedicationDispense
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.medication_dispense import (
    MedicationDispenseCreate,
    MedicationDispenseFilter,
    MedicationDispenseResponse,
    MedicationDispenseUpdate,
)
from app.services import (
    create_dispense,
    get_dispense_by_id,
    get_prescription_by_id,
    list_dispensations,
    update_dispense,
)
from app.services import patient as patient_service

router = APIRouter()


def _to_response_dto(dispense: MedicationDispense) -> MedicationDispenseResponse:
    """Format relational MedicationDispense into serializable response DTO with enriched names."""
    med_name = dispense.medication.name if getattr(dispense, "medication", None) else None
    patient_name = (
        dispense.patient.user.full_name
        if (getattr(dispense, "patient", None) and getattr(dispense.patient, "user", None))
        else None
    )
    dispenser_name = (
        dispense.dispenser.full_name
        if getattr(dispense, "dispenser", None)
        else None
    )

    return MedicationDispenseResponse(
        id=dispense.id,
        dispense_number=dispense.dispense_number,
        prescription_id=dispense.prescription_id,
        patient_id=dispense.patient_id,
        medication_id=dispense.medication_id,
        dispenser_id=dispense.dispenser_id,
        status=dispense.status,
        status_reason=dispense.status_reason,
        quantity_dispensed=dispense.quantity_dispensed,
        dispense_unit=dispense.dispense_unit,
        days_supply=dispense.days_supply,
        lot_number=dispense.lot_number,
        expiration_date=dispense.expiration_date,
        when_prepared=dispense.when_prepared,
        when_handed_over=dispense.when_handed_over,
        was_substituted=dispense.was_substituted,
        substitution_type=dispense.substitution_type,
        substitution_reason=dispense.substitution_reason,
        dosage_instruction=dispense.dosage_instruction,
        pharmacist_notes=dispense.pharmacist_notes,
        created_at=dispense.created_at,
        updated_at=dispense.updated_at,
        medication_name=med_name,
        patient_name=patient_name,
        dispenser_name=dispenser_name,
    )


async def _verify_dispense_read_access(
    db: AsyncSession,
    dispense: MedicationDispense,
    current_user: User,
) -> None:
    """Ensure patient only views their own dispensations; clinicians/admins have broader access."""
    if current_user.role in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB):
        return

    patient = await patient_service.get_patient_by_id(db, dispense.patient_id)
    if not patient or patient.user_id != current_user.id:
        raise PermissionDeniedException(
            message="You are not authorized to view this pharmaceutical dispensation."
        )


@router.post(
    "/prescriptions/{prescription_id}/dispense",
    response_model=APIResponse[MedicationDispenseResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Dispense and fulfill an active prescription",
)
async def dispense_prescription(
    prescription_id: str,
    payload: MedicationDispenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fulfill an active signed e-prescription with batch lot/expiry tracking and refill quota check."""
    # Ensure payload matches URL prescription_id
    payload.prescription_id = prescription_id

    # Verify authorization (Clinicians, Pharmacists, or Admins)
    if current_user.role not in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB):
        raise PermissionDeniedException(
            message="Only authorized clinical practitioners or pharmacy staff can dispense medications."
        )

    dispense = await create_dispense(db, payload, dispenser_user=current_user)
    return APIResponse(
        success=True,
        data=_to_response_dto(dispense),
        message=f"Medication dispensed successfully under tracking number {dispense.dispense_number}",
    )


@router.get(
    "/prescriptions/{prescription_id}/dispensations",
    response_model=PaginatedResponse[MedicationDispenseResponse],
    summary="List all fulfillment dispensations for a prescription",
)
async def list_prescription_dispensations(
    prescription_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List dispensation history and refills for a specific prescription."""
    prescription = await get_prescription_by_id(db, prescription_id)
    if not prescription:
        raise EntityNotFoundException("MedicationRequest", prescription_id)

    # Access control
    if current_user.role not in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB):
        patient = await patient_service.get_patient_by_id(db, prescription.patient_id)
        if not patient or patient.user_id != current_user.id:
            raise PermissionDeniedException("You are not authorized to view dispensations for this prescription.")

    filter_params = MedicationDispenseFilter(
        prescription_id=prescription_id,
        skip=skip,
        limit=limit,
    )
    dispensations, total = await list_dispensations(db, filter_params)
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    current_page = (skip // limit) + 1

    return PaginatedResponse(
        success=True,
        data=[_to_response_dto(d) for d in dispensations],
        pagination=PaginationMeta(
            total_count=total,
            page=current_page,
            limit=limit,
            total_pages=total_pages,
            has_next=current_page < total_pages,
            has_prev=current_page > 1,
        ),
    )


@router.post(
    "/dispensations",
    response_model=APIResponse[MedicationDispenseResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a medication dispensation record",
)
async def record_dispensation(
    payload: MedicationDispenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Directly record a dispensation fulfillment against an active prescription."""
    if current_user.role not in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB):
        raise PermissionDeniedException(
            message="Only authorized clinical practitioners or pharmacy staff can dispense medications."
        )

    dispense = await create_dispense(db, payload, dispenser_user=current_user)
    return APIResponse(
        success=True,
        data=_to_response_dto(dispense),
        message=f"Medication dispensation recorded with number {dispense.dispense_number}",
    )


@router.get(
    "/dispensations",
    response_model=PaginatedResponse[MedicationDispenseResponse],
    summary="List and filter pharmacy dispensations",
)
async def get_dispensations(
    patient_id: Optional[str] = Query(None, description="Filter by patient UUID"),
    prescription_id: Optional[str] = Query(None, description="Filter by prescription UUID"),
    status: Optional[MedicationDispenseStatus] = Query(None, description="Filter by status"),
    lot_number: Optional[str] = Query(None, description="Filter by lot number"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query pharmacy dispensations with role-based scoping."""
    effective_patient_id = patient_id

    # If logged in user is a patient, restrict to own profile
    if current_user.role == UserRole.PATIENT:
        patient = await patient_service.get_patient_by_user_id(db, current_user.id)
        if not patient:
            raise PermissionDeniedException(message="Patient profile not found for user")
        effective_patient_id = patient.id

    filter_params = MedicationDispenseFilter(
        patient_id=effective_patient_id,
        prescription_id=prescription_id,
        status=status,
        lot_number=lot_number,
        skip=skip,
        limit=limit,
    )
    dispensations, total = await list_dispensations(db, filter_params)
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    current_page = (skip // limit) + 1

    return PaginatedResponse(
        success=True,
        data=[_to_response_dto(d) for d in dispensations],
        pagination=PaginationMeta(
            total_count=total,
            page=current_page,
            limit=limit,
            total_pages=total_pages,
            has_next=current_page < total_pages,
            has_prev=current_page > 1,
        ),
    )


@router.get(
    "/dispensations/{dispense_id}",
    response_model=APIResponse[MedicationDispenseResponse],
    summary="Get medication dispensation details by UUID",
)
async def get_dispensation(
    dispense_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full details of a single dispensation."""
    dispense = await get_dispense_by_id(db, dispense_id)
    if not dispense:
        raise EntityNotFoundException("MedicationDispense", dispense_id)

    await _verify_dispense_read_access(db, dispense, current_user)

    return APIResponse(
        success=True,
        data=_to_response_dto(dispense),
    )


@router.get(
    "/dispensations/{dispense_id}/fhir",
    response_model=FHIRMedicationDispense,
    summary="Export dispensation as canonical HL7 FHIR Release 4 MedicationDispense",
)
async def export_dispensation_fhir(
    dispense_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export single dispensation formatted as certified HL7 FHIR Release 4 MedicationDispense."""
    dispense = await get_dispense_by_id(db, dispense_id)
    if not dispense:
        raise EntityNotFoundException("MedicationDispense", dispense_id)

    await _verify_dispense_read_access(db, dispense, current_user)

    return to_fhir_medication_dispense(
        dispense,
        medication=dispense.medication,
        prescription=dispense.prescription,
    )


@router.patch(
    "/dispensations/{dispense_id}",
    response_model=APIResponse[MedicationDispenseResponse],
    summary="Update dispensation fulfillment status or notes",
)
async def patch_dispensation(
    dispense_id: str,
    payload: MedicationDispenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update status (e.g. preparation -> completed) or record notes on a dispensation."""
    if current_user.role not in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB):
        raise PermissionDeniedException(
            message="Only authorized clinical practitioners or pharmacy staff can update dispensations."
        )

    updated = await update_dispense(db, dispense_id, payload)
    return APIResponse(
        success=True,
        data=_to_response_dto(updated),
        message="Dispensation updated successfully",
    )
