"""Conflict-free doctor consultation slot generation engine for NIRMAYA platform.

Computes discrete, non-overlapping availability windows adhering to clinical practice hours,
break intervals, and ensures idempotent slot generation across PostgreSQL and SQLite.
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional, Set
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictException,
    EntityNotFoundException,
    PermissionDeniedException,
)

from app.models.appointment import DoctorSlot
from app.models.doctor import DoctorProfile
from app.models.enums import SlotStatus
from app.schemas.appointment import (
    DoctorSlotResponse,
    SlotGenerateRequest,
    SlotGenerateResult,
)


def _normalize_utc(dt: datetime) -> datetime:
    """Normalize datetime to UTC and remove microsecond precision for exact interval matching."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.replace(microsecond=0)


async def generate_slots_for_doctor(
    db: AsyncSession,
    request: SlotGenerateRequest,
) -> SlotGenerateResult:
    """Generate discrete, conflict-free consultation slots for a doctor across a date range.

    Idempotent: Identifies pre-existing slots and skips overlaps without crashing or creating duplicates.
    """
    # 1. Verify doctor exists
    doctor = await db.scalar(
        select(DoctorProfile).where(DoctorProfile.id == request.doctor_id)
    )
    if not doctor:
        raise EntityNotFoundException("DoctorProfile", request.doctor_id)

    # 2. Query all existing slots for this doctor to identify pre-existing intervals
    existing_slots_stmt = select(DoctorSlot).where(DoctorSlot.doctor_id == request.doctor_id)
    existing_slots_result = await db.scalars(existing_slots_stmt)
    existing_slot_starts: Set[datetime] = {
        _normalize_utc(s.start_time) for s in existing_slots_result.all()
    }

    # 3. Generate candidate slot intervals day by day
    new_slots: List[DoctorSlot] = []
    skipped_count = 0
    current_date: date = request.start_date
    delta_days = (request.end_date - request.start_date).days + 1

    slot_delta = timedelta(minutes=request.slot_duration_minutes)

    for _ in range(delta_days):
        # Daily working bounds
        day_start = datetime.combine(
            current_date,
            time(request.day_start_hour, request.day_start_minute),
            tzinfo=timezone.utc,
        )
        day_end = datetime.combine(
            current_date,
            time(request.day_end_hour, request.day_end_minute),
            tzinfo=timezone.utc,
        )

        # Break bounds (if specified)
        break_start = None
        break_end = None
        if request.break_start_hour is not None and request.break_end_hour is not None:
            break_start = datetime.combine(
                current_date,
                time(request.break_start_hour, request.break_start_minute or 0),
                tzinfo=timezone.utc,
            )
            break_end = datetime.combine(
                current_date,
                time(request.break_end_hour, request.break_end_minute or 0),
                tzinfo=timezone.utc,
            )

        slot_start = day_start
        while slot_start + slot_delta <= day_end:
            slot_end = slot_start + slot_delta

            # Check if this slot overlaps with the break window
            is_break_overlap = False
            if break_start and break_end:
                if slot_start < break_end and slot_end > break_start:
                    is_break_overlap = True

            if not is_break_overlap:
                normalized_start = _normalize_utc(slot_start)
                if normalized_start in existing_slot_starts:
                    skipped_count += 1
                else:
                    slot_entity = DoctorSlot(
                        doctor_id=request.doctor_id,
                        start_time=normalized_start,
                        end_time=_normalize_utc(slot_end),
                        status=SlotStatus.AVAILABLE,
                        is_teleconsult=request.is_teleconsult,
                    )
                    new_slots.append(slot_entity)
                    existing_slot_starts.add(normalized_start)

            slot_start += slot_delta

        current_date += timedelta(days=1)

    # 4. Batch persist newly computed slots
    if new_slots:
        db.add_all(new_slots)
        await db.commit()
        for slot in new_slots:
            await db.refresh(slot)

    # 5. Format response
    response_slots = [DoctorSlotResponse.model_validate(s) for s in new_slots]
    return SlotGenerateResult(
        total_generated=len(new_slots),
        total_skipped_existing=skipped_count,
        slots=response_slots,
    )


async def sweep_expired_holds(
    db: AsyncSession,
    slot_id: Optional[str] = None,
) -> int:
    """Identify slots currently in HELD status whose held_until timestamp has passed,

    and atomically revert them back to AVAILABLE status.
    """
    now_utc = datetime.now(timezone.utc)
    conditions = [
        DoctorSlot.status == SlotStatus.HELD,
        DoctorSlot.held_until.is_not(None),
        DoctorSlot.held_until < now_utc,
    ]
    if slot_id:
        conditions.append(DoctorSlot.id == slot_id)

    stmt = select(DoctorSlot).where(and_(*conditions))
    expired_slots = list((await db.scalars(stmt)).all())

    swept_count = 0
    for slot in expired_slots:
        slot.status = SlotStatus.AVAILABLE
        slot.held_until = None
        slot.held_by_patient_id = None
        swept_count += 1

    if swept_count > 0:
        await db.commit()

    return swept_count


async def get_doctor_slots(
    db: AsyncSession,
    doctor_id: str,
    target_date: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[SlotStatus] = None,
    is_teleconsult: Optional[bool] = None,
) -> List[DoctorSlot]:
    """Query doctor consultation availability slots with optional temporal and status filtering."""
    # Automatically sweep any expired holds so returned availability is real-time accurate
    await sweep_expired_holds(db)

    stmt = (
        select(DoctorSlot)
        .where(DoctorSlot.doctor_id == doctor_id)
        .order_by(DoctorSlot.start_time.asc())
    )

    all_slots = list((await db.scalars(stmt)).all())

    filtered: List[DoctorSlot] = []
    for s in all_slots:
        st_utc = _normalize_utc(s.start_time)
        slot_date = st_utc.date()

        if target_date and slot_date != target_date:
            continue
        if start_date and slot_date < start_date:
            continue
        if end_date and slot_date > end_date:
            continue
        if status and s.status != status:
            continue
        if is_teleconsult is not None and s.is_teleconsult != is_teleconsult:
            continue
        filtered.append(s)

    return filtered


async def get_slot_by_id(
    db: AsyncSession,
    slot_id: str,
) -> Optional[DoctorSlot]:
    """Retrieve a single DoctorSlot by its primary key."""
    stmt = select(DoctorSlot).where(DoctorSlot.id == slot_id)
    return await db.scalar(stmt)


async def hold_slot(
    db: AsyncSession,
    slot_id: str,
    patient_id: str,
    duration_minutes: int = 10,
) -> DoctorSlot:
    """Reserve/hold a consultation slot with row-level locking.

    Raises ConflictException if slot is already booked, blocked, or held by another patient.
    """
    # 1. Sweep expired holds on this slot
    await sweep_expired_holds(db, slot_id=slot_id)

    # 2. Acquire exclusive row-level lock (FOR UPDATE)
    stmt = (
        select(DoctorSlot)
        .where(DoctorSlot.id == slot_id)
        .with_for_update()
    )
    slot = await db.scalar(stmt)
    if not slot:
        raise EntityNotFoundException("DoctorSlot", slot_id)

    # 3. Check current status
    now_utc = datetime.now(timezone.utc)
    if slot.status == SlotStatus.BOOKED:
        raise ConflictException(
            message=f"Slot '{slot_id}' is already booked",
            error_code="SLOT_ALREADY_BOOKED",
        )
    if slot.status == SlotStatus.BLOCKED:
        raise ConflictException(
            message=f"Slot '{slot_id}' is blocked by practitioner",
            error_code="SLOT_BLOCKED",
        )
    if slot.status == SlotStatus.HELD:
        # Check if held by another patient and not expired
        if slot.held_by_patient_id != patient_id and slot.held_until and slot.held_until > now_utc:
            raise ConflictException(
                message=f"Slot '{slot_id}' is currently held by another patient",
                error_code="SLOT_HELD_BY_ANOTHER_PATIENT",
            )

    # 4. Set hold
    expiration = now_utc + timedelta(minutes=duration_minutes)
    slot.status = SlotStatus.HELD
    slot.held_until = expiration
    slot.held_by_patient_id = patient_id

    await db.commit()
    await db.refresh(slot)
    return slot


async def release_slot_hold(
    db: AsyncSession,
    slot_id: str,
    patient_id: Optional[str] = None,
    force_admin: bool = False,
) -> DoctorSlot:
    """Release a held slot back to AVAILABLE status with row-level locking."""
    stmt = (
        select(DoctorSlot)
        .where(DoctorSlot.id == slot_id)
        .with_for_update()
    )
    slot = await db.scalar(stmt)
    if not slot:
        raise EntityNotFoundException("DoctorSlot", slot_id)

    if slot.status != SlotStatus.HELD:
        # Already released or booked
        return slot

    # If patient_id given and not force_admin, check ownership
    if not force_admin and patient_id and slot.held_by_patient_id != patient_id:
        raise PermissionDeniedException(
            message="You are not authorized to release a hold placed by another patient"
        )

    slot.status = SlotStatus.AVAILABLE
    slot.held_until = None
    slot.held_by_patient_id = None

    await db.commit()
    await db.refresh(slot)
    return slot

