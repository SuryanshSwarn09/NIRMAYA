"""Conflict-free doctor consultation slot generation engine for NIRMAYA platform.

Computes discrete, non-overlapping availability windows adhering to clinical practice hours,
break intervals, and ensures idempotent slot generation.
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional, Set
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import EntityNotFoundException
from app.models.appointment import DoctorSlot
from app.models.doctor import DoctorProfile
from app.models.enums import SlotStatus
from app.schemas.appointment import (
    DoctorSlotResponse,
    SlotGenerateRequest,
    SlotGenerateResult,
)


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

    # 2. Query all existing slots in the date range to avoid unique constraint violations
    range_start_dt = datetime.combine(
        request.start_date,
        time(0, 0, 0),
        tzinfo=timezone.utc,
    )
    range_end_dt = datetime.combine(
        request.end_date,
        time(23, 59, 59),
        tzinfo=timezone.utc,
    )

    existing_slots_stmt = select(DoctorSlot).where(
        and_(
            DoctorSlot.doctor_id == request.doctor_id,
            DoctorSlot.start_time >= range_start_dt,
            DoctorSlot.start_time <= range_end_dt,
        )
    )
    existing_slots_result = await db.scalars(existing_slots_stmt)
    existing_slot_starts: Set[datetime] = {
        s.start_time for s in existing_slots_result.all()
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
                # Overlaps if slot_start < break_end and slot_end > break_start
                if slot_start < break_end and slot_end > break_start:
                    is_break_overlap = True

            if not is_break_overlap:
                if slot_start in existing_slot_starts:
                    skipped_count += 1
                else:
                    slot_entity = DoctorSlot(
                        doctor_id=request.doctor_id,
                        start_time=slot_start,
                        end_time=slot_end,
                        status=SlotStatus.AVAILABLE,
                        is_teleconsult=request.is_teleconsult,
                    )
                    new_slots.append(slot_entity)
                    existing_slot_starts.add(slot_start)

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
    filters = [DoctorSlot.doctor_id == doctor_id]

    if target_date:
        dt_start = datetime.combine(target_date, time(0, 0, 0), tzinfo=timezone.utc)
        dt_end = datetime.combine(target_date, time(23, 59, 59), tzinfo=timezone.utc)
        filters.append(DoctorSlot.start_time >= dt_start)
        filters.append(DoctorSlot.start_time <= dt_end)
    else:
        if start_date:
            dt_start = datetime.combine(start_date, time(0, 0, 0), tzinfo=timezone.utc)
            filters.append(DoctorSlot.start_time >= dt_start)
        if end_date:
            dt_end = datetime.combine(end_date, time(23, 59, 59), tzinfo=timezone.utc)
            filters.append(DoctorSlot.start_time <= dt_end)

    if status:
        filters.append(DoctorSlot.status == status)

    if is_teleconsult is not None:
        filters.append(DoctorSlot.is_teleconsult == is_teleconsult)

    stmt = select(DoctorSlot).where(and_(*filters)).order_by(DoctorSlot.start_time.asc())
    result = await db.scalars(stmt)
    return list(result.all())


async def get_slot_by_id(
    db: AsyncSession,
    slot_id: str,
) -> Optional[DoctorSlot]:
    """Retrieve a single DoctorSlot by its primary key."""
    stmt = select(DoctorSlot).where(DoctorSlot.id == slot_id)
    return await db.scalar(stmt)
