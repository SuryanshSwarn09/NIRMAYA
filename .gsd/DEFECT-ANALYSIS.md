# Phase 7 — Part 2: Screenshot Defect Mapping & Root Cause Analysis

**Milestone:** Frontend Visual Audit & Layout Remediation (v1.3.1)  
**Date:** 2026-11-08  
**Scope:** Direct mapping of the 5 user-provided live screenshots to frontend codebase defects  

---

## 1. Screenshot Defect Mapping Matrix

| Screenshot ID | Route URL | Visible Symptoms | Offending Code & Root Cause | Planned Fix |
| :--- | :--- | :--- | :--- | :--- |
| **Screenshot 1** (`media_1794121203192_772908e1.jpg`) | `/register` | - Floating national emblem without container<br>- Unstyled role tabs<br>- Missing Card canvas around `PatientPasswordlessAuthCard`<br>- Plain text tabs for DigiLocker/Aadhaar/Mobile | [`register/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/register/page.tsx#L138): `<Card variant="mockup" className="ux4g-card ux4g-card-elevated ...">`<br>Root Cause: Universal `:where(*){border:0;padding:0}` stripped card box model and background opacity. | Decouple 8.3MB `ux4g.css`. Wrap registration form in clean Cal.com card canvas (`bg-white border border-[#e5e7eb] rounded-[10px] shadow-sm p-6 sm:p-8`). |
| **Screenshot 2 & 3** (`media_1794121203194_7c795386.jpg`, `media_1794121203253_9af4bdbc.jpg`) | `/login?returnUrl=%2Fdoctor` | - Header partially clipped by sticky navbar<br>- Login card has no background, border, or shadow<br>- Footer pulls up immediately under the form | [`login/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/login/page.tsx#L34) & [`UniversalNationalGatewayCard.tsx`](file:///e:/nirmaya-side/frontend/src/components/gateway/UniversalNationalGatewayCard.tsx#L326): `<div className="... ux4g-card ux4g-card-elevated">`<br>Root Cause: Reset stripped card borders; AppShell `<main>` lacks `flex-1`. | Restore `rounded-[10px] border border-[#d1d5db] bg-white shadow-sm overflow-hidden`; add `flex-1` to AppShell `<main>` to anchor footer at true bottom. |
| **Screenshot 4** (`media_1794121203317_9a757acf.jpg`) | `/doctor` | - Doctor OPD header compressed<br>- Complaint chips lack elevation<br>- Prescription pad card is squashed | [`ExpressOpdConsole.tsx`](file:///e:/nirmaya-side/frontend/src/components/clinical/ExpressOpdConsole.tsx#L422) & [`doctor/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/doctor/page.tsx#L304): Grid containers lack gutters. | Restore 2-column balanced grid (`lg:grid-cols-12 gap-6`) with Cal.com card borders (`border border-[#e2e8f0] bg-white p-4 shadow-xs`). |
| **Screenshot 5** (`media_1794121203297_db4601f2.jpg`) | `/fhir` | - Header and tab row missing / scrolled off<br>- JSON editor is a borderless textarea floating on empty canvas<br>- Right-side conformance report is absent | [`fhir/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/fhir/page.tsx#L511): The container lacks structured min-height, and `Card` components in right column collapse without Tailwind border specificity. | Restore structured page header, visible tab group, clean 12-column grid (`lg:grid-cols-12 gap-6`), and boxed code editor card with gray header tab. |

---

## 2. The 3 Architectural Mechanisms Causing the Failure

```
                  ┌────────────────────────────────────────────────────────┐
                  │ @import "ux4g-web-components/styles.css" (8.37 MB)     │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               ▼                             ▼                             ▼
┌─────────────────────────────┐┌───────────────────────────┐┌─────────────────────────────┐
│ 1. Universal CSS Reset      ││ 2. CSS Specificity Clash  ││ 3. Missing Flex Layout     │
│ :where(*){border:0;margin:0}││ .ux4g-card overrides      ││ <main> lacks flex-1,        │
│ Strips borders, margins,    ││ Tailwind bg-white,        ││ causing footer to collapse │
│ and paddings from HTML      ││ shadow-xs, and rounded    ││ upward into form pages     │
└─────────────────────────────┘└───────────────────────────┘└─────────────────────────────┘
```

1. **Universal Reset Infiltration:** Line 1 of `ux4g.css` uses `:where(*,:before,:after){border:0;box-sizing:border-box;margin:0;outline:0;padding:0}`. This resets every card, input, and button in the DOM.
2. **Component Specificity Clash:** Replacing working Tailwind primitives with `.ux4g-card` and `.ux4g-btn` caused elements to rely on Bootstrap-like utility classes that fail silently when decoupled from the UX4G JavaScript runtime.
3. **AppShell Layout Compression:** `<main id="main-content">` in `AppShell.tsx` lacked `flex-1`, allowing the dark footer to shoot up into the middle of the screen on `/login`, `/register`, and `/fhir`.

