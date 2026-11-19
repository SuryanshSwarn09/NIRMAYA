# Codebase Audit Progress Tracker (`PROGRESS.md`)

## 1. Global Audit Status

- **Current Position**: PHASE 2 - BACKEND (Batch B2-08 Complete · In Progress)
- **Active Subsystem**: `backend/app/schemas/` (Pydantic Schemas Part 4 - Portals & Security, 7 files audited)
- **Next Batch**: **Batch B2-09** (`backend/app/schemas/delegation.py` through `backend/app/schemas/emergency_vault.py`, 7 files)
- **Total Tracked Files**: 789
- **Source Files Audited**: 63 / 768 (8.2% of source files)
- **Overview / Baseline Reports**: 6 reports
- **Pending Source/Doc Reports**: 705
- **Cataloged Only (Binaries/Images/Docx)**: 20
- **Excluded Files**: 1 (Zero-byte git stub `.gitkeep`)

---

## 2. Findings Summary by Severity

| Severity | Description | Current Count | Target Remediation Plan |
| :---: | :--- | :---: | :--- |
| **S0** | Blocker (Exploitable vuln, data loss, crash on main path) | **0** | Immediate unapplied patch diff in report |
| **S1** | High Risk (Auth bypass, crypto flaw, hardcoded secrets, RLS/IP spoofing, audit ledger cascade, proxy audit cascade, Aadhaar logging, plaintext OTP response, crypto key repr leaks, JWT repr leaks, child Aadhaar/OTP repr leaks) | **16** | Unapplied patch diff in report (`SEC-01-01`/`BE-CFG-F01`, `SEC-01-02`, `BE-DEP-F01`, `BE-RAT-F01`, `BE-SEC-F01`, `BE-TRBAC-F01`, `BE-TEN-F01`, `BE-DEL-F01`, `BE-FPX-F01`, `BE-M1-F01`, `BE-M2-F01`, `BE-CRY-F01`, `BE-HIU-F01`, `BE-TRF-F01`, `BE-SCH-ATH-F01`, `BE-SCH-CABH-F01`) |
| **S2** | Medium Risk (Dead code, perf leak, architectural drift, debug flags, unlogged 500s, clinical cascade deletes, schema-ORM mismatches, schema shadowing, credential repr leaks, symmetric QR HMAC, unvalidated ltree/IP/hashes, redundant aliasing) | **63** | Unapplied patch diff in report (`BE-CFG-F02`, `BE-CFG-F03`, `BE-CFG-F04`, `BE-CFG-F05`, `BE-CSEC-F01`, `BE-CSEC-F02`, `BE-DEP-F02`, `BE-EXC-F01`, `BE-EXC-F02`, `SEC-01-05`, `BE-RAT-F02`, `BE-SEC-F02`, `BE-SEC-F03`, `BE-TRBAC-F02`, `BE-SEED-F01`, `BE-SES-F01`, `BE-ADH-F01`, `BE-ADH-F02`, `BE-APP-F01`, `BE-CMD-F01`, `BE-CON-F01`, `BE-DEL-F02`, `BE-DIA-F01`, `BE-DIA-F02`, `BE-DIA-F03`, `BE-DOC-F01`, `BE-FPX-F02`, `BE-LAB-F01`, `BE-LAB-F02`, `BE-MED-F01`, `BE-DISP-F01`, `BE-MRQ-F01`, `BE-PAT-F01`, `BE-PAT-F02`, `BE-SOP-F01`, `BE-USR-F01`, `BE-SCH-F01`, `BE-ABDM-F01`, `BE-M1-F02`, `BE-M2-F02`, `BE-M3C-F01`, `BE-CRY-F02`, `BE-HIU-F02`, `BE-TRF-F02`, `BE-SEC-AUD-F01`, `BE-ABH-F01`, `BE-ABH-F02`, `BE-SCH-ADH-F01`, `BE-SCH-ADH-F02`, `BE-SCH-APP-F01`, `BE-SCH-APP-F02`, `BE-SCH-ASVS-F01`, `BE-SCH-AHC-F01`, `BE-SCH-AHC-F02`, `BE-SCH-ATH-F02`, `BE-SCH-CDS-F01`, `BE-SCH-CABH-F02`, `BE-SCH-CPOR-F01`, `BE-SCH-CALR-F01`, `BE-SCH-CMD-F01`, `BE-SCH-CMD-F02`, `BE-SCH-CON-F01`, `BE-SCH-CRUN-F01`) |
| **S3** | Low Risk (Style inconsistency, minor doc drift, naming, CORS policies, deprecated utcnow, missing bounds, phone formats, unconstrained floats, stale versions, deprecated example, missing regex) | **75** | One-line fix prescription (`BE-CFG-F06`, `BE-CSEC-F03`, `BE-CORS-F01`, `BE-CORS-F02`, `BE-DEP-F03`, `BE-LOG-F01`, `BE-LOG-F02`, `BE-LOG-F03`, `BE-MID-F01`, `BE-MID-F02`, `SEC-01-08`, `BE-RAT-F03`, `BE-BASE-F01`, `BE-BASE-F02`, `BE-FIX-F01`, `BE-SEED-F02`, `BE-SES-F02`, `BE-TEN-F02`, `BE-ADH-F03`, `BE-APP-F02`, `BE-APP-F03`, `BE-CMD-F02`, `BE-CON-F02`, `BE-DEL-F03`, `BE-DOC-F02`, `BE-DOC-F03`, `BE-ENM-F01`, `BE-FPX-F03`, `BE-LAB-F03`, `BE-MED-F02`, `BE-DISP-F02`, `BE-MRQ-F02`, `BE-MRQ-F03`, `BE-OBS-F01`, `BE-PAT-F03`, `BE-SOP-F02`, `BE-USR-F02`, `BE-USR-F03`, `BE-SCH-F02`, `BE-ABDM-F02`, `BE-CER-F01`, `BE-M1-F03`, `BE-ISU-F01`, `BE-M3A-F01`, `BE-M3A-F02`, `BE-M3C-F02`, `BE-M3C-F03`, `BE-CRY-F03`, `BE-HIU-F03`, `BE-TRF-F03`, `BE-SEC-AUD-F02`, `BE-ABH-F03`, `BE-ACC-F01`, `BE-ACC-F02`, `BE-SCH-ADH-F03`, `BE-SCH-APP-F03`, `BE-SCH-ASVS-F02`, `BE-SCH-ASVS-F03`, `BE-SCH-AHC-F03`, `BE-SCH-ATH-F03`, `BE-SCH-BNK-F01`, `BE-SCH-BNK-F02`, `BE-SCH-CDS-F02`, `BE-SCH-CDS-F03`, `BE-SCH-CABH-F03`, `BE-SCH-CPOR-F02`, `BE-SCH-CPOR-F03`, `BE-SCH-CALR-F02`, `BE-SCH-CALR-F03`, `BE-SCH-CMD-F03`, `BE-SCH-COM-F01`, `BE-SCH-COM-F02`, `BE-SCH-CON-F02`, `BE-SCH-CON-F03`, `BE-SCH-CRUN-F02`) |
| **S4** | Note / Informational (Observation, educational note, barrel export, hardcoded mock ID, missing module docstring, hardcoded image tags) | **14** | Contextual note (`BE-CORE-001`, `BE-DB-001`, `BE-BASE-F03`, `BE-FIX-F02`, `BE-MOD-001`, `BE-M3C-F04`, `BE-SEC-AUD-F03`, `BE-ACC-F03`, `BE-SCH-ADH-F04`, `BE-SCH-AHC-F04`, `BE-SCH-BNK-F03`, `BE-SCH-CABH-F04`, `BE-SCH-CMD-F04`, `BE-SCH-CRUN-F03`) |
| **TOTAL** | | **168** | |

---

## 3. Proposed Batching Plan (8–10 Files Per Batch)

### PHASE 1 - Overview & Early Security Sweep (1 Batch · COMPLETE)

- Deliverables: `architecture.md`, `stack.md`, `run_build_deploy.md`, `folder_map.md`, `early_security_sweep.md`, `dev_timeline.md`.

---

### PHASE 2 - Backend Source Audit (243 Files · 27 Batches)

*Full report template per file (`02_backend/<mirrored path>.report.md`)*

- [x] **Batch B2-01 (8 files · COMPLETE)**: Core Engine & Security Primitives (`backend/app/core/__init__.py`, `config.py`, `container_security.py`, `cors.py`, `dependencies.py`, `exceptions.py`, `logging.py`, `middleware.py`)
- [x] **Batch B2-02 (9 files · COMPLETE)**: Rate Limiting & Database Engine (`rate_limit.py`, `security.py`, `territorial_rbac.py`, `db/__init__.py`, `base.py`, `fixtures.py`, `seeder.py`, `session.py`, `tenant_context.py`)
- [x] **Batch B2-03 (9 files · COMPLETE)**: SQLAlchemy ORM Models Part 1 (`models/__init__.py`, `administrative_hierarchy.py`, `appointment.py`, `command_center.py`, `condition.py`, `delegation.py`, `diagnostic.py`, `doctor.py`, `enums.py`)
- [x] **Batch B2-04 (9 files · COMPLETE)**: SQLAlchemy ORM Models Part 2 (`family_proxy.py`, `lab.py`, `medication.py`, `medication_dispense.py`, `medication_request.py`, `observation.py`, `patient.py`, `soap_note.py`, `user.py`)
- [x] **Batch B2-05 (7 files · COMPLETE)**: Pydantic Validation Schemas Part 1 - ABDM Subsystem (`schemas/__init__.py`, `abdm.py`, `abdm_certification.py`, `abdm_m1.py`, `abdm_m1_issuance.py`, `abdm_m2_bridge.py`, `abdm_m3_audit.py`)
- [x] **Batch B2-06 (7 files · COMPLETE)**: Pydantic Validation Schemas Part 2 - ABDM & Security (`abdm_m3_consent.py`, `abdm_m3_crypto.py`, `abdm_m3_hiu.py`, `abdm_m3_transfer.py`, `abdm_security_audit.py`, `abha_card.py`, `accessibility.py`)
- [x] **Batch B2-07 (7 files · COMPLETE)**: Pydantic Validation Schemas Part 3 - Clinical & Core (`administrative_hierarchy.py`, `appointment.py`, `asvs_fuzzer.py`, `audit_hash_chain.py`, `auth.py`, `benchmark.py`, `cds.py`)
- [x] **Batch B2-08 (7 files · COMPLETE)**: Pydantic Validation Schemas Part 4 - Portals & Security (`child_abha.py`, `citizen_portal.py`, `clinical_alerts.py`, `command_center.py`, `common.py`, `condition.py`, `container_runtime.py`)
- [ ] **Batch B2-09 (7 files · NEXT)**: Pydantic Validation Schemas Part 5 - Clinical Services (`delegation.py`, `demo.py`, `diagnostic.py`, `digilocker.py`, `doctor.py`, `edge_sync.py`, `emergency_vault.py`)
- [ ] **Batches B2-09 to B2-13 (45 files)**: Core Business Services (`backend/app/services/` - Auth, EMR, Security, Monograph, Legacy HIS)
- [ ] **Batches B2-14 to B2-17 (34 files)**: HL7 FHIR Subsystem (`backend/app/fhir/` - Schemas, Transformers, Validators)
- [ ] **Batches B2-18 to B2-23 (54 files)**: API Endpoints & Route Handlers (`backend/app/api/v1/endpoints/`)
- [ ] **Batches B2-24 to B2-25 (18 files)**: Middleware, Utilities, WebSockets, Worker Tasks (`backend/app/middleware/`, `backend/app/utils/`, `backend/app/websockets/`, `backend/app/tasks/`)
- [ ] **Batches B2-26 to B2-27 (12 files)**: Alembic Database Migrations (`backend/alembic/`)
- [ ] **Layer Summary**: `02_backend/_layer_summary.md`

---

### PHASE 3 - Frontend Source Audit (110 Active Files · 13 Batches)

- Batches B3-01 to B3-13 + 13 cataloged assets.

---

### PHASE 4 - Docs, AI Skills, Config, Tests & Infra (403 Files · 45 Batches)

- Sub-phases 4A, 4B, 4C, 4D.

---

### PHASE 5 - Cross-Cutting Synthesis (10 Master Reports)

- OWASP audit, patch index, dead code, performance, API contract matrix, etc.

---

### PHASE 6 - Index & Verification

- `00_INDEX.md`, 10-report empirical spot-check, and final audit sign-off.

---

## 4. Batch Execution Log

| Batch ID | Date / Time | Phase | Files Covered | S0 | S1 | S2 | S3 | S4 | Status |
| :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **B0-00** | 2026-11-18 | PHASE 0 | Full repository inventory & manifest generation (`00_MANIFEST.md`) | 0 | 0 | 0 | 0 | 0 | COMPLETE |
| **B1-01** | 2026-11-18 | PHASE 1 | Overview syntheses & early security baseline (6 reports) | 0 | 2 | 4 | 2 | 0 | COMPLETE |
| **B2-01** | 2026-11-18 | PHASE 2 | Core engine & security (`app/core/__init__.py` through `middleware.py`, 8 files) | 0 | 2 | 9 | 10 | 1 | COMPLETE |
| **B2-02** | 2026-11-18 | PHASE 2 | Rate limit, crypto, TRBAC, DB session & context (9 files) | 0 | 4 | 6 | 7 | 3 | COMPLETE |
| **B2-03** | 2026-11-18 | PHASE 2 | SQLAlchemy ORM Models Part 1 (`app/models/__init__.py` through `enums.py`, 9 files) | 0 | 1 | 10 | 9 | 1 | COMPLETE |
| **B2-04** | 2026-11-18 | PHASE 2 | SQLAlchemy ORM Models Part 2 (`app/models/family_proxy.py` through `user.py`, 9 files) | 0 | 1 | 10 | 11 | 0 | COMPLETE |
| **B2-05** | 2026-11-18 | PHASE 2 | Pydantic Schemas Part 1 - ABDM (`schemas/__init__.py` through `abdm_m3_audit.py`, 7 files) | 0 | 2 | 4 | 7 | 0 | COMPLETE |
| **B2-06** | 2026-11-18 | PHASE 2 | Pydantic Schemas Part 2 - ABDM & Security (`abdm_m3_consent.py` through `accessibility.py`, 7 files) | 0 | 3 | 7 | 9 | 3 | COMPLETE |
| **B2-07** | 2026-11-19 | PHASE 2 | Pydantic Schemas Part 3 - Clinical & Core (`administrative_hierarchy.py` through `cds.py`, 7 files) | 0 | 1 | 9 | 10 | 3 | COMPLETE |
| **B2-08** | 2026-11-19 | PHASE 2 | Pydantic Schemas Part 4 - Portals & Security (`child_abha.py` through `container_runtime.py`, 7 files) | 0 | 1 | 7 | 11 | 3 | COMPLETE |

---

## 5. Resumption Instructions

1. Active Phase: **PHASE 2 - BACKEND**
2. Next Batch to execute: **Batch B2-09 (7 files)**:
   - `backend/app/schemas/delegation.py`
   - `backend/app/schemas/demo.py`
   - `backend/app/schemas/diagnostic.py`
   - `backend/app/schemas/digilocker.py`
   - `backend/app/schemas/doctor.py`
   - `backend/app/schemas/edge_sync.py`
   - `backend/app/schemas/emergency_vault.py`
3. Generate reports under `audit/02_backend/app/schemas/`.
4. Update `00_MANIFEST.md`, `PROGRESS.md`, mirror to `docs/audit/`, register in `docs/SUMMARY.md`, commit and push.
