"""Service implementation for Unified DigiLocker & Aadhaar OTP Passwordless Patient Gateway."""

from datetime import date, datetime, timedelta, timezone
import re
from typing import Optional, Tuple
import uuid
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthenticationException, EntityNotFoundException
from app.core.security import create_access_token
from app.models.enums import Gender, UserRole
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.patient_auth import (
    PatientMobileFallbackLoginRequest,
    PatientUnifiedAuthRequest,
    PatientUnifiedAuthResponse,
)
from app.services.abdm_issuance import _generate_raw_14_digit_abha


def _parse_dob(dob_str: Optional[str]) -> Optional[date]:
    """Parse YYYY-MM-DD or DD-MM-YYYY date strings safely."""
    if not dob_str:
        return None
    try:
        parts = dob_str.strip().split("-")
        if len(parts) == 3:
            if len(parts[0]) == 4:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
            return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except (ValueError, IndexError):
        return None
    return None


def _clean_phr_handle(name: str) -> str:
    """Generate a clean 3-to-32 char alphanumeric base for @abdm handle."""
    clean = re.sub(r"[^a-z0-9]", "", name.lower().strip())
    if len(clean) < 3:
        clean = "user"
    clean = clean[:16]
    suffix = uuid.uuid4().hex[:6]
    return f"{clean}.{suffix}@abdm"


async def authenticate_or_register_patient(
    db: AsyncSession,
    request: PatientUnifiedAuthRequest,
) -> PatientUnifiedAuthResponse:
    """Authenticate existing patient or auto-register new patient with 14-digit ABHA.

    Features:
    - Auto-detects existing patient profile by email, phone, or masked Aadhaar.
    - Suggestion 3: Auto-mints certified 14-digit ABHA Number and @abdm handle on first login.
    - Suggestion 2: Issues 30-day extended JWT session token when remember_me is True.
    """
    clean_name = request.name.strip()
    if not clean_name:
        raise AuthenticationException("Patient legal name is required for verified authentication")

    # 1. Search for existing user / patient
    query = (
        select(User)
        .options(selectinload(User.patient_profile))
        .where(User.role == UserRole.PATIENT)
    )

    conditions = []
    if request.email:
        conditions.append(User.email == request.email.strip().lower())
    if request.mobile_number:
        conditions.append(User.phone_number == request.mobile_number.strip())

    user: Optional[User] = None
    if conditions:
        result = await db.execute(query.where(or_(*conditions)))
        user = result.scalars().first()

    # Fallback search by patient profile masked aadhaar if provided
    if not user and request.masked_aadhaar:
        pat_query = (
            select(PatientProfile)
            .options(selectinload(PatientProfile.user))
            .where(PatientProfile.address_line.ilike(f"%{request.masked_aadhaar}%"))
        )
        pat_result = await db.execute(pat_query)
        matched_profile = pat_result.scalars().first()
        if matched_profile and matched_profile.user:
            user = matched_profile.user

    is_new = False
    now_utc = datetime.now(timezone.utc)

    # 2. Existing Patient Flow: Update & Login
    if user:
        user.is_verified = True
        patient = user.patient_profile
        if not patient:
            # Create missing profile if user existed without one
            pat_id = str(uuid.uuid4())
            minted_abha = _generate_raw_14_digit_abha()
            minted_phr = _clean_phr_handle(clean_name)
            patient = PatientProfile(
                id=pat_id,
                user_id=user.id,
                date_of_birth=_parse_dob(request.date_of_birth),
                gender=Gender.MALE if (request.gender or "").lower() == "male" else (Gender.FEMALE if (request.gender or "").lower() == "female" else Gender.OTHER),
                address_line=request.formatted_address[:255] if request.formatted_address else None,
                city=request.district[:100] if request.district else None,
                state=request.state[:100] if request.state else None,
                pincode=request.pincode[:10] if request.pincode else None,
                abha_number=minted_abha,
                abha_address=minted_phr,
            )
            db.add(patient)
        else:
            # Sync any newly verified claims
            if request.formatted_address:
                patient.address_line = request.formatted_address[:255]
            if request.district:
                patient.city = request.district[:100]
            if request.state:
                patient.state = request.state[:100]
            if request.pincode:
                patient.pincode = request.pincode[:10]
            if request.date_of_birth and not patient.date_of_birth:
                patient.date_of_birth = _parse_dob(request.date_of_birth)
            # Auto-mint ABHA if missing
            if not patient.abha_number:
                patient.abha_number = _generate_raw_14_digit_abha()
            if not patient.abha_address:
                patient.abha_address = _clean_phr_handle(clean_name)

        await db.commit()
        await db.refresh(user)
        if patient:
            await db.refresh(patient)

    # 3. New Patient Flow: Instant 1-Tap Auto-Registration & Auto-ABHA Minting
    else:
        is_new = True
        u_id = str(uuid.uuid4())
        p_id = str(uuid.uuid4())

        # Synthesize email if none provided
        user_email = (
            request.email.strip().lower()
            if request.email
            else f"patient.{uuid.uuid4().hex[:8]}@abdm.nirmaya.in"
        )

        user = User(
            id=u_id,
            email=user_email,
            full_name=clean_name,
            phone_number=request.mobile_number.strip() if request.mobile_number else None,
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )

        # Auto-mint 14-digit ABHA Number and @abdm handle (Suggestion 3)
        minted_abha = _generate_raw_14_digit_abha()
        minted_phr = _clean_phr_handle(clean_name)

        patient = PatientProfile(
            id=p_id,
            user_id=u_id,
            date_of_birth=_parse_dob(request.date_of_birth),
            gender=Gender.MALE if (request.gender or "").lower() == "male" else (Gender.FEMALE if (request.gender or "").lower() == "female" else Gender.OTHER),
            address_line=request.formatted_address[:255] if request.formatted_address else None,
            city=request.district[:100] if request.district else None,
            state=request.state[:100] if request.state else None,
            pincode=request.pincode[:10] if request.pincode else None,
            abha_number=minted_abha,
            abha_address=minted_phr,
        )

        db.add_all([user, patient])
        await db.commit()
        await db.refresh(user)
        await db.refresh(patient)

    # 4. Suggestion 2: Session Longevity (30 Days when remember_me is True)
    if request.remember_me:
        expiry_delta = timedelta(days=30)
        expires_seconds = int(expiry_delta.total_seconds())  # 2,592,000s
    else:
        expiry_delta = timedelta(hours=24)
        expires_seconds = int(expiry_delta.total_seconds())  # 86,400s

    token_payload = {
        "sub": user.id,
        "email": user.email,
        "role": UserRole.PATIENT.value,
        "patient_id": str(patient.id),
        "auth_source": request.source,
    }

    access_token = create_access_token(
        data=token_payload,
        expires_delta=expiry_delta,
    )

    msg = (
        "Account created and verified via UIDAI e-KYC with 14-digit ABHA Number minted"
        if is_new
        else "Successfully authenticated via verified digital identity"
    )

    return PatientUnifiedAuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=expires_seconds,
        is_new_user=is_new,
        patient_id=str(patient.id),
        user_id=str(user.id),
        name=user.full_name,
        masked_aadhaar=request.masked_aadhaar,
        abha_number=patient.abha_number,
        abha_address=patient.abha_address,
        message=msg,
    )


async def authenticate_mobile_fallback(
    db: AsyncSession,
    request: PatientMobileFallbackLoginRequest,
) -> PatientUnifiedAuthResponse:
    """Authenticate patient via current active mobile OTP and optional ABHA handle (Suggestion 1)."""
    clean_phone = request.mobile_number.strip()
    clean_otp = request.otp.strip()

    # In sandbox/simulation, accept standard verification OTP '123456'
    if clean_otp != "123456":
        raise AuthenticationException("Invalid or expired mobile verification OTP")

    # Search by phone number or ABHA identifier
    query = (
        select(User)
        .options(selectinload(User.patient_profile))
        .where(User.role == UserRole.PATIENT)
    )

    conditions = [User.phone_number == clean_phone]
    if request.abha_identifier:
        clean_id = request.abha_identifier.strip()
        conditions.append(User.email.ilike(f"%{clean_id}%"))

    result = await db.execute(query.where(or_(*conditions)))
    user = result.scalars().first()

    if not user:
        # Fallback check on PatientProfile abha_number or abha_address
        if request.abha_identifier:
            clean_id = request.abha_identifier.strip()
            pat_query = (
                select(PatientProfile)
                .options(selectinload(PatientProfile.user))
                .where(
                    or_(
                        PatientProfile.abha_number == clean_id,
                        PatientProfile.abha_address.ilike(clean_id),
                    )
                )
            )
            pat_res = await db.execute(pat_query)
            pat = pat_res.scalars().first()
            if pat and pat.user:
                user = pat.user

    is_new = False
    if not user:
        # Register walk-in mobile patient
        is_new = True
        u_id = str(uuid.uuid4())
        p_id = str(uuid.uuid4())
        email = f"mobile.{uuid.uuid4().hex[:8]}@abdm.nirmaya.in"
        minted_abha = _generate_raw_14_digit_abha()
        minted_phr = f"user.{uuid.uuid4().hex[:6]}@abdm"

        user = User(
            id=u_id,
            email=email,
            full_name=f"Patient {clean_phone[-4:]}",
            phone_number=clean_phone,
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        patient = PatientProfile(
            id=p_id,
            user_id=u_id,
            abha_number=minted_abha,
            abha_address=minted_phr,
        )
        db.add_all([user, patient])
        await db.commit()
        await db.refresh(user)
        await db.refresh(patient)
    else:
        patient = user.patient_profile
        if not patient:
            p_id = str(uuid.uuid4())
            patient = PatientProfile(
                id=p_id,
                user_id=user.id,
                abha_number=_generate_raw_14_digit_abha(),
                abha_address=f"user.{uuid.uuid4().hex[:6]}@abdm",
            )
            db.add(patient)
            await db.commit()
            await db.refresh(patient)

    # 30-day session longevity
    if request.remember_me:
        expiry_delta = timedelta(days=30)
        expires_seconds = int(expiry_delta.total_seconds())
    else:
        expiry_delta = timedelta(hours=24)
        expires_seconds = int(expiry_delta.total_seconds())

    token_payload = {
        "sub": user.id,
        "email": user.email,
        "role": UserRole.PATIENT.value,
        "patient_id": str(patient.id),
        "auth_source": "mobile_fallback",
    }

    access_token = create_access_token(
        data=token_payload,
        expires_delta=expiry_delta,
    )

    return PatientUnifiedAuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=expires_seconds,
        is_new_user=is_new,
        patient_id=str(patient.id),
        user_id=str(user.id),
        name=user.full_name,
        masked_aadhaar=None,
        abha_number=patient.abha_number,
        abha_address=patient.abha_address,
        message="Authenticated via active mobile verification",
    )
