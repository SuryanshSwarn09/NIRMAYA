---
milestone: UX4G Government Design System Migration
version: 1.3.0
updated: 2026-11-07T22:33:00Z
---

# Roadmap

> **Current Phase:** Phase 6 - UX4G Government of India Design System Migration
> **Status:** Planning (Alignment Complete via /grill-me)

## Must-Haves (from Spec & Alignment Interview)

- [ ] Native Tailwind CSS v4 design tokens for official UX4G palette (India Blue `#0b4d8c`, Tiranga Saffron `#f47920`, India Green `#046a38`, Ashoka Navy, surface tints).
- [ ] Typography integration: Google Noto Sans & Noto Sans Devanagari via `next/font/google` for clean bilingual rendering.
- [ ] GIGW 3.0 Standard Accessibility Toolbar: A-/A/A+ font size adjuster, high-contrast mode toggle, skip-to-main-content landmark, bilingual English / हिन्दी toggle.
- [ ] Official Government of India Header Bar with Ashok Stambh national emblem and MoHFW / National Health Authority (NHA) credentials.
- [ ] Wave 1: Design Tokens, Noto Typography, GIGW 3.0 Header/Footer, and modernized UI Primitives (`Button`, `Card`, `Badge`, `Input`).
- [ ] Wave 2: Citizen Health Vault, Official ABHA Card redesign, and Landing / Authentication portals (`/`, `/login`, `/register`, `/patient`).
- [ ] Wave 3: Professional Consoles: Doctor EMR (`/doctor`), Diagnostic Lab (`/lab`), and Public Health Command Center (`/admin`).
- [ ] 100% Mobile responsiveness across rural smartphone viewports and zero TypeScript errors (`tsc --noEmit`).

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
**Status:** ⬜ Ready for Planning / Execution
**Objective:** Full-ecosystem migration of NIRMAYA frontend applications to the official MeitY/NeGD UX4G Design System and GIGW 3.0 accessibility standards.
**Depends on:** Phase 5
**Days:** 96+

**Wave Breakdown:**
- [ ] **Wave 1:** Core Foundations (Design Tokens, Noto Typography, GIGW 3.0 Header/Footer, & UI Primitives)
- [ ] **Wave 2:** Citizen & Identity (Citizen Health Vault, Official ABHA Card, & Landing/Auth Flows)
- [ ] **Wave 3:** Professional Consoles (Doctor Clinical EMR, Diagnostic Lab, & Public Health Command Center)

**Verification:**
- [ ] GIGW 3.0 compliance checklist audit
- [ ] W3C WCAG 2.1 AA automated accessibility audit
- [ ] Frontend TypeScript typecheck (`npm run typecheck --prefix frontend`) passing with 0 errors
- [ ] Full regression suite passing across all clinical workflows
