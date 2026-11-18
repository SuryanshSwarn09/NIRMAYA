# Audit Report: backend/app/schemas/abdm_m2_bridge.py

**Path:** `backend/app/schemas/abdm_m2_bridge.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 516 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Comprehensive Pydantic v2 schemas for ABDM Milestone 2 (M2) Health Information Provider (HIP) Bridge, covering asynchronous user authentication, fuzzy demographic patient discovery, and care context linkage.
- **Risk Level:** **S1 (High)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `LinkInitSimulateResponse.otp_sandbox_hint` transmits unmasked plain-text OTPs in API responses; if simulation endpoints are enabled or invoked in production, this leaks active authentication codes and bypasses two-factor authorization.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In ABDM Milestone 2, a hospital/clinic acts as a Health Information Provider (HIP). When a citizen uses an ABDM PHR app, they search for their records at the hospital. The ABDM Gateway sends asynchronous requests to the hospital's webhook endpoints: `/v0.5/care-contexts/discover` (patient discovery) and `/v0.5/links/link/init` & `/confirm` (care context linking). The hospital must respond immediately with HTTP 202 Accepted, and then dispatch an asynchronous callback (`/on-discover`, `/on-init`, `/on-confirm`) back to the central gateway. This file defines all incoming request and outbound callback payloads.

### How it works, step by step
1. **User Auth:** `GatewayAuthInitRequest` and `GatewayAuthOnInitCallback` handle practitioner-initiated demographic or OTP authentication via the gateway.
2. **Patient Discovery:** When a discovery request arrives (`GatewayPatientDiscoveryRequest`), the hospital runs fuzzy demographic matching (`PatientDiscoveryQuery`), generates similarity scores (`DemographicMatchBreakdown`), and returns discovered care contexts via `GatewayPatientOnDiscoverCallback`.
3. **Care Context Linkage:** The citizen selects care contexts to link (`GatewayLinkInitRequest`). The hospital dispatches an OTP and acknowledges via `GatewayLinkOnInitCallback`.
4. **Link Confirmation:** When the citizen submits the OTP (`GatewayLinkConfirmRequest`), the hospital validates the token and permanently links the contexts via `GatewayLinkOnConfirmCallback`.
5. **Auditing:** `AbdmM2AuditReport` summarizes webhook telemetry, callback latencies, and clock drift guards.

### Concepts and patterns used
- *ABDM Asynchronous Webhook-Callback Protocol:* Pairing every synchronous ingestion with a correlated asynchronous callback (`resp.requestId`).
- *Fuzzy Demographic Matching:* Scoring Name, Gender, and Year of Birth with ambiguity protection aborts.
- *Care Context Representation:* Grouping medical records into distinct clinical episodes (e.g., OPD consultations, discharge summaries).

### Key lines to read first
- `abdm_m2_bridge.py:163-223`: Patient discovery request and asynchronous callback schemas.
- `abdm_m2_bridge.py:302-356`: Link init request and on-init callback schemas.
- `abdm_m2_bridge.py:428-446`: `LinkInitSimulateResponse` and `otp_sandbox_hint`.
- `abdm_m2_bridge.py:493-515`: `AbdmM2AuditReport` system compliance schema.

### How to change it safely
Never change field names required by the NHA specification (e.g., `careContexts`, `referenceNumber`, `transactionId`). Always ensure `resp.requestId` is populated in callbacks to correlate with incoming requests.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing`, `pydantic` (BaseModel, Field, ConfigDict).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/abdm_m2_bridge_service.py`, `backend/app/services/abdm_discovery_service.py`, `backend/app/services/abdm_linking_service.py`, `backend/app/api/v1/endpoints/abdm_m2.py`.
- **Public Surface:** 24 Pydantic models.

### 2. Security [SEC]
- **Plaintext OTP Leakage in Simulation Response (CWE-200 / CWE-304):** `LinkInitSimulateResponse` (lines 435-438) defines `otp_sandbox_hint: Optional[str] = Field(default=None)`. If simulated link initiation endpoints are accessible in production environments, active OTP codes are transmitted directly to the client browser in JSON responses, completely compromising two-factor authentication (`BE-M2-F01`).
- **Unmasked OTP Tokens in Logs (CWE-532):** In `GatewayLinkConfirmConfirmation` (line 362) and `LinkConfirmSimulateRequest` (line 453), `token` and `otp_token` are plain string fields lacking `repr=False` or `SecretStr`, risking disclosure in access or debug logs (`BE-M2-F02`).
- **Ambiguity Protection:** `DemographicMatchBreakdown` and `AbdmM2AuditReport` enforce multi-match ambiguity aborts (line 506), preventing misattribution of sensitive patient health records.

### 3. Code quality [QUAL]
- High quality Pydantic v2 implementation with comprehensive field descriptions and `model_config = ConfigDict(from_attributes=True)` on every class.
- Explicit numerical bounds: `match_threshold` correctly specifies `ge=0.5, le=1.0`.

### 4. AI-generated-code smells [QUAL]
- None; the schemas adhere with clinical accuracy to the official NHA ABDM Gateway v0.5 protocol documentation.

### 5. Performance [PERF]
- Fast parsing with minimal serialization overhead across high-throughput webhook bursts.

### 6. Error handling & edge cases
- All callback models (`GatewayAuthOnInitCallback`, `GatewayPatientOnDiscoverCallback`, `GatewayLinkOnInitCallback`, `GatewayLinkOnConfirmCallback`) include an `error: Optional[Dict[str, Any]]` block, cleanly accommodating NHA error codes (e.g. 2500, 1400) without crashing deserialization.

### 7. Doc accuracy [DOC]
- Perfectly conforms to Month 3 Days 47–50 roadmap specifications.

### 8. Tests
- Covered by `backend/tests/test_abdm_m2.py` and `backend/tests/test_abdm_discovery.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-M2-F01 | S1 | [SEC] | 435-438 | Plaintext OTP exposed in simulated link responses | `otp_sandbox_hint: Optional[str] = Field(...)` | Ensure field is stripped or populated only when `settings.is_production is False` |
| BE-M2-F02 | S2 | [SEC] | 362, 453 | OTP token unmasked in string representation | `token: str = Field(...)` without `repr=False` | Add `repr=False` to `token` and `otp_token` Fields |

---

## Suggested Patches (NOT Applied)

### Patch BE-M2-F01 · Risk: Low · [UNTESTED]
Mask OTP tokens in request representations to prevent log leakage:

```diff
--- a/backend/app/schemas/abdm_m2_bridge.py
+++ b/backend/app/schemas/abdm_m2_bridge.py
@@ -361,3 +361,3 @@ class GatewayLinkConfirmConfirmation(BaseModel):
     linkRefNumber: str = Field(description="HIP link reference number returned in on-init")
-    token: str = Field(description="6-digit OTP code entered by patient")
+    token: str = Field(description="6-digit OTP code entered by patient", repr=False)
 
@@ -452,3 +452,3 @@ class LinkConfirmSimulateRequest(BaseModel):
     link_ref_number: str = Field(description="HIP linking reference number")
-    otp_token: str = Field(description="6-digit OTP code")
+    otp_token: str = Field(description="6-digit OTP code", repr=False)
```

---

## Verdict

**READY-WITH-FIXES** — Outstanding ABDM Milestone 2 schema suite implementing full NHA webhook-callback parity; masking OTP tokens and gating sandbox hints in production resolves security risks.
