"""REST API Endpoints for Break-The-Glass (BTG) Emergency Health Vault and Forensic Audit.

Provides Zero-Knowledge emergency health profile provisioning, audited emergency
override execution for ICU/ER physicians, and tamper-evident compliance audit trails.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.schemas.emergency_vault import (
    BTGAuditLogEntry,
    BTGOverrideRequest,
    BTGOverrideResponse,
    BTGStatsResponse,
    EmergencyProfileData,
    EmergencyVaultStatusResponse,
    EncryptedVaultEnvelope,
)
from app.services.emergency_vault import emergency_vault_service

router = APIRouter()


@router.post(
    "/vault/store",
    response_model=EncryptedVaultEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Encrypt and provision emergency health vault",
)
def store_emergency_vault(
    profile: EmergencyProfileData,
) -> EncryptedVaultEnvelope:
    """Provisions a Zero-Knowledge emergency health profile encrypted with Argon2id and AES-256-GCM AEAD."""
    return emergency_vault_service.store_vault(profile)


@router.get(
    "/vault/{patient_abha}/status",
    response_model=EmergencyVaultStatusResponse,
    summary="Check emergency vault status for patient",
)
def get_vault_status(
    patient_abha: str,
) -> EmergencyVaultStatusResponse:
    """Verifies whether an encrypted emergency health profile is provisioned for an ABHA identity."""
    return emergency_vault_service.get_vault_status(patient_abha)


@router.post(
    "/override",
    response_model=BTGOverrideResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Break-The-Glass emergency clinical override",
)
async def execute_emergency_override(
    request_data: BTGOverrideRequest,
    request: Request,
) -> BTGOverrideResponse:
    """Executes a legally compliant Break-The-Glass emergency override.

    Decrypts the patient's critical emergency health profile, records an immutable
    SHA-256 sealed forensic audit trail, and broadcasts real-time alerts.
    """
    client_ip = request.client.host if request.client else None
    try:
        return await emergency_vault_service.execute_emergency_override(
            request=request_data,
            ip_address=client_ip,
        )
    except EntityNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValidationException as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.get(
    "/audit",
    response_model=List[BTGAuditLogEntry],
    summary="Query forensic Break-The-Glass audit trail",
)
def get_btg_audit_trail(
    patient_abha: Optional[str] = Query(None, description="Filter audit trail by patient ABHA"),
    facility_id: Optional[str] = Query(None, description="Filter audit trail by hospital facility ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of audit events to return"),
) -> List[BTGAuditLogEntry]:
    """Retrieves immutable forensic audit records tracking all emergency overrides."""
    return emergency_vault_service.get_audit_trail(
        patient_abha=patient_abha,
        facility_id=facility_id,
        limit=limit,
    )


@router.get(
    "/stats",
    response_model=BTGStatsResponse,
    summary="Get hospital emergency override statistics",
)
def get_btg_stats(
    facility_id: Optional[str] = Query(None, description="Facility ID filter"),
) -> BTGStatsResponse:
    """Provides emergency department compliance and override justification breakdown."""
    return emergency_vault_service.get_stats(facility_id=facility_id)
