# Comprehensive Principal Software Audit & Technical Documentation
# File: `backend/app/schemas/workflow_isolation.py`
# Component: Zero-Contamination Workflow Isolation & Persona Management
# Release Version: 1.1.0-RC3 · ABDM / NRCES v4.1 Compliance

---

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/schemas/workflow_isolation.py` specifies the Pydantic domain models that govern zero-contamination clinical workflow isolation and context switching in NIRMAYA. Designed to serve pediatric minors, geriatric seniors, and self-managed citizen vaults, the models define context summaries, Universal Immunization Programme (UIP) vaccine tracking, WHO-standardized child growth percentiles, Comprehensive Geriatric Assessment (CGA) evaluations, and session switching requests ensuring strict cryptographic partition between clinical personas.

### Architectural Role & System Topology
```
           +-----------------------------------------------+
           |       Citizen Vault / Guardian Session        |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |            WorkflowSwitchRequest              |
           |      (target_patient_id, requested_by)        |
           +-----------------------------------------------+
                                  |
                   (Zero-Contamination Boundary Gate)
                                  v
           +-----------------------------------------------+
           |            WorkflowSwitchResponse             |
           |   (active_context, permitted_views, token)    |
           +-----------------------------------------------+
                                  |
             +--------------------+--------------------+
             |                                         |
             v                                         v
+-----------------------------+           +-----------------------------+
| PediatricImmunization /     |           | GeriatricAssessmentProfile  |
| PediatricGrowthObservation  |           | (Fried Frailty, Fall Risk)  |
+-----------------------------+           +-----------------------------+
```

### Key Import/Export Roster
- **Imports**:
  - `uuid`: Identifier generation.
  - `datetime, timezone` from `datetime`: UTC session timestamps.
  - `Enum` from `enum`: Workflow and clinical rating enumerations.
  - `Any, Dict, List, Optional` from `typing`: Type annotations.
  - `BaseModel, Field` from `pydantic`: Schema modeling and field constraints.
- **Exports**:
  - `ContextTypeEnum`: Persona categories (`SELF`, `PEDIATRIC_MINOR`, `GERIATRIC_SENIOR`).
  - `VaccinationStatusEnum`: UIP immunization statuses (`ADMINISTERED`, `SCHEDULED`, `OVERDUE`).
  - `NutritionalStatusEnum`: WHO child nutrition categories (`NORMAL`, `MODERATE_WASTING`, `STUNTING`, etc.).
  - `FallRiskCategoryEnum`: Timed Up and Go mobility grades (`LOW`, `MODERATE`, `HIGH`).
  - `DependentContextSummary`: Metadata for selectable dependent profiles.
  - `PediatricImmunizationMilestone`: Vaccination dose record under national guidelines.
  - `PediatricGrowthObservation`: Child anthropometric telemetry.
  - `GeriatricAssessmentProfile`: Senior CGA profile (frailty score, polypharmacy count, Katz ADL).
  - `WorkflowSwitchRequest`: Context transition request.
  - `WorkflowSwitchResponse`: Session boundary proof and permitted view segmentations.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Context Classifications**: Segregates patient access into three personas (`ContextTypeEnum`): independent adults (`SELF`), children (`PEDIATRIC_MINOR`), and elderly dependents (`GERIATRIC_SENIOR`).
2. **Context Summaries (`DependentContextSummary`)**: Outlines dependent patient profiles available to a logged-in guardian, containing patient UUID, legal name, masked ABHA number, age, relationship type, and current session activation state.
3. **Pediatric Health Trackers**:
   - `PediatricImmunizationMilestone`: Captures vaccine codes, dose sequence numbers, administration facility, and adverse reaction flags under India's Universal Immunization Programme.
   - `PediatricGrowthObservation`: Tracks age in completed months, height, weight, and WHO percentile classifications to detect stunting or wasting.
4. **Geriatric Clinical Profiles (`GeriatricAssessmentProfile`)**: Evaluates Fried Frailty scores (0–5), Timed Up and Go (TUG) transit times, Katz ADL independence index, Beers Criteria drug interactions, and polypharmacy counts.
5. **Session Switching (`WorkflowSwitchRequest`, `WorkflowSwitchResponse`)**: Manages transitions between health personas, returning cryptographically signed isolation session tokens (`isolation_session_id`) and segmented view permissions to guarantee zero cross-record contamination.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Insecure Direct Object Reference (IDOR) via Client-Specified User ID (CWE-639)
`WorkflowSwitchRequest` requires both `target_patient_id: str` and `requested_by_user_id: str` in the inbound request body. If the backend workflow switching endpoint relies on `requested_by_user_id` from the JSON payload rather than extracting the user ID directly from the authenticated JWT token (`current_user.id`), an attacker can craft a payload asserting any guardian's identity, switching into unauthorized dependent health contexts without valid authorization.

### Invariant 2: Demographic PII & ABHA Masking in Dependent Contexts (CWE-532 / CWE-312)
`DependentContextSummary` exposes `display_name: str` and `abha_number: Optional[str]` without `repr=False`. While the default field definition provides `"14-XXXX-XXXX-XXXX"`, when populated from the database with actual ABHA identifiers, string representations in debug logs or APM traces will leak citizen demographic identities and health numbers.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-WF-F01` | S1 | `[SEC]` | `workflow_isolation.py:100` | `WorkflowSwitchRequest` accepts `requested_by_user_id` in request body instead of relying on token identity |
| `BE-SCH-WF-F02` | S2 | `[SEC]` | `workflow_isolation.py:41-42` | `display_name` and `abha_number` lack `repr=False`, leaking PII in string representations |
| `BE-SCH-WF-F03` | S3 | `[QUAL]` | `workflow_isolation.py:38, 97, 103` | Several schemas omit `ConfigDict(from_attributes=True)` |
| `BE-SCH-WF-F04` | S3 | `[QUAL]` | `workflow_isolation.py:63` | `administered_by_hpr` lacks Healthcare Professional Registry format regex validation |

---

## Layer E: Unapplied Unified Diff Patches for S0–S2 Findings

```diff
--- a/backend/app/schemas/workflow_isolation.py
+++ b/backend/app/schemas/workflow_isolation.py
@@ -38,8 +38,8 @@
 class DependentContextSummary(BaseModel):
     """Summary of an available patient context for session switching."""
     patient_id: str = Field(..., description="Unique sovereign PatientProfile UUID")
-    display_name: str = Field(..., description="Legal demographic name")
-    abha_number: Optional[str] = Field("14-XXXX-XXXX-XXXX", description="14-digit ABDM ABHA Number or handle")
+    display_name: str = Field(..., repr=False, description="Legal demographic name")
+    abha_number: Optional[str] = Field("14-XXXX-XXXX-XXXX", repr=False, description="14-digit ABDM ABHA Number or handle")
     context_type: ContextTypeEnum = Field(..., description="Categorization of clinical context")
     age: int = Field(..., description="Chronological age in years")
     gender: str = Field(..., description="Administrative gender (Male/Female/Other)")
@@ -97,8 +97,7 @@
 class WorkflowSwitchRequest(BaseModel):
     """Payload to transition active session to a dependent or personal context."""
     target_patient_id: str = Field(..., description="PatientProfile UUID to switch into")
-    requested_by_user_id: str = Field(..., description="Authenticated guardian user ID")
 
 
 class WorkflowSwitchResponse(BaseModel):
```
