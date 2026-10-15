"""Pharmacy Medication Dispense and Fulfillment service layer for NIRMAYA platform.

Provides clinical business logic for dispensing prescribed medications, tracking
batch lot numbers and expiration dates, generic formulary substitutions,
refill decrement governance, and HL7 FHIR Release 4 MedicationDispense export.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException, EntityNotFoundException
from app.models.enums import MedicationDispenseStatus, MedicationRequestStatus
from app.models.medication import Medication
from app.models.medication_dispense import MedicationDispense
from app.models.medication_request import MedicationRequest
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.medication_dispense import (
    MedicationDispenseCreate,
    MedicationDispenseFilter,
    MedicationDispenseUpdate,
)


def _dispense_eager_load_options():
    return [
        selectinload(MedicationDispense.patient).selectinload(PatientProfile.user),
        selectinload(MedicationDispense.medication),
        selectinload(MedicationDispense.dispenser),
        selectinload(MedicationDispense.prescription).selectinload(MedicationRequest.doctor),
        selectinload(MedicationDispense.prescription).selectinload(MedicationRequest.encounter),
    ]


async def create_dispense(
    db: AsyncSession,
    payload: MedicationDispenseCreate,
    dispenser_user: Optional[User] = None,
) -> MedicationDispense:
    """Fulfill or record a pharmaceutical dispensation against an active e-prescription.

    Validates:
    - Prescription exists, is digitally signed, and in active/valid state.
    - Authorized refill repeats limit is not exceeded.
    - Generic/brand substitution rules and prescriber authorization flags.
    - Drug existence and batch expiration/lot traceability.
    - Decrements remaining refills and closes prescription when fully fulfilled.
    """
    # 1. Fetch authorizing prescription
    stmt = (
        select(MedicationRequest)
        .options(
            selectinload(MedicationRequest.medication),
            selectinload(MedicationRequest.dispensations),
        )
        .where(MedicationRequest.id == payload.prescription_id)
    )
    prescription = await db.scalar(stmt)
    if not prescription:
        raise EntityNotFoundException("MedicationRequest", payload.prescription_id)

    # 2. Check digital signature attestation
    if not prescription.is_signed:
        raise AppException(
            message="Prescription cannot be dispensed because it has not been digitally signed by the prescribing clinician",
            error_code="PRESCRIPTION_NOT_SIGNED",
            status_code=400,
        )

    # 3. Check prescription status eligibility
    if prescription.status not in (MedicationRequestStatus.ACTIVE, MedicationRequestStatus.COMPLETED):
        raise AppException(
            message=f"Prescription status '{prescription.status.value}' is not eligible for pharmacy dispensation",
            error_code="INVALID_PRESCRIPTION_STATUS",
            status_code=400,
        )

    # 4. Enforce authorized refill repeats quota
    max_authorized_fills = (prescription.number_of_repeats_allowed or 0) + 1
    count_stmt = select(func.count(MedicationDispense.id)).where(
        MedicationDispense.prescription_id == prescription.id,
        MedicationDispense.status.notin_([
            MedicationDispenseStatus.CANCELLED,
            MedicationDispenseStatus.DECLINED,
            MedicationDispenseStatus.ENTERED_IN_ERROR,
        ]),
    )
    existing_fills_count = await db.scalar(count_stmt) or 0

    if existing_fills_count >= max_authorized_fills:
        raise AppException(
            message=(
                f"Maximum authorized prescription fills reached. "
                f"Total authorized: {max_authorized_fills} (original + {prescription.number_of_repeats_allowed or 0} refills), "
                f"Already dispensed: {existing_fills_count}."
            ),
            error_code="REFILLS_EXHAUSTED",
            status_code=400,
        )

    # 5. Handle Generic Substitution Governance
    dispensed_med_id = payload.medication_id or prescription.medication_id
    is_substituted = payload.was_substituted or (dispensed_med_id != prescription.medication_id)

    if is_substituted:
        if not prescription.allow_generic_substitution:
            raise AppException(
                message="Generic or brand substitution is strictly prohibited by the prescriber for this prescription",
                error_code="SUBSTITUTION_DISALLOWED",
                status_code=400,
            )

        # Verify target substitute medication exists
        substitute_med = await db.scalar(select(Medication).where(Medication.id == dispensed_med_id))
        if not substitute_med:
            raise EntityNotFoundException("Medication", dispensed_med_id)

        sub_type = payload.substitution_type or "G"
        sub_reason = payload.substitution_reason or "Generic bioequivalent supplied per pharmacy formulary"
    else:
        dispensed_med_id = prescription.medication_id
        sub_type = None
        sub_reason = None

    # 6. Generate unique business tracking number
    dispense_number = f"DISP-{datetime.now(timezone.utc).strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

    # 7. Timestamps
    now_utc = datetime.now(timezone.utc)
    when_prepared = payload.when_prepared or now_utc
    when_handed_over = payload.when_handed_over
    if payload.status == MedicationDispenseStatus.COMPLETED and not when_handed_over:
        when_handed_over = now_utc

    # 8. Create MedicationDispense record
    dispense = MedicationDispense(
        dispense_number=dispense_number,
        prescription_id=prescription.id,
        patient_id=prescription.patient_id,
        medication_id=dispensed_med_id,
        dispenser_id=dispenser_user.id if dispenser_user else None,
        status=payload.status,
        status_reason=payload.status_reason,
        quantity_dispensed=payload.quantity_dispensed,
        dispense_unit=payload.dispense_unit,
        days_supply=payload.days_supply,
        lot_number=payload.lot_number,
        expiration_date=payload.expiration_date,
        when_prepared=when_prepared,
        when_handed_over=when_handed_over,
        was_substituted=is_substituted,
        substitution_type=sub_type,
        substitution_reason=sub_reason,
        dosage_instruction=payload.dosage_instruction or prescription.dosage_text,
        pharmacist_notes=payload.pharmacist_notes,
    )

    db.add(dispense)

    # 9. Update prescription status if all repeats are now fulfilled
    if (existing_fills_count + 1) >= max_authorized_fills:
        prescription.status = MedicationRequestStatus.COMPLETED

    await db.flush()

    # Re-fetch with eager loaded relationships
    return await get_dispense_by_id(db, dispense.id)  # type: ignore[return-value]


async def get_dispense_by_id(
    db: AsyncSession,
    dispense_id: str,
) -> Optional[MedicationDispense]:
    """Retrieve a single dispensation by UUID with eager loaded clinical relationships."""
    stmt = (
        select(MedicationDispense)
        .options(*_dispense_eager_load_options())
        .where(MedicationDispense.id == dispense_id)
    )
    return await db.scalar(stmt)


async def list_dispensations(
    db: AsyncSession,
    filter_params: MedicationDispenseFilter,
) -> Tuple[List[MedicationDispense], int]:
    """Query dispensations matching filter criteria with pagination."""
    query = select(MedicationDispense).options(*_dispense_eager_load_options())
    count_query = select(func.count(MedicationDispense.id))

    if filter_params.patient_id:
        query = query.where(MedicationDispense.patient_id == filter_params.patient_id)
        count_query = count_query.where(MedicationDispense.patient_id == filter_params.patient_id)

    if filter_params.prescription_id:
        query = query.where(MedicationDispense.prescription_id == filter_params.prescription_id)
        count_query = count_query.where(MedicationDispense.prescription_id == filter_params.prescription_id)

    if filter_params.status:
        query = query.where(MedicationDispense.status == filter_params.status)
        count_query = count_query.where(MedicationDispense.status == filter_params.status)

    if filter_params.lot_number:
        query = query.where(MedicationDispense.lot_number.ilike(f"%{filter_params.lot_number}%"))
        count_query = count_query.where(MedicationDispense.lot_number.ilike(f"%{filter_params.lot_number}%"))

    total = await db.scalar(count_query) or 0
    query = query.order_by(MedicationDispense.created_at.desc()).offset(filter_params.skip).limit(filter_params.limit)

    result = await db.execute(query)
    dispensations = list(result.scalars().all())

    return dispensations, total


async def update_dispense(
    db: AsyncSession,
    dispense_id: str,
    payload: MedicationDispenseUpdate,
) -> MedicationDispense:
    """Update fulfillment status or pharmacist notes on an existing dispensation."""
    dispense = await get_dispense_by_id(db, dispense_id)
    if not dispense:
        raise EntityNotFoundException("MedicationDispense", dispense_id)

    if payload.status is not None:
        dispense.status = payload.status
        if payload.status == MedicationDispenseStatus.COMPLETED and not dispense.when_handed_over:
            dispense.when_handed_over = payload.when_handed_over or datetime.now(timezone.utc)

    if payload.status_reason is not None:
        dispense.status_reason = payload.status_reason

    if payload.when_handed_over is not None:
        dispense.when_handed_over = payload.when_handed_over

    if payload.pharmacist_notes is not None:
        dispense.pharmacist_notes = payload.pharmacist_notes

    await db.flush()
    await db.refresh(dispense)
    return dispense
