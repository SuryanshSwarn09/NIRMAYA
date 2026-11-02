from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from app.core.container_security import get_container_security_headers
from app.schemas.family_proxy import (
    FamilyProxyCreateRequest,
    FamilyProxyResponse,
    ProxyAuditLogItem,
)
from app.services.family_proxy_service import family_proxy_service

router = APIRouter(prefix="/patients/proxy", tags=["Dependent & Family Health Proxy (DPDP Act Sec 9)"])


class ProxyAuthorizationCheckRequest(BaseModel):
    """Payload to verify delegated access permissions on a dependent record."""
    guardian_id: str = Field(..., description="Unique ID of guardian requesting access")
    dependent_id: str = Field(..., description="Unique ID of dependent patient")
    action: str = Field(..., description="Action to perform (e.g., VIEW_RECORDS, SCHEDULE_APPOINTMENT)")


class ProxyAuthorizationCheckResponse(BaseModel):
    """Result of authorization evaluation under zero-contamination constraints."""
    authorized: bool
    guardian_id: str
    dependent_id: str
    action: str
    evaluated_at: datetime


class ProxyRevokeRequest(BaseModel):
    """Payload for revoking a delegated proxy relationship."""
    actor_id: str = Field("pat-priya-sharma-01", description="Identifier of actor requesting revocation")
    reason: str = Field("Guardian Revocation", description="Clinical or administrative justification")


@router.get(
    "/relationships",
    summary="List Family Proxy Relationships",
    description="Retrieve familial proxy relationships for a specific guardian or all registered linkages.",
    response_model=List[FamilyProxyResponse],
)
async def list_relationships(
    response: Response,
    guardian_id: Optional[str] = Query(None, description="Optional filter by guardian patient ID"),
) -> List[FamilyProxyResponse]:
    """Retrieve all proxy relationships or those matching the guardian."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    if guardian_id:
        return family_proxy_service.list_dependents_for_guardian(guardian_id)
    return list(family_proxy_service._relationships.values())


@router.get(
    "/dependents",
    summary="List Active Dependents for Guardian",
    description="Retrieve all active dependents linked to the requesting guardian adhering to DPDP Act Sec 9.",
    response_model=List[FamilyProxyResponse],
)
async def list_dependents(
    response: Response,
    guardian_id: str = Query("pat-priya-sharma-01", description="Guardian patient ID"),
) -> List[FamilyProxyResponse]:
    """List active dependents for the specified guardian."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return family_proxy_service.list_dependents_for_guardian(guardian_id)


@router.post(
    "/relationships",
    summary="Establish Family Proxy Relationship",
    description="Establish and verify a new dependent family proxy linkage adhering to DPDP Act Sec 9.",
    response_model=FamilyProxyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def establish_relationship(
    request: FamilyProxyCreateRequest,
    response: Response,
) -> FamilyProxyResponse:
    """Create a new verified proxy relationship."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    try:
        return family_proxy_service.establish_proxy_relationship(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/relationships/{relationship_id}",
    summary="Get Proxy Relationship Details",
    description="Fetch single proxy relationship metadata and verification tier by relationship ID.",
    response_model=FamilyProxyResponse,
)
async def get_relationship(
    relationship_id: str,
    response: Response,
) -> FamilyProxyResponse:
    """Retrieve details of a single proxy relationship."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    rel = family_proxy_service.get_relationship(relationship_id)
    if not rel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proxy relationship '{relationship_id}' not found.",
        )
    return rel


@router.post(
    "/relationships/{relationship_id}/revoke",
    summary="Revoke Delegated Proxy Privileges",
    description="Revoke an active proxy relationship and record forensic audit entry.",
    response_model=FamilyProxyResponse,
)
async def revoke_relationship(
    relationship_id: str,
    payload: ProxyRevokeRequest,
    response: Response,
) -> FamilyProxyResponse:
    """Revoke proxy relationship privileges."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    try:
        return family_proxy_service.revoke_proxy_relationship(
            relationship_id=relationship_id,
            actor_id=payload.actor_id,
            reason=payload.reason,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/relationships/{relationship_id}/audit",
    summary="Get Immutable Proxy Forensic Audit Trail",
    description="Retrieve tamper-evident audit trail for actions performed via proxy relationship.",
    response_model=List[ProxyAuditLogItem],
)
async def get_proxy_audit_trail(
    relationship_id: str,
    response: Response,
) -> List[ProxyAuditLogItem]:
    """Retrieve audit log items for a specific relationship."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    return family_proxy_service.get_audit_logs(relationship_id=relationship_id)


@router.post(
    "/authorize-action",
    summary="Validate Proxy Action Authorization",
    description="Security guard evaluating whether an action on a dependent record is authorized under proxy delegation.",
    response_model=ProxyAuthorizationCheckResponse,
)
async def check_proxy_authorization(
    request: ProxyAuthorizationCheckRequest,
    response: Response,
) -> ProxyAuthorizationCheckResponse:
    """Evaluate proxy action permission."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    is_allowed = family_proxy_service.verify_proxy_access_permission(
        guardian_id=request.guardian_id,
        dependent_id=request.dependent_id,
        requested_action=request.action,
    )
    return ProxyAuthorizationCheckResponse(
        authorized=is_allowed,
        guardian_id=request.guardian_id,
        dependent_id=request.dependent_id,
        action=request.action,
        evaluated_at=datetime.now(timezone.utc),
    )

