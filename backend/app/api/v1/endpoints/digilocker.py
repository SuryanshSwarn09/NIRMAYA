"""DigiLocker OAuth 2.0 PKCE & e-Aadhaar verification API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.digilocker import (
    DigiLockerAuthorizeUrlResponse,
    DigiLockerCallbackRequest,
    DigiLockerVerificationResult,
    DigiLockerSyncPatientResponse,
)
from app.services.digilocker import (
    generate_authorization_url,
    verify_digilocker_callback,
    sync_patient_profile,
)

router = APIRouter(prefix="/auth/digilocker", tags=["DigiLocker Identity & e-Aadhaar"])


@router.get(
    "/authorize-url",
    response_model=APIResponse[DigiLockerAuthorizeUrlResponse],
    summary="Generate DigiLocker PKCE authorization redirect URL",
    description="Constructs the Government of India DigiLocker OAuth 2.0 authorization redirect URL with RFC 7636 S256 PKCE challenge and CSRF state token.",
)
async def get_authorize_url(
    state: Optional[str] = Query(default=None, description="Optional caller CSRF state parameter"),
) -> APIResponse[DigiLockerAuthorizeUrlResponse]:
    """Build and return DigiLocker authorization URL with PKCE security parameters."""
    response_data, _ = generate_authorization_url(state=state)
    return APIResponse(
        success=True,
        data=response_data,
        message="DigiLocker PKCE authorization URL generated successfully",
    )


@router.post(
    "/verify",
    response_model=APIResponse[DigiLockerVerificationResult],
    summary="Verify DigiLocker authorization code and extract e-Aadhaar claims",
    description="Exchanges the DigiLocker authorization code and PKCE code_verifier for a bearer token, retrieves the UIDAI e-Aadhaar XML certificate, and cryptographically extracts demographic claims.",
)
async def verify_digilocker_code(
    payload: DigiLockerCallbackRequest,
) -> APIResponse[DigiLockerVerificationResult]:
    """Exchange DigiLocker code, verify UIDAI e-Aadhaar XML, and extract certified identity claims."""
    result = await verify_digilocker_callback(
        code=payload.code,
        state=payload.state,
        code_verifier=payload.code_verifier,
    )
    return APIResponse(
        success=True,
        data=result,
        message="e-Aadhaar identity claims cryptographically verified via DigiLocker",
    )


@router.post(
    "/sync-patient/{patient_id}",
    response_model=APIResponse[DigiLockerSyncPatientResponse],
    summary="Synchronize verified e-Aadhaar demographic claims to PatientProfile",
    description="Updates the patient vault profile with certified UIDAI e-Aadhaar name, gender, DOB, address, and masked Aadhaar identifier.",
)
async def sync_patient_identity(
    patient_id: str,
    payload: DigiLockerVerificationResult,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[DigiLockerSyncPatientResponse]:
    """Synchronize verified e-Aadhaar demographic claims into the patient profile."""
    sync_result = await sync_patient_profile(
        db=db,
        patient_id=patient_id,
        demographics=payload.demographics,
        digilocker_id=payload.digilocker_id,
    )
    return APIResponse(
        success=True,
        data=sync_result,
        message="Patient profile successfully synchronized with verified e-Aadhaar claims",
    )
