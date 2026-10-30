"""Pydantic schemas for ABDM Milestone 3 (M3) Compliance Audit & Certification.

Defines schemas for real-time telemetry, cryptographic parity metrics,
consent ingestion metrics, encrypted transfer counts, and HIU consumer metrics
as per NHA ABDM v0.5 Data Flow and Fidelius specifications.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ConsentAuditMetrics(BaseModel):
    """Aggregated consent artefact metrics across HIP consent registry."""

    totalIngested: int = Field(..., description="Total consent notifications received and processed")
    activeGranted: int = Field(..., description="Currently active valid GRANTED consents")
    revoked: int = Field(..., description="Total consents explicitly revoked")
    expired: int = Field(..., description="Total consents expired past dataEraseAt")
    denied: int = Field(default=0, description="Total consents denied or invalid")


class CryptoAuditMetrics(BaseModel):
    """Cryptographic operations and NHA Fidelius parity metrics."""

    totalKeyAgreements: int = Field(..., description="Total Diffie-Hellman key exchanges performed")
    activeKeySessions: int = Field(..., description="Currently active unexpired key sessions")
    curveStandard: str = Field(
        default="Curve25519 (X25519)",
        description="Elliptic curve algorithm for ephemeral key agreement",
    )
    kdfStandard: str = Field(
        default="HKDF-SHA256",
        description="Key derivation function for symmetric key derivation",
    )
    cipherStandard: str = Field(
        default="AES-256-GCM (128-bit Tag)",
        description="Authenticated symmetric encryption algorithm",
    )
    parityScorePercentage: float = Field(
        default=100.0,
        description="NHA Fidelius cryptographic parity score (0.0-100.0)",
    )


class TransferAuditMetrics(BaseModel):
    """Data transfer push and gateway notification metrics as HIP provider."""

    totalTransfersDispatched: int = Field(..., description="Total data push requests dispatched as HIP")
    totalTransferredBatches: int = Field(..., description="Total batches successfully transferred")
    totalTransferredRecords: int = Field(..., description="Total FHIR clinical bundles pushed")
    totalTransferErrors: int = Field(..., description="Total transfer transmission failures")
    deliverySuccessRatePercentage: float = Field(
        default=100.0,
        description="Percentage of successful data transfer dispatches",
    )


class HIUConsumerAuditMetrics(BaseModel):
    """Health Information User (HIU) data consumer engine telemetry."""

    totalRequestsInitiated: int = Field(..., description="Total outbound HI requests initiated as HIU")
    activeHIUSessions: int = Field(..., description="Currently pending unexpired HIU sessions")
    totalBundlesDecrypted: int = Field(..., description="Total encrypted FHIR bundles decrypted and verified")
    totalEncountersImported: int = Field(..., description="Total clinical encounters extracted and indexed")
    totalPrescriptionsImported: int = Field(..., description="Total prescriptions extracted and indexed")
    totalDiagnosticReportsImported: int = Field(..., description="Total diagnostic reports extracted and indexed")
    totalObservationsImported: int = Field(..., description="Total clinical observations extracted and indexed")
    tamperRejections: int = Field(..., description="Total tampered or forged payloads rejected")
    integrityScorePercentage: float = Field(
        default=100.0,
        description="Cryptographic integrity and checksum verification score (0.0-100.0)",
    )


class AbdmM3AuditReport(BaseModel):
    """Standardized ABDM Milestone 3 Compliance Audit & Telemetry Report."""

    hipId: str = Field(..., description="Accredited Health Information Provider (HIP) Facility ID")
    hiuId: str = Field(..., description="Accredited Health Information User (HIU) Facility ID")
    gatewayConsentManagerId: str = Field(..., description="Gateway Consent Manager routing ID")
    status: str = Field(
        default="ABDM_M3_CERTIFIED",
        description="Milestone 3 certification and compliance status",
    )
    milestone: str = Field(
        default="Milestone 3: Health Information Exchange & Consent Management",
        description="Milestone title",
    )
    complianceStandard: str = Field(
        default="NHA ABDM v0.5 Data Flow & Fidelius Cryptographic Specifications",
        description="Authoritative regulatory standard",
    )
    consents: ConsentAuditMetrics = Field(..., description="Consent registry metrics")
    cryptography: CryptoAuditMetrics = Field(..., description="Cryptographic session telemetry")
    dataTransfers: TransferAuditMetrics = Field(..., description="HIP outbound transfer telemetry")
    hiuConsumer: HIUConsumerAuditMetrics = Field(..., description="HIU inbound ingestion telemetry")
    activeWebhookListeners: List[str] = Field(
        ...,
        description="List of registered ABDM M3 gateway and data webhook routes",
    )
    auditTimestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of audit report compilation",
    )
    version: str = Field(default="0.3.0-alpha.w11", description="Software release version")
    environment: str = Field(default="sandbox", description="Operating environment")
