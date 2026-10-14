"""Electronic Prescription and MedicationRequest service layer for NIRMAYA platform.

Provides clinical business logic for authoring, modifying, querying, cancelling,
and cryptographically signing HL7 FHIR R4-compliant e-prescriptions with
medicolegal SHA-256 digital signature attestation and immutability enforcement.
"""

from datetime import datetime, timezone
import hashlib
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, EntityNotFoundException
from app.models.appointment import Appointment
from app.models.condition import ClinicalCondition
from app.models.doctor import DoctorProfile
from app.models.enums import MedicationRequestStatus
from app.models.medication import Medication
from app.models.medication_request import MedicationRequest
from app.models.patient import PatientProfile
from app.schemas.medication_request import (
    MedicationRequestCreate,
    MedicationRequestFilter,
    MedicationRequestUpdate,
)


def _eager_load_options():
    return [
        selectinload(MedicationRequest.patient).selectinload(PatientProfile.user),
        selectinload(MedicationRequest.doctor).selectinload(DoctorProfile.user),
        selectinload(MedicationRequest.encounter),
        selectinload(MedicationRequest.medication),
        selectinload(MedicationRequest.reason_condition),
    ]


async def create_prescription(
    db: AsyncSession,
    patient_id: str,
    payload: MedicationRequestCreate,
    author_doctor_id: Optional[str] = None,
) -> MedicationRequest:
    """Author a new electronic prescription in draft status."""
    # 1. Verify patient exists
    patient = await db.scalar(select(PatientProfile).where(PatientProfile.id == patient_id))
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    # 2. Verify catalog medication exists
    medication = await db.scalar(select(Medication).where(Medication.id == payload.medication_id))
    if not medication:
        raise EntityNotFoundException("Medication", payload.medication_id)

    # 3. Resolve and verify prescriber doctor
    effective_doctor_id = author_doctor_id
    if effective_doctor_id:
        doctor = await db.scalar(select(DoctorProfile).where(DoctorProfile.id == effective_doctor_id))
        if not doctor:
            raise EntityNotFoundException("Doctor", effective_doctor_id)

    # 4. Verify encounter if linked
    if payload.encounter_id:
        encounter = await db.scalar(select(Appointment).where(Appointment.id == payload.encounter_id))
        if not encounter:
            raise EntityNotFoundException("Appointment", payload.encounter_id)

    # 5. Verify condition if linked
    if payload.reason_reference_id:
        condition = await db.scalar(select(ClinicalCondition).where(ClinicalCondition.id == payload.reason_reference_id))
        if not condition:
            raise EntityNotFoundException("Condition", payload.reason_reference_id)

    # 6. Instantiate prescription entity
    prescription = MedicationRequest(
        patient_id=patient_id,
        doctor_id=effective_doctor_id,
        encounter_id=payload.encounter_id,
        medication_id=payload.medication_id,
        status=MedicationRequestStatus.DRAFT,
        intent=payload.intent,
        priority=payload.priority,
        dosage_text=payload.dosage_text,
        dose_quantity=payload.dose_quantity,
        dose_unit=payload.dose_unit,
        route=payload.route,
        frequency=payload.frequency,
        period=payload.period,
        period_unit=payload.period_unit,
        as_needed=payload.as_needed,
        as_needed_reason=payload.as_needed_reason,
        additional_instructions=payload.additional_instructions,
        dispense_quantity=payload.dispense_quantity,
        dispense_unit=payload.dispense_unit,
        expected_supply_duration_days=payload.expected_supply_duration_days,
        number_of_repeats_allowed=payload.number_of_repeats_allowed,
        validity_period_start=payload.validity_period_start,
        validity_period_end=payload.validity_period_end,
        allow_generic_substitution=payload.allow_generic_substitution,
        substitution_reason=payload.substitution_reason,
        reason_code=payload.reason_code,
        reason_reference_id=payload.reason_reference_id,
        note=payload.note,
        is_signed=False,
    )

    db.add(prescription)
    await db.commit()

    # Re-fetch with eager loaded relationships
    return await get_prescription_by_id(db, prescription.id)


async def get_prescription_by_id(
    db: AsyncSession,
    prescription_id: str,
) -> MedicationRequest:
    """Retrieve an electronic prescription by its unique UUID."""
    stmt = (
        select(MedicationRequest)
        .where(MedicationRequest.id == prescription_id)
        .options(*_eager_load_options())
    )
    prescription = await db.scalar(stmt)
    if not prescription:
        raise EntityNotFoundException("MedicationRequest", prescription_id)

    return prescription


async def update_prescription(
    db: AsyncSession,
    prescription_id: str,
    payload: MedicationRequestUpdate,
) -> MedicationRequest:
    """Update a draft prescription prior to cryptographic digital signature."""
    prescription = await get_prescription_by_id(db, prescription_id)

    if prescription.is_signed:
        raise ConflictException(
            message="Cannot modify a finalized and digitally signed prescription. "
                    "Signed clinical prescriptions are immutable under FHIR & ABDM standards.",
            error_code="IMMUTABLE_SIGNED_RECORD",
        )

    # If updating medication, ensure it exists
    if payload.medication_id and payload.medication_id != prescription.medication_id:
        medication = await db.scalar(select(Medication).where(Medication.id == payload.medication_id))
        if not medication:
            raise EntityNotFoundException("Medication", payload.medication_id)

    # If updating condition reference
    if payload.reason_reference_id and payload.reason_reference_id != prescription.reason_reference_id:
        condition = await db.scalar(select(ClinicalCondition).where(ClinicalCondition.id == payload.reason_reference_id))
        if not condition:
            raise EntityNotFoundException("Condition", payload.reason_reference_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prescription, field, value)

    await db.commit()
    return await get_prescription_by_id(db, prescription.id)


async def sign_prescription(
    db: AsyncSession,
    prescription_id: str,
    signing_doctor_id: Optional[str] = None,
    signature_notes: Optional[str] = None,
) -> MedicationRequest:
    """Digitally sign and authorize an e-prescription with SHA-256 cryptographic sealing.

    Transitions status to ACTIVE and locks the record into an immutable medicolegal artifact.
    """
    prescription = await get_prescription_by_id(db, prescription_id)

    if prescription.is_signed:
        return prescription

    if signing_doctor_id:
        doctor = await db.scalar(select(DoctorProfile).where(DoctorProfile.id == signing_doctor_id))
        if not doctor:
            raise EntityNotFoundException("Doctor", signing_doctor_id)
        prescription.doctor_id = signing_doctor_id

    now_utc = datetime.now(timezone.utc)

    # Canonical string representation for deterministic tamper-evident hashing
    raw_signature_payload = (
        f"rx:{prescription.id}|"
        f"patient:{prescription.patient_id}|"
        f"doctor:{prescription.doctor_id}|"
        f"med:{prescription.medication_id}|"
        f"dose:{prescription.dose_quantity}_{prescription.dose_unit}|"
        f"freq:{prescription.frequency}|"
        f"route:{prescription.route}|"
        f"disp:{prescription.dispense_quantity}_{prescription.dispense_unit}|"
        f"repeats:{prescription.number_of_repeats_allowed}|"
        f"signed_at:{now_utc.isoformat()}"
    )

    signature_digest = hashlib.sha256(raw_signature_payload.encode("utf-8")).hexdigest()

    prescription.is_signed = True
    prescription.status = MedicationRequestStatus.ACTIVE
    prescription.signature_hash = signature_digest
    prescription.signed_at = now_utc

    if signature_notes:
        prescription.note = (
            f"{prescription.note}\n[Signed]: {signature_notes}"
            if prescription.note
            else f"[Signed]: {signature_notes}"
        )

    await db.commit()
    return await get_prescription_by_id(db, prescription.id)


async def cancel_prescription(
    db: AsyncSession,
    prescription_id: str,
    cancellation_reason: str,
) -> MedicationRequest:
    """Discontinue / cancel an active or draft prescription with clinical rationale."""
    prescription = await get_prescription_by_id(db, prescription_id)

    prescription.status = MedicationRequestStatus.CANCELLED
    prescription.cancellation_reason = cancellation_reason

    await db.commit()
    return await get_prescription_by_id(db, prescription.id)


async def mark_entered_in_error(
    db: AsyncSession,
    prescription_id: str,
) -> MedicationRequest:
    """Mark a prescription record as entered-in-error per FHIR audit standards."""
    prescription = await get_prescription_by_id(db, prescription_id)

    prescription.status = MedicationRequestStatus.ENTERED_IN_ERROR
    await db.commit()
    return await get_prescription_by_id(db, prescription.id)


async def list_prescriptions(
    db: AsyncSession,
    patient_id: Optional[str] = None,
    doctor_id: Optional[str] = None,
    filters: Optional[MedicationRequestFilter] = None,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[MedicationRequest], int]:
    """Query paginated electronic prescriptions with filtering."""
    base_query = select(MedicationRequest)

    if patient_id:
        base_query = base_query.where(MedicationRequest.patient_id == patient_id)

    if doctor_id:
        base_query = base_query.where(MedicationRequest.doctor_id == doctor_id)

    if filters:
        if filters.status:
            base_query = base_query.where(MedicationRequest.status == filters.status)
        if filters.is_signed is not None:
            base_query = base_query.where(MedicationRequest.is_signed == filters.is_signed)
        if filters.doctor_id:
            base_query = base_query.where(MedicationRequest.doctor_id == filters.doctor_id)
        if filters.encounter_id:
            base_query = base_query.where(MedicationRequest.encounter_id == filters.encounter_id)
        if filters.reason_code:
            base_query = base_query.where(MedicationRequest.reason_code == filters.reason_code)
        if filters.date_from:
            base_query = base_query.where(MedicationRequest.authored_on >= filters.date_from)
        if filters.date_to:
            base_query = base_query.where(MedicationRequest.authored_on <= filters.date_to)

    count_stmt = select(func.count()).select_from(base_query.subquery())
    count_res = await db.execute(count_stmt)
    total = count_res.scalar() or 0

    offset = (page - 1) * limit
    data_stmt = (
        base_query.options(*_eager_load_options())
        .order_by(MedicationRequest.authored_on.desc())
        .offset(offset)
        .limit(limit)
    )
    data_res = await db.execute(data_stmt)
    prescriptions = list(data_res.scalars().all())

    return prescriptions, total
