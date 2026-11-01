"""Pydantic v2 schemas for Dual-Mode Edge Node Appliance & Local-First Clinical Event Log.

Provides structured models for:
- Append-only clinical event logging with SHA-256 parent hash chaining
- Store-and-forward synchronization between edge clinic nodes and cloud/district servers
- Differential push/pull sync batch payloads and conflict detection
- Edge node hardware configuration, storage metrics, and sync health telemetry
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SyncStateEnum(str, Enum):
    """Synchronization lifecycle state of an edge event or appliance."""

    LOCAL_ONLY = "local_only"
    PENDING_SYNC = "pending_sync"
    SYNCING = "syncing"
    SYNCED = "synced"
    CONFLICT_DETECTED = "conflict_detected"


class ClinicalEventType(str, Enum):
    """Categorization of clinical domain events captured in the offline log."""

    PATIENT_REGISTRATION = "patient_registration"
    ENCOUNTER_CREATED = "encounter_created"
    OBSERVATION_RECORDED = "observation_recorded"
    SOAP_NOTE_SAVED = "soap_note_saved"
    PRESCRIPTION_ISSUED = "prescription_issued"
    DIAGNOSTIC_ORDER = "diagnostic_order"


class ClinicalEventLogEntry(BaseModel):
    """Cryptographically linked record in the append-only clinical event ledger."""

    model_config = ConfigDict(from_attributes=True)

    event_id: str = Field(
        ...,
        description="Unique UUID identifying this discrete clinical action",
    )
    sequence_number: int = Field(
        ...,
        ge=1,
        description="Strictly monotonically increasing integer sequence for vector clock ordering",
    )
    event_type: ClinicalEventType = Field(
        ...,
        description="Type of clinical domain mutation",
    )
    aggregate_id: str = Field(
        ...,
        description="ID of the parent entity (e.g. Patient ID, Appointment ID)",
    )
    payload_json: str = Field(
        ...,
        description="Deterministic JSON serialization of event data",
    )
    payload_sha256: str = Field(
        ...,
        description="SHA-256 digest of payload_json verifying data integrity",
    )
    prev_event_hash: str = Field(
        ...,
        description="SHA-256 hash of predecessor event in the append-only ledger",
    )
    author_id: str = Field(
        ...,
        description="Clinician or administrative user who originated the event",
    )
    facility_id: str = Field(
        ...,
        description="Edge clinic or PHC facility identifier",
    )
    local_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Device wall-clock timestamp when event was authored",
    )
    sync_state: SyncStateEnum = Field(
        SyncStateEnum.PENDING_SYNC,
        description="Current synchronization status",
    )


class EdgeNodeConfig(BaseModel):
    """Hardware and operational configuration parameters for an edge appliance."""

    model_config = ConfigDict(from_attributes=True)

    node_id: str = Field(
        "EDGE-PHC-BIHAR-042",
        description="Unique cryptographic hardware identifier for the clinic node",
    )
    facility_name: str = Field(
        "Primary Health Center Bikramganj",
        description="Human-readable clinic name",
    )
    facility_tier: str = Field(
        "TIER_3_RURAL_CLINIC",
        description="Administrative facility classification tier",
    )
    storage_engine: str = Field(
        "SQLITE_ENCRYPTED",
        description="Underlying local embedded database engine (SQLite with AES-256)",
    )
    sync_strategy: str = Field(
        "STORE_AND_FORWARD",
        description="Synchronization protocol pattern",
    )
    max_offline_retention_days: int = Field(
        90,
        description="Maximum days to buffer clinical event logs before forced purge",
    )
    uplink_endpoint: str = Field(
        "https://api.nirmaya.health/api/v1/edge/sync",
        description="Central cloud or district uplink synchronization endpoint",
    )
    auto_sync_interval_seconds: int = Field(
        300,
        description="Frequency of background uplink connection probe in seconds",
    )


class SyncBatchRequest(BaseModel):
    """Payload dispatched by edge appliance to push accumulated offline events to cloud."""

    model_config = ConfigDict(from_attributes=True)

    node_id: str = Field(
        ...,
        description="Originating edge appliance identifier",
    )
    batch_id: str = Field(
        ...,
        description="Unique UUID identifying this synchronization batch",
    )
    events: List[ClinicalEventLogEntry] = Field(
        default_factory=list,
        description="Batch of append-only clinical event entries to be merged",
    )
    last_synced_sequence: int = Field(
        ...,
        ge=0,
        description="Highest sequence number previously confirmed by central server",
    )
    dispatched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of sync dispatch",
    )


class SyncBatchResponse(BaseModel):
    """Acknowledgment and downstream delta response returned by central server."""

    model_config = ConfigDict(from_attributes=True)

    batch_id: str = Field(
        ...,
        description="Identifier of the processed sync batch",
    )
    accepted_count: int = Field(
        ...,
        ge=0,
        description="Count of events successfully merged into central store",
    )
    rejected_count: int = Field(
        ...,
        ge=0,
        description="Count of events rejected due to hash verification or schema errors",
    )
    latest_server_sequence: int = Field(
        ...,
        ge=0,
        description="Current server-side global sequence sequence number",
    )
    conflicts_detected: List[str] = Field(
        default_factory=list,
        description="Event IDs requiring conflict resolution traversal",
    )
    downstream_events: List[ClinicalEventLogEntry] = Field(
        default_factory=list,
        description="Server events (e.g. formulary updates, state directives) to pull to edge",
    )
    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of batch processing completion",
    )


class EdgeNodeTelemetry(BaseModel):
    """Telemetry report describing live sync health, buffer depth, and storage consumption."""

    model_config = ConfigDict(from_attributes=True)

    node_id: str = Field(
        ...,
        description="Edge appliance node identifier",
    )
    is_online: bool = Field(
        ...,
        description="True if uplink connection to central cloud is active",
    )
    sync_state: SyncStateEnum = Field(
        ...,
        description="Current operational sync mode",
    )
    pending_events_count: int = Field(
        ...,
        ge=0,
        description="Count of uncommitted offline events in local queue",
    )
    committed_events_count: int = Field(
        ...,
        ge=0,
        description="Count of events confirmed synced to cloud",
    )
    local_storage_used_mb: float = Field(
        ...,
        description="Disk space consumed by local encrypted database in megabytes",
    )
    local_storage_limit_mb: float = Field(
        500.0,
        description="Allocated local storage budget in megabytes",
    )
    last_sync_timestamp: Optional[datetime] = Field(
        None,
        description="Timestamp of last successful bidirectional sync exchange",
    )
    avg_sync_duration_ms: float = Field(
        ...,
        description="Average round-trip sync batch latency in milliseconds",
    )
    merkle_root_hash: str = Field(
        ...,
        description="Current SHA-256 Merkle root hash of the local event log",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of telemetry evaluation",
    )
