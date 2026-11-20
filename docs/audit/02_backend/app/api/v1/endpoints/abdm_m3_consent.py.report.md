# NIRMAYA Codebase Technical Audit Report

## File Identity
- **File Path**: `backend/app/api/v1/endpoints/abdm_m3_consent.py`
- **Subsystem**: ABDM Milestone 3 (M3) Consent Management & Webhooks
- **Component**: Consent Ingestion Webhook, Registry Query & Revocation API
- **Layer**: Routing & Presentation Layer

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Module Boundary
```
           [ABDM Gateway / External Client / Patient]
                               │
    ┌──────────────────────────┼──────────────────────────┐
    ▼ (POST /notify)           ▼ (GET /consents/{id})     ▼ (POST /{id}/revoke)
[inbound_gateway_consent_   [get_consent_by_id]        [revoke_consent]
 notify]                     │ (UNAUTHENTICATED)        │ (UNAUTHENTICATED)
    │ (validate_headers)       │                          │
    ▼                          ▼                          ▼
[FastAPI 202 Accepted]     [consent_registry_store.   [consent_registry_store.
    │                       get_consent()]             revoke_consent()]
    ▼ (background_tasks)
[process_and_dispatch_
 consent_notification]
```

### Imports & Exports
- **Imports**: `datetime`, `logging`, `time`, `uuid`, `fastapi` (`APIRouter`, `BackgroundTasks`, `Header`, `HTTPException`, `Response`, `status`), `app.core.exceptions`, schemas from `app.schemas.common`, `app.schemas.abdm_m2_bridge`, `app.schemas.abdm_m3_consent`, services from `app.services.abdm_hip_bridge` and `app.services.abdm_consent`.
- **Exports**: `router: APIRouter()`
- **Downstream Consumers**: `app/api/v1/router.py` (mounted at `/abdm/m3/consent`).

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/api/v1/endpoints/abdm_m3_consent.py` manages patient consent lifecycles under the ABDM Milestone 3 framework:
1. `POST /consents/hip/notify`: Gateway webhook called when a citizen grants, modifies, expires, or revokes consent. The endpoint performs replay validation (300s clock drift), registers the audit event, returns `202 Accepted` synchronously in <200ms, and schedules background signature verification and callback dispatch to `/v0.5/consents/hip/on-notify`.
2. `GET /consents/{consent_id}`: Retrieves stored consent artefact details and active permission scopes by consent ID.
3. `GET /consents/patient/{patient_id}`: Queries all active and historical consent artefacts linked to a patient's ABHA address.
4. `POST /consents/{consent_id}/revoke`: Marks an active consent artefact as revoked in the registry.
5. `POST /consents/simulate`: Generates and ingests synthetic ABDM consent notifications for sandbox testing.

---

## Layer C: Technical Deep Dive & Invariant Analysis

1. **Unauthenticated Global Consent Revocation Vulnerability (`revoke_consent`)**:
   Lines 148-163 declare `POST /consents/{consent_id}/revoke`. This endpoint contains NO authentication dependency. Any unauthorized actor on the network who knows or enumerates a `consent_id` can unilaterally revoke active consent artefacts across the hospital, immediately cutting off clinical data transfers between health facilities (Denial of Clinical Care).
2. **Unauthenticated Patient Consent Enumeration (`get_consents_by_patient`)**:
   Lines 113-125 declare `GET /consents/patient/{patient_id}`. This endpoint lacks authentication. Any third party can supply a patient's ABHA address or ID and retrieve all consent grants, disclosing treating clinician identities, health information types (e.g. Diagnostic Report, Prescription, Discharge Summary), date ranges, and institutional recipients.
3. **Unauthenticated Consent Artefact Introspection (`get_consent_by_id`)**:
   Lines 95-110 declare `GET /consents/{consent_id}` without authentication, exposing detailed electronic health information consent boundaries to anonymous callers.
4. **Missing Gateway Webhook Mutual Authentication**:
   Like the M2 endpoints, `/consents/hip/notify` validates timestamp drift and request ID format, but does not verify Gateway mutual TLS or bearer authorization tokens.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-ABDM-M3C-F01` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m3_consent.py:148` | `revoke_consent` is completely unauthenticated, enabling arbitrary remote callers to revoke legitimate clinical consents (Denial of Service). |
| `BE-ABDM-M3C-F02` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m3_consent.py:113` | `get_consents_by_patient` lacks authentication and authorization checks, exposing complete patient consent histories to anonymous callers. |
| `BE-ABDM-M3C-F03` | **S2** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m3_consent.py:95` | `get_consent_by_id` allows unauthenticated inspection of clinical consent artefacts and permission scopes. |
| `BE-ABDM-M3C-F04` | **S2** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m3_consent.py:36` | Inbound gateway webhook `/consents/hip/notify` lacks Gateway token authentication or mTLS validation. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-ABDM-M3C-P01`: Restrict Consent Query & Revocation Endpoints

```diff
--- a/backend/app/api/v1/endpoints/abdm_m3_consent.py
+++ b/backend/app/api/v1/endpoints/abdm_m3_consent.py
@@ -8,6 +8,8 @@ from typing import List, Optional
 import uuid
 
-from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Response, status
+from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Response, status
+from app.core.dependencies import get_current_user
+from app.models.user import User
 
 from app.core.exceptions import EntityNotFoundException, ValidationException
@@ -98,3 +100,6 @@ async def inbound_gateway_consent_notify(
-async def get_consent_by_id(consent_id: str) -> APIResponse[ConsentRecordRepresentation]:
+async def get_consent_by_id(
+    consent_id: str,
+    current_user: User = Depends(get_current_user),
+) -> APIResponse[ConsentRecordRepresentation]:
     """Retrieve details and active permission scopes for a stored consent artefact."""
@@ -116,3 +121,6 @@ async def get_consent_by_id(consent_id: str) -> APIResponse[ConsentRecordRepres
-async def get_consents_by_patient(patient_id: str) -> APIResponse[List[ConsentRecordRepresentation]]:
+async def get_consents_by_patient(
+    patient_id: str,
+    current_user: User = Depends(get_current_user),
+) -> APIResponse[List[ConsentRecordRepresentation]]:
     """Retrieve all consent grants registered for a given patient ABHA address."""
@@ -151,3 +159,6 @@ async def simulate_consent(
-async def revoke_consent(consent_id: str) -> APIResponse[ConsentRecordRepresentation]:
+async def revoke_consent(
+    consent_id: str,
+    current_user: User = Depends(get_current_user),
+) -> APIResponse[ConsentRecordRepresentation]:
     """Manually revoke an active consent in the registry."""
```
