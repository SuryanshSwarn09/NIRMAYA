# NIRMAYA Codebase Technical Audit Report

## File Identity
- **File Path**: `backend/app/api/v1/endpoints/abdm_issuance.py`
- **Subsystem**: ABDM Milestone 1 - ABHA Issuance & HPR Onboarding
- **Component**: 14-Digit ABHA Minting, PHR Handle Reservation & Doctor HPR Endpoints
- **Layer**: Routing & Presentation Layer

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Module Boundary
```
           [Citizen / Doctor / Authenticated Client]
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
  (POST /abha/create)    (POST /phr/link)        (POST /hpr/onboard)
[create_abha_number]    [link_phr_handle]       [onboard_clinician_hpr]
       │                       │                       │
       ▼ (IDOR Vulnerability)  ▼ (IDOR Vulnerability)  ▼ (IDOR Vulnerability)
[generate_14_digit_     [link_phr_address]      [onboard_doctor_hpr]
 abha(patient_id)]       (patient_id, handle)    (doctor_id, hpr_handle)
       │                       │                       │
       └───────────────────────┼───────────────────────┘
                               ▼
               [PostgreSQL Database (AsyncSession)]
```

### Imports & Exports
- **Imports**: `APIRouter`, `Depends`, `Query`, `status` from `fastapi`; `AsyncSession` from `sqlalchemy.ext.asyncio`; `get_current_user` from `app.core.dependencies`; `get_db` from `app.db.session`; `User` from `app.models.user`; schemas from `app.schemas.common` and `app.schemas.abdm_m1_issuance`; services from `app.services.abdm_issuance`.
- **Exports**: `router: APIRouter(prefix="/abdm/m1")`
- **Downstream Consumers**: `app/api/v1/router.py` (mounted at root with tags `["ABDM M1 - ABHA Issuance & HPR Onboarding"]`).

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/api/v1/endpoints/abdm_issuance.py` exposes clinical and administrative workflows for issuing ABDM digital credentials:
1. `POST /abdm/m1/abha/create`: Generates an official 14-digit ABHA number (`91-XXXX-XXXX-XXXX`) utilizing the Verhoeff check-digit algorithm and associates it with a `PatientProfile`.
2. `GET /abdm/m1/phr/check-availability`: Queries whether a requested `@abdm` PHR handle is currently free or registered, suggesting alternative prefixes if taken.
3. `POST /abdm/m1/phr/link`: Reserves and binds a validated `@abdm` address to a target patient profile.
4. `POST /abdm/m1/hpr/onboard`: Validates clinician medical council credentials and provisions a verified `@hpr.abdm` identity in the Healthcare Professional Registry.

---

## Layer C: Technical Deep Dive & Invariant Analysis

1. **Broken Object Level Authorization (BOLA / IDOR) on ABHA Minting (`create_abha_number`)**:
   In `create_abha_number` (lines 35-47), the endpoint injects `current_user: User = Depends(get_current_user)`. However, `current_user` is never used to verify tenancy or ownership:
   `await generate_14_digit_abha(db, payload.patient_id)`
   Any authenticated user (e.g. Patient A) can supply the `patient_id` of Patient B and mint or overwrite their official government health identity.
2. **Broken Object Level Authorization on PHR Address Linkage (`link_phr_handle`)**:
   Lines 74-85 accept `payload.patient_id` and `payload.abha_address`. Again, `current_user` is ignored. Any user can bind an arbitrary or offensive PHR handle to another citizen's profile.
3. **Privilege Escalation on Clinician HPR Onboarding (`onboard_clinician_hpr`)**:
   Lines 94-111 allow any authenticated user to claim HPR credentials on behalf of any `payload.doctor_id` without verifying that the caller possesses doctor administrative credentials or owns the associated doctor profile.
4. **Handle Enumeration Risk**:
   `check_handle_availability` (lines 55-65) is completely unauthenticated and unthrottled, allowing malicious actors to scrape and enumerate existing citizen health handles.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-ABDM-ISS-F01` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_issuance.py:35-41` | `create_abha_number` has an IDOR vulnerability: fails to verify that `current_user` owns `payload.patient_id` before issuing ABHA. |
| `BE-ABDM-ISS-F02` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_issuance.py:74-80` | `link_phr_handle` has an IDOR vulnerability: binds PHR handles to arbitrary `patient_id` without authorization checks. |
| `BE-ABDM-ISS-F03` | **S1** | `[SEC]` | `backend/app/api/v1/endpoints/abdm_issuance.py:94-106` | `onboard_clinician_hpr` lacks role verification, permitting non-doctors to onboard or modify arbitrary clinician HPR profiles. |
| `BE-ABDM-ISS-F04` | **S3** | `[PERF]` | `backend/app/api/v1/endpoints/abdm_issuance.py:55` | `check_handle_availability` lacks route-level rate limiting, enabling brute-force PHR handle enumeration. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-ABDM-ISS-P01`: Enforce Caller Ownership & Doctor Authorization

```diff
--- a/backend/app/api/v1/endpoints/abdm_issuance.py
+++ b/backend/app/api/v1/endpoints/abdm_issuance.py
@@ -2,5 +2,5 @@
 
-from fastapi import APIRouter, Depends, Query, status
+from fastapi import APIRouter, Depends, HTTPException, Query, status
 from sqlalchemy.ext.asyncio import AsyncSession
 
 from app.core.dependencies import get_current_user
@@ -39,4 +39,6 @@ async def create_abha_number(
 ) -> APIResponse[AbhaNumberCreateResponse]:
     """Issue official 14-digit ABHA number."""
+    if not (getattr(current_user, "is_superuser", False) or getattr(current_user, "role", "") in ("ADMIN", "DOCTOR") or str(getattr(current_user, "id", "")) == payload.patient_id):
+        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to target patient profile")
     response_data = await generate_14_digit_abha(db, payload.patient_id)
     return APIResponse(
@@ -78,4 +80,6 @@ async def link_phr_handle(
 ) -> APIResponse[PhrLinkResponse]:
     """Reserve and link @abdm handle to patient."""
+    if not (getattr(current_user, "is_superuser", False) or getattr(current_user, "role", "") in ("ADMIN", "DOCTOR") or str(getattr(current_user, "id", "")) == payload.patient_id):
+        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to target patient profile")
     response_data = await link_phr_address(db, payload.patient_id, payload.abha_address)
     return APIResponse(
@@ -98,4 +102,6 @@ async def onboard_clinician_hpr(
 ) -> APIResponse[HprOnboardResponse]:
     """Onboard clinician to national Healthcare Professional Registry."""
+    if not (getattr(current_user, "is_superuser", False) or getattr(current_user, "role", "") == "ADMIN" or (getattr(current_user, "role", "") == "DOCTOR" and str(getattr(current_user, "id", "")) == payload.doctor_id)):
+        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to onboard target doctor profile")
     response_data = await onboard_doctor_hpr(
         db=db,
```
