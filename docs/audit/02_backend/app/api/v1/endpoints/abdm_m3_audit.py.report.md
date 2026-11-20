# NIRMAYA Codebase Technical Audit Report

## File Identity
- **File Path**: `backend/app/api/v1/endpoints/abdm_m3_audit.py`
- **Subsystem**: ABDM Milestone 3 (M3) Integration Audit & Certification
- **Component**: Live Milestone 3 Compliance Diagnostics API
- **Layer**: Routing & Presentation Layer

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Module Boundary
```
  [Monitoring / Dashboard / External Client]
                     │
                     ▼ (GET /api/v1/abdm/m3/audit)
            [get_audit_report] (NO AUTH)
                     │
                     ▼
       [generate_m3_audit_report()]
                     │
    ┌────────────────┼────────────────┐
    ▼                ▼                ▼
[Consent Metrics] [Crypto Parity]  [Transfer Stats]
```

### Imports & Exports
- **Imports**: `logging`, `APIRouter`, `status` from `fastapi`; `AbdmM3AuditReport` from `app.schemas.abdm_m3_audit`; `generate_m3_audit_report` from `app.services.abdm_m3_audit`.
- **Exports**: `router: APIRouter()`
- **Downstream Consumers**: `app/api/v1/router.py` (mounted at `/abdm/m3/audit`).

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/api/v1/endpoints/abdm_m3_audit.py` provides the HTTP GET endpoint for ABDM Milestone 3 compliance telemetry. It registers two paths: `GET ""` and `GET "/"` (the latter with `include_in_schema=False` to handle trailing slash variations). It calls `generate_m3_audit_report()`, which compiles cryptographic parity results, consent transaction volumes, and data transfer statistics into a single structured report.

---

## Layer C: Technical Deep Dive & Invariant Analysis

1. **Unauthenticated Public Telemetry Disclosure**:
   Lines 18-38 define `get_audit_report` without any security dependency (`Depends(get_current_user)`). Any unauthenticated client can retrieve system transaction volumes, cryptographic key agreement success rates, and active HIP/HIU counters.
2. **Duplicate Route Registration Handling**:
   The use of both `""` and `"/"` handles FastAPI's trailing slash strictness, ensuring clients requesting either path receive identical HTTP 200 responses.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-ABDM-M3A-F01` | **S2** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m3_audit.py:18-38` | `get_audit_report` is completely unauthenticated, exposing real-time hospital cryptographic telemetry, consent numbers, and data transfer metrics. |
| `BE-ABDM-M3A-F02` | **S4** | `[DOC]` | `backend/app/api/v1/endpoints/abdm_m3_audit.py:1` | Module docstring lacks NHA ABDM v0.5 Milestone 3 specification reference URLs. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-ABDM-M3A-P01`: Restrict M3 Audit Endpoint to Authenticated Operators

```diff
--- a/backend/app/api/v1/endpoints/abdm_m3_audit.py
+++ b/backend/app/api/v1/endpoints/abdm_m3_audit.py
@@ -6,8 +6,10 @@ Exposes live compliance and telemetry diagnostics for ABDM M3:
 """
 
 import logging
-from fastapi import APIRouter, status
+from fastapi import APIRouter, Depends, status
 
+from app.core.dependencies import get_current_user
+from app.models.user import User
 from app.schemas.abdm_m3_audit import AbdmM3AuditReport
 from app.services.abdm_m3_audit import generate_m3_audit_report
 
@@ -32,3 +34,5 @@ router = APIRouter()
 )
-async def get_audit_report() -> AbdmM3AuditReport:
+async def get_audit_report(
+    current_user: User = Depends(get_current_user),
+) -> AbdmM3AuditReport:
     """Returns live ABDM Milestone 3 compliance audit report."""
```
