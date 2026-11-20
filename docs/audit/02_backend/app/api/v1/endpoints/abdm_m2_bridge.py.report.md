# NIRMAYA Codebase Technical Audit Report

## File Identity
- **File Path**: `backend/app/api/v1/endpoints/abdm_m2_bridge.py`
- **Subsystem**: ABDM Milestone 2 (M2) Health Information Provider (HIP) Bridge
- **Component**: Gateway Inbound Webhooks, Patient Discovery, Care Context Linkage & Telemetry Endpoints
- **Layer**: Routing & Presentation Layer

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Module Boundary
```
           [ABDM National Gateway / Simulation Cockpit]
                                │
    ┌───────────────────────────┼───────────────────────────┐
    ▼ (POST /users/auth/init)   ▼ (POST /care-contexts/...) ▼ (POST /links/link/...)
[inbound_gateway_auth_init]   [inbound_gateway_care_...]  [inbound_gateway_link_...]
    │                           │                           │
    ▼ (validate_gateway_headers)▼ (validate_gateway_headers)▼ (validate_gateway_headers)
[FastAPI 202 Accepted]        [FastAPI 202 Accepted]      [FastAPI 202 Accepted]
    │                           │                           │
    ▼ (background_tasks)        ▼ (background_tasks)        ▼ (background_tasks)
[dispatch_async_on_init]      [process_and_dispatch_...]  [process_and_dispatch_...]
                                │
                                ▼
                   [link_session_manager (RAM)]
                                │
                   [webhook_audit_store (RAM)]
```

### Imports & Exports
- **Imports**: `datetime`, `logging`, `time`, `uuid`, `fastapi` (`APIRouter`, `BackgroundTasks`, `Depends`, `Header`, `HTTPException`, `Response`, `status`), `sqlalchemy.ext.asyncio` (`AsyncSession`), schemas from `app.schemas.common` and `app.schemas.abdm_m2_bridge`, services from `app.services.abdm_hip_bridge`, `app.services.abdm_discovery`, and `app.services.abdm_linkage`.
- **Exports**: `router: APIRouter()`
- **Downstream Consumers**: `app/api/v1/router.py` (mounted at `/abdm/m2/bridge`).

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/api/v1/endpoints/abdm_m2_bridge.py` handles the NHA ABDM Milestone 2 protocol for Health Information Providers (HIP). It implements an asynchronous webhook architecture:
1. Inbound Webhooks from Gateway:
   - `POST /users/auth/init`: Gateway initiates citizen auth; server records event in audit store, returns `202 Accepted` synchronously in <200ms, and schedules background callback to `/v0.5/users/auth/on-init`.
   - `POST /care-contexts/discover`: Gateway queries care contexts by demographic attributes; server returns `202 Accepted` and launches background fuzzy matching and callback to `/v0.5/care-contexts/on-discover`.
   - `POST /links/link/init`: Gateway initiates care context linkage; server provisions an OTP session, returns `202 Accepted`, and schedules callback to `/v0.5/links/link/on-init`.
   - `POST /links/link/confirm`: Gateway submits citizen OTP; server verifies challenge token, returns `202 Accepted`, and dispatches `/v0.5/links/link/on-confirm`.
2. Simulation & Cockpit Tools:
   - `POST /discovery/simulate`: Tests fuzzy demographic matching against the database.
   - `POST /link/init/simulate`: Simulates care context linkage challenge from the UI.
   - `POST /link/confirm/simulate`: Simulates citizen OTP confirmation.
3. Telemetry & Auditing:
   - `GET /status`: Retrieves HIP bridge health.
   - `GET /events`: Lists recent inbound webhook events.
   - `GET /link/sessions`: Lists active link challenge sessions.
   - `GET /audit`: Compiles Milestone 2 compliance metrics.

---

## Layer C: Technical Deep Dive & Invariant Analysis

1. **Unauthenticated Active Session Introspection (`list_link_sessions_endpoint`)**:
   Lines 400-428 declare `GET /link/sessions`. This endpoint has ZERO authentication. Anyone on the network can query it and inspect unmasked citizen names, patient IDs, care context counts, transaction IDs, creation timestamps, and active OTP attempt counters.
2. **Missing Inbound Gateway Mutual Authentication / Signature Verification**:
   The webhook endpoints (`/users/auth/init`, `/care-contexts/discover`, `/links/link/init`, `/links/link/confirm`) only call `validate_gateway_headers`, which checks timestamp drift (<300s) and non-empty request IDs. There is NO verification of Gateway mutual TLS, NO bearer token validation against the NHA sandbox JWKS, and NO HMAC signature verification. Any unauthenticated caller can forge inbound gateway callbacks, injecting arbitrary linking attempts or fuzzy discovery scans.
3. **Unauthenticated Inspection of Webhook Event Logs (PII Leakage)**:
   Lines 132-144: `GET /events` exposes `WebhookEventItem` objects containing raw query parameters, patient names, and verified demographic identifiers without authentication.
4. **Unauthenticated Simulation State Mutation**:
   Endpoints `/discovery/simulate`, `/link/init/simulate`, and `/link/confirm/simulate` can be invoked anonymously to mutate in-memory link session states and trigger DB discovery queries.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-ABDM-M2-F01` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m2_bridge.py:400` | `list_link_sessions_endpoint` is completely unauthenticated, exposing active citizen link sessions, patient IDs, and OTP attempt counts. |
| `BE-ABDM-M2-F02` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m2_bridge.py:68,172,256,313` | Inbound gateway webhook endpoints lack mutual TLS or Gateway Bearer token validation, permitting unauthenticated webhook forgery. |
| `BE-ABDM-M2-F03` | **S2** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m2_bridge.py:133` | `list_webhook_events` is unauthenticated and exposes patient demographic PII and gateway payload details. |
| `BE-ABDM-M2-F04` | **S2** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m2_bridge.py:221,359,380` | Simulation endpoints allow unauthenticated users to trigger fuzzy matching database queries and mutate link session state. |
| `BE-ABDM-M2-F05` | **S3** | `[QUAL]` | `backend/app/api/v1/endpoints/abdm_m2_bridge.py:78` | Fallback from HTTP headers to JSON payload properties obscures transport-level header validation. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-ABDM-M2-P01`: Restrict Telemetry, Events & Link Sessions to Authorized Users

```diff
--- a/backend/app/api/v1/endpoints/abdm_m2_bridge.py
+++ b/backend/app/api/v1/endpoints/abdm_m2_bridge.py
@@ -10,6 +10,8 @@ from typing import List, Optional
 import uuid
 
 from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Response, status
+from app.core.dependencies import get_current_user
+from app.models.user import User
 from sqlalchemy.ext.asyncio import AsyncSession
 
 from app.db.session import get_db
@@ -137,4 +139,5 @@ async def get_hip_bridge_status() -> APIResponse[HipBridgeStatusResponse]:
-async def list_webhook_events(limit: int = 50) -> APIResponse[List[WebhookEventItem]]:
+async def list_webhook_events(
+    limit: int = 50,
+    current_user: User = Depends(get_current_user),
+) -> APIResponse[List[WebhookEventItem]]:
     """Retrieve recent inbound ABDM Gateway webhook events and response latencies."""
@@ -404,4 +407,5 @@ async def simulate_link_confirm_endpoint(
-async def list_link_sessions_endpoint(
+async def list_link_sessions_endpoint(
     limit: int = 50,
+    current_user: User = Depends(get_current_user),
 ) -> APIResponse[List[LinkSessionRepresentation]]:
     """List recent link challenge sessions with OTP state and remaining attempts."""
```
