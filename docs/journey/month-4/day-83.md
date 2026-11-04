# Day 83: Guardian Access Delegation Protocols & Consent Artifact Interceptor

**Milestone:** 17-03  
**Theme:** Week 17: Dependent & Family Health Proxy and Zero-Contamination Architecture  
**Status:** **COMPLETED** (791 Tests Passing across 47 Modules, 100% Green)

---

## Executive Summary

Today marks **Day 83**, delivering **Milestone 17-03: Guardian Access Delegation Protocols & Consent Artifact Interceptor**. Building upon Day 81's zero-contamination relational architecture and Day 82's ABDM Child-ABHA generation protocols, today's release operationalizes end-to-end electronic consent delegation under **ABDM Milestone M3** and the **Indian Digital Personal Data Protection (DPDP) Act 2023 Section 9**.

Under Indian law, minors and incapacitated senior dependents cannot provide independent digital consent for healthcare data exchange across hospitals, labs, and tele-health providers. To prevent unlawful record access while supporting legitimate pediatric and geriatric care, NIRMAYA introduces an enterprise consent delegation and interceptor subsystem:
1. Inbound ABDM Consent Request Interception: Automatically intercepts data exchange requests directed at dependent minors and routes them to verified parent/guardian consoles.
2. DPDP Act 2023 Section 9 Enforced Consent Granting: Requires verified guardians to digitally sign consent artifacts, binding explicit purpose codes (e.g., `CAREMGT`, `EMERGENCY`, `DIAGNOSTIC`), granular Health Information Types (HiTypes), and validity periods.
3. Ephemeral Scoped Proxy Bearer Tokens: Mints time-limited, purpose-restricted access tokens (`proxy:dependent:<purpose>`) with zero data contamination risk, ensuring clinicians access only the authorized dependent's records without exposure to guardian records.
4. Real-Time Consent Revocation Gateway: Allows parents to immediately revoke active consent artifacts, instantly terminating further clinical record ingestion across Health Information Users (HIUs).
5. Immutable Append-Only Audit Ledger: Logs every consent authorization, revocation, and token exchange for compliance audits by the Data Protection Board of India.

---

## Key Deliverables & Architectural Implementation

### 1. Pydantic Schemas & Domain Models

Authored in [`backend/app/schemas/guardian_delegation.py`](file:///e:/nirmaya-side/backend/app/schemas/guardian_delegation.py) and exported in [`backend/app/schemas/__init__.py`](file:///e:/nirmaya-side/backend/app/schemas/__init__.py):
- `ConsentPurposeEnum`: Standardized purpose codes (`CAREMGT`, `EMERGENCY`, `PUBHLTH`, `DIAGNOSTIC`) aligned with ABDM M3 and SNOMED CT.
- `DelegatedConsentStatusEnum`: Lifecycle state definitions (`REQUESTED`, `GRANTED`, `REVOKED`, `EXPIRED`).
- `DelegatedConsentGrantRequest`: Inbound payload capturing relationship binding, date ranges, HiTypes, and mandatory DPDP Act Sec 9 guardian digital signature attestation.
- `DelegatedConsentArtifactResponse`: Electronic consent artifact containing SHA-256 digital signature hash, validity timestamps, and zero-contamination certification.
- `ScopedProxyTokenRequest` & `ScopedProxyTokenResponse`: Scoped token exchange specifications with bounded duration (`60s` to `86400s`) and isolation claims.
- `DelegatedConsentRevokeRequest`: Payload capturing revocation rationale and guardian identity.
- `ConsentAuditTrailItem`: Immutable forensic ledger record tracking actor, action, timestamp, IP address, and operation status.

### 2. Guardian Consent Delegation & Token Service

Implemented in [`backend/app/services/guardian_delegation_service.py`](file:///e:/nirmaya-side/backend/app/services/guardian_delegation_service.py):
- **DPDP Act Sec 9 Attestation Engine:** Validates digital consent affirmations, rejecting any authorization attempts that lack parental attestation.
- **Proxy Authority Verification:** Integrates with `FamilyProxyService` to ensure the requesting actor possesses an active, verified proxy delegation for the target dependent.
- **Cryptographic Signature Engine:** Computes SHA-256 digital signature hashes over consent request parameters for non-repudiation.
- **Scoped Token Minting:** Generates cryptographically unique proxy Bearer tokens carrying purpose and relationship claims while isolating adult records.
- **Consent Interceptor Engine:** Security guard inspecting inbound consent requests, confirming eligibility and valid relationship bindings.
- **Lifecycle & Revocation Manager:** Transitions artifacts from `GRANTED` to `REVOKED`, updating forensic audit ledgers and invalidating downstream exchange sessions.

### 3. FastAPI REST Endpoints (`/api/v1/patients/proxy/*`)

Authored in [`backend/app/api/v1/endpoints/guardian_delegation.py`](file:///e:/nirmaya-side/backend/app/api/v1/endpoints/guardian_delegation.py) and mounted in [`backend/app/api/v1/router.py`](file:///e:/nirmaya-side/backend/app/api/v1/router.py):
- `POST /api/v1/patients/proxy/consent/grant`: Authorize and issue delegated ABDM consent artifact (HTTP 201).
- `POST /api/v1/patients/proxy/consent/{artifact_id}/revoke`: Immediately revoke an active delegated consent artifact.
- `POST /api/v1/patients/proxy/delegation/token`: Mint ephemeral scoped proxy token for clinical consultations.
- `POST /api/v1/patients/proxy/consent/intercept`: Intercept and verify inbound ABDM consent request eligibility.
- `GET /api/v1/patients/proxy/consent/artifacts`: Query active and historical delegated consent artifacts.
- `GET /api/v1/patients/proxy/consent/pending-requests`: Query inbound consent requests awaiting guardian review.
- `GET /api/v1/patients/proxy/consent/audit`: Fetch append-only forensic audit trail for regulatory compliance.

### 4. Cal.com Design System Frontend Dashboard

Implemented in [`frontend/src/components/clinical/GuardianConsentDelegationCard.tsx`](file:///e:/nirmaya-side/frontend/src/components/clinical/GuardianConsentDelegationCard.tsx) and mounted in [`frontend/src/app/doctor/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/doctor/page.tsx):
- **Pending ABDM Requests Tab:** Lists inbound requests with requester facility, clinician HPID, requested HiTypes, date range, and quick action buttons.
- **Delegated Consent Modal:** Interactive authorization dialog with granular HiType checkboxes, purpose selectors, and DPDP Act Sec 9 legal attestation.
- **Active Artifacts Console:** Real-time view of enforced consent artifacts with validity countdowns, claims inspector, and instant revocation flow.
- **Scoped Ephemeral Token Console:** Self-service token generator for emergency triage or consultations, showing token claims, expiry, and signed Bearer string.
- **Visual Design:** Strictly compliant with Cal.com monochrome design tokens (`#ffffff`, `#f9fafb`, `#e5e7eb`, `#111111`, zero emojis, zero em dashes).

---

## Verification & Empirical Metrics

- **Day 83 Test Suite:** 30 dedicated unit and integration tests in [`backend/tests/test_guardian_delegation.py`](file:///e:/nirmaya-side/backend/tests/test_guardian_delegation.py) passing in 0.79s.
- **Full Cumulative Test Suite:** 791 tests passing across 47 modules with zero failures and 100% green status.
- **Frontend Compilation:** Next.js 15 production build compiled and prerendered 13/13 static and dynamic routes cleanly.
- **Design System Conformance:** Strict Cal.com monochromatic tokens, valid badge variants (`emerald`, `warning`, `critical`, `neutral`, `verified`, `abdm`), zero emojis, zero em dashes.
