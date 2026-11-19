# Codebase Audit Report: `backend/app/services/command_center_service.py`

**Audit Target**: `backend/app/services/command_center_service.py`  
**Subsystem**: Backend - Public Health Surveillance & Command Center (`backend/app/services/`)  
**File Lines**: 498 LOC  
**Severity Breakdown**: S0: 0 | S1: 1 | S2: 2 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `command_center_service.py` module delivers territorial public health surveillance, disease outbreak cluster monitoring, critical care/ICU bed census telemetry, and official health containment directive issuance across India's 6-tier administrative hierarchy.

```
[ Public Health Officer / State Dashboard ]
                     │
                     ▼
       [ command_center_service.py ]
   ├── 1. Subtree Recursive Territorial Aggregation (_is_in_territory)
   ├── 2. Disease Outbreak Surveillance Heatmap (Dengue, Malaria, COVID-19)
   ├── 3. Critical Care & ICU Bed Census (> 85% Divert Alarms)
   ├── 4. Specialist Workforce & Roster Telemetry
   └── 5. Public Health Directive Dispatch Engine
                     │
                     ▼
   [ CommandCenterOverviewResponse / Directive Dispatch ]
```

### Import / Export Roster
- **Imports**: `datetime`, `logging`, `time`, `typing`, `uuid`, `app.schemas.administrative_hierarchy`, `app.schemas.command_center`, `app.services.administrative_hierarchy_service`.
- **Exports**: `CommandCenterService`, `command_center_service`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Territorial Aggregation**: Given a jurisdiction path (e.g. `india.27.492`), aggregates active disease clusters, ICU capacity, occupied beds, and active directives for the unit and all subordinate administrative entities.
2. **Outbreak Tracking**: Filters outbreak clusters by severity (`ALERT`, `WATCH`, `OUTBREAK`), reproduction rate ($R_t$), and 7-day trajectory.
3. **Bed Census & Diversion**: Tracks ICU bed and ventilator utilization, flagging facilities exceeding 85% occupancy with admission diversion directives.
4. **Directives Issuance**: Issues sovereign public health containment directives, recording issuing officer credentials, target jurisdiction, and expiration timelines.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. In-Memory Ephemeral Storage of Sovereign Health Directives
Lines 39–42 define `_outbreaks`, `_facilities`, and `_directives` as plain Python dictionaries. Official containment orders and ICU census data are not persisted to PostgreSQL or Redis. In the event of a worker crash or rolling update, sovereign directives disappear, causing lost records and split-brain states across multiple server instances.

### 2. Missing Concurrency Synchronization (Race Conditions)
Unlike other service components in the platform, `CommandCenterService` does not instantiate or use a `threading.Lock()` or `asyncio.Lock()`. When `issue_health_directive()` writes to `self._directives`, simultaneous read requests running `list_health_directives()` or `get_overview_metrics()` can raise `RuntimeError: dictionary changed size during iteration`.

### 3. Fabricated Specialist Workforce Statistics
In `get_workforce_roster()` (lines 184–224), medical specialist numbers and doctor-to-patient ratios are computed using static multipliers (`total_physicians = facility_count * 18`, `intensivists = max(facility_count * 3, 1)`). Rather than inspecting active doctor shifts from `DoctorProfile` or roster schedules, the platform fabricates workforce telemetry, creating a dangerous false sense of healthcare capacity during epidemics.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-CMD-F01` | **S1** | `[SEC/DATA]` | `backend/app/services/command_center_service.py:38-45, 230-260` | Official public health directives, outbreak clusters, and bed census records reside only in volatile RAM without database persistence. |
| `BE-SVC-CMD-F02` | **S2** | `[CONC]` | `backend/app/services/command_center_service.py:38-42, 230-277` | Unsynchronized dictionary mutation during directive creation leads to race conditions and `RuntimeError` during concurrent reads. |
| `BE-SVC-CMD-F03` | **S2** | `[QUAL]` | `backend/app/services/command_center_service.py:184-224` | Workforce telemetry fabricates physician and specialist counts via static multipliers (`facility_count * 18`) rather than querying real duty rosters. |
| `BE-SVC-CMD-F04` | **S3** | `[PERF]` | `backend/app/services/command_center_service.py:50-57` | String-based subtree filtering performs full scans over in-memory dictionaries instead of utilizing indexed database hierarchy lookups. |
| `BE-SVC-CMD-F05` | **S4** | `[QUAL]` | `backend/app/services/command_center_service.py:280-495` | Hardcoded demonstration outbreak clusters and facilities permanently seeded on initialization. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-CMD-F01` / `BE-SVC-CMD-F02`: Thread-Safe Directives Management with Concurrency Locks

```diff
--- a/backend/app/services/command_center_service.py
+++ b/backend/app/services/command_center_service.py
@@ -10,6 +10,7 @@
 from datetime import datetime, timezone, timedelta
 import logging
 import time
+import threading
 from typing import Dict, List, Optional
 import uuid
 
@@ -39,6 +40,7 @@ class CommandCenterService:
         self._outbreaks: Dict[str, dict] = {}
         self._facilities: Dict[str, dict] = {}
         self._directives: Dict[str, dict] = {}
+        self._lock = threading.Lock()
 
         # Auto-seed operational reference telemetry
         self._seed_sovereign_telemetry()
@@ -252,7 +254,8 @@ class CommandCenterService:
             "valid_until": payload.valid_until,
         }
 
-        self._directives[directive_id] = record
+        with self._lock:
+            self._directives[directive_id] = record
         logger.info(
             "Issued public health directive '%s' for jurisdiction '%s'",
             payload.headline,
```
