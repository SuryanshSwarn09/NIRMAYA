# NIRMAYA: Networked Interoperable Records Medical Assets & Your Archives
## Interim Project Report (Month 1 Comprehensive Review)

**Academic Target:** Final Year Major Project in Health Informatics & Computer Engineering  
**Candidate Name:** Suryansh Swarn  
**Project Lead:** Suryansh Swarn (`suryanshswarn@gmail.com`)  
**Repository:** `https://github.com/SuryanshSwarn09/NIRMAYA`  
**Milestone Scope:** Month 1 Complete (Weeks 1–4 / Days 1–20)  
**Milestone Release:** `v0.1.0` (Tag: `v0.1.0`)  
**Review Period:** September 1 – October 2, 2026  
**Standards Compliance:** HL7 FHIR Release 4 & Ayushman Bharat Digital Mission (ABDM)  

---

## Abstract

**NIRMAYA** is an enterprise-grade digital health interoperability network and longitudinal patient health vault engineered to resolve India's fragmented healthcare data ecosystem. Rather than isolating clinical information in proprietary database schemas, NIRMAYA structures encounters, demographic profiles, appointments, and diagnostic observations around international healthcare protocols (**HL7 FHIR Release 4**) and simulates India's national health data backbone (**Ayushman Bharat Digital Mission - ABDM**).

This interim report documents the engineering achievements of **Month 1** (a 4-week / 20-working-day development sprint). During this phase, NIRMAYA established a full-stack clinical foundation comprising:
1. An asynchronous, high-throughput backend using **FastAPI**, **Pydantic v2**, and **Async SQLAlchemy 2.0**.
2. A relational schema with strict foreign keys and migrations using **PostgreSQL 16** and **Alembic** (3 schema revisions).
3. Enterprise security and identity federation using **Supabase Auth**, **cryptographic JWT verification**, and **4-tier Role-Based Access Control (RBAC)**.
4. A high-concurrency appointment scheduling engine featuring **ACID row-level locking (`SELECT ... FOR UPDATE`)**, 10-minute temporary holds, and autonomous background sweeper reclamation.
5. Bidirectional, lossless transformers emitting **HL7 FHIR R4** `Appointment`, `Encounter`, `Patient`, `Practitioner`, and `Bundle` resources linked with **ABDM CareContexts** and SHA-256 integrity digests.
6. A clean, modern SaaS client application built with **Next.js 15 (App Router)**, **React 19**, and **Tailwind CSS v4** featuring three dedicated role portals.
7. An automated test suite expanding from a 6-test baseline to **151 passing tests (100% pass rate in 17.67s)** across **210+ atomic micro-commits**.

---

## Table of Contents

1. [Introduction & Problem Statement](#1-introduction--problem-statement)
2. [Project Scope & Month 1 Objectives](#2-project-scope--month-1-objectives)
3. [System Architecture & 3-Pillar Topology](#3-system-architecture--3-pillar-topology)
4. [Technology Stack & Architectural Rationale](#4-technology-stack--architectural-rationale)
5. [Detailed Engineering Progression (Days 1–20)](#5-detailed-engineering-progression-days-120)
6. [Relational Data Model & Database Design](#6-relational-data-model--database-design)
7. [Identity, Multi-Tenancy & 4-Tier RBAC](#7-identity-multi-tenancy--4-tier-rbac)
8. [Concurrency Engineering: Conflict-Free Scheduling](#8-concurrency-engineering-conflict-free-scheduling)
9. [Healthcare Interoperability: HL7 FHIR R4 & ABDM](#9-healthcare-interoperability-hl7-fhir-r4--abdm)
10. [Frontend Architecture & Clean SaaS Design System](#10-frontend-architecture--clean-saas-design-system)
11. [Verification, Testing & Performance Benchmarks](#11-verification-testing--performance-benchmarks)
12. [Version Control Discipline & Commit Logs](#12-version-control-discipline--commit-logs)
13. [Engineering Challenges & Implemented Solutions](#13-engineering-challenges--implemented-solutions)
14. [Subsequent Phase Roadmap (Months 2–4)](#14-subsequent-phase-roadmap-months-24)
15. [Conclusion & Review Committee Sign-Off](#15-conclusion--review-committee-sign-off)

---

## 1. Introduction & Problem Statement

### 1.1 The Healthcare Data Fragmentation Dilemma
In modern healthcare delivery worldwide—and acutely across expanding digital health ecosystems in India—medical data is trapped in disconnected, proprietary database silos. When patients visit multiple general practitioners, specialist clinics, and diagnostic labs:
- **Degraded Physical Records:** Prescriptions are predominantly written on physical paper that is easily misplaced, soiled, or degraded, preventing pharmacological reconciliation and contraindication checks.
- **Unsearchable Diagnostic Attachments:** Diagnostic laboratories generate unstructured, rasterized PDF attachments. Key quantitative metrics (such as HbA1c, platelet counts, or serum creatinine) cannot be tracked, graphed, or ingested by machine algorithms.
- **Zero Longitudinal Visibility:** Attending doctors treat acute clinical conditions with zero access to historical diagnoses, baseline vitals, or drug allergies documented by other providers.

### 1.2 The NIRMAYA Vision
NIRMAYA treats healthcare information not as transient application state, but as **standardized, structured, and patient-sovereign digital assets**. By aligning with the **Ayushman Bharat Digital Mission (ABDM)** and **HL7 FHIR R4**, NIRMAYA provides:
- A federated network where patients own their longitudinal medical ledger.
- Standardized digital consultations with structured encounter notes and e-prescriptions.
- A secured laboratory gateway where diagnostic parameters are ingested as machine-readable observations.

---

## 2. Project Scope & Month 1 Objectives

The complete NIRMAYA roadmap spans 4 months (16 weeks / 80 working days). Month 1 focuses strictly on building the rock-solid foundations of data persistence, multi-role security, appointment booking concurrency, and standards-compliant transformation.

| Objective | Target Domain | Deliverables & Month 1 Scope | Status |
|---|---|---|---|
| **OBJ-01** | Full-Stack Monorepo | Next.js 15 + FastAPI architecture, telemetry, pre-flight doctor diagnostics | **100% Completed** |
| **OBJ-02** | Relational Schemas | User, PatientProfile (ABHA), DoctorProfile (HPR), Lab models via PostgreSQL 16 | **100% Completed** |
| **OBJ-03** | Identity & Security | Supabase Auth, JWT middleware, 4-tier declarative RBAC guards, OWASP hardening | **100% Completed** |
| **OBJ-04** | Clinical Scheduling | Slot engine, ACID row-level locking (`SELECT ... FOR UPDATE`), 10-min hold sweep | **100% Completed** |
| **OBJ-05** | Interoperability | Lossless FHIR R4 `Appointment`, `Encounter`, `Bundle` transformers + ABDM CareContext | **100% Completed** |
| **OBJ-06** | Quality & Verification | 10+ daily atomic micro-commits, 151 passing automated tests, Milestone `v0.1.0` | **100% Completed** |

---

## 3. System Architecture & 3-Pillar Topology

NIRMAYA is organized into three distinct stakeholder pillars unified through an asynchronous API hub:

```
                      +---------------------------------------+
                      |            NIRMAYA PLATFORM           |
                      +---------------------------------------+
                                         |
     +-----------------------------------+-----------------------------------+
     |                                   |                                   |
     v                                   v                                   v
+-------------------------+ +-------------------------+ +-------------------------+
|   Patient Health Vault  | |   Provider (Doctor) EMR | | Diagnostic Lab Gateway  |
| (/patient)              | | (/doctor)               | | (/lab)                  |
| - Longitudinal History  | | - Encounter Reviews     | | - Report Ingestion      |
| - ABHA ID Integration   | | - Doctor Availability   | | - Structured Parameters |
| - Slot Booking & Holds  | | - Consultation Notes    | | - NABL Accreditation    |
+-------------------------+ +-------------------------+ +-------------------------+
     |                                   |                                   |
     +-----------------------------------+-----------------------------------+
                                         |
                                  HTTPS / JSON API
                                         |
                                         v
                      +---------------------------------------+
                      |     FastAPI Interoperability Core     |
                      |  - Pydantic v2 Schema Validation     |
                      |  - 4-Tier RBAC & Token Bucket Limiter |
                      |  - HL7 FHIR R4 Transformer Engine     |
                      |  - ABDM CareContext Cryptographic Bus |
                      +---------------------------------------+
                                  /             \
                                 v               v
                +--------------------+   +-----------------------+
                | PostgreSQL 16 DB   |   | Supabase Cloud Auth   |
                | - Asyncpg Pool     |   | - JWT Verification    |
                | - ACID Row Locks   |   | - Role Policies       |
                | - Alembic Schema   |   | - Signed Asset URLs   |
                +--------------------+   +-----------------------+
```

1. **Patient Health Vault (`/patient`):** Self-sovereign health repository where patients access complete timeline records, link their 14-digit ABHA identity, discover verified doctors, and execute appointments.
2. **Provider (Doctor) EMR (`/doctor`):** Clinical console enabling healthcare professionals to set up practice slots, review incoming patient bookings, and generate structured encounter notes.
3. **Diagnostic Lab Gateway (`/lab`):** Dedicated entry point for accredited facilities to ingest diagnostic reports and parameters.

---

## 4. Technology Stack & Architectural Rationale

| Layer | Technology | Architectural Role | Technical Rationale & Benefits |
|---|---|---|---|
| **Frontend Framework** | **Next.js 15 (App Router)** | Client & Server Rendering | Fast page loads with React Server Components, server actions, and Turbopack compiler. |
| **UI Library** | **React 19 & TypeScript 5** | Interactive Component Tree | Strict type safety across clinical props, hooks, and responsive viewports. |
| **Styling & Design** | **Tailwind CSS v4** | Semantic Design System | Custom CSS variables, dark/light clinical palettes, 1px hairline borders. |
| **Backend Framework** | **FastAPI 0.115+ (Python 3.11)** | RESTful API Engine | Asynchronous non-blocking architecture, native OpenAPI/Swagger generation, sub-millisecond route latency. |
| **Data Validation** | **Pydantic v2** | Request & Response Schemas | Rust-core validation engine for high-throughput serialization and strict regex checking. |
| **Database ORM** | **SQLAlchemy 2.0 (Async)** | Declarative Persistence | Async 2.0 syntax, non-blocking I/O via `asyncpg`, row-level locking primitives. |
| **Database Engine** | **PostgreSQL 16** | Relational ACID Store | Strong transactional consistency, row locks, robust indexing, and relational foreign keys. |
| **Schema Migrations** | **Alembic** | Version-Controlled DDL | Deterministic schema evolution with automated upgrade/downgrade scripts. |
| **Authentication** | **Supabase Auth & PyJWT** | Cloud Identity & Security | Cryptographic JWT verification (HS256/RS256), session cookie handling, zero password storage on server. |
| **Healthcare Protocol** | **HL7 FHIR Release 4** | Clinical Interoperability | International gold standard for electronic healthcare records (Appointment, Encounter, Bundle). |
| **National Standards** | **Simulated ABDM Ecosystem** | National Integration | Ayushman Bharat Health Account (ABHA), HPR, and CareContext consent linking. |

---

## 5. Detailed Engineering Progression (Days 1–20)

### Week 1: Monorepo Foundation, Telemetry & Diagnostics (Days 1–5)
- **Day 1 (Scaffold & Monorepo Init):** Clean directory separation between `frontend/` and `backend/`. Initialized Next.js 15 with Turbopack and FastAPI with CORS middleware.
- **Day 2 (Clinical Tokens & Theme):** Authored semantic CSS tokens in `globals.css` with WCAG AA compliant contrast ratios.
- **Day 3 (ASGI Telemetry Middleware):** Engineered custom ASGI middleware injecting correlation tracking (`X-Request-ID`) and sub-millisecond process timers (`X-Process-Time`).
- **Day 4 (Navigation Shell & Responsive Layout):** Built unified app shell with role navigation, active route highlights, and system status indicators.
- **Day 5 (Diagnostics Tooling & Week 1 Close):** Created `scripts/doctor.py` verifying 8 subsystems before boot. Closed Week 1 with 6 passing baseline tests.

### Week 2: Relational Data Models & Patient Vault CRUD (Days 6–10)
- **Day 6 (Async PostgreSQL & Connection Pooling):** Built `backend/app/db/session.py` with `asyncpg` pooling (`pool_size=10`, `max_overflow=20`) and connection recycling.
- **Day 7 (User & PatientProfile Entities):** Authored `User` and `PatientProfile` models. Implemented 14-digit ABHA validation regex (`91-XXXX-XXXX-XXXX`) and `@abdm` address formats.
- **Day 8 (Doctor & Lab Facility Entities):** Implemented `DoctorProfile` (NMC registration, specialty, consultation fee, HPR ID) and `DiagnosticLabFacility` (NABL accreditation).
- **Day 9 (Alembic Migration 0001 & Seeder):** Authored baseline migration `0001_initial_core_schema`. Created idempotent database seeding CLI (`scripts/seed-db.py`).
- **Day 10 (Patient Vault CRUD API & Week 2 Close):** Built REST endpoints for patient profile creation, retrieval, updates, and soft deletion. Reached **52 passing tests (100% pass rate in 1.85s)**.

### Week 3: Authentication, 4-Tier RBAC & Clean SaaS UI (Days 11–15)
- **Day 11 (Supabase Auth & JWT Middleware):** Integrated JWT signature verification decoding claims and extracting user UUID and email.
- **Day 12 (4-Tier RBAC & Security Guards):** Created declarative `RoleChecker` dependency supporting `PATIENT`, `DOCTOR`, `LAB_TECHNICIAN`, and `ADMIN`. Added cross-patient access boundary guards.
- **Day 13 (Doctor EMR Directory API):** Built `/api/v1/doctors` directory with specialty filters, search queries, and consultation fee sorting.
- **Day 14 (Clean SaaS UI Transformation):** Redesigned frontend using modern SaaS aesthetics: pure white `#ffffff` canvas, near-black `#111111` buttons, 1px borders, and 12px radii across all 3 portals.
- **Day 15 (Security Hardening & Rate Limiting):** Implemented sliding-window token-bucket rate limiter (`15 req/min` for auth; `60 req/min` general). Configured OWASP headers (CSP, HSTS, X-Frame-Options). Closed Week 3 with **115 passing tests**.

### Week 4: Clinical Encounters, Concurrency & Release v0.1.0 (Days 16–20)
- **Day 16 (DoctorSlot & Appointment Models):** Authored scheduling schema (Migration `0002`). Created slot generation engine computing discrete 30-minute consultation slots respecting doctor shifts and lunch breaks.
- **Day 17 (ACID Row-Level Concurrency & 10-Min Holds):** Implemented `SELECT ... FOR UPDATE` row locking during reservation. Created temporary slot holds (Migration `0003`) with deterministic HTTP 409 rejections. Built autonomous background sweeper (`sweep_expired_holds`).
- **Day 18 (HL7 FHIR R4 Transformers & ABDM CareContext):** Authored bidirectional transformers emitting standard FHIR R4 `Appointment`, `Encounter`, `Patient`, `Practitioner`, and `Bundle` resources. Linked encounters to ABDM CareContexts with SHA-256 cryptographic digests.
- **Day 19 (Interactive Slot Picker UI):** Built interactive slot booking UI with real-time 10-minute hold countdown timer on `/patient` and `/doctor`.
- **Day 20 (Month 1 Verification & Release v0.1.0):** Executed full end-to-end verification, concurrency stress tests, and WCAG accessibility audit. Tagged official release **`v0.1.0`** with **151 passing automated tests (100% pass rate in 17.67s)**.

---

## 6. Relational Data Model & Database Design

The relational schema is structured across 6 core entities with strict relational constraints:

```
+---------------------------------------------------------------------------------+
|                                 users Table                                     |
| id (UUID, PK) | email (VARCHAR, UK) | role (ENUM) | is_active | created_at      |
+---------------------------------------------------------------------------------+
         | 1:1                                  | 1:1                     | 1:1
         v                                      v                         v
+--------------------------+  +--------------------------+  +---------------------+
|  patient_profiles Table  |  |  doctor_profiles Table   |  | diagnostic_labs     |
| id (UUID, PK)            |  | id (UUID, PK)            |  | id (UUID, PK)       |
| user_id (UUID, FK, UK)   |  | user_id (UUID, FK, UK)   |  | user_id (UUID, FK)  |
| gender, date_of_birth    |  | registration_no (UK)     |  | facility_name       |
| blood_group              |  | specialty, fee           |  | license_no (UK)     |
| abha_number (UK)         |  | hpr_id (UK)              |  | nabl_acc_no (UK)    |
| abha_address (UK)        |  | is_teleconsult           |  | hfr_id (UK)         |
+--------------------------+  +--------------------------+  +---------------------+
         | 1:N                                  | 1:N
         |                                      v
         |                             +------------------------------------------+
         |                             |           doctor_slots Table             |
         |                             | id (UUID, PK)                            |
         |                             | doctor_id (UUID, FK)                     |
         |                             | start_time, end_time (TIMESTAMPTZ)       |
         |                             | status (available|held|booked|blocked)   |
         |                             | held_until (TIMESTAMPTZ)                 |
         |                             | held_by_patient_id (UUID, FK)            |
         |                             +------------------------------------------+
         |                                      | 1:1
         v                                      v
+---------------------------------------------------------------------------------+
|                              appointments Table                                 |
| id (UUID, PK) | patient_id (UUID, FK) | doctor_id (UUID, FK) | slot_id (UUID, FK)|
| scheduled_start | scheduled_end | status | appointment_type | clinical_notes    |
+---------------------------------------------------------------------------------+
```

### Alembic Migration History (Month 1):
1. **`2026_09_16_0001_initial_core_schema`:** Baseline tables for `users`, `patient_profiles`, `doctor_profiles`, and `diagnostic_labs`.
2. **`2026_09_28_0002_appointments_and_slots_schema`:** Added `doctor_slots` and `appointments` with foreign key relationships.
3. **`2026_09_29_0003_slot_concurrency_and_hold_fields`:** Added `held_until` and `held_by_patient_id` fields for temporary reservation holds.

---

## 7. Identity, Multi-Tenancy & 4-Tier RBAC

### 7.1 Multi-Tier Role Matrix
NIRMAYA enforces strict boundary isolation through four recognized user roles:
- **`PATIENT`:** Access restricted to own personal health profile, personal appointments, and shared health records.
- **`DOCTOR`:** Access to manage clinical availability slots, view booked appointments, and author encounter documentation.
- **`LAB_TECHNICIAN`:** Restricted to uploading and viewing diagnostic test findings.
- **`ADMIN`:** Superuser privileges for provider verification and platform audits.

### 7.2 Declarative Security Enforcement
```python
# Declarative role enforcement in FastAPI endpoints
@router.post("/slots/generate", response_model=APIResponse[list[DoctorSlotResponse]])
async def generate_slots(
    payload: SlotGenerationRequest,
    current_user: User = Depends(RoleChecker([UserRole.DOCTOR, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    ...
```

---

## 8. Concurrency Engineering: Conflict-Free Scheduling

A primary engineering innovation of Month 1 is the prevention of double-booking race conditions during high-concurrency booking traffic.

```
Patient A Request ──────────► [Acquire Row Lock: SELECT ... FOR UPDATE] ──► Status = HELD ──► Booking Confirmed (200 OK)
                                      ▲
                                      │ (Locks row during transaction)
                                      ▼
Patient B Request (Simultaneous) ───► [Blocked / Lock Contention] ────────► Checks Status ───► HTTP 409 Conflict
                                                                                               "SLOT_HELD_BY_ANOTHER_PATIENT"
```

1. **Row-Level Locking:** During reservation, the query executes `SELECT ... FROM doctor_slots WHERE id = :id FOR UPDATE`.
2. **State Verification:** If `status == 'available'` or `(status == 'held' and held_until < NOW())`, the lock is granted and updated to `HELD` with `held_until = NOW() + 10 MINUTES`.
3. **Deterministic Rejection:** Any competing transaction reading the row receives HTTP 409 Conflict with code `SLOT_HELD_BY_ANOTHER_PATIENT`.
4. **Autonomous Sweeper:** An asynchronous background task (`sweep_expired_holds`) periodically reclaims abandoned slots back to `AVAILABLE`.

---

## 9. Healthcare Interoperability: HL7 FHIR R4 & ABDM

### 9.1 HL7 FHIR Release 4 Mappings
Internal appointment and encounter records are converted into valid FHIR R4 JSON schemas:
- **FHIR `Appointment`:** Maps appointment status (`proposed`, `pending`, `booked`, `fulfilled`), scheduled start/end timestamps, and participant references (`Patient/<id>`, `Practitioner/<id>`).
- **FHIR `Encounter`:** Categorized using act codes `AMB` (ambulatory outpatient) and `VR` (virtual teleconsultation).
- **FHIR `Bundle`:** Serialized as `collection` bundles with metadata and SHA-256 cryptographic digests ensuring tamper-evidence.

### 9.2 ABDM Integration (Milestone 1)
- **14-Digit ABHA Identity:** Validated using the pattern `^[0-9]{2}-[0-9]{4}-[0-9]{4}-[0-9]{4}$`.
- **Healthcare Professional Registry (HPR):** Validated using `^HP[0-9]{2}-[0-9]{4}-[0-9]{4}$`.
- **CareContext Linkage:** Each completed encounter generates a deterministic ABDM CareContext ID (`APPT-XXXXXXXX`) enabling consent-based health information exchange.

---

## 10. Frontend Architecture & Clean SaaS Design System

The presentation tier is built using **Next.js 15 App Router** and styled with a clean SaaS design language:
- **Design Tokens:**
  - Canvas: Pure white (`#ffffff`) for maximum clarity.
  - Primary CTAs: Near-black (`#111111`) with smooth hover transitions.
  - Hairline Borders: 1px subtle gray (`#e5e7eb`).
  - Corner Radii: 12px for interactive cards, 16px for modal envelopes.
- **Portals Implemented:**
  - `/patient`: Health vault summary, ABHA details, and interactive slot picker.
  - `/doctor`: Practice schedule, incoming appointment queue, and profile settings.
  - `/lab`: Diagnostic facility registration and testing gateway.
  - `/login` & `/register`: Clean authentication views.

---

## 11. Verification, Testing & Performance Benchmarks

### 11.1 Quantitative Growth Metrics (Month 1)

| Dimension | Week 1 Baseline | Week 2 Close | Week 3 Close | Month 1 Finale (Week 4) | Total Growth |
|---|---|---|---|---|---|
| **Automated Tests** | 6 Tests | 52 Tests | 115 Tests | **151 Tests** | **+2,416%** |
| **Test Pass Rate** | 100% | 100% | 100% | **100% Pass** | Perfect Stability |
| **Pytest Runtime** | 0.14s | 1.85s | 22.10s | **17.67s** | Highly Optimized |
| **Frontend Routes** | 2 Pages | 5 Pages | 11 Routes | **11 Routes** | Prerendered Clean |
| **Alembic Migrations** | 0 Revisions | 1 Revision | 1 Revision | **3 Revisions** | Zero DDL drift |
| **Total Git Commits** | 25 Commits | 85 Commits | 160 Commits | **210+ Commits** | 10+ Daily Rule |

### 11.2 Concurrency Stress Testing
Using concurrent async pytest workers, the system was subjected to simulated simultaneous booking requests on the same slot. In 100% of test runs:
- Exactly **one** transaction secured the reservation.
- All competing transactions received deterministic HTTP 409 responses.
- **Zero** phantom or double bookings occurred.

---

## 12. Version Control Discipline & Commit Logs

Month 1 enforced an uncompromising development methodology:
- **10+ Atomic Micro-Commits Daily:** No massive end-of-day commits. Every commit represents a single logical unit of work with associated tests.
- **Strict Conventional Commits:** Standardized prefixes (`feat:`, `fix:`, `test:`, `refactor:`, `docs:`).
- **Official Milestone Tag:** Successfully tagged **`v0.1.0`** at the conclusion of Day 20.

---

## 13. Engineering Challenges & Implemented Solutions

1. **Challenge: Orphaned Slot Holds on Tab Close**  
   *Problem:* If a user abandons a booking by closing their browser, client-side timers cannot release the slot.  
   *Solution:* Authored the server-side autonomous background task `sweep_expired_holds` that evaluates `held_until < NOW()` and releases held slots unconditionally.
2. **Challenge: Reserved Keyword Collision in FHIR Schemas**  
   *Problem:* FHIR resources contain attributes named `class`, which is a reserved keyword in Python.  
   *Solution:* Configured Pydantic field aliases using `Field(alias='class')` with `populate_by_name=True`, ensuring valid internal code and valid external FHIR JSON.
3. **Challenge: Performance Overhead of Strict Validation**  
   *Problem:* Validating deeply nested FHIR resources can introduce route latency.  
   *Solution:* Leveraged Pydantic v2's Rust-compiled core, maintaining sub-millisecond execution times (`X-Process-Time` < 2ms).

---

## 14. Subsequent Phase Roadmap (Months 2–4)

With the Month 1 foundation complete, the subsequent phases expand into diagnostic clinical data:
- **Month 2 (Clinical Data & Observational Engine):** Problem Lists (SNOMED-CT), Vital Signs & LOINC Telemetry, Structured SOAP Clinical Encounter Notes, and Diagnostic Lab Orders/Results (`v0.2.0`).
- **Month 3 (Prescriptions & Advanced Exchange):** Structured E-Prescriptions (`MedicationRequest`), Drug interaction checking, and full FHIR Document Bundles (`v0.3.0`).
- **Month 4 (Hardening, Cloud & Defense):** Cloud deployment (Docker/Kubernetes), simulated ABDM M2/M3 consent network, academic thesis, and project defense (`v1.0.0`).

---

## 15. Conclusion & Review Committee Sign-Off

Month 1 of project NIRMAYA has met and exceeded all planned engineering milestones. The platform boasts a verified, high-performance architecture compliant with international healthcare standards (HL7 FHIR R4) and Indian national specifications (ABDM). All deliverables are backed by automated tests (151/151 passed), clean version control (210+ commits), and live production-ready code.

**Submitted By:**  
Suryansh Swarn  
Lead Developer & Candidate, Final Year Major Project  

**Reviewed & Accepted By:**  
Project Coordinator & Faculty Evaluation Committee  
Department of Computer Science & Engineering  
Date: October 2026  
