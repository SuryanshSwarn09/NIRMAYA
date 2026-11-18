# Audit Report: `backend/app/db/tenant_context.py`

**Path**: `backend/app/db/tenant_context.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 93 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Multi-tenant context isolation and PostgreSQL Row-Level Security (RLS) session manager · Risk: **S1 (High Risk)** · Verdict: **READY-WITH-FIXES** · Direct trust in unauthenticated client HTTP headers (`X-Tenant-ID`, `X-User-ID`, `X-User-Role`) allows complete spoofing of PostgreSQL RLS security context.

---

## Layer B — Explain It
- **What problem this file solves**: Provides tenant-aware database sessions where PostgreSQL transaction variables (`app.current_tenant`, `app.current_user`, `app.jurisdiction_path`) are populated for Row-Level Security (RLS) policies.
- **How it works step by step**:
  1. Manages task-local context using Python's `contextvars.ContextVar`.
  2. `get_tenant_db` extracts tenant headers (`X-Tenant-ID`, `X-User-ID`, `X-Jurisdiction-Path`, `X-User-Role`).
  3. `apply_tenant_context_to_session` executes `SET LOCAL app.current_tenant = ...` within the PostgreSQL transaction.
  4. Yields session to the route handler and resets context on completion.
- **Concepts & patterns used**:
  - *Row-Level Security (RLS)*: Database-level enforcement of tenant data isolation.
  - *Session-Local Configuration (`SET LOCAL`)*: Variables exist only for the lifespan of the current SQL transaction.
  - *ContextVars*: Thread/task-safe propagation of request metadata across coroutines.
- **Key lines to read first**:
  - `backend/app/db/tenant_context.py:17-30`: ContextVar declaration and accessors.
  - `backend/app/db/tenant_context.py:32-63`: PostgreSQL `SET LOCAL` injection logic.
  - `backend/app/db/tenant_context.py:65-81`: Header extraction in `get_tenant_db`.
- **How to change it safely**:
  - Must bind tenant parameters to the verified `current_user` JWT subject rather than raw request headers.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `contextvars`, `fastapi.Header`, `sqlalchemy.text`, `app.db.session.AsyncSessionLocal`, `app.schemas.security_scanner.TenantContextParams`.
   - **Imported by**: Multi-tenant endpoints in `backend/app/api/v1/endpoints/` and territorial command center routes.
   - **Public surface**: `get_current_tenant_context`, `set_current_tenant_context`, `apply_tenant_context_to_session`, `get_tenant_db`.

2. **Security [SEC]**:
   - *CWE-287 (Improper Authentication) & CWE-306 / OWASP A01:2021*: Lines 65-80 define:
     ```python
     async def get_tenant_db(
         x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
         x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
         x_jurisdiction_path: Optional[str] = Header("india", alias="X-Jurisdiction-Path"),
         x_role: Optional[str] = Header(None, alias="X-User-Role"),
     )
     ```
     Any unauthenticated client can send arbitrary values in these headers (e.g. `X-Tenant-ID: victim-hospital`, `X-User-Role: ADMIN`), which are directly injected into PostgreSQL session variables via `SET LOCAL`. If RLS policies rely on these variables, the entire multi-tenant security boundary is compromised.
   - Tenant variables must be derived from the cryptographically verified JWT bearer token via `Depends(get_current_user)`.

3. **Code quality [QUAL]**:
   - Proper use of `contextvars.Token` and `reset()` in line 92 ensures no context leakage between pooled async tasks.
   - Graceful SQLite fallback: detects dialect and skips `SET LOCAL` when running unit tests on SQLite.

4. **AI-generated smells [QUAL]**:
   - Prototype header-based parameter passing left in database security infrastructure.

5. **Performance [PERF]**:
   - Incurs 3-4 small `SET LOCAL` queries at the start of each transaction. For high-throughput endpoints, `set_config('app.var', value, true)` in a single multi-variable statement is faster.

6. **Error handling & edge cases**:
   - Rollback and reset handled safely in `try...finally`.

7. **Doc accuracy [DOC]**:
   - Documents RLS support, but does not disclose that headers are currently unauthenticated.

8. **Tests**:
   - Tested in `backend/tests/test_tenant_isolation.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-TEN-F01** | **S1** | `[SEC]` | `65-80` | Unverified client HTTP headers dictate PostgreSQL RLS context | `x_tenant_id = Header(...)` injected into `SET LOCAL` | Extract tenant/user/role from authenticated JWT `User` |
| **BE-TEN-F02** | **S3** | `[QUAL]` | `46-62` | Multiple sequential `SET LOCAL` queries | 4 separate `execute()` calls | Combine using `SELECT set_config(...)` |

---

## Suggested Patches (NOT Applied)

### Patch BE-TEN-P01 · risk of change: med · [UNTESTED]
```diff
--- a/backend/app/db/tenant_context.py
+++ b/backend/app/db/tenant_context.py
@@ -7,3 +7,5 @@ from contextvars import ContextVar
 from typing import AsyncGenerator, Dict, Optional
-from fastapi import Header, HTTPException, status
+from fastapi import Depends, Header, HTTPException, status
+from app.core.dependencies import get_current_user
+from app.models.user import User
 from sqlalchemy import text
@@ -65,6 +67,3 @@ async def apply_tenant_context_to_session(
 async def get_tenant_db(
-    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
-    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
-    x_jurisdiction_path: Optional[str] = Header("india", alias="X-Jurisdiction-Path"),
-    x_role: Optional[str] = Header(None, alias="X-User-Role"),
+    current_user: User = Depends(get_current_user),
 ) -> AsyncGenerator[AsyncSession, None]:
@@ -75,4 +74,4 @@ async def get_tenant_db(
     tenant_params = TenantContextParams(
-        tenant_id=x_tenant_id or "default-facility",
-        user_id=x_user_id or "system-user",
-        jurisdiction_path=x_jurisdiction_path or "india",
-        role=x_role or "CLINICIAN",
+        tenant_id=getattr(current_user, "facility_id", "default-facility"),
+        user_id=current_user.id,
+        jurisdiction_path=getattr(current_user, "jurisdiction_path", "india"),
+        role=current_user.role.value,
     )
```

---

## Verdict
**READY-WITH-FIXES** — The ContextVar and PostgreSQL session parameter design is sound; integrating with JWT authentication is required to prevent RLS context spoofing.
