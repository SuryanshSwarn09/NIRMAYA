"""Immutable Cryptographic Audit Hash-Chain Ledger Service for NIRMAYA.

Implements an append-only, tamper-evident forensic ledger where each block is
cryptographically chained to its predecessor via SHA-256. Includes an automated
Merkle mathematical verification algorithm that detects retroactive ledger mutation.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
import threading
from typing import Any, Dict, List, Optional
import uuid

from app.schemas.audit_hash_chain import (
    AuditAppendRequest,
    AuditBlock,
    AuditChainVerificationResult,
    AuditEventType,
)

logger = logging.getLogger("nirmaya.audit_hash_chain")

GENESIS_PREV_HASH = "0" * 64
GENESIS_TIMESTAMP = "2026-09-01T00:00:00.000000+00:00"


def compute_payload_digest(payload: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hash of a structured payload."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_block_hash(
    index: int,
    block_id: str,
    previous_hash: str,
    timestamp: str,
    event_type: str,
    actor_id: str,
    payload_digest: str,
) -> str:
    """Calculates SHA-256 block hash over canonical concatenated fields."""
    canonical = f"{index}:{block_id}:{previous_hash}:{timestamp}:{event_type}:{actor_id}:{payload_digest}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AuditHashChainLedger:
    """Thread-safe cryptographic ledger storing append-only audit blocks."""

    def __init__(self) -> None:
        self._chain: List[AuditBlock] = []
        self._lock = threading.Lock()
        self._initialize_genesis_and_seed()

    def _initialize_genesis_and_seed(self) -> None:
        """Initializes Block 0 (Genesis) and seeds sample clinical audit events."""
        genesis_digest = compute_payload_digest(
            {"manifest": "NIRMAYA Unified Health Interoperability Network Genesis Block"}
        )
        genesis_id = "blk-genesis-00000000"
        genesis_hash = compute_block_hash(
            index=0,
            block_id=genesis_id,
            previous_hash=GENESIS_PREV_HASH,
            timestamp=GENESIS_TIMESTAMP,
            event_type=AuditEventType.SYSTEM_GENESIS.value,
            actor_id="system@nirmaya.local",
            payload_digest=genesis_digest,
        )

        genesis_block = AuditBlock(
            index=0,
            blockId=genesis_id,
            previousHash=GENESIS_PREV_HASH,
            timestamp=GENESIS_TIMESTAMP,
            eventType=AuditEventType.SYSTEM_GENESIS,
            actorId="system@nirmaya.local",
            payloadDigest=genesis_digest,
            blockHash=genesis_hash,
        )
        self._chain.append(genesis_block)

        # Seed sample subsequent event: Break-The-Glass access
        seed_btg_payload = {
            "patientAbha": "91-8472-1092-4821",
            "justification": "Unconscious polytrauma resuscitation",
            "department": "Emergency",
        }
        self._append_internal(
            event_type=AuditEventType.EMERGENCY_BTG_ACCESS,
            actor_id="doc-ananya-sharma",
            actor_hpr="ananya.sharma@hpr.abdm",
            facility_id="fac-aiims-delhi",
            patient_abha="91-8472-1092-4821",
            payload=seed_btg_payload,
            timestamp="2026-10-31T09:00:00.000000+00:00",
        )

        # Seed sample panic alert acknowledgement
        seed_panic_ack = {
            "alertId": "alt-seed-001",
            "test": "Serum Potassium",
            "action": "IV Calcium Gluconate administered",
        }
        self._append_internal(
            event_type=AuditEventType.LAB_PANIC_ACK,
            actor_id="doc-ananya-sharma",
            actor_hpr="ananya.sharma@hpr.abdm",
            facility_id="fac-aiims-delhi",
            patient_abha="91-8472-1092-4821",
            payload=seed_panic_ack,
            timestamp="2026-10-31T09:05:00.000000+00:00",
        )

    def _append_internal(
        self,
        event_type: AuditEventType,
        actor_id: str,
        payload: Dict[str, Any],
        actor_hpr: Optional[str] = None,
        facility_id: Optional[str] = None,
        patient_abha: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> AuditBlock:
        """Internal append helper assuming lock or init."""
        prev = self._chain[-1]
        new_index = prev.index + 1
        new_id = f"blk-{uuid.uuid4().hex[:12]}"
        now_ts = timestamp or datetime.now(timezone.utc).isoformat()
        digest = compute_payload_digest(payload)
        new_hash = compute_block_hash(
            index=new_index,
            block_id=new_id,
            previous_hash=prev.blockHash,
            timestamp=now_ts,
            event_type=event_type.value,
            actor_id=actor_id,
            payload_digest=digest,
        )

        block = AuditBlock(
            index=new_index,
            blockId=new_id,
            previousHash=prev.blockHash,
            timestamp=now_ts,
            eventType=event_type,
            actorId=actor_id,
            actorHpr=actor_hpr,
            facilityId=facility_id,
            patientAbha=patient_abha,
            payloadDigest=digest,
            blockHash=new_hash,
        )
        self._chain.append(block)
        return block

    def append_event(self, request: AuditAppendRequest) -> AuditBlock:
        """Appends an auditable transaction block to the immutable hash-chain."""
        with self._lock:
            return self._append_internal(
                event_type=request.eventType,
                actor_id=request.actorId,
                payload=request.payload,
                actor_hpr=request.actorHpr,
                facility_id=request.facilityId,
                patient_abha=request.patientAbha,
            )

    def verify_chain_integrity(self) -> AuditChainVerificationResult:
        """Traverses the full ledger verifying SHA-256 block hashes and sequential chaining.

        Returns detailed report indicating validity or pinpointing exact block and reason for tampering.
        """
        with self._lock:
            chain_copy = list(self._chain)

        if not chain_copy:
            return AuditChainVerificationResult(
                isValid=False,
                totalBlocksVerified=0,
                genesisHash="",
                latestHash="",
                tamperedBlockIndex=0,
                tamperingReason="Empty audit chain",
            )

        # 1. Verify Genesis Block (Index 0)
        genesis = chain_copy[0]
        if genesis.index != 0 or genesis.previousHash != GENESIS_PREV_HASH:
            return AuditChainVerificationResult(
                isValid=False,
                totalBlocksVerified=1,
                genesisHash=genesis.blockHash,
                latestHash=chain_copy[-1].blockHash,
                tamperedBlockIndex=0,
                tamperingReason="Genesis block previousHash is non-zero or index is corrupted",
            )

        expected_genesis_hash = compute_block_hash(
            index=0,
            block_id=genesis.blockId,
            previous_hash=GENESIS_PREV_HASH,
            timestamp=genesis.timestamp,
            event_type=genesis.eventType.value,
            actor_id=genesis.actorId,
            payload_digest=genesis.payloadDigest,
        )
        if genesis.blockHash != expected_genesis_hash:
            return AuditChainVerificationResult(
                isValid=False,
                totalBlocksVerified=1,
                genesisHash=genesis.blockHash,
                latestHash=chain_copy[-1].blockHash,
                tamperedBlockIndex=0,
                tamperingReason="Genesis block hash integrity verification failed",
            )

        # 2. Sequentially Verify Chained Blocks
        for i in range(1, len(chain_copy)):
            prev_block = chain_copy[i - 1]
            curr_block = chain_copy[i]

            # Verify Index Continuity
            if curr_block.index != i:
                return AuditChainVerificationResult(
                    isValid=False,
                    totalBlocksVerified=i,
                    genesisHash=genesis.blockHash,
                    latestHash=chain_copy[-1].blockHash,
                    tamperedBlockIndex=i,
                    tamperingReason=f"Broken sequence index: expected {i}, found {curr_block.index}",
                )

            # Verify Previous Hash Pointer
            if curr_block.previousHash != prev_block.blockHash:
                return AuditChainVerificationResult(
                    isValid=False,
                    totalBlocksVerified=i,
                    genesisHash=genesis.blockHash,
                    latestHash=chain_copy[-1].blockHash,
                    tamperedBlockIndex=i,
                    tamperingReason=(
                        f"Cryptographic hash chain broken at block {i}: "
                        f"previousHash '{curr_block.previousHash[:12]}...' does not match "
                        f"preceding block hash '{prev_block.blockHash[:12]}...'"
                    ),
                )

            # Verify Current Block Hash Recalculation
            recalculated_hash = compute_block_hash(
                index=curr_block.index,
                block_id=curr_block.blockId,
                previous_hash=curr_block.previousHash,
                timestamp=curr_block.timestamp,
                event_type=curr_block.eventType.value,
                actor_id=curr_block.actorId,
                payload_digest=curr_block.payloadDigest,
            )
            if curr_block.blockHash != recalculated_hash:
                return AuditChainVerificationResult(
                    isValid=False,
                    totalBlocksVerified=i,
                    genesisHash=genesis.blockHash,
                    latestHash=chain_copy[-1].blockHash,
                    tamperedBlockIndex=i,
                    tamperingReason=(
                        f"Payload or header alteration detected in block {i}: "
                        f"stored hash does not match recalculated SHA-256 digest"
                    ),
                )

        return AuditChainVerificationResult(
            isValid=True,
            totalBlocksVerified=len(chain_copy),
            genesisHash=genesis.blockHash,
            latestHash=chain_copy[-1].blockHash,
            tamperedBlockIndex=None,
            tamperingReason=None,
        )

    def get_blocks(self, limit: int = 50, offset: int = 0) -> List[AuditBlock]:
        """Returns chronological list of audit blocks (newest first)."""
        with self._lock:
            reversed_chain = list(reversed(self._chain))
        return reversed_chain[offset : offset + limit]

    def get_patient_blocks(self, patient_abha: str) -> List[AuditBlock]:
        """Returns all audit blocks associated with a specific patient ABHA."""
        with self._lock:
            return [b for b in reversed(self._chain) if b.patientAbha == patient_abha]


# Global singleton ledger instance
audit_ledger_service = AuditHashChainLedger()
