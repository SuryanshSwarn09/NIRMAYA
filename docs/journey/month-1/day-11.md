# Day 11: Authentication, Supabase Auth Integration & JWT Session Middleware

**Date:** September 21, 2026  
**Milestone:** 03-01 (Month 1, Week 3, Day 1)  
**Author:** Suryansh Swarn  
**Status:** Completed  

---

## 1. Overview & Architectural Goals

Day 11 opens **Month 1, Week 3** of the NIRMAYA roadmap, establishing the authentication foundation for the entire platform. Rather than tightly coupling identity storage inside a monolith, NIRMAYA leverages **Supabase Auth** as a dedicated identity provider while verifying signed JSON Web Tokens (JWT) natively within the FastAPI ASGI pipeline.

Key objectives completed today:
1. **PyJWT Integration:** Standards-compliant JWT signature verification supporting symmetric HMAC-SHA256 (`HS256`) and asymmetric keys with strict RFC 7518 key-length validation.
2. **Core Security Utilities (`app/core/security.py`):** Cryptographic helpers for decoding access tokens against candidate keys (`SUPABASE_JWT_SECRET` and fallback `SECRET_KEY`), verifying audience claims (`authenticated`), and catching signature expiration without leaky exceptions.
3. **Pydantic v2 Auth Schemas (`app/schemas/auth.py`):** Typed models for `TokenPayload`, `TokenResponse`, `TokenVerifyRequest`, `TokenVerifyResponse`, and `AuthContext`.
4. **FastAPI Security Dependencies (`app/core/dependencies.py`):**
   - `get_token_payload`: Validates `Authorization: Bearer <token>` header, extracts claims, and parses subject identifiers.
   - `get_current_user`: Resolves the active database `User` entity matching `supabase_uid`, `id`, or `email`, eagerly loading related clinical profiles (`patient_profile`, `doctor_profile`, `lab_facility`) and rejecting deactivated accounts (403 Forbidden).
   - `get_current_active_user`: Enforces account active verification.
   - `get_optional_current_user`: Provides non-blocking identity resolution for public endpoints.
5. **Authentication Endpoints (`app/api/v1/endpoints/auth.py`):**
   - `GET /api/v1/auth/me` — Protected endpoint returning the authenticated caller's identity and assigned clinical roles.
   - `POST /api/v1/auth/verify` — Stateless token verification and claims inspection.
   - `POST /api/v1/auth/test-token` — Sandbox utility for issuing signed test JWTs in non-production environments.
6. **Automated Testing:** 12 new unit and integration tests covering signature validation, expiration, inactive accounts, and roundtrip verification, bringing the total suite to **78/78 passing tests (100%)**.

---

## 2. Technical Architecture & Data Flow

```
[ Client Request ]
       |  (Authorization: Bearer <token>)
       v
[ CorrelationIdMiddleware ] ---> Generates / propagates X-Request-ID
       |
       v
[ PerformanceTelemetryMiddleware ] ---> Starts timer, injects security headers
       |
       v
[ FastAPI Security Dependency: get_token_payload ]
       |  - Validates HTTP Bearer scheme
       |  - Decodes token via PyJWT (verifies signature, exp, aud)
       |  - Catches ExpiredSignatureError -> 401 TOKEN_EXPIRED
       |  - Catches InvalidSignatureError -> 401 INVALID_SIGNATURE
       v
[ FastAPI Security Dependency: get_current_user ]
       |  - Queries User by supabase_uid / id / email
       |  - Eagerly loads patient_profile, doctor_profile, lab_facility
       |  - Checks user.is_active (raises 403 FORBIDDEN if deactivated)
       v
[ Route Handler: /api/v1/auth/me ]
       |  - Serializes User into APIResponse[UserResponse]
       v
[ Outbound Response ] (HTTP 200 OK with X-Process-Time, X-Request-ID)
```

---

## 3. Micro-Commit Journal (10+ Commits Standard)

Following the disciplined pacing protocol, Day 11 delivered atomic micro-commits locally with concise conventional messages:

| # | Commit Hash | Conventional Message | Scope |
|---|---|---|---|
| **1** | `028a7fa` | `feat(core): configure jwt settings and algorithm defaults` | Added `JWT_ALGORITHM` and `JWT_AUDIENCE` settings in `app/core/config.py`. |
| **2** | `aeef18a` | `feat(core): add authentication exception and 401 error handler` | Created `AuthenticationException` with `WWW-Authenticate: Bearer` challenge header handling. |
| **3** | `4e480ac` | `feat(core): implement jwt encode decode and verification utilities` | Implemented `create_access_token`, `decode_access_token`, and password hashing in `app/core/security.py`. |
| **4** | `0b793e4` | `feat(schemas): add auth token payload and verification schemas` | Created `TokenPayload`, `TokenResponse`, `TokenVerifyRequest`, and `AuthContext` in `app/schemas/auth.py`. |
| **5** | `a210225` | `feat(core): implement get current user fastapi security dependencies` | Built `get_token_payload`, `get_current_user`, and `get_optional_current_user` in `app/core/dependencies.py`. |
| **6** | `8c26930` | `feat(api): create auth me and token verification endpoints` | Implemented `GET /auth/me`, `POST /auth/verify`, and `POST /auth/test-token` in `app/api/v1/endpoints/auth.py`. |
| **7** | `6f230af` | `feat(api): wire auth router into api v1 router` | Mounted `auth.router` with prefix `"/auth"` under `/api/v1` in `app/api/v1/router.py`. |
| **8** | `2d67bc4` | `test(core): add unit tests for jwt signing decoding and expiration` | Added 6 unit tests in `backend/tests/test_auth_jwt.py` covering token roundtrip, expiry, tampering, and prefix stripping. |
| **9** | `19a85a9` | `test(api): add integration tests for auth endpoints and security headers` | Added 6 integration tests in `backend/tests/test_api_auth.py` covering `/auth/me`, 401 challenges, inactive accounts, and test tokens. |
| **10** | *Pending* | `docs(journey): log day 11 deliverables and week 3 auth roadmap` | Documented Week 3 schedule, Day 11 architecture, and updated GitBook `SUMMARY.md`. |
| **11** | *Pending* | `docs(changelog): record milestone 03-01 auth and jwt middleware` | Appended Milestone 03-01 deliverables to `docs/CHANGELOG.md`. |

---

## 4. Test Verification & Coverage

Running the full pytest test suite verified **78/78 tests passing (100%)**:

```text
backend\tests\test_api_auth.py::test_get_me_success PASSED               [  1%]
backend\tests\test_api_auth.py::test_get_me_missing_authorization_header PASSED [  2%]
backend\tests\test_api_auth.py::test_get_me_invalid_token PASSED         [  3%]
backend\tests\test_api_auth.py::test_get_me_inactive_user PASSED         [  5%]
backend\tests\test_api_auth.py::test_verify_token_endpoint PASSED        [  6%]
backend\tests\test_api_auth.py::test_test_token_generation_and_me_roundtrip PASSED [  7%]
backend\tests\test_api_patients.py (8 tests) PASSED                      [ 17%]
backend\tests\test_auth_jwt.py (6 tests) PASSED                          [ 25%]
backend\tests\test_db_base.py (4 tests) PASSED                           [ 30%]
backend\tests\test_db_session.py (4 tests) PASSED                        [ 35%]
backend\tests\test_exceptions.py (4 tests) PASSED                        [ 41%]
backend\tests\test_health.py (7 tests) PASSED                            [ 50%]
backend\tests\test_meta.py (1 test) PASSED                               [ 51%]
backend\tests\test_migrations.py (2 tests) PASSED                        [ 53%]
backend\tests\test_models_doctor.py (5 tests) PASSED                     [ 60%]
backend\tests\test_models_lab.py (5 tests) PASSED                        [ 66%]
backend\tests\test_models_patient.py (4 tests) PASSED                     [ 71%]
backend\tests\test_models_user.py (3 tests) PASSED                        [ 75%]
backend\tests\test_schemas_doctor_lab.py (8 tests) PASSED                 [ 85%]
backend\tests\test_schemas_patient.py (7 tests) PASSED                    [ 94%]
backend\tests\test_seeder.py (4 tests) PASSED                            [100%]

============================= 78 passed in 25.15s =============================
```

---

## 5. Next Steps: Day 12 Preview

With JWT token validation and the `get_current_user` security dependency established, Day 12 will implement **Role-Based Access Control (RBAC)**:
- `require_role(allowed_roles: List[UserRole])` dependency factory.
- Role-specific access guards for Patient Vault (`UserRole.PATIENT`), Provider EMR (`UserRole.DOCTOR`), and Diagnostic Gateway (`UserRole.LAB_STAFF`).
- 403 Forbidden error handling for unauthorized cross-role resource access.
- Unit and integration tests for role boundaries and permission hierarchies.
