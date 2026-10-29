"""FastAPI routers for ABDM Milestone 3 (M3) Cryptographic Key Exchange & Health Information Flow.

Conforms to NHA ABDM v0.5 Data Flow Specification:
- Gateway Router (mounted under /v0.5):
  - POST /health-information/hip/request: Inbound data request from Gateway / HIU
  - POST /health-information/hip/on-request: Gateway acknowledgement callback
- Local API Router (mounted under /api/v1/abdm/m3/crypto):
  - POST /keys/generate: Local Curve25519 key & nonce generation
  - POST /exchange: Local ECDH & HKDF-SHA256 handshake computation
  - GET /sessions: Inspect active cryptographic sessions
  - GET /sessions/{transaction_id}: Get specific session details
  - POST /request: Direct alias for health information request
  - POST /on-request: Direct alias for health information on-request
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Response, status

from app.core.exceptions import ValidationException
from app.schemas.abdm_m3_crypto import (
    CryptoSessionDetail,
    GatewayHIError,
    GatewayRespRef,
    HIOnRequestAcknowledgement,
    HIOnRequestCallback,
    HIRequestPayload,
    KeyExchangeComputeRequest,
    KeyExchangeComputeResponse,
    KeyGenerationResponse,
)
from app.services.abdm_crypto import (
    AbdmCryptoService,
    crypto_session_store,
    dispatch_hi_on_request,
)
from app.services.abdm_hip_bridge import (
    validate_gateway_headers,
)

logger = logging.getLogger("nirmaya.abdm.m3_crypto_api")

gateway_router = APIRouter()
router = APIRouter()


# ============================================================================
# Handler Logic
# ============================================================================

async def handle_inbound_hi_request(
    payload: HIRequestPayload,
    background_tasks: BackgroundTasks,
    request_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    x_cm_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Processes inbound health information request, verifies consent artefact, executes ECDH key agreement."""
    req_id_val = request_id or str(payload.requestId)
    ts_val = timestamp or (payload.timestamp.isoformat() if payload.timestamp else None)

    # 1. Validate gateway headers if provided
    try:
        valid_req_id, _ = validate_gateway_headers(
            request_id_header=req_id_val,
            timestamp_header=ts_val,
            x_cm_id_header=x_cm_id,
        )
    except Exception as e:
        logger.warning(f"[handle_inbound_hi_request] Header validation note: {e}")

    logger.info(
        f"[handle_inbound_hi_request] Processing req={payload.requestId}, "
        f"tx={payload.transactionId}, consent={payload.hiRequest.consent.id}"
    )

    # 2. Process request: validate consent and derive symmetric key
    success, error_msg, session = AbdmCryptoService.process_inbound_hi_request(payload)

    if success and session:
        callback = HIOnRequestCallback(
            requestId=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            hiRequest=HIOnRequestAcknowledgement(
                transactionId=payload.transactionId,
                status="ACKNOWLEDGED",
            ),
            error=None,
            resp=GatewayRespRef(requestId=payload.requestId),
        )
        background_tasks.add_task(dispatch_hi_on_request, callback)

        return {
            "status": "ACCEPTED",
            "transactionId": str(payload.transactionId),
            "consentId": payload.hiRequest.consent.id,
            "keyExchange": {
                "cryptoAlg": "ECDH",
                "curve": "Curve25519",
                "hipPublicKey": session.hipPublicKey,
                "hipNonce": session.hipNonce,
            },
            "message": "Health information request verified and key agreement established",
        }
    else:
        # Formulate error callback to gateway
        callback = HIOnRequestCallback(
            requestId=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            hiRequest=None,
            error=GatewayHIError(
                code=1401,
                message=error_msg or "Consent artefact invalid or unauthorized",
            ),
            resp=GatewayRespRef(requestId=payload.requestId),
        )
        background_tasks.add_task(dispatch_hi_on_request, callback)

        return {
            "status": "REJECTED",
            "transactionId": str(payload.transactionId),
            "error": error_msg,
            "message": "Health information request rejected",
        }


async def handle_inbound_hi_on_request(
    callback: HIOnRequestCallback,
) -> Dict[str, Any]:
    """Receives Gateway acknowledgement callback."""
    logger.info(
        f"[handle_inbound_hi_on_request] Received on-request req={callback.requestId}, "
        f"correlated_to={callback.resp.requestId}, "
        f"status={callback.hiRequest.status if callback.hiRequest else 'ERROR'}"
    )
    return {
        "status": "RECEIVED",
        "requestId": str(callback.requestId),
        "correlatedRequestId": str(callback.resp.requestId),
    }


# ============================================================================
# Gateway Webhook Endpoints (Mounted under /v0.5)
# ============================================================================

@gateway_router.post(
    "/health-information/hip/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="ABDM Gateway Inbound Health Information Request",
    description="Processes inbound health information request from Gateway / HIU, verifies consent artefact, executes ECDH key agreement, and returns 202 Accepted while scheduling async on-request acknowledgement.",
)
async def gateway_inbound_health_information_request(
    payload: HIRequestPayload,
    background_tasks: BackgroundTasks,
    request_id: Optional[str] = Header(None, alias="REQUEST-ID"),
    timestamp: Optional[str] = Header(None, alias="TIMESTAMP"),
    x_cm_id: Optional[str] = Header(None, alias="X-CM-ID"),
) -> Dict[str, Any]:
    return await handle_inbound_hi_request(
        payload=payload,
        background_tasks=background_tasks,
        request_id=request_id,
        timestamp=timestamp,
        x_cm_id=x_cm_id,
    )


@gateway_router.post(
    "/health-information/hip/on-request",
    status_code=status.HTTP_200_OK,
    summary="ABDM Gateway Acknowledgement Callback Receiver",
)
async def gateway_inbound_health_information_on_request(
    callback: HIOnRequestCallback,
) -> Dict[str, Any]:
    return await handle_inbound_hi_on_request(callback)


# ============================================================================
# Local API Endpoints (Mounted under /api/v1/abdm/m3/crypto)
# ============================================================================

@router.post(
    "/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Direct API Alias for Inbound Health Information Request",
)
async def direct_inbound_health_information_request(
    payload: HIRequestPayload,
    background_tasks: BackgroundTasks,
    request_id: Optional[str] = Header(None, alias="REQUEST-ID"),
    timestamp: Optional[str] = Header(None, alias="TIMESTAMP"),
    x_cm_id: Optional[str] = Header(None, alias="X-CM-ID"),
) -> Dict[str, Any]:
    return await handle_inbound_hi_request(
        payload=payload,
        background_tasks=background_tasks,
        request_id=request_id,
        timestamp=timestamp,
        x_cm_id=x_cm_id,
    )


@router.post(
    "/on-request",
    status_code=status.HTTP_200_OK,
    summary="Direct API Alias for Acknowledgement Callback Receiver",
)
async def direct_inbound_health_information_on_request(
    callback: HIOnRequestCallback,
) -> Dict[str, Any]:
    return await handle_inbound_hi_on_request(callback)


@router.post(
    "/keys/generate",
    response_model=KeyGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Ephemeral Curve25519 Keypair & 32-Byte Nonce",
)
async def generate_ephemeral_key_pair() -> KeyGenerationResponse:
    """Generates an ephemeral Curve25519 key pair and CSPRNG 32-byte nonce."""
    _, b64_pub, b64_priv = AbdmCryptoService.generate_key_pair()
    _, b64_nonce = AbdmCryptoService.generate_nonce()

    return KeyGenerationResponse(
        publicKey=b64_pub,
        privateKey=b64_priv,
        nonce=b64_nonce,
        cryptoAlg="ECDH",
        curve="Curve25519",
    )


@router.post(
    "/exchange",
    response_model=KeyExchangeComputeResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute ECDH Shared Secret & HKDF-SHA256 Symmetric Key",
)
async def compute_key_exchange(
    req: KeyExchangeComputeRequest,
) -> KeyExchangeComputeResponse:
    """Computes full Diffie-Hellman shared secret and derived symmetric key for verification."""
    try:
        res = AbdmCryptoService.execute_key_exchange(
            local_private_key_b64=req.localPrivateKey,
            local_nonce_b64=req.localNonce,
            peer_public_key_b64=req.peerPublicKey,
            peer_nonce_b64=req.peerNonce,
        )
    except ValidationException as ve:
        raise HTTPException(status_code=400, detail=ve.message)
    except Exception as e:
        logger.error(f"[compute_key_exchange] Computation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Cryptographic computation failed: {str(e)}")

    return KeyExchangeComputeResponse(
        sharedSecretHex=res["shared_secret"].hex(),
        derivedKeyHex=res["derived_key"].hex(),
        saltHex=res["salt"].hex(),
        ivHex=res["iv"].hex(),
        status="SUCCESS",
    )


@router.get(
    "/sessions",
    response_model=List[CryptoSessionDetail],
    status_code=status.HTTP_200_OK,
    summary="List Active Cryptographic Sessions",
)
async def list_active_crypto_sessions() -> List[CryptoSessionDetail]:
    """Lists all unexpired cryptographic sessions stored in the HIP session cache."""
    return crypto_session_store.list_active_sessions()


@router.get(
    "/sessions/{transaction_id}",
    response_model=CryptoSessionDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Cryptographic Session by Transaction ID",
)
async def get_crypto_session(transaction_id: str) -> CryptoSessionDetail:
    """Retrieves session details for a specific data transfer transaction."""
    session = crypto_session_store.get_session(transaction_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Cryptographic session '{transaction_id}' not found or expired",
        )
    return session
