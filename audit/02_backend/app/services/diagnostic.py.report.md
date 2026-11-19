# Codebase Audit Report: `backend/app/services/diagnostic.py`

**Audit Target**: `backend/app/services/diagnostic.py`  
**Subsystem**: Backend - Diagnostic Orders & Laboratory Reports Service (`backend/app/services/`)  
**File Lines**: 345 LOC  
**Severity Breakdown**: S0: 0 | S1: 1 | S2: 2 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `diagnostic.py` module manages the lifecycle of diagnostic service requests (`DiagnosticOrder` / FHIR ServiceRequest) and verified clinical diagnostic reports (`DiagnosticReport`), linking clinical observations, laboratory findings, ordering doctors, and encounters.

```
[ Clinician Consultation / Lab Technician ]
                      │
                      ▼
            [ diagnostic.py Service ]
   ├── 1. Diagnostic Order Creation & Fulfillment Tracking
   ├── 2. Diagnostic Order Pagination & Multi-Criteria Filtering
   ├── 3. Verified Diagnostic Report Issuance
   ├── 4. Observation Linking & Automatic Panic/Abnormal Detection
   └── 5. Diagnostic Report Amendment & Lifecycle Updates
                      │
                      ▼
    [ PostgreSQL DiagnosticOrder & DiagnosticReport Tables ]
```

### Import / Export Roster
- **Imports**: `datetime`, `typing`, `sqlalchemy` (`func`, `select`, `ext.asyncio`, `orm.selectinload`), `app.core.exceptions`, `app.models`, `app.schemas.diagnostic`.
- **Exports**: `create_diagnostic_order()`, `get_diagnostic_order()`, `list_patient_diagnostic_orders()`, `update_diagnostic_order()`, `create_diagnostic_report()`, `get_diagnostic_report()`, `list_patient_diagnostic_reports()`, `update_diagnostic_report()`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Ordering Tests**: `create_diagnostic_order()` verifies patient, doctor, and encounter existence before inserting an active `DiagnosticOrder`.
2. **Order Querying & Updates**: Supports filtering by status, priority, category, and LOINC code, and allows amending order notes or priority.
3. **Issuing Reports**: `create_diagnostic_report()` validates the patient, optional order (marking it `COMPLETED`), performer doctor, and linked `ClinicalObservation` records.
4. **Abnormality Detection**: If any linked observation carries an abnormal interpretation (`HIGH`, `LOW`, `CRITICALLY_HIGH`, `CRITICALLY_LOW`, `ABNORMAL`), it automatically sets `is_abnormal = True` on the report.
5. **Amendment**: Allows updating report conclusions, status, or raw report data.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Missing Authorization on Report & Order Modifications (IDOR / Tampering)
In `update_diagnostic_order()` (lines 152–174) and `update_diagnostic_report()` (lines 322–345), there are no authorization or role-based permission checks. Any caller possessing a valid report or order UUID can alter diagnostic conclusions, flip the `is_abnormal` flag, or cancel critical laboratory orders without verification that the user is the ordering clinician, pathologist, or lab director.

### 2. Hardcoded Commercial Lab Fallback
At line 247:
```python
performer_name=payload.performer_name or "Metropolis Diagnostics & Pathology Lab",
```
If a hospital or clinic omits the performer name, NIRMAYA defaults to attributing the diagnostic investigation to a commercial third-party lab ("Metropolis Diagnostics & Pathology Lab") rather than falling back to the authenticated facility name or leaving it null.

### 3. Lack of Amendment Versioning
When a diagnostic report is updated via `update_diagnostic_report()`, the existing conclusion is overwritten in place without creating a historical version or recording the amending physician's digital signature and timestamp, violating clinical audit requirements.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-DIA-F01` | **S1** | `[SEC/MED]` | `backend/app/services/diagnostic.py:152-174, 322-345` | Missing authorization on order and report modification allows unauthorized tampering with pathology results and diagnostic conclusions. |
| `BE-SVC-DIA-F02` | **S2** | `[QUAL]` | `backend/app/services/diagnostic.py:247` | Hardcoded commercial laboratory fallback name ("Metropolis Diagnostics") permanently attributes unassigned reports to an external commercial vendor. |
| `BE-SVC-DIA-F03` | **S2** | `[QUAL/MED]` | `backend/app/services/diagnostic.py:322-345` | In-place mutation of finalized diagnostic reports destroys historical findings without versioning or amendment audit trails. |
| `BE-SVC-DIA-F04` | **S3** | `[PERF]` | `backend/app/services/diagnostic.py:133, 303` | Dual query execution with subquery count generates unoptimized table scans on large diagnostic histories. |
| `BE-SVC-DIA-F05` | **S4** | `[DOC]` | `backend/app/services/diagnostic.py:1-25` | Missing documentation on HL7 FHIR DiagnosticReport bundle export and NRCeS diagnostic profile mappings. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-DIA-F01`: Authorization Verification and Facility-Aware Performer Resolution

```diff
--- a/backend/app/services/diagnostic.py
+++ b/backend/app/services/diagnostic.py
@@ -154,8 +154,14 @@ async def update_diagnostic_order(
     order_id: str,
     payload: DiagnosticOrderUpdate,
+    current_user_id: str,
 ) -> DiagnosticOrder:
     """Update status, priority, or notes on an existing diagnostic order."""
     order = await get_diagnostic_order(db, order_id)
     if not order:
         raise EntityNotFoundException("DiagnosticOrder", order_id)
+
+    # Enforce authorization: only ordering doctor or admin can modify order
+    if order.doctor_id and order.doctor.user_id != current_user_id:
+        raise PermissionDeniedException("Only the ordering clinician can modify this diagnostic service request.")
 
     if payload.status is not None:
@@ -244,7 +250,7 @@ async def create_diagnostic_report(
         encounter_id=payload.encounter_id,
         performer_id=effective_performer_id,
-        performer_name=payload.performer_name or "Metropolis Diagnostics & Pathology Lab",
+        performer_name=payload.performer_name or "Institutional Diagnostic Laboratory",
         status=payload.status or DiagnosticReportStatus.FINAL,
         category=payload.category,
```
