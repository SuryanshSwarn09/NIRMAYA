---
milestone: UX4G Government Design System Migration
version: 1.3.0
updated: 2026-11-08T01:10:00Z
---

# Roadmap

> **Current Phase:** Phase 6 - UX4G Government of India Design System Migration
> **Status:** Complete (Wave 1, Wave 2, and Wave 3 Fully Implemented & Verified)

## Must-Haves (from Spec & Alignment Interview)

- [x] Native Tailwind CSS v4 design tokens for official UX4G palette (India Blue `#0b4d8c`, Tiranga Saffron `#f47920`, India Green `#046a38`, Ashoka Navy, surface tints).
- [x] Typography integration: Google Noto Sans & Noto Sans Devanagari via `next/font/google` for clean bilingual rendering.
- [x] GIGW 3.0 Standard Accessibility Toolbar: A-/A/A+ font size adjuster, high-contrast mode toggle, skip-to-main-content landmark, bilingual English / हिन्दी toggle.
- [x] Official Government of India Header Bar with Ashok Stambh national emblem and MoHFW / National Health Authority (NHA) credentials.
- [x] Wave 1: Design Tokens, Noto Typography, GIGW 3.0 Header/Footer, and modernized UI Primitives (`Button`, `Card`, `Badge`, `Input`).
- [x] Wave 2: Citizen Health Vault, Official ABHA Card redesign, and Landing / Authentication portals (`/`, `/login`, `/register`, `/patient`).
- [x] Wave 3: Professional Consoles: Doctor EMR (`/doctor`), Diagnostic Lab (`/lab`), and Public Health Command Center (`/admin`).
- [x] 100% Mobile responsiveness across rural smartphone viewports and zero TypeScript errors (`tsc --noEmit`).

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

---

### Phase 7: Comprehensive Frontend Visual Audit & Layout Remediation
**Status**: ✅ Complete
**Objective**: Audit every frontend visual file, map root causes of broken card containers and layout unevenness across all 8 routes, decouple the intrusive 8.3MB global CSS reset, clamp typography scale, and restore the clean Cal.com-inspired sovereign UI.
**Depends on**: Phase 6

**Tasks**:
- [x] Part 1: Comprehensive file-by-file audit of all 22 frontend visual files (`.gsd/FRONTEND-AUDIT.md`)
- [x] Part 2: Screenshot defect mapping and root-cause report (`.gsd/DEFECT-ANALYSIS.md`)
- [x] Part 3: Detailed implementation plan (`phase-7-visual-scale-and-consoles-finishing-plan.md`) with user approval gate before code changes
- [x] Wave 1 & 2 Remediation: Decoupled destructive `ux4g-web-components/styles.css` reset, clamped `.display-xl`/`.display-lg` scale in `globals.css`, restored pure Tailwind UI primitives (`Card`, `Button`, `Input`, `Badge`, `Alert`).
- [x] Route Remediations: Restored clean borders and card containers across `/`, `/login`, `/register`, `/doctor`, `/fhir`, `/patient`, `/lab`, and `/admin`.
- [x] Wave 3 Consoles: Cleaned Express 45s OPD Console, Lab LOINC Builder & Ledger, Super Admin Telemetry, and Digital ABHA Card.

**Verification**:
- [x] Decouple `ux4g-web-components/styles.css` from `globals.css` without breaking GIGW 3.0 government tokens
- [x] 100% of cards on `/register`, `/login`, `/doctor`, `/fhir`, `/patient`, `/admin`, `/lab`, `/` render with crisp borders, backgrounds, and shadows
- [x] TypeScript check passing (`npm run typecheck --prefix frontend`) with 0 errors
- [x] Test suite passing (`pytest backend/tests/test_ux4g_design_system_phase6.py` - 14/14 tests passed)

