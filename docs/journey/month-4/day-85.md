# Day 85: Multi-Guardian Concurrency and Conflict Resolution Engine

**Milestone:** 17-05  
**Theme:** Week 17: Dependent & Family Health Proxy and Zero-Contamination Architecture  
**Status:** **COMPLETED** (848 Tests Passing across 49 Modules, 100% Green)

---

## Executive Summary

Today marks **Day 85**, delivering **Milestone 17-05: Multi-Guardian Concurrency and Conflict Resolution Engine**, the concluding milestone of **Week 17: Dependent & Family Health Proxy and Zero-Contamination Architecture**. Following the zero-contamination relational models (Day 81), ABDM Child-ABHA demographic binding (Day 82), consent artifact interception (Day 83), and clinical workflow isolation (Day 84), today's milestone operationalizes multi-guardian concurrency arbitration, deterministic dispute management, and two-phase co-signing workflows.

Under **Section 9 of the Indian Digital Personal Data Protection (DPDP) Act 2023** and the **Guardians and Wards Act 1890**, a dependent child or vulnerable senior frequently possesses concurrent legal guardians (such as both natural parents or court-appointed joint custodians). In electronic health information systems, concurrent guardianship introduces critical concurrency risks:
1. **Conflicting Consent Directives:** One guardian may grant permission to share sensitive pediatric health records while the second guardian issues a contradictory revocation.
2. **Custodial Contests & Sub-Judice Litigation:** During active legal disputes in family court, unauthorized unilateral exfiltration of records by an alienated parent can breach statutory protections.
3. **High-Risk Intervention Authorization:** Certain major clinical or surgical interventions require verifiable affirmative assent from multiple guardians rather than unilateral authorization.

NIRMAYA resolves these challenges through a deterministic conflict resolution engine governed by two immutable legal invariants:
- **Pessimistic Revocation Invariant (Privacy Precedence):** Under privacy-preserving digital guardianship, any revocation by any verified lawful guardian immediately and unilaterally revokes consent across all sessions, regardless of which guardian originally granted it. Revocation always takes precedence over consent.
- **Disputed Custody Freeze (Court Sub-Judice Safeguard):** Upon registration of a formal custody contest or court reference under the Guardians and Wards Act 1890, the dependent's proxy relationship transitions to `DISPUTED_LOCKED`. Non-emergency proxy modifications and data transfers are frozen while preserving life-saving Break-The-Glass (`BTG`) emergency clinical access.
- **Dual-Guardian Co-Signing Workflow:** A two-phase cryptographic agreement protocol requiring counter-signatures from designated co-guardians to compute composite SHA-256 signatures before activating high-value consent artifacts.

---

## Key Deliverables & Architectural Implementation

### 1. Pydantic Schemas & Domain Models

Authored in [`backend/app/schemas/guardian_conflict.py`](file:///e:/nirmaya-side/backend/app/schemas/guardian_conflict.py) and exported in [`backend/app/schemas/__init__.py`](file:///e:/nirmaya-side/backend/app/schemas/__init__.py):
- `ConflictResolutionPolicyEnum`: Core arbitration policies (`PESSIMISTIC_REVOCATION_PREVALENCE`, `DUAL_GUARDIAN_CO_SIGNING`, `DISPUTED_CUSTODY_FREEZE`, `PRIMARY_GUARDIAN_ARBITRATION`).
- `GuardianDisputeStatusEnum`: Dispute lifecycle states (`ACTIVE_DISPUTE`, `COURT_SUB_JUDICE`, `RESOLVED`, `PENDING_MUTUAL_APPROVAL`).
- `CustodyModeEnum`: Operating governance modes (`JOINT_CONCURRENT`, `DUAL_SIGNATURE_REQUIRED`, `DISPUTED_LOCKED`).
- `GuardianActionTypeEnum`: Action categories subject to arbitration (`GRANT_CONSENT`, `REVOKE_CONSENT`, `RAISE_LEGAL_DISPUTE`, `RESOLVE_DISPUTE`, `CHANGE_CUSTODY_MODE`).
- `DualSignStatusEnum`: Authorization phase for co-signed artifacts (`PENDING_CO_SIGNATURE`, `FULLY_AUTHORIZED`, `REJECTED`).
- `GuardianEntry`: Demographic, authority verification tier, and priority tier model for authorized guardians.
- `MultiGuardianRelationshipSummary`: Complete dependent profile listing active guardians, custody mode, and dispute flags.
- `GuardianConflictResolutionRequest` & `GuardianConflictResolutionResponse`: Arbitration payload and outcome envelope with locked resource directives and SHA-256 audit hashes.
- `DualSignConsentArtifactRequest`, `DualSignCounterSignatureRequest`, and `DualSignConsentArtifactResponse`: Two-phase co-signing state models with composite signature calculation.

### 2. Multi-Guardian Concurrency & Conflict Resolution Service

Implemented in [`backend/app/services/guardian_conflict_service.py`](file:///e:/nirmaya-side/backend/app/services/guardian_conflict_service.py):
- **Multi-Guardian Discovery:** Aggregates concurrent guardians for pediatric and geriatric dependents (e.g. Dr. Priya Sharma as Mother and Vikram Sharma as Father for Aarav Sharma).
- **Pessimistic Revocation Gateway:** Evaluates unilateral revocation actions and propagates immediate revocation across all active sessions and underlying electronic consent artifacts.
- **Custody Dispute State Machine:** Automatically locks non-emergency proxy endpoints upon registration of a dispute ticket, capturing court order reference numbers and legal justifications.
- **Dispute Settlement Handler:** Restores standard `JOINT_CONCURRENT` custody upon receipt of court decree or mutual settlement attestation.
- **Two-Phase Dual-Signing Engine:** Mints initial pending artifact with primary guardian signature hash (`hashlib.sha256`) and computes composite SHA-256 signature when secondary guardian counter-signs.
- **Forensic Audit Ledger:** Append-only cryptographic ledger tracking all arbitration tickets, mode changes, and dual-sign completions.

### 3. FastAPI REST Endpoints (`/api/v1/patients/proxy/conflict/*`)

Authored in [`backend/app/api/v1/endpoints/guardian_conflict.py`](file:///e:/nirmaya-side/backend/app/api/v1/endpoints/guardian_conflict.py) and mounted in [`backend/app/api/v1/router.py`](file:///e:/nirmaya-side/backend/app/api/v1/router.py):
- `GET /api/v1/patients/proxy/conflict/dependents/{dependent_patient_id}/guardians`: Returns active guardians, current custody mode, and dispute flags. Emits security headers `X-Multi-Guardian-Engine: active` and `X-Custody-Governance`.
- `POST /api/v1/patients/proxy/conflict/arbitrate`: Submits proposed guardian action for policy arbitration. Returns arbitration ticket and locked resources.
- `POST /api/v1/patients/proxy/conflict/dispute/raise`: Registers formal custody contest and triggers automatic custodial freeze.
- `POST /api/v1/patients/proxy/conflict/dispute/resolve`: Settles active dispute and restores joint concurrent governance.
- `GET /api/v1/patients/proxy/conflict/disputes`: Enumerates active and historical dispute tickets.
- `POST /api/v1/patients/proxy/conflict/dual-sign/create`: Initiates two-phase co-signing artifact in `PENDING_CO_SIGNATURE` status.
- `POST /api/v1/patients/proxy/conflict/dual-sign/{artifact_id}/counter-sign`: Validates co-guardian identity and computes composite authorization signature.
- `GET /api/v1/patients/proxy/conflict/audit-ledger`: Retrieves immutable forensic audit events with SHA-256 hashes.

### 4. Cal.com Design System Frontend Component

Implemented in [`frontend/src/components/clinical/MultiGuardianConflictResolutionCard.tsx`](file:///e:/nirmaya-side/frontend/src/components/clinical/MultiGuardianConflictResolutionCard.tsx), exported in [`frontend/src/components/clinical/index.ts`](file:///e:/nirmaya-side/frontend/src/components/clinical/index.ts), and mounted in [`frontend/src/app/doctor/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/doctor/page.tsx):
- **Guardian Concurrency Matrix:** Displays visual cards for authorized co-guardians (Dr. Priya Sharma and Vikram Sharma) with verification authority badges and priority tiers.
- **Governance Mode Controller:** Interactive selector supporting `JOINT_CONCURRENT`, `DUAL_SIGNATURE_REQUIRED`, and `DISPUTED_LOCKED` states.
- **Interactive Arbitration Simulator:** Live action buttons to simulate unilateral revocation, raise court sub-judice dispute freeze, and resolve legal disputes.
- **Dual-Sign Co-Signing Queue:** Visual queue displaying pending consent requests with one-click co-guardian digital signature attestation.
- **Forensic Audit Log:** Real-time stream of arbitration tickets and composite SHA-256 hashes.
- **Design Token Compliance:** Pure white canvas (`#ffffff`), cards (`#f9fafb`), hairline borders (`#e5e7eb`), action buttons (`#111111`), valid badge variants (`emerald`, `warning`, `critical`, `neutral`, `verified`), zero emojis, and zero em dashes.

---

## Verification and Test Coverage

A dedicated test suite was authored in [`backend/tests/test_guardian_conflict.py`](file:///e:/nirmaya-side/backend/tests/test_guardian_conflict.py), containing 28 rigorous unit and integration tests:
1. `test_get_guardians_for_dependent_pediatric_seed`: Verified discovery of both Mother and Father for Aarav Sharma.
2. `test_get_guardians_for_dependent_alias_resolution`: Verified alias resolution for `pat-pediatric-001`.
3. `test_get_guardians_for_senior_dependent`: Verified single-guardian senior context for Kavita Sharma.
4. `test_get_guardians_for_unregistered_arbitrary_dependent`: Verified dynamic fallback for unregistered IDs.
5. `test_pessimistic_revocation_prevalence_unilateral`: Verified unilateral revocation immediate prevalence.
6. `test_pessimistic_revocation_prevails_even_during_active_dispute`: Verified revocation honored during active litigation.
7. `test_arbitrate_signature_attestation_mandatory`: Verified digital attestation requirement under DPDP Act Sec 9.
8. `test_arbitrate_unilateral_grant_under_joint_concurrent`: Verified grant approved under joint concurrent mode.
9. `test_arbitrate_unilateral_grant_blocked_when_dual_sign_required`: Verified unilateral grant blocked under dual-sign mode.
10. `test_raise_custodial_dispute_active_dispute`: Verified custodial freeze and locked resource list.
11. `test_raise_custodial_dispute_court_sub_judice`: Verified `COURT_SUB_JUDICE` flag when court order reference provided.
12. `test_arbitrate_non_revocation_blocked_during_active_dispute`: Verified non-emergency actions rejected during freeze.
13. `test_resolve_custodial_dispute_restores_joint_concurrent`: Verified dispute resolution clears custody lock.
14. `test_create_dual_sign_request_lifecycle`: Verified initiation of two-phase artifact.
15. `test_create_dual_sign_request_attestation_required`: Verified attestation check on creation.
16. `test_counter_sign_dual_artifact_success`: Verified composite hash generation and full authorization.
17. `test_counter_sign_unauthorized_signer_rejected`: Verified rejection of unauthorized third-party signer.
18. `test_counter_sign_nonexistent_artifact_fails`: Verified error handling on unknown artifact ID.
19. `test_counter_sign_attestation_required`: Verified attestation check on counter-signing.
20. `test_counter_sign_already_authorized_artifact_fails`: Verified idempotency and rejection of re-signing.
21. `test_list_dispute_tickets_filtering`: Verified dispute listing and dependent filtering.
22. `test_audit_ledger_immutable_trail`: Verified tamper-evident audit logging.
23. `test_api_get_guardians_endpoint`: Verified REST endpoint and container security headers.
24. `test_api_arbitrate_pessimistic_revocation_endpoint`: Verified arbitration REST flow.
25. `test_api_arbitrate_missing_attestation_fails`: Verified REST error handling on missing attestation.
26. `test_api_raise_and_resolve_dispute_endpoint`: Verified dispute lifecycle via API.
27. `test_api_dual_sign_e2e_flow`: Verified end-to-end two-phase co-signing via REST.
28. `test_api_audit_ledger_endpoint`: Verified audit ledger retrieval via REST.

### Cumulative Quality Metrics
- **Dedicated Test Suite:** 28 / 28 passed in 3.55s.
- **Cumulative Backend Test Suite:** 848 / 848 passed across 49 test modules in 104.47s (100% green).
- **Frontend Compilation:** Next.js 15 production build compiled and prerendered 13/13 static and dynamic routes cleanly.
- **Design Tokens:** Strict Cal.com monochrome palette (`#ffffff`, `#f9fafb`, `#e5e7eb`, `#111111`), valid badge variants, zero emojis, zero em dashes.
