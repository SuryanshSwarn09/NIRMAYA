# Month 1: Foundation, Schemas & Authentication

**Milestone Target:** Establish the monolithic monorepo foundation, clinical relational schemas, Supabase RBAC authentication, transactional appointment scheduling with ACID row-locking, and HL7 FHIR Release 4 Encounter bundle export (**Milestone Release `v0.1.0`**).

---

## 1. Month 1 Architectural Scope

Month 1 laid the enterprise foundation of Project NIRMAYA across four structured weeks:
- **Week 1: Monorepo Setup & UI Foundation (Days 1–5):** Next.js 15 App Router scaffold, Tailwind CSS v4 clinical design tokens, FastAPI asynchronous core settings, telemetry middleware, and unified navigation shell.
- **Week 2: Relational Schemas & Patient Vault (Days 6–10):** PostgreSQL 16 entity models (User, PatientProfile, DoctorProfile, DiagnosticLabFacility), Alembic migrations `0001`, seeder scripts, and Patient Vault CRUD API.
- **Week 3: Authentication & RBAC Security (Days 11–15):** Supabase Auth integration, JWT Bearer token validation, multi-role access control (`patient`, `doctor`, `lab`, `admin`), Cal.com modern SaaS design system transformation, and security hardening.
- **Week 4: Clinical Encounters & Month 1 Close (Days 16–20):** Appointment scheduling models, DoctorSlot generation algorithms, ACID row-level locking (`SELECT FOR UPDATE`), 10-minute Redis TTL slot holds, HL7 FHIR R4 Encounter bundle export, and Milestone `v0.1.0` release.

---

## 2. Weekly Breakdown

| Week | Title & Focus | Days | Key Deliverables & Interoperability |
|---|---|---|---|
| **Week 1** | Monorepo Setup & UI Foundation | Days 1–5 | Next.js 15, FastAPI async core, Tailwind CSS v4 clinical palette, UI primitives (`Badge`, `Button`, `Card`), health check API. |
| **Week 2** | Relational Schemas & Patient Vault | Days 6–10 | PostgreSQL models, Alembic migration `0001_initial_core_schema`, database seeder, Patient Vault REST endpoints. |
| **Week 3** | Authentication & RBAC Security | Days 11–15 | Supabase Auth JWT middleware, Role-Based Access Control, Doctor EMR directory, Cal.com design system migration, rate limiting. |
| **Week 4** | Clinical Encounters & Month 1 Close | Days 16–20 | Appointment scheduling, conflict-free slot holds, HL7 FHIR R4 Encounter serialization, full verification, and Release `v0.1.0`. |

---

## 3. Month 1 Milestones Achieved

- **130+ Atomic Micro-Commits:** Authored under conventional commit standards.
- **Milestone v0.1.0 Released:** Verified with 130+ backend tests passing 100%.
- **Zero Schema Drift:** All database entities versioned through Alembic migrations.
- **Production Cal.com UI:** Unified clinical design system with responsive layouts and pure white canvases.
