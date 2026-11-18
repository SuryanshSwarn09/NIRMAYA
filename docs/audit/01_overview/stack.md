# NIRMAYA: Technology Stack & Dependency Matrix

**Audit Layer**: `01_overview`  
**Scope**: Complete runtime, library, database, tooling, and framework inventory.  
**Citations**: `backend/requirements.txt:1-21`, `frontend/package.json:1-32`, `package.json:1-35`, `docker-compose.yml:1-161`, `Caddyfile:1-85`.

---

## 1. Runtimes & Core Platforms

| Subsystem | Technology | Version | Architectural Purpose |
| :--- | :--- | :---: | :--- |
| **Backend Runtime** | Python (CPython) | `3.11.x` / `3.12.x` | Asynchronous ASGI execution engine for FastAPI and clinical services |
| **Frontend Runtime** | Node.js | `>=18.17.0` (v20 LTS recommended) | Build orchestration and Next.js React server runtime |
| **Primary Database** | PostgreSQL | `16-alpine` | Relational ACID storage, row-level locks, transactional appointments |
| **In-Memory Cache / Bus** | Redis | `7-alpine` | Distributed Pub/Sub event bus for multi-node WebSocket broadcasting |
| **Edge Ingress Proxy** | Caddy Server | `2.8-alpine` | Automated Let's Encrypt TLS, HSTS, gzip/zstd, and edge rate-limiting |

---

## 2. Backend Dependency Matrix (`backend/requirements.txt`)

| Package | Version Constraint | Primary Role | Security & Architectural Notes |
| :--- | :---: | :--- | :--- |
| `fastapi` | `>=0.115.0` | Core Web & API Framework | High-throughput asynchronous routing and automatic OpenAPI generation |
| `uvicorn[standard]` | `>=0.30.0` | ASGI Server Implementation | Production event loop running uvloop and httptools |
| `pydantic` | `>=2.8.0` | Data Validation & Schemas | Rust-accelerated validation for HL7 FHIR and clinical request payloads |
| `pydantic-settings` | `>=2.4.0` | Environment Configuration | Strict typed settings parsing from environment variables and `.env` |
| `sqlalchemy[asyncio]` | `>=2.0.32` | ORM & Query Builder | 2.0-style async session management (`AsyncSessionLocal`) |
| `alembic` | `>=1.13.2` | Database Migration Engine | Sequential schema versioning (9 applied migration revisions) |
| `asyncpg` | `>=0.29.0` | PostgreSQL Async Driver | Binary protocol async driver for high concurrency database I/O |
| `psycopg2-binary` | `>=2.9.9` | PostgreSQL Sync Driver | Fallback driver used by synchronous Alembic migration runner |
| `aiosqlite` | `>=0.20.0` | SQLite Async Driver | Enables zero-configuration local developer persistence |
| `python-jose[cryptography]`| `>=3.3.0` | JWT & JWS Signatures | ABDM and Supabase token verification and claim parsing |
| `pyjwt[crypto]` | `>=2.8.0` | JWT Handling | Secondary standards-compliant JWT decoder |
| `passlib[bcrypt]` | `>=1.7.4` | Password Hashing | Salted bcrypt key derivation for local credentials |
| `python-multipart` | `>=0.0.9` | Form/Multipart Parser | Secure parsing of file uploads and OAuth2 password flows |
| `httpx` | `>=0.27.0` | Asynchronous HTTP Client | Outbound calls to ABDM Sandbox Gateway and DigiLocker APIs |
| `redis` | `>=5.0.0` | Redis Client | Distributed WebSocket cluster sync via Pub/Sub channels |
| `reportlab` | `>=4.2.0` | PDF Generation Engine | Programmatic generation of compliant clinical prescription PDFs |
| `pytest` | `>=8.3.0` | Test Runner | Test suite execution engine (109 passing unit/integration tests) |
| `pytest-asyncio` | `>=0.23.8` | Async Test Support | Allows async test coroutines against async SQLAlchemy sessions |

---

## 3. Frontend Dependency Matrix (`frontend/package.json`)

| Package | Version | Layer / Purpose | Audit Notes |
| :--- | :---: | :--- | :--- |
| `next` | `15.5.25` | App Router Framework | Server components, edge middleware, and Turbopack compiler |
| `react` / `react-dom` | `19.1.0` | UI Library | React 19 concurrent features, transitions, and server actions |
| `typescript` | `^5` | Type Safety | Strict typing enabled (`noEmit: true` passed with 0 errors) |
| `tailwindcss` | `^4` | Utility Styling Engine | Tailwind v4 using `@tailwindcss/postcss` architecture |
| `lucide-react` | `^1.43.0` | Iconography | Lightweight tree-shakable SVG icon set |
| `framer-motion` | `^13.2.0` | Motion Animations | Micro-interactions and smooth queue state transitions |
| `recharts` | `^3.10.1` | Telemetry Charts | Responsive SVG vital sign graphing (Blood pressure, SpO2, Pulse) |
| `qrcode` | `^1.5.4` | QR Code Generation | Client-side dynamic rendering of 14-digit ABHA QR codes |
| `clsx` / `tailwind-merge` | `^2.1.1` / `^3.6.0` | Class Name Utilities | Conditional styling concatenation and Tailwind conflict resolution |
| `ux4g-web-components` | `^3.0.2` | Design System Artifact | Decoupled in Phase 7 to prevent global style bleed; imported selectively |

---

## 4. Build, Scripting & Quality Tooling

- **Workspace Monorepo Orchestration**: Root `package.json:6-16` provides cross-platform lifecycle hooks (`npm run dev`, `npm run build`, `npm run test`, `npm run doctor`).
- **PowerShell & Bash Parity**: Platform startup scripts provided as both `scripts/run-dev.ps1` and `scripts/run-dev.sh`.
- **System Doctor**: `scripts/doctor.py` validates ports (3000, 8000), Python dependencies, Node packages, and database connectivity.
- **Docker Compose**: `docker-compose.yml` standardizes multi-service deployment with healthchecks for `postgres`, `redis`, `backend`, `frontend`, and `caddy`.
