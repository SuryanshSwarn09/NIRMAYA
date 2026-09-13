# Day 6: SQLAlchemy 2.0 Async Engine, Connection Pooling & Alembic Scaffold

**Date:** September 13, 2026  
**Milestone:** 02-01 (Opening Week 2: Database Schemas & Persistence)  
**Focus Area:** Asynchronous Relational Engine, Connection Pool Tuning, Session Dependency Lifecycle, Database Health Probe, and Alembic Migration Environment

---

## 1. Objectives

Week 2 transitions NIRMAYA from monorepo foundation to **relational persistence, clinical data modeling, and schema migrations**. Day 6 establishes the underlying asynchronous database architecture:
1. **Engine & Connection Pooling:** Configure SQLAlchemy 2.0 `create_async_engine` with PostgreSQL 16 connection pooling (`pool_size=10`, `max_overflow=20`, `pool_timeout=30s`, `pool_recycle=3600s`, `pool_pre_ping=True`).
2. **Session Dependency Lifecycle (`get_db`):** Implement an async session factory (`AsyncSessionLocal`) and a deterministic generator dependency providing automatic commit on success, rollback on exception, and guaranteed session closure.
3. **Active Health & Latency Probe (`check_db_health`):** Build an active probe executing `SELECT 1` with microsecond-level latency benchmarking, integrated directly into `/api/v1/health` with a protective 2.0-second timeout.
4. **Alembic Asynchronous Scaffold:** Configure `alembic.ini`, `alembic/env.py`, and `script.py.mako` supporting `asyncpg` via `run_sync` and reflecting NIRMAYA's `Base.metadata`.
5. **Standalone Database CLI Validator:** Provide `scripts/db-check.py` allowing developers to inspect pool parameters and test database connectivity prior to launching full server processes.
6. **Automated Unit Testing:** Establish test coverage for base mixins, async session lifecycles, and health probe telemetry.

---

## 2. Engineering Work Completed

### 1. Database Settings & Computed URLs (`backend/app/core/config.py`)
- Added connection pool parameters: `DATABASE_POOL_TIMEOUT = 30` and `DATABASE_POOL_RECYCLE = 3600`.
- Added computed property `sync_database_url` dynamically converting `postgresql+asyncpg://` into `postgresql+psycopg2://` for Alembic offline inspection and synchronous migration tools.

### 2. Async Engine & Session Factory (`backend/app/db/session.py`)
- Instantiated global `async_engine` configured with connection pool parameters, echo toggling, and `pool_pre_ping=True`.
- Created `AsyncSessionLocal` using `async_sessionmaker(expire_on_commit=False, autoflush=False)`.

### 3. Session Dependency & Latency Probe (`backend/app/db/session.py`, `app/db/__init__.py`)
- Implemented `get_db() -> AsyncGenerator[AsyncSession, None]` with strict transaction safety.
- Built `check_db_health(engine: AsyncEngine | None = None) -> Dict[str, Any]` executing `SELECT 1` and measuring query round-trip latency in milliseconds.
- Re-exported all database primitives from `backend/app/db/__init__.py`.

### 4. Database Health Schemas & Probe Integration (`backend/app/schemas/health.py`, `app/api/v1/endpoints/health.py`)
- Enhanced `DatabaseHealth` Pydantic schema with `driver`, `database_type`, `latency_ms`, `error`, and `pool_size`.
- Integrated `check_db_health()` with `asyncio.wait_for(timeout=2.0)` into `/api/v1/health`. If the database is unreachable, the endpoint returns `200 OK` with degraded status diagnostics rather than failing with an unhandled exception.

### 5. Asynchronous Alembic Migration Environment (`backend/alembic/`)
- Initialized `alembic.ini` with standard directory and script location.
- Implemented `alembic/env.py` utilizing `async_engine_from_config` and `connection.run_sync(do_run_migrations)`.
- Bound `target_metadata` to NIRMAYA's `Base.metadata` in `app.db.base`.
- Created `alembic/script.py.mako` migration template and `alembic/versions/.gitkeep`.

### 6. Standalone CLI Database Probe (`scripts/db-check.py`)
- Built a command-line connectivity probe script displaying target connection parameters, pool configuration, ping latency, and actionable Docker setup instructions if unreachable.

---

## 3. Verification & Build Results

### Pre-flight Diagnostic Doctor (`python scripts/doctor.py`):
```text
================================================================
       NIRMAYA System Diagnostic & Pre-Flight Validator         
================================================================

[Python Environment]
  Version: 3.11.7
  Status:  PASS (>= 3.11 compatible)

[Backend Dependencies & Venv]
  Venv:    FOUND (backend\.venv)
  Package: fastapi      -> CHECK VENV
  Package: pydantic     -> CHECK VENV
  Package: sqlalchemy   -> CHECK VENV
  Package: alembic      -> CHECK VENV
  Package: asyncpg      -> CHECK VENV
  Package: pytest       -> CHECK VENV
  Package: httpx        -> CHECK VENV

[Configuration & Secrets Check]
  Backend .env.example      -> PRESENT
  Frontend .env.example     -> PRESENT
  Alembic Config            -> PRESENT
  GitBook Docs YAML         -> PRESENT
  GitBook Summary           -> PRESENT

[OK] NIRMAYA Pre-Flight Check PASSED! Ready for development.
```

### Automated Pytest Suite (`15/15 tests passing`):
```text
tests/test_db_base.py::test_declarative_base_tablename_derivation PASSED [  6%]
tests/test_db_base.py::test_uuid_primary_key_mixin_schema PASSED         [ 13%]
tests/test_db_base.py::test_timestamp_mixin_schema PASSED                [ 20%]
tests/test_db_base.py::test_entity_persistence_with_mixins PASSED        [ 26%]
tests/test_db_session.py::test_check_db_health_success_with_sqlite PASSED [ 33%]
tests/test_db_session.py::test_check_db_health_failure_handling PASSED   [ 40%]
tests/test_db_session.py::test_get_db_session_generator_lifecycle PASSED [ 46%]
tests/test_db_session.py::test_get_db_session_rollback_on_exception PASSED [ 53%]
tests/test_exceptions.py::test_app_exception_attributes PASSED           [ 60%]
tests/test_exceptions.py::test_entity_not_found_exception PASSED         [ 66%]
tests/test_exceptions.py::test_permission_denied_exception PASSED        [ 73%]
tests/test_exceptions.py::test_not_found_error_payload_envelope PASSED   [ 80%]
tests/test_health.py::test_root_endpoint PASSED                          [ 86%]
tests/test_health.py::test_health_check_payload_structure PASSED         [ 93%]
tests/test_health.py::test_database_health_probe_mock_healthy PASSED     [100%]
============================= 15 passed in 2.85s ==============================
```

---

## 4. Next Daily Milestone: Day 7 (Tue)
- **Focus:** `feat(models): create user, role, and patient entity models`
- **Scope:** Define SQLAlchemy 2.0 relational models for `User` (UUID, email, role, supabase_uid) and `PatientProfile` (dob, gender, blood_group, emergency_contact), with foreign key constraints and Pydantic validation schemas.
