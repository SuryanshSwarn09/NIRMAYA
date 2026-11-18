# Audit Report: `backend/app/core/config.py`

**Path**: `backend/app/core/config.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 194 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Centralized Pydantic v2 application settings defining database, JWT security, ABDM sandbox, and Redis configurations · Risk: **S1 (High Risk)** · Verdict: **READY-WITH-FIXES** · Fallback defaults for `SECRET_KEY`, database URL, and third-party secrets risk authentication compromise if environment variables are omitted in production.

---

## Layer B — Explain It
- **What problem this file solves**: Provides a strongly-typed, validated configuration singleton (`settings = Settings()`) that ingests system environment variables, local `.env` files, and defaults for the entire FastAPI platform.
- **How it works step by step**:
  1. Defines `Settings` subclassing `pydantic_settings.BaseSettings`.
  2. Declares typed configuration attributes with default values.
  3. Validates environment literals (`ENVIRONMENT: Literal["development", "staging", "production"]`).
  4. Automatically derives secondary properties (`sync_database_url` for Alembic, `is_production`).
  5. Instantiates the global immutable `settings` singleton on module load.
- **Concepts & patterns used**:
  - *Settings Factory Pattern*: Encapsulates environment ingestion into a single immutable object.
  - *Computed Fields*: Dynamically derives driver compatibility strings (`sync_database_url`) using `@computed_field`.
- **Key lines to read first**:
  - `backend/app/core/config.py:25-28`: Definition of `SECRET_KEY`.
  - `backend/app/core/config.py:40-47`: Hardcoded default `BACKEND_CORS_ORIGINS`.
  - `backend/app/core/config.py:50-59`: PostgreSQL pool configuration (`pool_size=10`, `max_overflow=20`).
  - `backend/app/core/config.py:184-192`: Conversion between `postgresql+asyncpg` and synchronous `postgresql+psycopg2`.
- **How to change it safely**:
  - Adding a new variable requires adding a typed field and matching entry in `.env.example`.
  - Never remove `sync_database_url` as `backend/alembic/env.py` relies on it for schema migrations.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `pydantic_settings.BaseSettings`, `pydantic.Field`, `pydantic.computed_field`.
   - **Imported by**: Imported by almost every backend file (`main.py`, `dependencies.py`, `session.py`, `transformers.py`, etc.).
   - **Public surface**: Exports `Settings` and singleton instance `settings`.

2. **Security [SEC]**:
   - *CWE-798 / OWASP A07:2021*: Static default fallback for `SECRET_KEY: str = Field(default="[REDACTED]")`. In production, a missing variable silently falls back to this known string.
   - *CWE-798 / OWASP A07:2021*: Hardcoded database credentials in default `DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:[REDACTED]@localhost:5432/nirmaya")`.
   - *CWE-798 / OWASP A07:2021*: Hardcoded dummy tokens for `SUPABASE_JWT_SECRET` (`line 67`), `ABDM_CLIENT_SECRET` (`line 83`), and `DIGILOCKER_CLIENT_SECRET` (`line 109`).
   - *CWE-489 / OWASP A05:2021*: `DEBUG: bool = True` enabled by default (`line 22`).
   - *CWE-598 / OWASP A02:2021*: `WS_TOKEN_PARAM = "token"` (`line 165`) facilitates passing JWTs in URL query strings.
   - *CWE-613 / OWASP A07:2021*: `ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7` (7 days) without refresh token revocation increases the blast radius of stolen tokens.

3. **Code quality [QUAL]**:
   - Clean Pydantic v2 conventions. `SettingsConfigDict` properly configures case sensitivity and extra attributes (`ignore`).
   - Duplication: `BACKEND_CORS_ORIGINS` is hardcoded here and duplicated in `.env.example`.

4. **AI-generated smells [QUAL]**:
   - Overly verbose docstrings and redundant default fallback values designed to make local testing "just work" without configuration, inadvertently creating security loopholes in production.

5. **Performance [PERF]**:
   - Database connection pool settings (`pool_size=10`, `max_overflow=20`, `pool_timeout=30`, `pool_recycle=3600`) are well-tuned for typical concurrent async workloads.

6. **Error handling & edge cases**:
   - If an invalid type is passed in the environment (e.g. non-integer for `DATABASE_POOL_SIZE`), Pydantic raises `ValidationError` immediately during application startup, preventing broken runtime states.

7. **Doc accuracy [DOC]**:
   - `docs/architecture/` claims Zero-Trust configuration, but source defaults to permissive development flags.

8. **Tests**:
   - Tested indirectly in `backend/tests/test_health.py` and `backend/tests/test_auth_jwt.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-CFG-F01** | **S1** | `[SEC]` | `25-28` | Default static fallback for `SECRET_KEY` | `SECRET_KEY = "nirmaya-super-secret-dev-key..."` | Remove default or enforce validator for production |
| **BE-CFG-F02** | **S2** | `[SEC]` | `22-23` | Default `DEBUG = True` enabled | `DEBUG: bool = True` | Default to `False` unless explicitly set in dev |
| **BE-CFG-F03** | **S2** | `[SEC]` | `51` | Default DB URL includes credentials | `postgres:postgres@localhost:5432` | Empty default with required validation in production |
| **BE-CFG-F04** | **S2** | `[SEC]` | `67, 83, 109` | Hardcoded third-party secrets | `sbx-client-secret-placeholder-key-2026` | Empty default string |
| **BE-CFG-F05** | **S2** | `[SEC]` | `165-168` | WebSocket JWT query string token parameter | `WS_TOKEN_PARAM: str = "token"` | Switch to cookie-based or initial frame auth |
| **BE-CFG-F06** | **S3** | `[SEC]` | `29` | 7-day token expiration lifetime | `ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7` | Reduce access token lifetime to 15-60 minutes |

---

## Suggested Patches (NOT Applied)

### Patch BE-CFG-P01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/core/config.py
+++ b/backend/app/core/config.py
@@ -22,7 +22,7 @@ class Settings(BaseSettings):
     ENVIRONMENT: Literal["development", "staging", "production"] = "development"
-    DEBUG: bool = True
+    DEBUG: bool = False
 
     # Security & Tokens
     SECRET_KEY: str = Field(
-        default="nirmaya-super-secret-dev-key-change-in-production-2026",
+        default="",
         description="Core JWT signing secret",
@@ -176,2 +176,7 @@ class Settings(BaseSettings):
+    def model_post_init(self, __context):
+        if self.is_production:
+            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
+                raise ValueError("CRITICAL: Production requires SECRET_KEY with >= 32 characters.")
+            if "postgres:postgres" in self.DATABASE_URL:
+                raise ValueError("CRITICAL: Production cannot use default database credentials.")
```

---

## Verdict
**READY-WITH-FIXES** — Solid Pydantic v2 architecture, but production security requires eliminating static credential fallbacks.
