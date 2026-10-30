"""Pydantic schemas for ABDM Milestone 3 (M3) Encrypted Health Data Transfer Pipeline.

Conforms to NHA ABDM v0.5 Data Flow & Fidelius Specifications:
- Data Transfer Push Payload (POST {dataPushUrl} / /v0.5/health-information/transfer)
- Encrypted Data Entry (AES-256-GCM ciphertext + SHA-256 Checksum)
- Gateway Session Status Notification (POST /v0.5/health-information/notify)
- Diagnostic & testing utility schemas for direct encryption/decryption
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.abdm_m3_crypto import KeyMaterial


class EncryptedDataEntry(BaseModel):
    """Encrypted clinical record entry serialized as FHIR R4 JSON and encrypted with AES-256-GCM."""

    content: str = Field(description="Base64-encoded AES-256-GCM ciphertext with appended 128-bit authentication tag")
    media: str = Field(default="application/fhir+json", description="MIME type of encrypted payload")
    checksum: str = Field(description="Tamper-evident SHA-256 digest of original plaintext bundle")
    careContextReference: str = Field(description="Associated care context reference ID (e.g. ENC-2026-001)")

    model_config = ConfigDict(from_attributes=True)


class DataTransferPushPayload(BaseModel):
    """Health information data push payload sent by HIP directly to HIU dataPushUrl."""

    pageNumber: int = Field(default=1, description="Current data page index")
    pageCount: int = Field(default=1, description="Total pages in transfer")
    transactionId: uuid.UUID = Field(description="Correlation transaction ID established in /hip/request")
    entries: List[EncryptedDataEntry] = Field(description="List of encrypted clinical bundle entries")
    keyMaterial: KeyMaterial = Field(description="HIP's ephemeral Curve25519 public key and nonce")

    model_config = ConfigDict(from_attributes=True)


class DataTransferPushResponse(BaseModel):
    """Response returned upon dispatching data transfer push."""

    status: str = Field(default="SUCCESS", description="Transfer dispatch status: SUCCESS | FAILED")
    transactionId: str = Field(description="Correlation transaction ID")
    consentId: str = Field(description="Authorized consent artefact ID")
    entriesCount: int = Field(description="Number of clinical bundle entries packaged and pushed")
    dataPushUrl: str = Field(description="Destination URL where payload was delivered")
    deliveredAt: datetime = Field(description="UTC timestamp of delivery")
    message: str = Field(default="Health information successfully encrypted and transferred")

    model_config = ConfigDict(from_attributes=True)


class TransferNotifier(BaseModel):
    """Notifier entity identification for Gateway status update."""

    type: str = Field(default="HIP", description="Entity role: HIP | HIU")
    id: str = Field(description="Identifier of notifier (e.g. IN0410000123)")

    model_config = ConfigDict(from_attributes=True)


class TransferStatusResponse(BaseModel):
    """Per-care-context transfer status report."""

    careContextReference: str = Field(description="Care context identifier")
    hiStatus: str = Field(default="OK", description="Delivery status: OK | ERRORED")
    description: Optional[str] = Field(default="Transferred successfully", description="Status note")

    model_config = ConfigDict(from_attributes=True)


class TransferStatusNotification(BaseModel):
    """Status summary of overall transfer session."""

    sessionStatus: str = Field(default="TRANSFERRED", description="Session state: TRANSFERRED | FAILED")
    hipId: str = Field(description="HIP ID responsible for data transfer")
    statusResponses: List[TransferStatusResponse] = Field(description="Care context status list")

    model_config = ConfigDict(from_attributes=True)


class TransferNotificationDetail(BaseModel):
    """Notification body for ABDM Gateway /v0.5/health-information/notify."""

    consentId: str = Field(description="Consent artefact UUID")
    transactionId: str = Field(description="Correlation transaction ID")
    doneAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when data transfer concluded",
    )
    notifier: TransferNotifier = Field(description="Notifier details")
    statusNotification: TransferStatusNotification = Field(description="Status notification details")

    model_config = ConfigDict(from_attributes=True)


class DataTransferNotificationPayload(BaseModel):
    """ABDM Gateway Transfer Status Notification: POST /v0.5/health-information/notify."""

    requestId: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique UUID for this notification",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of notification dispatch",
    )
    notification: TransferNotificationDetail = Field(description="Transfer notification detail")

    model_config = ConfigDict(from_attributes=True)


class DirectEncryptRequest(BaseModel):
    """Testing utility schema for direct AES-256-GCM encryption."""

    plaintext: str = Field(description="Plaintext string or JSON to encrypt")
    keyHex: str = Field(description="Hex-encoded 32-byte (256-bit) symmetric AES key")
    ivHex: str = Field(description="Hex-encoded 12-byte (96-bit) IV")

    model_config = ConfigDict(from_attributes=True)


class DirectEncryptResponse(BaseModel):
    """Testing utility response for direct encryption."""

    ciphertext: str = Field(description="Base64-encoded ciphertext with appended 128-bit authentication tag")
    checksum: str = Field(description="SHA-256 digest of unencrypted plaintext")
    status: str = Field(default="SUCCESS")

    model_config = ConfigDict(from_attributes=True)


class DirectDecryptRequest(BaseModel):
    """Testing utility schema for direct AES-256-GCM decryption."""

    ciphertext: str = Field(description="Base64-encoded ciphertext with appended tag")
    keyHex: str = Field(description="Hex-encoded 32-byte symmetric AES key")
    ivHex: str = Field(description="Hex-encoded 12-byte IV")

    model_config = ConfigDict(from_attributes=True)


class DirectDecryptResponse(BaseModel):
    """Testing utility response for direct decryption."""

    plaintext: str = Field(description="Decrypted plaintext UTF-8 string")
    status: str = Field(default="SUCCESS")

    model_config = ConfigDict(from_attributes=True)


class TransferTriggerRequest(BaseModel):
    """Request model for manually triggering a health information data transfer."""

    transactionId: str = Field(description="Active transaction ID established in /hip/request")

    model_config = ConfigDict(from_attributes=True)


class TransferAuditRecord(BaseModel):
    """Audit log record for outgoing or incoming health data transfers."""

    id: str = Field(description="Audit entry UUID")
    transactionId: str = Field(description="Transaction ID")
    consentId: str = Field(description="Consent ID")
    direction: str = Field(description="OUTBOUND_PUSH | INBOUND_RECEIVE")
    entriesCount: int = Field(description="Number of bundles transferred")
    dataPushUrl: Optional[str] = Field(default=None, description="Destination URL")
    status: str = Field(default="SUCCESS", description="Transfer status: SUCCESS | FAILED")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of event",
    )

    model_config = ConfigDict(from_attributes=True)

