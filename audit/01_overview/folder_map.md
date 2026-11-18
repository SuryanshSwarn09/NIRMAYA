# NIRMAYA: Codebase Directory Map & Navigation Guide

**Audit Layer**: `01_overview`  
**Scope**: Structural layout, subsystem boundaries, entry points, and directory navigation for new developers.  
**Citations**: `backend/app/`, `frontend/src/`, `docs/`, `scripts/`, `.gsd/`.

---

## 1. Monorepo Root Directory Layout

```
nirmaya/
├── audit/                  # Principal software audit reports and verification matrices
│   ├── 00_MANIFEST.md      # Full 789-file repository manifest with status
│   ├── PROGRESS.md         # Resumable audit tracker and findings tally
│   └── 01_overview/        # Architecture, stack, build/run, folder map, early security
├── backend/                # FastAPI Python backend subsystem (Port 8000)
│   ├── alembic/            # Alembic database migration scripts (9 revisions)
│   ├── app/                # Core application package
│   │   ├── api/v1/         # Route handlers and API v1 endpoints (59 modules)
│   │   ├── core/           # Security, configuration, dependencies, CORS, middleware
│   │   ├── db/             # SQLAlchemy async engine, sessionmaker, fixtures, seeder
│   │   ├── fhir/           # HL7 FHIR R4 schemas, transformers, NRCES validators
│   │   ├── models/         # SQLAlchemy ORM entity models
│   │   ├── schemas/        # Pydantic v2 request/response validation models
│   │   └── services/       # Domain business logic, ABDM bridges, Fidelius crypto
│   ├── tests/              # Automated test suite (98 test files; pytest-asyncio)
│   ├── Dockerfile          # Multi-stage hardened Alpine container definition
│   └── requirements.txt    # Python backend dependencies
├── frontend/               # Next.js 15 App Router frontend subsystem (Port 3000)
│   ├── public/             # Static public assets (icons, brand logos, national emblem)
│   ├── src/
│   │   ├── app/            # Next.js 15 App Router pages and route handlers
│   │   ├── components/     # Modular React 19 UI components
│   │   │   ├── clinical/   # Clinician consultation pad, PACS viewer, admin telemetry
│   │   │   ├── common/     # National emblem, BrandLogo
│   │   │   ├── gateway/    # Universal National Gateway switcher
│   │   │   ├── layout/     # AppShell, Navbar, Footer, AccessibilityBar
│   │   │   ├── patient/    # Patient vault, ABHA cards, DigiLocker auth, vitals
│   │   │   └── ui/         # Cal.com design system primitive components
│   │   ├── context/        # React context providers (AuthContext, AccessibilityContext)
│   │   ├── hooks/          # Custom hooks (real-time WebSockets, queues)
│   │   ├── lib/            # Typed API client (api.ts), utils, offline queue, i18n
│   │   └── middleware.ts   # Edge authentication guard & 4-quadrant role router
│   ├── Dockerfile          # Next.js standalone runner container (<150MB)
│   └── package.json        # Frontend dependencies and npm scripts
├── docs/                   # GitBook documentation, academic manuscripts, daily logs
│   ├── architecture/       # Detailed architectural whitepapers
│   ├── reports/            # Comparative analysis whitepapers and failure case studies
│   ├── journey/            # 4-month (80-day) chronological micro-commit journal
│   └── academic/           # IEEE Transactions LaTeX manuscript and bibliography
├── scripts/                # Cross-platform developer scripts (doctor, seed, run-dev)
├── .agent/ / .agents/      # AI agent skills, prompts, and design system rules
├── .gsd/                   # GSD (Get Stuff Done) roadmap, state tracking, and templates
├── docker-compose.yml      # Multi-container production orchestration specification
├── Caddyfile               # Production edge reverse proxy with TLS and HSTS
└── package.json            # Monorepo root lifecycle scripts (npm run dev/build/test)
```

---

## 2. Key Backend Subsystem Modules (`backend/app/`)

| Path | Purpose & Primary Exports |
| :--- | :--- |
| `backend/app/main.py` | FastAPI entry point, lifespan initialization, middleware binding, route mounting. |
| `backend/app/core/config.py` | `Settings` class managing JWT secrets, database connection URLs, and ABDM flags. |
| `backend/app/core/dependencies.py` | FastAPI dependency injection: token validation, role-based access control. |
| `backend/app/core/cors.py` | Allowed origins resolution and GIGW 3.0 / healthcare security headers. |
| `backend/app/core/middleware.py` | Performance telemetry (`X-Process-Time`), correlation ID (`X-Request-ID`). |
| `backend/app/core/rate_limit.py` | In-memory token-bucket rate limiter mitigating DoS and brute-force attacks. |
| `backend/app/db/session.py` | Async SQLAlchemy 2.0 engine (`create_async_engine`), `AsyncSessionLocal`, `get_db`. |
| `backend/app/db/base.py` | Declarative Base class aggregating all SQLAlchemy ORM models for Alembic. |
| `backend/app/api/v1/router.py` | Master router aggregating 59 discrete endpoint modules under `/api/v1`. |
| `backend/app/fhir/transformers.py` | Bi-directional mapping between database models and HL7 FHIR R4 Resources. |
| `backend/app/fhir/validators.py` | Conformance validation against National Resource Centre for EHR Standards (NRCES). |
| `backend/app/services/abdm_crypto_service.py` | Fidelius-compatible Diffie-Hellman (Curve25519) key exchange & AES-GCM-256 cipher. |
| `backend/app/services/websocket_manager.py` | Real-time Pub/Sub WebSocket message bus with Redis and memory backends. |

---

## 3. Key Frontend Subsystem Modules (`frontend/src/`)

| Path | Purpose & Primary Exports |
| :--- | :--- |
| `frontend/src/middleware.ts` | Next.js Edge middleware enforcing 4-quadrant role boundaries (`/patient`, `/doctor`, etc.). |
| `frontend/src/app/layout.tsx` | Root server layout injecting Google Fonts (Noto Sans, Inter), metadata, and providers. |
| `frontend/src/app/page.tsx` | Sovereign national health network landing portal showcasing ABDM capabilities. |
| `frontend/src/app/doctor/page.tsx` | Clinician consultation workspace, high-velocity 45-second OPD console. |
| `frontend/src/app/patient/page.tsx` | Citizen health vault, longitudinal timeline, condition records, and consent grants. |
| `frontend/src/app/admin/page.tsx` | Territorial governance command center, node telemetry, comparative benchmarks. |
| `frontend/src/components/clinical/` | Prescription pad, PACS/DICOM viewer modal, SOAP notes, container runtime cards. |
| `frontend/src/components/patient/` | Digital ABHA Card, DigiLocker integration card, vitals telemetry charts. |
| `frontend/src/components/layout/` | GIGW 3.0 accessibility toolbar, bilingual language switcher, system status bar. |
| `frontend/src/lib/api.ts` | Monolithic typed API client abstracting all backend REST endpoints and token refresh. |

---

## 4. Documentation & Developer Artifacts (`docs/`)

- `docs/architecture/`: Deep technical whitepapers detailing FHIR schema mapping, ABDM milestone compliance (M1, M2, M3), and cryptographic protocols.
- `docs/journey/`: Structured 4-month daily dev logs (`month-1` through `month-5`), recording architectural decisions, bug remediations, and micro-commits.
- `docs/reports/`: Enterprise engineering monographs, failure case studies (e.g. Vercel deployment post-mortem), and 6-platform comparative benchmark reports.
- `docs/academic/`: IEEE Transactions 2-column capstone manuscript (`nirmaya_ieee_manuscript.tex`) and BibTeX citations for academic defense.
