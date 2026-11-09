"""FastAPI endpoints for Universal High-Density National Health Gateway.

Exposes:
- /api/v1/gateway/auth/aadhaar/challenge
- /api/v1/gateway/auth/aadhaar/verify
- /api/v1/gateway/auth/digilocker/verify
- /api/v1/gateway/auth/mobile/verify
- /api/v1/gateway/auth/emergency/bypass
- /api/v1/gateway/sessions
- /api/v1/gateway/sessions/revoke
- /api/v1/gateway/sessions/revoke-all
- /api/v1/gateway/shield/metrics
- /api/v1/gateway/emergency/audit
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.schemas.common import APIResponse
from app.schemas.national_gateway import (
    AadhaarOtpChallengeRequest,
    AadhaarOtpChallengeResponse,
    AadhaarOtpVerifyRequest,
    AbhaMobileLoginRequest,
    DigiLockerKycAuthRequest,
    EmergencyBypassAuthRequest,
    GatewayDeviceSession,
    GatewaySessionResponse,
    RateShieldMetrics,
    SessionRevokeRequest,
)
from app.services.national_gateway_service import national_gateway_service

router = APIRouter(prefix="/gateway", tags=["Universal High-Density National Health Gateway"])


def get_client_ip(request: Request) -> str:
    """Helper to extract reliable client IP."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def get_user_agent(request: Request) -> str:
    """Helper to extract user agent header."""
    return request.headers.get("User-Agent", "NIRMAYA-Client/1.0")


@router.post(
    "/auth/aadhaar/challenge",
    response_model=APIResponse[AadhaarOtpChallengeResponse],
    status_code=status.HTTP_200_OK,
    summary="Initiate Aadhaar demographic OTP challenge",
)
async def initiate_aadhaar_challenge(
    payload: AadhaarOtpChallengeRequest,
    request: Request,
) -> APIResponse[AadhaarOtpChallengeResponse]:
    """Initiates 6-digit demographic OTP challenge to Aadhaar-registered mobile."""
    client_ip = get_client_ip(request)
    try:
        challenge_resp = national_gateway_service.initiate_aadhaar_challenge(payload, client_ip=client_ip)
        return APIResponse(success=True, data=challenge_resp, message=challenge_resp.message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))


@router.post(
    "/auth/aadhaar/verify",
    response_model=APIResponse[GatewaySessionResponse],
    status_code=status.HTTP_200_OK,
    summary="Verify Aadhaar OTP and issue gateway session",
)
async def verify_aadhaar_otp(
    payload: AadhaarOtpVerifyRequest,
    request: Request,
) -> APIResponse[GatewaySessionResponse]:
    """Verifies OTP challenge response and returns authenticated session token."""
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    try:
        session_resp = national_gateway_service.verify_aadhaar_otp(
            payload, client_ip=client_ip, user_agent=user_agent
        )
        return APIResponse(success=True, data=session_resp, message=session_resp.message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))


@router.post(
    "/auth/digilocker/verify",
    response_model=APIResponse[GatewaySessionResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate or register citizen via DigiLocker e-KYC claims",
)
async def verify_digilocker_kyc(
    payload: DigiLockerKycAuthRequest,
    request: Request,
) -> APIResponse[GatewaySessionResponse]:
    """Exchanges DigiLocker OAuth2 code and PKCE verifier for authenticated gateway session."""
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    try:
        session_resp = national_gateway_service.verify_digilocker_kyc(
            payload, client_ip=client_ip, user_agent=user_agent
        )
        return APIResponse(success=True, data=session_resp, message=session_resp.message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/auth/mobile/verify",
    response_model=APIResponse[GatewaySessionResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate via active SIM mobile OTP and ABHA lookup",
)
async def verify_abha_mobile(
    payload: AbhaMobileLoginRequest,
    request: Request,
) -> APIResponse[GatewaySessionResponse]:
    """Validates mobile OTP and maps citizen profile."""
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    try:
        session_resp = national_gateway_service.verify_abha_mobile(
            payload, client_ip=client_ip, user_agent=user_agent
        )
        return APIResponse(success=True, data=session_resp, message=session_resp.message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))


@router.post(
    "/auth/emergency/bypass",
    response_model=APIResponse[GatewaySessionResponse],
    status_code=status.HTTP_200_OK,
    summary="Mint break-the-glass emergency offline session with SHA-256 tamper seal",
)
async def mint_emergency_bypass_session(
    payload: EmergencyBypassAuthRequest,
    request: Request,
) -> APIResponse[GatewaySessionResponse]:
    """Issues high-privilege emergency clinical session with immutable cryptographic seal."""
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    try:
        session_resp = national_gateway_service.mint_emergency_bypass_session(
            payload, client_ip=client_ip, user_agent=user_agent
        )
        return APIResponse(success=True, data=session_resp, message=session_resp.message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/sessions",
    response_model=APIResponse[List[GatewayDeviceSession]],
    status_code=status.HTTP_200_OK,
    summary="List active distributed sessions for a user",
)
async def list_active_sessions(
    user_id: str = Query(..., description="User UUID to query active sessions"),
) -> APIResponse[List[GatewayDeviceSession]]:
    """Retrieves all active, non-expired device sessions for multi-device management."""
    sessions = national_gateway_service.list_active_sessions(user_id)
    return APIResponse(
        success=True,
        data=sessions,
        message=f"Found {len(sessions)} active distributed sessions.",
    )


@router.post(
    "/sessions/revoke",
    response_model=APIResponse[bool],
    status_code=status.HTTP_200_OK,
    summary="Revoke a specific active device session",
)
async def revoke_session(
    payload: SessionRevokeRequest,
) -> APIResponse[bool]:
    """Invalidates an active device session immediately across the gateway."""
    revoked = national_gateway_service.revoke_session(payload.session_id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or already revoked.")
    return APIResponse(success=True, data=True, message="Session successfully revoked.")


@router.post(
    "/sessions/revoke-all",
    response_model=APIResponse[int],
    status_code=status.HTTP_200_OK,
    summary="Revoke all active sessions for a user (Global Sign-Out)",
)
async def revoke_all_sessions(
    user_id: str = Query(..., description="User UUID to sign out across all devices"),
) -> APIResponse[int]:
    """Terminates all active sessions for the specified user."""
    count = national_gateway_service.revoke_all_sessions(user_id)
    return APIResponse(success=True, data=count, message=f"Revoked {count} active sessions.")


@router.get(
    "/shield/metrics",
    response_model=APIResponse[RateShieldMetrics],
    status_code=status.HTTP_200_OK,
    summary="Get real-time rate limiter metrics and 50k req/s SLA capacity status",
)
async def get_rate_shield_metrics() -> APIResponse[RateShieldMetrics]:
    """Returns telemetry from the high-density token-bucket rate limiter shield."""
    metrics = national_gateway_service.get_rate_shield_metrics()
    return APIResponse(success=True, data=metrics, message="Rate shield operating at optimal capacity.")


@router.get(
    "/emergency/audit",
    response_model=APIResponse[List[dict]],
    status_code=status.HTTP_200_OK,
    summary="Retrieve immutable log of break-the-glass emergency sessions",
)
async def get_emergency_audit_logs() -> APIResponse[List[dict]]:
    """Returns all break-the-glass emergency bypass events recorded by the gateway."""
    logs = national_gateway_service.get_emergency_audit_logs()
    return APIResponse(success=True, data=logs, message=f"Retrieved {len(logs)} emergency audit records.")

