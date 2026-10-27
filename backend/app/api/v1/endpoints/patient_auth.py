"""Endpoints for Unified DigiLocker & Aadhaar OTP Passwordless Patient Gateway."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import APIResponse
from app.schemas.patient_auth import (
    PatientMobileFallbackLoginRequest,
    PatientUnifiedAuthRequest,
    PatientUnifiedAuthResponse,
)
from app.services.patient_auth import (
    authenticate_mobile_fallback,
    authenticate_or_register_patient,
)

router = APIRouter(prefix="/auth/patient", tags=["Passwordless Patient Authentication"])


@router.post(
    "/login-or-register",
    response_model=APIResponse[PatientUnifiedAuthResponse],
    status_code=status.HTTP_200_OK,
    summary="One-tap passwordless login or registration for patients",
    description="Authenticates existing patient or auto-registers a new patient using verified DigiLocker e-Aadhaar or direct Aadhaar OTP claims. Auto-mints 14-digit ABHA on first registration and issues 30-day session token.",
)
async def patient_unified_login_or_register(
    payload: PatientUnifiedAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientUnifiedAuthResponse]:
    """Authenticate or register patient via verified digital identity."""
    auth_result = await authenticate_or_register_patient(db, payload)
    return APIResponse(
        success=True,
        data=auth_result,
        message=auth_result.message,
    )


@router.post(
    "/mobile-fallback-login",
    response_model=APIResponse[PatientUnifiedAuthResponse],
    status_code=status.HTTP_200_OK,
    summary="Mobile OTP fallback authentication for patients with mismatched SIM cards",
    description="Authenticates patient using current active mobile OTP and optional ABHA handle when Aadhaar-linked mobile is inaccessible.",
)
async def patient_mobile_fallback_login(
    payload: PatientMobileFallbackLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientUnifiedAuthResponse]:
    """Authenticate patient via active mobile fallback."""
    auth_result = await authenticate_mobile_fallback(db, payload)
    return APIResponse(
        success=True,
        data=auth_result,
        message=auth_result.message,
    )
