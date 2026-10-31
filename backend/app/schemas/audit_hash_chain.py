"""Cryptographic Audit Hash-Chain and Emergency Notification Schemas for NIRMAYA.

Defines models for:
1. Immutable SHA-256 hash-chained forensic audit blocks.
2. Mathematical Merkle audit chain verification results.
3. Emergency contact SMS dispatch records and carrier payloads.
4. High-concurrency WebSocket stress test metrics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class AuditEventType(str, Enum):
    """Classification of auditable system, security, and clinical transactions."""

    SYSTEM_GENESIS = "SYSTEM_GENESIS"
    EMERGENCY_BTG_ACCESS = "EMERGENCY_BTG_ACCESS"
    LAB_PANIC_ACK = "LAB_PANIC_ACK"
    CONSULTATION_QUEUE_TRANSITION = "CONSULTATION_QUEUE_TRANSITION"
    PHI_RECORD_EXPORT = "PHI_RECORD_EXPORT"
    CONSENT_REVOCATION = "CONSENT_REVOCATION"
    PRESCRIPTION_SIGN = "PRESCRIPTION_SIGN"
    CRITICAL_ALERT_DISPATCH = "CRITICAL_ALERT_DISPATCH"


class AuditBlock(BaseModel):
    """Immutable forensic audit block cryptographically chained to its predecessor."""

    index: int = Field(description="Monotonically increasing sequence number (0 = Genesis)")
    blockId: str = Field(description="Unique block identifier")
    previousHash: str = Field(description="SHA-256 hash digest of the preceding block in the chain")
    timestamp: str = Field(description="ISO 8601 UTC timestamp of block creation")
    eventType: AuditEventType = Field(description="Auditable clinical or security event category")
    actorId: str = Field(description="User or service identity executing the transaction")
    actorHpr: Optional[str] = Field(default=None, description="National Healthcare Professional Registry address")
    facilityId: Optional[str] = Field(default=None, description="Healthcare facility or clinic identifier")
    patientAbha: Optional[str] = Field(default=None, description="Subject patient ABHA identifier if applicable")
    payloadDigest: str = Field(description="SHA-256 digest of the structured transaction payload")
    blockHash: str = Field(description="Cryptographic SHA-256 seal of this block")

    model_config = ConfigDict(from_attributes=True)


class AuditAppendRequest(BaseModel):
    """Payload to record an auditable event in the hash-chain ledger."""

    eventType: AuditEventType = Field(description="Event classification")
    actorId: str = Field(description="Actor identity executing transaction")
    actorHpr: Optional[str] = Field(default=None, description="Actor HPR address")
    facilityId: Optional[str] = Field(default=None, description="Facility identifier")
    patientAbha: Optional[str] = Field(default=None, description="Patient ABHA")
    payload: Dict[str, Any] = Field(description="Arbitrary structured event payload to hash and seal")

    model_config = ConfigDict(from_attributes=True)


class AuditChainVerificationResult(BaseModel):
    """Detailed cryptographic audit report returned by ledger verification engine."""

    isValid: bool = Field(description="Whether the entire hash chain is cryptographically unbroken")
    totalBlocksVerified: int = Field(description="Total blocks verified from Genesis to Head")
    genesisHash: str = Field(description="Cryptographic digest of block index 0")
    latestHash: str = Field(description="Cryptographic digest of the current head block")
    tamperedBlockIndex: Optional[int] = Field(default=None, description="Index of corrupted block if detected")
    tamperingReason: Optional[str] = Field(default=None, description="Diagnostic reason for chain invalidity")
    verifiedAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of verification run",
    )

    model_config = ConfigDict(from_attributes=True)


class EmergencyDispatchMessage(BaseModel):
    """Dispatched emergency SMS notification record sent to patient next of kin."""

    dispatchId: str = Field(
        default_factory=lambda: f"disp-{uuid.uuid4().hex[:12]}",
        description="Unique dispatch identifier",
    )
    patientAbha: str = Field(description="14-digit patient ABHA number")
    patientName: str = Field(description="Patient full display name")
    contactName: str = Field(description="Emergency contact person name")
    contactPhone: str = Field(description="Emergency contact telephone number")
    relationship: str = Field(description="Relationship to patient (e.g. Spouse, Parent)")
    hospitalName: str = Field(description="Admitting hospital facility name")
    doctorName: str = Field(description="Attending emergency physician name")
    departmentPhone: str = Field(description="Emergency department telephone number")
    messageText: str = Field(description="Full text of the dispatched emergency SMS")
    deliveryStatus: str = Field(default="DELIVERED", description="Carrier delivery state: DELIVERED, SENT, FAILED")
    gatewayReferenceId: str = Field(description="Simulated carrier message gateway reference ID")
    dispatchTimestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC dispatch timestamp",
    )

    model_config = ConfigDict(from_attributes=True)


class EmergencyDispatchTestRequest(BaseModel):
    """Payload to trigger a simulated emergency contact notification dispatch."""

    patientAbha: str = Field(description="Patient ABHA number")
    patientName: str = Field(description="Patient full display name")
    contactName: str = Field(description="Emergency contact name")
    contactPhone: str = Field(description="Contact phone number")
    relationship: str = Field(default="Family Member", description="Relationship")
    hospitalName: str = Field(default="AIIMS New Delhi - Apex Trauma Center", description="Hospital name")
    doctorName: str = Field(default="Dr. Ananya Sharma", description="Attending clinician name")
    departmentPhone: str = Field(default="+91 11 2659 8700", description="Emergency triage phone")

    model_config = ConfigDict(from_attributes=True)


class ConcurrencyBenchmarkMetrics(BaseModel):
    """Performance telemetry from high-concurrency WebSocket stress test harness."""

    concurrentClients: int = Field(description="Total simultaneous active client connections")
    messagesDispatched: int = Field(description="Total messages broadcast over Pub/Sub")
    messagesReceived: int = Field(description="Total messages successfully received across all clients")
    averageLatencyMs: float = Field(description="Average delivery latency in milliseconds")
    p99LatencyMs: float = Field(description="99th percentile delivery latency in milliseconds")
    packetLossRate: float = Field(description="Packet loss ratio (0.0 to 1.0)")
    durationSeconds: float = Field(description="Benchmark run duration in seconds")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC execution timestamp",
    )

    model_config = ConfigDict(from_attributes=True)
