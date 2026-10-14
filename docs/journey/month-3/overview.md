# Month 3: ABDM Milestones & Health Information Exchange

**Milestone Target:** Implement national healthcare interoperability standards including Ayushman Bharat Digital Mission (ABDM M1, M2, and M3), Health Information Provider (HIP), Health Information User (HIU), FHIR R4 Bundle validation, and Milestone Release `v0.3.0`.

---

## 1. Month 3 Architectural Scope

Month 3 integrates NIRMAYA into the Indian National Digital Health Ecosystem:
- **Week 9: ABDM Milestone 1 - ABHA Creation & Aadhaar OTP Verification (Days 41–45):** Aadhaar demographic OTP verification, ABHA Number generation, ABHA Address (PHR handle) reservation, and digital identity card issuance.
- **Week 10: ABDM Milestone 2 - HIP Discovery & Health Record Linking (Days 46–50):** Health Information Provider (HIP) gateway, patient discovery (`/v0.5/care-contexts/discover`), OTP linking (`/v0.5/links/link/confirm`), and care context management.
- **Week 11: ABDM Milestone 3 - Consent Manager & HIE-CM Gateway (Days 51–55):** Consent Artefact generation, cryptographic key pair exchange (Diffie-Hellman / ECDH), Health Information Exchange (HIU) data flow, and encrypted FHIR Bundle transfer.
- **Week 12: Comprehensive Interoperability Audit & Milestone Release v0.3.0 (Days 56–60):** End-to-end sandbox testing via ABDM Sandbox portal, FHIR R4 validation engine, and Milestone Release `v0.3.0`.

---

## 2. Weekly Breakdown

| Week | Title & Focus | Days | Key Standards & Interoperability |
|---|---|---|---|
| **Week 9** | ABDM M1: ABHA Registration & Identity | Days 41–45 | Aadhaar e-KYC, Mobile OTP, ABHA Number (14-digit), PHR Handle (`@abdm`), QR verification. |
| **Week 10** | ABDM M2: HIP Discovery & Care Contexts | Days 46–50 | HIP Discovery API, Care Context linking, asynchronous webhook callbacks, HIP service. |
| **Week 11** | ABDM M3: Consent & Encrypted Data Flow | Days 51–55 | HIU/HIP consent gateway, Diffie-Hellman key exchange, AES-GCM data encryption, FHIR transfer. |
| **Week 12** | FHIR Bundle Validator & Release v0.3.0 | Days 56–60 | FHIR R4 DiagnosticReport/CarePlan bundles, sandbox certification, Release `v0.3.0`. |
