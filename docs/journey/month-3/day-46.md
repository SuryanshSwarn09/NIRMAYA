# Day 46: Milestone 10-01 - Unified DigiLocker & Aadhaar OTP Passwordless Patient Gateway

**Milestone:** 10-01 (Month 3, Week 10)  
**Author:** Suryansh Swarn (`suryanshswarn@gmail.com`)  
**Status:** Completed & Certified  

---

## 1. Executive Summary

Day 46 transforms the citizen authentication experience in the NIRMAYA national digital health platform from traditional username/password credentials into an **authenticated, passwordless Government e-KYC gateway**.

By uniting our cryptographic DigiLocker OAuth 2.0 PKCE engine and Direct Aadhaar Demographic OTP services into a single entry door, patients can sign in or auto-register in under 15 seconds with zero manual typing.

### Three Strategic Architectural Enhancements Delivered:
1. **Suggestion 1 (Mismatched SIM Fallback):** Dual-channel authentication with dedicated active mobile fallback for patients whose current phone number differs from their older Aadhaar-registered SIM card.
2. **Suggestion 2 (Session Longevity):** Configurable 30-day extended JWT session token (`remember_me: true`, 2,592,000 seconds) so citizens are not subjected to daily OTP fatigue on personal devices.
3. **Suggestion 3 (Automatic 14-Digit ABHA Minting on First Login):** New citizens logging in via DigiLocker or Aadhaar OTP have their `User` and `PatientProfile` created automatically, their verified legal demographics populated, their official 14-digit ABHA Number (`91-XXXX-XXXX-XXXX`) minted with Verhoeff mathematical verification, and an initial `@abdm` handle reserved—all in a single atomic transaction.

---

## 2. Technical Architecture & Endpoints

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│              UNIFIED PASSWORDLESS PATIENT AUTHENTICATION GATEWAY                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   [ Channel A: DigiLocker OAuth PKCE ]   [ Channel B: Direct Aadhaar OTP ]      │
│                     \                                 /                         │
│                      ▼                               ▼                          │
│               [ UIDAI e-KYC Demographic Claims Extraction ]                     │
│               - Legal Name, Gender, DOB, Address, Masked UID                    │
│                                      │                                          │
│                                      ▼                                          │
│                    [ Patient Account Resolution Engine ]                        │
│                                      │                                          │
│             ┌────────────────────────┴────────────────────────┐                 │
│             ▼                                                 ▼                 │
│      [ Existing Patient ]                              [ New Patient ]          │
│   - Fetch profile                               - Auto-create User              │
│   - Sync updated claims                         - Auto-create PatientProfile    │
│                                                 - Auto-mint 14-Digit ABHA       │
│                                                 - Auto-reserve @abdm Handle     │
│             └────────────────────────┬────────────────────────┘                 │
│                                      │                                          │
│                                      ▼                                          │
│               [ 30-Day Extended JWT Session Generation ]                        │
│               - Access Token + Refresh Token (30-day TTL)                       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Backend Components
- **Schemas (`backend/app/schemas/patient_auth.py`):**
  - `PatientUnifiedAuthRequest`: Ingests identity source (`"digilocker"`, `"aadhaar_otp"`), certified demographics (name, DOB, gender, masked Aadhaar, structured address), and `remember_me` boolean.
  - `PatientMobileFallbackLoginRequest`: Ingests 10-digit mobile number, OTP, optional ABHA identifier, and `remember_me`.
  - `PatientUnifiedAuthResponse`: Returns JWT `access_token`, `expires_in_seconds`, `is_new_user`, user demographic summary, and minted ABHA Number/address.
- **Service Layer (`backend/app/services/patient_auth.py`):**
  - `authenticate_or_register_patient`: Idempotently resolves existing users, commits new profiles, auto-mints 14-digit ABHA numbers, and generates 30-day JWT sessions.
  - `authenticate_mobile_fallback`: Fallback mobile OTP verification engine with ABHA handle resolution.
- **API Endpoints (`backend/app/api/v1/endpoints/patient_auth.py`):**
  - `POST /api/v1/auth/patient/login-or-register`
  - `POST /api/v1/auth/patient/mobile-fallback-login`

---

## 3. Frontend Implementation

- **`PatientPasswordlessAuthCard.tsx` (`frontend/src/components/patient/PatientPasswordlessAuthCard.tsx`):**
  - Cal.com geometric design (`#ffffff` canvas, hairline borders `#e5e7eb`, `rounded-[8px]` containers, `rounded-[6px]` badges).
  - 3-mode tab switcher:
    - **Tab 1: DigiLocker 1-Click:** One-click OAuth PKCE verification with zero manual typing.
    - **Tab 2: Aadhaar OTP:** 12-digit Aadhaar input with auto-formatting, 6-digit OTP verification with 60-second cooldown timer and 10-minute validity.
    - **Tab 3: Mobile Fallback:** Active mobile phone + optional ABHA handle input.
  - "Remember this device for 30 days" session longevity checkbox.
- **Redesigned `/login` & `/register` Pages:**
  - Role portal switcher: `Patient (Citizen)` | `Doctor (Clinician)` | `Lab / Staff`.
  - Seamlessly mounts `PatientPasswordlessAuthCard` when `Patient` is selected, eliminating passwords entirely.
  - Preserves practitioner HPR and staff credential login for clinical consoles.

---

## 4. Verification & Testing Evidence

- **Unit & Integration Test Suite (`backend/tests/test_patient_unified_auth.py`):**
  - `test_new_patient_auto_registration_and_auto_abha`: PASSED (Verhoeff check digit verified on minted ABHA).
  - `test_existing_patient_seamless_login`: PASSED (No duplicate records created).
  - `test_session_longevity_toggle`: PASSED (30 days / 2,592,000s vs 24h / 86,400s).
  - `test_mobile_fallback_authentication`: PASSED (Active mobile verification).
  - `test_mobile_fallback_invalid_otp`: PASSED (401 error rejection).
- **Frontend Verification:**
  - Static typecheck (`npx tsc --noEmit`): **0 errors**.
  - Production build (`npm run build`): **0 errors**, all 13 routes compiled cleanly.
- **Full Backend Regression Suite:** **294 / 294 passed (100% green)**.
