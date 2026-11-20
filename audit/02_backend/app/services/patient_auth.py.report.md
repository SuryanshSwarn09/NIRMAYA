# Codebase Technical Audit Report: `backend/app/services/patient_auth.py`

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`patient_auth.py` provides the authentication, auto-registration, and identity issuance service layer for the Unified DigiLocker & Aadhaar OTP Passwordless Patient Gateway. It resolves citizen user identities from incoming e-KYC claims, auto-mints 14-digit Ayushman Bharat Health Account (ABHA) numbers and `@abdm` handles upon initial login, configures 30-day extended session longevity, and handles mobile OTP authentication fallbacks.

### System Topology & Auth Ingress
```
     [ DigiLocker e-KYC / Aadhaar OTP / Mobile SIM ]
                           |
                           v
     +---------------------------------------------+
     |             PatientAuthService              |
     +---------------------------------------------+
     | - Citizen Identity Matching & Profile Sync  |
     | - Auto-Minting 14-Digit ABHA & @abdm Handle |
     | - Extended 30-Day Session JWT Token Minter  |
     | - Walk-in Mobile OTP Fallback Flow          |
     +---------------------------------------------+
                           |
                  (AsyncSession ORM)
                           v
              [( PostgreSQL Database )]
              Tables: `users`, `patient_profiles`
```

### Module Metadata & Imports/Exports
- **Module Path:** `backend/app/services/patient_auth.py`
- **Component Classification:** Patient Authentication, Gateway & Auto-ABHA Minter
- **Lines of Code:** 351 LOC
- **Imports:** `datetime`, `re`, `typing`, `uuid`, `sqlalchemy.*`, `sqlalchemy.ext.asyncio.AsyncSession`, `app.core.exceptions.*`, `app.core.security.create_access_token`, `app.models.*`, `app.schemas.patient_auth.*`, `app.services.abdm_issuance._generate_raw_14_digit_abha`
- **Primary Exports:** `authenticate_or_register_patient`, `authenticate_mobile_fallback`

---

## Layer B: Plain-Language Developer Walkthrough

The service powers passwordless onboarding for citizens:
1. **Unified Authentication & Auto-Registration (`authenticate_or_register_patient`)**:
   - Searches for an existing citizen by email, phone, or masked Aadhaar.
   - If an existing user is found, it verifies the account, updates demographic claims (address, district, state, pin code), auto-mints missing ABHA numbers/handles, and commits changes.
   - If no user matches, it automatically provisions a new `User` record (role `PATIENT`), creates a linked `PatientProfile`, mints a 14-digit ABHA number, assigns an `@abdm` handle, and saves both entities.
   - Calculates session token expiration (30 days if `remember_me=True`, otherwise 24 hours), encodes a signed JWT, and returns `PatientUnifiedAuthResponse`.
2. **Mobile Fallback Authentication (`authenticate_mobile_fallback`)**:
   - Validates 10-digit mobile number and verification OTP.
   - Resolves existing patient profiles or registers walk-in patients on the fly with a newly minted ABHA number, returning an authenticated session.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Mandatory Demographic Claim Synchronization
When an existing citizen logs in via a verified government channel (e.g. DigiLocker), newly attested demographic values (verified address, district, state, and pin code) are synchronized into their PostgreSQL `PatientProfile` at lines 145–160, guaranteeing records reflect the latest sovereign e-KYC state.

### Invariant 2: Session Longevity Invariant
To prevent citizen drop-off in high-density rural clinics, session duration is governed by the `remember_me` parameter:
$$\text{Duration} = \begin{cases} 30 \text{ days} & \text{if } \text{remember\_me} = \text{True} \\ 24 \text{ hours} & \text{otherwise} \end{cases}$$

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
|---|---|---|---|---|
| `BE-SVC-PAU-F01` | **S1** | `[SEC]` | `backend/app/services/patient_auth.py:255-265` | Hardcoded Static Verification OTP `"123456"` in Production Code Path. `authenticate_mobile_fallback` explicitly asserts `if clean_otp != "123456": raise AuthenticationException(...)`, allowing anyone to authenticate into any citizen account by knowing their 10-digit mobile number and typing `123456`. |
| `BE-SVC-PAU-F02` | **S1** | `[SEC]` | `backend/app/services/patient_auth.py:85-100` | Masked Aadhaar ILIKE Query on Free-Text `address_line` Field. Performs `PatientProfile.address_line.ilike(f"%{request.masked_aadhaar}%")` to link an existing user. Any user who types an address that happens to contain "4821" will be linked to another citizen's account, causing account takeover and demographic hijacking. |
| `BE-SVC-PAU-F03` | **S2** | `[SEC]` | `backend/app/services/patient_auth.py:115-130, 160-175` | In-House Synthetic 14-Digit ABHA Number Minting (`_generate_raw_14_digit_abha`) without National Health Authority (NHA) ABDM Gateway Verification. Emits counterfeit ABHA identifiers (`91-XXXX-XXXX-XXXX`) into the local PostgreSQL database that fail verification across other national health facilities. |
| `BE-SVC-PAU-F04` | **S2** | `[QUAL]` | `backend/app/services/patient_auth.py:200-210` | Excessive 30-Day Session Token Expiration (`timedelta(days=30)`) on Sensitive Healthcare Portal Without Refresh Token Rotation or Device Binding. |
| `BE-SVC-PAU-F05` | **S3** | `[PERF]` | `backend/app/services/patient_auth.py:65-80` | Non-Indexed Disjunction in User Lookup (`or_(*conditions)`). |
| `BE-SVC-PAU-F06` | **S4** | `[DOC]` | `backend/app/services/patient_auth.py:10-18` | Missing UIDAI Demographics Match Score Policy Documentation. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch 1: Remove Dangerous Address-Line Masked Aadhaar Search (`BE-SVC-PAU-F02`)
```diff
--- a/backend/app/services/patient_auth.py
+++ b/backend/app/services/patient_auth.py
@@ -83,12 +83,2 @@ async def authenticate_or_register_patient(
-    # Fallback search by patient profile masked aadhaar if provided
-    if not user and request.masked_aadhaar:
-        pat_query = (
-            select(PatientProfile)
-            .options(selectinload(PatientProfile.user))
-            .where(PatientProfile.address_line.ilike(f"%{request.masked_aadhaar}%"))
-        )
-        pat_result = await db.execute(pat_query)
-        matched_profile = pat_result.scalars().first()
-        if matched_profile and matched_profile.user:
-            user = matched_profile.user
```

### Patch 2: Disallow Hardcoded Static OTP in Production (`BE-SVC-PAU-F01`)
```diff
--- a/backend/app/services/patient_auth.py
+++ b/backend/app/services/patient_auth.py
@@ -256,4 +256,6 @@ async def authenticate_mobile_fallback(
-    # In sandbox/simulation, accept standard verification OTP '123456'
-    if clean_otp != "123456":
-        raise AuthenticationException("Invalid or expired mobile verification OTP")
+    from app.services.sms_service import verify_mobile_otp
+    is_valid = await verify_mobile_otp(clean_phone, clean_otp)
+    if not is_valid:
+        raise AuthenticationException("Invalid or expired mobile verification OTP")
```
