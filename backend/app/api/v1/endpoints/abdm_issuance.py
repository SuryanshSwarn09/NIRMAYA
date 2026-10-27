"""ABDM Milestone 1 ABHA Number Issuance, PHR Address Reservation & HPR Onboarding Endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.abdm_m1_issuance import (
    AbhaNumberCreateRequest,
    AbhaNumberCreateResponse,
    HprOnboardRequest,
    HprOnboardResponse,
    PhrAvailabilityResponse,
    PhrLinkRequest,
    PhrLinkResponse,
)
from app.services.abdm_issuance import (
    check_phr_availability,
    generate_14_digit_abha,
    link_phr_address,
    onboard_doctor_hpr,
)

router = APIRouter(prefix="/abdm/m1", tags=["ABDM M1 - ABHA Issuance & HPR Onboarding"])


@router.post(
    "/abha/create",
    response_model=APIResponse[AbhaNumberCreateResponse],
    summary="Issue official 14-digit ABHA Number for verified patient",
    description="Mint a certified 14-digit Ayushman Bharat Health Account number (91-XXXX-XXXX-XXXX) with Verhoeff check-digit and link to PatientProfile.",
)
async def create_abha_number(
    payload: AbhaNumberCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[AbhaNumberCreateResponse]:
    """Issue official 14-digit ABHA number."""
    response_data = await generate_14_digit_abha(db, payload.patient_id)
    return APIResponse(
        success=True,
        data=response_data,
        message=response_data.message,
    )


@router.get(
    "/phr/check-availability",
    response_model=APIResponse[PhrAvailabilityResponse],
    summary="Check availability of @abdm PHR handle",
    description="Validates syntax and queries ABDM registry for address availability, returning alternative suggestions if taken.",
)
async def check_handle_availability(
    handle: str = Query(description="Handle name without @abdm suffix"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PhrAvailabilityResponse]:
    """Check availability of requested PHR handle."""
    response_data = await check_phr_availability(db, handle)
    return APIResponse(
        success=True,
        data=response_data,
        message="PHR address availability evaluated successfully",
    )


@router.post(
    "/phr/link",
    response_model=APIResponse[PhrLinkResponse],
    summary="Reserve and link @abdm PHR handle to patient profile",
    description="Associates the claimed @abdm PHR address handle with the patient profile.",
)
async def link_phr_handle(
    payload: PhrLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[PhrLinkResponse]:
    """Reserve and link @abdm handle to patient."""
    response_data = await link_phr_address(db, payload.patient_id, payload.abha_address)
    return APIResponse(
        success=True,
        data=response_data,
        message=response_data.message,
    )


@router.post(
    "/hpr/onboard",
    response_model=APIResponse[HprOnboardResponse],
    summary="Onboard doctor to ABDM Healthcare Professional Registry",
    description="Validates clinician medical council credentials and issues verified @hpr.abdm identity.",
)
async def onboard_clinician_hpr(
    payload: HprOnboardRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[HprOnboardResponse]:
    """Onboard clinician to national Healthcare Professional Registry."""
    response_data = await onboard_doctor_hpr(
        db=db,
        doctor_id=payload.doctor_id,
        registration_number=payload.registration_number,
        medical_council=payload.medical_council,
        hpr_handle=payload.hpr_handle,
    )
    return APIResponse(
        success=True,
        data=response_data,
        message=response_data.message,
    )
