from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from app.core.container_security import get_container_security_headers
from app.schemas.common import APIResponse
from app.schemas.guardian_conflict import (
    ConflictResolutionPolicyEnum,
    CustodyModeEnum,
    DualSignConsentArtifactRequest,
    DualSignConsentArtifactResponse,
    DualSignCounterSignatureRequest,
    DualSignStatusEnum,
    GuardianActionTypeEnum,
    GuardianConflictResolutionRequest,
    GuardianConflictResolutionResponse,
    GuardianDisputeStatusEnum,
    MultiGuardianRelationshipSummary,
)
from app.services.guardian_conflict_service import guardian_conflict_service

router = APIRouter(
    prefix="/patients/proxy/conflict",
    tags=["Multi-Guardian Concurrency & Conflict Resolution Engine"],
)


class RaiseDisputeRequest(BaseModel):
    dependent_patient_id: str = Field(..., description="Target dependent patient ID")
    initiating_guardian_id: str = Field(..., description="Guardian filing custody dispute")
    justification: str = Field(..., description="Custodial or legal rationale")
    legal_order_reference: Optional[str] = Field(None, description="Court case or decree reference")
    guardian_signature_attestation: bool = Field(True, description="Digital signature attestation")


class ResolveDisputeRequest(BaseModel):
    dependent_patient_id: str = Field(..., description="Target dependent patient ID")
    initiating_guardian_id: str = Field(..., description="Guardian submitting resolution")
    justification: str = Field(..., description="Resolution or mutual agreement rationale")
    legal_order_reference: Optional[str] = Field(None, description="Court case or decree reference")
    guardian_signature_attestation: bool = Field(True, description="Digital signature attestation")


@router.get(
    "/dependents/{dependent_patient_id}/guardians",
    response_model=APIResponse[MultiGuardianRelationshipSummary],
    summary="Retrieve all registered guardians and active custody governance for a dependent",
)
async def get_guardians_for_dependent(
    dependent_patient_id: str,
    response: Response,
) -> APIResponse[MultiGuardianRelationshipSummary]:
    for k, v in get_container_security_headers().items():
        response.headers[k] = v

    summary = guardian_conflict_service.get_guardians_for_dependent(dependent_patient_id)
    response.headers["X-Multi-Guardian-Engine"] = "active"
    response.headers["X-Custody-Governance"] = summary.custody_mode.value

    return APIResponse(success=True, data=summary)


@router.post(
    "/arbitrate",
    response_model=APIResponse[GuardianConflictResolutionResponse],
    summary="Submit multi-guardian action for policy arbitration and pessimistic resolution",
)
async def arbitrate_guardian_action(
    payload: GuardianConflictResolutionRequest,
    response: Response,
) -> APIResponse[GuardianConflictResolutionResponse]:
    for k, v in get_container_security_headers().items():
        response.headers[k] = v

    try:
        result = guardian_conflict_service.arbitrate_action(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    response.headers["X-Conflict-Arbitration-Ticket"] = result.ticket_id
    response.headers["X-Pessimistic-Resolution"] = result.effective_policy.value

    return APIResponse(success=True, data=result)


@router.post(
    "/dispute/raise",
    response_model=APIResponse[GuardianConflictResolutionResponse],
    summary="Register a formal custody dispute and engage automatic custodial pessimistic freeze",
)
async def raise_custodial_dispute(
    payload: RaiseDisputeRequest,
    response: Response,
) -> APIResponse[GuardianConflictResolutionResponse]:
    for k, v in get_container_security_headers().items():
        response.headers[k] = v

    arb_req = GuardianConflictResolutionRequest(
        dependent_patient_id=payload.dependent_patient_id,
        initiating_guardian_id=payload.initiating_guardian_id,
        action_type=GuardianActionTypeEnum.RAISE_LEGAL_DISPUTE,
        target_artifact_id=None,
        proposed_policy=ConflictResolutionPolicyEnum.DISPUTED_CUSTODY_FREEZE,
        legal_order_reference=payload.legal_order_reference,
        justification=payload.justification,
        guardian_signature_attestation=payload.guardian_signature_attestation,
    )
    try:
        result = guardian_conflict_service.arbitrate_action(arb_req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    response.headers["X-Custody-Dispute-Ticket"] = result.ticket_id
    return APIResponse(success=True, data=result)


@router.post(
    "/dispute/resolve",
    response_model=APIResponse[GuardianConflictResolutionResponse],
    summary="Resolve an active custody contest and restore standard governance",
)
async def resolve_custodial_dispute(
    payload: ResolveDisputeRequest,
    response: Response,
) -> APIResponse[GuardianConflictResolutionResponse]:
    for k, v in get_container_security_headers().items():
        response.headers[k] = v

    arb_req = GuardianConflictResolutionRequest(
        dependent_patient_id=payload.dependent_patient_id,
        initiating_guardian_id=payload.initiating_guardian_id,
        action_type=GuardianActionTypeEnum.RESOLVE_DISPUTE,
        target_artifact_id=None,
        proposed_policy=ConflictResolutionPolicyEnum.PRIMARY_GUARDIAN_ARBITRATION,
        legal_order_reference=payload.legal_order_reference,
        justification=payload.justification,
        guardian_signature_attestation=payload.guardian_signature_attestation,
    )
    try:
        result = guardian_conflict_service.arbitrate_action(arb_req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    response.headers["X-Custody-Resolution-Ticket"] = result.ticket_id
    return APIResponse(success=True, data=result)


@router.get(
    "/disputes",
    response_model=APIResponse[List[Dict[str, Any]]],
    summary="List registered disputes and sub-judice custody contests",
)
async def list_dispute_tickets(
    dependent_patient_id: Optional[str] = Query(None, description="Optional dependent ID filter"),
    response: Response = None,
) -> APIResponse[List[Dict[str, Any]]]:
    if response:
        for k, v in get_container_security_headers().items():
            response.headers[k] = v

    tickets = guardian_conflict_service.list_dispute_tickets(dependent_patient_id)
    return APIResponse(success=True, data=tickets)


@router.post(
    "/dual-sign/create",
    response_model=APIResponse[DualSignConsentArtifactResponse],
    summary="Initiate two-phase co-signed consent artifact requiring secondary guardian counter-signature",
)
async def create_dual_sign_artifact(
    payload: DualSignConsentArtifactRequest,
    response: Response,
) -> APIResponse[DualSignConsentArtifactResponse]:
    for k, v in get_container_security_headers().items():
        response.headers[k] = v

    try:
        artifact = guardian_conflict_service.create_dual_sign_request(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    response.headers["X-Dual-Sign-Artifact-Id"] = artifact.artifact_id
    response.headers["X-Dual-Sign-Status"] = artifact.status.value

    return APIResponse(success=True, data=artifact)


@router.post(
    "/dual-sign/{artifact_id}/counter-sign",
    response_model=APIResponse[DualSignConsentArtifactResponse],
    summary="Submit secondary guardian digital counter-signature to fully authorize consent artifact",
)
async def counter_sign_dual_artifact(
    artifact_id: str,
    payload: DualSignCounterSignatureRequest,
    response: Response,
) -> APIResponse[DualSignConsentArtifactResponse]:
    for k, v in get_container_security_headers().items():
        response.headers[k] = v

    payload.artifact_id = artifact_id
    try:
        artifact = guardian_conflict_service.counter_sign_dual_artifact(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    response.headers["X-Dual-Sign-Artifact-Id"] = artifact.artifact_id
    response.headers["X-Dual-Sign-Status"] = artifact.status.value

    return APIResponse(success=True, data=artifact)


@router.get(
    "/audit-ledger",
    response_model=APIResponse[List[Dict[str, Any]]],
    summary="Retrieve immutable forensic audit trail of all arbitration and multi-guardian events",
)
async def get_audit_ledger(
    dependent_patient_id: Optional[str] = Query(None, description="Optional dependent ID filter"),
    response: Response = None,
) -> APIResponse[List[Dict[str, Any]]]:
    if response:
        for k, v in get_container_security_headers().items():
            response.headers[k] = v

    ledger = guardian_conflict_service.get_audit_ledger(dependent_patient_id)
    return APIResponse(success=True, data=ledger)
