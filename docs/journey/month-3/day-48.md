# Day 48: Milestone 10-03 - ABDM M2 Patient Discovery & Fuzzy Demographic Matcher

**Milestone:** 10-03 (Month 3, Week 10 / ABDM M2 Discovery Protocol)  
**Author:** Suryansh Swarn (`suryanshswarn@gmail.com`)  
**Status:** Completed & Certified  

---

## 1. Executive Summary

Day 48 delivers the complete, production-grade implementation of the **ABDM Milestone 2 (M2) Patient Discovery Protocol** for NIRMAYA Health Information Provider (HIP) nodes.

Under the National Health Authority (NHA) ABDM M2 specification, when a citizen searches for their historical health records inside any ABDM-compliant PHR mobile app (e.g., ABHA App, Aarogya Setu, Paytm Health, Eka Care), the central ABDM Gateway broadcasts an asynchronous discovery query (`POST /v0.5/care-contexts/discover`) to registered HIP hospital systems.

NIRMAYA must instantaneously evaluate incoming patient queries against its database, discover matching patient records with mathematical confidence, extract all associated care contexts (consultations, lab investigations), and respond asynchronously back to the gateway (`POST /v0.5/care-contexts/on-discover`).

---

## 2. Multi-Tier Demographic Matching Engine

The discovery engine employs a multi-tiered matching pipeline to balance recall (finding the right patient despite typos or transpositions) with strict patient privacy:

```
┌────────────────────────────────────────────────────────────────────────┐
│             ABDM M2 MULTI-TIER PATIENT DISCOVERY ENGINE                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   [ Inbound Gateway Query: Name, Gender, YOB, Mobile, Identifiers ]    │
│                               │                                        │
│                               ▼                                        │
│          [ Tier 1: Deterministic Verified Match ]                      │
│          - Exact ABHA Number (91-XXXX-XXXX-XXXX)                       │
│          - Exact ABHA Address (username@abdm)                          │
│          - Exact MRN / Local Patient Reference                         │
│          ───► Match Score = 1.00 (Instant Match)                       │
│                               │                                        │
│                     (If no exact match)                                │
│                               ▼                                        │
│          [ Tier 2: Verified Mobile + Fuzzy Demographics ]              │
│          - Normalized 10-digit Phone Match                             │
│          - Levenshtein & Token-Set Name Similarity                     │
│          - Year-of-Birth Tolerance (+/- 1 year = 0.85)                 │
│          - Strict Gender Alignment                                     │
│          ───► Match Score = 0.90 to 0.95                               │
│                               │                                        │
│                     (If no mobile match)                               │
│                               ▼                                        │
│          [ Tier 3: Pure Fuzzy Demographic Match ]                      │
│          - Weighted Formula:                                           │
│            Score = (Name * 0.50) + (YOB * 0.30) + (Gender * 0.20)      │
│                               │                                        │
│                               ▼                                        │
│          [ Ambiguity Protection Filter ]                               │
│          - Candidate with highest score selected                       │
│          - If multiple candidates score >= threshold and the top       │
│            two scores differ by <= 0.08, query is REJECTED             │
│            (ABDM Code 1441: Discovery ambiguity detected)             │
│                               │                                        │
│                               ▼                                        │
│          [ Care Context Extractor ]                                    │
│          - Clinical Consultations (OPD / Teleconsultations)            │
│          - Diagnostic Laboratory Orders (LOINC Panels)                 │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Mathematical & Normalization Rules:
1. **Honorific Stripping:** Strips common prefixes (`Mr.`, `Mrs.`, `Ms.`, `Dr.`, `Shri`, `Smt`, `Kumar`, `Kumari`) and punctuation to prevent superficial mismatches.
2. **Levenshtein Distance & Token Sort:** Evaluates both full string similarity and token set permutations (e.g., `"Arun Kumar Patel"` matches `"Patel Arun"` with high confidence).
3. **Year of Birth Tolerance:** Exact match = 1.00; +/- 1 year variance (common in self-reported rural demographics) = 0.85; larger variance = 0.00.
4. **Gender Strictness:** Gender mismatch yields 0.0 score, immediately failing the match threshold.

---

## 3. Endpoints & Protocol Flow

### Inbound ABDM Gateway Webhook:
- **`POST /v0.5/care-contexts/discover`** (Complies with NHA ABDM M2 HIP API):
  - Returns `202 Accepted` immediately with acknowledgement payload.
  - Spawns background worker to perform database evaluation.
  - Dispatches signed asynchronous callback `POST /v0.5/care-contexts/on-discover` to gateway with correlation IDs (`resp.requestId = req.requestId`).

### Interactive Sandboxing & Operator Tools:
- **`POST /api/v1/abdm/m2/bridge/discovery/simulate`**:
  - Allows EMR administrators and compliance auditors to test discovery queries in real-time.
  - Returns comprehensive diagnostic breakdown: match score, breakdown by dimension (name, YOB, gender, mobile, identifier), matched patient vault profile, care contexts count, and ambiguity status.

---

## 4. Frontend Cal.com Components

- **`PatientDiscoverySimulatorModal.tsx` (`frontend/src/components/abdm/PatientDiscoverySimulatorModal.tsx`):**
  - Cal.com clean design language (`#ffffff` canvas, hairline `#e5e7eb` borders, `rounded-[8px]` containers, `rounded-[6px]` badges, `#111827` action buttons).
  - Search criteria form: Full Name, 10-digit Mobile, Gender, Year of Birth, ABHA Number/Address, and Match Threshold Slider (0.50 to 1.00).
  - Diagnostic Match Result card:
    - Real-time score gauge (e.g. 95% Match).
    - Dimension-by-dimension radar pill badges (Name: 1.0, YOB: 1.0, Gender: 1.0, Mobile: 1.0).
    - Discovered Patient Demographic Card (Legal Name, Masked Phone, DOB, Gender, ABHA Number).
    - Discovered Care Contexts List (Appointments, Consultations, Diagnostic LOINC orders).
- **Mounted in `frontend/src/app/abdm/page.tsx`:**
  - Accessible via "Simulate Patient Discovery" button in the ABDM M2 Bridge Cockpit.

---

## 5. Verification & Testing Evidence

- **Automated Test Suite (`backend/tests/test_abdm_m2_discovery.py`):**
  - `test_levenshtein_distance_and_ratio`: PASSED (Exact, typo, empty strings).
  - `test_honorific_stripping`: PASSED (Shri, Smt, Dr, etc.).
  - `test_calculate_name_similarity`: PASSED (Typo tolerance, token reordering).
  - `test_calculate_yob_and_gender_similarity`: PASSED (Exact, +/-1 yr grace, gender mismatch).
  - `test_candidate_match_deterministic_abha`: PASSED (Score 1.0).
  - `test_candidate_match_mobile_and_fuzzy_name`: PASSED (Score 0.95 with typo).
  - `test_discover_patient_with_care_contexts`: PASSED (Returns clinical appointment and diagnostic order care contexts).
  - `test_endpoint_care_contexts_discover_sync_202`: PASSED (202 Accepted on gateway query).
  - `test_endpoint_discovery_simulate`: PASSED (Simulate endpoint returns match score and care contexts).
  - `test_discovery_ambiguity_protection`: PASSED (Rejects close collisions to protect patient privacy).
- **Frontend Verification:**
  - Static typecheck (`npx tsc --noEmit`): **0 errors**.
  - Production build (`npm run build`): **0 errors**, all 13 routes compiled cleanly.
- **Full Backend Regression Suite:** **312 / 312 passed (100% green in 119.20s)**.
