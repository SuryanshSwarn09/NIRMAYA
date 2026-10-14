# Week 2: Database Models & Patient Vault

**Milestone Target:** Design and implement the relational entity models, SQLAlchemy 2.0 async engine, connection pooling, initial Alembic database migration, idempotent seeder, and the Patient Health Vault CRUD API.

---

## Daily Schedule & Commit Breakdown

| Day | Focus Area | Key Deliverables | Status |
|---|---|---|---|
| **Day 6 (Mon)** | Async Engine, Pooling & Alembic | SQLAlchemy 2.0 asyncpg engine, connection pool lifecycle, Alembic environment | **Completed** |
| **Day 7 (Tue)** | User & Patient Profile Models | `User` entity, `PatientProfile` model with ABHA number/address, demographics | **Completed** |
| **Day 8 (Wed)** | Provider & Diagnostic Entities | `DoctorProfile` with medical council licenses, `DiagnosticLabFacility` with HFR ID | **Completed** |
| **Day 9 (Thu)** | Initial Migrations & Seeder | Alembic migration `0001_initial_core_schema`, automated database seeder | **Completed** |
| **Day 10 (Fri)** | Patient Vault CRUD API | REST endpoints for patient profiles, pagination envelopes, error handling | **Completed** |

---

## Week 2 Highlights

- PostgreSQL 16 database integration using `asyncpg` driver and connection pooling.
- Complete entity models for Users, Patients, Doctors, and Diagnostic Labs with 1:1 and 1:N relations.
- Baseline Alembic migration establishing foundational database tables and indexes.
- Idempotent clinical database seeder supporting quick-start development environments.
