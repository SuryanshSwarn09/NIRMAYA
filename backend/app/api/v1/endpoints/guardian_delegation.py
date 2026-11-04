from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from app.core.container_security import get_container_security_headers
from app.schemas.guardian_delegation import (
    ConsentAuditTrailItem,
    DelegatedConsentArtifactResponse,
    DelegatedConsentGrantRequest,
    DelegatedConsentRevokeRequest,
    ScopedProxyTokenRequest,
    ScopedProxyTokenResponse,
)
from app.services.guardian_delegation_service import guardian_delegation_service

router = APIRouter(
    prefix="/patients/proxy",
    tags=["Guardian Access Delegation & ABDM Consent Interceptor"],
)


class ConsentInterceptRequest(BaseModel):
    """Payload to evaluate proxy eligibility on an inbound ABDM consent request."""
    guardian_id: str = Field(..., description="Unique ID of guardian")
    dependent_id: str = Field(..., description="Unique ID of dependent patient")
    consent_request_id: str = Field(..., description="Inbound ABDM consent request ID")


@router.post(
    "/delegation/token",
    summary="Issue Ephemeral Scoped Proxy Access Token",
    description="Exchanges verified family proxy delegation for an ephemeral, purpose-restricted Bearer token under DPDP Act Sec 9.",
    response_model=ScopedProxyTokenResponse,
)
async def issue_scoped_proxy_token(
    payload: ScopedProxyTokenRequest,
    response: Response,
) -> ScopedProxyTokenResponse:
    """Issue ephemeral scoped proxy access token."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    try:
        return guardian_delegation_service.generate_scoped_proxy_token(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/consent/grant",
    summary="Authorize and Issue Delegated ABDM Electronic Consent Artifact",
    description="Signs and issues an ABDM electronic consent artifact for a dependent patient, certified by a verified proxy guardian.",
    response_model=DelegatedConsentArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def grant_delegated_consent(
    payload: DelegatedConsentGrantRequest,
    response: Response,
) -> DelegatedConsentArtifactResponse:
    """Authorize and grant delegated consent artifact."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    try:
        return guardian_delegation_service.grant_delegated_consent(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/consent/{artifact_id}/revoke",
    summary="Revoke Delegated Consent Artifact",
    description="Revokes an active delegated consent artifact, halting further clinical record ingestion by the requesting HIU.",
    response_model=DelegatedConsentArtifactResponse,
)
async def revoke_delegated_consent(
    artifact_id: str,
    payload: DelegatedConsentRevokeRequest,
    response: Response,
) -> DelegatedConsentArtifactResponse:
    """Revoke delegated consent artifact."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    try:
        return guardian_delegation_service.revoke_delegated_consent(payload)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/consent/artifacts",
    summary="List Delegated Electronic Consent Artifacts",
    description="Retrieve active and historical electronic consent artifacts issued via proxy delegation.",
    response_model=List[DelegatedConsentArtifactResponse],
)
async def list_delegated_consent_artifacts(
    response: Response,
    guardian_id: Optional[str] = Query(None, description="Optional filter by guardian ID"),
    dependent_id: Optional[str] = Query(None, description="Optional filter by dependent ID"),
) -> List[DelegatedConsentArtifactResponse]:
    """List delegated consent artifacts."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    return guardian_delegation_service.list_delegated_consents(guardian_id, dependent_id)


@router.get(
    "/consent/pending-requests",
    summary="List Pending Inbound ABDM Consent Requests",
    description="Retrieve inbound consent requests awaiting guardian review and authorization.",
)
async def list_pending_consent_requests(
    response: Response,
) -> List[Dict[str, Any]]:
    """Retrieve pending consent requests."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    return guardian_delegation_service.list_pending_requests()


@router.get(
    "/consent/audit",
    summary="Get Immutable Consent Delegation Audit Trail",
    description="Retrieve append-only forensic audit entries for all proxy consent authorizations, revocations, and token grants.",
    response_model=List[ConsentAuditTrailItem],
)
async def get_consent_audit_trail(
    response: Response,
    artifact_id: Optional[str] = Query(None, description="Optional filter by artifact ID"),
) -> List[ConsentAuditTrailItem]:
    """Retrieve forensic audit trail of consent delegation events."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    return guardian_delegation_service.get_audit_trail(artifact_id)


@router.post(
    "/consent/intercept",
    summary="Intercept and Verify Inbound Consent Request Eligibility",
    description="Security guard evaluating whether an inbound consent request on a dependent record is authorized for proxy action.",
)
async def intercept_inbound_consent(
    payload: ConsentInterceptRequest,
    response: Response,
) -> Dict[str, Any]:
    """Evaluate proxy eligibility for inbound consent request."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    return guardian_delegation_service.intercept_consent_request(
        guardian_id=payload.guardian_id,
        dependent_id=payload.dependent_id,
        consent_request_id=payload.consent_request_id,
    )
