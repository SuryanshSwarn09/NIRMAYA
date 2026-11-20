# NIRMAYA Codebase Technical Audit Report

## File Identity
- **File Path**: `backend/app/api/v1/endpoints/abdm_m3_crypto.py`
- **Subsystem**: ABDM Milestone 3 (M3) Cryptographic Key Exchange & Health Information Flow
- **Component**: Curve25519 ECDH Handshake, HKDF Derivation & Data Flow Router
- **Layer**: Routing & Presentation Layer

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Module Boundary
```
           [ABDM Gateway / Third-Party HIU / Attacker]
                                │
    ┌───────────────────────────┼───────────────────────────┐
    ▼ (POST /keys/generate)     ▼ (POST /exchange)          ▼ (GET /sessions)
[generate_ephemeral_key_pair] [compute_key_exchange]      [list_active_crypto_sessions]
    │ (NO AUTH)                 │ (UNAUTH ORACLE)           │ (UNAUTHENTICATED)
    ▼                           ▼                           ▼
[AbdmCryptoService.         [AbdmCryptoService.         [crypto_session_store.
 generate_key_pair()]        execute_key_exchange()]     list_active_sessions()]
                                │
                                ▼
                   [Curve25519 ECDH + HKDF]
                                │
               ┌────────────────┴────────────────┐
               ▼ (Orphaned / Unmounted)          ▼ (Mounted in router.py)
      [gateway_router (DEAD CODE)]      [router: /api/v1/abdm/m3/crypto]
      (/health-information/hip/request) (/request, /on-request)
```

### Imports & Exports
- **Imports**: `datetime`, `logging`, `typing` (`Any`, `Dict`, `List`, `Optional`), `uuid`, `fastapi` (`APIRouter`, `BackgroundTasks`, `Header`, `HTTPException`, `Query`, `Response`, `status`), `app.core.exceptions`, schemas from `app.schemas.abdm_m3_crypto`, services from `app.services.abdm_crypto` and `app.services.abdm_hip_bridge`.
- **Exports**: `router: APIRouter()`, `gateway_router: APIRouter()`
- **Downstream Consumers**: `app/api/v1/router.py` (mounts `router` at `/abdm/m3/crypto`; fails to mount `gateway_router`).

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/api/v1/endpoints/abdm_m3_crypto.py` implements the cryptographic handshake mandated by the NHA ABDM v0.5 Data Flow Specification:
1. `handle_inbound_hi_request`: Evaluates inbound health information requests, verifies consent artefacts, generates an ephemeral Curve25519 key pair and 32-byte nonce, performs Diffie-Hellman key agreement, derives symmetric AES-GCM encryption keys using HKDF-SHA256, and schedules an asynchronous acknowledgment callback (`HIOnRequestCallback`) to the gateway.
2. `handle_inbound_hi_on_request`: Ingests gateway acknowledgments.
3. Two routers are defined:
   - `gateway_router`: Mounts `/health-information/hip/request` and `/health-information/hip/on-request` intended for the official Gateway `/v0.5` root.
   - `router`: Mounts local utilities: `/request`, `/on-request`, `/keys/generate`, `/exchange`, `/sessions`, and `/sessions/{transaction_id}`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

1. **Unmounted Gateway Router (Architectural Dead Code)**:
   Line 46 declares `gateway_router = APIRouter()`, which defines lines 150-180 (`/health-information/hip/request` and `/health-information/hip/on-request`).
   However, inspecting `app/api/v1/router.py` (lines 23 and 72) reveals:
   `api_router.include_router(abdm_m3_crypto.router, prefix="/abdm/m3/crypto", tags=["ABDM M3 - Key Exchange & Cryptography"])`
   `gateway_router` is NEVER included in `api_router` or `main.py`! Consequently, the official NHA ABDM Gateway endpoint `/v0.5/health-information/hip/request` is completely missing from the running FastAPI application, causing all incoming live ABDM data exchange requests to fail with HTTP 404!
2. **Unauthenticated Cryptographic Session Introspection (`list_active_crypto_sessions`, `get_crypto_session`)**:
   Lines 271-296 expose `/sessions` and `/sessions/{transaction_id}` without authentication. Any external caller can query active transactions, retrieving `CryptoSessionDetail` objects that reveal transaction IDs, consent IDs, HIP public keys, and nonces.
3. **Unauthenticated Key Exchange Oracle (`compute_key_exchange`)**:
   Lines 240-269 allow any unauthenticated caller to submit public keys and nonces and compute HKDF-SHA256 derived keys, salt, and IVs. While mathematical operations in isolation are harmless, exposing raw crypto derivation routines publicly turns the hospital server into a compute worker for arbitrary external parties.
4. **Cryptographic Exception String Disclosure**:
   Line 260: `raise HTTPException(status_code=400, detail=f"Cryptographic computation failed: {str(e)}")` leaks raw internal cryptographic errors to clients.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-ABDM-M3K-F01` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m3_crypto.py:271-296` | `list_active_crypto_sessions` and `get_crypto_session` are unauthenticated, exposing active transaction IDs, consent IDs, public keys, and nonces. |
| `BE-ABDM-M3K-F02` | **S2** | `[QUAL]` | `backend/app/api/v1/endpoints/abdm_m3_crypto.py:46,150-180` | `gateway_router` is defined but never mounted in `router.py`, leaving the official NHA `/v0.5/health-information/hip/request` endpoint unmounted and unreachable. |
| `BE-ABDM-M3K-F03` | **S2** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m3_crypto.py:240-269` | Unauthenticated key exchange computation oracle allows arbitrary external parties to utilize server compute for ECDH/HKDF operations. |
| `BE-ABDM-M3K-F04` | **S2** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m3_crypto.py:260` | Raw cryptographic exception string leaked in HTTP 400 response detail. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-ABDM-M3K-P01`: Restrict Crypto Introspection and Sanitize Exceptions

```diff
--- a/backend/app/api/v1/endpoints/abdm_m3_crypto.py
+++ b/backend/app/api/v1/endpoints/abdm_m3_crypto.py
@@ -20,7 +20,9 @@ from typing import Any, Dict, List, Optional
 import uuid
 
-from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Response, status
+from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Response, status
+from app.core.dependencies import get_current_user
+from app.models.user import User
 
 from app.core.exceptions import ValidationException
@@ -260,3 +262,3 @@ async def compute_key_exchange(
     except Exception as e:
         logger.error(f"[compute_key_exchange] Computation failed: {e}")
-        raise HTTPException(status_code=400, detail=f"Cryptographic computation failed: {str(e)}")
+        raise HTTPException(status_code=400, detail="Cryptographic key exchange computation failed due to invalid key format")
@@ -274,3 +276,5 @@ async def compute_key_exchange(
-async def list_active_crypto_sessions() -> List[CryptoSessionDetail]:
+async def list_active_crypto_sessions(
+    current_user: User = Depends(get_current_user),
+) -> List[CryptoSessionDetail]:
     """Lists all unexpired cryptographic sessions stored in the HIP session cache."""
@@ -285,3 +289,6 @@ async def list_active_crypto_sessions() -> List[CryptoSessionDetail]:
-async def get_crypto_session(transaction_id: str) -> CryptoSessionDetail:
+async def get_crypto_session(
+    transaction_id: str,
+    current_user: User = Depends(get_current_user),
+) -> CryptoSessionDetail:
     """Retrieves session details for a specific data transfer transaction."""
```
