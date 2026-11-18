# Phase 7 — Part 1: Comprehensive Frontend Visual Audit

**Milestone:** Frontend Visual Audit & Layout Remediation (v1.3.1)  
**Date:** 2026-11-08  
**Scope:** `frontend/` directory (All 22 Visual Files Audited 1-by-1)  
**Strategy:** Hybrid Clean Token Architecture (Decouple 8.3MB UX4G CSS Reset, preserve Sovereign Indian DPI identity)  

---

## 1. Executive Visual Audit Overview

An exhaustive audit of all visual files in [`frontend/`](file:///e:/nirmaya-side/frontend/) was conducted following the user-approved Phase 7 roadmap. 

### Core Root Cause Identified
The primary systemic cause of the visual breakdown across all web pages is the global import of `ux4g-web-components/styles.css` (8.37 MB) at the top of [`frontend/src/app/globals.css`](file:///e:/nirmaya-side/frontend/src/app/globals.css):
```css
:where(*,:before,:after) {
  border: 0;
  box-sizing: border-box;
  margin: 0;
  outline: 0;
  padding: 0;
}
:where(button) { background: none; cursor: pointer; }
:where(body) { background-color: var(--ux4g-bg-neutral-elevated); ... }
```
Because this stylesheet was placed before Tailwind CSS v4, its unlayered global `:where(*)` reset silently stripped borders, margins, and container paddings from standard HTML elements, while `.ux4g-card`, `.ux4g-btn`, and `.ux4g-input` classes clashed with Tailwind utility compositions, rendering cards invisible and elements floating without containers.

---

## 2. File-by-File Audit (22 Files)

### Group A: Global Styling & Application Shell

#### 1. [`frontend/src/app/globals.css`](file:///e:/nirmaya-side/frontend/src/app/globals.css)
- **Role:** Core styling entrypoint, design tokens, display typography, and WCAG/GIGW 3.0 accessibility themes.
- **Current Defect:**
  - Line 1 imports `ux4g-web-components/styles.css` (8.3MB), injecting destructive universal resets `:where(*){border:0;margin:0;padding:0}`.
  - Overrides Tailwind base layer rules and destroys default browser form controls.
- **Remediation:** Remove `@import "ux4g-web-components/styles.css";`. Retain and cleanly define native Tailwind v4 tokens for official Government colors (`#0b4d8c` India Blue, `#f47920` Saffron, `#046a38` Green, `#072847` Ashoka Navy), surface tints, and hairline utilities.

#### 2. [`frontend/src/app/layout.tsx`](file:///e:/nirmaya-side/frontend/src/app/layout.tsx)
- **Role:** Root layout wrapping all pages in `AccessibilityProvider`, `AuthProvider`, `AppShell`, and loading Google Fonts (Noto Sans, Noto Sans Devanagari).
- **Current Defect:**
  - Inherits the broken `:where(body)` reset from `ux4g.css`.
  - Font variable declarations work well, but body container lacks proper min-height bounds.
- **Remediation:** Ensure body has `min-h-screen bg-[#f8fafc] text-[#111827] antialiased flex flex-col`.

#### 3. [`frontend/src/components/layout/AppShell.tsx`](file:///e:/nirmaya-side/frontend/src/components/layout/AppShell.tsx)
- **Role:** Common shell rendering `AccessibilityBar`, `Navbar`, dynamic child content (`<main>`), and `Footer`.
- **Current Defect:**
  - Lacks structured flex layout (`flex-1`) on `<main id="main-content">`, causing footers to collapse upward into short form pages (e.g. `/login`, `/register`, `/fhir`).
- **Remediation:** Set `<main id="main-content" className="flex-1 w-full">` to push footer to the true bottom.

#### 4. [`frontend/src/components/layout/AccessibilityBar.tsx`](file:///e:/nirmaya-side/frontend/src/components/layout/AccessibilityBar.tsx)
- **Role:** GIGW 3.0 Government of India masthead, Tricolor stripe, Ashok Stambh national emblem, bilingual switcher, text scaling, contrast, and role portal navigation.
- **Current Defect:**
  - Role portal bar secondary strip has unconstrained width and uneven spacing between portal badges and the jargon explainer button.
- **Remediation:** Enforce structured 2-cluster layout (left: role navigation; right: accessibility tools) with explicit `h-10` container height.

#### 5. [`frontend/src/components/layout/Navbar.tsx`](file:///e:/nirmaya-side/frontend/src/components/layout/Navbar.tsx)
- **Role:** Sticky desktop/mobile navigation header with brand identity, ABDM certification badge, primary navigation links, and authenticated user avatar.
- **Current Defect:**
  - Missing bottom border definition when `border: 0` reset is applied; links lack consistent hover backgrounds.
- **Remediation:** Restore clean hairline border (`border-b border-[#e5e7eb] bg-white/95 backdrop-blur-md`).

#### 6. [`frontend/src/components/layout/Footer.tsx`](file:///e:/nirmaya-side/frontend/src/components/layout/Footer.tsx)
- **Role:** National health portal sovereign footer with GIGW 3.0 / DPDP Act 2023 compliance stamps, helpline links, and academic credentials.
- **Current Defect:**
  - Collapses into pages with small vertical height due to AppShell `<main>` lack of `flex-1`.
- **Remediation:** Maintain dark sovereign navy canvas (`bg-[#051c33] text-white border-t border-[#0b4d8c]`) with clear multi-column layout.

---

### Group B: UI Primitives & Component Canvas

#### 7. [`frontend/src/components/ui/Card.tsx`](file:///e:/nirmaya-side/frontend/src/components/ui/Card.tsx)
- **Role:** Universal card canvas used by every single portal, auth form, and dashboard.
- **Current Defect:**
  - Injected with `.ux4g-card .ux4g-card-elevated` which stripped default Tailwind borders and background opacity.
- **Remediation:** Restore Cal.com-inspired modern SaaS card standard:
  `bg-white border border-[#e5e7eb] rounded-[8px] p-6 shadow-xs text-[#111827] transition-all` with clear variant mappings (`feature`, `elevated`, `outlined`, `mockup`).

#### 8. [`frontend/src/components/ui/Button.tsx`](file:///e:/nirmaya-side/frontend/src/components/ui/Button.tsx)
- **Role:** Interactive action triggers across consultation pads, form submits, and navigation CTAs.
- **Current Defect:**
  - Relied on `.ux4g-btn ux4g-btn-primary`, causing buttons to lose background colors and border radii under reset.
- **Remediation:** Re-anchor variants on Tailwind utilities:
  - `primary`: `bg-[#0b4d8c] text-white hover:bg-[#083c6f] active:bg-[#062d53] shadow-xs`
  - `secondary`: `bg-[#e8f1f9] text-[#0b4d8c] hover:bg-[#d0e4f5] border border-[#b9d5ee]`
  - `outline`: `bg-white text-[#0b4d8c] border border-[#0b4d8c] hover:bg-[#e8f1f9]`
  - `danger`: `bg-[#dc2626] text-white hover:bg-[#b91c1c]`

#### 9. [`frontend/src/components/ui/Badge.tsx`](file:///e:/nirmaya-side/frontend/src/components/ui/Badge.tsx)
- **Role:** Status indicators for verified ABHA, HPR, LOINC, and clinical priority levels.
- **Current Defect:**
  - `.ux4g-badge` reset removed vertical alignment and font weights.
- **Remediation:** Restore clean pill badges: `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold`.

#### 10. [`frontend/src/components/ui/Input.tsx`](file:///e:/nirmaya-side/frontend/src/components/ui/Input.tsx)
- **Role:** Text inputs, OTP boxes, and search fields.
- **Current Defect:**
  - `.ux4g-input` removed focus ring styles and hairline borders.
- **Remediation:** Enforce `h-10 px-3.5 py-2 text-sm rounded-[6px] border border-[#d1d5db] bg-white text-[#111827] placeholder:text-[#9ca3af] focus:outline-none focus:border-[#0b4d8c] focus:ring-1 focus:ring-[#0b4d8c]`.

#### 11. [`frontend/src/components/ui/Alert.tsx`](file:///e:/nirmaya-side/frontend/src/components/ui/Alert.tsx)
- **Role:** Clinical safety alerts, break-the-glass notifications, and form error banners.
- **Current Defect:**
  - Relied on `.ux4g-alert` classes that lacked structured icon-content gutters.
- **Remediation:** Clean rounded alerts with semantic tints (`danger`, `warning`, `success`, `info`).

#### 12. [`frontend/src/components/ui/NavPillGroup.tsx`](file:///e:/nirmaya-side/frontend/src/components/ui/NavPillGroup.tsx)
- **Role:** Interactive segmented pill switchers on the landing page and consultation views.
- **Current Defect:**
  - Reset caused buttons inside the pill group to lose padding and active background indicator.
- **Remediation:** Clean pill container: `inline-flex p-1 rounded-full bg-[#f1f5f9] border border-[#e2e8f0]` with active white pill (`bg-white shadow-xs text-[#0b4d8c]`).

---

### Group C: Core Application Route Pages

#### 13. [`frontend/src/app/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/page.tsx) (Universal Landing Page)
- **Role:** Sovereign DPI gateway, Hero marquee, 3-pillar product showcase, and live consultation booking preview.
- **Current Defect:**
  - Hero headline typography collision (`.display-xl`); Three Pillars section vertical rhythm needed expansion.
- **Remediation:** Fixed in previous wave (`max-w-3xl`, `line-height: 1.18`, `py-16 sm:py-20`); verify clean card canvas on the right-hand mock appointment card.

#### 14. [`frontend/src/app/register/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/register/page.tsx) (Registration Portal)
- **Role:** Citizen 1-tap ABHA registration, Doctor HPR onboarding, and Lab registration.
- **Current Defect (Screenshot 1):**
  - Ashok Stambh national emblem and title text float on empty white screen.
  - Role switcher tabs (`Citizen`, `Doctor`, `Lab`) lack container borders and active card styling.
  - Registration card wrapper (`<Card>`) is completely transparent / missing border and shadow.
- **Remediation:** Wrap in structured `Card` with `bg-white border border-[#e5e7eb] rounded-[10px] shadow-sm p-6 sm:p-8`; clean segmented role tab switcher.

#### 15. [`frontend/src/components/patient/PatientPasswordlessAuthCard.tsx`](file:///e:/nirmaya-side/frontend/src/components/patient/PatientPasswordlessAuthCard.tsx)
- **Role:** DigiLocker 1-click, Aadhaar OTP challenge, and mobile fallback authentication.
- **Current Defect (Screenshot 1):**
  - Mode buttons (`DigiLocker 1-Click`, `Aadhaar OTP`, `Mobile Fallback`) have no tab backgrounds or borders.
  - Government e-KYC box and OTP input fields lack card borders and padding.
- **Remediation:** Restore segmented pill tab headers with active `#0b4d8c` pill, crisp input boxes (`h-11 border border-[#d1d5db]`), and prominent action button.

#### 16. [`frontend/src/app/login/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/login/page.tsx) (Unified Sign In Page)
- **Role:** Universal National Health Gateway single sign-on entrypoint.
- **Current Defect (Screenshots 2 & 3):**
  - Header is pushed or chopped off at top of viewport.
  - Form container card is completely invisible; inputs float on blank background.
  - Footer is slammed directly under the form without vertical breathing room.
- **Remediation:** Center in `min-h-[calc(100vh-12rem)] flex items-center justify-center py-12 px-4`; wrap inside elevated `UniversalNationalGatewayCard`.

#### 17. [`frontend/src/components/gateway/UniversalNationalGatewayCard.tsx`](file:///e:/nirmaya-side/frontend/src/components/gateway/UniversalNationalGatewayCard.tsx)
- **Role:** 4-role multi-channel authentication card (Citizen, Doctor, Lab, Pharmacy).
- **Current Defect (Screenshots 2 & 3):**
  - Container card (`ux4g-card ux4g-card-elevated`) lost its outer borders and white canvas.
  - Helpline micro-strip and role tabs have missing background contrast.
- **Remediation:** Restore explicit `rounded-[10px] border border-[#d1d5db] bg-white shadow-sm overflow-hidden` with clean tab borders.

#### 18. [`frontend/src/app/doctor/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/doctor/page.tsx) (Doctor Clinical EMR)
- **Role:** Clinical consultation workspace: High-Velocity Express OPD vs Specialist EMR Vault.
- **Current Defect (Screenshot 4):**
  - Missing top padding; mode switcher buttons squashed.
  - Telemetry cards and SOAP panels lose hairline borders under reset.
- **Remediation:** Restore `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 bg-white min-h-screen`; clean card grid.

#### 19. [`frontend/src/components/clinical/ExpressOpdConsole.tsx`](file:///e:/nirmaya-side/frontend/src/components/clinical/ExpressOpdConsole.tsx)
- **Role:** 45-second high-velocity OPD queue, 1-click chief complaint chips, plain Rx bundles, and sub-50ms HPR digital signing.
- **Current Defect (Screenshot 4):**
  - 1-click complaint chips and prescription regimen cards lacked distinct border contrast.
  - Allergy alert was an overwhelming pulsing crimson block.
- **Remediation:** Fixed in previous wave (crisp `#cbd5e1` borders, active `#0b4d8c`, calmed alert); ensure parent card containers have visible boundaries.

#### 20. [`frontend/src/app/patient/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/patient/page.tsx) (Citizen Health Vault)
- **Role:** Longitudinal PHR locker, daily medication schedule, and doctor consultation history.
- **Current Defect:**
  - ABHA card container and prescription timeline cards lost distinct white canvas elevation.
- **Remediation:** Restore `Card` borders and ensure `OfficialAbhaCard` has sharp holographic security borders.

#### 21. [`frontend/src/app/fhir/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/fhir/page.tsx) (HL7 FHIR Standards Engine)
- **Role:** NRCeS India R4 bundle validator, profile catalog, and medical ontology browser.
- **Current Defect (Screenshot 5):**
  - The entire page header ("HL7 FHIR R4 Standards & Conformance Engine") and tabs are scrolled off or hidden.
  - JSON payload textarea has NO card border, NO header, and raw JSON text floats on an empty screen right above the footer.
- **Remediation:** Restore structured page container with visible header, tab row, two-column grid (`lg:grid-cols-12 gap-6`), and boxed code editor card (`border border-[#d1d5db] rounded-[8px] bg-white`).

#### 22. [`frontend/src/app/admin/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/admin/page.tsx) & [`frontend/src/app/lab/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/lab/page.tsx)
- **Role:** Sovereign Command Center (LGD administrative tree) and Diagnostic Lab console (LOINC observation builder).
- **Current Defect:**
  - Telemetry cards and worklist tables rely on `.ux4g-card` classes that lose borders under the reset.
- **Remediation:** Restore clean `Card` containers with hairline borders (`border border-[#e5e7eb] shadow-xs`).

