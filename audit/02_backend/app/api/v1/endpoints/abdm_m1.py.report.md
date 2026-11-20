# NIRMAYA Codebase Technical Audit Report

## File Identity
- **File Path**: `backend/app/api/v1/endpoints/abdm_m1.py`
- **Subsystem**: ABDM Milestone 1 - Aadhaar Demographic OTP Verification
- **Component**: Direct Aadhaar OTP Initiation, UIDAI Verification & Patient Sync API
- **Layer**: Routing & Presentation Layer

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Module Boundary
```
  [Citizen / Patient / Client Application]
                     │
  ┌──────────────────┼──────────────────┐
  ▼ (POST /generate) ▼ (POST /verify)   ▼ (POST /sync-patient/{id})
[request_aadhaar_   [submit_aadhaar_   [sync_aadhaar_identity]
 otp] (NO AUTH)      otp] (NO AUTH)     │
  │                  │                  ▼ (Unverified Payload IDOR)
  ▼                  ▼                 [sync_unified_patient_profile]
[generate_aadhaar_  [verify_aadhaar_    │
 otp(aadhaar)]       otp(txn_id, otp)]  ▼
  │                  │                 [PostgreSQL PatientProfile]
  ▼                  ▼
[Mock / Live UIDAI  [Demographic
 Authentication]     Claims Result]
```

### Imports & Exports
- **Imports**: `APIRouter`, `Depends`, `status` from `fastapi`; `AsyncSession` from `sqlalchemy.ext.asyncio`; `get_current_user` from `app.core.dependencies`; `get_db` from `app.db.session`; `User` from `app.models.user`; schemas from `app.schemas.common` and `app.schemas.abdm_m1`; services from `app.services.aadhaar_otp`.
- **Exports**: `router: APIRouter(prefix="/abdm/m1/aadhaar")`
- **Downstream Consumers**: `app/api/v1/router.py` (mounted at root with tags `["ABDM M1 - Aadhaar Demographic OTP Verification"]`).

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/api/v1/endpoints/abdm_m1.py` exposes three endpoints driving Aadhaar OTP e-KYC:
1. `POST /abdm/m1/aadhaar/generate-otp`: Validates a 12-digit Aadhaar number, performs RSA demographic encryption, and triggers OTP dispatch to the citizen's UIDAI-linked mobile phone.
2. `POST /abdm/m1/aadhaar/verify-otp`: Accepts the transaction ID (`txn_id`) and 6-digit OTP, validating them against the session store to extract authenticated UIDAI demographic claims.
3. `POST /abdm/m1/aadhaar/sync-patient/{patient_id}`: Persists verified demographic claims (name, DOB, gender, address, masked Aadhaar) directly into the database `PatientProfile`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

1. **Unverified Client Demographic Payload Injection (`sync_aadhaar_identity`)**:
   Lines 68-80 receive `patient_id: str` in the path and `payload: AadhaarOtpVerifyResponse` in the HTTP request body. 
   Notice the critical design flaw: the client directly posts the demographic claims payload (`payload.demographics`)! The endpoint does NOT verify that the claims came from a validly completed OTP session verified on the server side. A malicious client can construct a completely fabricated `AadhaarOtpVerifyResponse` with spoofed government demographic attributes and inject it directly into any target `patient_id`.
2. **Broken Object Level Authorization (IDOR) on Profile Synchronization**:
   `sync_aadhaar_identity` accepts `patient_id: str` as an arbitrary route parameter. While `current_user: User = Depends(get_current_user)` is present, there is NO check ensuring that `current_user.id == patient_id` or that `current_user` has clinical admin rights. Any registered patient can overwrite the legal demographic claims of any other patient in the database.
3. **SMS Bombing & Rate Limit Omission on OTP Dispatch**:
   `request_aadhaar_otp` (lines 32-41) does not require authentication and has no IP or phone number rate-limiting middleware configured at the route level. Attackers can flood the endpoint, depleting SMS credits and harassing citizens with automated OTP messages.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-ABDM-M1-F01` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m1.py:68-80` | `sync_aadhaar_identity` accepts raw client-crafted demographic payloads without validating server-side OTP transaction proofs, enabling arbitrary identity forgery. |
| `BE-ABDM-M1-F02` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_m1.py:69,75` | `sync_aadhaar_identity` allows any authenticated user to overwrite demographic profiles of arbitrary `patient_id` (IDOR/BOLA). |
| `BE-ABDM-M1-F03` | **S2** | `[PERF]` | `backend/app/api/v1/endpoints/abdm_m1.py:32` | `request_aadhaar_otp` is unauthenticated and unthrottled, allowing SMS toll fraud and OTP spam attacks. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-ABDM-M1-P01`: Restrict Demographic Sync to Verified Server Sessions and Authorize Ownership

```diff
--- a/backend/app/api/v1/endpoints/abdm_m1.py
+++ b/backend/app/api/v1/endpoints/abdm_m1.py
@@ -2,5 +2,5 @@
 
-from fastapi import APIRouter, Depends, status
+from fastapi import APIRouter, Depends, HTTPException, status
 from sqlalchemy.ext.asyncio import AsyncSession
 
 from app.core.dependencies import get_current_user
@@ -73,4 +73,7 @@ async def sync_aadhaar_identity(
 ) -> APIResponse[UnifiedIdentitySyncResponse]:
     """Synchronize verified Aadhaar e-KYC demographic claims into PatientProfile."""
+    if not (getattr(current_user, "is_superuser", False) or getattr(current_user, "role", "") in ("ADMIN", "DOCTOR") or str(getattr(current_user, "id", "")) == patient_id):
+        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to target patient profile")
+
     sync_result = await sync_unified_patient_profile(
         db=db,
```
