# Day 82: ABDM Child ABHA Linkage & Verified Demographic Proxy Binding

**Milestone:** 17-02  
**Theme:** Week 17: Dependent & Family Health Proxy and Zero-Contamination Architecture  
**Status:** **COMPLETED** (761 Tests Passing across 46 Modules, 100% Green)

---

## Executive Summary

Today marks **Day 82**, delivering **Milestone 17-02: ABDM Child ABHA Linkage & Verified Demographic Proxy Binding**. Building upon the foundational Zero-Contamination architecture established on Day 81, today's work implements the official National Health Authority (NHA) ABDM M1 protocol for parent-authorized Child ABHA creation and demographic binding under strict compliance with the **Indian Digital Personal Data Protection (DPDP) Act 2023 Section 9**.

Because minor children cannot independently undergo biometric e-KYC or maintain independent mobile numbers in Aadhaar, the national health stack requires Child ABHA generation to be authorized by a verified parent or legal guardian. NIRMAYA implements this via a 4-step verified workflow: parent Aadhaar OTP challenge, demographic validation (< 18 years age-of-majority constraint), DigiLocker municipal birth certificate cryptographic fingerprinting, and generation of a sovereign 14-digit Child ABHA number (`14-XXXX-XXXX-XXXX`) and federated ABHA address (`<child>@abdm`).

To ensure national interoperability across hospital and state repository systems, proxy delegations are serialized into standard **HL7 FHIR Release 4 `RelatedPerson`** resources complying with NRCeS guidelines.

---

## Key Deliverables & Architectural Implementation

### 1. Pydantic Schemas & Domain Models

Authored in [`backend/app/schemas/child_abha.py`](file:///e:/nirmaya-side/backend/app/schemas/child_abha.py) and exported in [`backend/app/schemas/__init__.py`](file:///e:/nirmaya-side/backend/app/schemas/__init__.py):
- `ChildAbhaOtpRequest` & `ChildAbhaOtpResponse`: Dispatches simulated Aadhaar OTP to parent's registered mobile with mandatory DPDP Act Sec 9 consent attestation.
- `ChildAbhaRegistrationRequest` & `ChildAbhaRegistrationResponse`: Encapsulates OTP verification, child legal demographics, preferred `@abdm` handle, birth certificate reference, and offline QR code payload.
- `DigiLockerDocumentVerificationRequest` & `DigiLockerDocumentVerificationResponse`: Municipal certificate validation returning SHA-256 cryptographic fingerprints.
- `FhirRelatedPersonRepresentation`: HL7 FHIR R4 compliant schema with `patient` reference, HL7 v3 `RoleCode` (`PRN` / `CHILD` / `GUARD`), telecom, and validity periods.

### 2. Child ABHA & Demographic Binding Service

Implemented in [`backend/app/services/child_abha_service.py`](file:///e:/nirmaya-side/backend/app/services/child_abha_service.py):
- **Guardian Aadhaar OTP Engine:** Manages transient OTP challenge sessions with 10-minute expirations and masked phone numbers (`XXXXXX4821`).
- **Child-ABHA Minting Engine:** Generates standard 14-digit ABHA numbers prefixed with `14-` and constructs federated ABHA address handles.
- **Sovereign Profile Provisioning:** Provisions an independent `PatientProfile` UUID (`pat-child-<uuid>`) maintaining absolute isolation from guardian health records.
- **DigiLocker Adapter:** Cryptographically validates municipal birth certificate IDs and computes SHA-256 hashes for non-repudiation.
- **Zero-Contamination Delegation Linkage:** Binds child to guardian via `FamilyProxyService.establish_proxy_relationship` with `FULL_MANAGEMENT` scope.
- **HL7 FHIR R4 Serializer:** Maps proxy relationship types to standard HL7 v3 RoleCodes (`PRN` for child minor, `CHILD` for senior parent) with complete NRCeS profile conformance.

### 3. FastAPI Child-ABHA REST Endpoints (`/api/v1/patients/proxy/child-abha/*`)

Authored in [`backend/app/api/v1/endpoints/child_abha.py`](file:///e:/nirmaya-side/backend/app/api/v1/endpoints/child_abha.py) and mounted in [`backend/app/api/v1/router.py`](file:///e:/nirmaya-side/backend/app/api/v1/router.py):
- `POST /api/v1/patients/proxy/child-abha/otp-request`: Request guardian Aadhaar OTP challenge.
- `POST /api/v1/patients/proxy/child-abha/verify-and-create`: Verify OTP, mint Child ABHA, and link proxy delegation (HTTP 201).
- `POST /api/v1/patients/proxy/child-abha/digilocker/verify`: Verify birth certificate provenance via DigiLocker adapter.
- `GET /api/v1/patients/proxy/child-abha/{relationship_id}/fhir-related-person`: Export HL7 FHIR R4 `RelatedPerson` JSON resource.

### 4. Cal.com Design System Frontend Component

Implemented in [`frontend/src/components/clinical/ChildAbhaBindingCard.tsx`](file:///e:/nirmaya-side/frontend/src/components/clinical/ChildAbhaBindingCard.tsx) and mounted in [`frontend/src/app/doctor/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/doctor/page.tsx):
- **Step 1: Guardian Authorization:** Displays guardian Aadhaar entry and DPDP Act Sec 9 consent attestation.
- **Step 2: Child Demographics:** Form capturing child legal name, gender, DOB, preferred `@abdm` handle, and birth certificate ID.
- **Step 3: DigiLocker Instant Verification:** Real-time certificate validation displaying SHA-256 document fingerprint badge.
- **Step 4: Issued Child ABHA Credential Card:** Digital ABHA card display with 14-digit number, `@abdm` address, offline QR code, and sovereign vault badge.
- **HL7 FHIR R4 RelatedPerson Inspector:** Live collapsible JSON viewer displaying the generated FHIR resource.

---

## Verification & Empirical Metrics

- **Total Test Suite:** **761 / 761 tests passing** across 46 test modules (100% green).
- **Day 82 Test Suite:** 24 dedicated unit and integration tests in [`backend/tests/test_child_abha_linkage.py`](file:///e:/nirmaya-side/backend/tests/test_child_abha_linkage.py) executing in 1.30s.
- **Frontend Compilation:** Next.js 15 production build clean across all 13 routes (`npm run build`).
- **Design Tokens:** Strict Cal.com monochrome palette (`#ffffff`, `#f9fafb`, `#e5e7eb`, `#111111`), zero emojis, zero em dashes.
