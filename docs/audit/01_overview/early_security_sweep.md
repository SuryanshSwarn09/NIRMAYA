# Early Security Sweep & Attack Surface Baseline

**Audit Layer**: `01_overview`  
**Date**: 2026-11-18  
**Scope**: Read-only static sweep of committed secrets, environment fallback vulnerabilities, `.gitignore` gaps, CORS policies, debug flags, and default credentials.  
**Auditor**: Principal Software Auditor & Technical Writer

---

## 1. Executive Summary

This early security sweep established a baseline analysis of repository configuration, runtime entry points, and credential handling prior to per-file deep inspection. 

- **Highest Finding Severity**: **S1 (High Risk)**
- **Verdict**: **READY-WITH-FIXES**
- **Core Concerns**: Hardcoded fallback values for JWT secrets, database connection URLs, and third-party integration keys present in `backend/app/core/config.py` and `docker-compose.yml`; enabled `DEBUG = True` by default in backend configuration; query-string transmission of JWT tokens for WebSocket connections; and potential `.gitignore` gaps for non-local environment files.

---

## 2. Findings Matrix

| ID | Sev | Tag | CWE / OWASP | File & Line | Summary of Issue |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **SEC-01-01** | **S1** | `[SEC]` | CWE-798 / A07:2021 | `backend/app/core/config.py:25-28` | Hardcoded default fallback `SECRET_KEY` permits forged JWTs if environment variable is omitted. |
| **SEC-01-02** | **S1** | `[SEC]` | CWE-798 / A07:2021 | `docker-compose.yml:87-89` | Hardcoded fallback credentials for `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, and `SECRET_KEY`. |
| **SEC-01-03** | **S2** | `[SEC]` | CWE-489 / A05:2021 | `backend/app/core/config.py:22-23` | `DEBUG = True` enabled by default leaks stack traces and internal routes if not explicitly overridden. |
| **SEC-01-04** | **S2** | `[SEC]` | CWE-798 / A07:2021 | `backend/app/core/config.py:51` | Hardcoded default PostgreSQL credentials (`postgres:[REDACTED]`) in connection string. |
| **SEC-01-05** | **S2** | `[SEC]` | CWE-798 / A07:2021 | `backend/alembic.ini:32` | Hardcoded default PostgreSQL credentials in migration configuration. |
| **SEC-01-06** | **S2** | `[SEC]` | CWE-598 / A02:2021 | `backend/app/core/config.py:165-168` | JWT token passed via URL query parameter (`?token=`) for WebSocket authentication leaks into server/proxy logs. |
| **SEC-01-07** | **S3** | `[SEC]` | CWE-942 / A05:2021 | `backend/app/main.py:60-66` | CORS middleware allows wildcard methods (`allow_methods=["*"]`) and headers with `allow_credentials=True`. |
| **SEC-01-08** | **S3** | `[SEC]` | CWE-538 / A05:2021 | `.gitignore:23-25` | Incomplete environment ignore pattern (`.env.*.local` misses `.env.production` or `.env.staging` if created locally). |

---

## 3. Detailed Finding Analysis

### Finding SEC-01-01: Hardcoded Default Fallback for JWT `SECRET_KEY`
- **Location**: `backend/app/core/config.py:25-28`
- **CWE / OWASP**: CWE-798 (Use of Hard-coded Credentials) / OWASP A07:2021 Identification and Authentication Failures
- **Evidence**:
  ```python
  # backend/app/core/config.py:25-28
  SECRET_KEY: str = Field(
      default="[REDACTED]",
      description="Core JWT signing secret",
  )
  ```
- **Impact**: If `SECRET_KEY` is not provided in a deployed environment, the application falls back to a publicly known static key, allowing any attacker to forge valid administrative and clinician JWTs.
- **Remediation**: Remove default string value in production or enforce a validator that raises a `ValueError` on startup if `ENVIRONMENT == "production"` and the secret matches the default or has entropy < 32 bytes.

### Finding SEC-01-02: Hardcoded Fallback Credentials in Docker Compose
- **Location**: `docker-compose.yml:87-89`
- **CWE / OWASP**: CWE-798 / OWASP A07:2021
- **Evidence**:
  ```yaml
  # docker-compose.yml:87-89
  DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-nirmaya_user}:${POSTGRES_PASSWORD:-[REDACTED]}@postgres:5432/${POSTGRES_DB:-nirmaya}
  REDIS_URL: redis://:${REDIS_PASSWORD:-[REDACTED]}@redis:6379/0
  SECRET_KEY: ${SECRET_KEY:-[REDACTED]}
  ```
- **Impact**: If run without an external `.env` file, the cluster initializes with static predictable credentials across database, cache, and token signing.
- **Remediation**: Use mandatory variable syntax (`${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}`) to fail fast during container orchestration.

### Finding SEC-01-03: Default `DEBUG = True` Flag
- **Location**: `backend/app/core/config.py:22-23` and `backend/app/main.py:43`
- **CWE / OWASP**: CWE-489 (Active Debug Code) / OWASP A05:2021 Security Misconfiguration
- **Evidence**:
  ```python
  # backend/app/core/config.py:22-23
  ENVIRONMENT: Literal["development", "staging", "production"] = "development"
  DEBUG: bool = True
  ```
- **Impact**: When `DEBUG` is true, FastAPI formats uncaught exceptions with full stack traces, local variable context, and internal file paths in HTTP 500 error responses.
- **Remediation**: Default `DEBUG: bool = False` and set conditionally based on `ENVIRONMENT == "development"`.

### Finding SEC-01-04 & SEC-01-05: Default Database Credentials
- **Location**: `backend/app/core/config.py:51` and `backend/alembic.ini:32`
- **CWE / OWASP**: CWE-798 / OWASP A07:2021
- **Evidence**:
  ```python
  # backend/app/core/config.py:51
  DATABASE_URL: str = Field(
      default="postgresql+asyncpg://postgres:[REDACTED]@localhost:5432/nirmaya",
      description="Async PostgreSQL connection string",
  )
  ```
  ```ini
  # backend/alembic.ini:32
  sqlalchemy.url = postgresql+psycopg2://postgres:[REDACTED]@localhost:5432/nirmaya
  ```
- **Impact**: Default PostgreSQL superuser credentials (`postgres:[REDACTED]`) are embedded in source and configuration.
- **Remediation**: Rely on environment variable injection; remove credentials from `alembic.ini` and read via `app.core.config.settings.sync_database_url` inside `alembic/env.py`.

### Finding SEC-01-06: WebSocket Authentication via URL Query Parameter
- **Location**: `backend/app/core/config.py:165-168` and `backend/app/api/v1/endpoints/websockets.py`
- **CWE / OWASP**: CWE-598 (Use of GET Request Method With Sensitive Query Strings) / OWASP A02:2021 Cryptographic Failures
- **Evidence**:
  ```python
  # backend/app/core/config.py:165-168
  WS_TOKEN_PARAM: str = Field(
      default="token",
      description="Query parameter name containing client JWT auth token",
  )
  ```
- **Impact**: WebSocket connections (`/ws/events?token=ey...`) expose bearer tokens in URL query strings, persisting them in reverse proxy access logs (Caddy/Nginx) and browser history.
- **Remediation**: Authenticate WebSocket upgrades using HTTP-Only session cookies or initial post-handshake authorization ticket frames.

### Finding SEC-01-07: Permissive CORS Method and Header Allowances
- **Location**: `backend/app/main.py:60-66`
- **CWE / OWASP**: CWE-942 (Permissive Cross-Domain Policy) / OWASP A05:2021 Security Misconfiguration
- **Evidence**:
  ```python
  # backend/app/main.py:60-66
  app.add_middleware(
      CORSMiddleware,
      allow_origins=get_allowed_origins(),
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- **Impact**: Combining `allow_credentials=True` with wildcard methods (`["*"]`) and headers increases exploit surface if an authorized origin is vulnerable to XSS.
- **Remediation**: Explicitly restrict methods to `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]` and enumerate permitted headers (`["Authorization", "Content-Type", "X-Request-ID"]`).

### Finding SEC-01-08: Local Environment File Pattern Gaps in `.gitignore`
- **Location**: `.gitignore:23-25`
- **CWE / OWASP**: CWE-538 (Data Leakage Through Repository Inclusion) / OWASP A05:2021
- **Evidence**:
  ```gitignore
  # .gitignore:23-25
  .env
  .env.local
  .env.*.local
  ```
- **Impact**: Files named `.env.production`, `.env.staging`, or `.env.edge` (without `.local` suffix) are not excluded by git, presenting a risk of accidental secret check-in.
- **Remediation**: Update pattern to `.env*` and exclude only explicit templates:
  ```gitignore
  .env*
  !.env.example
  !.env.*.example
  ```

---

## 4. Suggested Unapplied Patches

### Patch SEC-01-01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/core/config.py
+++ b/backend/app/core/config.py
@@ -25,4 +25,4 @@ class Settings(BaseSettings):
     SECRET_KEY: str = Field(
-        default="nirmaya-super-secret-dev-key-change-in-production-2026",
+        default="",
         description="Core JWT signing secret",
     )
@@ -176,2 +176,6 @@ class Settings(BaseSettings):
+    def model_post_init(self, __context):
+        if self.is_production and (not self.SECRET_KEY or len(self.SECRET_KEY) < 32):
+            raise ValueError("Production environment requires a high-entropy SECRET_KEY >= 32 characters.")
+
```

### Patch SEC-01-02 · risk of change: low · [UNTESTED]
```diff
--- a/docker-compose.yml
+++ b/docker-compose.yml
@@ -87,3 +87,3 @@ services:
-      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-nirmaya_user}:${POSTGRES_PASSWORD:-nirmaya_secure_pass_2026}@postgres:5432/${POSTGRES_DB:-nirmaya}
-      REDIS_URL: redis://:${REDIS_PASSWORD:-nirmaya_redis_pass_2026}@redis:6379/0
-      SECRET_KEY: ${SECRET_KEY:-nirmaya_production_super_secret_jwt_key_2026_xyz}
+      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:?POSTGRES_USER required}:${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}@postgres:5432/${POSTGRES_DB:-nirmaya}
+      REDIS_URL: redis://:${REDIS_PASSWORD:?REDIS_PASSWORD required}@redis:6379/0
+      SECRET_KEY: ${SECRET_KEY:?SECRET_KEY required}
```

### Patch SEC-01-03 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/core/config.py
+++ b/backend/app/core/config.py
@@ -22,2 +22,2 @@ class Settings(BaseSettings):
     ENVIRONMENT: Literal["development", "staging", "production"] = "development"
-    DEBUG: bool = True
+    DEBUG: bool = False
```

### Patch SEC-01-07 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/main.py
+++ b/backend/app/main.py
@@ -63,3 +63,3 @@ app.add_middleware(
     allow_credentials=True,
-    allow_methods=["*"],
-    allow_headers=["*"],
+    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
+    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
 )
```

### Patch SEC-01-08 · risk of change: low · [UNTESTED]
```diff
--- a/.gitignore
+++ b/.gitignore
@@ -23,3 +23,3 @@ backend/env/
-.env
-.env.local
-.env.*.local
+.env*
+!.env.example
+!.env.*.example
```
