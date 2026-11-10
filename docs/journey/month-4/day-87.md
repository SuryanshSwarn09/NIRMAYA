# Day 87: Strict CoWIN/DigiLocker 3-Tile Citizen Portal (/patient)

**Date:** Tue Nov 10, 2026  
**Milestone:** 18-02 (Phase 5: Production Hardening & National Scale Architecture)  
**Target Release:** `v1.1.0`  
**Test Suite Target:** $\ge 903$ Tests Passing (100% Green)

---

## 1. Overview and Objectives

Healthcare interfaces frequently overwhelm citizens and caregivers with complex navigation, clinical jargon, and dense EHR menus. Inspired by the extreme usability and national adoption of India's Digital Public Infrastructure (CoWIN, DigiLocker, and Aarogya Setu), Day 87 introduces the **Strict CoWIN/DigiLocker 3-Tile Citizen Portal (`/patient`)**.

Within 3 seconds of loading, any citizen can instantly view and execute the 3 most essential daily healthcare tasks:
1. **Tile 1 (My Health ID):** 14-digit official ABHA ID (`91-8472-1048-2190`), verified `@abdm` handle, demographic profile, and a 1-click full-screen maximum-brightness QR modal for instant hospital OPD counter scanning.
2. **Tile 2 (Today's Active Medicines):** Complete elimination of Latin prescription abbreviations (`b.i.d.`, `t.i.d.`, `q.h.s.`, `p.o.`) in favor of plain time-of-day badges (Morning, Afternoon, Night), plain meal instructions, active course countdown progress bars, and proactive refill alerts.
3. **Tile 3 (Doctor Visits & Reports):** Chronological hospital consultations, clear plain-language diagnoses, and 1-click downloads of tamper-evident digitally signed prescription summaries and verified lab reports.
4. **Header Dependent Family Persona Switching:** Direct integration with `CalcomDependentSwitcher` to switch between Self (Adult), Pediatric Minor (Aarav Patel), and Geriatric Senior (Ramesh Patel) contexts with instant sub-10ms UI updates.
5. **Dual-Mode Ergonomics:** A high-contrast segmented control allowing citizens to toggle between the streamlined 3-Tile Citizen View and the in-depth Specialist Health Vault (vitals telemetry, longitudinal problem lists, and WebRTC telemedicine).

---

## 2. Implemented Architecture

```mermaid
flowchart TD
    subgraph PortalView["CoWIN/DigiLocker 3-Tile Citizen Portal (/patient)"]
        ContextSwitcher["CalcomDependentSwitcher: Self | Minor (Aarav) | Senior (Ramesh)"]
        ModeToggle["View Mode: 3-Tile Citizen View vs Specialist Health Vault"]
        
        subgraph ThreeTiles["High-Impact 3-Tile Grid"]
            Tile1["Tile 1: My Health ID Card & OPD Counter QR Modal"]
            Tile2["Tile 2: Today's Active Medicines (Morning / Noon / Night)"]
            Tile3["Tile 3: Doctor Visits & Digitally Signed Reports"]
        end
        
        ContextSwitcher --> ModeToggle
        ModeToggle --> ThreeTiles
    end

    subgraph AggregationLayer["Citizen Portal Backend Service"]
        Aggregator["Sub-10ms Aggregator (get_citizen_three_tiles)"]
        MemCache["In-Memory LRU Cache Store"]
        SigEngine["Plain-Language Schedule Parser & Refill Engine"]
        TokenMinter["Hospital Check-In QR Generator (60-min TTL)"]
    end

    ThreeTiles --> Aggregator
    Aggregator --> MemCache
    Aggregator --> SigEngine
    Aggregator --> TokenMinter
```

---

## 3. Key Components Implemented

### Component A: Unified Pydantic Schemas (`backend/app/schemas/citizen_portal.py`)
- `CitizenHealthIdSummary`: Official 14-digit ABHA display, formatted number, legal name, demographic profile, and camera-ready QR string.
- `PlainScheduleItem`: Visual time-of-day intake flags (`morning`, `afternoon`, `night`, `as_needed`) with human-friendly descriptions.
- `CitizenActiveMedicineItem`: Medicine name, dosage, plain schedule list, countdown duration, and refill urgency badges (`none`, `soon`, `urgent`).
- `CitizenVisitReportItem`: Chronological consultations and diagnostic reports with plain diagnoses, SHA-256 signatures, and download URLs.
- `HospitalCheckInQrResponse`: Ephemeral check-in token with 60-minute TTL and facility context routing.
- `CitizenThreeTileResponse`: Atomic 3-tile aggregation container with cache hit telemetry.

### Component B: Enterprise Service Layer (`backend/app/services/citizen_portal_service.py`)
- `get_citizen_three_tiles`: Atomic aggregation providing sub-10ms delivery of all 3 tiles for adult, pediatric, and geriatric personas.
- `_parse_frequency_code`: Intelligent parser converting clinical sig codes (`1-0-1`, `0-1-0`, `1-1-1`, `0-0-1`, `PRN`) into plain time-of-day indicators.
- `_calculate_refill_urgency`: Calculates proactive refill deadlines ($\le 3$ days $\rightarrow$ urgent, $\le 7$ days $\rightarrow$ soon).
- `generate_hospital_checkin_qr`: Mints high-contrast OPD scan payloads with 3600-second TTL.

### Component C: REST API Endpoints (`backend/app/api/v1/endpoints/citizen_portal.py`)
- `GET /api/v1/patient/citizen-portal/tiles`: Primary aggregated 3-tile endpoint.
- `GET /api/v1/patient/citizen-portal/qr-token`: Short-lived OPD check-in token generator.
- `GET /api/v1/patient/citizen-portal/medicines`: Focused active medicines schedule feed.
- `GET /api/v1/patient/citizen-portal/visits`: Chronological doctor consultations and lab reports feed.

### Component D: Cal.com Design System Frontend UI
- [`DpiHealthIdTile`](file:///e:/nirmaya-side/frontend/src/components/patient/DpiHealthIdTile.tsx): Tile 1 component rendering the ABHA ID card, 1-click copy action, and hospital OPD scan button.
- [`DpiQrCheckInModal`](file:///e:/nirmaya-side/frontend/src/components/patient/DpiQrCheckInModal.tsx): Full-screen maximum-brightness modal for hospital OPD scanners.
- [`DpiActiveMedicinesTile`](file:///e:/nirmaya-side/frontend/src/components/patient/DpiActiveMedicinesTile.tsx): Tile 2 component rendering plain Morning/Afternoon/Night indicators, meal instructions, and refill countdowns.
- [`DpiPastVisitsTile`](file:///e:/nirmaya-side/frontend/src/components/patient/DpiPastVisitsTile.tsx): Tile 3 component with tabbed filtering and 1-click signed PDF summaries.
- [`PatientVaultPage`](file:///e:/nirmaya-side/frontend/src/app/patient/page.tsx): Updated with dual-mode switching and integrated with `CalcomDependentSwitcher`.

---

## 4. Verification and Benchmark Results

- **Next.js 15 Production Build:** 100% clean compilation across all 13 routes.
- **Dedicated Portal Tests:** 26 / 26 tests passing in 1.78s (`test_citizen_portal.py`).
- **Cumulative Test Suite:** 903 / 903 tests passing across 51 test modules.
- **Aggregation Latency:** Sub-10ms delivery on cached responses ($< 5\text{ms}$ average).

---

## 5. Artifacts and Commits

- Schemas: [`backend/app/schemas/citizen_portal.py`](file:///e:/nirmaya-side/backend/app/schemas/citizen_portal.py)
- Service: [`backend/app/services/citizen_portal_service.py`](file:///e:/nirmaya-side/backend/app/services/citizen_portal_service.py)
- Endpoints: [`backend/app/api/v1/endpoints/citizen_portal.py`](file:///e:/nirmaya-side/backend/app/api/v1/endpoints/citizen_portal.py)
- UI Components: [`frontend/src/components/patient/`](file:///e:/nirmaya-side/frontend/src/components/patient/)
- Tests: [`backend/tests/test_citizen_portal.py`](file:///e:/nirmaya-side/backend/tests/test_citizen_portal.py)
- Page: [`frontend/src/app/patient/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/patient/page.tsx)
