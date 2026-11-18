# Codebase Audit Master Manifest (00_MANIFEST.md)

## 1. Executive Summary & Stack Profile
- **Repository**: NIRMAYA (Networked Interoperable Records Medical Assets & Your Archives)
- **Total Tracked Files**: 789 files
- **Total Untracked Workspace Files**: 67 files (cataloged below for confirmation)
- **Total LOC (Tracked Code & Docs)**: 179,264 lines
- **Detected Stack Profile**:
  - **Backend Framework**: FastAPI (>=0.115.0), Uvicorn (>=0.30.0), Python 3.11/3.12
  - **Database & ORM**: PostgreSQL (asyncpg/psycopg2-binary) & SQLite (aiosqlite), SQLAlchemy (>=2.0.32 async), Alembic (>=1.13.2)
  - **Authentication & Security**: UIDAI Aadhaar Demographic OTP Challenge, DigiLocker e-KYC flow, JWT (python-jose, pyjwt), Passlib (bcrypt), RFC 7636 PKCE S256
  - **Health Standards & Compliance**: HL7 FHIR Release 4, NRCES India extensions, SNOMED CT, LOINC, Verhoeff D5 Checksum (ABHA minting)
  - **Frontend Architecture**: Next.js 15.5.25 (App Router, Turbopack), React 19.1.0, TypeScript 5.x
  - **UI / Design System**: Tailwind CSS v4 (@tailwindcss/postcss), Cal.com-inspired design tokens, Lucide React (v1.43), UX4G web components decoupled
  - **Real-Time Telemetry**: WebSockets (FastAPI WebSockets + React hooks: OPD Queue & Clinical Notifications)
  - **Edge & Infrastructure**: Caddy 2 (Edge Reverse Proxy, automated HTTPS, compression, rate-limiting), Docker, Docker Compose, Vercel

---

## 2. Inventory Breakdown by Architectural Layer & Phase

| Layer | Phase | Description | Total Files | Pending Reports | Cataloged Only | Excluded |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `02_backend` | PHASE 2 | Backend API, Models, Schemas, Services, FHIR, Migrations | 243 | 243 | 0 | 0 |
| `03_frontend` | PHASE 3 | Next.js App Router, Components, Hooks, Context, Libs | 133 | 120 | 13 | 0 |
| `04_docs` | PHASE 4 | Specs, Architecture, Dev Logs, Milestones, Reports | 216 | 209 | 7 | 0 |
| `05_ai_skills` | PHASE 4 | Agent Skills, UI/UX data, prompts, writing guidelines | 65 | 65 | 0 | 0 |
| `06_config_tests_infra` | PHASE 4 | Backend Tests (98), Configs, Scripts, Infra, Lockfile | 132 | 131 | 0 | 1 |
| **TOTAL** | | | **789** | **768** | **20** | **1** |

---

## 3. Huge Files & Complexity Hotspots (>1,000 LOC or >100 KB)
These files require extra audit rigor and may be evaluated in dedicated single-file review slots within their respective batches:

| Path | LOC | Size (Bytes) | Layer | Audit Notes |
| :--- | :---: | :---: | :--- | :--- |
| `backend/app/fhir/schemas.py` | 1,169 | 41,000 | `02_backend` | FHIR domain models (1.1k+ LOC); audit for validation constraints |
| `backend/app/fhir/transformers.py` | 2,047 | 66,931 | `02_backend` | FHIR R4 resource conversion engine (2k+ LOC); audit for schema conformance and field loss |
| `backend/app/services/legacy_his_service.py` | 1,135 | 44,542 | `02_backend` | HL7 v2.x to FHIR bridge (1.1k+ LOC); audit for payload sanitization and parsing risks |
| `backend/app/services/monograph_service.py` | 2,101 | 109,826 | `02_backend` | Core clinical monograph engine (2k+ LOC); audit for injection, algorithmic complexity, and memory |
| `frontend/src/app/patient/page.tsx` | 1,294 | 46,371 | `03_frontend` | Patient portal console (1.2k+ LOC); audit for modularity, re-render cascades, and auth guard |
| `frontend/src/components/clinical/PacsViewerModal.tsx` | 1,061 | 41,628 | `03_frontend` | DICOM/PACS viewer modal (1k+ LOC); audit for memory leaks on canvas and asset loading |
| `frontend/src/components/clinical/PrescriptionAuthoringPad.tsx` | 1,688 | 71,568 | `03_frontend` | OPD Rx pad component (1.6k+ LOC); audit for state management, re-renders, and drug-interaction hooks |
| `frontend/src/lib/api.ts` | 1,909 | 51,227 | `03_frontend` | Monolithic frontend API client (1.9k+ LOC); audit for error handling, token injection, and endpoint drift |
| `docs/CHANGELOG.md` | 2,761 | 297,598 | `04_docs` | Exhaustive project changelog (2.7k+ LOC, ~298 KB); audit for doc claims vs reality |
| `docs/assets/nirmaya-mockup.png` | 0 | 408,862 | `04_docs` | Mockup graphic (408 KB); cataloged only |
| `.agent/skills/ui-ux-pro-max/scripts/design_system.py` | 1,067 | 43,614 | `05_ai_skills` | UI/UX skill script (1k+ LOC); duplicated in .agent/ and .agents/ |
| `.agents/skills/ui-ux-pro-max/scripts/design_system.py` | 1,067 | 43,614 | `05_ai_skills` | UI/UX skill script (1k+ LOC); duplicated in .agent/ and .agents/ |
| `frontend/package-lock.json` | 2,474 | 85,453 | `06_config_tests_infra` | Frontend dependency lockfile (2.4k+ LOC); single summary report required per Rule 6 |

---

## 4. Cataloged Binaries, Images & Non-Text Assets (Rule 6)
Per Rule 6, binary assets and documents receive catalog entries noting file path, size, file type, and all codebase reference locations rather than line-by-line source reports:

| Path | File Type | Size | Codebase References |
| :--- | :--- | :---: | :--- |
| `NIRMAYA_Interim_Project_Report_Month_1.docx` | Binary (DOCX) | 45,741 bytes | `scripts/generate_interim_report_doc.py` |
| `backend/alembic/versions/.gitkeep` | Git Keepfile | 37 bytes | `docs/journey/month-1/day-6.md` |
| `docs/assets/favicon.ico` | Binary (ICO) | 5,238 bytes | `frontend/src/app/layout.tsx` |
| `docs/assets/icon-192.png` | Binary (PNG) | 10,522 bytes | `README.md`, `docs/README.md` |
| `docs/assets/icon-512.png` | Binary (PNG) | 38,890 bytes | *None (unreferenced asset)* |
| `docs/assets/logo.png` | Binary (PNG) | 38,890 bytes | `frontend/src/components/common/BrandLogo.tsx` |
| `docs/assets/nirmaya-mockup.png` | Binary (PNG) | 408,862 bytes | `README.md`, `docs/README.md` |
| `docs/reports/nirmaya-vs-apollo-aarogyasetu-comparative-analysis.docx` | Binary (DOCX) | 56,541 bytes | *None (unreferenced asset)* |
| `frontend/public/apple-touch-icon.png` | Binary (PNG) | 7,723 bytes | `frontend/src/app/layout.tsx` |
| `frontend/public/favicon.ico` | Binary (ICO) | 5,238 bytes | `frontend/src/app/layout.tsx` |
| `frontend/public/file.svg` | Binary (SVG) | 391 bytes | *None (unreferenced asset)* |
| `frontend/public/globe.svg` | Binary (SVG) | 1,035 bytes | *None (unreferenced asset)* |
| `frontend/public/icon-192.png` | Binary (PNG) | 10,522 bytes | `README.md`, `docs/README.md` |
| `frontend/public/icon-512.png` | Binary (PNG) | 38,890 bytes | *None (unreferenced asset)* |
| `frontend/public/icon.png` | Binary (PNG) | 10,522 bytes | `docs/journey/month-4/day-63.md`, `docs/journey/month-4/day-64.md`, `docs/journey/month-4/day-65.md`, `docs/reports/case-study-vercel-deployment-failure.md`, `frontend/src/app/layout.tsx` |
| `frontend/public/logo.png` | Binary (PNG) | 38,890 bytes | `frontend/src/components/common/BrandLogo.tsx` |
| `frontend/public/next.svg` | Binary (SVG) | 1,375 bytes | *None (unreferenced asset)* |
| `frontend/public/vercel.svg` | Binary (SVG) | 128 bytes | *None (unreferenced asset)* |
| `frontend/public/window.svg` | Binary (SVG) | 385 bytes | *None (unreferenced asset)* |
| `frontend/src/app/favicon.ico` | Binary (ICO) | 5,238 bytes | `frontend/src/app/layout.tsx` |
| `frontend/src/app/icon.png` | Binary (PNG) | 10,522 bytes | `docs/journey/month-4/day-63.md`, `docs/journey/month-4/day-64.md`, `docs/journey/month-4/day-65.md`, `docs/reports/case-study-vercel-deployment-failure.md`, `frontend/src/app/layout.tsx` |

---

## 5. Untracked Workspace Files (Pending Scope Confirmation)
The following files exist in the working directory but are currently untracked in Git. By default, Phase 4 includes them under `05_ai_skills` and `06_config_tests_infra` unless explicitly excluded by user direction:

| Path | Recommended Layer | Type | Status |
| :--- | :--- | :--- | :--- |
| `.agent/workflows/add-phase.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/add-todo.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/audit-milestone.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/check-todos.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/complete-milestone.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/debug.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/discuss-phase.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/execute.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/help.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/insert-phase.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/install.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/list-phase-assumptions.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/map.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/new-milestone.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/new-project.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/pause.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/plan-milestone-gaps.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/plan.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/progress.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/remove-phase.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/research-phase.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/resume.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/sprint.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/update.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/verify.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/web-search.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agent/workflows/whats-new.md` | `05_ai_skills` | GSD Agent Workflow | `PENDING (Untracked)` |
| `.agents/agents/gsd-debugger.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/agents/gsd-executor.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/agents/gsd-planner.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/agents/gsd-researcher.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/agents/gsd-verifier.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/codebase-mapper/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/context-compressor/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/context-fetch/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/context-health-monitor/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/debugger/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/empirical-validation/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/executor/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/plan-checker/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/planner/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/subagent-delegation/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/token-budget/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.agents/skills/verifier/SKILL.md` | `05_ai_skills` | GSD Agent / Skill | `PENDING (Untracked)` |
| `.gemini/GEMINI.md` | `05_ai_skills` | Agent Rule / Style Guide | `PENDING (Untracked)` |
| `GSD-STYLE.md` | `05_ai_skills` | Agent Rule / Style Guide | `PENDING (Untracked)` |
| `PROJECT_RULES.md` | `05_ai_skills` | Agent Rule / Style Guide | `PENDING (Untracked)` |
| `adapters/CLAUDE.md` | `05_ai_skills` | Agent Adapter Prompt | `PENDING (Untracked)` |
| `adapters/GEMINI.md` | `05_ai_skills` | Agent Adapter Prompt | `PENDING (Untracked)` |
| `adapters/GPT_OSS.md` | `05_ai_skills` | Agent Adapter Prompt | `PENDING (Untracked)` |
| `model_capabilities.yaml` | `05_ai_skills` | Agent Rule / Style Guide | `PENDING (Untracked)` |
| `scripts/search_repo.ps1` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/search_repo.sh` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/setup_search.ps1` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/setup_search.sh` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-agents.ps1` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-agents.sh` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-all.ps1` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-all.sh` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-encoding.ps1` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-encoding.sh` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-skills.ps1` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-skills.sh` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-templates.ps1` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-templates.sh` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-workflows.ps1` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |
| `scripts/validate-workflows.sh` | `06_config_tests_infra` | GSD Validation Script | `PENDING (Untracked)` |

---

## 6. Deterministic Exclusions (Rule 6)
The following runtime, cache, and dependency directories are strictly excluded from the audit manifest and reports:

| Directory / Pattern | Reason for Exclusion |
| :--- | :--- |
| `.git/` | Version control internal database and logs |
| `node_modules/`, `frontend/node_modules/` | Third-party vendor dependencies (lockfile audited separately) |
| `backend/.venv/`, `venv/` | Python virtual environment binaries and site-packages |
| `.next/`, `frontend/.next/` | Next.js build cache and compiled server/client bundles |
| `__pycache__/`, `*.pyc` | Compiled Python bytecode caches |
| `.pytest_cache/` | Test runner local execution caches |
| `dist/`, `build/` | Compiled production artifacts |

---

## 7. Master File Table (All 789 Tracked Files)

| # | Path | Layer | Phase | Type | LOC | Status |
| :---: | :--- | :--- | :---: | :--- | :---: | :---: |
| 1 | `backend/alembic/env.py` | `02_backend` | PHASE 2 | Database Migration | 86 | `PENDING` |
| 2 | `backend/alembic/script.py.mako` | `02_backend` | PHASE 2 | Database Migration | 26 | `PENDING` |
| 3 | `backend/alembic/versions/2026_09_16_0001_initial_core_schema.py` | `02_backend` | PHASE 2 | Database Migration | 165 | `PENDING` |
| 4 | `backend/alembic/versions/2026_09_28_0002_appointments_and_slots_schema.py` | `02_backend` | PHASE 2 | Database Migration | 106 | `PENDING` |
| 5 | `backend/alembic/versions/2026_09_29_0003_slot_concurrency_and_hold_fields.py` | `02_backend` | PHASE 2 | Database Migration | 62 | `PENDING` |
| 6 | `backend/alembic/versions/2026_10_05_0004_conditions_schema.py` | `02_backend` | PHASE 2 | Database Migration | 99 | `PENDING` |
| 7 | `backend/alembic/versions/2026_10_05_0005_observations_schema.py` | `02_backend` | PHASE 2 | Database Migration | 109 | `PENDING` |
| 8 | `backend/alembic/versions/2026_10_06_0006_soap_notes_schema.py` | `02_backend` | PHASE 2 | Database Migration | 100 | `PENDING` |
| 9 | `backend/alembic/versions/2026_10_07_0007_diagnostics_schema.py` | `02_backend` | PHASE 2 | Database Migration | 183 | `PENDING` |
| 10 | `backend/alembic/versions/2026_10_13_0008_medication_catalog_schema.py` | `02_backend` | PHASE 2 | Database Migration | 80 | `PENDING` |
| 11 | `backend/alembic/versions/2026_10_14_0009_medication_request_schema.py` | `02_backend` | PHASE 2 | Database Migration | 94 | `PENDING` |
| 12 | `backend/alembic/versions/2026_10_15_0010_medication_dispense_schema.py` | `02_backend` | PHASE 2 | Database Migration | 81 | `PENDING` |
| 13 | `backend/alembic/versions/2026_11_01_0011_lgd_administrative_hierarchy_ltree.py` | `02_backend` | PHASE 2 | Database Migration | 92 | `PENDING` |
| 14 | `backend/app/__init__.py` | `02_backend` | PHASE 2 | Python Source | 5 | `PENDING` |
| 15 | `backend/app/abdm/__init__.py` | `02_backend` | PHASE 2 | Python Source | 11 | `PENDING` |
| 16 | `backend/app/abdm/client.py` | `02_backend` | PHASE 2 | Python Source | 172 | `PENDING` |
| 17 | `backend/app/abdm/security/__init__.py` | `02_backend` | PHASE 2 | Python Source | 5 | `PENDING` |
| 18 | `backend/app/abdm/security/rsa.py` | `02_backend` | PHASE 2 | Python Source | 171 | `PENDING` |
| 19 | `backend/app/api/__init__.py` | `02_backend` | PHASE 2 | Python Source | 1 | `PENDING` |
| 20 | `backend/app/api/v1/__init__.py` | `02_backend` | PHASE 2 | Python Source | 1 | `PENDING` |
| 21 | `backend/app/api/v1/endpoints/__init__.py` | `02_backend` | PHASE 2 | Python Source | 4 | `PENDING` |
| 22 | `backend/app/api/v1/endpoints/abdm.py` | `02_backend` | PHASE 2 | Python Source | 140 | `PENDING` |
| 23 | `backend/app/api/v1/endpoints/abdm_certification.py` | `02_backend` | PHASE 2 | Python Source | 87 | `PENDING` |
| 24 | `backend/app/api/v1/endpoints/abdm_issuance.py` | `02_backend` | PHASE 2 | Python Source | 111 | `PENDING` |
| 25 | `backend/app/api/v1/endpoints/abdm_m1.py` | `02_backend` | PHASE 2 | Python Source | 85 | `PENDING` |
| 26 | `backend/app/api/v1/endpoints/abdm_m2_bridge.py` | `02_backend` | PHASE 2 | Python Source | 444 | `PENDING` |
| 27 | `backend/app/api/v1/endpoints/abdm_m3_audit.py` | `02_backend` | PHASE 2 | Python Source | 39 | `PENDING` |
| 28 | `backend/app/api/v1/endpoints/abdm_m3_consent.py` | `02_backend` | PHASE 2 | Python Source | 163 | `PENDING` |
| 29 | `backend/app/api/v1/endpoints/abdm_m3_crypto.py` | `02_backend` | PHASE 2 | Python Source | 296 | `PENDING` |
| 30 | `backend/app/api/v1/endpoints/abdm_m3_hiu.py` | `02_backend` | PHASE 2 | Python Source | 183 | `PENDING` |
| 31 | `backend/app/api/v1/endpoints/abdm_m3_transfer.py` | `02_backend` | PHASE 2 | Python Source | 223 | `PENDING` |
| 32 | `backend/app/api/v1/endpoints/abdm_security_audit.py` | `02_backend` | PHASE 2 | Python Source | 86 | `PENDING` |
| 33 | `backend/app/api/v1/endpoints/accessibility.py` | `02_backend` | PHASE 2 | Python Source | 120 | `PENDING` |
| 34 | `backend/app/api/v1/endpoints/administrative_hierarchy.py` | `02_backend` | PHASE 2 | Python Source | 266 | `PENDING` |
| 35 | `backend/app/api/v1/endpoints/appointments.py` | `02_backend` | PHASE 2 | Python Source | 355 | `PENDING` |
| 36 | `backend/app/api/v1/endpoints/asvs_audit.py` | `02_backend` | PHASE 2 | Python Source | 89 | `PENDING` |
| 37 | `backend/app/api/v1/endpoints/audit.py` | `02_backend` | PHASE 2 | Python Source | 86 | `PENDING` |
| 38 | `backend/app/api/v1/endpoints/audit_ledger.py` | `02_backend` | PHASE 2 | Python Source | 104 | `PENDING` |
| 39 | `backend/app/api/v1/endpoints/auth.py` | `02_backend` | PHASE 2 | Python Source | 215 | `PENDING` |
| 40 | `backend/app/api/v1/endpoints/benchmarks.py` | `02_backend` | PHASE 2 | Python Source | 89 | `PENDING` |
| 41 | `backend/app/api/v1/endpoints/child_abha.py` | `02_backend` | PHASE 2 | Python Source | 100 | `PENDING` |
| 42 | `backend/app/api/v1/endpoints/citizen_portal.py` | `02_backend` | PHASE 2 | Python Source | 116 | `PENDING` |
| 43 | `backend/app/api/v1/endpoints/clinical_alerts.py` | `02_backend` | PHASE 2 | Python Source | 140 | `PENDING` |
| 44 | `backend/app/api/v1/endpoints/command_center.py` | `02_backend` | PHASE 2 | Python Source | 135 | `PENDING` |
| 45 | `backend/app/api/v1/endpoints/conditions.py` | `02_backend` | PHASE 2 | Python Source | 283 | `PENDING` |
| 46 | `backend/app/api/v1/endpoints/container.py` | `02_backend` | PHASE 2 | Python Source | 135 | `PENDING` |
| 47 | `backend/app/api/v1/endpoints/delegation.py` | `02_backend` | PHASE 2 | Python Source | 180 | `PENDING` |
| 48 | `backend/app/api/v1/endpoints/demo.py` | `02_backend` | PHASE 2 | Python Source | 89 | `PENDING` |
| 49 | `backend/app/api/v1/endpoints/diagnostics.py` | `02_backend` | PHASE 2 | Python Source | 370 | `PENDING` |
| 50 | `backend/app/api/v1/endpoints/digilocker.py` | `02_backend` | PHASE 2 | Python Source | 89 | `PENDING` |
| 51 | `backend/app/api/v1/endpoints/doctors.py` | `02_backend` | PHASE 2 | Python Source | 382 | `PENDING` |
| 52 | `backend/app/api/v1/endpoints/edge_sync.py` | `02_backend` | PHASE 2 | Python Source | 86 | `PENDING` |
| 53 | `backend/app/api/v1/endpoints/emergency_vault.py` | `02_backend` | PHASE 2 | Python Source | 111 | `PENDING` |
| 54 | `backend/app/api/v1/endpoints/express_consultation.py` | `02_backend` | PHASE 2 | Python Source | 135 | `PENDING` |
| 55 | `backend/app/api/v1/endpoints/family_proxy.py` | `02_backend` | PHASE 2 | Python Source | 189 | `PENDING` |
| 56 | `backend/app/api/v1/endpoints/fhir_validator.py` | `02_backend` | PHASE 2 | Python Source | 86 | `PENDING` |
| 57 | `backend/app/api/v1/endpoints/guardian_conflict.py` | `02_backend` | PHASE 2 | Python Source | 227 | `PENDING` |
| 58 | `backend/app/api/v1/endpoints/guardian_delegation.py` | `02_backend` | PHASE 2 | Python Source | 160 | `PENDING` |
| 59 | `backend/app/api/v1/endpoints/health.py` | `02_backend` | PHASE 2 | Python Source | 105 | `PENDING` |
| 60 | `backend/app/api/v1/endpoints/legacy_his.py` | `02_backend` | PHASE 2 | Python Source | 237 | `PENDING` |
| 61 | `backend/app/api/v1/endpoints/medication_dispenses.py` | `02_backend` | PHASE 2 | Python Source | 318 | `PENDING` |
| 62 | `backend/app/api/v1/endpoints/medication_requests.py` | `02_backend` | PHASE 2 | Python Source | 302 | `PENDING` |
| 63 | `backend/app/api/v1/endpoints/medications.py` | `02_backend` | PHASE 2 | Python Source | 199 | `PENDING` |
| 64 | `backend/app/api/v1/endpoints/meta.py` | `02_backend` | PHASE 2 | Python Source | 86 | `PENDING` |
| 65 | `backend/app/api/v1/endpoints/monograph.py` | `02_backend` | PHASE 2 | Python Source | 379 | `PENDING` |
| 66 | `backend/app/api/v1/endpoints/national_gateway.py` | `02_backend` | PHASE 2 | Python Source | 233 | `PENDING` |
| 67 | `backend/app/api/v1/endpoints/observations.py` | `02_backend` | PHASE 2 | Python Source | 273 | `PENDING` |
| 68 | `backend/app/api/v1/endpoints/opd_queue.py` | `02_backend` | PHASE 2 | Python Source | 128 | `PENDING` |
| 69 | `backend/app/api/v1/endpoints/orchestration.py` | `02_backend` | PHASE 2 | Python Source | 80 | `PENDING` |
| 70 | `backend/app/api/v1/endpoints/patient_auth.py` | `02_backend` | PHASE 2 | Python Source | 58 | `PENDING` |
| 71 | `backend/app/api/v1/endpoints/patients.py` | `02_backend` | PHASE 2 | Python Source | 232 | `PENDING` |
| 72 | `backend/app/api/v1/endpoints/release.py` | `02_backend` | PHASE 2 | Python Source | 86 | `PENDING` |
| 73 | `backend/app/api/v1/endpoints/security_scan.py` | `02_backend` | PHASE 2 | Python Source | 85 | `PENDING` |
| 74 | `backend/app/api/v1/endpoints/soap_notes.py` | `02_backend` | PHASE 2 | Python Source | 257 | `PENDING` |
| 75 | `backend/app/api/v1/endpoints/terminology_validator.py` | `02_backend` | PHASE 2 | Python Source | 110 | `PENDING` |
| 76 | `backend/app/api/v1/endpoints/websockets.py` | `02_backend` | PHASE 2 | Python Source | 211 | `PENDING` |
| 77 | `backend/app/api/v1/endpoints/workflow_isolation.py` | `02_backend` | PHASE 2 | Python Source | 153 | `PENDING` |
| 78 | `backend/app/api/v1/router.py` | `02_backend` | PHASE 2 | Python Source | 127 | `PENDING` |
| 79 | `backend/app/core/__init__.py` | `02_backend` | PHASE 2 | Python Source | 6 | `DONE` |
| 80 | `backend/app/core/config.py` | `02_backend` | PHASE 2 | Python Source | 194 | `DONE` |
| 81 | `backend/app/core/container_security.py` | `02_backend` | PHASE 2 | Python Source | 80 | `DONE` |
| 82 | `backend/app/core/cors.py` | `02_backend` | PHASE 2 | Python Source | 45 | `DONE` |
| 83 | `backend/app/core/dependencies.py` | `02_backend` | PHASE 2 | Python Source | 249 | `DONE` |
| 84 | `backend/app/core/exceptions.py` | `02_backend` | PHASE 2 | Python Source | 177 | `DONE` |
| 85 | `backend/app/core/logging.py` | `02_backend` | PHASE 2 | Python Source | 38 | `DONE` |
| 86 | `backend/app/core/middleware.py` | `02_backend` | PHASE 2 | Python Source | 51 | `DONE` |
| 87 | `backend/app/core/rate_limit.py` | `02_backend` | PHASE 2 | Python Source | 195 | `DONE` |
| 88 | `backend/app/core/security.py` | `02_backend` | PHASE 2 | Python Source | 103 | `DONE` |
| 89 | `backend/app/core/territorial_rbac.py` | `02_backend` | PHASE 2 | Python Source | 99 | `DONE` |
| 90 | `backend/app/db/__init__.py` | `02_backend` | PHASE 2 | Python Source | 34 | `DONE` |
| 91 | `backend/app/db/base.py` | `02_backend` | PHASE 2 | Python Source | 46 | `DONE` |
| 92 | `backend/app/db/fixtures.py` | `02_backend` | PHASE 2 | Python Source | 275 | `DONE` |
| 93 | `backend/app/db/seeder.py` | `02_backend` | PHASE 2 | Python Source | 143 | `DONE` |
| 94 | `backend/app/db/session.py` | `02_backend` | PHASE 2 | Python Source | 153 | `DONE` |
| 95 | `backend/app/db/tenant_context.py` | `02_backend` | PHASE 2 | Python Source | 93 | `DONE` |
| 96 | `backend/app/fhir/__init__.py` | `02_backend` | PHASE 2 | Python Source | 100 | `PENDING` |
| 97 | `backend/app/fhir/schemas.py` | `02_backend` | PHASE 2 | Python Source | 1169 | `PENDING` |
| 98 | `backend/app/fhir/transformers.py` | `02_backend` | PHASE 2 | Python Source | 2047 | `PENDING` |
| 99 | `backend/app/main.py` | `02_backend` | PHASE 2 | Python Source | 94 | `PENDING` |
| 100 | `backend/app/models/__init__.py` | `02_backend` | PHASE 2 | Python Source | 116 | `DONE` |
| 101 | `backend/app/models/administrative_hierarchy.py` | `02_backend` | PHASE 2 | Python Source | 172 | `DONE` |
| 102 | `backend/app/models/appointment.py` | `02_backend` | PHASE 2 | Python Source | 223 | `DONE` |
| 103 | `backend/app/models/command_center.py` | `02_backend` | PHASE 2 | Python Source | 229 | `DONE` |
| 104 | `backend/app/models/condition.py` | `02_backend` | PHASE 2 | Python Source | 150 | `DONE` |
| 105 | `backend/app/models/delegation.py` | `02_backend` | PHASE 2 | Python Source | 151 | `DONE` |
| 106 | `backend/app/models/diagnostic.py` | `02_backend` | PHASE 2 | Python Source | 310 | `DONE` |
| 107 | `backend/app/models/doctor.py` | `02_backend` | PHASE 2 | Python Source | 150 | `DONE` |
| 108 | `backend/app/models/enums.py` | `02_backend` | PHASE 2 | Python Source | 446 | `DONE` |
| 109 | `backend/app/models/family_proxy.py` | `02_backend` | PHASE 2 | Python Source | 134 | `DONE` |
| 110 | `backend/app/models/lab.py` | `02_backend` | PHASE 2 | Python Source | 111 | `DONE` |
| 111 | `backend/app/models/medication.py` | `02_backend` | PHASE 2 | Python Source | 197 | `DONE` |
| 112 | `backend/app/models/medication_dispense.py` | `02_backend` | PHASE 2 | Python Source | 184 | `DONE` |
| 113 | `backend/app/models/medication_request.py` | `02_backend` | PHASE 2 | Python Source | 287 | `DONE` |
| 114 | `backend/app/models/observation.py` | `02_backend` | PHASE 2 | Python Source | 210 | `DONE` |
| 115 | `backend/app/models/patient.py` | `02_backend` | PHASE 2 | Python Source | 165 | `DONE` |
| 116 | `backend/app/models/soap_note.py` | `02_backend` | PHASE 2 | Python Source | 166 | `DONE` |
| 117 | `backend/app/models/user.py` | `02_backend` | PHASE 2 | Python Source | 81 | `DONE` |
| 118 | `backend/app/schemas/__init__.py` | `02_backend` | PHASE 2 | Python Source | 771 | `DONE` |
| 119 | `backend/app/schemas/abdm.py` | `02_backend` | PHASE 2 | Python Source | 84 | `DONE` |
| 120 | `backend/app/schemas/abdm_certification.py` | `02_backend` | PHASE 2 | Python Source | 139 | `DONE` |
| 121 | `backend/app/schemas/abdm_m1.py` | `02_backend` | PHASE 2 | Python Source | 114 | `DONE` |
| 122 | `backend/app/schemas/abdm_m1_issuance.py` | `02_backend` | PHASE 2 | Python Source | 126 | `DONE` |
| 123 | `backend/app/schemas/abdm_m2_bridge.py` | `02_backend` | PHASE 2 | Python Source | 516 | `DONE` |
| 124 | `backend/app/schemas/abdm_m3_audit.py` | `02_backend` | PHASE 2 | Python Source | 108 | `DONE` |
| 125 | `backend/app/schemas/abdm_m3_consent.py` | `02_backend` | PHASE 2 | Python Source | 304 | `DONE` |
| 126 | `backend/app/schemas/abdm_m3_crypto.py` | `02_backend` | PHASE 2 | Python Source | 189 | `DONE` |
| 127 | `backend/app/schemas/abdm_m3_hiu.py` | `02_backend` | PHASE 2 | Python Source | 149 | `DONE` |
| 128 | `backend/app/schemas/abdm_m3_transfer.py` | `02_backend` | PHASE 2 | Python Source | 179 | `DONE` |
| 129 | `backend/app/schemas/abdm_security_audit.py` | `02_backend` | PHASE 2 | Python Source | 148 | `DONE` |
| 130 | `backend/app/schemas/abha_card.py` | `02_backend` | PHASE 2 | Python Source | 73 | `DONE` |
| 131 | `backend/app/schemas/accessibility.py` | `02_backend` | PHASE 2 | Python Source | 78 | `DONE` |
| 132 | `backend/app/schemas/administrative_hierarchy.py` | `02_backend` | PHASE 2 | Python Source | 129 | `PENDING` |
| 133 | `backend/app/schemas/appointment.py` | `02_backend` | PHASE 2 | Python Source | 240 | `PENDING` |
| 134 | `backend/app/schemas/asvs_fuzzer.py` | `02_backend` | PHASE 2 | Python Source | 149 | `PENDING` |
| 135 | `backend/app/schemas/audit_hash_chain.py` | `02_backend` | PHASE 2 | Python Source | 135 | `PENDING` |
| 136 | `backend/app/schemas/auth.py` | `02_backend` | PHASE 2 | Python Source | 58 | `PENDING` |
| 137 | `backend/app/schemas/benchmark.py` | `02_backend` | PHASE 2 | Python Source | 104 | `PENDING` |
| 138 | `backend/app/schemas/cds.py` | `02_backend` | PHASE 2 | Python Source | 137 | `PENDING` |
| 139 | `backend/app/schemas/child_abha.py` | `02_backend` | PHASE 2 | Python Source | 84 | `PENDING` |
| 140 | `backend/app/schemas/citizen_portal.py` | `02_backend` | PHASE 2 | Python Source | 225 | `PENDING` |
| 141 | `backend/app/schemas/clinical_alerts.py` | `02_backend` | PHASE 2 | Python Source | 155 | `PENDING` |
| 142 | `backend/app/schemas/command_center.py` | `02_backend` | PHASE 2 | Python Source | 164 | `PENDING` |
| 143 | `backend/app/schemas/common.py` | `02_backend` | PHASE 2 | Python Source | 57 | `PENDING` |
| 144 | `backend/app/schemas/condition.py` | `02_backend` | PHASE 2 | Python Source | 172 | `PENDING` |
| 145 | `backend/app/schemas/container_runtime.py` | `02_backend` | PHASE 2 | Python Source | 452 | `PENDING` |
| 146 | `backend/app/schemas/delegation.py` | `02_backend` | PHASE 2 | Python Source | 164 | `PENDING` |
| 147 | `backend/app/schemas/demo.py` | `02_backend` | PHASE 2 | Python Source | 79 | `PENDING` |
| 148 | `backend/app/schemas/diagnostic.py` | `02_backend` | PHASE 2 | Python Source | 265 | `PENDING` |
| 149 | `backend/app/schemas/digilocker.py` | `02_backend` | PHASE 2 | Python Source | 98 | `PENDING` |
| 150 | `backend/app/schemas/doctor.py` | `02_backend` | PHASE 2 | Python Source | 106 | `PENDING` |
| 151 | `backend/app/schemas/edge_sync.py` | `02_backend` | PHASE 2 | Python Source | 244 | `PENDING` |
| 152 | `backend/app/schemas/emergency_vault.py` | `02_backend` | PHASE 2 | Python Source | 224 | `PENDING` |
| 153 | `backend/app/schemas/express_consultation.py` | `02_backend` | PHASE 2 | Python Source | 137 | `PENDING` |
| 154 | `backend/app/schemas/family_proxy.py` | `02_backend` | PHASE 2 | Python Source | 83 | `PENDING` |
| 155 | `backend/app/schemas/fhir_validator.py` | `02_backend` | PHASE 2 | Python Source | 141 | `PENDING` |
| 156 | `backend/app/schemas/guardian_conflict.py` | `02_backend` | PHASE 2 | Python Source | 129 | `PENDING` |
| 157 | `backend/app/schemas/guardian_delegation.py` | `02_backend` | PHASE 2 | Python Source | 95 | `PENDING` |
| 158 | `backend/app/schemas/health.py` | `02_backend` | PHASE 2 | Python Source | 41 | `PENDING` |
| 159 | `backend/app/schemas/lab.py` | `02_backend` | PHASE 2 | Python Source | 134 | `PENDING` |
| 160 | `backend/app/schemas/legacy_his.py` | `02_backend` | PHASE 2 | Python Source | 198 | `PENDING` |
| 161 | `backend/app/schemas/license_audit.py` | `02_backend` | PHASE 2 | Python Source | 112 | `PENDING` |
| 162 | `backend/app/schemas/medication.py` | `02_backend` | PHASE 2 | Python Source | 195 | `PENDING` |
| 163 | `backend/app/schemas/medication_dispense.py` | `02_backend` | PHASE 2 | Python Source | 223 | `PENDING` |
| 164 | `backend/app/schemas/medication_request.py` | `02_backend` | PHASE 2 | Python Source | 242 | `PENDING` |
| 165 | `backend/app/schemas/monograph.py` | `02_backend` | PHASE 2 | Python Source | 457 | `PENDING` |
| 166 | `backend/app/schemas/national_gateway.py` | `02_backend` | PHASE 2 | Python Source | 154 | `PENDING` |
| 167 | `backend/app/schemas/observation.py` | `02_backend` | PHASE 2 | Python Source | 307 | `PENDING` |
| 168 | `backend/app/schemas/opd_queue.py` | `02_backend` | PHASE 2 | Python Source | 143 | `PENDING` |
| 169 | `backend/app/schemas/orchestration.py` | `02_backend` | PHASE 2 | Python Source | 252 | `PENDING` |
| 170 | `backend/app/schemas/patient.py` | `02_backend` | PHASE 2 | Python Source | 119 | `PENDING` |
| 171 | `backend/app/schemas/patient_auth.py` | `02_backend` | PHASE 2 | Python Source | 62 | `PENDING` |
| 172 | `backend/app/schemas/release.py` | `02_backend` | PHASE 2 | Python Source | 110 | `PENDING` |
| 173 | `backend/app/schemas/security_scanner.py` | `02_backend` | PHASE 2 | Python Source | 156 | `PENDING` |
| 174 | `backend/app/schemas/soap_note.py` | `02_backend` | PHASE 2 | Python Source | 150 | `PENDING` |
| 175 | `backend/app/schemas/terminology_validator.py` | `02_backend` | PHASE 2 | Python Source | 171 | `PENDING` |
| 176 | `backend/app/schemas/user.py` | `02_backend` | PHASE 2 | Python Source | 67 | `PENDING` |
| 177 | `backend/app/schemas/websocket_events.py` | `02_backend` | PHASE 2 | Python Source | 247 | `PENDING` |
| 178 | `backend/app/schemas/workflow_isolation.py` | `02_backend` | PHASE 2 | Python Source | 109 | `PENDING` |
| 179 | `backend/app/services/__init__.py` | `02_backend` | PHASE 2 | Python Source | 339 | `PENDING` |
| 180 | `backend/app/services/aadhaar_otp.py` | `02_backend` | PHASE 2 | Python Source | 320 | `PENDING` |
| 181 | `backend/app/services/abdm_certification.py` | `02_backend` | PHASE 2 | Python Source | 798 | `PENDING` |
| 182 | `backend/app/services/abdm_consent.py` | `02_backend` | PHASE 2 | Python Source | 450 | `PENDING` |
| 183 | `backend/app/services/abdm_crypto.py` | `02_backend` | PHASE 2 | Python Source | 434 | `PENDING` |
| 184 | `backend/app/services/abdm_discovery.py` | `02_backend` | PHASE 2 | Python Source | 724 | `PENDING` |
| 185 | `backend/app/services/abdm_hip_bridge.py` | `02_backend` | PHASE 2 | Python Source | 401 | `PENDING` |
| 186 | `backend/app/services/abdm_hiu.py` | `02_backend` | PHASE 2 | Python Source | 548 | `PENDING` |
| 187 | `backend/app/services/abdm_issuance.py` | `02_backend` | PHASE 2 | Python Source | 299 | `PENDING` |
| 188 | `backend/app/services/abdm_linkage.py` | `02_backend` | PHASE 2 | Python Source | 695 | `PENDING` |
| 189 | `backend/app/services/abdm_m3_audit.py` | `02_backend` | PHASE 2 | Python Source | 151 | `PENDING` |
| 190 | `backend/app/services/abdm_security_audit.py` | `02_backend` | PHASE 2 | Python Source | 788 | `PENDING` |
| 191 | `backend/app/services/abdm_transfer.py` | `02_backend` | PHASE 2 | Python Source | 577 | `PENDING` |
| 192 | `backend/app/services/abha_card.py` | `02_backend` | PHASE 2 | Python Source | 200 | `PENDING` |
| 193 | `backend/app/services/accessibility_service.py` | `02_backend` | PHASE 2 | Python Source | 424 | `PENDING` |
| 194 | `backend/app/services/administrative_hierarchy_service.py` | `02_backend` | PHASE 2 | Python Source | 585 | `PENDING` |
| 195 | `backend/app/services/appointment.py` | `02_backend` | PHASE 2 | Python Source | 290 | `PENDING` |
| 196 | `backend/app/services/asvs_audit_service.py` | `02_backend` | PHASE 2 | Python Source | 217 | `PENDING` |
| 197 | `backend/app/services/asvs_fuzzer.py` | `02_backend` | PHASE 2 | Python Source | 253 | `PENDING` |
| 198 | `backend/app/services/audit_hash_chain.py` | `02_backend` | PHASE 2 | Python Source | 296 | `PENDING` |
| 199 | `backend/app/services/benchmark_service.py` | `02_backend` | PHASE 2 | Python Source | 838 | `PENDING` |
| 200 | `backend/app/services/cds_rules.py` | `02_backend` | PHASE 2 | Python Source | 598 | `PENDING` |
| 201 | `backend/app/services/cds_safety.py` | `02_backend` | PHASE 2 | Python Source | 181 | `PENDING` |
| 202 | `backend/app/services/child_abha_service.py` | `02_backend` | PHASE 2 | Python Source | 206 | `PENDING` |
| 203 | `backend/app/services/citizen_portal_service.py` | `02_backend` | PHASE 2 | Python Source | 750 | `PENDING` |
| 204 | `backend/app/services/clinical_alerts.py` | `02_backend` | PHASE 2 | Python Source | 464 | `PENDING` |
| 205 | `backend/app/services/command_center_service.py` | `02_backend` | PHASE 2 | Python Source | 498 | `PENDING` |
| 206 | `backend/app/services/condition.py` | `02_backend` | PHASE 2 | Python Source | 243 | `PENDING` |
| 207 | `backend/app/services/container_service.py` | `02_backend` | PHASE 2 | Python Source | 535 | `PENDING` |
| 208 | `backend/app/services/delegation_service.py` | `02_backend` | PHASE 2 | Python Source | 459 | `PENDING` |
| 209 | `backend/app/services/demo_service.py` | `02_backend` | PHASE 2 | Python Source | 601 | `PENDING` |
| 210 | `backend/app/services/dependency_scanner.py` | `02_backend` | PHASE 2 | Python Source | 254 | `PENDING` |
| 211 | `backend/app/services/diagnostic.py` | `02_backend` | PHASE 2 | Python Source | 345 | `PENDING` |
| 212 | `backend/app/services/digilocker.py` | `02_backend` | PHASE 2 | Python Source | 370 | `PENDING` |
| 213 | `backend/app/services/doctor.py` | `02_backend` | PHASE 2 | Python Source | 238 | `PENDING` |
| 214 | `backend/app/services/dos_shield.py` | `02_backend` | PHASE 2 | Python Source | 204 | `PENDING` |
| 215 | `backend/app/services/edge_sync_service.py` | `02_backend` | PHASE 2 | Python Source | 342 | `PENDING` |
| 216 | `backend/app/services/emergency_dispatch.py` | `02_backend` | PHASE 2 | Python Source | 173 | `PENDING` |
| 217 | `backend/app/services/emergency_vault.py` | `02_backend` | PHASE 2 | Python Source | 387 | `PENDING` |
| 218 | `backend/app/services/express_consultation_service.py` | `02_backend` | PHASE 2 | Python Source | 636 | `PENDING` |
| 219 | `backend/app/services/family_proxy_service.py` | `02_backend` | PHASE 2 | Python Source | 267 | `PENDING` |
| 220 | `backend/app/services/fhir_validator.py` | `02_backend` | PHASE 2 | Python Source | 688 | `PENDING` |
| 221 | `backend/app/services/guardian_conflict_service.py` | `02_backend` | PHASE 2 | Python Source | 552 | `PENDING` |
| 222 | `backend/app/services/guardian_delegation_service.py` | `02_backend` | PHASE 2 | Python Source | 284 | `PENDING` |
| 223 | `backend/app/services/legacy_his_service.py` | `02_backend` | PHASE 2 | Python Source | 1135 | `PENDING` |
| 224 | `backend/app/services/license_audit_service.py` | `02_backend` | PHASE 2 | Python Source | 587 | `PENDING` |
| 225 | `backend/app/services/medication.py` | `02_backend` | PHASE 2 | Python Source | 853 | `PENDING` |
| 226 | `backend/app/services/medication_dispense.py` | `02_backend` | PHASE 2 | Python Source | 246 | `PENDING` |
| 227 | `backend/app/services/medication_request.py` | `02_backend` | PHASE 2 | Python Source | 297 | `PENDING` |
| 228 | `backend/app/services/monograph_service.py` | `02_backend` | PHASE 2 | Python Source | 2101 | `PENDING` |
| 229 | `backend/app/services/national_gateway_service.py` | `02_backend` | PHASE 2 | Python Source | 523 | `PENDING` |
| 230 | `backend/app/services/observation.py` | `02_backend` | PHASE 2 | Python Source | 301 | `PENDING` |
| 231 | `backend/app/services/opd_queue.py` | `02_backend` | PHASE 2 | Python Source | 334 | `PENDING` |
| 232 | `backend/app/services/orchestration_service.py` | `02_backend` | PHASE 2 | Python Source | 391 | `PENDING` |
| 233 | `backend/app/services/patient.py` | `02_backend` | PHASE 2 | Python Source | 212 | `PENDING` |
| 234 | `backend/app/services/patient_auth.py` | `02_backend` | PHASE 2 | Python Source | 351 | `PENDING` |
| 235 | `backend/app/services/release_service.py` | `02_backend` | PHASE 2 | Python Source | 538 | `PENDING` |
| 236 | `backend/app/services/security_scanner.py` | `02_backend` | PHASE 2 | Python Source | 470 | `PENDING` |
| 237 | `backend/app/services/slot_engine.py` | `02_backend` | PHASE 2 | Python Source | 313 | `PENDING` |
| 238 | `backend/app/services/soap_note.py` | `02_backend` | PHASE 2 | Python Source | 248 | `PENDING` |
| 239 | `backend/app/services/terminology_validator.py` | `02_backend` | PHASE 2 | Python Source | 831 | `PENDING` |
| 240 | `backend/app/services/websocket_manager.py` | `02_backend` | PHASE 2 | Python Source | 472 | `PENDING` |
| 241 | `backend/app/services/workflow_isolation_service.py` | `02_backend` | PHASE 2 | Python Source | 436 | `PENDING` |
| 242 | `backend/docker-entrypoint.sh` | `02_backend` | PHASE 2 | Backend Asset | 32 | `PENDING` |
| 243 | `backend/pytest.ini` | `02_backend` | PHASE 2 | Backend Asset | 9 | `PENDING` |
| 244 | `frontend/public/apple-touch-icon.png` | `03_frontend` | PHASE 3 | Binary (PNG) | 0 | `CATALOGED-ONLY` |
| 245 | `frontend/public/favicon.ico` | `03_frontend` | PHASE 3 | Binary (ICO) | 0 | `CATALOGED-ONLY` |
| 246 | `frontend/public/file.svg` | `03_frontend` | PHASE 3 | Binary (SVG) | 0 | `CATALOGED-ONLY` |
| 247 | `frontend/public/globe.svg` | `03_frontend` | PHASE 3 | Binary (SVG) | 0 | `CATALOGED-ONLY` |
| 248 | `frontend/public/icon-192.png` | `03_frontend` | PHASE 3 | Binary (PNG) | 0 | `CATALOGED-ONLY` |
| 249 | `frontend/public/icon-512.png` | `03_frontend` | PHASE 3 | Binary (PNG) | 0 | `CATALOGED-ONLY` |
| 250 | `frontend/public/icon.png` | `03_frontend` | PHASE 3 | Binary (PNG) | 0 | `CATALOGED-ONLY` |
| 251 | `frontend/public/logo.png` | `03_frontend` | PHASE 3 | Binary (PNG) | 0 | `CATALOGED-ONLY` |
| 252 | `frontend/public/next.svg` | `03_frontend` | PHASE 3 | Binary (SVG) | 0 | `CATALOGED-ONLY` |
| 253 | `frontend/public/vercel.svg` | `03_frontend` | PHASE 3 | Binary (SVG) | 0 | `CATALOGED-ONLY` |
| 254 | `frontend/public/window.svg` | `03_frontend` | PHASE 3 | Binary (SVG) | 0 | `CATALOGED-ONLY` |
| 255 | `frontend/src/app/admin/page.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 172 | `PENDING` |
| 256 | `frontend/src/app/api/health/route.ts` | `03_frontend` | PHASE 3 | Frontend Source | 57 | `PENDING` |
| 257 | `frontend/src/app/doctor/page.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 882 | `PENDING` |
| 258 | `frontend/src/app/favicon.ico` | `03_frontend` | PHASE 3 | Binary (ICO) | 0 | `CATALOGED-ONLY` |
| 259 | `frontend/src/app/fhir/page.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 965 | `PENDING` |
| 260 | `frontend/src/app/globals.css` | `03_frontend` | PHASE 3 | Frontend Source | 288 | `PENDING` |
| 261 | `frontend/src/app/icon.png` | `03_frontend` | PHASE 3 | Binary (PNG) | 0 | `CATALOGED-ONLY` |
| 262 | `frontend/src/app/lab/page.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 872 | `PENDING` |
| 263 | `frontend/src/app/layout.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 43 | `PENDING` |
| 264 | `frontend/src/app/login/page.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 68 | `PENDING` |
| 265 | `frontend/src/app/page.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 519 | `PENDING` |
| 266 | `frontend/src/app/patient/page.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 1294 | `PENDING` |
| 267 | `frontend/src/app/privacy/page.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 222 | `PENDING` |
| 268 | `frontend/src/app/register/page.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 260 | `PENDING` |
| 269 | `frontend/src/app/terms/page.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 186 | `PENDING` |
| 270 | `frontend/src/components/appointments/AppointmentBookingModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 367 | `PENDING` |
| 271 | `frontend/src/components/appointments/ClinicalSlotPicker.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 589 | `PENDING` |
| 272 | `frontend/src/components/appointments/DoctorSlotManager.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 522 | `PENDING` |
| 273 | `frontend/src/components/appointments/SlotHoldCountdown.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 124 | `PENDING` |
| 274 | `frontend/src/components/appointments/index.ts` | `03_frontend` | PHASE 3 | Frontend Source | 8 | `PENDING` |
| 275 | `frontend/src/components/clinical/AbdmGatewayStatusCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 220 | `PENDING` |
| 276 | `frontend/src/components/clinical/AcademicMonographViewerCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 518 | `PENDING` |
| 277 | `frontend/src/components/clinical/AdministrativeHierarchyViewerCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 810 | `PENDING` |
| 278 | `frontend/src/components/clinical/AsvsComplianceShieldCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 553 | `PENDING` |
| 279 | `frontend/src/components/clinical/AuditLedgerVerificationCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 458 | `PENDING` |
| 280 | `frontend/src/components/clinical/BreakTheGlassModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 497 | `PENDING` |
| 281 | `frontend/src/components/clinical/CDSAlertBanner.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 334 | `PENDING` |
| 282 | `frontend/src/components/clinical/CareContextLinkageModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 525 | `PENDING` |
| 283 | `frontend/src/components/clinical/ChainOfCommandDelegationCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 678 | `PENDING` |
| 284 | `frontend/src/components/clinical/ChildAbhaBindingCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 525 | `PENDING` |
| 285 | `frontend/src/components/clinical/ClinicalAlertToastSystem.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 396 | `PENDING` |
| 286 | `frontend/src/components/clinical/ClinicalQuickActionRail.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 145 | `PENDING` |
| 287 | `frontend/src/components/clinical/ClinicianConsultationQueue.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 572 | `PENDING` |
| 288 | `frontend/src/components/clinical/ContainerRuntimeCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 454 | `PENDING` |
| 289 | `frontend/src/components/clinical/DiagnosticOrderTracker.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 937 | `PENDING` |
| 290 | `frontend/src/components/clinical/DockerOrchestrationCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 372 | `PENDING` |
| 291 | `frontend/src/components/clinical/EdgeNodeSyncCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 300 | `PENDING` |
| 292 | `frontend/src/components/clinical/ExpressOpdConsole.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 683 | `PENDING` |
| 293 | `frontend/src/components/clinical/FamilyProxyRelationshipCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 573 | `PENDING` |
| 294 | `frontend/src/components/clinical/FrontendContainerCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 347 | `PENDING` |
| 295 | `frontend/src/components/clinical/GuardianConsentDelegationCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 853 | `PENDING` |
| 296 | `frontend/src/components/clinical/HipBridgeConsoleCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 563 | `PENDING` |
| 297 | `frontend/src/components/clinical/HprOnboardingCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 308 | `PENDING` |
| 298 | `frontend/src/components/clinical/InteractiveDemoSandboxCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 671 | `PENDING` |
| 299 | `frontend/src/components/clinical/LegacyHisFederationCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 660 | `PENDING` |
| 300 | `frontend/src/components/clinical/MedicationCatalogBrowser.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 824 | `PENDING` |
| 301 | `frontend/src/components/clinical/MultiGuardianConflictResolutionCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 684 | `PENDING` |
| 302 | `frontend/src/components/clinical/PacsViewerModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 1061 | `PENDING` |
| 303 | `frontend/src/components/clinical/PatientDemographicBanner.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 329 | `PENDING` |
| 304 | `frontend/src/components/clinical/PatientDiscoverySimulatorModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 404 | `PENDING` |
| 305 | `frontend/src/components/clinical/PerformanceBenchmarkCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 510 | `PENDING` |
| 306 | `frontend/src/components/clinical/PharmacyDispenseModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 414 | `PENDING` |
| 307 | `frontend/src/components/clinical/PlatformComparisonViewerCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 628 | `PENDING` |
| 308 | `frontend/src/components/clinical/PrescriptionAuthoringPad.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 1688 | `PENDING` |
| 309 | `frontend/src/components/clinical/ProblemListPanel.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 510 | `PENDING` |
| 310 | `frontend/src/components/clinical/ProductionReleaseCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 346 | `PENDING` |
| 311 | `frontend/src/components/clinical/SecurityScanReportCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 674 | `PENDING` |
| 312 | `frontend/src/components/clinical/SoapNoteEditor.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 924 | `PENDING` |
| 313 | `frontend/src/components/clinical/SystemAuditLicenseCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 513 | `PENDING` |
| 314 | `frontend/src/components/clinical/TerritorialCommandCenterCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 856 | `PENDING` |
| 315 | `frontend/src/components/clinical/VitalsTelemetryPanel.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 414 | `PENDING` |
| 316 | `frontend/src/components/clinical/index.ts` | `03_frontend` | PHASE 3 | Frontend Source | 110 | `PENDING` |
| 317 | `frontend/src/components/common/BrandLogo.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 84 | `PENDING` |
| 318 | `frontend/src/components/common/NationalEmblem.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 64 | `PENDING` |
| 319 | `frontend/src/components/gateway/UniversalNationalGatewayCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 886 | `PENDING` |
| 320 | `frontend/src/components/gateway/index.ts` | `03_frontend` | PHASE 3 | Frontend Source | 3 | `PENDING` |
| 321 | `frontend/src/components/layout/AccessibilityBar.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 333 | `PENDING` |
| 322 | `frontend/src/components/layout/AppShell.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 49 | `PENDING` |
| 323 | `frontend/src/components/layout/Footer.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 116 | `PENDING` |
| 324 | `frontend/src/components/layout/MobileNav.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 155 | `PENDING` |
| 325 | `frontend/src/components/layout/Navbar.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 138 | `PENDING` |
| 326 | `frontend/src/components/layout/SystemStatusBar.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 85 | `PENDING` |
| 327 | `frontend/src/components/layout/index.ts` | `03_frontend` | PHASE 3 | Frontend Source | 6 | `PENDING` |
| 328 | `frontend/src/components/patient/AadhaarOtpVerificationModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 387 | `PENDING` |
| 329 | `frontend/src/components/patient/AbhaCardExportModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 462 | `PENDING` |
| 330 | `frontend/src/components/patient/AbhaCreationModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 554 | `PENDING` |
| 331 | `frontend/src/components/patient/AbhaQrVerificationModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 425 | `PENDING` |
| 332 | `frontend/src/components/patient/BloodPressureChart.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 317 | `PENDING` |
| 333 | `frontend/src/components/patient/CalcomDependentSwitcher.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 204 | `PENDING` |
| 334 | `frontend/src/components/patient/DigiLockerAuthCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 305 | `PENDING` |
| 335 | `frontend/src/components/patient/DigitalAbhaCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 441 | `PENDING` |
| 336 | `frontend/src/components/patient/DpiActiveMedicinesTile.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 264 | `PENDING` |
| 337 | `frontend/src/components/patient/DpiHealthIdTile.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 213 | `PENDING` |
| 338 | `frontend/src/components/patient/DpiPastVisitsTile.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 199 | `PENDING` |
| 339 | `frontend/src/components/patient/DpiQrCheckInModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 141 | `PENDING` |
| 340 | `frontend/src/components/patient/GeriatricCareAssessmentCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 176 | `PENDING` |
| 341 | `frontend/src/components/patient/PatientConditionCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 200 | `PENDING` |
| 342 | `frontend/src/components/patient/PatientConditionUpdateModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 258 | `PENDING` |
| 343 | `frontend/src/components/patient/PatientHeader.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 99 | `PENDING` |
| 344 | `frontend/src/components/patient/PatientMetricsBar.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 133 | `PENDING` |
| 345 | `frontend/src/components/patient/PatientModals.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 549 | `PENDING` |
| 346 | `frontend/src/components/patient/PatientNavTabs.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 61 | `PENDING` |
| 347 | `frontend/src/components/patient/PatientOverviewTab.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 472 | `PENDING` |
| 348 | `frontend/src/components/patient/PatientPasswordlessAuthCard.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 611 | `PENDING` |
| 349 | `frontend/src/components/patient/PatientPrescriptionsTab.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 204 | `PENDING` |
| 350 | `frontend/src/components/patient/PatientProblemsTab.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 273 | `PENDING` |
| 351 | `frontend/src/components/patient/PatientRecordsTab.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 533 | `PENDING` |
| 352 | `frontend/src/components/patient/PatientVitalsTelemetry.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 350 | `PENDING` |
| 353 | `frontend/src/components/patient/PediatricImmunizationTimeline.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 274 | `PENDING` |
| 354 | `frontend/src/components/patient/TelemedicineReadinessModal.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 322 | `PENDING` |
| 355 | `frontend/src/components/patient/VitalsMetricChart.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 383 | `PENDING` |
| 356 | `frontend/src/components/patient/index.ts` | `03_frontend` | PHASE 3 | Frontend Source | 29 | `PENDING` |
| 357 | `frontend/src/components/ui/Alert.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 59 | `PENDING` |
| 358 | `frontend/src/components/ui/Badge.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 90 | `PENDING` |
| 359 | `frontend/src/components/ui/Button.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 64 | `PENDING` |
| 360 | `frontend/src/components/ui/Card.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 107 | `PENDING` |
| 361 | `frontend/src/components/ui/Input.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 69 | `PENDING` |
| 362 | `frontend/src/components/ui/NavPillGroup.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 84 | `PENDING` |
| 363 | `frontend/src/components/ui/index.ts` | `03_frontend` | PHASE 3 | Frontend Source | 6 | `PENDING` |
| 364 | `frontend/src/config/navigation.ts` | `03_frontend` | PHASE 3 | Frontend Source | 85 | `PENDING` |
| 365 | `frontend/src/context/AccessibilityContext.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 176 | `PENDING` |
| 366 | `frontend/src/context/AuthContext.tsx` | `03_frontend` | PHASE 3 | Frontend Source | 233 | `PENDING` |
| 367 | `frontend/src/hooks/useClinicalNotificationsWebSocket.ts` | `03_frontend` | PHASE 3 | Frontend Source | 281 | `PENDING` |
| 368 | `frontend/src/hooks/useOpdQueueWebSocket.ts` | `03_frontend` | PHASE 3 | Frontend Source | 175 | `PENDING` |
| 369 | `frontend/src/lib/api.ts` | `03_frontend` | PHASE 3 | Frontend Source | 1909 | `PENDING` |
| 370 | `frontend/src/lib/conditions.ts` | `03_frontend` | PHASE 3 | Frontend Source | 371 | `PENDING` |
| 371 | `frontend/src/lib/i18n/dictionary.ts` | `03_frontend` | PHASE 3 | Frontend Source | 252 | `PENDING` |
| 372 | `frontend/src/lib/offlineQueue.ts` | `03_frontend` | PHASE 3 | Frontend Source | 92 | `PENDING` |
| 373 | `frontend/src/lib/qr.ts` | `03_frontend` | PHASE 3 | Frontend Source | 131 | `PENDING` |
| 374 | `frontend/src/lib/utils.ts` | `03_frontend` | PHASE 3 | Frontend Source | 9 | `PENDING` |
| 375 | `frontend/src/lib/vitals.ts` | `03_frontend` | PHASE 3 | Frontend Source | 331 | `PENDING` |
| 376 | `frontend/src/middleware.ts` | `03_frontend` | PHASE 3 | Frontend Source | 79 | `PENDING` |
| 377 | `.gsd/DEFECT-ANALYSIS.md` | `04_docs` | PHASE 4 | Documentation / Log | 40 | `PENDING` |
| 378 | `.gsd/FRONTEND-AUDIT.md` | `04_docs` | PHASE 4 | Documentation / Log | 190 | `PENDING` |
| 379 | `.gsd/ROADMAP.md` | `04_docs` | PHASE 4 | Documentation / Log | 97 | `PENDING` |
| 380 | `.gsd/STATE.md` | `04_docs` | PHASE 4 | Documentation / Log | 47 | `PENDING` |
| 381 | `.gsd/examples/cross-platform.md` | `04_docs` | PHASE 4 | Documentation / Log | 99 | `PENDING` |
| 382 | `.gsd/examples/multi-wave-workflow.md` | `04_docs` | PHASE 4 | Documentation / Log | 256 | `PENDING` |
| 383 | `.gsd/examples/quick-reference.md` | `04_docs` | PHASE 4 | Documentation / Log | 73 | `PENDING` |
| 384 | `.gsd/examples/workflow-example.md` | `04_docs` | PHASE 4 | Documentation / Log | 139 | `PENDING` |
| 385 | `.gsd/milestones/ux4g-SUMMARY.md` | `04_docs` | PHASE 4 | Documentation / Log | 69 | `PENDING` |
| 386 | `.gsd/templates/DEBUG.md` | `04_docs` | PHASE 4 | Documentation / Log | 123 | `PENDING` |
| 387 | `.gsd/templates/PLAN.md` | `04_docs` | PHASE 4 | Documentation / Log | 90 | `PENDING` |
| 388 | `.gsd/templates/RESEARCH.md` | `04_docs` | PHASE 4 | Documentation / Log | 75 | `PENDING` |
| 389 | `.gsd/templates/SUMMARY.md` | `04_docs` | PHASE 4 | Documentation / Log | 103 | `PENDING` |
| 390 | `.gsd/templates/UAT.md` | `04_docs` | PHASE 4 | Documentation / Log | 168 | `PENDING` |
| 391 | `.gsd/templates/VERIFICATION.md` | `04_docs` | PHASE 4 | Documentation / Log | 70 | `PENDING` |
| 392 | `.gsd/templates/architecture.md` | `04_docs` | PHASE 4 | Documentation / Log | 67 | `PENDING` |
| 393 | `.gsd/templates/context.md` | `04_docs` | PHASE 4 | Documentation / Log | 91 | `PENDING` |
| 394 | `.gsd/templates/decisions.md` | `04_docs` | PHASE 4 | Documentation / Log | 37 | `PENDING` |
| 395 | `.gsd/templates/discovery.md` | `04_docs` | PHASE 4 | Documentation / Log | 122 | `PENDING` |
| 396 | `.gsd/templates/journal.md` | `04_docs` | PHASE 4 | Documentation / Log | 46 | `PENDING` |
| 397 | `.gsd/templates/milestone.md` | `04_docs` | PHASE 4 | Documentation / Log | 91 | `PENDING` |
| 398 | `.gsd/templates/phase-summary.md` | `04_docs` | PHASE 4 | Documentation / Log | 52 | `PENDING` |
| 399 | `.gsd/templates/project.md` | `04_docs` | PHASE 4 | Documentation / Log | 124 | `PENDING` |
| 400 | `.gsd/templates/requirements.md` | `04_docs` | PHASE 4 | Documentation / Log | 92 | `PENDING` |
| 401 | `.gsd/templates/roadmap.md` | `04_docs` | PHASE 4 | Documentation / Log | 103 | `PENDING` |
| 402 | `.gsd/templates/spec.md` | `04_docs` | PHASE 4 | Documentation / Log | 51 | `PENDING` |
| 403 | `.gsd/templates/sprint.md` | `04_docs` | PHASE 4 | Documentation / Log | 57 | `PENDING` |
| 404 | `.gsd/templates/stack.md` | `04_docs` | PHASE 4 | Documentation / Log | 62 | `PENDING` |
| 405 | `.gsd/templates/state.md` | `04_docs` | PHASE 4 | Documentation / Log | 92 | `PENDING` |
| 406 | `.gsd/templates/state_snapshot.md` | `04_docs` | PHASE 4 | Documentation / Log | 132 | `PENDING` |
| 407 | `.gsd/templates/todo.md` | `04_docs` | PHASE 4 | Documentation / Log | 32 | `PENDING` |
| 408 | `.gsd/templates/token_report.md` | `04_docs` | PHASE 4 | Documentation / Log | 79 | `PENDING` |
| 409 | `.gsd/templates/user-setup.md` | `04_docs` | PHASE 4 | Documentation / Log | 116 | `PENDING` |
| 410 | `NIRMAYA_Interim_Project_Report_Month_1.docx` | `04_docs` | PHASE 4 | Binary (DOCX) | 0 | `CATALOGED-ONLY` |
| 411 | `README.md` | `04_docs` | PHASE 4 | Documentation / Log | 227 | `PENDING` |
| 412 | `RELEASE_NOTES_v1.0.0.md` | `04_docs` | PHASE 4 | Documentation / Log | 130 | `PENDING` |
| 413 | `RELEASE_NOTES_v1.1.0.md` | `04_docs` | PHASE 4 | Documentation / Log | 165 | `PENDING` |
| 414 | `RELEASE_NOTES_v1.2.0.md` | `04_docs` | PHASE 4 | Documentation / Log | 99 | `PENDING` |
| 415 | `docs/ARCHITECTURE.md` | `04_docs` | PHASE 4 | Documentation / Log | 284 | `PENDING` |
| 416 | `docs/CHANGELOG.md` | `04_docs` | PHASE 4 | Documentation / Log | 2761 | `PENDING` |
| 417 | `docs/README.md` | `04_docs` | PHASE 4 | Documentation / Log | 163 | `PENDING` |
| 418 | `docs/SUMMARY.md` | `04_docs` | PHASE 4 | Documentation / Log | 179 | `PENDING` |
| 419 | `docs/academic/latex/nirmaya_ieee_manuscript.tex` | `04_docs` | PHASE 4 | Documentation / Log | 551 | `PENDING` |
| 420 | `docs/academic/latex/references.bib` | `04_docs` | PHASE 4 | Documentation / Log | 251 | `PENDING` |
| 421 | `docs/academic/nirmaya-ieee-research-paper.md` | `04_docs` | PHASE 4 | Documentation / Log | 527 | `PENDING` |
| 422 | `docs/assets/favicon.ico` | `04_docs` | PHASE 4 | Binary (ICO) | 0 | `CATALOGED-ONLY` |
| 423 | `docs/assets/icon-192.png` | `04_docs` | PHASE 4 | Binary (PNG) | 0 | `CATALOGED-ONLY` |
| 424 | `docs/assets/icon-512.png` | `04_docs` | PHASE 4 | Binary (PNG) | 0 | `CATALOGED-ONLY` |
| 425 | `docs/assets/logo.png` | `04_docs` | PHASE 4 | Binary (PNG) | 0 | `CATALOGED-ONLY` |
| 426 | `docs/assets/nirmaya-mockup.png` | `04_docs` | PHASE 4 | Binary (PNG) | 0 | `CATALOGED-ONLY` |
| 427 | `docs/design.md` | `04_docs` | PHASE 4 | Documentation / Log | 94 | `PENDING` |
| 428 | `docs/faq/finalized-system-architecture.md` | `04_docs` | PHASE 4 | Documentation / Log | 250 | `PENDING` |
| 429 | `docs/faq/medical-practitioner-verification.md` | `04_docs` | PHASE 4 | Documentation / Log | 174 | `PENDING` |
| 430 | `docs/gitbook-docs.yaml` | `04_docs` | PHASE 4 | Documentation / Log | 12 | `PENDING` |
| 431 | `docs/journey/month-1/architecture-audit.md` | `04_docs` | PHASE 4 | Documentation / Log | 64 | `PENDING` |
| 432 | `docs/journey/month-1/calcom-design-system-migration.md` | `04_docs` | PHASE 4 | Documentation / Log | 70 | `PENDING` |
| 433 | `docs/journey/month-1/day-1.md` | `04_docs` | PHASE 4 | Documentation / Log | 56 | `PENDING` |
| 434 | `docs/journey/month-1/day-10.md` | `04_docs` | PHASE 4 | Documentation / Log | 145 | `PENDING` |
| 435 | `docs/journey/month-1/day-11.md` | `04_docs` | PHASE 4 | Documentation / Log | 120 | `PENDING` |
| 436 | `docs/journey/month-1/day-12.md` | `04_docs` | PHASE 4 | Documentation / Log | 128 | `PENDING` |
| 437 | `docs/journey/month-1/day-13.md` | `04_docs` | PHASE 4 | Documentation / Log | 115 | `PENDING` |
| 438 | `docs/journey/month-1/day-14.md` | `04_docs` | PHASE 4 | Documentation / Log | 82 | `PENDING` |
| 439 | `docs/journey/month-1/day-15.md` | `04_docs` | PHASE 4 | Documentation / Log | 145 | `PENDING` |
| 440 | `docs/journey/month-1/day-16.md` | `04_docs` | PHASE 4 | Documentation / Log | 104 | `PENDING` |
| 441 | `docs/journey/month-1/day-17.md` | `04_docs` | PHASE 4 | Documentation / Log | 122 | `PENDING` |
| 442 | `docs/journey/month-1/day-18.md` | `04_docs` | PHASE 4 | Documentation / Log | 132 | `PENDING` |
| 443 | `docs/journey/month-1/day-19.md` | `04_docs` | PHASE 4 | Documentation / Log | 106 | `PENDING` |
| 444 | `docs/journey/month-1/day-2.md` | `04_docs` | PHASE 4 | Documentation / Log | 47 | `PENDING` |
| 445 | `docs/journey/month-1/day-20.md` | `04_docs` | PHASE 4 | Documentation / Log | 153 | `PENDING` |
| 446 | `docs/journey/month-1/day-3.md` | `04_docs` | PHASE 4 | Documentation / Log | 54 | `PENDING` |
| 447 | `docs/journey/month-1/day-4.md` | `04_docs` | PHASE 4 | Documentation / Log | 46 | `PENDING` |
| 448 | `docs/journey/month-1/day-5.md` | `04_docs` | PHASE 4 | Documentation / Log | 88 | `PENDING` |
| 449 | `docs/journey/month-1/day-6.md` | `04_docs` | PHASE 4 | Documentation / Log | 107 | `PENDING` |
| 450 | `docs/journey/month-1/day-7.md` | `04_docs` | PHASE 4 | Documentation / Log | 81 | `PENDING` |
| 451 | `docs/journey/month-1/day-8.md` | `04_docs` | PHASE 4 | Documentation / Log | 131 | `PENDING` |
| 452 | `docs/journey/month-1/day-9.md` | `04_docs` | PHASE 4 | Documentation / Log | 175 | `PENDING` |
| 453 | `docs/journey/month-1/month-1-retrospective.md` | `04_docs` | PHASE 4 | Documentation / Log | 193 | `PENDING` |
| 454 | `docs/journey/month-1/overview.md` | `04_docs` | PHASE 4 | Documentation / Log | 33 | `PENDING` |
| 455 | `docs/journey/month-1/week-1-2-executive-audit.md` | `04_docs` | PHASE 4 | Documentation / Log | 210 | `PENDING` |
| 456 | `docs/journey/month-1/week-1-3-codebase-audit.md` | `04_docs` | PHASE 4 | Documentation / Log | 147 | `PENDING` |
| 457 | `docs/journey/month-1/week-1-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 100 | `PENDING` |
| 458 | `docs/journey/month-1/week-1.md` | `04_docs` | PHASE 4 | Documentation / Log | 24 | `PENDING` |
| 459 | `docs/journey/month-1/week-2-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 104 | `PENDING` |
| 460 | `docs/journey/month-1/week-2.md` | `04_docs` | PHASE 4 | Documentation / Log | 24 | `PENDING` |
| 461 | `docs/journey/month-1/week-3-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 109 | `PENDING` |
| 462 | `docs/journey/month-1/week-3.md` | `04_docs` | PHASE 4 | Documentation / Log | 23 | `PENDING` |
| 463 | `docs/journey/month-1/week-4-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 99 | `PENDING` |
| 464 | `docs/journey/month-1/week-4.md` | `04_docs` | PHASE 4 | Documentation / Log | 34 | `PENDING` |
| 465 | `docs/journey/month-2/day-21.md` | `04_docs` | PHASE 4 | Documentation / Log | 61 | `PENDING` |
| 466 | `docs/journey/month-2/day-22.md` | `04_docs` | PHASE 4 | Documentation / Log | 88 | `PENDING` |
| 467 | `docs/journey/month-2/day-23.md` | `04_docs` | PHASE 4 | Documentation / Log | 92 | `PENDING` |
| 468 | `docs/journey/month-2/day-24.md` | `04_docs` | PHASE 4 | Documentation / Log | 99 | `PENDING` |
| 469 | `docs/journey/month-2/day-25.md` | `04_docs` | PHASE 4 | Documentation / Log | 110 | `PENDING` |
| 470 | `docs/journey/month-2/day-26.md` | `04_docs` | PHASE 4 | Documentation / Log | 93 | `PENDING` |
| 471 | `docs/journey/month-2/day-27.md` | `04_docs` | PHASE 4 | Documentation / Log | 111 | `PENDING` |
| 472 | `docs/journey/month-2/day-28.md` | `04_docs` | PHASE 4 | Documentation / Log | 71 | `PENDING` |
| 473 | `docs/journey/month-2/day-29.md` | `04_docs` | PHASE 4 | Documentation / Log | 95 | `PENDING` |
| 474 | `docs/journey/month-2/day-30.md` | `04_docs` | PHASE 4 | Documentation / Log | 162 | `PENDING` |
| 475 | `docs/journey/month-2/day-31.md` | `04_docs` | PHASE 4 | Documentation / Log | 97 | `PENDING` |
| 476 | `docs/journey/month-2/day-32.md` | `04_docs` | PHASE 4 | Documentation / Log | 115 | `PENDING` |
| 477 | `docs/journey/month-2/day-33.md` | `04_docs` | PHASE 4 | Documentation / Log | 86 | `PENDING` |
| 478 | `docs/journey/month-2/day-34.md` | `04_docs` | PHASE 4 | Documentation / Log | 95 | `PENDING` |
| 479 | `docs/journey/month-2/day-35.md` | `04_docs` | PHASE 4 | Documentation / Log | 96 | `PENDING` |
| 480 | `docs/journey/month-2/day-36.md` | `04_docs` | PHASE 4 | Documentation / Log | 94 | `PENDING` |
| 481 | `docs/journey/month-2/day-37.md` | `04_docs` | PHASE 4 | Documentation / Log | 98 | `PENDING` |
| 482 | `docs/journey/month-2/day-38.md` | `04_docs` | PHASE 4 | Documentation / Log | 108 | `PENDING` |
| 483 | `docs/journey/month-2/day-39.md` | `04_docs` | PHASE 4 | Documentation / Log | 104 | `PENDING` |
| 484 | `docs/journey/month-2/day-40.md` | `04_docs` | PHASE 4 | Documentation / Log | 111 | `PENDING` |
| 485 | `docs/journey/month-2/month-2-retrospective.md` | `04_docs` | PHASE 4 | Documentation / Log | 216 | `PENDING` |
| 486 | `docs/journey/month-2/overview.md` | `04_docs` | PHASE 4 | Documentation / Log | 70 | `PENDING` |
| 487 | `docs/journey/month-2/week-5-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 120 | `PENDING` |
| 488 | `docs/journey/month-2/week-5.md` | `04_docs` | PHASE 4 | Documentation / Log | 32 | `PENDING` |
| 489 | `docs/journey/month-2/week-6-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 111 | `PENDING` |
| 490 | `docs/journey/month-2/week-6.md` | `04_docs` | PHASE 4 | Documentation / Log | 25 | `PENDING` |
| 491 | `docs/journey/month-2/week-7-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 120 | `PENDING` |
| 492 | `docs/journey/month-2/week-7.md` | `04_docs` | PHASE 4 | Documentation / Log | 23 | `PENDING` |
| 493 | `docs/journey/month-2/week-8-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 111 | `PENDING` |
| 494 | `docs/journey/month-2/week-8.md` | `04_docs` | PHASE 4 | Documentation / Log | 23 | `PENDING` |
| 495 | `docs/journey/month-3/day-41.md` | `04_docs` | PHASE 4 | Documentation / Log | 117 | `PENDING` |
| 496 | `docs/journey/month-3/day-42.md` | `04_docs` | PHASE 4 | Documentation / Log | 100 | `PENDING` |
| 497 | `docs/journey/month-3/day-43.md` | `04_docs` | PHASE 4 | Documentation / Log | 90 | `PENDING` |
| 498 | `docs/journey/month-3/day-44.md` | `04_docs` | PHASE 4 | Documentation / Log | 93 | `PENDING` |
| 499 | `docs/journey/month-3/day-45.md` | `04_docs` | PHASE 4 | Documentation / Log | 105 | `PENDING` |
| 500 | `docs/journey/month-3/day-46.md` | `04_docs` | PHASE 4 | Documentation / Log | 95 | `PENDING` |
| 501 | `docs/journey/month-3/day-47.md` | `04_docs` | PHASE 4 | Documentation / Log | 100 | `PENDING` |
| 502 | `docs/journey/month-3/day-48.md` | `04_docs` | PHASE 4 | Documentation / Log | 121 | `PENDING` |
| 503 | `docs/journey/month-3/day-49.md` | `04_docs` | PHASE 4 | Documentation / Log | 161 | `PENDING` |
| 504 | `docs/journey/month-3/day-50.md` | `04_docs` | PHASE 4 | Documentation / Log | 124 | `PENDING` |
| 505 | `docs/journey/month-3/day-51.md` | `04_docs` | PHASE 4 | Documentation / Log | 87 | `PENDING` |
| 506 | `docs/journey/month-3/day-52.md` | `04_docs` | PHASE 4 | Documentation / Log | 94 | `PENDING` |
| 507 | `docs/journey/month-3/day-53.md` | `04_docs` | PHASE 4 | Documentation / Log | 88 | `PENDING` |
| 508 | `docs/journey/month-3/day-54.md` | `04_docs` | PHASE 4 | Documentation / Log | 100 | `PENDING` |
| 509 | `docs/journey/month-3/day-55.md` | `04_docs` | PHASE 4 | Documentation / Log | 119 | `PENDING` |
| 510 | `docs/journey/month-3/day-56.md` | `04_docs` | PHASE 4 | Documentation / Log | 151 | `PENDING` |
| 511 | `docs/journey/month-3/day-57.md` | `04_docs` | PHASE 4 | Documentation / Log | 139 | `PENDING` |
| 512 | `docs/journey/month-3/day-58.md` | `04_docs` | PHASE 4 | Documentation / Log | 134 | `PENDING` |
| 513 | `docs/journey/month-3/day-59.md` | `04_docs` | PHASE 4 | Documentation / Log | 137 | `PENDING` |
| 514 | `docs/journey/month-3/day-60.md` | `04_docs` | PHASE 4 | Documentation / Log | 137 | `PENDING` |
| 515 | `docs/journey/month-3/month-3-retrospective.md` | `04_docs` | PHASE 4 | Documentation / Log | 253 | `PENDING` |
| 516 | `docs/journey/month-3/overview.md` | `04_docs` | PHASE 4 | Documentation / Log | 24 | `PENDING` |
| 517 | `docs/journey/month-3/week-10-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 94 | `PENDING` |
| 518 | `docs/journey/month-3/week-10.md` | `04_docs` | PHASE 4 | Documentation / Log | 23 | `PENDING` |
| 519 | `docs/journey/month-3/week-11-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 111 | `PENDING` |
| 520 | `docs/journey/month-3/week-11.md` | `04_docs` | PHASE 4 | Documentation / Log | 23 | `PENDING` |
| 521 | `docs/journey/month-3/week-12-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 124 | `PENDING` |
| 522 | `docs/journey/month-3/week-12.md` | `04_docs` | PHASE 4 | Documentation / Log | 66 | `PENDING` |
| 523 | `docs/journey/month-3/week-9-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 112 | `PENDING` |
| 524 | `docs/journey/month-3/week-9.md` | `04_docs` | PHASE 4 | Documentation / Log | 23 | `PENDING` |
| 525 | `docs/journey/month-4/day-61.md` | `04_docs` | PHASE 4 | Documentation / Log | 123 | `PENDING` |
| 526 | `docs/journey/month-4/day-62.md` | `04_docs` | PHASE 4 | Documentation / Log | 116 | `PENDING` |
| 527 | `docs/journey/month-4/day-63.md` | `04_docs` | PHASE 4 | Documentation / Log | 156 | `PENDING` |
| 528 | `docs/journey/month-4/day-64.md` | `04_docs` | PHASE 4 | Documentation / Log | 144 | `PENDING` |
| 529 | `docs/journey/month-4/day-65.md` | `04_docs` | PHASE 4 | Documentation / Log | 147 | `PENDING` |
| 530 | `docs/journey/month-4/day-66.md` | `04_docs` | PHASE 4 | Documentation / Log | 96 | `PENDING` |
| 531 | `docs/journey/month-4/day-67.md` | `04_docs` | PHASE 4 | Documentation / Log | 94 | `PENDING` |
| 532 | `docs/journey/month-4/day-68.md` | `04_docs` | PHASE 4 | Documentation / Log | 91 | `PENDING` |
| 533 | `docs/journey/month-4/day-69.md` | `04_docs` | PHASE 4 | Documentation / Log | 119 | `PENDING` |
| 534 | `docs/journey/month-4/day-70.md` | `04_docs` | PHASE 4 | Documentation / Log | 87 | `PENDING` |
| 535 | `docs/journey/month-4/day-71.md` | `04_docs` | PHASE 4 | Documentation / Log | 96 | `PENDING` |
| 536 | `docs/journey/month-4/day-72.md` | `04_docs` | PHASE 4 | Documentation / Log | 82 | `PENDING` |
| 537 | `docs/journey/month-4/day-73.md` | `04_docs` | PHASE 4 | Documentation / Log | 101 | `PENDING` |
| 538 | `docs/journey/month-4/day-74.md` | `04_docs` | PHASE 4 | Documentation / Log | 108 | `PENDING` |
| 539 | `docs/journey/month-4/day-75.md` | `04_docs` | PHASE 4 | Documentation / Log | 75 | `PENDING` |
| 540 | `docs/journey/month-4/day-76.md` | `04_docs` | PHASE 4 | Documentation / Log | 83 | `PENDING` |
| 541 | `docs/journey/month-4/day-77.md` | `04_docs` | PHASE 4 | Documentation / Log | 79 | `PENDING` |
| 542 | `docs/journey/month-4/day-78.md` | `04_docs` | PHASE 4 | Documentation / Log | 83 | `PENDING` |
| 543 | `docs/journey/month-4/day-79.md` | `04_docs` | PHASE 4 | Documentation / Log | 94 | `PENDING` |
| 544 | `docs/journey/month-4/day-80.md` | `04_docs` | PHASE 4 | Documentation / Log | 93 | `PENDING` |
| 545 | `docs/journey/month-4/day-81.md` | `04_docs` | PHASE 4 | Documentation / Log | 76 | `PENDING` |
| 546 | `docs/journey/month-4/day-82.md` | `04_docs` | PHASE 4 | Documentation / Log | 63 | `PENDING` |
| 547 | `docs/journey/month-4/day-83.md` | `04_docs` | PHASE 4 | Documentation / Log | 72 | `PENDING` |
| 548 | `docs/journey/month-4/day-84.md` | `04_docs` | PHASE 4 | Documentation / Log | 73 | `PENDING` |
| 549 | `docs/journey/month-4/day-85.md` | `04_docs` | PHASE 4 | Documentation / Log | 110 | `PENDING` |
| 550 | `docs/journey/month-4/day-86.md` | `04_docs` | PHASE 4 | Documentation / Log | 126 | `PENDING` |
| 551 | `docs/journey/month-4/day-87.md` | `04_docs` | PHASE 4 | Documentation / Log | 103 | `PENDING` |
| 552 | `docs/journey/month-4/day-88.md` | `04_docs` | PHASE 4 | Documentation / Log | 117 | `PENDING` |
| 553 | `docs/journey/month-4/day-89.md` | `04_docs` | PHASE 4 | Documentation / Log | 147 | `PENDING` |
| 554 | `docs/journey/month-4/day-90.md` | `04_docs` | PHASE 4 | Documentation / Log | 150 | `PENDING` |
| 555 | `docs/journey/month-4/month-4-retrospective.md` | `04_docs` | PHASE 4 | Documentation / Log | 79 | `PENDING` |
| 556 | `docs/journey/month-4/overview.md` | `04_docs` | PHASE 4 | Documentation / Log | 24 | `PENDING` |
| 557 | `docs/journey/month-4/week-13-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 126 | `PENDING` |
| 558 | `docs/journey/month-4/week-13.md` | `04_docs` | PHASE 4 | Documentation / Log | 67 | `PENDING` |
| 559 | `docs/journey/month-4/week-14-review.md` | `04_docs` | PHASE 4 | Documentation / Log | 134 | `PENDING` |
| 560 | `docs/journey/month-4/week-14.md` | `04_docs` | PHASE 4 | Documentation / Log | 32 | `PENDING` |
| 561 | `docs/journey/month-4/week-15.md` | `04_docs` | PHASE 4 | Documentation / Log | 23 | `PENDING` |
| 562 | `docs/journey/month-4/week-16.md` | `04_docs` | PHASE 4 | Documentation / Log | 23 | `PENDING` |
| 563 | `docs/journey/month-4/week-17.md` | `04_docs` | PHASE 4 | Documentation / Log | 28 | `PENDING` |
| 564 | `docs/journey/month-4/week-18-retrospective.md` | `04_docs` | PHASE 4 | Documentation / Log | 115 | `PENDING` |
| 565 | `docs/journey/month-4/week-18.md` | `04_docs` | PHASE 4 | Documentation / Log | 28 | `PENDING` |
| 566 | `docs/journey/month-5/day-91.md` | `04_docs` | PHASE 4 | Documentation / Log | 104 | `PENDING` |
| 567 | `docs/journey/month-5/day-92.md` | `04_docs` | PHASE 4 | Documentation / Log | 133 | `PENDING` |
| 568 | `docs/journey/month-5/day-93.md` | `04_docs` | PHASE 4 | Documentation / Log | 147 | `PENDING` |
| 569 | `docs/journey/month-5/day-94.md` | `04_docs` | PHASE 4 | Documentation / Log | 108 | `PENDING` |
| 570 | `docs/journey/month-5/day-95.md` | `04_docs` | PHASE 4 | Documentation / Log | 119 | `PENDING` |
| 571 | `docs/journey/month-5/overview.md` | `04_docs` | PHASE 4 | Documentation / Log | 31 | `PENDING` |
| 572 | `docs/journey/overview.md` | `04_docs` | PHASE 4 | Documentation / Log | 34 | `PENDING` |
| 573 | `docs/reports/case-study-vercel-deployment-failure.md` | `04_docs` | PHASE 4 | Documentation / Log | 267 | `PENDING` |
| 574 | `docs/reports/interim-project-report-month-1.md` | `04_docs` | PHASE 4 | Documentation / Log | 364 | `PENDING` |
| 575 | `docs/reports/master-engineering-roadmap-days-1-80.md` | `04_docs` | PHASE 4 | Documentation / Log | 406 | `PENDING` |
| 576 | `docs/reports/nirmaya-academic-project-monograph-thesis.md` | `04_docs` | PHASE 4 | Documentation / Log | 355 | `PENDING` |
| 577 | `docs/reports/nirmaya-capstone-presentation-deck.md` | `04_docs` | PHASE 4 | Documentation / Log | 152 | `PENDING` |
| 578 | `docs/reports/nirmaya-family-proxy-access-architecture.md` | `04_docs` | PHASE 4 | Documentation / Log | 126 | `PENDING` |
| 579 | `docs/reports/nirmaya-interactive-demo-script.md` | `04_docs` | PHASE 4 | Documentation / Log | 117 | `PENDING` |
| 580 | `docs/reports/nirmaya-release-v1.0.0-master-notes.md` | `04_docs` | PHASE 4 | Documentation / Log | 56 | `PENDING` |
| 581 | `docs/reports/nirmaya-sbom-cyclonedx.json` | `04_docs` | PHASE 4 | Documentation / Log | 459 | `PENDING` |
| 582 | `docs/reports/nirmaya-system-audit-and-license-compliance.md` | `04_docs` | PHASE 4 | Documentation / Log | 161 | `PENDING` |
| 583 | `docs/reports/nirmaya-vs-apollo-aarogyasetu-comparative-analysis.docx` | `04_docs` | PHASE 4 | Binary (DOCX) | 0 | `CATALOGED-ONLY` |
| 584 | `docs/reports/nirmaya-vs-apollo-aarogyasetu-comparative-analysis.md` | `04_docs` | PHASE 4 | Documentation / Log | 407 | `PENDING` |
| 585 | `docs/standards/abdm-abha.md` | `04_docs` | PHASE 4 | Documentation / Log | 52 | `PENDING` |
| 586 | `docs/standards/federated-database-edge-architecture.md` | `04_docs` | PHASE 4 | Documentation / Log | 396 | `PENDING` |
| 587 | `docs/standards/fhir-r4.md` | `04_docs` | PHASE 4 | Documentation / Log | 73 | `PENDING` |
| 588 | `docs/standards/indian-administrative-hierarchy.md` | `04_docs` | PHASE 4 | Documentation / Log | 206 | `PENDING` |
| 589 | `docs/vision/architecture.md` | `04_docs` | PHASE 4 | Documentation / Log | 50 | `PENDING` |
| 590 | `docs/vision/problem-statement.md` | `04_docs` | PHASE 4 | Documentation / Log | 24 | `PENDING` |
| 591 | `docs/vision/tech-stack.md` | `04_docs` | PHASE 4 | Documentation / Log | 38 | `PENDING` |
| 592 | `frontend/README.md` | `04_docs` | PHASE 4 | Documentation | 45 | `PENDING` |
| 593 | `.agent/skills/academic-research-writer/SKILL.md` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 183 | `PENDING` |
| 594 | `.agent/skills/academic-research-writer/references/ACADEMIC-WRITING.md` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 28 | `PENDING` |
| 595 | `.agent/skills/academic-research-writer/references/IEEE-CITATION-GUIDE.md` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 35 | `PENDING` |
| 596 | `.agent/skills/academic-research-writer/references/SOURCE-VERIFICATION.md` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 18 | `PENDING` |
| 597 | `.agent/skills/ui-ux-pro-max/SKILL.md` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 292 | `PENDING` |
| 598 | `.agent/skills/ui-ux-pro-max/data/charts.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 26 | `PENDING` |
| 599 | `.agent/skills/ui-ux-pro-max/data/colors.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 97 | `PENDING` |
| 600 | `.agent/skills/ui-ux-pro-max/data/icons.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 101 | `PENDING` |
| 601 | `.agent/skills/ui-ux-pro-max/data/landing.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 31 | `PENDING` |
| 602 | `.agent/skills/ui-ux-pro-max/data/products.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 97 | `PENDING` |
| 603 | `.agent/skills/ui-ux-pro-max/data/react-performance.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 45 | `PENDING` |
| 604 | `.agent/skills/ui-ux-pro-max/data/stacks/astro.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 54 | `PENDING` |
| 605 | `.agent/skills/ui-ux-pro-max/data/stacks/flutter.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 53 | `PENDING` |
| 606 | `.agent/skills/ui-ux-pro-max/data/stacks/html-tailwind.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 56 | `PENDING` |
| 607 | `.agent/skills/ui-ux-pro-max/data/stacks/jetpack-compose.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 53 | `PENDING` |
| 608 | `.agent/skills/ui-ux-pro-max/data/stacks/nextjs.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 53 | `PENDING` |
| 609 | `.agent/skills/ui-ux-pro-max/data/stacks/nuxt-ui.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 51 | `PENDING` |
| 610 | `.agent/skills/ui-ux-pro-max/data/stacks/nuxtjs.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 59 | `PENDING` |
| 611 | `.agent/skills/ui-ux-pro-max/data/stacks/react-native.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 52 | `PENDING` |
| 612 | `.agent/skills/ui-ux-pro-max/data/stacks/react.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 54 | `PENDING` |
| 613 | `.agent/skills/ui-ux-pro-max/data/stacks/shadcn.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 61 | `PENDING` |
| 614 | `.agent/skills/ui-ux-pro-max/data/stacks/svelte.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 54 | `PENDING` |
| 615 | `.agent/skills/ui-ux-pro-max/data/stacks/swiftui.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 51 | `PENDING` |
| 616 | `.agent/skills/ui-ux-pro-max/data/stacks/vue.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 50 | `PENDING` |
| 617 | `.agent/skills/ui-ux-pro-max/data/styles.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 68 | `PENDING` |
| 618 | `.agent/skills/ui-ux-pro-max/data/typography.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 58 | `PENDING` |
| 619 | `.agent/skills/ui-ux-pro-max/data/ui-reasoning.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 101 | `PENDING` |
| 620 | `.agent/skills/ui-ux-pro-max/data/ux-guidelines.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 100 | `PENDING` |
| 621 | `.agent/skills/ui-ux-pro-max/data/web-interface.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 31 | `PENDING` |
| 622 | `.agent/skills/ui-ux-pro-max/scripts/core.py` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 253 | `PENDING` |
| 623 | `.agent/skills/ui-ux-pro-max/scripts/design_system.py` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 1067 | `PENDING` |
| 624 | `.agent/skills/ui-ux-pro-max/scripts/search.py` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 114 | `PENDING` |
| 625 | `.agents/skills/academic-research-writer/SKILL.md` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 184 | `PENDING` |
| 626 | `.agents/skills/academic-research-writer/references/ACADEMIC-WRITING.md` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 29 | `PENDING` |
| 627 | `.agents/skills/academic-research-writer/references/IEEE-CITATION-GUIDE.md` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 36 | `PENDING` |
| 628 | `.agents/skills/academic-research-writer/references/SOURCE-VERIFICATION.md` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 19 | `PENDING` |
| 629 | `.agents/skills/calcom-design-system/SKILL.md` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 215 | `PENDING` |
| 630 | `.agents/skills/ui-ux-pro-max/SKILL.md` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 292 | `PENDING` |
| 631 | `.agents/skills/ui-ux-pro-max/data/charts.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 26 | `PENDING` |
| 632 | `.agents/skills/ui-ux-pro-max/data/colors.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 97 | `PENDING` |
| 633 | `.agents/skills/ui-ux-pro-max/data/icons.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 101 | `PENDING` |
| 634 | `.agents/skills/ui-ux-pro-max/data/landing.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 31 | `PENDING` |
| 635 | `.agents/skills/ui-ux-pro-max/data/products.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 97 | `PENDING` |
| 636 | `.agents/skills/ui-ux-pro-max/data/react-performance.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 45 | `PENDING` |
| 637 | `.agents/skills/ui-ux-pro-max/data/stacks/astro.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 54 | `PENDING` |
| 638 | `.agents/skills/ui-ux-pro-max/data/stacks/flutter.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 53 | `PENDING` |
| 639 | `.agents/skills/ui-ux-pro-max/data/stacks/html-tailwind.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 56 | `PENDING` |
| 640 | `.agents/skills/ui-ux-pro-max/data/stacks/jetpack-compose.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 53 | `PENDING` |
| 641 | `.agents/skills/ui-ux-pro-max/data/stacks/nextjs.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 53 | `PENDING` |
| 642 | `.agents/skills/ui-ux-pro-max/data/stacks/nuxt-ui.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 51 | `PENDING` |
| 643 | `.agents/skills/ui-ux-pro-max/data/stacks/nuxtjs.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 59 | `PENDING` |
| 644 | `.agents/skills/ui-ux-pro-max/data/stacks/react-native.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 52 | `PENDING` |
| 645 | `.agents/skills/ui-ux-pro-max/data/stacks/react.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 54 | `PENDING` |
| 646 | `.agents/skills/ui-ux-pro-max/data/stacks/shadcn.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 61 | `PENDING` |
| 647 | `.agents/skills/ui-ux-pro-max/data/stacks/svelte.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 54 | `PENDING` |
| 648 | `.agents/skills/ui-ux-pro-max/data/stacks/swiftui.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 51 | `PENDING` |
| 649 | `.agents/skills/ui-ux-pro-max/data/stacks/vue.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 50 | `PENDING` |
| 650 | `.agents/skills/ui-ux-pro-max/data/styles.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 68 | `PENDING` |
| 651 | `.agents/skills/ui-ux-pro-max/data/typography.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 58 | `PENDING` |
| 652 | `.agents/skills/ui-ux-pro-max/data/ui-reasoning.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 101 | `PENDING` |
| 653 | `.agents/skills/ui-ux-pro-max/data/ux-guidelines.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 100 | `PENDING` |
| 654 | `.agents/skills/ui-ux-pro-max/data/web-interface.csv` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 31 | `PENDING` |
| 655 | `.agents/skills/ui-ux-pro-max/scripts/core.py` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 253 | `PENDING` |
| 656 | `.agents/skills/ui-ux-pro-max/scripts/design_system.py` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 1067 | `PENDING` |
| 657 | `.agents/skills/ui-ux-pro-max/scripts/search.py` | `05_ai_skills` | PHASE 4 | AI Skill / Resource | 114 | `PENDING` |
| 658 | `.dockerignore` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 34 | `PENDING` |
| 659 | `.env.edge.example` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 20 | `PENDING` |
| 660 | `.env.production.example` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 51 | `PENDING` |
| 661 | `.gitbook.yaml` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 8 | `PENDING` |
| 662 | `.gitignore` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 44 | `PENDING` |
| 663 | `Caddyfile` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 84 | `PENDING` |
| 664 | `Caddyfile.edge` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 29 | `PENDING` |
| 665 | `VERSION` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 1 | `PENDING` |
| 666 | `backend/.dockerignore` | `06_config_tests_infra` | PHASE 4 | Backend Config / Env | 35 | `PENDING` |
| 667 | `backend/.env.example` | `06_config_tests_infra` | PHASE 4 | Backend Config / Env | 32 | `PENDING` |
| 668 | `backend/Dockerfile` | `06_config_tests_infra` | PHASE 4 | Backend Config / Env | 92 | `PENDING` |
| 669 | `backend/alembic.ini` | `06_config_tests_infra` | PHASE 4 | Backend Config / Env | 69 | `PENDING` |
| 670 | `backend/alembic/versions/.gitkeep` | `06_config_tests_infra` | PHASE 4 | Git Keepfile | 1 | `EXCLUDED (Zero-byte git stub)` |
| 671 | `backend/requirements.txt` | `06_config_tests_infra` | PHASE 4 | Backend Config / Env | 21 | `PENDING` |
| 672 | `backend/tests/__init__.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 1 | `PENDING` |
| 673 | `backend/tests/conftest.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 24 | `PENDING` |
| 674 | `backend/tests/test_aadhaar_otp_auth.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 274 | `PENDING` |
| 675 | `backend/tests/test_abdm_gateway_auth.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 223 | `PENDING` |
| 676 | `backend/tests/test_abdm_m1_abha_hpr.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 267 | `PENDING` |
| 677 | `backend/tests/test_abdm_m2_discovery.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 444 | `PENDING` |
| 678 | `backend/tests/test_abdm_m2_hip_bridge.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 207 | `PENDING` |
| 679 | `backend/tests/test_abdm_m2_linkage.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 419 | `PENDING` |
| 680 | `backend/tests/test_abdm_m3_consent.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 367 | `PENDING` |
| 681 | `backend/tests/test_abdm_m3_crypto.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 462 | `PENDING` |
| 682 | `backend/tests/test_abdm_m3_hiu.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 484 | `PENDING` |
| 683 | `backend/tests/test_abdm_m3_transfer.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 437 | `PENDING` |
| 684 | `backend/tests/test_abdm_sandbox_certification.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 191 | `PENDING` |
| 685 | `backend/tests/test_abdm_security_penetration.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 220 | `PENDING` |
| 686 | `backend/tests/test_abha_card.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 303 | `PENDING` |
| 687 | `backend/tests/test_academic_monograph.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 248 | `PENDING` |
| 688 | `backend/tests/test_accessibility.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 335 | `PENDING` |
| 689 | `backend/tests/test_administrative_hierarchy.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 437 | `PENDING` |
| 690 | `backend/tests/test_api_auth.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 220 | `PENDING` |
| 691 | `backend/tests/test_api_doctors.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 430 | `PENDING` |
| 692 | `backend/tests/test_api_patients.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 420 | `PENDING` |
| 693 | `backend/tests/test_api_rbac.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 208 | `PENDING` |
| 694 | `backend/tests/test_appointment_concurrency.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 513 | `PENDING` |
| 695 | `backend/tests/test_appointments.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 505 | `PENDING` |
| 696 | `backend/tests/test_asvs_and_dos_shield.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 235 | `PENDING` |
| 697 | `backend/tests/test_audit_hash_chain_and_concurrency.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 349 | `PENDING` |
| 698 | `backend/tests/test_auth_jwt.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 84 | `PENDING` |
| 699 | `backend/tests/test_break_the_glass_vault.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 306 | `PENDING` |
| 700 | `backend/tests/test_calcom_booking_flow.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 229 | `PENDING` |
| 701 | `backend/tests/test_cds_safety.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 364 | `PENDING` |
| 702 | `backend/tests/test_child_abha_linkage.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 422 | `PENDING` |
| 703 | `backend/tests/test_citizen_portal.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 354 | `PENDING` |
| 704 | `backend/tests/test_clinical_alerts_sync.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 275 | `PENDING` |
| 705 | `backend/tests/test_conditions.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 581 | `PENDING` |
| 706 | `backend/tests/test_container_runtime.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 258 | `PENDING` |
| 707 | `backend/tests/test_db_base.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 83 | `PENDING` |
| 708 | `backend/tests/test_db_session.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 65 | `PENDING` |
| 709 | `backend/tests/test_delegation_and_trbac.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 510 | `PENDING` |
| 710 | `backend/tests/test_diagnostics.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 669 | `PENDING` |
| 711 | `backend/tests/test_digilocker_auth.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 247 | `PENDING` |
| 712 | `backend/tests/test_docker_orchestration.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 221 | `PENDING` |
| 713 | `backend/tests/test_doctor_queue.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 346 | `PENDING` |
| 714 | `backend/tests/test_doctor_service.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 357 | `PENDING` |
| 715 | `backend/tests/test_edge_node_sync.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 252 | `PENDING` |
| 716 | `backend/tests/test_exceptions.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 53 | `PENDING` |
| 717 | `backend/tests/test_express_consultation.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 558 | `PENDING` |
| 718 | `backend/tests/test_family_proxy.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 434 | `PENDING` |
| 719 | `backend/tests/test_fhir_encounter.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 804 | `PENDING` |
| 720 | `backend/tests/test_fhir_r4_bundle_validator.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 669 | `PENDING` |
| 721 | `backend/tests/test_frontend_container_runtime.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 232 | `PENDING` |
| 722 | `backend/tests/test_guardian_conflict.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 616 | `PENDING` |
| 723 | `backend/tests/test_guardian_delegation.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 544 | `PENDING` |
| 724 | `backend/tests/test_health.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 115 | `PENDING` |
| 725 | `backend/tests/test_ieee_manuscript_day91.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 209 | `PENDING` |
| 726 | `backend/tests/test_ieee_manuscript_day92.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 200 | `PENDING` |
| 727 | `backend/tests/test_ieee_manuscript_day93.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 236 | `PENDING` |
| 728 | `backend/tests/test_ieee_manuscript_day94.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 255 | `PENDING` |
| 729 | `backend/tests/test_ieee_manuscript_day95.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 299 | `PENDING` |
| 730 | `backend/tests/test_interactive_demo.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 235 | `PENDING` |
| 731 | `backend/tests/test_legacy_his_federation.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 295 | `PENDING` |
| 732 | `backend/tests/test_master_release.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 194 | `PENDING` |
| 733 | `backend/tests/test_medication_dispense.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 515 | `PENDING` |
| 734 | `backend/tests/test_medication_requests.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 620 | `PENDING` |
| 735 | `backend/tests/test_medications.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 361 | `PENDING` |
| 736 | `backend/tests/test_meta.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 47 | `PENDING` |
| 737 | `backend/tests/test_migrations.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 299 | `PENDING` |
| 738 | `backend/tests/test_models_doctor.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 193 | `PENDING` |
| 739 | `backend/tests/test_models_lab.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 238 | `PENDING` |
| 740 | `backend/tests/test_models_patient.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 143 | `PENDING` |
| 741 | `backend/tests/test_models_user.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 98 | `PENDING` |
| 742 | `backend/tests/test_month_1_e2e_verification.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 595 | `PENDING` |
| 743 | `backend/tests/test_month_2_e2e_verification.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 699 | `PENDING` |
| 744 | `backend/tests/test_national_gateway.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 529 | `PENDING` |
| 745 | `backend/tests/test_observations.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 678 | `PENDING` |
| 746 | `backend/tests/test_opd_queue_sync.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 240 | `PENDING` |
| 747 | `backend/tests/test_patient_unified_auth.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 234 | `PENDING` |
| 748 | `backend/tests/test_performance_benchmarks.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 262 | `PENDING` |
| 749 | `backend/tests/test_platform_comparison_report.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 100 | `PENDING` |
| 750 | `backend/tests/test_public_health_command_center.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 412 | `PENDING` |
| 751 | `backend/tests/test_rate_limit.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 139 | `PENDING` |
| 752 | `backend/tests/test_rbac.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 247 | `PENDING` |
| 753 | `backend/tests/test_release_v1_1_0.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 329 | `PENDING` |
| 754 | `backend/tests/test_sast_security_scanner.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 276 | `PENDING` |
| 755 | `backend/tests/test_schemas_doctor_lab.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 282 | `PENDING` |
| 756 | `backend/tests/test_schemas_patient.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 116 | `PENDING` |
| 757 | `backend/tests/test_seeder.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 149 | `PENDING` |
| 758 | `backend/tests/test_soap_notes.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 620 | `PENDING` |
| 759 | `backend/tests/test_system_audit_licenses.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 247 | `PENDING` |
| 760 | `backend/tests/test_terminology_validator.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 357 | `PENDING` |
| 761 | `backend/tests/test_ux4g_design_system_phase6.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 233 | `PENDING` |
| 762 | `backend/tests/test_websockets_gateway.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 265 | `PENDING` |
| 763 | `backend/tests/test_week_10_e2e_verification.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 508 | `PENDING` |
| 764 | `backend/tests/test_week_11_m3_integration_audit.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 642 | `PENDING` |
| 765 | `backend/tests/test_week_5_e2e_verification.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 623 | `PENDING` |
| 766 | `backend/tests/test_week_6_e2e_verification.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 882 | `PENDING` |
| 767 | `backend/tests/test_week_7_e2e_verification.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 620 | `PENDING` |
| 768 | `backend/tests/test_week_9_e2e_verification.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 584 | `PENDING` |
| 769 | `backend/tests/test_workflow_isolation.py` | `06_config_tests_infra` | PHASE 4 | Backend Test | 528 | `PENDING` |
| 770 | `docker-compose.edge.yml` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 123 | `PENDING` |
| 771 | `docker-compose.yml` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 161 | `PENDING` |
| 772 | `frontend/.dockerignore` | `06_config_tests_infra` | PHASE 4 | Frontend Config | 45 | `PENDING` |
| 773 | `frontend/.env.example` | `06_config_tests_infra` | PHASE 4 | Frontend Config | 15 | `PENDING` |
| 774 | `frontend/.gitignore` | `06_config_tests_infra` | PHASE 4 | Frontend Config | 42 | `PENDING` |
| 775 | `frontend/Dockerfile` | `06_config_tests_infra` | PHASE 4 | Frontend Config | 77 | `PENDING` |
| 776 | `frontend/next.config.ts` | `06_config_tests_infra` | PHASE 4 | Frontend Config | 68 | `PENDING` |
| 777 | `frontend/package-lock.json` | `06_config_tests_infra` | PHASE 4 | Frontend Config | 2474 | `PENDING` |
| 778 | `frontend/package.json` | `06_config_tests_infra` | PHASE 4 | Frontend Config | 32 | `PENDING` |
| 779 | `frontend/postcss.config.mjs` | `06_config_tests_infra` | PHASE 4 | Frontend Config | 5 | `PENDING` |
| 780 | `frontend/tsconfig.json` | `06_config_tests_infra` | PHASE 4 | Frontend Config | 27 | `PENDING` |
| 781 | `gitbook-docs.yaml` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 12 | `PENDING` |
| 782 | `package.json` | `06_config_tests_infra` | PHASE 4 | Root Config / Infra | 35 | `PENDING` |
| 783 | `scripts/db-check.py` | `06_config_tests_infra` | PHASE 4 | Automation Script | 49 | `PENDING` |
| 784 | `scripts/doctor.py` | `06_config_tests_infra` | PHASE 4 | Automation Script | 172 | `PENDING` |
| 785 | `scripts/generate_interim_report_doc.py` | `06_config_tests_infra` | PHASE 4 | Automation Script | 435 | `PENDING` |
| 786 | `scripts/run-dev.ps1` | `06_config_tests_infra` | PHASE 4 | Automation Script | 42 | `PENDING` |
| 787 | `scripts/run-dev.sh` | `06_config_tests_infra` | PHASE 4 | Automation Script | 53 | `PENDING` |
| 788 | `scripts/seed-db.py` | `06_config_tests_infra` | PHASE 4 | Automation Script | 111 | `PENDING` |
| 789 | `scripts/validate_ieee_latex.py` | `06_config_tests_infra` | PHASE 4 | Automation Script | 178 | `PENDING` |
