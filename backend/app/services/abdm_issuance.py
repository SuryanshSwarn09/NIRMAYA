"""Service layer for ABDM Milestone 1 ABHA Number Issuance, PHR Handle & HPR Onboarding."""

import re
import secrets
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, EntityNotFoundException
from app.models.doctor import DoctorProfile
from app.models.patient import PatientProfile
from app.schemas.abdm_m1_issuance import (
    AbhaNumberCreateResponse,
    HprOnboardResponse,
    PhrAvailabilityResponse,
    PhrLinkResponse,
)
from app.services.aadhaar_otp import generate_verhoeff, validate_verhoeff
from app.services.doctor import get_doctor_by_id
from app.services.patient import get_patient_by_id

RESERVED_HANDLES = {
    "admin",
    "root",
    "system",
    "nha",
    "abdm",
    "gov",
    "official",
    "support",
    "help",
    "security",
    "hospital",
    "clinic",
    "doctor",
    "patient",
}


def _generate_raw_14_digit_abha() -> str:
    """Generate a 14-digit ABHA number string with Verhoeff check digit.

    Format: 91-XXXX-XXXX-XXXX
    - Prefix: 91 (2 digits)
    - Body: 11 random decimal digits
    - Suffix: 1 Verhoeff check digit
    """
    prefix = "91"
    body_digits = f"{secrets.randbelow(10**11):011d}"
    base_13 = prefix + body_digits
    check_digit = generate_verhoeff(base_13)
    full_14 = base_13 + check_digit

    # Format as 91-XXXX-XXXX-XXXX
    return f"{full_14[:2]}-{full_14[2:6]}-{full_14[6:10]}-{full_14[10:14]}"


async def generate_14_digit_abha(
    db: AsyncSession,
    patient_id: str,
) -> AbhaNumberCreateResponse:
    """Generate and bind an official 14-digit ABHA Number to a patient profile.

    Args:
        db: Active async database session
        patient_id: UUID of target PatientProfile

    Returns:
        AbhaNumberCreateResponse with generated ABHA number
    """
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        raise EntityNotFoundException("PatientProfile", patient_id)

    # If patient already has an assigned ABHA number, return it idempotently
    if patient.abha_number:
        return AbhaNumberCreateResponse(
            patient_id=str(patient.id),
            abha_number=patient.abha_number,
            status="active",
            message="Existing 14-digit ABHA number retrieved successfully",
        )

    # Generate unique 14-digit ABHA number
    max_retries = 10
    formatted_abha = None
    for _ in range(max_retries):
        candidate = _generate_raw_14_digit_abha()
        existing = await db.scalar(
            select(PatientProfile).where(PatientProfile.abha_number == candidate)
        )
        if not existing:
            formatted_abha = candidate
            break

    if not formatted_abha:
        raise AppException("Failed to generate unique 14-digit ABHA number. Please retry.")

    patient.abha_number = formatted_abha
    await db.commit()
    await db.refresh(patient)

    return AbhaNumberCreateResponse(
        patient_id=str(patient.id),
        abha_number=formatted_abha,
        status="active",
        message="Official 14-digit ABHA number successfully generated and linked to patient profile",
    )


async def check_phr_availability(
    db: AsyncSession,
    handle: str,
) -> PhrAvailabilityResponse:
    """Check whether a requested ABHA PHR address handle is available.

    Args:
        db: Active async database session
        handle: Requested handle name (with or without @abdm suffix)

    Returns:
        PhrAvailabilityResponse with availability status and collision suggestions
    """
    clean_handle = handle.strip().lower()
    if "@" in clean_handle:
        clean_handle = clean_handle.split("@")[0]

    full_address = f"{clean_handle}@abdm"

    # Validation: syntax and length
    if not re.match(r"^[a-z0-9._]{3,32}$", clean_handle):
        return PhrAvailabilityResponse(
            handle=clean_handle,
            full_address=full_address,
            is_available=False,
            suggestions=[
                f"{clean_handle[:20]}12@abdm",
                f"{clean_handle[:20]}.in@abdm",
            ],
        )

    # Check reserved keywords
    if clean_handle in RESERVED_HANDLES:
        return PhrAvailabilityResponse(
            handle=clean_handle,
            full_address=full_address,
            is_available=False,
            suggestions=[
                f"my.{clean_handle}@abdm",
                f"{clean_handle}.health@abdm",
                f"{clean_handle}26@abdm",
            ],
        )

    # Check database uniqueness
    existing = await db.scalar(
        select(PatientProfile).where(PatientProfile.abha_address == full_address)
    )

    if existing:
        suggestions = [
            f"{clean_handle}12@abdm",
            f"{clean_handle}.in@abdm",
            f"{clean_handle}26@abdm",
        ]
        return PhrAvailabilityResponse(
            handle=clean_handle,
            full_address=full_address,
            is_available=False,
            suggestions=suggestions,
        )

    return PhrAvailabilityResponse(
        handle=clean_handle,
        full_address=full_address,
        is_available=True,
        suggestions=[],
    )


async def link_phr_address(
    db: AsyncSession,
    patient_id: str,
    abha_address: str,
) -> PhrLinkResponse:
    """Reserve and link an official @abdm PHR handle to a patient profile.

    Args:
        db: Active async database session
        patient_id: UUID of target PatientProfile
        abha_address: Desired PHR address handle

    Returns:
        PhrLinkResponse confirming linked address
    """
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        raise EntityNotFoundException("PatientProfile", patient_id)

    clean_address = abha_address.strip().lower()
    if not clean_address.endswith("@abdm"):
        clean_address = f"{clean_address}@abdm"

    handle_part = clean_address.split("@")[0]
    if not re.match(r"^[a-z0-9._]{3,32}$", handle_part):
        raise AppException(
            "Invalid ABHA address format. Must be 3-32 characters containing letters, numbers, dots, or underscores."
        )

    if handle_part in RESERVED_HANDLES:
        raise AppException(f"The handle '{handle_part}' is a reserved ABDM national keyword.")

    # Check if another patient already owns this exact address
    existing = await db.scalar(
        select(PatientProfile).where(
            PatientProfile.abha_address == clean_address,
            PatientProfile.id != patient.id,
        )
    )
    if existing:
        raise AppException(f"ABHA PHR address '{clean_address}' is already registered by another citizen")

    patient.abha_address = clean_address
    await db.commit()
    await db.refresh(patient)

    return PhrLinkResponse(
        patient_id=str(patient.id),
        abha_number=patient.abha_number,
        abha_address=clean_address,
        status="active",
        message="ABHA PHR address successfully reserved and linked to patient profile",
    )


async def onboard_doctor_hpr(
    db: AsyncSession,
    doctor_id: str,
    registration_number: str,
    medical_council: str,
    hpr_handle: str,
) -> HprOnboardResponse:
    """Onboard an accredited clinician to the ABDM Healthcare Professional Registry.

    Args:
        db: Active async database session
        doctor_id: UUID of target DoctorProfile
        registration_number: State Council or NMC registration number
        medical_council: Medical Council authority name
        hpr_handle: Desired HPR handle (e.g. ananya.sharma@hpr.abdm)

    Returns:
        HprOnboardResponse confirming HPR credential issuance
    """
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise EntityNotFoundException("DoctorProfile", doctor_id)

    clean_hpr = hpr_handle.strip().lower()
    if not clean_hpr.endswith("@hpr.abdm"):
        clean_hpr = f"{clean_hpr}@hpr.abdm"

    handle_part = clean_hpr.split("@")[0]
    if not re.match(r"^[a-z0-9._]{3,32}$", handle_part):
        raise AppException(
            "Invalid HPR handle format. Must be 3-32 characters containing lowercase letters, numbers, dots, or underscores."
        )

    # Check collision across other doctors
    existing = await db.scalar(
        select(DoctorProfile).where(
            DoctorProfile.hpr_id == clean_hpr,
            DoctorProfile.id != doctor.id,
        )
    )
    if existing:
        raise AppException(f"HPR ID '{clean_hpr}' is already assigned to another accredited healthcare professional")

    # Update doctor credentials
    doctor.hpr_id = clean_hpr
    if registration_number:
        doctor.registration_number = registration_number
    if medical_council:
        doctor.medical_council = medical_council

    await db.commit()
    await db.refresh(doctor)

    return HprOnboardResponse(
        doctor_id=str(doctor.id),
        hpr_id=clean_hpr,
        registration_number=doctor.registration_number,
        medical_council=doctor.medical_council,
        status="verified",
        verified_at=datetime.now(timezone.utc),
        message="Clinician successfully onboarded to National Healthcare Professional Registry (HPR)",
    )
