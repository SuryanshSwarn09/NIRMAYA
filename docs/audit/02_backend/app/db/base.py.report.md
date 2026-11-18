# Audit Report: `backend/app/db/base.py`

**Path**: `backend/app/db/base.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 46 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
SQLAlchemy 2.0 DeclarativeBase and standard clinical entity mixins (`TimestampMixin`, `UUIDPrimaryKeyMixin`) · Risk: **S3 (Low Risk)** · Verdict: **READY-WITH-FIXES** · Solid 2.0 type-annotated DeclarativeBase; naive acronym table naming and string-based UUIDs over native PostgreSQL UUIDs.

---

## Layer B — Explain It
- **What problem this file solves**: Provides the root declarative base and common audit columns (UUID primary keys, UTC creation/update timestamps) inherited by all relational models.
- **How it works step by step**:
  1. `Base` subclasses SQLAlchemy 2.0 `DeclarativeBase`.
  2. Implements automatic snake_case `__tablename__` generation via `@declared_attr.directive`.
  3. `TimestampMixin` provides indexed `created_at` and auto-updating `updated_at`.
  4. `UUIDPrimaryKeyMixin` assigns a 36-character UUID4 string as the primary key.
- **Concepts & patterns used**:
  - *Declarative Mapping*: SQLAlchemy 2.0 `Mapped[...]` and `mapped_column(...)`.
  - *Mixin Pattern*: Reusable column sets mixed into model classes.
- **Key lines to read first**:
  - `backend/app/db/base.py:9-18`: DeclarativeBase and `__tablename__` directive.
  - `backend/app/db/base.py:20-34`: Timestamp audit mixin.
  - `backend/app/db/base.py:37-46`: UUID primary key mixin.
- **How to change it safely**:
  - Do not change column types here without generating a comprehensive Alembic migration.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `uuid`, `datetime`, `sqlalchemy.DateTime`, `sqlalchemy.String`, `sqlalchemy.orm.DeclarativeBase`, `Mapped`, `mapped_column`, `declared_attr`.
   - **Imported by**: All model files in `backend/app/models/` and `backend/alembic/env.py`.
   - **Public surface**: `Base`, `TimestampMixin`, `UUIDPrimaryKeyMixin`.

2. **Security [SEC]**:
   - UUID4 keys prevent sequential ID enumeration attacks (anti-scraping defense).
   - Timezones are explicitly preserved (`DateTime(timezone=True)`).

3. **Code quality [QUAL]**:
   - High-quality SQLAlchemy 2.0 typed syntax.
   - The snake_case conversion regex on line 17 (`"".join(["_" + c.lower() if c.isupper() else c for c in name])`) splits acronyms into single-character tokens (e.g. `SOAPNote` becomes `s_o_a_p_note`). Models must explicitly define `__tablename__` to avoid unexpected names.

4. **AI-generated smells [QUAL]**:
   - None observed.

5. **Performance [PERF]**:
   - Storing UUIDs as `String(36)` instead of native PostgreSQL `UUID` / binary increases index B-tree size and foreign key join overhead by ~2.5x.

6. **Error handling & edge cases**:
   - Timestamps rely on Python-side defaults (`default=lambda: datetime.now(timezone.utc)`). If bulk SQL inserts bypass the ORM, timestamps will be NULL unless a database-level `server_default=func.now()` is declared.

7. **Doc accuracy [DOC]**:
   - Matches architecture documentation.

8. **Tests**:
   - Tested across all ORM and migration tests.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-BASE-F01** | **S3** | `[QUAL]` | `17` | Naive snake_case splitter fragments acronyms | `SOAPNote` -> `s_o_a_p_note` | Use regex `re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()` |
| **BE-BASE-F02** | **S3** | `[PERF]` | `40-46` | String(36) UUIDs increase index size over native UUIDs | `Mapped[str] = mapped_column(String(36)...)` | Consider `sqlalchemy.dialects.postgresql.UUID` |
| **BE-BASE-F03** | **S4** | `[QUAL]` | `25, 32` | Python-side timestamp defaults lack database `server_default` | `default=lambda: datetime.now(timezone.utc)` | Add `server_default=func.now()` |

---

## Suggested Patches (NOT Applied)

### Patch BE-BASE-P01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/db/base.py
+++ b/backend/app/db/base.py
@@ -1,3 +1,4 @@
+import re
 import uuid
 from datetime import datetime, timezone
 from sqlalchemy import DateTime, String
@@ -16,3 +17,3 @@ class Base(DeclarativeBase):
-        # Convert PascalCase to snake_case
-        return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")
+        # Proper regex conversion preserving acronyms
+        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
+        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
```

---

## Verdict
**READY-WITH-FIXES** — Clean modern SQLAlchemy 2.0 base foundation; minor improvements to table name derivation suggested.
