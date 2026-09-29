"""Clinical appointment booking and lifecycle management service for NIRMAYA platform.

Handles slot reservation, concurrency conflict prevention, status transitions,
and automatic slot replenishment upon cancellation. Aligned with HL7 FHIR R4 Appointment.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import AppException, ConflictException, EntityNotFoundException
from app.models.appointment import Appointment, DoctorSlot
from app.models.doctor import DoctorProfile
from app.models.enums import AppointmentStatus, SlotStatus
from app.models.patient import PatientProfile
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusUpdate,
)
from app.services.slot_engine import sweep_expired_holds



def _format_appointment_response(appt: Appointment) -> AppointmentResponse:
    """Helper formatting an Appointment ORM instance into AppointmentResponse with joined details."""
    doctor_name = None
    doctor_specialty = None
    patient_name = None

    if appt.doctor:
        doctor_specialty = appt.doctor.specialty.value if hasattr(appt.doctor.specialty, "value") else str(appt.doctor.specialty)
        if appt.doctor.user:
            doctor_name = appt.doctor.user.full_name

    if appt.patient and appt.patient.user:
        patient_name = appt.patient.user.full_name

    return AppointmentResponse(
        id=appt.id,
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        slot_id=appt.slot_id,
        appointment_type=appt.appointment_type,
        status=appt.status,
        scheduled_start=appt.scheduled_start,
        scheduled_end=appt.scheduled_end,
        reason=appt.reason,
        clinical_notes=appt.clinical_notes,
        teleconsultation_url=appt.teleconsultation_url,
        created_at=appt.created_at,
        updated_at=appt.updated_at,
        doctor_name=doctor_name,
        doctor_specialty=doctor_specialty,
        patient_name=patient_name,
    )


async def book_appointment(
    db: AsyncSession,
    patient_id: str,
    payload: AppointmentCreate,
) -> AppointmentResponse:
    """Book a new clinical appointment for a patient with a doctor.

    If a slot_id is specified, verifies slot availability and locks/updates slot to BOOKED.
    Raises ConflictException if slot is already booked, held, or blocked.
    """
    # 1. Validate PatientProfile exists
    patient = await db.scalar(
        select(PatientProfile)
        .options(selectinload(PatientProfile.user))
        .where(PatientProfile.id == patient_id)
    )
    if not patient:
        raise EntityNotFoundException("PatientProfile", patient_id)

    # 2. Validate DoctorProfile exists
    doctor = await db.scalar(
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.id == payload.doctor_id)
    )
    if not doctor:
        raise EntityNotFoundException("DoctorProfile", payload.doctor_id)

    slot_entity: Optional[DoctorSlot] = None
    scheduled_start: datetime
    scheduled_end: datetime

    # 3. Process slot if provided
    if payload.slot_id:
        # Sweep expired holds first
        await sweep_expired_holds(db, slot_id=payload.slot_id)

        # Acquire exclusive row-level lock (FOR UPDATE in PostgreSQL, db-level in SQLite)
        slot_stmt = (
            select(DoctorSlot)
            .where(DoctorSlot.id == payload.slot_id)
            .with_for_update()
        )
        slot_entity = await db.scalar(slot_stmt)
        if not slot_entity:
            raise EntityNotFoundException("DoctorSlot", payload.slot_id)

        if slot_entity.doctor_id != payload.doctor_id:
            raise AppException(
                message=f"Slot '{payload.slot_id}' does not belong to Doctor '{payload.doctor_id}'",
                error_code="SLOT_DOCTOR_MISMATCH",
                status_code=400,
            )

        now_utc = datetime.now(timezone.utc)
        if slot_entity.status == SlotStatus.BOOKED:
            raise ConflictException(
                message=f"Slot '{payload.slot_id}' is already booked",
                error_code="SLOT_NOT_AVAILABLE",
            )
        elif slot_entity.status == SlotStatus.BLOCKED:
            raise ConflictException(
                message=f"Slot '{payload.slot_id}' is blocked by practitioner",
                error_code="SLOT_BLOCKED",
            )
        elif slot_entity.status == SlotStatus.HELD:
            # Check if held by another patient and hold has not expired
            if slot_entity.held_by_patient_id != patient_id and slot_entity.held_until and slot_entity.held_until > now_utc:
                raise ConflictException(
                    message=f"Slot '{payload.slot_id}' is currently held by another patient",
                    error_code="SLOT_HELD_BY_ANOTHER_PATIENT",
                )

        scheduled_start = slot_entity.start_time
        scheduled_end = slot_entity.end_time

        # Mark slot as booked and clear temporary hold metadata
        slot_entity.status = SlotStatus.BOOKED
        slot_entity.held_until = None
        slot_entity.held_by_patient_id = None
    else:
        # Non-slot ad-hoc / walk-in booking
        if not payload.scheduled_start or not payload.scheduled_end:
            raise AppException(
                message="Scheduled start and end time are required when booking without a slot",
                error_code="MISSING_SCHEDULE_TIMES",
                status_code=400,
            )
        scheduled_start = payload.scheduled_start
        scheduled_end = payload.scheduled_end


    # 4. Instantiate Appointment entity
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=payload.doctor_id,
        slot_id=payload.slot_id,
        appointment_type=payload.appointment_type,
        status=AppointmentStatus.SCHEDULED,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        reason=payload.reason,
        clinical_notes=payload.clinical_notes,
        teleconsultation_url=payload.teleconsultation_url,
    )
    db.add(appointment)
    await db.commit()

    # Re-query with full relationships for structured response
    refreshed = await get_appointment_by_id(db, appointment.id)
    if not refreshed:
        raise AppException("Failed to load newly created appointment", status_code=500)
    return _format_appointment_response(refreshed)


async def get_appointment_by_id(
    db: AsyncSession,
    appointment_id: str,
) -> Optional[Appointment]:
    """Retrieve an Appointment with joined Doctor, Patient, and User relations."""
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.doctor).selectinload(DoctorProfile.user),
            selectinload(Appointment.patient).selectinload(PatientProfile.user),
            selectinload(Appointment.slot),
        )
        .where(Appointment.id == appointment_id)
    )
    return await db.scalar(stmt)


async def list_appointments(
    db: AsyncSession,
    patient_id: Optional[str] = None,
    doctor_id: Optional[str] = None,
    status: Optional[AppointmentStatus] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[AppointmentResponse], int]:
    """Query appointments with multi-parameter filtering and pagination."""
    filters = []
    if patient_id:
        filters.append(Appointment.patient_id == patient_id)
    if doctor_id:
        filters.append(Appointment.doctor_id == doctor_id)
    if status:
        filters.append(Appointment.status == status)
    if from_date:
        filters.append(Appointment.scheduled_start >= from_date)
    if to_date:
        filters.append(Appointment.scheduled_start <= to_date)

    where_clause = and_(*filters) if filters else True

    # Total count
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(Appointment).where(where_clause)
    total = (await db.scalar(count_stmt)) or 0

    # Paged query
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.doctor).selectinload(DoctorProfile.user),
            selectinload(Appointment.patient).selectinload(PatientProfile.user),
            selectinload(Appointment.slot),
        )
        .where(where_clause)
        .order_by(Appointment.scheduled_start.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.scalars(stmt)
    records = list(result.all())
    formatted = [_format_appointment_response(r) for r in records]
    return formatted, total


async def update_appointment_status(
    db: AsyncSession,
    appointment_id: str,
    payload: AppointmentStatusUpdate,
) -> AppointmentResponse:
    """Transition appointment status and handle resource lifecycle (e.g. freeing slot on cancellation)."""
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise EntityNotFoundException("Appointment", appointment_id)

    previous_status = appointment.status
    target_status = payload.status

    # If cancelling, replenish/free the associated slot
    if target_status == AppointmentStatus.CANCELLED:
        if appointment.slot_id:
            slot_stmt = (
                select(DoctorSlot)
                .where(DoctorSlot.id == appointment.slot_id)
                .with_for_update()
            )
            slot = await db.scalar(slot_stmt)
            if slot and slot.status in (SlotStatus.BOOKED, SlotStatus.HELD):
                slot.status = SlotStatus.AVAILABLE
                slot.held_until = None
                slot.held_by_patient_id = None

    appointment.status = target_status


    if payload.clinical_notes:
        if appointment.clinical_notes:
            appointment.clinical_notes = f"{appointment.clinical_notes}\n{payload.clinical_notes}"
        else:
            appointment.clinical_notes = payload.clinical_notes

    await db.commit()
    refreshed = await get_appointment_by_id(db, appointment_id)
    if not refreshed:
        raise AppException("Failed to load updated appointment", status_code=500)
    return _format_appointment_response(refreshed)
