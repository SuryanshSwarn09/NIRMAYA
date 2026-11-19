# Technical Audit Report: backend/app/services/abdm_issuance.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/abdm_issuance.py` implements the service logic for ABDM Milestone 1 (M1): generating and linking 14-digit ABHA numbers, checking PHR handle availability, binding `@abdm` PHR addresses to patient profiles, and onboarding healthcare practitioners into the Healthcare Professional Registry (HPR). The audit identified significant compliance and security vulnerabilities: ABHA numbers are generated pseudo-randomly using local Verhoeff checksums rather than minting via official NHA ABDM Gateway APIs, and Doctor HPR onboarding unconditionally marks clinicians as verified without validating medical council credentials against the national registry.

### Architectural Roster
- **Module Name:** `backend/app/services/abdm_issuance.py`
- **Primary Responsibility:** ABHA number assignment, PHR address availability validation and linkage, and Doctor HPR onboarding.
- **Upstream Dependencies:**
  - `sqlalchemy.ext.asyncio.AsyncSession`
  - `app.core.exceptions.AppException`, `EntityNotFoundException`
  - `app.models.patient.PatientProfile`
  - `app.models.doctor.DoctorProfile`
  - `app.services.aadhaar_otp.generate_verhoeff`
  - `app.services.patient.get_patient_by_id`
  - `app.services.doctor.get_doctor_by_id`
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/abdm_m1.py`
  - `backend/app/api/v1/endpoints/doctor.py`
- **Exported Symbols:**
  - `RESERVED_HANDLES`
  - `generate_14_digit_abha`
  - `check_phr_availability`
  - `link_phr_address`
  - `onboard_doctor_hpr`

```
+-----------------------------------------------------------------------------------+
|                        ABDM Milestone 1 Issuance Flows                            |
|                                                                                   |
|  [Citizen / Patient]                                                              |
|          |                                                                        |
|          +--> [generate_14_digit_abha]                                            |
|          |         |-- Check existing patient.abha_number                         |
|          |         |-- Generate 14-digit local number (Prefix '91' + Verhoeff)    |
|          |         +--> Commit to PatientProfile.abha_number                      |
|          |                                                                        |
|          +--> [check_phr_availability]                                            |
|          |         |-- Validate regex & check RESERVED_HANDLES                    |
|          |         +--> SELECT PatientProfile WHERE abha_address = handle         |
|          |                                                                        |
|          +--> [link_phr_address]                                                  |
|                    +--> Bind verified handle to PatientProfile.abha_address       |
|                                                                                   |
|  [Clinician / Doctor]                                                             |
|          |                                                                        |
|          +--> [onboard_doctor_hpr]                                                |
|                    |-- Validate format '<handle>@hpr.abdm'                        |
|                    |-- Check collision in DoctorProfile                           |
|                    +--> Commit status="verified" (Mock/Local Bypass)              |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

This module provides the core onboarding and identity management functions required under ABDM M1:

1. **ABHA Number Creation (`generate_14_digit_abha`):** If a patient already has an assigned ABHA number, the function returns it idempotently. If not, `_generate_raw_14_digit_abha` builds a 14-digit candidate string starting with prefix `91-`, followed by 11 cryptographically secure random digits (`secrets.randbelow`), and terminates with a Verhoeff check digit. The candidate is checked against PostgreSQL for collisions and bound to `patient.abha_number`.
2. **PHR Address Availability Checking (`check_phr_availability`):** When a patient chooses a personalized health address (e.g., `rohit.sharma@abdm`), this method strips the `@abdm` suffix, checks the syntax (3–32 alphanumeric/dot/underscore characters), checks against a blacklist of reserved handles (`admin`, `root`, `nha`, `abdm`, `gov`, `doctor`, etc.), and queries `PatientProfile` for existing claims. If taken or invalid, it suggests alternative suffixes.
3. **PHR Address Linkage (`link_phr_address`):** Once chosen, this method re-validates the address, ensures no other citizen claims it, and commits the address to `patient.abha_address`.
4. **Doctor HPR Registration (`onboard_doctor_hpr`):** Allows doctors to register their national Healthcare Professional Registry (HPR) handle (e.g., `ananya.sharma@hpr.abdm`), along with their state medical council name and registration number. The function checks for handle collisions and updates `DoctorProfile`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Compliance Standards
- **ABDM 14-Digit Format:** The ABHA number must conform to `^\d{2}-\d{4}-\d{4}-\d{4}$` with valid Verhoeff parity.
- **Uniqueness Invariant:** No two patient profiles may possess identical ABHA numbers or `@abdm` addresses.
- **Reserved Handles Security:** System and administrative handles must never be registered by regular citizens.

### Vulnerabilities & Operational Risks
- **Synthetic ABHA Minting in Production:** Official ABDM compliance strictly requires ABHA numbers to be issued by the National Health Authority (NHA) via Aadhaar or Mobile OTP verification. Minting local `91-` numbers produces identifiers that fail lookups across the national health grid (Apollo, Max, government hospitals).
- **Unverified Clinician Attestation:** `onboard_doctor_hpr` marks clinicians with `status="verified"` without verifying the credentials against the National Medical Commission (NMC) or ABDM HPR gateway. Anyone with doctor access can claim arbitrary registration numbers and councils.
- **Race Condition in Address Binding:** `check_phr_availability` and `link_phr_address` query for address existence with a non-locking `SELECT`. Under concurrent requests, two users could reserve the same handle if the database column lacks a unique constraint or locking mechanism.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-ISS-F01` | **S1** | `[SEC]` | `abdm_issuance.py:42-58, 86-104` | Local synthetic 14-digit ABHA generation bypasses official NHA gateway enrollment, producing invalid unroutable national IDs. |
| `BE-SVC-ISS-F02` | **S1** | `[SEC]` | `abdm_issuance.py:238-299` | Clinician HPR onboarding automatically sets `status="verified"` without calling NMC or ABDM HPR registry verification APIs. |
| `BE-SVC-ISS-F03` | **S2** | `[SEC]` | `abdm_issuance.py:216-227` | Race window between handle availability check and record commit allows duplicate ABHA PHR address registration under concurrent requests. |
| `BE-SVC-ISS-F04` | **S3** | `[QUAL]` | `abdm_issuance.py:24-40` | `RESERVED_HANDLES` set is hardcoded in memory rather than managed via configurable rules or database seed tables. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Production NHA Verification Guard & Locking (`BE-SVC-ISS-F01`, `BE-SVC-ISS-F02`)

```diff
--- a/backend/app/services/abdm_issuance.py
+++ b/backend/app/services/abdm_issuance.py
@@ -60,6 +60,11 @@ async def generate_14_digit_abha(
     db: AsyncSession,
     patient_id: str,
 ) -> AbhaNumberCreateResponse:
+    if getattr(settings, "ENVIRONMENT", "development") == "production":
+        raise AppException(
+            "Local ABHA minting is disabled in production. ABHA numbers must be issued "
+            "via official ABDM Aadhaar OTP gateway enrollment (/api/v1/abdm/aadhaar/generate-otp)."
+        )
     patient = await get_patient_by_id(db, patient_id)
     if not patient:
         raise EntityNotFoundException("PatientProfile", patient_id)
@@ -280,6 +285,11 @@ async def onboard_doctor_hpr(
     if existing:
         raise AppException(f"HPR ID '{clean_hpr}' is already assigned to another accredited healthcare professional")
 
+    # Production check: verify credentials against NHA HPR registry
+    verification_status = "verified" if settings.ENVIRONMENT != "production" else "pending_nha_verification"
+
     # Update doctor credentials
     doctor.hpr_id = clean_hpr
     if registration_number:
@@ -287,6 +297,6 @@ async def onboard_doctor_hpr(
     if medical_council:
         doctor.medical_council = medical_council
 
     await db.commit()
     await db.refresh(doctor)
 
     return HprOnboardResponse(
         doctor_id=str(doctor.id),
         hpr_id=clean_hpr,
         registration_number=doctor.registration_number,
         medical_council=doctor.medical_council,
-        status="verified",
+        status=verification_status,
         verified_at=datetime.now(timezone.utc),
```
