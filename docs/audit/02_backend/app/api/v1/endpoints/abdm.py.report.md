# NIRMAYA Codebase Technical Audit Report

## File Identity
- **File Path**: `backend/app/api/v1/endpoints/abdm.py`
- **Subsystem**: ABDM Gateway & National Interoperability
- **Component**: Gateway Status, Session Management & RSA Cryptography API
- **Layer**: Routing & Presentation Layer

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Module Boundary
```
  [Client / Frontend / Health Interop Client]
                     │
  ┌──────────────────┴──────────────────┐
  ▼ (GET /abdm/status)                  ▼ (POST /abdm/crypto/encrypt-demographics)
[get_gateway_status]                  [encrypt_demographics] (UNAUTHENTICATED)
  │                                     │
  ▼                                     ▼
[ABDMGatewayClient]                   [ABDMRSAEncryptionManager]
  │ (OAuth v0.5 /sessions)              │ (RSA-OAEP-256)
  ▼                                     ▼
[National Gateway Sandbox]            [Base64 Encrypted Ciphertext]
```

### Imports & Exports
- **Imports**: `APIRouter`, `Depends`, `HTTPException`, `status` from `fastapi`; `BaseModel`, `Field` from `pydantic`; `ABDMGatewayClient`, `get_abdm_gateway_client` from `app.abdm.client`; `ABDMRSAEncryptionManager`, `get_abdm_encryption_manager` from `app.abdm.security.rsa`; `get_current_user` from `app.core.dependencies`; `User` from `app.models.user`; schemas from `app.schemas.common` and `app.schemas.abdm`.
- **Exports**: `router: APIRouter(prefix="/abdm")`
- **Downstream Consumers**: `app/api/v1/router.py` (mounted at root with tags `["ABDM Gateway & National Interoperability"]`).

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/api/v1/endpoints/abdm.py` exposes REST endpoints interfacing with the NHA ABDM Gateway:
1. `GET /abdm/status`: Ingests gateway status, token health, and sandbox parameters.
2. `POST /abdm/sessions/refresh`: Forces invalidation of cached bearer tokens and requests a fresh token from `/v0.5/sessions`.
3. `GET /abdm/crypto/public-key`: Exports active RSA-2048 public key certificate in PEM format along with SHA-256 fingerprint.
4. `POST /abdm/crypto/encrypt-demographics`: Encrypts patient demographic dictionaries using RSA-OAEP SHA-256 for compliant ABDM dispatch.
5. `POST /abdm/crypto/decrypt-demographics`: Authenticated endpoint allowing authorized users to decrypt inbound demographic ciphertext using the facility private key.

---

## Layer C: Technical Deep Dive & Invariant Analysis

1. **Unauthenticated Public Encryption Oracle (`encrypt_demographics`)**:
   Line 98-115 declares `def encrypt_demographics(payload: ABDMEncryptionPayload, crypto_mgr: ABDMRSAEncryptionManager = Depends(get_abdm_encryption_manager))`. Notice the complete absence of `current_user: User = Depends(get_current_user)`. Any anonymous caller on the network can use NIRMAYA's server as an encryption oracle, generating validly signed/encrypted NHA demographic envelopes.
2. **Decryption Error Information Leakage**:
   Lines 111-114 and 137-140:
   `detail=f"Failed to decrypt demographic payload: {str(e)}"`
   Leaking raw exception strings (`ValueError: Ciphertext length must be equal to key size`, `IndexError`, or specific padding errors) provides attackers with an oracle to distinguish padding failures from formatting errors, facilitating Bleichenbacher-style or Manger-style chosen-ciphertext attacks.
3. **Session Refresh Without RBAC**:
   Line 59-65: `refresh_gateway_session` requires `current_user: User = Depends(get_current_user)`. However, it does not check if `current_user.role == UserRole.ADMIN`. Any low-privileged patient or staff user can flood the gateway token refresh endpoint, exhausting NHA API rate limits and disrupting health data exchange for the entire hospital.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-ABDM-EP-F01` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm.py:98` | `encrypt_demographics` lacks authentication dependency, acting as an unauthenticated encryption oracle for arbitrary demographic data. |
| `BE-ABDM-EP-F02` | **S2** | `[SEC]` | `backend/app/api/v1/endpoints/abdm.py:113,139` | Raw cryptographic exception string leaked in HTTP 400 response detail, providing error oracle clues. |
| `BE-ABDM-EP-F03` | **S2** | `[SEC]` | `backend/app/api/v1/endpoints/abdm.py:59-62` | `refresh_gateway_session` lacks role-based access control, allowing non-admin users to force gateway token renewals. |
| `BE-ABDM-EP-F04` | **S3** | `[QUAL]` | `backend/app/api/v1/endpoints/abdm.py:79` | Unauthenticated public key endpoint does not cache response headers (`Cache-Control`), triggering redundant RSA serialization. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-ABDM-EP-P01`: Secure Demographic Encryption and Redact Crypto Errors

```diff
--- a/backend/app/api/v1/endpoints/abdm.py
+++ b/backend/app/api/v1/endpoints/abdm.py
@@ -58,6 +58,7 @@ async def get_gateway_status(
 )
 async def refresh_gateway_session(
     current_user: User = Depends(get_current_user),
+    _admin: None = Depends(lambda user=Depends(get_current_user): None if getattr(user, "is_superuser", False) or getattr(user, "role", "") == "ADMIN" else (_ for _ in ()).throw(HTTPException(status_code=403, detail="Admin privilege required"))),
     gateway_client: ABDMGatewayClient = Depends(get_abdm_gateway_client),
 ) -> APIResponse[GatewayStatusResponse]:
     """Force acquisition of a fresh session token from the ABDM Gateway."""
@@ -98,6 +99,7 @@ def get_public_key(
 def encrypt_demographics(
     payload: ABDMEncryptionPayload,
+    current_user: User = Depends(get_current_user),
     crypto_mgr: ABDMRSAEncryptionManager = Depends(get_abdm_encryption_manager),
 ) -> APIResponse[ABDMEncryptedResponse]:
     """Encrypt a demographic dictionary using the active ABDM RSA public key."""
@@ -111,7 +113,7 @@ def encrypt_demographics(
     except Exception as e:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
-            detail=f"Failed to encrypt demographic payload: {str(e)}",
+            detail="Failed to encrypt demographic payload due to invalid format or parameters",
         )
 
 
@@ -137,4 +139,4 @@ def decrypt_demographics(
     except Exception as e:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
-            detail=f"Failed to decrypt demographic payload: {str(e)}",
+            detail="Failed to decrypt demographic payload: invalid ciphertext or padding",
         )
```
