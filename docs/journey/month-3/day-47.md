# Day 47: Milestone 10-02 - HIP Bridge Service & Webhook Ingest

**Milestone:** 10-02 (Month 3, Week 10)  
**Author:** Suryansh Swarn (`suryanshswarn@gmail.com`)  
**Status:** Completed & Certified  

---

## 1. Executive Summary

Day 47 initiates **Month 3, Week 10: ABDM Milestone 2 (M2) - Health Information Provider (HIP) Discovery & Care Contexts**.

Under ABDM Milestone 2, NIRMAYA operates as a certified Health Information Provider (HIP). Central to the ABDM architecture is an **asynchronous messaging protocol**:
1. The ABDM Central Gateway issues an inbound webhook request (e.g. `POST /v0.5/users/auth/init`) to the registered HIP listener.
2. The HIP enforces cryptographic header validation and **timestamp drift replay attack protection** ($\pm 300$ seconds / 5 minutes).
3. The HIP immediately acknowledges the webhook synchronously with **HTTP 202 Accepted** (under 200ms) without blocking the Gateway.
4. An asynchronous background task formats the official ABDM callback payload, preserves correlation reference (`resp.requestId == incomingRequestId`), and dispatches it to the ABDM Gateway endpoint (`POST /v0.5/users/auth/on-init`).
5. All webhook ingest transactions, processing latencies, and dispatch outcomes are recorded in a live telemetry audit store.

---

## 2. Technical Architecture & Endpoints

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   ABDM MILESTONE 2: ASYNCHRONOUS HIP BRIDGE FLOW                       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [ ABDM Central Gateway / CM ]                     [ NIRMAYA HIP Bridge ]             │
│                 │                                              │                       │
│                 │── 1. POST /v0.5/users/auth/init ────────────▶│                       │
│                 │   (Headers: REQUEST-ID, TIMESTAMP, X-CM-ID)  │                       │
│                 │                                              │                       │
│                 │◀── 2. HTTP 202 Accepted (Synchronous) ───────│ (Under 200ms)         │
│                 │                                              │                       │
│                 │                                       [ FastAPI BackgroundTask ]     │
│                 │                                       - Validate replay drift (±5m)  │
│                 │                                       - Resolve patient auth modes   │
│                 │                                       - Generate correlation payload │
│                 │                                              │                       │
│                 │◀── 3. POST /v0.5/users/auth/on-init ─────────│ (Asynchronous Dispatch)
│                 │   (Payload: resp.requestId == incomingId)    │                       │
│                 │                                              ▼                       │
│                                                     [ Webhook Telemetry Log ]          │
│                                                     - Ingest Audit Table               │
│                                                     - Latency & Status Reporting       │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Backend Components
- **Schemas (`backend/app/schemas/abdm_m2_bridge.py`):**
  - `GatewayAuthInitRequest`: Standard ABDM schema for `/v0.5/users/auth/init` with `requestId`, `timestamp`, and `query` block (`id`, `purpose`, `authMode`, `requester`).
  - `GatewayAuthOnInitCallback`: ABDM specification for `/v0.5/users/auth/on-init` featuring `auth.transactionId`, `auth.mode`, `auth.meta.hint`, and correlation pointer `resp.requestId`.
  - `WebhookEventItem`: Circular buffer audit record capturing `request_id`, `event_type`, `status` (`ACCEPTED`, `CALLBACK_SENT`), `latency_ms`, and `received_at`.
  - `HipBridgeStatusResponse`: Real-time telemetry report on registered HIP node (`IN0410000123`), active listeners, sandbox mode, and total processed events.
  - `TestPingResponse`: Structured report from end-to-end simulated webhook ping.
- **Service Layer (`backend/app/services/abdm_hip_bridge.py`):**
  - `validate_gateway_headers`: Replay defense checking that `|request_time - now_utc| <= 300` seconds and validating `REQUEST-ID` UUID format.
  - `dispatch_async_on_init_callback`: Background worker correlating outbound callbacks and recording delivery.
  - `webhook_audit_store`: Thread-safe circular in-memory buffer retaining the latest 50 webhook events.
  - `simulate_gateway_test_ping`: 1-click test simulation executing synchronous 202 Accepted and async callback delivery.
- **API Endpoints (`backend/app/api/v1/endpoints/abdm_m2_bridge.py` & `main.py`):**
  - `POST /v0.5/users/auth/init`: Gateway inbound webhook returning HTTP 202 Accepted.
  - `POST /api/v1/abdm/m2/bridge/users/auth/init`: Internal bridge mirror route.
  - `GET /api/v1/abdm/m2/bridge/status`: HIP node health and listener registration.
  - `GET /api/v1/abdm/m2/bridge/events`: Recent inbound webhook audit log.
  - `POST /api/v1/abdm/m2/bridge/test-ping`: Simulates Gateway ping.

---

## 3. Frontend Cal.com Components

- **`HipBridgeConsoleCard.tsx` (`frontend/src/components/clinical/HipBridgeConsoleCard.tsx`):**
  - Cal.com geometric design: `#ffffff` canvas, hairline borders (`#e5e7eb`), `rounded-[8px]` containers, and `rounded-[6px]` badges.
  - Live indicator: **HIP Node Online (ID: `IN0410000123` • NIRMAYA Apex Hospital)**.
  - Active Webhook Listeners: `POST /v0.5/users/auth/init` with 202 Accepted ingest.
  - Replay Defense indicator: `±300s Timestamp Drift Window`.
  - **[Simulate Gateway Ping]** action button: triggers test ping and displays real-time 202 Accepted status and correlated callback payload.
  - Live Inbound Webhook Audit Log table: lists incoming request IDs, event types, status (`202 Accepted`, `Callback Sent`), processing latency, and received time.
- **Mounted in Doctor EMR Cockpit (`frontend/src/app/doctor/page.tsx`):**
  - Displayed alongside `AbdmGatewayStatusCard` for complete clinical and administrative observability.

---

## 4. Verification & Testing Evidence

- **Dedicated Test Suite (`backend/tests/test_abdm_m2_hip_bridge.py`):**
  - **8 / 8 passed (100% green in 9.98s)**:
    - `test_inbound_auth_init_202_accepted`
    - `test_api_v1_bridge_auth_init`
    - `test_timestamp_drift_replay_protection` (verifies drift >300s rejected with HTTP 400)
    - `test_invalid_request_id_header` (verifies non-UUID rejected with HTTP 400)
    - `test_async_on_init_callback_correlation` (verifies `resp.requestId == incomingId`)
    - `test_bridge_status_endpoint`
    - `test_test_ping_simulation`
    - `test_webhook_events_endpoint`
- **Frontend Quality Assurance:**
  - `npx tsc --noEmit`: **0 errors**.
  - `npm run build`: **0 errors**, all 13 routes compiled cleanly.
