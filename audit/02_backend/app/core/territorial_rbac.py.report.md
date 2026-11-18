# Audit Report: `backend/app/core/territorial_rbac.py`

**Path**: `backend/app/core/territorial_rbac.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 99 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Scoped Territorial Role-Based Access Control (TRBAC) enforcing Indian LGD 6-tier administrative boundaries · Risk: **S1 (High Risk)** · Verdict: **READY-WITH-FIXES** · Client HTTP header `X-Officer-Jurisdiction` directly dictates officer authority and defaults to `"india"` (full national root bypass) when omitted.

---

## Layer B — Explain It
- **What problem this file solves**: Restricts administrative and clinical surveillance queries to an inspecting officer's assigned administrative jurisdiction (e.g., district officer in `india.27.492` cannot inspect hospital data in `india.29.501`).
- **How it works step by step**:
  1. `is_territorial_access_allowed` evaluates if `officer_scope_path` covers `target_resource_path` via exact match, prefix match (`o_path + "."`), or national root bypass (`"india"`).
  2. `TerritorialSecurityScope` intercepts requests, reading `X-Officer-Jurisdiction` from request headers.
  3. Dispatches verification request to `delegation_service.validate_territorial_scope`.
  4. Raises HTTP 403 Forbidden if lateral or upward boundary violation occurs.
- **Concepts & patterns used**:
  - *Hierarchical RBAC (TRBAC)*: Models administrative command hierarchies using tree structures.
  - *LGD Integration*: Maps to India's Local Government Directory state and district codes.
- **Key lines to read first**:
  - `backend/app/core/territorial_rbac.py:14-34`: Path comparison logic.
  - `backend/app/core/territorial_rbac.py:44-61`: Header and query parameter extraction.
  - `backend/app/core/territorial_rbac.py:66-73`: Default fallback to `"india"`.
- **How to change it safely**:
  - Officer jurisdiction must be extracted from the authenticated user's JWT / database record, NOT from unverified request headers.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `fastapi.Depends`, `fastapi.Header`, `fastapi.Query`, `fastapi.HTTPException`, `app.services.delegation_service`.
   - **Imported by**: Administrative endpoints (`backend/app/api/v1/endpoints/administrative_hierarchy.py`, `command_center.py`).
   - **Public surface**: `is_territorial_access_allowed`, `TerritorialSecurityScope`, `require_territory`, `verify_command_center_access`.

2. **Security [SEC]**:
   - *CWE-287 (Improper Authentication) & CWE-306 (Missing Authentication for Critical Function) / OWASP A01:2021*:
     Lines 45-48 and 67 state:
     ```python
     x_officer_jurisdiction: Optional[str] = Header(None, ...)
     ...
     officer_path = _clean_str(x_officer_jurisdiction) or "india"
     ```
     And lines 23-24 state:
     ```python
     if o_path == "india":
         return True  # National root bypass
     ```
     Any unauthenticated user or low-privilege officer who omits `X-Officer-Jurisdiction` automatically defaults to `"india"`, granting complete national root access across all Indian states and districts! Furthermore, an attacker can simply send `X-Officer-Jurisdiction: india` to bypass all territorial checks.

3. **Code quality [QUAL]**:
   - Concise evaluation logic in `is_territorial_access_allowed`.

4. **AI-generated smells [QUAL]**:
   - Relying on simulated request headers (`X-Officer-Jurisdiction`) rather than integrating with `get_current_user` is a prototype scaffold that bypasses the actual authentication layer.

5. **Performance [PERF]**:
   - Fast string comparison (< 1ms).

6. **Error handling & edge cases**:
   - Safely rejects empty paths.

7. **Doc accuracy [DOC]**:
   - `docs/architecture/` claims cryptographically verified territorial delegation, but code currently accepts arbitrary client headers.

8. **Tests**:
   - Tested in `backend/tests/test_territorial_hierarchy.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-TRBAC-F01** | **S1** | `[SEC]` | `45-48, 67` | Insecure client header controls authority; defaults to full national root | `officer_path = _clean_str(x_officer_jurisdiction) or "india"` | Resolve officer jurisdiction from authenticated User model |
| **BE-TRBAC-F02** | **S2** | `[SEC]` | `23-24` | Hardcoded unconditional bypass on `"india"` string | `if o_path == "india": return True` | Require explicit `ADMIN` role for national root override |

---

## Suggested Patches (NOT Applied)

### Patch BE-TRBAC-P01 · risk of change: med · [UNTESTED]
```diff
--- a/backend/app/core/territorial_rbac.py
+++ b/backend/app/core/territorial_rbac.py
@@ -7,3 +7,5 @@ from typing import Any, Callable, Optional
 from fastapi import Depends, Header, HTTPException, Query, status
+from app.core.dependencies import get_current_active_user
+from app.models.user import User
+from app.models.enums import UserRole
 
@@ -44,4 +46,2 @@ class TerritorialSecurityScope:
     async def __call__(
-        self,
-        x_officer_jurisdiction: Optional[str] = Header(None),
         path: Optional[str] = Query(None),
@@ -52,2 +52,3 @@ class TerritorialSecurityScope:
         target_path: Optional[str] = Query(None),
+        current_user: User = Depends(get_current_active_user),
     ) -> str:
@@ -63,3 +64,7 @@ class TerritorialSecurityScope:
-        officer_path = _clean_str(x_officer_jurisdiction) or "india"
+        # Bind strictly to authenticated user's jurisdiction
+        officer_path = getattr(current_user, "jurisdiction_path", None)
+        if not officer_path:
+            officer_path = "india" if current_user.role == UserRole.ADMIN else "unassigned"
```

---

## Verdict
**READY-WITH-FIXES** — The hierarchical LGD concept is strong, but tying officer jurisdiction to authenticated user state instead of an arbitrary HTTP header is imperative.
