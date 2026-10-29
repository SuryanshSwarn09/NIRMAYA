"""FastAPI routers for ABDM Milestone 3 (M3) Encrypted Health Data Transfer Pipeline.

Conforms to NHA ABDM v0.5 Data Flow Specification:
- Gateway Router (mounted under /v0.5):
  - POST /health-information/transfer: Inbound data transfer receiver (when NIRMAYA acts as HIU)
  - POST /health-information/notify: Transfer status notification callback receiver
- Local API Router (mounted under /api/v1/abdm/m3/transfer):
  - POST /push: Initiate encrypted data transfer push for an active transaction
  - POST /encrypt: Direct testing utility for AES-256-GCM authenticated encryption
  - POST /decrypt: Direct testing utility for AES-256-GCM authenticated decryption
  - GET /history: Query recent data transfer audit history
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, status

from app.core.exceptions import ValidationException
from app.schemas.abdm_m3_transfer import (
    DataTransferNotificationPayload,
    DataTransferPushPayload,
    DataTransferPushResponse,
    DirectDecryptRequest,
    DirectDecryptResponse,
    DirectEncryptRequest,
    DirectEncryptResponse,
    TransferAuditRecord,
    TransferTriggerRequest,
)
from app.services.abdm_transfer import (
    AbdmTransferService,
    dispatch_transfer_notify,
    dispatch_transfer_push,
    transfer_audit_store,
)

logger = logging.getLogger("nirmaya.abdm.m3_transfer_api")

gateway_router = APIRouter()
router = APIRouter()


# ============================================================================
# Gateway Webhook Endpoints (Mounted under /v0.5)
# ============================================================================

@gateway_router.post(
    "/health-information/transfer",
    status_code=status.HTTP_200_OK,
    summary="ABDM Gateway Inbound Encrypted Health Data Transfer Receiver",
    description="Receives encrypted clinical bundle transfer from HIP (used when NIRMAYA operates as HIU).",
)
async def gateway_inbound_health_information_transfer(
    payload: DataTransferPushPayload,
) -> Dict[str, Any]:
    """Inbound receiver for encrypted health information FHIR bundles."""
    logger.info(
        f"[gateway_inbound_health_information_transfer] Received data transfer for "
        f"tx={payload.transactionId}, entries_count={len(payload.entries)}"
    )

    # Record in audit store
    audit_rec = TransferAuditRecord(
        id=str(uuid.uuid4()),
        transactionId=str(payload.transactionId),
        consentId="INBOUND",
        direction="INBOUND_RECEIVE",
        entriesCount=len(payload.entries),
        status="RECEIVED",
        timestamp=datetime.now(timezone.utc),
    )
    transfer_audit_store.add_record(audit_rec)

    return {
        "status": "RECEIVED",
        "transactionId": str(payload.transactionId),
        "entriesReceived": len(payload.entries),
        "pageNumber": payload.pageNumber,
        "pageCount": payload.pageCount,
        "message": f"Successfully ingested {len(payload.entries)} encrypted FHIR bundle entries",
    }


@gateway_router.post(
    "/health-information/notify",
    status_code=status.HTTP_200_OK,
    summary="ABDM Gateway Health Information Status Notification Receiver",
)
async def gateway_inbound_health_information_notify(
    payload: DataTransferNotificationPayload,
) -> Dict[str, Any]:
    """Receives Gateway confirmation of transfer session completion."""
    logger.info(
        f"[gateway_inbound_health_information_notify] Transfer status notification for "
        f"tx={payload.notification.transactionId}, "
        f"status={payload.notification.statusNotification.sessionStatus}"
    )
    return {
        "status": "ACKNOWLEDGED",
        "requestId": str(payload.requestId),
        "transactionId": payload.notification.transactionId,
    }


# ============================================================================
# Local API Endpoints (Mounted under /api/v1/abdm/m3/transfer)
# ============================================================================

@router.post(
    "/push",
    response_model=DataTransferPushResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate Encrypted Health Data Transfer Push",
    description="Packages authorized clinical records into FHIR R4 Document Bundles, encrypts with AES-256-GCM, and dispatches to HIU dataPushUrl.",
)
async def trigger_encrypted_data_transfer(
    req: TransferTriggerRequest,
    background_tasks: BackgroundTasks,
) -> DataTransferPushResponse:
    """Manually triggers health data packaging, encryption, and dispatch."""
    try:
        response = AbdmTransferService.execute_data_transfer(req.transactionId)
        return response
    except ValidationException as ve:
        raise HTTPException(status_code=400, detail=ve.message)
    except Exception as e:
        logger.error(f"[trigger_encrypted_data_transfer] Data transfer execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Encrypted data transfer pipeline failed: {str(e)}",
        )


@router.post(
    "/encrypt",
    response_model=DirectEncryptResponse,
    status_code=status.HTTP_200_OK,
    summary="Direct AES-256-GCM Encryption Utility",
)
async def direct_encrypt_utility(
    req: DirectEncryptRequest,
) -> DirectEncryptResponse:
    """Encrypts arbitrary plaintext string using AES-256-GCM and returns Base64 ciphertext with SHA-256 checksum."""
    try:
        key_bytes = bytes.fromhex(req.keyHex)
        iv_bytes = bytes.fromhex(req.ivHex)
        b64_cipher, checksum = AbdmTransferService.encrypt_payload(
            plaintext=req.plaintext,
            derived_key=key_bytes,
            iv=iv_bytes,
        )
        return DirectEncryptResponse(
            ciphertext=b64_cipher,
            checksum=checksum,
            status="SUCCESS",
        )
    except ValidationException as ve:
        raise HTTPException(status_code=400, detail=ve.message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Encryption failed: {str(e)}")


@router.post(
    "/decrypt",
    response_model=DirectDecryptResponse,
    status_code=status.HTTP_200_OK,
    summary="Direct AES-256-GCM Decryption Utility",
)
async def direct_decrypt_utility(
    req: DirectDecryptRequest,
) -> DirectDecryptResponse:
    """Decrypts Base64 AES-256-GCM ciphertext and validates authentication tag."""
    try:
        key_bytes = bytes.fromhex(req.keyHex)
        iv_bytes = bytes.fromhex(req.ivHex)
        plaintext = AbdmTransferService.decrypt_payload(
            b64_ciphertext=req.ciphertext,
            derived_key=key_bytes,
            iv=iv_bytes,
        )
        return DirectDecryptResponse(
            plaintext=plaintext,
            status="SUCCESS",
        )
    except ValidationException as ve:
        raise HTTPException(status_code=400, detail=ve.message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")


@router.get(
    "/history",
    response_model=List[TransferAuditRecord],
    status_code=status.HTTP_200_OK,
    summary="Query Recent Data Transfer Audit Records",
)
async def get_transfer_history() -> List[TransferAuditRecord]:
    """Retrieves circular audit records of recent data transfers."""
    return transfer_audit_store.get_records()
