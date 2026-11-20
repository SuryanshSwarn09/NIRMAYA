# Principal Software Engineering Audit: backend/app/services/workflow_isolation_service.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/workflow_isolation_service.py` implements specialized clinical workflow isolation, session context switching, and segmented electronic health record (EHR) view management for pediatric minors and geriatric seniors under Section 9 of India's Digital Personal Data Protection (DPDP) Act 2023. It ensures zero-data-contamination between primary patient vaults and dependent minor/senior profiles, tracks pediatric growth against World Health Organization (WHO) percentile curves, manages National Universal Immunization Programme (UIP) schedules, and calculates Comprehensive Geriatric Assessments (CGA), Fried frailty scores, fall risk indices, and Beers Criteria polypharmacy alerts. Critical architectural vulnerabilities include volatile in-memory persistence that loses updated clinical records and context sessions upon server restart, unauthenticated clinical record mutations permitting anyone to alter immunization or geriatric profiles without cryptographic HPR verification, and hardcoded heuristic gender determinations.

### System Topology & Architectural Invariants
```
                  +-------------------------------------------------+
                  |      NIRMAYA Citizen Portal & Doctor Consoles   |
                  |     (app.api.v1.endpoints.workflow_isolation)   |
                  +-----------------------+-------------------------+
                                          |
                                          v
                  +-------------------------------------------------+
                  |          WorkflowIsolationService               |
                  |       (workflow_isolation_service.py)           |
                  +-----------------------+-------------------------+
                                          |
        +-----------------+---------------+-----------------+
        |                 |               |                 |
        v                 v               v                 v
  +-----------+     +-----------+   +-----------+     +-----------+
  | list_     |     | switch_   |   | Pediatric |     | Geriatric |
  | available_|     | active_   |   | Services  |     | Services  |
  | contexts()|     | context() |   | - UIP     |     | - CGA     |
  | - Self    |     | - Checks  |   |   schedule|     |   Profiles|
  | - Minor   |     |   proxy   |   | - WHO     |     | - Beers   |
  | - Senior  |     | - Filters |   |   growth  |     |   Criteria|
  +-----------+     |   views   |   +-----------+     +-----------+
                    +-----------+
```

### Import / Export Surface Map
- **Upstream Dependencies:**
  - `uuid`: Isolation session ID generation.
  - `datetime.datetime`, `datetime.timezone`: UTC timestamp recording.
  - `typing.Dict`, `typing.List`, `typing.Optional`: Type annotations.
  - `app.schemas.workflow_isolation`: `ContextTypeEnum`, `DependentContextSummary`, `FallRiskCategoryEnum`, `GeriatricAssessmentProfile`, `NutritionalStatusEnum`, `PediatricGrowthObservation`, `PediatricImmunizationMilestone`, `VaccinationStatusEnum`, `WorkflowSwitchResponse`.
  - `app.services.family_proxy_service.family_proxy_service`: Verification of guardian-dependent proxy delegations.
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/workflow_isolation.py`: Context switching, pediatric immunization, and geriatric CGA endpoints.
- **Exported Interface:**
  - `WorkflowIsolationService`: Service managing clinical workflow isolation.
  - `workflow_isolation_service`: Global singleton instance.

---

## Layer B: Plain-Language Developer Walkthrough

The `workflow_isolation_service.py` module governs how the platform safely switches between adult, pediatric, and geriatric clinical workflows while preserving strict regulatory separation:
1. **Context Enumeration (`list_available_contexts`)**: When an authenticated user requests their available contexts, the service always includes the user's primary identity (`ContextTypeEnum.SELF`). It then queries `family_proxy_service` for all verified legal delegations held by this user. Minor dependents (< 18 years) are assigned `PEDIATRIC_MINOR` context; seniors (>= 60 years) are assigned `GERIATRIC_SENIOR` context.
2. **Context Switching (`switch_active_context`)**: When a parent or caregiver switches from their own health record to their dependent child's record, this function validates that the caller holds an authorized proxy delegation. If verified, it activates that target patient context and returns a dynamic list of permitted clinical views. For children, the UI displays pediatric immunizations, WHO growth percentiles, and school health records; for seniors, the UI displays CGA assessments, Beers polypharmacy audits, and fall risk indicators.
3. **Pediatric Subsystem (`get_pediatric_immunizations`, `record_immunization`, `get_pediatric_growth_history`)**: Tracks vaccinations according to India's National Universal Immunization Programme (BCG, OPV, HepB, Pentavalent, Rotavirus, MR, DPT). Updates can be recorded with batch numbers, administering HPR IDs, and facility names.
4. **Geriatric Subsystem (`get_geriatric_assessment`, `update_geriatric_assessment`)**: Tracks Comprehensive Geriatric Assessment metrics including Fried Frailty score, Timed Up and Go (TUG) fall risk, Katz Activities of Daily Living (ADL), Mini-Cog score, and Beers Criteria medication alerts.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Volatile In-Memory Storage for High-Stakes Clinical Records
In `WorkflowIsolationService.__init__` (lines 24-29):
```python
self._active_contexts: Dict[str, str] = {}
self._immunization_records: Dict[str, List[PediatricImmunizationMilestone]] = self._init_seed_immunizations()
self._growth_observations: Dict[str, List[PediatricGrowthObservation]] = self._init_seed_growth_observations()
self._geriatric_assessments: Dict[str, GeriatricAssessmentProfile] = self._init_seed_geriatric_assessments()
```
The active session contexts, recorded pediatric vaccinations (`record_immunization`), and geriatric assessments (`update_geriatric_assessment`) are stored entirely in ephemeral Python dictionary memory. No relational database tables or persistent storage engines are used. If the FastAPI process restarts or rolls out a new container, all real-time pediatric vaccination records and senior fall risk assessments are lost.

### Invariant 2: Unrestricted Mutation Without Practitioner HPR Verification
In `record_immunization` (lines 388-403) and `update_geriatric_assessment` (lines 427-433):
The service mutates clinical records without verifying whether the caller is a registered healthcare practitioner (HPR) or whether the update payload carries a valid digital signature. An unauthorized guardian or malicious client can overwrite official vaccination batch numbers or modify medical notes directly.

### Invariant 3: Heuristic Gender Determination Based on Substring Matching
In `list_available_contexts` (line 319):
```python
gender="Female" if "Kavita" in dep_name else "Male",
```
The patient's clinical gender is inferred using a hardcoded string test: if the dependent's name contains `"Kavita"`, it assigns `"Female"`, otherwise it defaults to `"Male"`. In a production healthcare system, demographic attributes such as biological sex and gender identity must be retrieved from the authoritative patient profile or UIDAI e-KYC record; heuristic guessing can lead to severe medication dosing and diagnostic errors.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SVC-WFI-F01` | **S1** | `[SEC]` / `[QUAL]` | `workflow_isolation_service.py:24-29` | Volatile in-memory dictionary storage for active contexts, immunizations, and CGA records results in complete data loss on process restart. |
| `BE-SVC-WFI-F02` | **S1** | `[SEC]` | `workflow_isolation_service.py:388-433` | Clinical record ingestion lacks healthcare practitioner (HPR) credential validation or digital signature verification. |
| `BE-SVC-WFI-F03` | **S2** | `[QUAL]` | `workflow_isolation_service.py:319` | Hardcoded substring heuristic (`"Kavita" in dep_name`) guesses patient gender, causing clinical misclassification. |
| `BE-SVC-WFI-F04` | **S2** | `[QUAL]` | `workflow_isolation_service.py:185-186` | Shared reference to mutable default UIP schedule list allows mutations on one child profile to contaminate other defaults. |
| `BE-SVC-WFI-F05` | **S3** | `[PERF]` | `workflow_isolation_service.py:335-337` | Unindexed linear list filtering over proxy contexts on every context switch. |
| `BE-SVC-WFI-F06` | **S4** | `[DOC]` | `workflow_isolation_service.py:255-266` | Beers Criteria polypharmacy rules lack documentation on AGES / AGS Beers Criteria 2023 update and interaction severity scales. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-WFI-F03-F04`: Remove Gender Heuristic & Deep Copy Seed Schedules
```diff
--- a/backend/app/services/workflow_isolation_service.py
+++ b/backend/app/services/workflow_isolation_service.py
@@ -1,4 +1,5 @@
 import uuid
+import copy
 from datetime import datetime, timezone
 from typing import Dict, List, Optional
 
@@ -316,7 +317,7 @@
                     display_name=dep_name,
                     abha_number=dep_abha,
                     context_type=ctx_type,
                     age=dep.dependent_age,
-                    gender="Female" if "Kavita" in dep_name else "Male",
+                    gender=getattr(dep, "dependent_gender", "Unknown"),
                     proxy_relationship_id=dep.relationship_id,
                     relationship_type=dep.relationship_type.value,
                     access_scope=dep.access_scope.value,
@@ -385,7 +386,8 @@
     def get_pediatric_immunizations(self, child_id: str) -> List[PediatricImmunizationMilestone]:
         """Fetch National Universal Immunization Programme (UIP) timeline for child dependent."""
-        return self._immunization_records.get(child_id, self._immunization_records.get("default", []))
+        records = self._immunization_records.get(child_id)
+        if records is None:
+            records = copy.deepcopy(self._immunization_records.get("default", []))
+            self._immunization_records[child_id] = records
+        return records
```
