# NIRMAYA Design System Specification

**Scope:** Visual Identity, UI Primitives, Color Tokens & Clinical Interaction Standards  
**Version:** 1.0.0  

---

## 1. Design Philosophy

NIRMAYA (Networked Interoperable Records Medical Assets & Your Archives) employs a **clean, high-contrast modern SaaS design aesthetic** engineered specifically for clinical clarity, accessibility, and high data density without cognitive overload:

1. **Pure White Canvas (`#ffffff`):** Avoids noisy gradients or heavy background textures; clinical information is displayed against crisp, readable surfaces.
2. **High-Contrast Primary Actions (`#111111`):** Core calls-to-action (CTAs) utilize near-black styling (`#111111` with `#242424` hover states), creating unambiguous affordances that stand out across dense EMR panels.
3. **Hairline Subtle Borders (`#e5e7eb`):** Structural demarcation relies on delicate 1px hairline borders rather than heavy shadows or bevels.
4. **Soft Pastel Semantic Badges:** Status indicators utilize muted pastel fills paired with deeply saturated typography (e.g. emerald `#ecfdf5` / `#065f46` for verified records, rose `#fef2f2` / `#991b1b` for abnormal results) preventing visual fatigue.
5. **Architectural Grounding (Dark Footer):** A deep near-black footer (`#101010`) acts as the single grounding dark surface on public pages, providing a definitive visual closure.
6. **Brand Separation & Trademark Exclusivity:** All external trademarks and brand names are strictly excluded from user interfaces, portal navigation, and modal dialogues. Visual layouts and ergonomic design patterns are implemented independently using custom Vanilla Tailwind CSS and React primitives.

---

## 2. Core Color Tokens

### Neutral & Surface Foundation
| Token | Hex Value | Semantic Usage |
|---|---|---|
| `canvas-white` | `#ffffff` | Primary background canvas, card surfaces, modal dialog bodies |
| `surface-subtle` | `#f8f9fa` | Secondary panel backgrounds, table headers, hover highlights |
| `surface-muted` | `#f5f5f5` | Feature card containers, segmented pill wrappers |
| `surface-dark` | `#101010` | Grounding footer background, code block containers |
| `border-hairline` | `#e5e7eb` | Standard 1px card borders, dividing lines, input outlines |
| `border-subtle` | `#d1d5db` | Interactive input focus states, active card outlines |

### Typography & Monochromatic Hierarchy
| Token | Hex Value | Usage |
|---|---|---|
| `text-primary` | `#111111` | Headings, primary labels, selected item text, buttons |
| `text-secondary` | `#374151` | Body copy, descriptive annotations, active metadata |
| `text-muted` | `#6b7280` | Timestamps, secondary subtitles, helper hints |
| `text-faint` | `#9ca3af` | Placeholder copy, disabled controls |

### Clinical Status & Semantic Pastel Tokens
| Semantic Role | Background Fill | Border | Text Foreground | Application |
|---|---|---|---|---|
| **Verified / Normal** | `#ecfdf5` | `#a7f3d0` | `#065f46` | HPR Verified, Active Consents, Normal LOINC results |
| **Pending / Warning** | `#fff7ed` | `#fed7aa` | `#9a3412` | Slot Holds, Preliminary SOAP notes, Borderline ranges |
| **Critical / Abnormal** | `#fef2f2` | `#fecaca` | `#991b1b` | Abnormal laboratory flags, emergency requisitions |
| **ABDM / National** | `#f5f3ff` | `#ddd6fe` | `#5b21b6` | ABHA Health ID badges, Care Context linkages |
| **FHIR Standard** | `#f8f9fa` | `#e5e7eb` | `#111111` | HL7 FHIR Release 4 standard badges, JSON inspections |

---

## 3. Typography Hierarchy

NIRMAYA combines a modern geometric sans-serif for editorial readability with a specialized monospace font for cryptographic and clinical codes:

- **Primary Sans:** Inter / Plus Jakarta Sans (`var(--font-sans)`)
  - `display-xl`: 48px – 64px, weight 600, letter-spacing -2px (Landing hero headlines)
  - `display-lg`: 36px – 44px, weight 600, letter-spacing -1.5px (Portal section titles)
  - `display-md`: 24px – 32px, weight 600, letter-spacing -1px (Card headers, modal titles)
  - `body-sm`: 13px – 14px, weight 400 / 500 (Clinical narratives, SOAP notes)
  - `caption`: 11px – 12px, weight 500 / 600 (Badges, metadata labels, status chips)
- **Clinical Monospace:** JetBrains Mono (`var(--font-mono)`)
  - Standardized for ABHA 14-digit IDs (`91-8472-1092-4821`), LOINC codes (`24331-1`), SHA-256 cryptographic digests, and FHIR R4 raw resource payloads.

---

## 4. Layout Geometry & Grid Systems

1. **7/5 Asymmetric Grid System:**
   - Landing page hero and provider scheduling interfaces deploy a 7-column primary content pane paired with a 5-column secondary action or calendar matrix pane on desktop (`lg:grid-cols-12`).
2. **Corner Radii Scale:**
   - `6px`: Action chips, inline input fields, small badges (`rounded-[6px]`)
   - `8px`: Standard buttons, consultation list items (`rounded-[8px]`)
   - `12px`: Standard feature and EMR cards (`rounded-[12px]`)
   - `16px`: Hero mockups, interactive slot pickers, modal dialog containers (`rounded-[16px]`)
   - `9999px`: Status indicator pills, NavPillGroup switcher containers (`rounded-full`)

---

## 5. UI Primitives Overview

- **`Button` (`components/ui/Button.tsx`):**
  - Variants: `primary` (`#111111` solid), `secondary` (white `#ffffff` with hairline `#e5e7eb`), `outline`, `ghost`, `danger`.
  - Supports loading spinners and embedded clinical icons.
- **`Badge` (`components/ui/Badge.tsx`):**
  - Compact status chips supporting optional pulsating status dots and clinical semantic colorings (`verified`, `pending`, `critical`, `abdm`, `fhir`).
- **`Card` (`components/ui/Card.tsx`):**
  - Structural content enclosures featuring `feature` (subtle `#f5f5f5` surface) and `mockup` (pure `#ffffff` canvas with hairline border and subtle shadow).
- **`NavPillGroup` (`components/ui/NavPillGroup.tsx`):**
  - Segmented sub-navigation control with pill-shaped rounded container and floating white active tab indicator.
- **`ClinicalSlotPicker` (`components/appointments/ClinicalSlotPicker.tsx`):**
  - Dual-pane scheduling interface with monthly interactive calendar matrix on the left and time availability buttons on the right with modality filters (In-Person vs Virtual).
- **`SlotHoldCountdown` (`components/appointments/SlotHoldCountdown.tsx`):**
  - Real-time 10-minute hold duration banner reassuring patients during intake checkout that their slot is locked against concurrent bookings.
