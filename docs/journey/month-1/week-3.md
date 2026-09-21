# Week 3: Authentication, Supabase Integration & RBAC Security

**Milestone Target:** Implement enterprise-grade authentication using Supabase Auth JWT verification, role-based access control (RBAC), multi-role account onboarding, and security hardening.

---

## Daily Schedule & Commit Breakdown

| Day | Focus Area | Key Deliverables | Status |
|---|---|---|---|
| **Day 11 (Mon)** | Supabase Auth & JWT Middleware | PyJWT validation, claims extraction, `get_current_user` dependency, `/auth/me` & `/auth/verify` endpoints | **Completed** |
| **Day 12 (Tue)** | Role-Based Access Control (RBAC) | Security dependencies (`require_role`), doctor/patient authorization guards, 403 error enforcement | *Next* |
| **Day 13 (Wed)** | User Registration & Profile Sync | User onboarding API, Supabase Auth webhook handler, clinical profile initialization | *Scheduled* |
| **Day 14 (Thu)** | Frontend Auth Integration | Supabase Auth client, protected route middleware, session persistence & login state | *Scheduled* |
| **Day 15 (Fri)** | Security Audit & Week 3 Close | Rate limiting middleware, OWASP compliance verification, test suites & release `v0.1.0-alpha.w3` | *Scheduled* |

---

## Week 3 Architecture Highlights

- **Decoupled Identity Provider:** Supabase Auth manages user credentials and OAuth handshakes while NIRMAYA validates cryptographically signed JWT tokens on every clinical request.
- **FastAPI Dependency Injection:** Security guards (`get_current_user`, `get_current_active_user`, `require_role`) guarantee that clinical endpoints enforce role boundaries before executing business logic.
- **Standards-Compliant Token Envelopes:** Standard HTTP 401 Unauthorized responses accompanied by `WWW-Authenticate: Bearer` challenge headers and machine-readable error codes (`TOKEN_EXPIRED`, `INVALID_TOKEN`, `AUTHENTICATION_REQUIRED`).
