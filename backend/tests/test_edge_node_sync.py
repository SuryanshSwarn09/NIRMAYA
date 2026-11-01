"""Unit and integration test suite for Dual-Mode Edge Node Appliance & Offline Sync Engine.

Verifies:
- Append-only clinical event log recording with SHA-256 parent hash chaining
- Vector clock sequence ordering and tamper-evident Merkle root calculation
- Tamper detection on payload alteration or sequence breaks
- Store-and-forward batch push and pull synchronization workflows
- docker-compose.edge.yml low-resource constraint auditing (<512MB RAM budget)
- REST API endpoints under /api/v1/edge/*
"""

import copy
import hashlib
import json
import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.edge_sync import (
    ClinicalEventLogEntry,
    ClinicalEventType,
    EdgeNodeConfig,
    EdgeNodeTelemetry,
    SyncBatchRequest,
    SyncBatchResponse,
    SyncStateEnum,
)
from app.services.edge_sync_service import edge_sync_service


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide synchronous TestClient for edge REST API testing."""
    with TestClient(app) as test_client:
        yield test_client


# -----------------------------------------------------------------------------
# 1. Edge Node Configuration & Ledger Recording Tests
# -----------------------------------------------------------------------------


def test_edge_node_config_defaults():
    """Verify default edge node configuration specifies rural clinic parameters."""
    config = edge_sync_service.get_edge_config()
    assert isinstance(config, EdgeNodeConfig)
    assert "EDGE-PHC" in config.node_id
    assert config.facility_tier == "TIER_3_RURAL_CLINIC"
    assert config.storage_engine == "SQLITE_ENCRYPTED"
    assert config.sync_strategy == "STORE_AND_FORWARD"
    assert config.max_offline_retention_days >= 30


def test_clinical_event_recording_and_sha256():
    """Verify clinical events are recorded with deterministic SHA-256 digests."""
    entry = edge_sync_service.record_clinical_event(
        event_type=ClinicalEventType.OBSERVATION_RECORDED,
        aggregate_id="pat-test-101",
        payload={"systolicBp": 128, "diastolicBp": 82, "loinc": "8480-6"},
        author_id="doc-rural-01",
        facility_id="EDGE-PHC-BIHAR-042",
    )
    assert isinstance(entry, ClinicalEventLogEntry)
    assert entry.sequence_number >= 1
    assert entry.event_type == ClinicalEventType.OBSERVATION_RECORDED
    assert entry.aggregate_id == "pat-test-101"
    assert entry.sync_state == SyncStateEnum.PENDING_SYNC

    # Verify SHA-256 recomputation matches exactly
    recomputed_sha = hashlib.sha256(entry.payload_json.encode("utf-8")).hexdigest()
    assert entry.payload_sha256 == recomputed_sha


def test_event_hash_chain_sequential_integrity():
    """Verify hash chain verification confirms sequential integrity."""
    events = edge_sync_service._event_ledger
    assert len(events) >= 2
    is_valid, error = edge_sync_service.verify_event_hash_chain(events)
    assert is_valid is True
    assert error is None


def test_event_hash_chain_tamper_detection():
    """Verify tamper detection triggers when payload content is modified."""
    events_copy = copy.deepcopy(edge_sync_service._event_ledger)
    assert len(events_copy) >= 2

    # Tamper with the payload JSON without updating SHA-256
    events_copy[1].payload_json = json.dumps({"tampered": True})
    is_valid, error = edge_sync_service.verify_event_hash_chain(events_copy)
    assert is_valid is False
    assert "Integrity violation" in str(error)


def test_event_hash_chain_sequence_break_detection():
    """Verify detection when sequence numbers have an unexpected jump."""
    events_copy = copy.deepcopy(edge_sync_service._event_ledger)
    assert len(events_copy) >= 2

    events_copy[1].sequence_number = events_copy[0].sequence_number + 5
    is_valid, error = edge_sync_service.verify_event_hash_chain(events_copy)
    assert is_valid is False
    assert "Sequence break" in str(error)


def test_merkle_root_calculation():
    """Verify calculation of deterministic Merkle root hash across event digests."""
    merkle_root = edge_sync_service.compute_merkle_root()
    assert isinstance(merkle_root, str)
    assert len(merkle_root) == 64  # Valid 64-char hex SHA-256 string


# -----------------------------------------------------------------------------
# 2. Store-and-Forward Sync Batch Processing Tests
# -----------------------------------------------------------------------------


def test_sync_batch_push_valid():
    """Verify pushing valid append-only event batch advances server sequence."""
    events = edge_sync_service._event_ledger[:2]
    batch_req = SyncBatchRequest(
        node_id="EDGE-PHC-BIHAR-042",
        batch_id="batch-test-push-01",
        events=events,
        last_synced_sequence=0,
    )
    response = edge_sync_service.process_sync_batch_push(batch_req)
    assert isinstance(response, SyncBatchResponse)
    assert response.accepted_count == len(events)
    assert response.rejected_count == 0
    assert len(response.conflicts_detected) == 0


def test_sync_batch_push_tampered_rejected():
    """Verify pushing tampered batch results in rejection and conflict flag."""
    events_copy = copy.deepcopy(edge_sync_service._event_ledger[:2])
    events_copy[1].payload_json = json.dumps({"fraud": True})

    batch_req = SyncBatchRequest(
        node_id="EDGE-PHC-BIHAR-042",
        batch_id="batch-tampered-01",
        events=events_copy,
        last_synced_sequence=0,
    )
    response = edge_sync_service.process_sync_batch_push(batch_req)
    assert response.accepted_count == 0
    assert response.rejected_count == len(events_copy)
    assert len(response.conflicts_detected) > 0


def test_sync_batch_pull_differential():
    """Verify pulling updates returns server-side master clinical events."""
    response = edge_sync_service.generate_sync_batch_pull("EDGE-PHC-BIHAR-042", since_sequence=0)
    assert isinstance(response, SyncBatchResponse)
    assert response.accepted_count >= 1
    assert len(response.downstream_events) >= 1


# -----------------------------------------------------------------------------
# 3. Static Compose & File Auditing Tests
# -----------------------------------------------------------------------------


def test_edge_compose_static_audit():
    """Verify static analysis of docker-compose.edge.yml checks memory limits and SQLite."""
    result = edge_sync_service.audit_edge_compose_file()
    assert result["exists"] is True
    assert result["compliance_score_pct"] == 100.0
    assert result["has_sqlite_mode"] is True
    assert result["has_memory_limits"] is True
    assert result["has_caddy_gateway"] is True


def test_edge_compose_missing_handling():
    """Verify audit_edge_compose_file handles missing paths gracefully."""
    result = edge_sync_service.audit_edge_compose_file("/missing/docker-compose.edge.yml")
    assert result["exists"] is False
    assert result["compliance_score_pct"] == 0.0


def test_env_edge_example_structure():
    """Verify .env.edge.example contains critical edge keys."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    edge_env_path = os.path.join(base_dir, ".env.edge.example")
    assert os.path.exists(edge_env_path)

    with open(edge_env_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "NIRMAYA_NODE_ID=" in content
    assert "SQLITE_DB_PATH=" in content
    assert "UPLINK_URL=" in content
    assert "SECRET_KEY=" in content


# -----------------------------------------------------------------------------
# 4. REST API Endpoint Integration Tests
# -----------------------------------------------------------------------------


def test_rest_api_edge_status(client: TestClient):
    """Verify GET /api/v1/edge/status returns telemetry and storage metrics."""
    response = client.get("/api/v1/edge/status")
    assert response.status_code == 200
    data = response.json()
    assert "node_id" in data
    assert "pending_events_count" in data
    assert "local_storage_used_mb" in data
    assert "merkle_root_hash" in data
    assert response.headers.get("X-Security-Standard") is not None


def test_rest_api_edge_config(client: TestClient):
    """Verify GET /api/v1/edge/config returns edge appliance manifest."""
    response = client.get("/api/v1/edge/config")
    assert response.status_code == 200
    data = response.json()
    assert data["facility_tier"] == "TIER_3_RURAL_CLINIC"
    assert data["storage_engine"] == "SQLITE_ENCRYPTED"


def test_rest_api_edge_audit(client: TestClient):
    """Verify GET /api/v1/edge/audit returns 100% compliance."""
    response = client.get("/api/v1/edge/audit")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["compliance_score_pct"] == 100.0


def test_rest_api_edge_push_and_pull(client: TestClient):
    """Verify end-to-end REST push and pull synchronization workflows."""
    events_payload = [e.model_dump(mode="json") for e in edge_sync_service._event_ledger[:1]]
    push_body = {
        "node_id": "EDGE-PHC-BIHAR-042",
        "batch_id": "rest-push-test-01",
        "events": events_payload,
        "last_synced_sequence": 0,
        "dispatched_at": "2026-11-01T06:00:00Z",
    }
    push_resp = client.post("/api/v1/edge/sync/push", json=push_body)
    assert push_resp.status_code == 200
    push_data = push_resp.json()
    assert push_data["accepted_count"] == 1

    pull_resp = client.post("/api/v1/edge/sync/pull?node_id=EDGE-PHC-BIHAR-042&since_sequence=0")
    assert pull_resp.status_code == 200
    pull_data = pull_resp.json()
    assert pull_data["accepted_count"] >= 1

