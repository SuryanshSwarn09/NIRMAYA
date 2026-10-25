"""ABDM Milestone 1 Direct Aadhaar Demographic OTP Verification API Endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.abdm_m1 import (
    AadhaarOtpGenerateRequest,
    AadhaarOtpGenerateResponse,
    AadhaarOtpVerifyRequest,
    AadhaarOtpVerifyResponse,
    UnifiedIdentitySyncResponse,
)
from app.services.aadhaar_otp import (
    generate_aadhaar_otp,
    verify_aadhaar_otp,
    sync_unified_patient_profile,
)

router = APIRouter(prefix="/abdm/m1/aadhaar", tags=["ABDM M1 - Aadhaar Demographic OTP Verification"])


@router.post(
    "/generate-otp",
    response_model=APIResponse[AadhaarOtpGenerateResponse],
    summary="Dispatch Aadhaar demographic authentication OTP",
    description="Validates 12-digit Aadhaar number, performs RSA-OAEP public key demographic encryption on the fly, and dispatches a 6-digit OTP to the registered mobile number.",
)
async def request_aadhaar_otp(
    payload: AadhaarOtpGenerateRequest,
) -> APIResponse[AadhaarOtpGenerateResponse]:
    """Initiate Aadhaar OTP verification transaction session."""
    response_data = generate_aadhaar_otp(payload.aadhaar_number)
    return APIResponse(
        success=True,
        data=response_data,
        message=response_data.message,
    )


@router.post(
    "/verify-otp",
    response_model=APIResponse[AadhaarOtpVerifyResponse],
    summary="Verify Aadhaar OTP and extract certified demographic claims",
    description="Verifies the submitted 6-digit OTP against an active transaction session, returning authenticated UIDAI e-KYC demographic claims.",
)
async def submit_aadhaar_otp(
    payload: AadhaarOtpVerifyRequest,
) -> APIResponse[AadhaarOtpVerifyResponse]:
    """Verify Aadhaar OTP and extract certified demographic claims."""
    verify_data = verify_aadhaar_otp(payload.txn_id, payload.otp)
    return APIResponse(
        success=True,
        data=verify_data,
        message="Aadhaar demographic identity successfully verified via UIDAI e-KYC",
    )


@router.post(
    "/sync-patient/{patient_id}",
    response_model=APIResponse[UnifiedIdentitySyncResponse],
    summary="Synchronize verified Aadhaar demographic claims to PatientProfile",
    description="Atomically updates the patient vault profile with certified UIDAI Aadhaar legal name, gender, DOB, address, and masked Aadhaar identifier.",
)
async def sync_aadhaar_identity(
    patient_id: str,
    payload: AadhaarOtpVerifyResponse,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[UnifiedIdentitySyncResponse]:
    """Synchronize verified Aadhaar e-KYC demographic claims into PatientProfile."""
    sync_result = await sync_unified_patient_profile(
        db=db,
        patient_id=patient_id,
        demographics=payload.demographics,
        source="aadhaar_otp",
    )
    return APIResponse(
        success=True,
        data=sync_result,
        message=sync_result.message,
    )
