# Technical Audit Report: backend/app/services/administrative_hierarchy_service.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/administrative_hierarchy_service.py` provides the administrative hierarchy and territorial jurisdiction traversal engine for NIRMAYA. It models the sovereign 6-tier governance structure of India (Country, State, Division, District, Sub-District, Facility) aligned with the official Ministry of Panchayati Raj Local Government Directory (LGD). It provides methods for path-based hierarchical traversal (`india.27.492`), ancestor/descendant lookups, jurisdictional supervision boundary enforcement, and officer appointment management. The audit identified two critical **S1** architectural deficiencies: the entire registry operates in volatile in-memory dictionaries without PostgreSQL persistence (losing all runtime unit and officer changes on restart), and the module falsely reports `ltree_index_status="GIST_OPTIMIZED"` while actually executing naive Python string operations instead of database GiST queries.

### Architectural Roster
- **Module Name:** `backend/app/services/administrative_hierarchy_service.py`
- **Primary Responsibility:** Sovereign Indian administrative hierarchy management, LGD directory seeding, territorial path traversal, and officer jurisdictional boundary checks.
- **Upstream Dependencies:**
  - `app.schemas.administrative_hierarchy` (`AdminLevelEnum`, `GovtDesignationEnum`, `AdministrativeUnitCreate`, etc.)
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/administrative_hierarchy.py`
  - Territorial RBAC security checks (`app.core.territorial_rbac`)
- **Exported Symbols:**
  - `AdministrativeHierarchyService`
  - `hierarchy_service`

```
+-----------------------------------------------------------------------------------+
|                   Sovereign National LGD Administrative Engine                    |
|                                                                                   |
|  [Administrative Officer / Admin Console]                                         |
|          |                                                                        |
|          +--> [find_descendants(path)] / [find_ancestors(path)]                   |
|          |         +--> In-memory path token matching (e.g. 'india.27.492')       |
|          |                                                                        |
|          +--> [verify_jurisdiction_access(officer_scope, target_facility)]        |
|          |         +--> Subpath prefix evaluation                                 |
|          |                                                                        |
|          +--> [create_unit] / [appoint_officer]                                   |
|                    +--> In-Memory Dictionaries (_units, _officers)                |
|                         (VOLATILE: No PostgreSQL ltree table sync!)               |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

This module models India's administrative boundaries to control who can view and supervise public health data:

1. **National LGD Seeding (`_seed_national_lgd_directory`):** On startup, seeds the root National unit (`india`), all 36 States and Union Territories with official Census/LGD codes (e.g. `27` for Maharashtra, `07` for Delhi, `29` for Karnataka, `19` for West Bengal), sample divisions (Pune, Konkan), districts (Pune 492, Satara 493, Mumbai 485, New Delhi 89, Kolkata 342, Paschim Bardhaman 718), and key sub-districts (Haveli, Pune City, Durgapur). It also assigns sample demo officers (National Director, State Secretary, CMO Pune, BMO Haveli).
2. **Territorial Traversal:**
   - **`find_descendants`:** Emulates PostgreSQL ltree `path <@ target` by filtering units whose `path` starts with `path + "."`.
   - **`find_ancestors`:** Emulates `path @> target` by splitting the dot-separated string and resolving each prefix up to `india`.
   - **`build_jurisdiction_tree`:** Recursively constructs a nested JSON tree node structure up to `max_depth` for UI drilldown menus.
3. **Jurisdiction Verification (`verify_jurisdiction_access`):** Validates whether a supervising officer has jurisdictional authority over a target healthcare facility. For instance, a Chief Medical Officer assigned to Pune (`india.27.492`) has authority over Haveli (`india.27.492.4182`), but is rejected if attempting to access Satara (`india.27.493`).
4. **Unit and Officer Management:** Provides CRUD methods to register new territorial units (`create_unit`) and assign healthcare officers (`appoint_officer`).

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Specification Standards
- **Hierarchical Containment Invariant:** An officer scoped to path $P_{officer}$ can access facility $P_{facility}$ if and only if $P_{facility} = P_{officer}$ or $P_{facility}$ is prefixed by $P_{officer} + "."$.
- **LGD Code Uniqueness:** No two administrative units may share the same Ministry LGD code.

### Vulnerabilities & Architectural Deficiencies
- **Zero Database Persistence:** Despite the platform having a PostgreSQL database and an `AdministrativeHierarchy` ORM model, this service maintains all state in `self._units` and `self._officers` dictionaries in RAM. If an administrator creates a new block or appoints a new CMO, the records disappear completely on server reboot or across Uvicorn workers.
- **Deceptive Index Status & Benchmark Telemetry:** The module claims "sub-2ms territorial queries via PostgreSQL ltree" and lines 324-325 assert `ltree_index_status="GIST_OPTIMIZED"` and `sub_2ms_benchmark_passed=True`. In reality, the query never touches PostgreSQL or a GiST index; it measures the duration of iterating through a 50-item Python list in local RAM.
- **Unsynchronized Concurrency Hazard:** Line 30 states "Thread-safe administrative hierarchy...", but no `threading.Lock` or `RLock` guards the dictionary mutations in `create_unit`, `update_unit`, or `appoint_officer`.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-ADM-F01` | **S1** | `[QUAL]` | `administrative_hierarchy_service.py:34-43, 193-268` | All territorial units and appointed officers are held in ephemeral RAM dictionaries without database synchronization, wiping administrative state on restart. |
| `BE-SVC-ADM-F02` | **S1** | `[QUAL]` | `administrative_hierarchy_service.py:3-5, 324-326` | Service misreports `ltree_index_status="GIST_OPTIMIZED"` and sub-2ms DB benchmarks while executing naive in-memory Python string scans. |
| `BE-SVC-ADM-F03` | **S2** | `[QUAL]` | `administrative_hierarchy_service.py:30, 216-220, 262-266` | Class claims thread safety but implements zero synchronization locks around concurrent mutations of `_units` and `_officers`. |
| `BE-SVC-ADM-F04` | **S2** | `[SEC]` | `administrative_hierarchy_service.py:193, 239` | `create_unit` and `appoint_officer` lack caller authorization or signature validation, allowing unauthorized creation of administrative entities. |
| `BE-SVC-ADM-F05` | **S3** | `[QUAL]` | `administrative_hierarchy_service.py:168-187` | `_build_tree_recursive` does not guard against potential cyclic parent loops if corrupted unit hierarchies are introduced. |
| `BE-SVC-ADM-F06` | **S4** | `[DOC]` | `administrative_hierarchy_service.py:500-550` | Hardcoded demo officer email addresses and IDs seeded directly into the service layer. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Thread-Safety Lock & Persistence Warning (`BE-SVC-ADM-F01`, `BE-SVC-ADM-F03`)

```diff
--- a/backend/app/services/administrative_hierarchy_service.py
+++ b/backend/app/services/administrative_hierarchy_service.py
@@ -10,6 +10,7 @@
 from datetime import datetime, timezone
+import threading
 from typing import Dict, List, Optional, Set
 import uuid
 
@@ -34,6 +35,11 @@ class AdministrativeHierarchyService:
         self._units: Dict[str, dict] = {}  # id -> unit dict
         self._units_by_path: Dict[str, dict] = {}  # path -> unit dict
         self._units_by_lgd: Dict[str, dict] = {}  # lgd_code -> unit dict
         self._officers: Dict[str, dict] = {}  # id -> officer dict
         self._officers_by_unit: Dict[str, List[dict]] = {}  # unit_id -> list of officers
         self._is_seeded: bool = False
+        self._lock = threading.RLock()
+        logger.warning(
+            "[SECURITY] AdministrativeHierarchyService is currently operating in EPHEMERAL in-memory mode. "
+            "Unit additions and officer appointments will NOT persist across process restarts."
+        )
```
