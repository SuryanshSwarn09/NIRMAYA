from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Response, status

from app.core.container_security import get_container_security_headers
from app.schemas.child_abha import (
    ChildAbhaOtpRequest,
    ChildAbhaOtpResponse,
    ChildAbhaRegistrationRequest,
    ChildAbhaRegistrationResponse,
    DigiLockerDocumentVerificationRequest,
    DigiLockerDocumentVerificationResponse,
    FhirRelatedPersonRepresentation,
)
from app.services.child_abha_service import child_abha_service

router = APIRouter(
    prefix="/patients/proxy/child-abha",
    tags=["ABDM Child-ABHA Linkage & Verified Demographic Proxy Binding"],
)


@router.post(
    "/otp-request",
    summary="Initiate Guardian Aadhaar OTP Challenge for Child-ABHA",
    description="Dispatches simulated Aadhaar OTP to parent/guardian registered mobile for minor child onboarding under DPDP Act Sec 9.",
    response_model=ChildAbhaOtpResponse,
)
async def request_child_abha_otp(
    payload: ChildAbhaOtpRequest,
    response: Response,
) -> ChildAbhaOtpResponse:
    """Request guardian Aadhaar OTP challenge."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    try:
        return child_abha_service.request_guardian_otp_for_child_abha(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/verify-and-create",
    summary="Verify Guardian OTP and Issue Sovereign Child-ABHA",
    description="Validates Aadhaar OTP, enforces age-of-majority constraint, mints 14-digit Child ABHA, and establishes zero-contamination proxy delegation.",
    response_model=ChildAbhaRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def verify_otp_and_issue_child_abha(
    payload: ChildAbhaRegistrationRequest,
    response: Response,
) -> ChildAbhaRegistrationResponse:
    """Verify OTP, mint Child ABHA, and bind zero-contamination proxy delegation."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    try:
        return child_abha_service.verify_and_issue_child_abha(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/digilocker/verify",
    summary="Verify Birth Certificate via DigiLocker Adapter",
    description="Validates municipal birth certificate provenance and returns SHA-256 cryptographic document fingerprint.",
    response_model=DigiLockerDocumentVerificationResponse,
)
async def verify_digilocker_document(
    payload: DigiLockerDocumentVerificationRequest,
    response: Response,
) -> DigiLockerDocumentVerificationResponse:
    """Verify birth certificate via DigiLocker API adapter."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    try:
        return child_abha_service.verify_digilocker_certificate(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{relationship_id}/fhir-related-person",
    summary="Export HL7 FHIR R4 RelatedPerson Resource",
    description="Transforms internal proxy delegation into NRCeS compliant HL7 FHIR R4 RelatedPerson representation.",
    response_model=FhirRelatedPersonRepresentation,
)
async def export_fhir_related_person(
    relationship_id: str,
    response: Response,
) -> FhirRelatedPersonRepresentation:
    """Export proxy relationship as HL7 FHIR R4 RelatedPerson."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    try:
        return child_abha_service.serialize_to_fhir_related_person(relationship_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
