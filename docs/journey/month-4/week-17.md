# Week 17: Dependent & Family Health Proxy and Zero-Contamination Architecture

**Milestone Target:** Extend NIRMAYA's sovereign health platform to support dependent minors and elderly parents under strict compliance with the Indian Digital Personal Data Protection (DPDP) Act 2023 Section 9 and ABDM familial proxy guidelines.

---

## Daily Schedule and Architectural Focus

| Day | Focus Area | Planned Deliverables | Status |
|---|---|---|---|
| **Day 81** | Dependent and Family Health Proxy Schema and Zero-Contamination Architecture | DPDP Act Sec 9 compliance, independent PatientProfile records, multi-tier verification authority, zero-contamination invariants | **In Progress** |
| **Day 82** | ABDM Child ABHA Linkage and Verified Demographic Proxy Binding | ABDM M1 child ABHA creation, Aadhaar demographic parent binding, DigiLocker verification adapter | Upcoming |
| **Day 83** | Guardian Access Delegation Protocols and Consent Artifact Interceptor | Consent artifact interceptor, scope-restricted tokens, audit trails, revocations | Upcoming |
| **Day 84** | Pediatric and Geriatric Workflow Isolation with Cal.com Dependent Switcher | Cal.com dependent switcher, patient-context switcher, EHR view segmentation, immunization timeline | Upcoming |
| **Day 85** | Multi-Guardian Concurrency and Conflict Resolution Engine | Conflict arbitration, joint-custody state machine, audit alerts, access dispute handling | Upcoming |

---

## Week 17 Core Architectural Invariants

1. **Zero Record Contamination:** Dependents possess independent, sovereign `PatientProfile` entities. Guardian records never store dependent clinical observations or conditions directly.
2. **DPDP Act 2023 Section 9 Compliance:** Processing of personal data of children requires verifiable consent from parents or lawful guardians.
3. **Multi-Tier Verification Authority:** Proxy linkages require cryptographically verified proof (DigiLocker birth certificate, Aadhaar e-KYC demographic match, or legal court guardianship orders).
4. **Scope-Restricted Privileges:** Access scopes are explicitly bounded to Full Management, Appointments Only, Records View Only, or Emergency Only.
5. **Immutable Forensic Ledger:** All proxy actions generate tamper-evident audit records capturing guardian identity, dependent identity, action, and timestamp.

