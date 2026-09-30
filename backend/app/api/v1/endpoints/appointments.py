"""Clinical appointment booking and encounter lifecycle API endpoints for NIRMAYA."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.core.exceptions import (
    AppException,
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.db.session import get_db
from app.fhir import (
    FHIRAppointment,
    FHIREncounter,
    to_fhir_appointment,
    to_fhir_encounter,
)
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus, UserRole
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusUpdate,
)
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.services import appointment as appointment_service
from app.services import doctor as doctor_service
from app.services import patient as patient_service

router = APIRouter()


def _verify_appointment_access(appt: Appointment, current_user: User) -> None:
    """Verify that current user is the patient, doctor, or an administrator."""
    is_admin = current_user.role == UserRole.ADMIN
    is_patient = appt.patient and appt.patient.user_id == current_user.id
    is_doctor = appt.doctor and appt.doctor.user_id == current_user.id

    if not (is_admin or is_patient or is_doctor):
        raise PermissionDeniedException(
            message="You are not authorized to access this clinical encounter resource"
        )



@router.post(
    "/",
    response_model=APIResponse[AppointmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Book a clinical appointment",
    description="Reserves a doctor consultation slot and creates an HL7 FHIR aligned Appointment record.",
)
async def create_appointment(
    payload: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AppointmentResponse]:
    """Book a new clinical consultation appointment."""
    # Resolve PatientProfile for current user
    patient = await patient_service.get_patient_by_user_id(db, current_user.id)
    if not patient and current_user.role != UserRole.ADMIN:
        raise AppException(
            message="Authenticated user does not have an active patient vault profile",
            error_code="PATIENT_PROFILE_REQUIRED",
            status_code=400,
        )

    patient_id = patient.id if patient else payload.doctor_id  # Fallback if admin
    appt = await appointment_service.book_appointment(
        db=db,
        patient_id=patient_id,
        payload=payload,
    )
    return APIResponse(
        message="Clinical appointment scheduled successfully",
        data=appt,
    )


@router.get(
    "/",
    response_model=PaginatedResponse[AppointmentResponse],
    summary="List consultation appointments",
    description="Retrieves a paginated list of appointments filtered by the authenticated user's clinical role.",
)
async def list_user_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status", description="Filter by appointment status"),
    from_date: Optional[datetime] = Query(None, description="Start date filter (UTC)"),
    to_date: Optional[datetime] = Query(None, description="End date filter (UTC)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AppointmentResponse]:
    """List appointments for the current authenticated persona."""
    patient_id: Optional[str] = None
    doctor_id: Optional[str] = None

    if current_user.role == UserRole.PATIENT:
        patient = await patient_service.get_patient_by_user_id(db, current_user.id)
        if patient:
            patient_id = patient.id
        else:
            return PaginatedResponse(
                data=[],
                meta=PaginationMeta(total=0, limit=limit, offset=offset, has_more=False),
            )
    elif current_user.role == UserRole.DOCTOR:
        doctor = await doctor_service.get_doctor_by_user_id(db, current_user.id)
        if doctor:
            doctor_id = doctor.id
        else:
            return PaginatedResponse(
                data=[],
                meta=PaginationMeta(total=0, limit=limit, offset=offset, has_more=False),
            )

    items, total = await appointment_service.list_appointments(
        db=db,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status=status_filter,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse(
        data=items,
        meta=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.get(
    "/{appointment_id}",
    response_model=APIResponse[AppointmentResponse],
    summary="Get appointment details",
    description="Retrieves a single clinical appointment by UUID, enforcing participant authorization.",
)
async def get_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AppointmentResponse]:
    """Get appointment by ID enforcing patient, practitioner, or admin authorization."""
    appt = await appointment_service.get_appointment_by_id(db, appointment_id)
    if not appt:
        raise EntityNotFoundException("Appointment", appointment_id)

    # Verify authorization: current user must be the patient, doctor, or admin
    is_admin = current_user.role == UserRole.ADMIN
    is_patient = appt.patient and appt.patient.user_id == current_user.id
    is_doctor = appt.doctor and appt.doctor.user_id == current_user.id

    if not (is_admin or is_patient or is_doctor):
        raise PermissionDeniedException(
            message="You are not authorized to view this clinical appointment"
        )

    response_data = appointment_service._format_appointment_response(appt)
    return APIResponse(
        message="Appointment details retrieved successfully",
        data=response_data,
    )


@router.patch(
    "/{appointment_id}/status",
    response_model=APIResponse[AppointmentResponse],
    summary="Update appointment status",
    description="Transitions an appointment lifecycle state (e.g., confirmed, completed, cancelled).",
)
async def update_status(
    appointment_id: str,
    payload: AppointmentStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AppointmentResponse]:
    """Update appointment status and handle resource lifecycle transitions."""
    appt = await appointment_service.get_appointment_by_id(db, appointment_id)
    if not appt:
        raise EntityNotFoundException("Appointment", appointment_id)

    is_admin = current_user.role == UserRole.ADMIN
    is_patient = appt.patient and appt.patient.user_id == current_user.id
    is_doctor = appt.doctor and appt.doctor.user_id == current_user.id

    if not (is_admin or is_patient or is_doctor):
        raise PermissionDeniedException(
            message="You are not authorized to modify this clinical appointment"
        )

    # Patients can only cancel their appointments
    if is_patient and not is_admin and not is_doctor:
        if payload.status != AppointmentStatus.CANCELLED:
            raise PermissionDeniedException(
                message="Patients are only authorized to cancel their appointments"
            )

    updated = await appointment_service.update_appointment_status(
        db=db,
        appointment_id=appointment_id,
        payload=payload,
    )
    return APIResponse(
        message=f"Appointment status transitioned to {payload.status.value}",
        data=updated,
    )


# ============================================================================
# HL7 FHIR Release 4 Endpoints
# ============================================================================


@router.get(
    "/{appointment_id}/fhir",
    response_model=APIResponse[FHIRAppointment],
    summary="Export appointment as HL7 FHIR R4 Appointment",
    description="Serializes internal clinical appointment model into an HL7 FHIR Release 4 compliant Appointment resource.",
)
async def get_appointment_fhir(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[FHIRAppointment]:
    """Retrieve appointment formatted as an HL7 FHIR R4 Appointment resource."""
    appt = await appointment_service.get_appointment_by_id(db, appointment_id)
    if not appt:
        raise EntityNotFoundException("Appointment", appointment_id)

    _verify_appointment_access(appt, current_user)
    fhir_resource = to_fhir_appointment(appt)
    return APIResponse(
        message="HL7 FHIR R4 Appointment resource generated successfully",
        data=fhir_resource,
    )


@router.get(
    "/{appointment_id}/encounter",
    response_model=APIResponse[FHIREncounter],
    summary="Export encounter as HL7 FHIR R4 Encounter",
    description="Serializes clinical encounter into an HL7 FHIR Release 4 compliant Encounter resource with ambulatory/virtual classification.",
)
async def get_encounter_fhir(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[FHIREncounter]:
    """Retrieve clinical encounter formatted as an HL7 FHIR R4 Encounter resource."""
    appt = await appointment_service.get_appointment_by_id(db, appointment_id)
    if not appt:
        raise EntityNotFoundException("Appointment", appointment_id)

    _verify_appointment_access(appt, current_user)
    fhir_resource = to_fhir_encounter(appt)
    return APIResponse(
        message="HL7 FHIR R4 Encounter resource generated successfully",
        data=fhir_resource,
    )

