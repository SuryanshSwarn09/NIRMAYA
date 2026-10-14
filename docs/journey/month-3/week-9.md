# Week 9: ABDM Milestone 1 - ABHA Creation & Verification

**Milestone Target:** Implement ABDM Milestone 1 compliance, enabling Aadhaar-based OTP verification, 14-digit ABHA Number generation, unique PHR address allocation, and digital ABHA ID Card issuance.

---

## Daily Schedule & Architectural Focus

| Day | Focus Area | Planned Deliverables | Status |
|---|---|---|---|
| **Day 41** | ABDM Sandbox Gateway & Session Auth | Gateway client, client credentials exchange, RSA public key encryption | Planned |
| **Day 42** | Aadhaar Demographic OTP Verification | Aadhaar OTP request API, OTP validation endpoint, e-KYC payload parser | Planned |
| **Day 43** | ABHA Number Creation & Profile Linkage | 14-digit ABHA number generator, profile sync with local `PatientProfile` | Planned |
| **Day 44** | ABHA Address (PHR Handle) Reservation | PHR handle availability check, `@abdm` address linkage, digital card download | Planned |
| **Day 45** | M1 Compliance Verification & Review | Automated test suite for M1 endpoints, ABDM Sandbox audit checklist | Planned |

---

## Interoperability Highlights

- **Standard Compliance:** ABDM M1 National Health Authority specifications.
- **Cryptographic Security:** RSA-2048 encryption for Aadhaar demographic transmission.
- **Bi-directional Sync:** Automatic synchronization between ABDM e-KYC profile and NIRMAYA Patient Vault.
