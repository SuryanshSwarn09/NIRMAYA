---
name: calcom-design-system
description: Cal.com-inspired clean modern SaaS design system for NIRMAYA. Covers color tokens (white canvas, #111111 primary, #f5f5f5 cards, #101010 dark footer), Cal Sans & Inter typography, 8px/12px/16px radius hierarchy, nav-pill-groups, and product UI fragments embedded directly inside cards.
---

# Cal.com Design System & UI Architecture

A clean, calendar-software-first interface anchored on a pure white canvas (`#ffffff`) with near-black primary CTAs (`#111111`) and custom **Cal Sans** display typography. The system reads as friendly modern SaaS — generous whitespace, soft-rounded cards (~12px), product UI fragments shown directly inside cards, and a dark navy/black footer (`#101010`) that visually closes long-scroll pages. Brand voltage comes from the Cal Sans display headline (a custom geometric face) and from product UI artifacts shown in-card rather than from heavy accent colors.

---

## 1. Design Tokens & Specification

### Colors
```yaml
colors:
  primary: "#111111"
  primary-active: "#242424"
  primary-disabled: "#e5e7eb"
  ink: "#111111"
  body: "#374151"
  muted: "#6b7280"
  muted-soft: "#898989"
  hairline: "#e5e7eb"
  hairline-soft: "#f3f4f6"
  canvas: "#ffffff"
  surface-soft: "#f8f9fa"
  surface-card: "#f5f5f5"
  surface-strong: "#e5e7eb"
  surface-dark: "#101010"
  surface-dark-elevated: "#1a1a1a"
  on-primary: "#ffffff"
  on-dark: "#ffffff"
  on-dark-soft: "#a1a1aa"
  brand-accent: "#3b82f6"
  success: "#10b981"
  warning: "#f59e0b"
  error: "#ef4444"
  badge-orange: "#fb923c"
  badge-pink: "#ec4899"
  badge-violet: "#8b5cf6"
  badge-emerald: "#34d399"
```

### Typography Scale
```yaml
typography:
  display-xl:
    fontFamily: "Cal Sans, Inter, sans-serif"
    fontSize: 64px
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: -2px
  display-lg:
    fontFamily: "Cal Sans, Inter, sans-serif"
    fontSize: 48px
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -1.5px
  display-md:
    fontFamily: "Cal Sans, Inter, sans-serif"
    fontSize: 36px
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: -1px
  display-sm:
    fontFamily: "Cal Sans, Inter, sans-serif"
    fontSize: 28px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: -0.5px
  title-lg:
    fontFamily: "Inter, sans-serif"
    fontSize: 22px
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: -0.3px
  title-md:
    fontFamily: "Inter, sans-serif"
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: 0
  title-sm:
    fontFamily: "Inter, sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: 0
  body-md:
    fontFamily: "Inter, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0
  body-sm:
    fontFamily: "Inter, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0
  caption:
    fontFamily: "Inter, sans-serif"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0
  code:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0
  button:
    fontFamily: "Inter, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0
  nav-link:
    fontFamily: "Inter, sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0
```

### Border Radius Hierarchy
```yaml
rounded:
  xs: 4px       # Badge accents, indicators
  sm: 6px       # Dropdown items, inner elements
  md: 8px       # Standard CTA buttons, text inputs, category tabs
  lg: 12px      # Content cards (feature cards, pricing tiers, testimonial cards)
  xl: 16px      # Hero app-mockup container card
  pill: 9999px  # Nav-pill-group, status badge pills
  full: 9999px  # Circular avatars, icon buttons
```

### Spacing System
```yaml
spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  section: 96px # Standard vertical rhythm between major bands
```

---

## 2. Core Visual & Component Blueprints

### Buttons
- **`button-primary`**: Background `#111111`, Text `#ffffff`, Inter 14px/600, Rounded 8px (`rounded-md`), Padding `12px 20px`, Height `40px`. Active/Pressed state shifts to `#242424`.
- **`button-secondary`**: White canvas background, text `#111111`, 1px hairline border (`#e5e7eb`), rounded 8px.
- **`button-icon-circular`**: 36px circular button (`rounded-full`), white background, hairline border.
- **`button-text-link`**: Transparent background, text `#111111`, Inter 14px/600.

### Top Navigation & Nav-Pill-Group
- **`top-nav`**: Pinned white nav bar (`#ffffff`), 64px height, hairline bottom border. Brand wordmark on left, horizontal links in center (`Inter 14px / 500`), right-side CTA cluster.
- **`nav-pill-group`**: Signature Cal.com component. Soft background (`#f8f9fa`), internal padding `6px`, rounded `rounded-full` (`9999px`). Active tab is a white pill with subtle shadow (`0 1px 2px rgba(0,0,0,0.05)`). Inactive tabs have muted text (`#6b7280`).

### Cards & In-Card Product UI Fragments
- **`feature-card`**: Light gray background (`#f5f5f5`), rounded 12px (`rounded-xl`), internal padding 32px.
- **`product-mockup-card`**: White card (`#ffffff`) with 1px hairline border and subtle shadow. Contains real, live product UI chrome (e.g. appointment picker, ABHA ID card, lab test order table) rather than abstract illustrations.
- **`pricing-tier-card-featured`**: Inverts to `#101010` dark surface with `#ffffff` text. Color contrast performs the elevation without loud badges or gradients.

### Footer
- **`footer`**: Deep near-black (`#101010`) closing the entire page. Text is `#a1a1aa`. Multi-column link hierarchy. The only dark surface on the page.

---

## 3. Translation to NIRMAYA Healthcare Platform

When styling the NIRMAYA frontend (Next.js 15 + Tailwind CSS):

1. **Header & Brand:**
   - Wordmark: "nirmaya" with lowercase geometric Cal Sans weight 600, paired with an interoperability badge pill (`#f8f9fa`).
   - Top-right CTA: "Launch Health Vault" (`button-primary` in `#111111`).
2. **Hero Band:**
   - Left (7 cols): Display-xl headline with -2px letter-spacing: *"Interoperable health records, finally simplified."*
   - Right (5 cols): Embedded product UI mockup showing an interactive **ABHA Health ID card + Doctor Consultation Slot Picker** inside a `#ffffff` card with `rounded-2xl` and subtle drop shadow.
3. **Pillar Switcher (Nav-Pill-Group):**
   - A floating pill switcher toggling between:
     - `Patient Vault (FHIR R4 / ABHA)`
     - `Doctor EMR (Specialties / HPR)`
     - `Diagnostic Gateway (Lab / HFR)`
4. **Clinical UI Artifacts inside Cards:**
   - Rather than stock illustrations, render realistic in-card UI fragments:
     - Real doctor profile with consultation fees, HPR ID badge (`@hpr.abdm`), and specialty tags.
     - Real ABDM ABHA resolution widget (14-digit number and `@abdm` handle).
     - Real diagnostic test order panel with LOINC / NABL badges.
5. **Footer:**
   - `#101010` dark navy/black background closing the portal, with links to Standards (HL7 FHIR R4, ABDM, DISHA), API Documentation, and GitBook journey log.

---

## 4. Do's and Don'ts

### Do
- Reserve `#111111` for primary CTAs and display type.
- Use Cal Sans (or Inter 600 with negative tracking `-0.04em`) for display headlines.
- Maintain strict alternating rhythm: White canvas → `#f5f5f5` feature cards → White product-mockup cards → `#101010` dark footer.
- Keep border radii disciplined: `8px` for buttons/inputs, `12px` for cards, `16px` for hero mockup container, `9999px` for pills.
- Show real product UI chrome inside cards.

### Don't
- Don't use heavy gradient fills or glassmorphism blurs.
- Don't use bright accent colors on primary buttons (keep buttons near-black `#111111`).
- Don't put dark cards anywhere except the footer and the featured highlight card.
- Don't exceed 1200px max content container width on desktop.
