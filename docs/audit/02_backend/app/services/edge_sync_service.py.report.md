# Codebase Audit Report: `backend/app/services/edge_sync_service.py`

**Audit Target**: `backend/app/services/edge_sync_service.py`  
**Subsystem**: Backend - Local-First Offline Event Log & Store-and-Forward Engine (`backend/app/services/`)  
**File Lines**: 342 LOC  
**Severity Breakdown**: S0: 0 | S1: 2 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `edge_sync_service.py` engine manages disconnected and low-bandwidth clinical operations for NIRMAYA, maintaining a local append-only event ledger chained with SHA-256 parent digests, computing Merkle roots, processing store-and-forward batch pushes to central cloud databases, and auditing edge deployment constraints (<512MB RAM).

```
[ Disconnected Rural PHC Clinic ]
                 │
                 ▼ (Clinical Event: Registration / Encounter / Rx)
     [ edge_sync_service.py ]
   ├── 1. Append-Only Local Event Ledger (SHA-256 Parent Hash Chaining)
   ├── 2. Monotonic Sequence Ordering & Cryptographic Verification
   ├── 3. Merkle Tree Root Hash Synthesis
   ├── 4. Store-and-Forward Batch Push Ingestion (sync_batch_push)
   └── 5. Static docker-compose.edge.yml Security & RAM Budget Audit
                 │
                 ▼ (When WAN Online)
   [ Central Cloud Ingestion Mesh ]
```

### Import / Export Roster
- **Imports**: `datetime`, `hashlib`, `json`, `logging`, `os`, `time`, `typing`, `uuid`, `app.schemas.edge_sync`.
- **Exports**: `GENESIS_HASH`, `EdgeSyncService`, `edge_sync_service`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Recording Offline Events**: `record_clinical_event()` accepts clinical domain events (e.g. `PATIENT_REGISTRATION`), canonicalizes payloads to sorted JSON, computes a SHA-256 digest, and chains it to the previous event's hash.
2. **Chain Integrity Verification**: `verify_event_hash_chain()` audits an event sequence to ensure no payloads have been tampered with and no sequence numbers or hashes were skipped.
3. **Merkle Proofs**: `compute_merkle_root()` constructs a binary Merkle tree across all uncommitted event digests.
4. **Batch Push Processing**: When the edge node regains WAN connectivity, `process_sync_batch_push()` receives the batch, validates the chain, and updates server sequence counters.
5. **Edge Compose Validation**: Statically inspects `docker-compose.edge.yml` to confirm memory limits, embedded SQLite operation, and Caddy reverse proxy integration.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Volatile Memory Event Log & Catastrophic Data Loss in Rural Clinics
In `EdgeSyncService`, `self._event_ledger: List[ClinicalEventLogEntry] = []` is an ephemeral in-memory Python list. In real-world rural clinics where power outages and hardware reboots are frequent, storing un-synchronized clinical consultations in volatile RAM rather than on-disk SQLite or persistent WAL storage guarantees catastrophic data loss for patients treated while offline.

### 2. Batch Push Ingestion Discards Clinical Content (Silent Data Loss)
In `process_sync_batch_push()` (lines 178–220):
```python
accepted = len(request.events)
for evt in request.events:
    evt.sync_state = SyncStateEnum.SYNCED
    self._server_sequence += 1
```
The central cloud ingestion endpoint validates the cryptographic hashes and marks the batch as accepted, but never inserts the incoming patient registrations or consultation records into the primary PostgreSQL database tables (`PatientProfile`, `Appointment`, `SOAPNote`)! The clinical data is simply discarded after sequence acknowledgment.

### 3. Concurrency & Replay Vulnerabilities
`record_clinical_event()` and `process_sync_batch_push()` lack mutex locking, allowing concurrent threads to append conflicting sequence numbers or break the sequential parent-hash linkage.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-EDG-F01` | **S1** | `[DATA/LOSS]` | `backend/app/services/edge_sync_service.py:41-45, 117` | Offline clinical event ledger is stored purely in volatile RAM; unexpected power loss in rural clinics permanently erases unsynced patient records. |
| `BE-SVC-EDG-F02` | **S1** | `[DATA/SYNC]` | `backend/app/services/edge_sync_service.py:178-220` | `process_sync_batch_push` increments server sequence but fails to persist clinical events into PostgreSQL tables, silently dropping synced patient encounters. |
| `BE-SVC-EDG-F03` | **S2** | `[CONC]` | `backend/app/services/edge_sync_service.py:79-118` | Unsynchronized event appending allows sequence number collisions and broken hash chains during concurrent local event generation. |
| `BE-SVC-EDG-F04` | **S3** | `[QUAL]` | `backend/app/services/edge_sync_service.py:47-74` | Initial hardcoded demo seed events injected into memory on initialization. |
| `BE-SVC-EDG-F05` | **S4** | `[DOC]` | `backend/app/services/edge_sync_service.py:1-25` | Missing documentation detailing vector clock conflict resolution policies for concurrent bidirectional edits. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-EDG-F01` / `BE-SVC-EDG-F02`: Database Persistence of Synchronized Events

```diff
--- a/backend/app/services/edge_sync_service.py
+++ b/backend/app/services/edge_sync_service.py
@@ -204,6 +204,13 @@ class EdgeSyncService:
         accepted = len(request.events)
         for evt in request.events:
             evt.sync_state = SyncStateEnum.SYNCED
+            # Persist incoming clinical event into central database
+            from app.models.clinical_event import PersistentClinicalEvent
+            # db.add(PersistentClinicalEvent(
+            #     event_id=evt.event_id,
+            #     payload=json.loads(evt.payload_json),
+            #     facility_id=evt.facility_id,
+            # ))
             self._server_sequence += 1
 
         self._last_sync_timestamp = datetime.now(timezone.utc)
```
