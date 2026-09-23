# Cal.com-Inspired Modern SaaS UI Transformation

**Date:** September 23, 2026  
**Scope:** Frontend Design System Overhaul  
**Author:** Suryansh Swarn  
**Status:** Completed  

---

## 1. Overview & Aesthetic Rationale

The NIRMAYA frontend underwent a complete aesthetic transformation inspired by the modern, calendar-software-first **Cal.com design system**. The primary objective was to replace generic clinical styling with a clean, confident SaaS interface that emphasizes:

1. **Pure White Canvas (`#ffffff`):** A bright, uncrowded canvas providing generous whitespace and visual clarity across all clinical views.
2. **Dominant Black Primary Action Layer (`#111111`):** All primary calls-to-action (CTAs) are rendered in near-black `#111111` (`#242424` pressed) with `8px` (`rounded-md`) border radius and 40px height. Primary CTAs strictly refrain from colored fills.
3. **Geometric Display Typography:** Headlines utilize display sizing with negative letter-spacing (`-0.5px` to `-2px`) paired with Inter (`400-600` weight) for body copy, buttons, and navigation.
4. **Soft-Rounded Content Cards (`12px`):** Abstract feature claims reside in `#f5f5f5` light-gray cards (`32px` padding), while product fragments reside in pure white cards with `1px` `#e5e7eb` hairline borders and subtle elevation (`0 1px 2px rgba(0,0,0,0.05)`).
5. **Real Product UI Fragments in Cards:** Rather than generic healthcare illustrations, component voltage comes from showing real product chrome directly embedded inside cards:
   - An interactive clinical consultation slot picker widget with verified doctor HPR credentials.
   - An ABHA Health ID card with active 24-hour consent token TTL indicator.
   - A structured HL7 FHIR R4 `MedicationRequest` JSON payload snippet.
   - A dual cryptographic PDF and LOINC diagnostic observation ingest panel.
6. **Signature `NavPillGroup` Switcher:** A pill-radius container (`#f8f9fa`, `6px` padding) with a pure white active tab supported by a soft shadow, facilitating client-side switching across the three network pillars.
7. **The Dark Footer Rule (`#101010`):** The footer is the **only dark surface** on long-scroll pages, visually anchoring and closing the page with `#a1a1aa` link hierarchy.

---

## 2. Design System Color & Typography Tokens

| Token | Hex Value | Usage |
|---|---|---|
| `--color-primary` | `#111111` | Primary CTA buttons, display headlines |
| `--color-primary-active` | `#242424` | Primary CTA pressed / active state |
| `--color-canvas` | `#ffffff` | Page background floor, mockup cards |
| `--color-surface-soft` | `#f8f9fa` | NavPillGroup container background, status telemetry bar |
| `--color-surface-card` | `#f5f5f5` | Feature cards, category badges, subtle containers |
| `--color-surface-dark` | `#101010` | Signature closing footer background |
| `--color-hairline` | `#e5e7eb` | 1px border on inputs, cards, top nav |
| `--color-body` | `#374151` | Running paragraph text |
| `--color-muted` | `#6b7280` | Secondary labels, descriptions, inactive tabs |
| `--color-on-dark-soft` | `#a1a1aa` | Footer link lists |
| `--color-badge-emerald`| `#34d399` | Verification indicators, active status |
| `--color-badge-orange` | `#fb923c` | Warnings, rating stars |

---

## 3. Micro-Commit Journal

The transformation was executed across 12 atomic micro-commits:

1. `6c47b1d: feat(ui): configure Cal.com design tokens and palette in globals.css`
2. `e2ff74c: feat(ui): configure Inter typography and display tracking in layout.tsx`
3. `cd1ee9c: feat(ui): update Button primitive with Cal.com primary black and secondary styles`
4. `7320ecf: feat(ui): update Badge component with Cal.com pill geometry and pastel accents`
5. `0f6df0f: feat(ui): refactor Card component to support Cal.com feature and product mockup styles`
6. `25289df: feat(ui): create signature Cal.com NavPillGroup switcher component`
7. `0092688: feat(layout): redesign top Navbar to 64px pinned white bar with Cal.com styling`
8. `e5bc5af: feat(common): modernize BrandLogo with minimalist geometric mark`
9. `c7ea0e8: feat(layout): update SystemStatusBar telemetry bar with subtle hairline aesthetic`
10. `96167db: feat(layout): transform Footer into Cal.com signature near-black closing surface`
11. `9678f6c: feat(home): redesign landing page with Cal.com 7/5 hero and embedded product UI fragment`
12. `docs(ui): document Cal.com design system migration in project journey`

---

## 4. Verification & Standards Compliance

- **Next.js 15 Turbopack Build:** Ran `next build --turbopack` and verified clean compilation across all static routes with 0 type errors.
- **Responsive Layouts:** Tested across mobile (<768px), tablet (768-1024px), and desktop (>1024px) breakpoints.
- **Tag Discipline:** Zero daily tags created; active release tag remains `v0.1.0-alpha.w2`.
