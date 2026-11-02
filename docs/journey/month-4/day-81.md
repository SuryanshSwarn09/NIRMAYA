# Day 81: Dependent & Family Health Proxy Schema & Zero-Contamination Architecture

**Milestone:** 17-01  
**Theme:** Week 17: Dependent & Family Health Proxy & Zero-Contamination Architecture  
**Status:** **COMPLETED** (737 Tests Passing across 45 Modules, 100% Green)

---

## Executive Summary

Today marks **Day 81**, inaugurating Phase 5 (National Scale Expansion & DPI Redesign, Weeks 17 to 19). Day 81 delivers **Milestone 17-01: Dependent & Family Health Proxy Schema & Zero-Contamination Architecture**, establishing legal, architectural, and clinical safety foundations for family-mediated healthcare delivery across India.

Under the Indian **Digital Personal Data Protection (DPDP) Act 2023 Section 9**, processing the personal health data of minor children requires verifiable consent from parents or lawful guardians, accompanied by strict protections against tracking, behavioral monitoring, or record mixing. NIRMAYA establishes an uncompromising **Zero-Contamination Architecture**: minor children and senior parents are provisioned sovereign, independent `PatientProfile` records. Guardian authority is modeled exclusively through audited delegation links in `PatientProxyRelationship`, ensuring pediatric and geriatric clinical data never colocates or contaminates guardian health charts.

The subsystem features multi-tier verification authority (DigiLocker birth certificate cryptographic hashes, Aadhaar demographic e-KYC, and judicial guardianship orders), automated age-of-majority constraint validation (< 18 for minor child proxies), granular privilege scoping (Full Management, Appointments Only, Records View Only, Emergency Restricted), and an append-only forensic audit trail.

---

## Key Deliverables & Architectural Implementation

### 1. Relational & Pydantic Data Models

- **Relational Schema (`PatientProxyRelationship`):** Implemented in [`backend/app/models/family_proxy.py`](file:///e:/nirmaya-side/backend/app/models/family_proxy.py) with foreign keys to `patient_profile.id`, enums for relationship type, verification authority tier, access scope, and relationship lifecycle status.
- **Forensic Audit Schema (`ProxyAuditLog`):** Append-only ledger recording `actor_guardian_id`, `target_dependent_id`, `action_performed`, `resource_accessed`, `ip_address`, `timestamp`, and `authorized` flag.
- **Pydantic Validation Schemas:** Authored in [`backend/app/schemas/family_proxy.py`](file:///e:/nirmaya-side/backend/app/schemas/family_proxy.py) with DPDP Act Sec 9 consent validation, ISO-8601 DOB parsing, and SHA-256 fingerprint tracking.

### 2. Family Proxy Management Service

Implemented in [`backend/app/services/family_proxy_service.py`](file:///e:/nirmaya-side/backend/app/services/family_proxy_service.py):
- **Zero-Contamination Guard:** Enforces distinct identities between guardian and dependent (`guardian_id != dependent_id`).
- **Verifiable Consent Enforcement:** Mandates verifiable guardian consent attestation under DPDP Act 2023 Sec 9.
- **Age-of-Majority Engine:** Evaluates dependent age dynamically from date of birth; prevents minor child proxy creation for individuals $\ge 18$.
- **Multi-Tier Verification:** Tracks DigiLocker birth certificate SHA-256 hashes, Aadhaar e-KYC matches, and court legal guardianship orders.
- **Scope Restriction Engine:** Restricts privileges based on granted scope (e.g., rejecting clinical notes viewing for `APPOINTMENTS_ONLY` proxies).
- **Forensic Audit Interceptor:** Logs all access attempts (authorized and unauthorized) into the immutable audit trail.

### 3. FastAPI Family Proxy REST API (`/api/v1/patients/proxy/*`)

Authored in [`backend/app/api/v1/endpoints/family_proxy.py`](file:///e:/nirmaya-side/backend/app/api/v1/endpoints/family_proxy.py) and mounted in [`backend/app/api/v1/router.py`](file:///e:/nirmaya-side/backend/app/api/v1/router.py):
- `GET /api/v1/patients/proxy/relationships`: Retrieve all proxy relationships or filter by guardian.
- `GET /api/v1/patients/proxy/dependents`: List active verified dependents for a guardian.
- `POST /api/v1/patients/proxy/relationships`: Establish new verified proxy linkage with DPDP Act Sec 9 validation (HTTP 201).
- `GET /api/v1/patients/proxy/relationships/{id}`: Retrieve detailed metadata for a specific proxy linkage.
- `POST /api/v1/patients/proxy/relationships/{id}/revoke`: Revoke delegated proxy authority and log forensic audit record.
- `GET /api/v1/patients/proxy/relationships/{id}/audit`: Retrieve immutable forensic access logs for a relationship.
- `POST /api/v1/patients/proxy/authorize-action`: Real-time security guard checking whether a guardian is authorized to perform an operation on a dependent.

### 4. Cal.com Design System Frontend Dashboard

Implemented in [`frontend/src/components/clinical/FamilyProxyRelationshipCard.tsx`](file:///e:/nirmaya-side/frontend/src/components/clinical/FamilyProxyRelationshipCard.tsx) and mounted in [`frontend/src/app/doctor/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/doctor/page.tsx):
- **Guardian Identity Header:** Displays Dr. Priya Sharma (`pat-priya-sharma-01`), DPDP Act Sec 9 compliance badge, and ABDM UHI Proxy indicator.
- **Dependent Switcher Tabs:** Seamless switching between Aarav Sharma (Son, Minor 8 yrs) and Kavita Sharma (Mother, Senior 68 yrs).
- **Demographic & Sovereignty Card:** Displays isolated ABHA number, internal patient UUID, verification authority, and document SHA-256 hash.
- **Zero-Contamination Architecture Invariant Checklist:** Visual verification of independent vaults, consent records, age-of-majority guards, and hash provenance.
- **Clinical Care Status Panel:** Shows latest clinical encounter, pending appointments, active medications, and immunization status.
- **Immutable Forensic Audit Trail Table:** Displays timestamped operations, action verbs, target resources, network origins, and authorization status pills.
- **Context Switcher & Revocation Controls:** Quick actions to switch active clinical context or revoke delegation privileges.
- **Add Dependent Proxy Modal:** Clean form to register new dependents with consent attestation and verification authority selection.

### 5. Architectural Proof & Documentation

- Published [`docs/journey/month-4/week-17.md`](file:///e:/nirmaya-side/docs/journey/month-4/week-17.md) covering the Week 17 schedule and core invariants.
- Published [`docs/reports/nirmaya-family-proxy-access-architecture.md`](file:///e:/nirmaya-side/docs/reports/nirmaya-family-proxy-access-architecture.md) detailing clinical threat models, legal requirements under DPDP Act Sec 9, and the 5-point invariant scorecard.

---

## Verification & Empirical Metrics

- **Total Test Suite:** **737 / 737 tests passing** across 45 test modules (100% green).
- **Day 81 Test Suite:** 25 dedicated unit and integration tests in [`backend/tests/test_family_proxy.py`](file:///e:/nirmaya-side/backend/tests/test_family_proxy.py) executing in 0.69 seconds.
- **Frontend Compilation:** Next.js 15 production build clean across all 13 routes (`npm run build`).
- **Design Tokens:** Strict Cal.com monochrome palette (`#ffffff`, `#f9fafb`, `#e5e7eb`, `#111111`), zero emojis, zero em dashes.
