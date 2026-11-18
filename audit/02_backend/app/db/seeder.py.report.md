# Audit Report: `backend/app/db/seeder.py`

**Path**: `backend/app/db/seeder.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 143 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Asynchronous database seeding engine populating synthetic clinical fixtures and managing database reset · Risk: **S2 (Medium Risk)** · Verdict: **READY-WITH-FIXES** · Missing environment guard in `clear_database` permits catastrophic data deletion if invoked in production.

---

## Layer B — Explain It
- **What problem this file solves**: Provides idempotent initialization and test database resets, populating the database with users, patient profiles, clinician registrations, accredited lab facilities, and clinical formulary medications.
- **How it works step by step**:
  1. `clear_database` issues delete statements in reverse foreign key order (`Medication`, `Lab`, `Doctor`, `Patient`, `User`).
  2. `seed_database` verifies if each fixture entity already exists by email; inserts missing records.
  3. Flushes intermediate rows to resolve foreign key constraints (`user.id` assigned to profile `user_id`).
  4. Triggers clinical medication formulary seeder (`seed_medications_if_empty`).
  5. Commits all records and returns a statistical summary of inserted rows.
- **Concepts & patterns used**:
  - *Idempotent Seeding*: Checks existence before insertion, allowing repeated safe executions.
  - *Flush vs Commit*: Calls `await session.flush()` to populate generated UUIDs for child relations.
- **Key lines to read first**:
  - `backend/app/db/seeder.py:17-38`: Truncation sequence.
  - `backend/app/db/seeder.py:41-64`: Core seeding flow and reset handling.
  - `backend/app/db/seeder.py:74-90`: Patient profile creation.
- **How to change it safely**:
  - When adding new entity tables with foreign keys, add them to `clear_database` in reverse dependency order to prevent constraint violation exceptions.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `sqlalchemy.delete`, `sqlalchemy.select`, `sqlalchemy.ext.asyncio.AsyncSession`, `app.db.fixtures.*`.
   - **Imported by**: `scripts/seed-db.py`, `backend/tests/conftest.py`, `backend/app/api/v1/endpoints/demo.py`.
   - **Public surface**: `clear_database`, `seed_database`.

2. **Security [SEC]**:
   - *CWE-284 (Improper Access Control) & CWE-269 (Improper Privilege Management) / OWASP A01:2021*:
     Neither `clear_database` nor `seed_database` verifies `settings.is_production` before issuing destructive SQL `delete()` operations. If the demo endpoint (`/api/v1/demo/reset`) or a maintenance script is triggered in production, patient records will be completely erased.
   - *Passwordless Admin*: Line 69 creates the administrator user with `User(**ADMIN_FIXTURE)`, which does not set `hashed_password`. If local password auth is attempted, authentication fails or behaves unpredictably.

3. **Code quality [QUAL]**:
   - Idempotency checks (`select(User).where(User.email == ...)`) prevent duplicate key collisions.
   - Good transaction management with final `await session.commit()`.

4. **AI-generated smells [QUAL]**:
   - Late inline import on line 128: `from app.services.medication import seed_medications_if_empty` to break a circular dependency.

5. **Performance [PERF]**:
   - Executes individual queries per fixture item. Fine for small fixture datasets (<100 rows), but bulk inserts (`session.add_all`) should be used for larger sets.

6. **Error handling & edge cases**:
   - Properly catches missing rows via `scalar_one_or_none()`.

7. **Doc accuracy [DOC]**:
   - Matches seeder CLI instructions in `README.md`.

8. **Tests**:
   - Tested in `backend/tests/test_db_seeder.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-SEED-F01** | **S2** | `[SEC]` | `17-39, 57-59` | No environment safety guard preventing table truncation in production | `async def clear_database(session: AsyncSession):` | Block execution if `settings.is_production` is True |
| **BE-SEED-F02** | **S3** | `[QUAL]` | `128` | Late function-level import to avoid circular dependency | `from app.services.medication import ...` | Restructure imports or use dependency injection |

---

## Suggested Patches (NOT Applied)

### Patch BE-SEED-P01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/db/seeder.py
+++ b/backend/app/db/seeder.py
@@ -7,2 +7,3 @@ from typing import Any, Dict
 from sqlalchemy import delete, select
 from sqlalchemy.ext.asyncio import AsyncSession
+from app.core.config import settings
@@ -17,2 +18,4 @@ async def clear_database(session: AsyncSession) -> Dict[str, int]:
     """Truncate all core entities in reverse foreign key order."""
+    if settings.is_production:
+        raise RuntimeError("CRITICAL: clear_database is forbidden in production environments.")
     from app.models.doctor import DoctorProfile
```

---

## Verdict
**READY-WITH-FIXES** — Reliable synthetic seeder; adding a production guard to `clear_database` is critical to prevent accidental data loss.
