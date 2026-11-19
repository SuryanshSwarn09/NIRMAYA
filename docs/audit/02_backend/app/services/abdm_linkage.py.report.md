# Technical Audit Report: backend/app/services/abdm_linkage.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/abdm_linkage.py` implements the ABDM Milestone 2 (M2) Care Context Linkage and OTP Verification engine. It handles inbound discovery and link initiation (`/v0.5/links/link/init`), generates 6-digit cryptographic OTP challenges, masks recipient phone numbers, verifies citizen OTP submissions (`/v0.5/links/link/confirm`), and dispatches asynchronous callbacks to the ABDM Gateway (`/v0.5/links/link/on-init` and `/v0.5/links/link/on-confirm`). The audit revealed critical vulnerabilities: active linkage sessions are stored in an unshared in-memory dictionary that breaks on multi-worker deployments, link confirmation status is never persisted to the database, and predictable default OTPs (`"123456"`) are used when `DEBUG` is true.

### Architectural Roster
- **Module Name:** `backend/app/services/abdm_linkage.py`
- **Primary Responsibility:** Care context link session lifecycle, OTP challenge generation, verification, and Gateway callback orchestration.
- **Upstream Dependencies:**
  - `sqlalchemy.ext.asyncio.AsyncSession`
  - `app.core.config.settings`
  - `app.models.patient.PatientProfile`
  - `app.models.user.User`
  - `app.schemas.abdm_m2_bridge` (`GatewayLinkInitRequest`, `GatewayLinkConfirmRequest`, etc.)
  - `app.services.abdm_discovery.resolve_patient_care_contexts`
  - `app.services.abdm_hip_bridge.webhook_audit_store`
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/abdm_linkage.py`
  - `backend/app/api/v1/endpoints/abdm_m2.py`
- **Exported Symbols:**
  - `AbdmLinkSession`, `AbdmLinkSessionManager`, `link_session_manager`
  - `mask_phone_number`
  - `initiate_care_context_linking`
  - `confirm_care_context_linking`
  - `dispatch_async_on_link_init_callback`
  - `dispatch_async_on_link_confirm_callback`
  - `simulate_care_context_link_init`

```
+-----------------------------------------------------------------------------------+
|                        ABDM M2 Care Context Linkage Engine                        |
|                                                                                   |
|  [ABDM Gateway / User]                                                            |
|          |                                                                        |
|          +--> POST /v0.5/links/link/init                                          |
|          |         |                                                              |
|          |         v                                                              |
|          |    [initiate_care_context_linking]                                     |
|          |         |-- Resolve Patient & Care Contexts from DB                    |
|          |         |-- Generate 6-digit OTP & LINK-REF-XXXXXXXX                   |
|          |         |-- Store AbdmLinkSession in link_session_manager (In-Memory)  |
|          |         +--> dispatch_async_on_link_init_callback (/on-init)           |
|          |                                                                        |
|          +--> POST /v0.5/links/link/confirm                                       |
|                    |                                                              |
|                    v                                                              |
|               [confirm_care_context_linking]                                      |
|                    |-- verify_otp: validate token against stored session          |
|                    |-- Check 10-minute expiry & decrement attempts (max 3)        |
|                    |-- Update session.status = 'CONFIRMED' (In-Memory Only!)      |
|                    +--> dispatch_async_on_link_confirm_callback (/on-confirm)     |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

When an Ayushman citizen links their past hospital visits (care contexts) to their ABHA app (e.g., Aarogya Setu, ABHA app), this service manages the handshake:

1. **Link Initiation (`initiate_care_context_linking`):** The ABDM Gateway forwards a link request specifying the patient's ABHA address or profile reference number and requested care contexts. The service resolves the patient profile in PostgreSQL, checks matching care contexts using `resolve_patient_care_contexts`, and creates an `AbdmLinkSession`.
2. **Session & OTP Generation (`create_session`):** Generates a random link reference number (`LINK-REF-XXXXXXXX`) and a 6-digit OTP. The session is stored in the singleton `link_session_manager` with a 10-minute expiry and an allowance of 3 verification attempts.
3. **Gateway Callback (`dispatch_async_on_link_init_callback`):** Asynchronously dispatches an HTTP POST to the Gateway's `/v0.5/links/link/on-init` endpoint, including the masked patient phone number (e.g., `+91 ******3210`) so the citizen knows where the SMS was dispatched. In non-production environments, the callback is simulated.
4. **Link Confirmation (`confirm_care_context_linking`):** When the citizen submits the received OTP via `/v0.5/links/link/confirm`, `verify_otp` validates the token. If valid, the session status transitions to `CONFIRMED`.
5. **Gateway Confirmation Callback (`dispatch_async_on_link_confirm_callback`):** Notifies the Gateway via `/v0.5/links/link/on-confirm` with the list of confirmed care contexts and the patient display name.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Specification Requirements
- **Max Attempt Lockout:** A linkage challenge must fail permanently after 3 consecutive invalid OTP attempts to prevent brute-forcing.
- **Expiry Bound:** Link sessions must expire after 10 minutes (600 seconds).
- **Phone Privacy:** The telephone number transmitted to ABDM Gateway must be masked showing at most the country code and trailing 4 digits.

### Security & Operational Flaws
- **Session Isolation in Multi-Worker Environments:** `AbdmLinkSessionManager` stores sessions in a local dictionary (`self._sessions: Dict[str, AbdmLinkSession]`). In multi-worker Uvicorn setups, if `/init` lands on worker 1 and `/confirm` lands on worker 2, worker 2 has no record of the session, causing failure.
- **Absence of Database Persistence for Linked Contexts:** When `verify_otp` succeeds, `session.status` is set to `"CONFIRMED"` strictly in memory. No database table records that the patient's care contexts are officially linked to their ABHA address.
- **Predictable Sandbox OTP:** Line 111 uses `"123456"` when `settings.DEBUG` is true. If `DEBUG` is accidentally set to true in production, any user can link any patient's records using `"123456"`.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-LNK-F01` | **S1** | `[SEC]` | `abdm_linkage.py:111` | Predictable static OTP `"123456"` is generated whenever `settings.DEBUG` is True, allowing unauthorized account linkage if debug mode is active. |
| `BE-SVC-LNK-F02` | **S1** | `[SEC]` | `abdm_linkage.py:86-130` | In-memory `AbdmLinkSessionManager` is not shared across multi-worker Uvicorn processes, causing OTP verification failures in production. |
| `BE-SVC-LNK-F03` | **S2** | `[QUAL]` | `abdm_linkage.py:300-313` | Link confirmation is held exclusively in memory; care context linkage state is never committed to PostgreSQL, causing state loss on restart. |
| `BE-SVC-LNK-F04` | **S2** | `[SEC]` | `abdm_linkage.py:223-299` | Lack of IP or account-level rate limiting on `initiate_care_context_linking` allows automated SMS exhaustion and user enumeration. |
| `BE-SVC-LNK-F05` | **S3** | `[QUAL]` | `abdm_linkage.py:203-216` | Phone masking utility does not strictly validate phone number length prior to slicing, risking incorrect masking for non-standard formats. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Production CSPRNG OTP & Environment Guard (`BE-SVC-LNK-F01`)

```diff
--- a/backend/app/services/abdm_linkage.py
+++ b/backend/app/services/abdm_linkage.py
@@ -107,8 +107,11 @@ class AbdmLinkSessionManager:
             token_hex = uuid.uuid4().hex[:8].upper()
             link_ref = f"LINK-REF-{token_hex}"
 
-            # Default to predictable test OTP in sandbox if not specified
-            otp_code = otp or ("123456" if settings.DEBUG else "".join(secrets.choice("0123456789") for _ in range(6)))
+            # Require CSPRNG generated OTP unless explicit simulation override is provided in test
+            if getattr(settings, "ENVIRONMENT", "development") == "production":
+                otp_code = "".join(secrets.choice("0123456789") for _ in range(6))
+            else:
+                otp_code = otp or ("123456" if settings.DEBUG else "".join(secrets.choice("0123456789") for _ in range(6)))
             now = datetime.now(timezone.utc)
             expires = now + timedelta(minutes=ttl_minutes)
```
