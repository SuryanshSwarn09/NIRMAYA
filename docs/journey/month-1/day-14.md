# Day 14: Frontend Auth Integration, Session Persistence & Clinical Portals

**Date:** September 24, 2026  
**Milestone:** 03-04 (Month 1, Week 3, Day 4)  
**Author:** Suryansh Swarn  
**Status:** Completed  

---

## 1. Overview & Architectural Goals

Day 14 bridges the backend Supabase authentication and Role-Based Access Control (RBAC) security layer (implemented on Days 11–13) directly into the Next.js 15 App Router frontend. 

The primary goals accomplished today:
1. **Frontend Session State & Cookie Synchronization (`AuthContext.tsx`):**
   - Implemented `AuthContext` and custom `useAuth()` hook managing JWT tokens, active persona roles (`PATIENT`, `DOCTOR`, `LAB`, `ADMIN`), and user profile metadata.
   - Synchronized credentials between `localStorage` (for instant client-side retrieval) and standard HTTP cookies (`nirmaya_token`, `nirmaya_role`) with `SameSite=Lax` for Next.js server-side edge middleware evaluation.
2. **Next.js Edge Route Protection Middleware (`src/middleware.ts`):**
   - Guards clinical workspaces (`/patient/*`, `/doctor/*`, `/lab/*`) against unauthenticated visitors, automatically redirecting to `/login?returnUrl=...`.
   - Prevents unauthorized cross-role boundaries (e.g. patients attempting to access doctor workspaces are gracefully redirected to the patient vault).
3. **Cal.com-Styled Authentication Pages:**
   - **`/login`:** Pure white canvas with `#111111` primary CTAs, email/password form, and **One-Click Clinical Demo Personas** enabling instant sandbox verification for Dr. Ananya Sharma (Doctor), Arun Patel (Patient), Apollo Diagnostics (Lab), and Root Admin.
   - **`/register`:** Cal.com-styled onboarding experience with `NavPillGroup` role selector and ABHA 14-digit identifier simulation.
4. **Scaffolded Clinical Portals:**
   - **`/patient` (Patient Health Vault):** Official Ayushman Bharat Health ID Card display, QR verification code, active consent delegation manager with time-bound countdown, and longitudinal clinical history timeline.
   - **`/doctor` (Provider EMR Console):** Verified Healthcare Professional Registry (HPR) badge, daily consultation queue, and structured clinical encounter note editor producing standard HL7 FHIR R4 `MedicationRequest` JSON bundles.
5. **Dynamic Navigation Session State:**
   - Integrated `Navbar.tsx` with `useAuth()`, dynamically presenting user avatars (36px circular Cal.com avatar with initials), active role pills, and sign-out controls when logged in.

---

## 2. Technical Architecture & Data Flow

```
[User Browser]
      │
      ▼
[Next.js 15 App Router] ── (src/middleware.ts) ──► Validates Cookie (nirmaya_token)
      │                                                │
      ├─► /login (Demo Personas / Credentials)        │ (If valid)
      ├─► /register (ABHA ID Role Selector)            ▼
      ├─► /patient (ABHA Health Card & Timeline)  ◄── Allowed
      └─► /doctor (HPR EMR & FHIR MedicationRequest)
      │
      ▼
[Frontend API Client] (src/lib/api.ts)
      │ Automatic Bearer Token Injection
      ▼
[FastAPI Backend Engine] (/api/v1/auth/*, /api/v1/patients/*, /api/v1/doctors/*)
      │ JWT Signature & Role Claims Validation
      ▼
[PostgreSQL 16 & Supabase Auth Simulation]
```

---

## 3. Micro-Commit Journal (10+ Commits Standard)

Following the disciplined pacing protocol, Day 14 was implemented across 13 atomic micro-commits:

1. `5fe19c6: feat(auth): create frontend AuthContext and useAuth session provider`
2. `b5fdad6: feat(api): wire auth token injection and user endpoints in api client`
3. `2f50c6d: feat(auth): implement next.js route middleware for protected clinical routes`
4. `7e4a0bd: feat(ui): design cal.com styled login page with credentials form and demo personas`
5. `e0014b0: feat(ui): build cal.com styled abha registration page with role selector`
6. `2f08864: feat(portal): scaffold patient vault portal with abha card and timeline`
7. `5541255: feat(portal): scaffold provider emr console with hpr badge and prescription flow`
8. `2449b13: feat(layout): connect navbar to auth context with dynamic user session state`
9. `5c0ff79: feat(layout): wrap app shell in auth provider`
10. `test(frontend): verify client auth lifecycle and build with turbopack`
11. `docs(journey): log day 14 frontend auth and session persistence deliverables`
12. `docs(changelog): record milestone 03-04 frontend auth integration`
13. `chore(release): batch push day 14 deliverables to origin main`

---

## 4. Verification & Testing

- **Next.js 15 Turbopack Build:** Verified compilation of all static routes (`/`, `/login`, `/register`, `/patient`, `/doctor`) with 0 errors.
- **Backend Test Suite:** Executed `pytest backend/tests -q` with all **109 tests passing (100%)**.
- **System Doctor Diagnostic:** Executed `python scripts/doctor.py` passing **8/8 checks**.
- **Tag Discipline:** Zero daily tags created; active tag remains `v0.1.0-alpha.w2` (weekly release tag `v0.1.0-alpha.w3` scheduled for Day 15 close).
