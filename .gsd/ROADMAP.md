---
milestone: UX4G Government Design System Migration
version: 1.3.0
updated: 2026-11-07T22:25:00Z
---

# Roadmap

> **Current Phase:** Phase 6 - UX4G Government of India Design System Migration
> **Status:** Planning

## Must-Haves (from Requirements)

- [ ] Align color palette and design tokens with official MeitY/NeGD UX4G standards (India Blue, Tiranga Saffron, India Green).
- [ ] Implement Guidelines for Indian Government Websites (GIGW 3.0) and W3C WCAG 2.1 AA accessibility controls (font resize, high contrast, skip-to-content).
- [ ] Add standardized Government of India (GOI) header bar with Ashok Stambh emblem and bilingual language selector.
- [ ] Modernize Citizen Vault, Doctor EMR, Diagnostic Lab, and Command Center UI components with UX4G design primitives.
- [ ] Maintain 100% responsive design across mobile (rural smartphone) and desktop resolutions with zero TypeScript errors.

---

## Phases

### Phase 1: Foundations & Core Architecture (Milestone M1 ABHA & Citizen Registry)
**Status:** ✅ Complete
**Objective:** Core microservices, PostgreSQL 16 schema, Verhoeff D5 algorithm, Aadhaar OTP simulation, and Milestone M1 ABHA issuance.
**Days:** 1–20

---

### Phase 2: Clinical EMR, FHIR R4 Engine & Milestone M2 HIP Bridge
**Status:** ✅ Complete
**Objective:** NRCeS HL7 FHIR R4 bijective translation, SNOMED-CT / LOINC clinical ontologies, and Milestone M2 HIP care-context discovery/linkage.
**Days:** 21–40

---

### Phase 3: Milestone M3 HIU Consent Manager & Fidelius Cryptographic Transfer
**Status:** ✅ Complete
**Objective:** Consent artefact electronic signing, Curve25519 Diffie-Hellman key agreement, and AES-256-GCM encrypted transfer.
**Days:** 41–60

---

### Phase 4: Production Readiness, LGD Governance & Enterprise Deployment
**Status:** ✅ Complete
**Objective:** 6-tier sovereign LGD administrative hierarchy (PostgreSQL ltree), Scoped TRBAC, Docker orchestration, and Release v1.0.0.
**Days:** 61–80

---

### Phase 5: Sovereign Archival, Academic Treatise, Monograph & IEEE Paper
**Status:** ✅ Complete
**Objective:** 10-chapter formal project monograph, IEEE Transactions research manuscript with 26 citations, and Release v1.2.0.
**Days:** 81–95

---

### Phase 6: UX4G Government of India Design System Migration
**Status:** ⬜ Not Started
**Objective:** Migrate NIRMAYA frontend applications to the official MeitY/NeGD UX4G Design System and GIGW 3.0 accessibility standards for nationwide government adoption.
**Depends on:** Phase 5
**Days:** 96+

**Tasks:**
- [ ] TBD (run /plan 6 to create)

**Verification:**
- [ ] GIGW 3.0 compliance checklist audit
- [ ] W3C WCAG 2.1 AA automated accessibility audit
- [ ] Frontend TypeScript typecheck (`npm run typecheck --prefix frontend`) passing with 0 errors
- [ ] Full regression suite passing across all clinical workflows
