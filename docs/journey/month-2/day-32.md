# Day 32: Milestone 07-02: Interactive Digital ABHA ID Card Generator & QR Verification

**Date:** October 23, 2026  
**Milestone:** 07-02 (Month 2, Week 7)  
**Executed Micro-Commits (Strict 8-Commit Schedule):**  
1. `ec52e05: feat(abdm): implement abha card cryptographic payload generator and verification service`
2. `02a7b38: feat(api): expose rest endpoints for abha card generation and qr signature verification`
3. `0589fd3: feat(frontend): implement pure vector qr code generator and abdm payload encoder`
4. `0be6825: feat(frontend): implement authentic dual-sided digital abha id card canvas`
5. `dd3e322: feat(frontend): implement abha card high-res export and print modal`
6. `81762b5: feat(frontend): implement interactive abha qr code scanner and verification modal`
7. `c7162a7: feat(frontend): integrate digital abha card and verification into patient portal`
8. `docs(journey): author day 32 engineering log, update summary, and changelog`

---

## 1. Objectives & Architectural Context

Under the **Ayushman Bharat Digital Mission (ABDM)** specification established by India's National Health Authority (NHA), every citizen is entitled to an authentic digital health identity represented by a 14-digit Ayushman Bharat Health Account (ABHA) number and an `@abdm` health handle. A cornerstone of national interoperability is the **Digital ABHA ID Card**—a cryptographic credential containing essential demographic claims and an offline-verifiable vector QR code.

Prior to Day 32, NIRMAYA's patient portal rendered a placeholder mockup card without dynamic QR code generation, cryptographic signatures, dual-sided flip capabilities, or export utilities. 

Day 32 delivered an enterprise-grade, end-to-end digital ABHA ID Card system encompassing:
1. **Cryptographic Payload Generator & Verification Engine:** Canonical demographic claims normalization with HMAC-SHA256 digital attestation and timing-safe signature comparison.
2. **REST API Surface:** FastAPI endpoints for authenticated card generation and public/provider QR payload integrity verification.
3. **Pure Vector QR Code Engine:** Zero-dependency SVG rasterization and compact ABDM JSON string encoding.
4. **Dual-Sided 3D Card Canvas:** Authentic National Health Authority styling with Indian tricolor banner, emblem badge, demographic claims, 14-digit ABHA copy utility, and emergency health profile.
5. **High-Res Export & Print Modal:** ID-1 wallet print sheet (85.6mm × 54mm) with `@media print` styling, vector SVG export, and JSON claim certificate download.
6. **Interactive QR Scanner & Verification Modal:** In-browser scanner simulator, real-time signature audit against ABDM root, and cryptographic tamper-detection testing tool.

---

## 2. Engineered Component Architecture

```
e:\nirmaya-side\
├── backend\app\
│   ├── schemas\abha_card.py       # Pydantic v2 models: AbhaCardData, AbhaQrPayload, AbhaCardResponse, Verification
│   ├── services\abha_card.py      # HMAC-SHA256 signer, claims canonicalizer, and timing-safe verifier
│   └── api\v1\endpoints\patients.py # GET /{patient_id}/abha-card & POST /verify-abha-qr endpoints
├── backend\tests\
│   └── test_abha_card.py          # 5 test suites covering signing, verification, tampering, & cross-tenant security
└── frontend\src\
    ├── lib\
    │   ├── qr.ts                  # Pure vector SVG & PNG DataURL engine using qrcode with ABDM encoders
    │   └── api.ts                 # Typed client methods getPatientAbhaCard & verifyAbhaQr with payload models
    ├── components\patient\
    │   ├── DigitalAbhaCard.tsx    # Dual-sided CR80 card with 3D CSS flip, tricolor banner, and vector QR
    │   ├── AbhaCardExportModal.tsx# ID-1 wallet print sheet (85.6mm x 54mm), SVG download, & JSON certificate
    │   ├── AbhaQrVerificationModal.tsx # Scanner simulator, signature verifier, and tamper test tool
    │   └── PatientOverviewTab.tsx # Integrated DigitalAbhaCard with action triggers
    └── app\patient\page.tsx       # Live state orchestration, card fetch effect, and modal lifecycle
```

---

## 3. Cryptographic Verification & Security Protocol

### 3.1 Claims Normalization & HMAC-SHA256 Signature
To guarantee zero-knowledge offline verifiability, the backend service canonicalizes demographic attributes into a strictly ordered ABDM payload:
- `hidn`: 14-digit unhyphenated ABHA ID (e.g. `91847210924821`).
- `hid`: Registered health handle (`arun.patel@abdm`).
- `name`: Cardholder legal name.
- `gender`: ISO gender abbreviation (`M`, `F`, `O`).
- `dob`: ISO date of birth (`YYYY-MM-DD`).
- `state_name`: Registered state node.
- `dist_name`: Registered district jurisdiction.
- `mobile`: Masked mobile number (`+91 98*** **421`).
- `blood_group`: ABO/Rh code (e.g. `O+`).
- `issue_date`: UTC ISO timestamp.

The canonical string is signed with HMAC-SHA256 using the platform's root secret:
$$\text{Signature} = \text{HMAC-SHA256}(K_{\text{ABDM\_ROOT}}, \text{Payload}_{\text{canonical}})$$

### 3.2 Timing-Safe Verification
To prevent timing side-channel attacks during signature verification, `verify_abha_qr_payload` strictly employs Python's `hmac.compare_digest`:
```python
is_authentic = hmac.compare_digest(expected_signature, claims["signature"])
```
Any modification to the demographic payload (e.g., altering the cardholder's name or ABHA ID) produces an immediate cryptographic rejection.

---

## 4. Cal.com Design & UX Implementation

The frontend components strictly follow the **Cal.com design system** (`calcom-design-system` skill):
- **Card Surface & Canvas:** Crisp pure white (`#ffffff`) background, soft rounded edges (`rounded-[16px]`), subtle borders (`border-[#e5e7eb]`), and near-black primary CTAs (`#111111`).
- **3D Interactive Card Flip:** Smooth CSS 3D transform (`perspective: 1200px`, `transformStyle: preserve-3d`, `duration-700 ease-out`) flipping between the official ABDM Front Face and the Emergency Medical Profile Back Face.
- **National Tricolor Accent:** Elegant saffron (`#FF9933`), white (`#FFFFFF`), and green (`#138808`) accent bar along the card's top edge.
- **Pure Vector QR Code:** Rendered dynamically at runtime via `generateQrSvgString` with zero loss in resolution or pixelation at any zoom level.
- **ID-1 Wallet Print Format:** Embedded `@media print` stylesheet formatting front and back cards side-by-side with exact CR80 credit-card dimensions (85.60mm × 53.98mm) and cut lines for lamination.
- **Interactive Tamper Testing:** Built-in security auditor tool that intentionally mutates the cardholder name while preserving the original signature, demonstrating ABDM anti-forgery protection in real time.

---

## 5. Verification & Test Metrics

1. **Backend Automated Tests:**
   - Ran `backend/.venv/Scripts/pytest.exe tests/test_abha_card.py -v`:
     - `test_generate_abha_card_success`: **PASSED**
     - `test_verify_abha_qr_valid_payload`: **PASSED**
     - `test_verify_abha_qr_detects_tampering`: **PASSED**
     - `test_verify_abha_qr_malformed_input`: **PASSED**
     - `test_patient_cross_tenant_abha_card_isolation`: **PASSED**
   - Full test suite: **233 / 233 tests passed (100% green)** across 39 test files in 63.69s.
2. **Frontend Type Check:**
   - Ran `npx tsc --noEmit` in `frontend/`: **0 errors**.
3. **Frontend Production Build:**
   - Ran `npm run build` in `frontend/`:
     - Next.js 15.5.25 compiled successfully in 60s.
     - **11/11 static pages generated with 0 errors**.
     - Route `/patient`: 30.7 kB.
4. **Git Discipline:**
   - Exactly **8 micro-commits** authored under `Suryansh Swarn <suryanshswarn@gmail.com>`.
   - **Zero release tags created today** (Alpha tag `v0.2.0-alpha.w7` reserved for Day 35 Week 7 close).
