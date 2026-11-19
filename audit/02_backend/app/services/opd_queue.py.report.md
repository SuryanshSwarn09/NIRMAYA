# Codebase Technical Audit Report: `backend/app/services/opd_queue.py`

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`opd_queue.py` implements the Outpatient Department (OPD) Consultation Queue Service Engine for NIRMAYA. It manages daily facility patient queues, sequential token generation, clinical triage categorization (EMERGENT, URGENT, STANDARD, NON_URGENT), consulting room assignment, wait time estimation, queue lifecycle transitions, and real-time WebSocket event dissemination to facility displays and doctor workspaces.

### System Topology & OPD Queue Flow
```
   [ Arriving Patient / Kiosk ]
                |
     (Check-in & Assign Token)
                v
   +------------------------------------+
   |          OpdQueueService           |
   +------------------------------------+
   | - Sequential Daily Token Dispenser |
   | - Clinical Triage Priority Sorter  |
   | - Consulting Room Assignment FSM   |
   | - Wait Time Estimation Engine      |
   +------------------------------------+
        /                          \
       v                            v
  (WebSocket Broadcast)       (Doctor Workspace)
  Channel: `facility_queue`   Channel: `doctor_workspace`
```

### Module Metadata & Imports/Exports
- **Module Path:** `backend/app/services/opd_queue.py`
- **Component Classification:** Clinical Workflow & OPD Queue Management Engine
- **Lines of Code:** 334 LOC
- **Imports:** `asyncio`, `datetime`, `logging`, `typing`, `uuid`, `app.core.exceptions.*`, `app.schemas.opd_queue.*`, `app.schemas.websocket_events.*`, `app.services.websocket_manager.ws_manager`
- **Primary Export:** `opd_queue_service` (Global Singleton Instance)

---

## Layer B: Plain-Language Developer Walkthrough

The service models the daily patient journey in an outpatient hospital department:
1. **Patient Check-in (`check_in_patient`)**: Arriving patients register with their demographic and ABHA details. An `asyncio.Lock` synchronizes sequential token assignment (`_token_counters[facility_id] += 1`). Wait times are estimated dynamically based on triage severity (5 min for EMERGENT, 15 min for URGENT, 30 min for STANDARD). An event payload is broadcast via WebSockets to the facility queue display and the assigned doctor's EMR.
2. **Clinical Triage Adjustment (`update_triage`)**: Nursing staff can elevate a patient's triage level (e.g. from STANDARD to EMERGENT upon detecting severe distress) and adjust wait times with triage notes, reordering queue positions.
3. **Doctor Calling Patient (`call_patient`)**: A consulting physician calls the patient token into a designated room (e.g., "Room 1"), transitioning status to `CALLED`, stamping the timestamp, and triggering audio-visual alerts across hospital digital displays.
4. **Queue Lifecycle Advancement (`update_status`)**: Tracks transitions through `IN_CONSULTATION`, `COMPLETED`, `ABSENT`, or `CANCELLED`, recording consultation start and completion times.
5. **Queue Retrieval & Statistics (`get_facility_queue` & `get_queue_stats`)**: Retrieves the queue sorted primarily by clinical urgency (EMERGENT first) and secondarily by token number, calculating real-time statistics (active tokens, urgent counts, average wait time).

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Triage-First Clinical Queue Ordering
Standard FIFO token ordering in hospital waiting rooms is unsafe during clinical emergencies. The service enforces an invariant where patients triaged as `EMERGENT` or `URGENT` preempt normal waiting order regardless of their arrival token number:
$$\text{SortKey}(e) = (\text{IsActive}(e), \text{TriagePriority}(e), \text{TokenNumber}(e))$$
This guarantees that acute conditions (e.g. chest pain, severe asthma) are presented first to attending clinicians.

### Invariant 2: Facility & Doctor Multi-Channel Broadcast Synchronization
Whenever a queue entry mutations occurs (check-in, triage update, room call, completion), the service broadcasts the update across two independent WebSocket channels: the public facility waiting room board (`facility_queue:{facility_id}`) and the private clinical workspace (`doctor_workspace:{doctor_id}`).

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
|---|---|---|---|---|
| `BE-SVC-OPD-F01` | **S1** | `[SEC]` | `backend/app/services/opd_queue.py:38-44` | Volatile In-Memory OPD Queue and Daily Token Counter Storage. Active facility queues and token sequence numbers exist purely in Python memory. Container restart or multi-worker deployment desynchronizes tokens, causing duplicated token assignments (#1 given to multiple patients) and loss of active clinical queues in busy government hospitals. |
| `BE-SVC-OPD-F02` | **S1** | `[SEC]` | `backend/app/services/opd_queue.py:195-240` | Unrestricted Queue State Manipulation Without Clinician Identity or Room Authorization. `update_status` and `call_patient` accept arbitrary strings and transition queue states (e.g. marking a patient `COMPLETED` or `CANCELLED`) without validating if the caller is the assigned doctor or front-desk staff. |
| `BE-SVC-OPD-F03` | **S2** | `[QUAL]` | `backend/app/services/opd_queue.py:100-110` | In-Memory Lock (`asyncio.Lock()`) Fails Across Multi-Worker Uvicorn Processes. `self._lock` is local to a single Python event loop. In production, multiple Uvicorn worker processes will concurrently increment `_token_counters`, producing duplicate tokens. |
| `BE-SVC-OPD-F04` | **S2** | `[QUAL]` | `backend/app/services/opd_queue.py:90-98` | Inefficient Full Linear Iteration in `_find_entry_and_facility`. Iterates through all facilities and all their entries to find a queue ID instead of maintaining a global `queue_id -> facility_id` lookup map. |
| `BE-SVC-OPD-F05` | **S3** | `[PERF]` | `backend/app/services/opd_queue.py:245-290` | Sorting and Aggregations Computed In-Memory on Every Queue Query without Caching. |
| `BE-SVC-OPD-F06` | **S4** | `[DOC]` | `backend/app/services/opd_queue.py:10-16` | Missing Operational Documentation on Midnight Token Reset Scheduler and Emergency Department Code Red protocols. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch 1: Maintain Direct Queue Index Map (`BE-SVC-OPD-F04`)
```diff
--- a/backend/app/services/opd_queue.py
+++ b/backend/app/services/opd_queue.py
@@ -39,2 +39,3 @@ class OpdQueueService:
         self._queues: Dict[str, Dict[str, OPDQueueEntry]] = {}
+        self._entry_index: Dict[str, str] = {}
         self._token_counters: Dict[str, int] = {}
@@ -91,4 +92,6 @@ class OpdQueueService:
     def _find_entry_and_facility(self, queue_id: str) -> tuple[Optional[str], Optional[OPDQueueEntry]]:
-        for fac_id, entries in self._queues.items():
-            if queue_id in entries:
-                return fac_id, entries[queue_id]
+        fac_id = self._entry_index.get(queue_id)
+        if fac_id and fac_id in self._queues:
+            return fac_id, self._queues[fac_id].get(queue_id)
         return None, None
```

### Patch 2: Add Distributed Redis Lock Placeholder for Token Numbering (`BE-SVC-OPD-F03`)
```diff
--- a/backend/app/services/opd_queue.py
+++ b/backend/app/services/opd_queue.py
@@ -102,3 +102,4 @@ class OpdQueueService:
         async with self._lock:
+            # Note: Must migrate to Redis atomic INCR (facility:token:YYYYMMDD) for multi-worker support
             fac_id = req.facilityId
             if fac_id not in self._token_counters:
```
