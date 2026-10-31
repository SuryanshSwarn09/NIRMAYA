"""REST API Endpoints for Cryptographic Audit Hash-Chain and Emergency SMS Dispatch.

Provides endpoints to:
1. Cryptographically verify the integrity of the append-only SHA-256 audit ledger.
2. Query immutable audit blocks chronologically or by patient ABHA.
3. Append custom structured audit events to the ledger.
4. Dispatch and inspect simulated Break-The-Glass emergency contact notifications.
"""

from typing import List, Optional

from fastapi import APIRouter, Query, status

from app.schemas.audit_hash_chain import (
    AuditAppendRequest,
    AuditBlock,
    AuditChainVerificationResult,
    EmergencyDispatchMessage,
    EmergencyDispatchTestRequest,
)
from app.services.audit_hash_chain import audit_ledger_service
from app.services.emergency_dispatch import emergency_dispatch_service

router = APIRouter()


@router.get(
    "/verify",
    response_model=AuditChainVerificationResult,
    summary="Verify cryptographic integrity of audit hash-chain",
)
def verify_audit_chain() -> AuditChainVerificationResult:
    """Performs an exhaustive sequential SHA-256 hash-chain verification from Genesis to Head.

    Detects any block injection, header tampering, or retroactive payload alteration.
    """
    return audit_ledger_service.verify_chain_integrity()


@router.get(
    "/blocks",
    response_model=List[AuditBlock],
    summary="Retrieve chronological audit ledger blocks",
)
def get_audit_blocks(
    limit: int = Query(50, ge=1, le=200, description="Maximum blocks to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[AuditBlock]:
    """Returns chronological audit ledger blocks, newest first."""
    return audit_ledger_service.get_blocks(limit=limit, offset=offset)


@router.get(
    "/patient/{patient_abha}",
    response_model=List[AuditBlock],
    summary="Retrieve audit blocks associated with a patient ABHA",
)
def get_patient_audit_blocks(
    patient_abha: str,
) -> List[AuditBlock]:
    """Returns all cryptographic audit trail blocks linked to the specified patient ABHA."""
    return audit_ledger_service.get_patient_blocks(patient_abha=patient_abha)


@router.post(
    "/append",
    response_model=AuditBlock,
    status_code=status.HTTP_201_CREATED,
    summary="Append a custom auditable event to the hash-chain",
)
def append_audit_event(
    request: AuditAppendRequest,
) -> AuditBlock:
    """Computes SHA-256 payload digest, cryptographically links to the previous head hash, and appends block."""
    return audit_ledger_service.append_event(request)


@router.post(
    "/emergency-dispatch/test",
    response_model=EmergencyDispatchMessage,
    status_code=status.HTTP_201_CREATED,
    summary="Dispatch simulated Break-The-Glass emergency SMS alert",
)
def dispatch_emergency_alert(
    request: EmergencyDispatchTestRequest,
) -> EmergencyDispatchMessage:
    """Dispatches a Break-The-Glass emergency SMS alert to patient next-of-kin via simulated telecom gateway.

    Automatically appends a CRITICAL_ALERT_DISPATCH block to the immutable audit ledger.
    """
    return emergency_dispatch_service.dispatch_emergency_sms(request)


@router.get(
    "/emergency-dispatch/history",
    response_model=List[EmergencyDispatchMessage],
    summary="Query emergency SMS dispatch history",
)
def get_emergency_dispatch_history(
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    patient_abha: Optional[str] = Query(None, description="Filter by patient ABHA"),
) -> List[EmergencyDispatchMessage]:
    """Retrieves carrier dispatch records with carrier message gateway reference IDs and delivery statuses."""
    return emergency_dispatch_service.get_history(limit=limit, patient_abha=patient_abha)
