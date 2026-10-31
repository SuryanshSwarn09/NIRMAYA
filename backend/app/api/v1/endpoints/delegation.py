"""REST endpoints for Chain-of-Command Administrative Provisioning and Scoped TRBAC."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.delegation import (
    AdministrativeDelegationCreate,
    AdministrativeDelegationResponse,
    DelegationRevokeRequest,
    TerritorialScopeValidationRequest,
    TerritorialScopeValidationResponse,
    GovEmailValidationResult,
    DelegationAuditRecord,
)
from app.services.delegation_service import delegation_service

router = APIRouter()


@router.post(
    "/delegations",
    response_model=AdministrativeDelegationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Delegate administrative authority down the chain of command",
    description="Provisions official authority to a subordinate officer with Aadhaar OTP and government email verification.",
)
async def create_delegation(payload: AdministrativeDelegationCreate) -> AdministrativeDelegationResponse:
    """Create a new administrative chain-of-command delegation."""
    try:
        return delegation_service.create_delegation(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/delegations",
    response_model=List[AdministrativeDelegationResponse],
    summary="List administrative delegations",
    description="Query active and historical authority delegations with unit, jurisdiction, and status filters.",
)
async def list_delegations(
    administrative_unit_id: Optional[str] = Query(None, description="Filter by assigned unit UUID"),
    jurisdiction_path: Optional[str] = Query(None, description="Filter by jurisdiction path prefix"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[AdministrativeDelegationResponse]:
    """List recorded delegations matching query filters."""
    return delegation_service.list_delegations(
        administrative_unit_id=administrative_unit_id,
        jurisdiction_path=jurisdiction_path,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/delegations/audit-chain",
    response_model=List[DelegationAuditRecord],
    summary="Get cryptographic delegation audit ledger",
    description="Returns the chronological, immutable SHA-256 audit hash ledger of all delegation events.",
)
async def get_delegation_audit_ledger(
    limit: int = Query(50, ge=1, le=200, description="Number of recent ledger records to fetch"),
) -> List[DelegationAuditRecord]:
    """Retrieve chronological audit hash-chain entries."""
    return delegation_service.get_audit_ledger(limit=limit)


@router.get(
    "/delegations/verify-email",
    response_model=GovEmailValidationResult,
    summary="Validate government email domain",
    description="Verifies whether an email address belongs to authorized Government of India domains (.gov.in, .nic.in).",
)
async def verify_gov_email(
    email: str = Query(..., description="Email address to evaluate"),
) -> GovEmailValidationResult:
    """Verify government email domain."""
    return delegation_service.validate_gov_email(email)


@router.get(
    "/delegations/{delegation_id}",
    response_model=AdministrativeDelegationResponse,
    summary="Get delegation by UUID",
    description="Fetch full details and audit hash for a specific administrative delegation.",
)
async def get_delegation_by_id(delegation_id: str) -> AdministrativeDelegationResponse:
    """Fetch delegation record by UUID."""
    record = delegation_service.get_delegation_by_id(delegation_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delegation record '{delegation_id}' not found.",
        )
    return record


@router.post(
    "/delegations/{delegation_id}/revoke",
    response_model=AdministrativeDelegationResponse,
    summary="Revoke an administrative delegation",
    description="Revokes an active authority delegation and records an unalterable revocation block in the audit ledger.",
)
async def revoke_delegation(
    delegation_id: str,
    payload: DelegationRevokeRequest,
) -> AdministrativeDelegationResponse:
    """Revoke an active delegation."""
    # Ensure payload ID matches URL param
    payload.delegation_id = delegation_id
    try:
        return delegation_service.revoke_delegation(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/delegations/validate-scope",
    response_model=TerritorialScopeValidationResponse,
    summary="Sub-2ms Scoped TRBAC verification",
    description="Validates whether an officer's assigned jurisdiction path covers a target healthcare facility or resource path.",
)
async def validate_scope(
    payload: TerritorialScopeValidationRequest,
) -> TerritorialScopeValidationResponse:
    """Perform instant territorial authority validation."""
    return delegation_service.validate_territorial_scope(payload)
