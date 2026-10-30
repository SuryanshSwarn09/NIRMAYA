"""FastAPI router for ABDM Milestone 3 (M3) Health Information User (HIU) Data Consumer Engine.

Conforms to NHA ABDM v0.5 Data Flow Specification:
- POST /api/v1/abdm/m3/hiu/request: Initiate health data request under consent
- POST /api/v1/abdm/m3/hiu/transfer: Inbound receiver for encrypted health data push
- GET /api/v1/abdm/m3/hiu/records/patient/{patient_id}: Query imported longitudinal patient records
- GET /api/v1/abdm/m3/hiu/records/transaction/{transaction_id}: Query records by transaction ID
- GET /api/v1/abdm/m3/hiu/sessions: List active HIU request sessions
- GET /api/v1/abdm/m3/hiu/sessions/{transaction_id}: Get HIU request session detail
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, status

from app.core.exceptions import ValidationException
from app.schemas.abdm_m3_hiu import (
    DecryptedClinicalBundle,
    HIUDataRequestInitiate,
    HIUPatientRecordsResponse,
    HIURequestSession,
)
from app.schemas.abdm_m3_transfer import (
    DataTransferPushPayload,
)
from app.services.abdm_hiu import (
    AbdmHIUService,
    hiu_record_store,
    hiu_request_store,
)

logger = logging.getLogger("nirmaya.abdm.m3_hiu_api")

router = APIRouter()


# ============================================================================
# HIU Request & Ingestion Endpoints
# ============================================================================

@router.post(
    "/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate Outbound Health Information Request (HIU Mode)",
    description="Generates ephemeral Curve25519 keypair and nonce, caches session in HIURequestStore, and formulates Gateway request.",
)
async def initiate_health_information_request(
    req: HIUDataRequestInitiate,
) -> Dict[str, Any]:
    """Initiates an outbound health information request for a consented patient."""
    try:
        session, gateway_payload = AbdmHIUService.initiate_hi_request(req)
        return {
            "status": "INITIATED",
            "transactionId": session.transactionId,
            "consentId": session.consentId,
            "patientId": session.patientId,
            "keyMaterial": {
                "cryptoAlg": "ECDH",
                "curve": "Curve25519",
                "publicKey": session.hiuPublicKey,
                "nonce": session.hiuNonce,
            },
            "gatewayPayload": gateway_payload,
            "message": "Health information request initiated and ephemeral keys generated",
        }
    except ValidationException as ve:
        raise HTTPException(status_code=400, detail=ve.message)
    except Exception as e:
        logger.error(f"[initiate_health_information_request] Failed: {e}")
        raise HTTPException(status_code=500, detail=f"Request initiation failed: {str(e)}")


@router.post(
    "/transfer",
    status_code=status.HTTP_200_OK,
    summary="Inbound Encrypted Data Transfer Receiver (HIU Mode)",
    description="Ingests encrypted FHIR bundles from HIP, derives symmetric key via Nonce XOR and ECDH, decrypts with AES-256-GCM, verifies SHA-256 checksums, and parses clinical records.",
)
async def inbound_encrypted_transfer_receiver(
    payload: DataTransferPushPayload,
) -> Dict[str, Any]:
    """Ingests, decrypts, and parses encrypted health records pushed by peer HIP."""
    success, error_msg, bundles = AbdmHIUService.process_inbound_transfer(payload)

    if not success:
        logger.warning(f"[inbound_encrypted_transfer_receiver] Rejected: {error_msg}")
        raise HTTPException(
            status_code=400,
            detail=error_msg or "Failed to decrypt and process inbound transfer",
        )

    return {
        "status": "PROCESSED",
        "transactionId": str(payload.transactionId),
        "bundlesImported": len(bundles),
        "totalEncounters": sum(len(b.encounters) for b in bundles),
        "totalDiagnostics": sum(len(b.diagnosticReports) for b in bundles),
        "totalPrescriptions": sum(len(b.prescriptions) for b in bundles),
        "totalObservations": sum(len(b.observations) for b in bundles),
        "message": f"Successfully decrypted and ingested {len(bundles)} clinical bundles into patient record vault",
    }


# ============================================================================
# Longitudinal Record Queries for Clinicians
# ============================================================================

@router.get(
    "/records/patient/{patient_id}",
    response_model=HIUPatientRecordsResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Imported Longitudinal Medical Records by Patient ID",
)
async def get_patient_longitudinal_records(
    patient_id: str,
    transaction_id: Optional[str] = Query(None, description="Optional transaction filter"),
    consent_id: Optional[str] = Query(None, description="Optional consent filter"),
) -> HIUPatientRecordsResponse:
    """Retrieves all historical medical records decrypted and imported for a patient."""
    return AbdmHIUService.aggregate_patient_records(
        patient_id=patient_id,
        transaction_id=transaction_id,
        consent_id=consent_id,
    )


@router.get(
    "/records/transaction/{transaction_id}",
    response_model=HIUPatientRecordsResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Imported Records by Transaction ID",
)
async def get_transaction_records(
    transaction_id: str,
) -> HIUPatientRecordsResponse:
    """Retrieves records imported specifically in a given data transfer transaction."""
    session = hiu_request_store.get_session(transaction_id)
    patient_id = session.patientId if session else "UNKNOWN"
    consent_id = session.consentId if session else None

    return AbdmHIUService.aggregate_patient_records(
        patient_id=patient_id,
        transaction_id=transaction_id,
        consent_id=consent_id,
    )


# ============================================================================
# Session Inspection Endpoints
# ============================================================================

@router.get(
    "/sessions",
    response_model=List[HIURequestSession],
    status_code=status.HTTP_200_OK,
    summary="List Active HIU Request Sessions",
)
async def list_hiu_sessions() -> List[HIURequestSession]:
    """Lists all active and unexpired HIU data request sessions."""
    return hiu_request_store.list_sessions()


@router.get(
    "/sessions/{transaction_id}",
    response_model=HIURequestSession,
    status_code=status.HTTP_200_OK,
    summary="Get HIU Request Session Detail",
)
async def get_hiu_session(
    transaction_id: str,
) -> HIURequestSession:
    """Retrieves session details by transaction ID."""
    session = hiu_request_store.get_session(transaction_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"HIU request session '{transaction_id}' not found or expired",
        )
    return session
