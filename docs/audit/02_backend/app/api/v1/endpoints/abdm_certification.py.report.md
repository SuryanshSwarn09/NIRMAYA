# NIRMAYA Codebase Technical Audit Report

## File Identity
- **File Path**: `backend/app/api/v1/endpoints/abdm_certification.py`
- **Subsystem**: ABDM Certification & Regression Testing
- **Component**: Sandbox Test Harness & Compliance Endpoints
- **Layer**: Routing & Presentation Layer

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Module Boundary
```
  [External QA Client / Auditor / Attacker]
                     │
  ┌──────────────────┼──────────────────┐
  ▼ (POST /run)      ▼ (GET /report)    ▼ (GET /vectors)
[run_certification_ [get_latest_cert..] [get_vector_catalog]
 harness] (NO AUTH)   (NO AUTH)          (NO AUTH)
  │                  │                  │
  └──────────────────┼──────────────────┘
                     ▼
       [abdm_sandbox_certifier Service]
                     │
  ┌──────────────────┼──────────────────┐
  ▼                  ▼                  ▼
[M1 Test Vectors]  [M2 Test Vectors]  [M3 Test Vectors]
```

### Imports & Exports
- **Imports**: `logging`, `Optional`, `APIRouter`, `HTTPException`, `status` from `fastapi`; schemas `RunCertificationRequest`, `SandboxCertificationReport`, `VectorCatalogResponse` from `app.schemas.abdm_certification`; `OFFICIAL_VECTOR_CATALOG`, `abdm_sandbox_certifier` from `app.services.abdm_certification`.
- **Exports**: `router: APIRouter()`
- **Downstream Consumers**: `app/api/v1/router.py` (mounted at `/abdm/certification`).

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/api/v1/endpoints/abdm_certification.py` provides the HTTP interface for running ABDM Milestone 1, Milestone 2, and Milestone 3 automated test vectors. It supports three operations:
1. `POST /run`: Executes NHA test scenarios on demand, accepting milestone filters, facility IDs, and mock network delay settings, generating a signed SHA-256 certification proof.
2. `GET /report`: Fetches the most recent cached certification report, running an execution run if none exists.
3. `GET /vectors`: Returns the static catalog of official NHA ABDM Gateway v0.5 test vectors.

---

## Layer C: Technical Deep Dive & Invariant Analysis

1. **Unauthenticated Test Harness Execution (`run_certification_harness`)**:
   Lines 37-54 contain no authentication dependency (`current_user: User = Depends(get_current_user)`). Any external entity on the public internet can trigger automated certification test runs. Because the test harness executes simulated crypto handshakes, OTP generations, and network delays, an attacker can launch an asynchronous Denial of Service (DoS) attack, overwhelming server worker threads.
2. **Unauthenticated Information Disclosure of Compliance Vectors**:
   Both `GET /report` and `GET /vectors` are public endpoints without RBAC or authentication. Attackers can fingerprint system state, discover facility IDs, and inspect internal test harness configurations.
3. **Internal Error Traceback / Exception Leakage**:
   Lines 50-53:
   `detail=f"Certification harness failed during execution: {str(exc)}"`
   Leaking unhandled Python exceptions exposes file paths, internal service state, and dependency errors to external clients.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-ABDM-CRT-F01` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_certification.py:37` | `run_certification_harness` is unauthenticated, allowing public attackers to trigger resource-intensive test executions and forge certification reports. |
| `BE-ABDM-CRT-F02` | **S2** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_certification.py:64,81` | Unauthenticated compliance reporting and vector catalog endpoints expose internal facility identifiers and testing topologies. |
| `BE-ABDM-CRT-F03` | **S2** | `[QUAL]` | `backend/app/api/v1/endpoints/abdm_certification.py:52` | Raw exception string `str(exc)` returned in HTTP 500 error response details. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-ABDM-CRT-P01`: Restrict Certification Endpoints to Authorized Administrators

```diff
--- a/backend/app/api/v1/endpoints/abdm_certification.py
+++ b/backend/app/api/v1/endpoints/abdm_certification.py
@@ -10,7 +10,9 @@ import logging
 from typing import Optional
-from fastapi import APIRouter, HTTPException, status
+from fastapi import APIRouter, Depends, HTTPException, status
 
+from app.core.dependencies import get_current_user
+from app.models.user import User
 from app.schemas.abdm_certification import (
     RunCertificationRequest,
@@ -37,6 +39,7 @@ router = APIRouter()
 def run_certification_harness(
     request: RunCertificationRequest,
+    current_user: User = Depends(get_current_user),
 ) -> SandboxCertificationReport:
     """Executes official sandbox certification harness and returns compliance report."""
+    if getattr(current_user, "role", "") != "ADMIN" and not getattr(current_user, "is_superuser", False):
+        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin authorization required")
     try:
@@ -51,5 +54,5 @@ def run_certification_harness(
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
-            detail=f"Certification harness failed during execution: {str(exc)}",
+            detail="Certification harness failed during execution. Please inspect system logs.",
         )
 
@@ -63,4 +66,5 @@ def run_certification_harness(
-def get_latest_certification_report() -> SandboxCertificationReport:
+def get_latest_certification_report(
+    current_user: User = Depends(get_current_user),
+) -> SandboxCertificationReport:
     """Returns the most recent certification report or runs one on demand."""
```
