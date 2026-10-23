# Day 31: Milestone 07-01: Patient Portal App Shell & Modular Layout Refactor

**Date:** October 23, 2026  
**Milestone:** 07-01 (Month 2, Week 7 Kickoff)  
**Primary Commits:**  
- `feat(frontend): scaffold cal.com patient portal component hierarchy and metrics bar`  
- `refactor(frontend): decompose monolithic patient vault into modular cal.com tabs and modals`  

---

## 1. Objectives & Architectural Context

Week 7 marks the commencement of **Consumer-Facing Healthcare Interfaces, Interactive ABHA Card Generators & Telemedicine Preparation**. Following the successful delivery of longitudinal problem lists (Week 5) and outpatient e-prescriptions with closed-loop pharmacy fulfillment (Week 6), Week 7 bridges these enterprise clinical engines into an elegant, consumer-grade patient health portal.

Before Day 31, `frontend/src/app/patient/page.tsx` had grown into a monolithic **1,732-line** client component that intermingled state orchestration, clinical booking widgets, prescription registries, lab gateways, vitals logging, and modal dialogs. This monolith created high cognitive overhead, impeded granular component testing, and risked compilation regressions.

Day 31 achieved a zero-downtime architectural refactor of the patient portal, adhering strictly to the **Cal.com design system** (`calcom-design-system` skill) and establishing the modular foundation for the upcoming Week 7 milestones.

---

## 2. Engineered Component Architecture

The 1,732-line monolith was decomposed into 7 single-responsibility modules housed under `frontend/src/components/patient/`:

```
frontend/src/components/patient/
├── PatientHeader.tsx             # Patient identity, verified ABHA pill, encryption indicator & CTAs
├── PatientMetricsBar.tsx         # 4 Cal.com product metric cards with interactive jump triggers
├── PatientNavTabs.tsx            # Segmented NavPillGroup switching between 5 clinical domains
├── PatientOverviewTab.tsx        # 12-column responsive dashboard (ABHA Card, Consent, Encounters, Vitals)
├── PatientPrescriptionsTab.tsx   # e-Prescription registry with directions, refill quotas & FHIR inspector
├── PatientRecordsTab.tsx         # Diagnostic lab reports, requisitions, SOAP notes & timeline
├── PatientModals.tsx             # Biometric vitals logger, FHIR JSON viewer & MedicationRequest inspector
└── index.ts                      # Clean barrel export interface
```

### Module Specifications:

1. **`PatientHeader.tsx` (Identity & Sovereign Provenance):**
   - Displays patient initials avatar circle (`rounded-full`, `#f3f4f6` surface, `#e5e7eb` hairline border).
   - "Self-Sovereign" verification pill and active ABHA green status indicator (`#059669`).
   - Quick action cluster: "Export FHIR Bundle" (`variant="secondary"`) and responsive contextual button toggling between "Book Consultation" (`#111111` CTA) and "Back to Dashboard".

2. **`PatientMetricsBar.tsx` (Clinical Health Indicators):**
   - Implements 4 Cal.com-inspired product cards (`rounded-[12px]`, `bg-[#f8f9fa]`, hover `bg-white`, `border-[#e5e7eb]`):
     - **Active e-Prescriptions:** Count of signed digital prescriptions with pharmacy tracking badge.
     - **Scheduled Encounters:** Confirmed clinical visits count with status indicator.
     - **Problem List & Conditions:** Diagnosed conditions count with SNOMED-CT ontology chip.
     - **Latest Vitals Status:** Systolic/diastolic blood pressure reading, SpO2 percentage, and direct "+ Log Vital" trigger.

3. **`PatientNavTabs.tsx` (Cal.com NavPillGroup):**
   - Segmented navigation with rounded pills (`rounded-full`) and subtle elevation (`shadow-[0_1px_3px_rgba(0,0,0,0.08)]` on active state):
     - `overview`: Dashboard Overview
     - `prescriptions`: Prescriptions & Rx (with live badge counter)
     - `problems`: Problem List & Conditions (with live badge counter)
     - `records`: Health Records & Diagnostics
     - `book`: Schedule Consultation

4. **`PatientOverviewTab.tsx` (Unified Dashboard):**
   - **Left Column (5 cols):** Official Ayushman Bharat Health Card preview with QR code representation, ABHA ID number, ABHA Address (`@abdm`), Blood group, and active time-bound Consent Manager delegation with instant access revocation.
   - **Right Column (7 cols):** Confirmed Clinical Consultations list with ABDM CareContext references, recent e-prescriptions snapshot, and recent biometric vitals snapshot.

5. **`PatientPrescriptionsTab.tsx` (Medication Vault):**
   - High-fidelity prescription cards displaying dosage instructions, directions for use, quantity dispensed, authorized refill quotas, generic substitution authorization, and attending clinician SHA-256 cryptographic attestation.

6. **`PatientRecordsTab.tsx` (Diagnostic & Observational Engine):**
   - LOINC-coded vital signs telemetry grid with physiological abnormal badges (`critical`, `warning`, `emerald`).
   - Structured SOAP Consultation Notes with 4 distinct clinical sections (Subjective, Objective, Assessment, Plan) conforming to HL7 FHIR Composition.
   - Diagnostic Laboratory Investigations with dual sub-tabs ("Finalized Reports" with calibrated quantitative observations and "Active Requisitions" with specimen protocols).
   - Chronological longitudinal clinical timeline.

7. **`PatientModals.tsx` (Interactive Clinical Overlays):**
   - Modal for logging calibrated home biometric measurements (Heart Rate, Blood Pressure, SpO2) mapping to LOINC codes.
   - Dual JSON inspection modals for HL7 FHIR Release 4 Observation/Composition and ABDM NRCeS Prescription profiles.

8. **`frontend/src/app/patient/page.tsx` (Streamlined Orchestrator):**
   - Scaled down from **1,732 lines** to **~435 lines** of clean, readable state orchestration and view switching.

---

## 3. Quantitative Verification Metrics

| Verification Category | Target | Achieved Result | Status |
|---|---|---|---|
| **File Complexity Reduction** | Monolith decomposition | 1,732 lines $\rightarrow$ 435 lines (**74.9% reduction**) | **Decomposed** |
| **Modular Subcomponents** | High-cohesion modules | 7 single-responsibility components | **Engineered** |
| **TypeScript Type Checking** | 0 errors | `npx tsc --noEmit` passed with 0 errors | **100% Type-Safe** |
| **Next.js 15 Production Build** | Full static optimization | **11 / 11 pages compiled** (`/patient`: 13.3 kB) | **Clean Build** |
| **Backend Automated Tests** | 100% pass rate | **228 / 228 tests passing** (0 failures, 76.89s) | **100% Green** |
| **Design System Alignment** | Cal.com Tokens | `#ffffff` canvas, `#111111` buttons, `#e5e7eb` borders | **100% Compliant** |
| **Tag Discipline** | No premature release | Major tag `v0.2.0` deferred until Day 40 close | **Discipline Kept** |

---

## 4. Next Milestone Roadmap

- **Day 32 (Milestone 07-02):** Interactive Digital ABHA ID Card Generator & QR Verification (Canvas rendering, cryptographic QR code payload encoder, SVG/PNG export modal, and print engine).
