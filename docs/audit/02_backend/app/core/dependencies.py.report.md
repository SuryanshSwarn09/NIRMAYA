# Audit Report: `backend/app/core/dependencies.py`

**Path**: `backend/app/core/dependencies.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 249 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
FastAPI security dependencies for bearer JWT validation, user resolution, and role-based access control (RBAC) · Risk: **S1 (High Risk)** · Verdict: **READY-WITH-FIXES** · Global clinician bypass in `verify_patient_access` allows any doctor/lab to access any patient's records without active consultation or ABDM consent artefact.

---

## Layer B — Explain It
- **What problem this file solves**: Provides dependency injection guards (`Depends(get_current_user)`, `Depends(require_doctor)`) that authenticate incoming HTTP requests, decode JWT tokens, load the user from PostgreSQL, and enforce role permissions.
- **How it works step by step**:
  1. `get_token_payload` extracts bearer token from the `Authorization` header and decodes claims.
  2. `get_current_user` queries the database for the matching `User` entity, eagerly loading profiles (`patient_profile`, `doctor_profile`, `lab_facility`).
  3. `RoleChecker` verifies the actor has the required `UserRole` (or `ADMIN` superuser override).
  4. Specialized verification functions (`verify_patient_access`, `verify_patient_modification_access`, `verify_doctor_modification_access`) guard object-level modifications.
- **Concepts & patterns used**:
  - *Dependency Injection*: Decouples authentication logic from individual API route handlers.
  - *RBAC Guard*: `RoleChecker` class callable enforcing role boundaries.
  - *Object-Level Authorization*: Verifies ownership (`patient.user_id == current_user.id`) to prevent IDOR vulnerabilities.
- **Key lines to read first**:
  - `backend/app/core/dependencies.py:25-53`: Token extraction and claim validation.
  - `backend/app/core/dependencies.py:61-75`: User lookup query.
  - `backend/app/core/dependencies.py:137-158`: `RoleChecker` implementation.
  - `backend/app/core/dependencies.py:173-198`: `verify_patient_access` logic.
- **How to change it safely**:
  - Adding a new role requires updating `app.models.enums.UserRole` and creating a corresponding `require_<role>` helper.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `fastapi.Depends`, `fastapi.security.HTTPBearer`, `sqlalchemy.select`, `app.models.*`, `app.core.security.decode_access_token`.
   - **Imported by**: Mounted across all 59 endpoint modules in `backend/app/api/v1/endpoints/`.
   - **Public surface**: `get_token_payload`, `get_current_user`, `get_current_active_user`, `get_optional_current_user`, `require_patient`, `require_doctor`, `require_lab`, `require_admin`, `verify_patient_access`, `verify_patient_modification_access`.

2. **Security [SEC]**:
   - *CWE-285 (Improper Authorization) / OWASP A01:2021*: Lines 189-191 state:
     ```python
     if current_user.role in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB):
         return patient
     ```
     This permits any authenticated doctor or laboratory account to access any patient's complete demographic and clinical health records without checking for an active appointment, consultation, or ABDM consent artefact. Under DPDP Act 2023, access must be tied to verified patient consent.
   - *CWE-287 (Improper Authentication) / OWASP A07:2021*: Lines 61-64 match `User` via `or_(User.supabase_uid == sub, User.id == sub, User.email == email)`. If a token has an arbitrary `sub` but an email matching a target user, it binds to that user. The lookup should strictly require `sub` matching `supabase_uid` or `id`.
   - *Positive Controls*: Inactive accounts are blocked (`user.is_active` check); profile modifications strictly require account ownership or admin (`lines 216-221`).

3. **Code quality [QUAL]**:
   - Clean async SQLAlchemy 2.0 query patterns using `selectinload` to prevent N+1 query cascades on user profile relationships.

4. **AI-generated smells [QUAL]**:
   - Duplicated user resolution logic between `get_current_user` (lines 61-75) and `get_optional_current_user` (lines 116-130).

5. **Performance [PERF]**:
   - High-performance query with `selectinload`; single round-trip retrieves user and profile.

6. **Error handling & edge cases**:
   - Raises structured domain exceptions (`AuthenticationException`, `PermissionDeniedException`, `EntityNotFoundException`).

7. **Doc accuracy [DOC]**:
   - Matches API route documentation.

8. **Tests**:
   - Thoroughly tested in `backend/tests/test_auth_jwt.py`, `backend/tests/test_auth_rbac.py`, and `backend/tests/test_auth_dependencies.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-DEP-F01** | **S1** | `[SEC]` | `189-191` | Unrestricted patient health record access by any doctor or lab | `if current_user.role in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB): return patient` | Enforce active encounter or ABDM consent check |
| **BE-DEP-F02** | **S2** | `[SEC]` | `61-64` | Disjunctive OR query binds user on email alone | `conditions.append(User.email == str(payload.email))` | Disallow email-only fallback binding |
| **BE-DEP-F03** | **S3** | `[QUAL]` | `133-134` | Blanket exception suppression in optional user resolver | `except Exception: return None` | Catch specific `JWTError` / DB exceptions |

---

## Suggested Patches (NOT Applied)

### Patch BE-DEP-P01 · risk of change: med · [UNTESTED]
```diff
--- a/backend/app/core/dependencies.py
+++ b/backend/app/core/dependencies.py
@@ -61,4 +61,2 @@ async def get_current_user(
     conditions = [User.supabase_uid == payload.sub, User.id == payload.sub]
-    if payload.email:
-        conditions.append(User.email == str(payload.email))
 
```

### Patch BE-DEP-P02 · risk of change: med · [UNTESTED]
```diff
--- a/backend/app/core/dependencies.py
+++ b/backend/app/core/dependencies.py
@@ -189,3 +189,7 @@ async def verify_patient_access(
-    # Admin, Doctors, and Labs have clinical reading access; Patients can only view their own record
-    if current_user.role in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB):
+    # Admin has supervisory access; Patient has self-access
+    if current_user.role == UserRole.ADMIN:
         return patient
+
+    if current_user.role in (UserRole.DOCTOR, UserRole.LAB):
+        # TODO: Verify active appointment or valid ABDM consent artefact
+        return patient
```

---

## Verdict
**READY-WITH-FIXES** — Robust core RBAC mechanism; object-level consent verification must be hardened for DPDP Act 2023 compliance.
