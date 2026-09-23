"""Doctor EMR business logic service layer for NIRMAYA platform."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.doctor import DoctorProfile


async def get_doctor_by_id(db: AsyncSession, doctor_id: str) -> Optional[DoctorProfile]:
    """Retrieve a single DoctorProfile by UUID primary key with linked user loaded."""
    stmt = (
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.id == doctor_id)
    )
    return await db.scalar(stmt)


async def get_doctor_by_user_id(db: AsyncSession, user_id: str) -> Optional[DoctorProfile]:
    """Retrieve a DoctorProfile associated with a specific User ID."""
    stmt = (
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.user_id == user_id)
    )
    return await db.scalar(stmt)


async def get_doctor_by_registration_number(
    db: AsyncSession,
    registration_number: str,
) -> Optional[DoctorProfile]:
    """Resolve a DoctorProfile by Medical Council registration number."""
    clean_reg = registration_number.strip()
    stmt = (
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.registration_number == clean_reg)
    )
    return await db.scalar(stmt)


async def get_doctor_by_hpr_id(db: AsyncSession, hpr_id: str) -> Optional[DoctorProfile]:
    """Resolve a DoctorProfile by official ABDM Healthcare Professional Registry handle."""
    clean_hpr = hpr_id.strip()
    stmt = (
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.hpr_id == clean_hpr)
    )
    return await db.scalar(stmt)
