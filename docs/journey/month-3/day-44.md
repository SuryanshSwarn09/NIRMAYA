# Day 44: Milestone 09-04: 14-Digit ABHA Generation, @abdm PHR Handle Reservation & HPR Doctor Onboarding

**Date:** October 28, 2026  
**Milestone:** 09-04 (Month 3, Week 9)  
**Executed Micro-Commits:**  
1. `feat(abdm): implement 14-digit abha issuance and phr handle reservation service`
2. `feat(patient): add abha creation modal and doctor hpr onboarding card`
3. `test(abdm): author automated test suite for abha issuance phr linking and hpr`
4. `docs(journey): record Day 44 milestone log, update summary, and changelog`

---

## 1. Objectives & Architectural Context

Building upon Day 41 (ABDM Gateway Session Client & RSA-2048 Cryptography), Day 42 (DigiLocker OAuth 2.0 PKCE & e-Aadhaar Verification), and Day 43 (Direct Aadhaar Demographic OTP Verification), **Day 44** delivers the credential issuance and practitioner onboarding engine for **ABDM Milestone 1 (M1)**:

1. **14-Digit ABHA Number Minting (`91-XXXX-XXXX-XXXX`):**
   - National Health Authority compliant 14-digit health identity number.
   - Begins with India country code `91`, followed by 11 randomly generated digits, and finalized with a mathematical **Verhoeff check digit** calculated over the preceding 13 digits.
   - Automatic format separation into 4 groups (`91-XXXX-XXXX-XXXX`).

2. **`@abdm` PHR Address Reservation & Linkage:**
   - Universal Personal Health Record (PHR) handle engine enforcing regex `^[a-z0-9._]{3,32}$`.
   - Enforces `@abdm` suffix across all patient handle claims.
   - Real-time availability check endpoint with reserved keyword filtering (`admin`, `root`, `nha`, `abdm`, `gov`, `support`, etc.) and collision detection against already registered handles.
   - Deterministic 3-alternative handle suggestion generator on collisions.
   - Persistent handle linkage binding the newly minted 14-digit ABHA Number to the reserved `@abdm` address.

3. **Healthcare Professional Registry (HPR) Onboarding:**
   - Practitioner credential verification and registry onboarding binding state medical council credentials (e.g. DMC, MMC, KMC, NMC) to official `@hpr.abdm` handles.
   - Updates `DoctorProfile.hpr_id` column in the database with active NHA registry status.

4. **Cal.com Geometric Frontend Components:**
   - `AbhaCreationModal.tsx`: A 3-step modal (14-digit ABHA generation, debounced `@abdm` handle search & claim, and credential card confirmation) designed with Cal.com geometric aesthetics (`rounded-[8px]`, `#ffffff` canvas, `#e5e7eb` hairline borders, `#111827` action buttons).
   - `HprOnboardingCard.tsx`: Dedicated HPR verification card in the Doctor EMR Cockpit (`/doctor`) allowing clinicians to view active registry status or onboard their state medical council credentials.

---

## 2. Engineered Component Architecture

```
e:\nirmaya-side\
├── backend\
│   ├── app\
│   │   ├── schemas\
│   │   │   ├── abdm_m1_issuance.py      # Pydantic v2 schemas: AbhaCreate, PhrAvailability, PhrLink, HprOnboard
│   │   │   └── __init__.py              # Exported issuance schemas
│   │   ├── services\
│   │   │   ├── abdm_issuance.py         # 14-digit ABHA generator, Verhoeff validator, PHR engine, HPR service
│   │   │   └── __init__.py              # Exported issuance services
│   │   └── api\v1\
│   │       ├── endpoints\abdm_issuance.py # REST endpoints: /abha/create, /phr/check-availability, /phr/link, /hpr/onboard
│   │       └── router.py                # Mounted /abdm/m1 router
│   └── tests\
│       └── test_abdm_m1_abha_hpr.py     # Automated test suite (5 / 5 passed)
└── frontend\src\
    ├── components\
    │   ├── patient\
    │   │   ├── AbhaCreationModal.tsx    # 3-step ABHA minting & PHR reservation modal
    │   │   ├── DigitalAbhaCard.tsx      # Integrated "Issue / Link ABHA" trigger
    │   │   ├── PatientOverviewTab.tsx   # Forwarded ABHA creation handlers
    │   │   └── index.ts                 # Barrel exports
    │   └── clinical\
    │       ├── HprOnboardingCard.tsx    # Doctor EMR Cockpit HPR registry onboarding card
    │       └── index.ts                 # Barrel exports
    └── app\
        ├── patient\page.tsx             # Mounted AbhaCreationModal in patient vault
        └── doctor\page.tsx              # Mounted HprOnboardingCard in doctor cockpit
```

---

## 3. Verification & Compliance Evidence

1. **Automated Backend Test Suite (`test_abdm_m1_abha_hpr.py`):**
   - `test_generate_14_digit_abha_service`: **PASSED** (14-digit length, 91 prefix, 4-group formatting, Verhoeff mathematical validity).
   - `test_phr_availability_and_reserved_keywords`: **PASSED** (Reserved keywords flagged unavailable with 3 valid alternatives; valid custom handles approved).
   - `test_endpoint_create_abha_number`: **PASSED** (`POST /api/v1/abdm/m1/abha/create` returns M1-compliant ABHA payload).
   - `test_endpoint_phr_link_and_collision`: **PASSED** (`POST /api/v1/abdm/m1/phr/link` links address, rejects duplicates with HTTP 400).
   - `test_endpoint_hpr_onboard_doctor`: **PASSED** (`POST /api/v1/abdm/m1/hpr/onboard` creates/updates doctor profile with `@hpr.abdm` ID).
   - **Result:** **5 / 5 passed (100% green in 1.48s)**.

2. **Full Backend Regression Suite:**
   - **282 / 282 passed (100% green in 62.84s)** across all 24 test modules.

3. **Frontend Production Build & Typecheck:**
   - TypeScript verification (`tsc --noEmit`): **0 errors**.
   - Next.js 15.5.25 App Router compilation: **0 errors**.

4. **Security & Standard Compliance:**
   - **Verhoeff Checksum (Dihedral Group D5):** Enforced on 14th digit to detect 100% of single-digit entry errors and transposition errors.
   - **Reserved Word Sanitization:** Disallows squatting or impersonation of official NHA, ABDM, and government handles.
   - **Strict Anti-Vibe-Coding:** Cal.com geometric design language, zero purple gradients, zero emojis, zero em dashes.
