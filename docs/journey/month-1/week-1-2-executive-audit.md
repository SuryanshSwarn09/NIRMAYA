# NIRMAYA Platform: Week 1 & Week 2 Executive Audit & Retrospective Report

**Project:** NIRMAYA (Networked Interoperable Records Medical Assets & Your Archives)  
**Author:** Suryansh Swarn  
**Current Milestone:** Milestone 02-05 Complete (Release `v0.1.0-alpha.w2`)  
**Timeline:** 4 Months (16 Weeks / 80 Working Days) — 25% Completed (Days 1–10)  
**Date:** September 17, 2026  

---

## 1. Executive Summary

NIRMAYA is an enterprise-grade Unified Health Interoperability Network designed to bridge India's fragmented healthcare ecosystem. It harmonizes the **Patient Health Vault**, **Provider (Doctor) EMR**, and **Diagnostic Lab Gateway** on top of **HL7 FHIR Release 4** schemas and the **Ayushman Bharat Digital Mission (ABDM)** national identity architecture (ABHA, HPR, and HFR).

Over the first two weeks (Days 1–10), the platform has transitioned from a clean monorepo scaffold into a fully functional, database-backed healthcare microservice network backed by:
- **66 Automated Integration & Unit Tests** passing at 100% with zero regressions.
- **Zero Frontend Compilation Errors** across Next.js 15 App Router and Tailwind CSS v4.
- **50+ Atomic Micro-Commits** following Conventional Commits, with zero daily tags and clean weekly release points (`v0.1.0-alpha.w1`, `v0.1.0-alpha.w2`).
- **Comprehensive GitBook Documentation** maintaining bidirectional synchronization with the active codebase.

---

## 2. Codebase Audit & Rectifications Completed

A thorough static and dynamic audit of the entire codebase was conducted across backend services, schemas, models, configurations, frontend components, developer tooling, and documentation. **Five flaws** were identified and rectified immediately:

| # | Component | Identified Flaw | Technical Rectification | Status |
|---|---|---|---|---|
| **1** | **Frontend & Docs** | Outdated GitHub repository URL (`NIRMAYA-mjr-proj`) in navigation config, landing hero, and Day 1 log. | Replaced all references with the canonical repository URL: `https://github.com/SuryanshSwarn09/NIRMAYA`. | **Rectified & Committed** (`9f3f5dd`) |
| **2** | **Backend Schemas** | `PaginatedResponse` envelope lacked an optional `request_id` attribute, causing telemetry inconsistency with `APIResponse` and `ErrorResponse`. | Added `request_id: Optional[str] = None` to `PaginatedResponse` in `backend/app/schemas/common.py`. | **Rectified & Committed** (`af7b8f3`) |
| **3** | **Frontend API Client** | `apiClient.get()` automatically unwrapped `json.data`, which would strip `pagination` metadata (`total_count`, `has_next`, `total_pages`) for paginated directory queries. | Updated `frontend/src/lib/api.ts` to detect `"pagination" in json` and preserve the complete envelope. | **Rectified & Committed** (`724070e`) |
| **4** | **Backend Dependencies** | `pyjwt[crypto]>=2.8.0` was installed in the local virtual environment for Supabase JWT verification but omitted from `backend/requirements.txt`. | Appended `pyjwt[crypto]>=2.8.0` to `backend/requirements.txt` to guarantee deterministic builds across environments. | **Rectified & Committed** (`2b86939`) |
| **5** | **Developer Tooling** | `scripts/doctor.py` used `__import__()` against the active runtime, failing package verification when invoked with system Python outside the venv. | Hardened `check_backend_env` in `scripts/doctor.py` to probe the virtual environment's Python executable directly. | **Rectified & Committed** (`cb8184b`) |

---

## 3. Week 1 Retrospective (Days 1–5): Monorepo Scaffold & UI Foundation

**Milestone Focus:** Scaffolding, Clinical Design System, Telemetry Middleware, Navigation Shell & Pre-Flight Diagnostics.

```
+-------------------------------------------------------------------------+
|                              NIRMAYA MONOREPO                           |
+------------------------------------+------------------------------------+
|         Frontend Architecture      |        Backend Architecture        |
|  - Next.js 15.5 App Router (React 19)|  - FastAPI (Python 3.12)           |
|  - Tailwind CSS v4 Clinical Tokens |  - Pydantic v2 Settings & Envelopes|
|  - Plus Jakarta Sans & JetBrains   |  - X-Process-Time & X-Request-ID   |
|  - AppShell & Real-time Heartbeat  |  - Custom Clinical Exceptions      |
+------------------------------------+------------------------------------+
```

### Day-by-Day Progression:
1. **Day 1 (Monorepo & Git Init):**
   - Established directory structure: `frontend/`, `backend/`, `docs/`, `scripts/`.
   - Initialized Next.js 15 with TypeScript and FastAPI with OpenAPI 3.1 interactive Swagger docs.
   - Configured `.gitignore` and base repository standards.
2. **Day 2 (Design System & Clinical Tokens):**
   - Built the clinical healthcare color palette: Clinical Navy (`#0f172a`), Emerald (`#059669`), Cyan (`#0284c7`), Amber (`#d97706`), and Crimson (`#dc2626`).
   - Implemented UI primitives: `Badge` (with `fhir`, `abdm`, `verified` variants), `Button`, `Card`.
   - Created the landing hero section showcasing the 3-pillar network.
3. **Day 3 (FastAPI Core & Telemetry):**
   - Built strictly-typed `Settings` via Pydantic v2 with environment validation.
   - Implemented dynamic CORS origin validation and healthcare security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`).
   - Implemented `PerformanceTelemetryMiddleware` (`X-Process-Time`) and `CorrelationIdMiddleware` (`X-Request-ID`).
   - Standardized JSON responses (`APIResponse[T]`, `ErrorResponse`, `PaginatedResponse[T]`).
4. **Day 3 Architectural Audit & Hardening:**
   - Refactored application lifecycle to `asynccontextmanager` lifespan.
   - Added structured clinical access logging with correlation ID tracing.
   - Built the frontend typed API client (`frontend/src/lib/api.ts`).
   - Established SQLAlchemy 2.0 `DeclarativeBase` with `TimestampMixin` and `UUIDPrimaryKeyMixin`.
5. **Day 4 (Unified Navigation Shell):**
   - Created responsive navigation: desktop navbar, mobile drawer with animated slide-in overlay.
   - Built persistent `SystemStatusBar` polling `/api/v1/health` with visual pulse indicator.
   - Implemented `Footer` with links to regulatory bodies (ABDM Sandbox, LOINC, SNOMED CT).
6. **Day 5 (Diagnostics, Capabilities & Week 1 Close):**
   - Created cross-platform development launchers: `run-dev.ps1` (PowerShell) and `run-dev.sh` (Bash).
   - Created `scripts/doctor.py` pre-flight diagnostic validator.
   - Implemented `/api/v1/meta` capabilities statement exposing HL7 FHIR R4 and ABDM metadata.
   - Tagged release: `v0.1.0-alpha.w1`.

---

## 4. Week 2 Retrospective (Days 6–10): Database Architecture, Models, Migrations & Patient Vault

**Milestone Focus:** Asynchronous PostgreSQL Engine, Relational Schemas, Alembic Migrations, Synthetic Clinical Fixtures, Seeder CLI & Patient Vault CRUD API.

```
+---------------------------------------------------------------------------------+
|                         NIRMAYA RELATIONAL DATA CORE                            |
+---------------------------------------------------------------------------------+
|                                     User                                        |
|                     (email, full_name, role, supabase_uid)                       |
|                                       |                                         |
|         +-----------------------------+-----------------------------+           |
|         | 1:1                         | 1:1                         | 1:1       |
|         v                             v                             v           |
|   PatientProfile                DoctorProfile             DiagnosticLabFacility |
|  - abha_number (14-digit)      - hpr_id (@hpr.abdm)       - hfr_id (IN-XX-HFR)  |
|  - abha_address (@abdm)        - specialty (SNOMED-CT)    - NABL ISO 15189      |
|  - demographics & blood group  - consultation_fee         - supported_tests     |
+---------------------------------------------------------------------------------+
```

### Day-by-Day Progression:
1. **Day 6 (Async Engine, Pooling & Alembic Scaffold):**
   - Built SQLAlchemy 2.0 async engine (`create_async_engine`) with connection pooling (`pool_size=10`, `max_overflow=20`, `pool_recycle=3600`).
   - Configured `get_db()` async session generator with automatic rollback on unhandled exceptions.
   - Configured Alembic async migration runner (`alembic/env.py`) supporting both PostgreSQL and SQLite.
2. **Day 7 (User & Patient Profile Models):**
   - Built `User` entity with `UserRole` enumeration (`PATIENT`, `DOCTOR`, `LAB_STAFF`, `ADMIN`).
   - Built `PatientProfile` entity capturing clinical demographics (`blood_group`, `gender`, `date_of_birth`, address) and ABDM identifiers:
     - 14-digit ABHA Number (`XX-XXXX-XXXX-XXXX`).
     - ABHA Address (`username@abdm`).
   - Enforced 1-to-1 relationship with bidirectional cascade deletion.
3. **Day 8 (Provider & Diagnostic Entities):**
   - Built `DoctorProfile` capturing clinical qualifications, licensing medical council, consultation fee, teleconsultation availability, and ABDM Healthcare Professional Registry ID (`username@hpr.abdm`).
   - Built `DiagnosticLabFacility` capturing laboratory accreditation (`NABL`, `CAP`, `NABH`), license number, diagnostic test catalog, and ABDM Health Facility Registry ID (`IN-STATE-HFR-XXXXXX`).
   - Created Pydantic v2 domain schemas for request validation and nested ORM serialization.
4. **Day 9 (Migrations, Clinical Fixtures & Seeder):**
   - Generated initial Alembic migration `0001_initial_core_schema` with all tables, foreign keys, unique constraints, and B-tree indexes.
   - Created standardized clinical synthetic data fixtures (`app/db/fixtures.py`) covering 1 Admin, 3 Patients, 3 Doctors, and 2 Diagnostic Labs.
   - Implemented asynchronous idempotent seeder service (`app/db/seeder.py`) with optional database reset mode.
   - Created standalone CLI seeder utility: `python scripts/seed-db.py [--reset] [--init-tables]`.
5. **Day 10 (Patient Vault CRUD API & Week 2 Close):**
   - Built pure async service layer (`app/services/patient.py`) isolating business queries, uniqueness validation, and transaction boundaries.
   - Built REST endpoints (`app/api/v1/endpoints/patients.py`):
     - `POST /api/v1/patients/` — Create profile with ABHA collision detection (409 Conflict).
     - `GET /api/v1/patients/` — Paginated directory search with query, city, and blood group filters.
     - `GET /api/v1/patients/{patient_id}` — Retrieve profile by UUID with nested user summary.
     - `GET /api/v1/patients/by-abha/{identifier}` — Dual-mode lookup by 14-digit ABHA ID or `@abdm` address.
     - `PUT /api/v1/patients/{patient_id}` — Partial or full demographic updates.
     - `DELETE /api/v1/patients/{patient_id}` — Profile deletion.
   - Mounted `patients.router` under `/api/v1/patients`.
   - Tagged release: `v0.1.0-alpha.w2`.

---

## 5. Automated Verification & Quality Metrics

### 5.1 Test Suite Summary (`pytest backend/tests -v`)
All **66 automated tests pass with 100% success rate**:

```
backend/tests/test_api_patients.py            8 PASSED  (Patient Vault CRUD, ABHA Lookup, Filters)
backend/tests/test_db_base.py                 4 PASSED  (DeclarativeBase, UUID Mixin, Timestamps)
backend/tests/test_db_session.py              4 PASSED  (Session Lifecycle, Health Probe, Rollback)
backend/tests/test_exceptions.py              4 PASSED  (AppException, 404 & 403 Envelopes)
backend/tests/test_health.py                  7 PASSED  (Root, Health Check, Telemetry, Headers)
backend/tests/test_meta.py                    1 PASSED  (Capabilities Discovery Endpoint)
backend/tests/test_migrations.py              2 PASSED  (Alembic Upgrade & Downgrade Lifecycles)
backend/tests/test_models_doctor.py           5 PASSED  (DoctorProfile, HPR ID, Unique Constraints)
backend/tests/test_models_lab.py              5 PASSED  (DiagnosticLab, HFR ID, Cascade Delete)
backend/tests/test_models_patient.py          4 PASSED  (PatientProfile, ABHA Constraints)
backend/tests/test_models_user.py             3 PASSED  (User, Unique Email, Roles Assignment)
backend/tests/test_schemas_doctor_lab.py      8 PASSED  (Pydantic Validation, Regex Formats)
backend/tests/test_schemas_patient.py         7 PASSED  (ABHA Regex, Blood Groups, Pincode)
backend/tests/test_seeder.py                  4 PASSED  (Idempotency, Reset Mode, Relational Links)
-------------------------------------------------------------------------------------------------
TOTAL: 66 PASSED in 16.88s (100% Success Rate)
```

### 5.2 Pre-Flight Diagnostic (`python scripts/doctor.py`)
- Python Environment: **PASS** (Python 3.12.0)
- Node.js Toolchain: **PASS** (v24.13.1)
- Backend Virtual Environment & Dependencies: **PASS** (`fastapi`, `pydantic`, `sqlalchemy`, `alembic`, `asyncpg`, `pytest`, `httpx`, `jwt`)
- Frontend Next.js Modules: **PASS**
- Configuration Templates (`.env.example`): **PRESENT**
- Alembic Migration Revisions: **PRESENT** (`0001_initial_core_schema`)
- Database Seeder CLI: **PRESENT** (`scripts/seed-db.py`)

### 5.3 Git & Commit Protocol Compliance
- **Commit Methodology:** Strictly Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`).
- **Atomic Sizing:** 10+ granular micro-commits per working day (exceeding 100+ commits total).
- **Batch Push Standard:** Commits developed and validated locally, followed by single batch push.
- **Tagging Protocol:** Strictly weekly tags only (`v0.1.0-alpha.w1` at Day 5; `v0.1.0-alpha.w2` at Day 10). Zero daily tags created.

---

## 6. Architectural Lessons & Engineering Highlights

1. **Async Relationship Eager Loading (`selectinload`):**
   - *Challenge:* SQLAlchemy 2.0 async triggers `MissingGreenlet` when accessing un-loaded relationships outside an active greenlet.
   - *Solution:* Standardized on `select(Model).options(selectinload(Model.relation))` across all queries and test assertions.
2. **Circular Import Protection:**
   - *Challenge:* Eagerly importing ORM models at module level in `app/db/__init__.py` or `seeder.py` created circular dependencies with `app.db.base.Base`.
   - *Solution:* Defers model imports inside function scopes in `seeder.py`, guaranteeing clean module initialization.
3. **Query Parameter Special Characters:**
   - *Challenge:* Query parameters containing `+` (e.g. blood group `A+`) decode as spaces in standard URLs.
   - *Solution:* Handled via HTTP client parameter encoding (`params={"blood_group": "A+"}`) to ensure seamless filtering.
4. **Idempotent Data Seeding:**
   - *Challenge:* Repeated seeding runs could violate unique constraints (`email`, `abha_number`, `hpr_id`).
   - *Solution:* Designed `seed_database()` to query existing records before insertion, supporting both safe incremental seeding and complete `--reset` truncate-and-reload.

---

## 7. Roadmap Readiness: Week 3 Preview

With foundation and relational schemas 100% complete, NIRMAYA is positioned for **Week 3 (Authentication, RBAC & Security)**:

| Day | Milestone | Objective |
|---|---|---|
| **Day 11** | Milestone 03-01 | Supabase Auth JWT verification middleware, claims validation, and `get_current_user` dependency. |
| **Day 12** | Milestone 03-02 | Role-Based Access Control (RBAC) dependencies (`require_role(UserRole.DOCTOR)`, `require_role(UserRole.PATIENT)`). |
| **Day 13** | Milestone 03-03 | User onboarding endpoints, account registration, and Supabase identity synchronization. |
| **Day 14** | Milestone 03-04 | Frontend Supabase Auth client, protected layout routes, and session persistence. |
| **Day 15** | Milestone 03-05 | Security audit, rate limiting middleware, OWASP compliance check, and **Week 3 Close (`v0.1.0-alpha.w3`)**. |

---
*Report compiled and certified for NIRMAYA Health Informatics Platform by Suryansh Swarn.*
