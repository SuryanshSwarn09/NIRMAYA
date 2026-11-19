# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/edge_sync.py`
**Audited Path:** `backend/app/schemas/edge_sync.py`  
**Module:** `backend` | **Subsystem:** Edge Appliance & Offline Synchronization Engine  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/edge_sync.py` provides the canonical Pydantic v2 schemas for NIRMAYA's dual-mode edge node appliance and local-first clinical event log architecture. It structures data serialization for rural clinics, primary health centers (PHCs), and sub-district health posts operating under intermittent or absent internet connectivity. The schema defines:
- The append-only clinical mutation ledger (`ClinicalEventLogEntry`) featuring SHA-256 parent hash chaining and monotonically increasing sequence counters for Lamport/vector clock ordering.
- Store-and-forward differential batch payloads (`SyncBatchRequest`, `SyncBatchResponse`) for bidirectional uplink push/pull between edge nodes and cloud central instances.
- Hardware configuration parameters (`EdgeNodeConfig`) and operational health telemetry (`EdgeNodeTelemetry`), including storage watermarks and Merkle tree root digests.

#### 2. Key Components & Class Roster
- `SyncStateEnum`: Enumerates synchronization lifecycle states (`local_only`, `pending_sync`, `syncing`, `synced`, `conflict_detected`).
- `ClinicalEventType`: Categorizes discrete domain mutations captured offline (`patient_registration`, `encounter_created`, `observation_recorded`, `soap_note_saved`, `prescription_issued`, `diagnostic_order`).
- `ClinicalEventLogEntry`: The fundamental append-only cryptographic event record tracking `event_id`, `sequence_number`, `payload_json`, `payload_sha256`, `prev_event_hash`, `author_id`, and `facility_id`.
- `EdgeNodeConfig`: Edge appliance identity and runtime parameters (`node_id`, `facility_tier`, `storage_engine`, `max_offline_retention_days`, `uplink_endpoint`, `auto_sync_interval_seconds`).
- `SyncBatchRequest`: Payload dispatched by edge appliances to push uncommitted offline event batches to cloud or district relays.
- `SyncBatchResponse`: Central acknowledgment schema returning merge statistics (`accepted_count`, `rejected_count`), global sequence anchors, conflict identifiers, and downstream server-to-edge deltas.
- `EdgeNodeTelemetry`: Real-time health report tracking uplink online status, uncommitted queue depths, encrypted storage consumption in megabytes, latency metrics, and local Merkle root hashes.

---

### Layer B: Plain-Language Developer Walkthrough

Imagine a primary health clinic located in a remote mountainous or rural district where internet access drops for days at a time. Doctors and nurses still need to register patients, record vitals, write clinical encounter notes, and dispense medications. 

`edge_sync.py` provides the formal blueprints for the edge computer sitting in that clinic. Every time a clinician performs an action, it is packaged as a `ClinicalEventLogEntry`. This is essentially a block in a micro-blockchain: it contains the clinical data, a SHA-256 fingerprint of that data, and a fingerprint of the immediately preceding event (`prev_event_hash`). This ensures that records cannot be altered or inserted out of order while the clinic is disconnected.

When cellular or satellite connectivity is temporarily restored, the edge appliance gathers all pending entries into a `SyncBatchRequest` and dispatches them to the NIRMAYA central server. The server verifies each cryptographic link, reconciles sequence numbers, stores the new clinical data, and replies with a `SyncBatchResponse` containing any updates originating from the cloud (such as newly updated drug formularies or patient identity verifications). Additionally, the edge node periodically transmits an `EdgeNodeTelemetry` ping so regional IT supervisors can monitor remaining disk capacity and queue depth before an edge appliance runs out of storage space.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **Cryptographic Hash Chaining:** `ClinicalEventLogEntry` implements an immutable hash chain via `payload_sha256` and `prev_event_hash`. Every mutation commits to the prior event's state, preventing silent log manipulation or truncation during offline buffering.
- **Vector Sequencing:** `sequence_number` utilizes `ge=1` to enforce strict positive monotonic sequence growth per edge node, providing deterministic conflict detection.
- **ORM Independence:** Schemas specify `ConfigDict(from_attributes=True)` enabling direct deserialization from local SQLite / SQLCipher tables to wire transfer envelopes.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Unmasked PHI in Event Payload Logs (`BE-SCH-EDGE-F01`)
- **Severity:** S2 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/edge_sync.py:59-62`
- **Description:** `payload_json` contains deterministic JSON strings representing raw patient registrations, clinical observations, diagnoses, and prescriptions. In Pydantic v2, printing or logging `ClinicalEventLogEntry` or `SyncBatchRequest` (e.g. in FastAPI exception handlers, audit middleware, or debug logging) prints the full string representation of `payload_json`, exposing sensitive Personal Health Information (PHI) in plaintext logs.
- **Impact:** Compromises patient confidentiality in centralized logging pipelines (CWE-532).
- **Remediation:** Mark `payload_json` with `repr=False` in its `Field` definition.

##### Vulnerability 2: Missing Cryptographic Digest Format Constraints (`BE-SCH-EDGE-F02`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/edge_sync.py:63-70`, `237-240`
- **Description:** Fields `payload_sha256`, `prev_event_hash`, and `merkle_root_hash` are typed as generic `str` without length constraints or hex pattern matching. An edge node or intermediary proxy could inject malformed strings, empty strings, or non-hex digests without triggering validation errors.
- **Impact:** Downstream cryptographic verification services may fail unexpectedly or accept corrupted chain states.
- **Remediation:** Enforce `pattern=r"^[a-fA-F0-9]{64}$"` and `min_length=64, max_length=64` on all SHA-256 hash fields.

##### Vulnerability 3: Unvalidated HTTP URL in Edge Node Configuration (`BE-SCH-EDGE-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/edge_sync.py:118-121`
- **Description:** `uplink_endpoint` in `EdgeNodeConfig` is declared as a plain `str` rather than `AnyHttpUrl` or `HttpUrl`, allowing invalid or non-HTTP URIs to pass schema validation.
- **Impact:** Misconfigured edge nodes could fail during sync synchronization dispatch with unhandled URI scheme exceptions.
- **Remediation:** Utilize Pydantic's `HttpUrl` or validate schema prefixes.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-EDGE-F01` | S2 | `[SEC]` | `edge_sync.py:59-62` | Unmasked raw clinical JSON payload in `ClinicalEventLogEntry.payload_json` exposed in `repr` |
| `BE-SCH-EDGE-F02` | S2 | `[QUAL]` | `edge_sync.py:63-70, 237-240` | SHA-256 hash digests lack 64-character hex regex validation |
| `BE-SCH-EDGE-F03` | S3 | `[QUAL]` | `edge_sync.py:118-121` | `uplink_endpoint` uses unvalidated string instead of strict URL type |
| `BE-SCH-EDGE-F04` | S3 | `[QUAL]` | `edge_sync.py:221-224` | `local_storage_used_mb` lacks `ge=0.0` non-negative constraint |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/edge_sync.py
+++ b/backend/app/schemas/edge_sync.py
@@ -10,7 +10,7 @@ from datetime import datetime, timezone
 from enum import Enum
 from typing import Dict, List, Optional
-from pydantic import BaseModel, ConfigDict, Field
+from pydantic import BaseModel, ConfigDict, Field, HttpUrl
 
 
 class SyncStateEnum(str, Enum):
@@ -59,14 +59,19 @@ class ClinicalEventLogEntry(BaseModel):
     payload_json: str = Field(
         ...,
+        repr=False,
         description="Deterministic JSON serialization of event data",
     )
     payload_sha256: str = Field(
         ...,
+        pattern=r"^[a-fA-F0-9]{64}$",
+        min_length=64,
+        max_length=64,
         description="SHA-256 digest of payload_json verifying data integrity",
     )
     prev_event_hash: str = Field(
         ...,
+        pattern=r"^[a-fA-F0-9]{64}$",
+        min_length=64,
+        max_length=64,
         description="SHA-256 hash of predecessor event in the append-only ledger",
     )
     author_id: str = Field(
@@ -118,7 +123,7 @@ class EdgeNodeConfig(BaseModel):
-    uplink_endpoint: str = Field(
+    uplink_endpoint: HttpUrl = Field(
         "https://api.nirmaya.health/api/v1/edge/sync",
         description="Central cloud or district uplink synchronization endpoint",
     )
@@ -221,6 +226,7 @@ class EdgeNodeTelemetry(BaseModel):
     local_storage_used_mb: float = Field(
         ...,
+        ge=0.0,
         description="Disk space consumed by local encrypted database in megabytes",
     )
     local_storage_limit_mb: float = Field(
@@ -237,6 +243,9 @@ class EdgeNodeTelemetry(BaseModel):
     merkle_root_hash: str = Field(
         ...,
+        pattern=r"^[a-fA-F0-9]{64}$",
+        min_length=64,
+        max_length=64,
         description="Current SHA-256 Merkle root hash of the local event log",
     )
```
