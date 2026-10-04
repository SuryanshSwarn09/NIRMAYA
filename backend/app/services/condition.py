"""Clinical Condition & Problem List service layer for NIRMAYA platform.

Provides business logic for recording diagnoses, querying longitudinal problem lists,
status transitions (e.g. active to resolved), and HL7 FHIR R4 interoperability.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import EntityNotFoundException
from app.models.appointment import Appointment
from app.models.condition import ClinicalCondition
from app.models.doctor import DoctorProfile
from app.models.enums import ClinicalStatus
from app.models.patient import PatientProfile
from app.schemas.condition import ConditionCreate, ConditionFilter, ConditionUpdate


async def record_condition(
    db: AsyncSession,
    patient_id: str,
    payload: ConditionCreate,
    recorder_doctor_id: Optional[str] = None,
) -> ClinicalCondition:
    """Record a new clinical condition onto a patient's problem list.

    Args:
        db: Async database session.
        patient_id: UUID of the subject patient.
        payload: Condition creation attributes.
        recorder_doctor_id: Optional UUID of the diagnosing DoctorProfile.

    Returns:
        The newly persisted ClinicalCondition instance.

    Raises:
        EntityNotFoundException: If patient, encounter, or doctor cannot be found.
    """
    # 1. Validate patient existence
    patient = await db.scalar(
        select(PatientProfile).where(PatientProfile.id == patient_id)
    )
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    # 2. Validate encounter if linked
    if payload.encounter_id:
        encounter = await db.scalar(
            select(Appointment).where(
                Appointment.id == payload.encounter_id,
                Appointment.patient_id == patient_id,
            )
        )
        if not encounter:
            raise EntityNotFoundException("Appointment encounter", payload.encounter_id)

    # 3. Validate recorder doctor if linked
    if recorder_doctor_id:
        doctor = await db.scalar(
            select(DoctorProfile).where(DoctorProfile.id == recorder_doctor_id)
        )
        if not doctor:
            raise EntityNotFoundException("Doctor", recorder_doctor_id)

    # 4. Handle auto-abatement if resolved on creation
    abatement_time = payload.abatement_date_time
    if payload.clinical_status == ClinicalStatus.RESOLVED and not abatement_time:
        abatement_time = datetime.now(timezone.utc)

    condition = ClinicalCondition(
        patient_id=patient_id,
        encounter_id=payload.encounter_id,
        recorded_by_doctor_id=recorder_doctor_id,
        clinical_status=payload.clinical_status,
        verification_status=payload.verification_status,
        category=payload.category,
        severity=payload.severity,
        code_coding_system=payload.code_coding_system,
        code_value=payload.code_value,
        code_display=payload.code_display,
        body_site=payload.body_site,
        onset_date_time=payload.onset_date_time,
        abatement_date_time=abatement_time,
        recorded_date=datetime.now(timezone.utc),
        note=payload.note,
    )

    db.add(condition)
    await db.flush()
    await db.refresh(condition)
    return condition


async def get_condition_by_id(
    db: AsyncSession,
    condition_id: str,
) -> Optional[ClinicalCondition]:
    """Retrieve a single ClinicalCondition by ID with associated relationships loaded."""
    stmt = (
        select(ClinicalCondition)
        .options(
            selectinload(ClinicalCondition.patient).selectinload(PatientProfile.user),
            selectinload(ClinicalCondition.recorded_by_doctor).selectinload(DoctorProfile.user),
            selectinload(ClinicalCondition.encounter),
        )
        .where(ClinicalCondition.id == condition_id)
    )
    return await db.scalar(stmt)


async def list_patient_conditions(
    db: AsyncSession,
    patient_id: str,
    filters: Optional[ConditionFilter] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[ClinicalCondition], int]:
    """List conditions on a patient's problem list with optional filtering and pagination.

    Args:
        db: Async database session.
        patient_id: UUID of the subject patient.
        filters: Optional filter criteria (status, category, severity, encounter).
        skip: Offset for pagination.
        limit: Max records to return.

    Returns:
        Tuple of (list of ClinicalCondition, total count matching filter).
    """
    # Verify patient exists
    patient = await db.scalar(
        select(PatientProfile.id).where(PatientProfile.id == patient_id)
    )
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    base_query = (
        select(ClinicalCondition)
        .where(ClinicalCondition.patient_id == patient_id)
        .options(
            selectinload(ClinicalCondition.recorded_by_doctor).selectinload(DoctorProfile.user),
            selectinload(ClinicalCondition.encounter),
        )
    )
    count_query = (
        select(func.count(ClinicalCondition.id))
        .where(ClinicalCondition.patient_id == patient_id)
    )

    if filters:
        if filters.clinical_status is not None:
            base_query = base_query.where(ClinicalCondition.clinical_status == filters.clinical_status)
            count_query = count_query.where(ClinicalCondition.clinical_status == filters.clinical_status)
        if filters.verification_status is not None:
            base_query = base_query.where(ClinicalCondition.verification_status == filters.verification_status)
            count_query = count_query.where(ClinicalCondition.verification_status == filters.verification_status)
        if filters.category is not None:
            base_query = base_query.where(ClinicalCondition.category == filters.category)
            count_query = count_query.where(ClinicalCondition.category == filters.category)
        if filters.severity is not None:
            base_query = base_query.where(ClinicalCondition.severity == filters.severity)
            count_query = count_query.where(ClinicalCondition.severity == filters.severity)
        if filters.encounter_id is not None:
            base_query = base_query.where(ClinicalCondition.encounter_id == filters.encounter_id)
            count_query = count_query.where(ClinicalCondition.encounter_id == filters.encounter_id)

    total_count = await db.scalar(count_query) or 0
    stmt = (
        base_query
        .order_by(ClinicalCondition.recorded_date.desc())
        .offset(skip)
        .limit(limit)
    )
    results = await db.scalars(stmt)
    return list(results.all()), total_count


async def update_condition(
    db: AsyncSession,
    condition_id: str,
    payload: ConditionUpdate,
) -> ClinicalCondition:
    """Update condition clinical status, severity, notes, or resolution timestamps.

    Args:
        db: Async database session.
        condition_id: UUID of condition to update.
        payload: Attributes to update.

    Returns:
        The updated ClinicalCondition entity.

    Raises:
        EntityNotFoundException: If condition does not exist.
    """
    condition = await get_condition_by_id(db, condition_id)
    if not condition:
        raise EntityNotFoundException("Condition", condition_id)

    if payload.clinical_status is not None:
        condition.clinical_status = payload.clinical_status
        # If transitioning to RESOLVED and abatement time not supplied, auto-set UTC now
        if payload.clinical_status == ClinicalStatus.RESOLVED and not condition.abatement_date_time and not payload.abatement_date_time:
            condition.abatement_date_time = datetime.now(timezone.utc)

    if payload.verification_status is not None:
        condition.verification_status = payload.verification_status
    if payload.category is not None:
        condition.category = payload.category
    if payload.severity is not None:
        condition.severity = payload.severity
    if payload.body_site is not None:
        condition.body_site = payload.body_site
    if payload.onset_date_time is not None:
        condition.onset_date_time = payload.onset_date_time
    if payload.abatement_date_time is not None:
        condition.abatement_date_time = payload.abatement_date_time
    if payload.note is not None:
        if condition.note:
            condition.note = f"{condition.note}\n{payload.note}"
        else:
            condition.note = payload.note

    await db.flush()
    await db.refresh(condition)
    return condition


async def delete_condition(
    db: AsyncSession,
    condition_id: str,
) -> None:
    """Permanently remove a clinical condition from the problem list."""
    condition = await db.scalar(
        select(ClinicalCondition).where(ClinicalCondition.id == condition_id)
    )
    if not condition:
        raise EntityNotFoundException("Condition", condition_id)

    await db.delete(condition)
    await db.flush()
