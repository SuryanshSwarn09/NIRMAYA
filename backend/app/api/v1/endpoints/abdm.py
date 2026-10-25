"""ABDM Gateway Interoperability & Cryptographic Service Endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.abdm.client import ABDMGatewayClient, get_abdm_gateway_client
from app.abdm.security.rsa import ABDMRSAEncryptionManager, get_abdm_encryption_manager
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.abdm import (
    ABDMEncryptedResponse,
    ABDMEncryptionPayload,
    GatewayStatusResponse,
)

router = APIRouter(prefix="/abdm", tags=["ABDM Gateway & National Interoperability"])


class DecryptRequest(BaseModel):
    """Payload containing ciphertext to decrypt."""

    ciphertext: str = Field(description="Base64 encoded RSA-OAEP ciphertext")


class PublicKeyResponse(BaseModel):
    """Export of ABDM public key configuration."""

    public_key_pem: str = Field(description="PEM-encoded RSA-2048 public key")
    fingerprint: str = Field(description="SHA-256 hex fingerprint of SubjectPublicKeyInfo")
    algorithm: str = Field(default="RSA-OAEP-256", description="Encryption algorithm specification")


@router.get(
    "/status",
    response_model=APIResponse[GatewayStatusResponse],
    summary="Get ABDM Gateway connectivity and session status",
    description="Returns the connection health, current session token validity, and RSA cryptographic readiness.",
)
async def get_gateway_status(
    gateway_client: ABDMGatewayClient = Depends(get_abdm_gateway_client),
) -> APIResponse[GatewayStatusResponse]:
    """Retrieve ABDM Gateway connectivity, token health, and sandbox state."""
    status_data = await gateway_client.get_gateway_status()
    return APIResponse(
        success=True,
        data=status_data,
        message="ABDM Gateway status retrieved successfully",
    )


@router.post(
    "/sessions/refresh",
    response_model=APIResponse[GatewayStatusResponse],
    summary="Force refresh ABDM Gateway session bearer token",
    description="Acquires a fresh bearer access token from /v0.5/sessions, bypassing cache.",
)
async def refresh_gateway_session(
    current_user: User = Depends(get_current_user),
    gateway_client: ABDMGatewayClient = Depends(get_abdm_gateway_client),
) -> APIResponse[GatewayStatusResponse]:
    """Force acquisition of a fresh session token from the ABDM Gateway."""
    await gateway_client.get_session_token(force_refresh=True)
    status_data = await gateway_client.get_gateway_status()
    return APIResponse(
        success=True,
        data=status_data,
        message="ABDM Gateway session token refreshed successfully",
    )


@router.get(
    "/crypto/public-key",
    response_model=APIResponse[PublicKeyResponse],
    summary="Get ABDM Gateway RSA-2048 public key certificate",
    description="Returns the active public key in PEM format along with its SHA-256 fingerprint.",
)
def get_public_key(
    crypto_mgr: ABDMRSAEncryptionManager = Depends(get_abdm_encryption_manager),
) -> APIResponse[PublicKeyResponse]:
    """Export active RSA public key for demographic encryption verification."""
    pem = crypto_mgr.get_public_key_pem()
    fp = crypto_mgr.get_public_key_fingerprint()
    return APIResponse(
        success=True,
        data=PublicKeyResponse(public_key_pem=pem, fingerprint=fp),
        message="ABDM RSA public key exported successfully",
    )


@router.post(
    "/crypto/encrypt-demographics",
    response_model=APIResponse[ABDMEncryptedResponse],
    summary="Encrypt demographic data using ABDM RSA-OAEP SHA-256",
    description="Encrypts patient demographic attributes conforming to National Health Authority (NHA) specifications.",
)
def encrypt_demographics(
    payload: ABDMEncryptionPayload,
    crypto_mgr: ABDMRSAEncryptionManager = Depends(get_abdm_encryption_manager),
) -> APIResponse[ABDMEncryptedResponse]:
    """Encrypt a demographic dictionary using the active ABDM RSA public key."""
    try:
        ciphertext = crypto_mgr.encrypt_demographic_payload(payload.demographic_data)
        return APIResponse(
            success=True,
            data=ABDMEncryptedResponse(encrypted_data=ciphertext),
            message="Demographic data encrypted successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to encrypt demographic payload: {str(e)}",
        )


@router.post(
    "/crypto/decrypt-demographics",
    response_model=APIResponse[Dict[str, Any]],
    summary="Decrypt demographic ciphertext using ABDM RSA private key",
    description="Decrypts an RSA-OAEP base64 ciphertext and reconstructs the demographic dictionary.",
)
def decrypt_demographics(
    payload: DecryptRequest,
    current_user: User = Depends(get_current_user),
    crypto_mgr: ABDMRSAEncryptionManager = Depends(get_abdm_encryption_manager),
) -> APIResponse[Dict[str, Any]]:
    """Decrypt demographic ciphertext using the active ABDM RSA private key."""
    try:
        decrypted_dict = crypto_mgr.decrypt_demographic_payload(payload.ciphertext)
        return APIResponse(
            success=True,
            data=decrypted_dict,
            message="Demographic data decrypted successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decrypt demographic payload: {str(e)}",
        )
