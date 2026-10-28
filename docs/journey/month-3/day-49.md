# Day 49: Milestone 10-04 - ABDM M2 Care Context Linkage & OTP Verification

**Milestone:** 10-04 (Month 3, Week 10 / ABDM M2 Care Context Linkage Protocol)  
**Author:** Suryansh Swarn (`suryanshswarn@gmail.com`)  
**Status:** Completed & Certified  

---

## 1. Executive Summary

Day 49 delivers the complete, production-grade implementation of the **ABDM Milestone 2 (M2) Care Context Linkage & OTP Verification Protocol** for NIRMAYA Health Information Provider (HIP) nodes.

Under the National Health Authority (NHA) ABDM M2 specifications, once a citizen discovers their matching care contexts at a HIP node via their Personal Health Record (PHR) application (e.g., ABHA App, Aarogya Setu, Paytm Health), they proceed to link these clinical records to their ABHA address. This linkage enables granular, patient-mediated data sharing across India's federated health network.

The care context linking protocol requires a multi-step, asynchronous, stateful verification exchange involving direct SMS OTP challenges, replay-defended gateway webhooks, strict correlation validation, and permanent record linkage.

---

## 2. Multi-Step Care Context Linkage Protocol Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               ABDM M2 CARE CONTEXT LINKAGE & OTP VERIFICATION LIFECYCLE                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   Citizen (PHR App)         ABDM Gateway                 NIRMAYA HIP Node              │
│          │                       │                              │                      │
│   1. Select Care Contexts        │                              │                      │
│      & Click "Link Records" ────►│                              │                      │
│                                  │   POST /v0.5/links/link/init │                      │
│                                  │ ────────────────────────────►│                      │
│                                  │                              │                      │
│                                  │   HTTP 202 Accepted (Sync)   │ 1. Validate Replay   │
│                                  │ ◄────────────────────────────│ 2. Find Patient Vault│
│                                  │                              │ 3. Create Session    │
│                                  │                              │    (10m TTL, 3 tries)│
│                                  │                              │ 4. Issue 6-digit OTP │
│                                  │                              │ 5. Direct SMS / Mock │
│                                  │                              │                      │
│                                  │  POST /v0.5/links/link/on-init                      │
│                                  │ ◄────────────────────────────│ (Async Callback with │
│                                  │                              │  transactionRef &    │
│                                  │                              │  masked phone)       │
│                                  │                              │                      │
│   2. Citizen receives OTP SMS    │                              │                      │
│      and enters 6-digit code────►│                              │                      │
│                                  │ POST /v0.5/links/link/confirm│                      │
│                                  │ ────────────────────────────►│                      │
│                                  │                              │                      │
│                                  │   HTTP 202 Accepted (Sync)   │ 1. Lookup Session    │
│                                  │ ◄────────────────────────────│ 2. Validate OTP code │
│                                  │                              │ 3. Decrement tries   │
│                                  │                              │ 4. Mark CONFIRMED    │
│                                  │                              │ 5. Commit Linkage    │
│                                  │                              │                      │
│                                  │ POST /v0.5/links/link/on-confirm                    │
│                                  │ ◄────────────────────────────│ (Async Callback with │
│                                  │                              │  confirmed patient & │
│                                  │                              │  care context list)  │
│                                  │                              │                      │
│   3. Records Linked & Visible    │                              │                      │
│      in Citizen PHR Vault  ◄─────│                              │                      │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Session Management & Security Engineering

The care context linking process is backed by a thread-safe in-memory and database-backed session engine (`AbdmLinkSessionManager`) implemented in `backend/app/services/abdm_linkage.py`:

1. **Stateful Session Lifecycle:**
   - Every `init` request mints a cryptographically strong UUID `transaction_ref` (or `link_reference`).
   - Session statuses: `PENDING` -> `CONFIRMED` / `EXPIRED` / `FAILED`.
2. **Strict Time-To-Live (TTL):**
   - OTP sessions expire after exactly 600 seconds (10 minutes).
   - Attempts made after expiry are immediately rejected with ABDM Error `1440: Link session expired`.
3. **Attempt Decoupling & Brute-Force Defense:**
   - Strict maximum of 3 verification attempts.
   - Each invalid OTP entry decrements remaining attempts and returns ABDM Error `1441: Invalid OTP. X attempts remaining`.
   - On the 3rd failed attempt, the session transitions to `FAILED` and is locked against further input.
4. **Privacy-Preserving Phone Masking:**
   - Patient mobile numbers are masked following ABDM norms (e.g., `+91 9876543210` -> `+91 ******3210`), ensuring sensitive identifiers are not exposed in logs or callbacks.
5. **Replay & Timestamp Protection:**
   - Inbound webhook headers (`REQUEST-ID`, `TIMESTAMP`) are strictly enforced with $\pm 300$s clock drift tolerance.
   - Idempotency checks prevent duplicate executions of identical request IDs.

---

## 4. Endpoints & Schemas Implemented

### ABDM Gateway Inbound Webhooks:
- **`POST /v0.5/links/link/init`** (NHA Standard):
  - Validates gateway auth and replay headers.
  - Spawns background worker `process_inbound_link_init_worker`.
  - Returns synchronous `202 Accepted` acknowledgment.
  - Dispatches `POST /v0.5/links/link/on-init` to ABDM Gateway.
- **`POST /v0.5/links/link/confirm`** (NHA Standard):
  - Validates gateway auth and replay headers.
  - Spawns background worker `process_inbound_link_confirm_worker`.
  - Returns synchronous `202 Accepted` acknowledgment.
  - Dispatches `POST /v0.5/links/link/on-confirm` to ABDM Gateway.

### Interactive Clinical Sandboxing & Verification Endpoints:
- **`POST /api/v1/abdm/m2/bridge/link/init/simulate`**:
  - Allows clinicians and sandbox operators to initiate linking challenges for any patient profile.
  - Returns transaction reference, masked phone, TTL, and generated sandbox OTP.
- **`POST /api/v1/abdm/m2/bridge/link/confirm/simulate`**:
  - Validates OTP submissions against active sessions.
  - Returns verification status, remaining attempts, and linked care context records.
- **`GET /api/v1/abdm/m2/bridge/link/sessions`**:
  - Lists active and historical link sessions with timestamps, attempt counts, and status filters.

---

## 5. Cal.com Design System Frontend Implementation

### `CareContextLinkageModal.tsx` (`frontend/src/components/clinical/CareContextLinkageModal.tsx`)
A 3-step geometric wizard adhering strictly to the Cal.com design language:
- **Canvas & Typography:** Pure white `#ffffff` canvas, hairline borders (`#e5e7eb`), sans-serif typography, dark action buttons (`#111827`), geometric radii (`rounded-[8px]` containers, `rounded-[6px]` badges).
- **Step 1 - Patient Selection & Care Context Resolution:**
  - Fast-pick sandbox patient pills (`Arun Patel`, `Priya Sharma`, `Rahul Verma`).
  - Custom ABHA / Patient Reference input with real-time care context resolution.
  - Previews discovered clinical consultations and diagnostic panels before initiating linkage.
- **Step 2 - 6-Digit OTP Verification:**
  - Masked mobile display (`+91 ******3210`) with live countdown timer (10:00).
  - 6-digit individual PIN input cells with auto-focus and keyboard navigation.
  - Sandbox 1-click OTP autofill badge for rapid local testing.
  - Real-time attempt warning banners when invalid codes are submitted.
- **Step 3 - Linked Records Confirmation:**
  - High-confidence verification card with timestamp and transaction reference badge.
  - Summary of permanently linked care context references.
  - Collapsible JSON inspector showing raw ABDM `POST /v0.5/links/link/on-confirm` payload for audit review.

### Integration in `HipBridgeConsoleCard.tsx`:
- Added `"Link Care Contexts"` button alongside `"Simulate Discovery"` in the HIP Bridge header.
- Updated active listener telemetry in the bridge console to reflect `/v0.5/links/link/init`, `on-init`, `confirm`, and `on-confirm`.

---

## 6. Verification & Automated Test Evidence

### Dedicated Test Suite: `backend/tests/test_abdm_m2_linkage.py`
10 out of 10 automated tests passing with 100% green status:
1. `test_mask_phone_number`: Validates privacy masking format (+91 ******XXXX).
2. `test_link_session_manager_lifecycle`: Full session lifecycle from pending to confirmed.
3. `test_link_session_manager_invalid_otp_and_decrement`: Validates attempt counter decrement and failure lockout.
4. `test_link_session_manager_expired`: Validates TTL expiration logic.
5. `test_link_session_nonexistent_reference`: Validates handling of invalid transaction references.
6. `test_initiate_care_context_linking_success`: Validates synchronous 202 Accepted and session creation.
7. `test_initiate_care_context_linking_patient_not_found`: Validates ABDM Error 1440 on unknown patient identifiers.
8. `test_confirm_care_context_linking`: Validates complete OTP confirmation flow.
9. `test_simulate_link_init_and_confirm`: Validates operator simulation endpoints.
10. `test_dispatch_async_callbacks_telemetry`: Validates background callback dispatch and webhook audit telemetry.

### Suite Results:
- **`test_abdm_m2_linkage.py`:** 10 / 10 passed (0.41s)
- **All ABDM M2 Tests Combined (`test_abdm_m2_hip_bridge.py`, `test_abdm_m2_discovery.py`, `test_abdm_m2_linkage.py`):** **28 / 28 passed in 4.90s**
- **TypeScript Static Typecheck (`npx tsc --noEmit`):** **0 errors**
- **Next.js 15 Production Build (`npm run build`):** **13 / 13 static pages generated cleanly with 0 errors**
