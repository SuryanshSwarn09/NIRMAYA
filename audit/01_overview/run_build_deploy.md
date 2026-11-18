# NIRMAYA: Run, Build, Test & Deployment Playbook

**Audit Layer**: `01_overview`  
**Scope**: Development environment bootstrap, build pipeline, testing procedures, containerization, and cloud deployment.  
**Citations**: `package.json:6-16`, `scripts/doctor.py:1-172`, `scripts/run-dev.ps1:1-67`, `scripts/run-dev.sh:1-68`, `backend/Dockerfile:1-92`, `frontend/Dockerfile:1-77`, `docker-compose.yml:1-161`, `frontend/next.config.ts:1-68`.

---

## 1. Local Developer Bootstrap & Diagnostics

NIRMAYA provides automated diagnostic and dual-process orchestration scripts supporting both Windows (PowerShell) and POSIX (Bash).

### Step 1: Pre-flight Verification (`scripts/doctor.py`)
Run system diagnostics to verify Python `>=3.11`, Node.js `>=18`, virtual environment bindings, port availability (3000, 8000), and configuration files:
```bash
python scripts/doctor.py
```
- Validates PATH for `python`, `node`, `npm`, and `git`.
- Checks for `.env` in `backend/` and `frontend/` (warns if missing).
- Probes port `8000` (FastAPI backend) and `3000` (Next.js frontend) to verify no zombie port collisions.

### Step 2: Concurrent Local Development Launch
Start both FastAPI (with Uvicorn auto-reload) and Next.js (with Turbopack) concurrently:

- **Windows PowerShell**:
  ```powershell
  npm run dev
  # Internally executes: powershell -ExecutionPolicy Bypass -File ./scripts/run-dev.ps1
  ```
- **Linux / macOS Bash**:
  ```bash
  npm run dev:bash
  # Internally executes: bash ./scripts/run-dev.sh
  ```

### Step 3: Local Endpoints
- **Frontend Portal**: `http://localhost:3000`
- **FastAPI Core Backend**: `http://localhost:8000`
- **Interactive Swagger Documentation**: `http://localhost:8000/docs`
- **OpenAPI JSON Spec**: `http://localhost:8000/api/v1/openapi.json`
- **System Health Status**: `http://localhost:8000/api/v1/health`

---

## 2. Test Execution & Quality Gates

The test suite validates database models, FHIR transformations, encryption algorithms, API endpoints, and design system contracts.

### Backend Automated Test Suite (Pytest)
```bash
npm run test:backend
# Or directly:
cd backend && python -m pytest -v
```
- **Execution Target**: 98 test files in `backend/tests/` executing against SQLite async engine or PostgreSQL.
- **Async Fixtures**: Handled via `pytest-asyncio` using transactional rollbacks (`backend/tests/conftest.py`).

### Frontend TypeScript Verification
```bash
npm --prefix frontend run typecheck
# Executes: tsc --noEmit
```
- Ensures 100% type conformance across Next.js 15 App Router pages, clinical components, and API payload definitions.

---

## 3. Production Build Pipeline

```bash
# Full monorepo build (installs frontend deps and compiles Next.js standalone)
npm run build
```

1. **Frontend Compilation**: `next build` runs Turbopack, generating an optimized `standalone` output directory (`frontend/.next/standalone`).
2. **Asset Optimization**: Inlines critical CSS, compresses images, and emits hashed static chunks cached with `Cache-Control: public, max-age=31536000, immutable`.
3. **Database Migrations**:
   ```bash
   cd backend && alembic upgrade head
   ```
   Applies sequential migration revisions (`2026_09_16_0001` through `2026_11_16_0009`) in PostgreSQL.

---

## 4. Multi-Stage Docker Containerization

The production deployment relies on two CIS Docker Benchmark-compliant multi-stage Dockerfiles:

### Backend Dockerfile (`backend/Dockerfile:1-92`)
- **Stage 1 (builder)**: Base `python:3.12-alpine`, installs build tools (`gcc`, `musl-dev`, `libpq-dev`), builds virtual environment at `/opt/venv`.
- **Stage 2 (runtime)**: Base `python:3.12-alpine`, discards compilers, copies `/opt/venv`, creates non-root user `nirmaya` (UID 10001), runs Uvicorn on port `8000` with active container healthchecks (`CMD-SHELL curl -f http://localhost:8000/api/v1/health`).

### Frontend Dockerfile (`frontend/Dockerfile:1-77`)
- **Stage 1 (deps)**: Base `node:20-alpine`, runs `npm ci`.
- **Stage 2 (builder)**: Base `node:20-alpine`, runs `npm run build` targeting `output: "standalone"`.
- **Stage 3 (runner)**: Base `node:20-alpine`, non-root user `nextjs` (UID 1001, GID 1001), runs `server.js` directly via Node (< 150MB total container footprint).

---

## 5. Docker Compose Orchestration (`docker-compose.yml`)

The multi-container production topology consists of 5 coordinated services:
1. `postgres`: PostgreSQL 16 Alpine with healthcheck `pg_isready -U nirmaya_user` and named volume `postgres_data`.
2. `redis`: Redis 7 Alpine with healthcheck `redis-cli ping` and persistent volume `redis_data`.
3. `backend`: FastAPI container depending on `postgres` and `redis` health.
4. `frontend`: Next.js standalone container depending on `backend`.
5. `caddy`: Reverse proxy exposing ports `80` and `443` with automatic TLS and internal proxying to `frontend:3000` and `backend:8000`.

---

## 6. Cloud Deployment Targets

1. **Edge Web Portal (Vercel)**:
   - Live URL: `https://nirmaya-tau.vercel.app`
   - Configured via `frontend/next.config.ts:54-65`, rewriting `/api/v1/:path*` to the production FastAPI endpoint (`BACKEND_API_URL`).
2. **API & Database Engine (Self-Hosted / Cloud VPS)**:
   - Deployed via Docker Compose or Kubernetes, secured behind Caddy edge proxy with SSL termination and HSTS.
