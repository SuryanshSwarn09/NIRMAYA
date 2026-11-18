# Audit Report: `backend/app/models/administrative_hierarchy.py`

**Path**: `backend/app/models/administrative_hierarchy.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 172 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Sovereign territorial administrative units and appointed officer models integrating PostgreSQL `ltree` hierarchies · Risk: **S2 (Medium Risk)** · Verdict: **READY-WITH-FIXES** · Conflict between database foreign key `RESTRICT` and SQLAlchemy ORM `cascade="all, delete-orphan"` on child units; custom `ltree` type decorator is clean.

---

## Layer B — Explain It
- **What problem this file solves**: Models India's 6-tier Local Government Directory (LGD) administrative command hierarchy (Country $\rightarrow$ State $\rightarrow$ Division $\rightarrow$ District $\rightarrow$ Sub-district $\rightarrow$ Facility) and records appointed government health officers.
- **How it works step by step**:
  1. `LTreePath` custom TypeDecorator provides native PostgreSQL `ltree` in production and `String(255)` on SQLite during automated tests.
  2. `AdministrativeUnit` stores unit name, LGD code, level enum, and hierarchical dotted path (`path`).
  3. Supports tree traversal via self-referential `parent` and `children` relationships.
  4. `AdministrativeOfficer` links a `User` identity to an administrative unit, designation, and assigned `jurisdiction_path`.
  5. Implements PostgreSQL GiST indexes for sub-millisecond tree searches.
- **Concepts & patterns used**:
  - *Materialized Path Pattern*: PostgreSQL `ltree` facilitates fast ancestor and descendant queries.
  - *Self-Referential Association*: `remote_side` relationships modeling organizational command trees.
- **Key lines to read first**:
  - `backend/app/models/administrative_hierarchy.py:23-37`: `LTreePath` dialect abstraction.
  - `backend/app/models/administrative_hierarchy.py:39-102`: `AdministrativeUnit` definition and GiST index.
  - `backend/app/models/administrative_hierarchy.py:105-172`: `AdministrativeOfficer` definition.
- **How to change it safely**:
  - Ensure the PostgreSQL `ltree` extension is installed before executing migrations on a clean database.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `sqlalchemy.*`, `app.db.base.Base`, `app.models.enums.AdminLevelEnum`, `app.models.enums.GovtDesignationEnum`.
   - **Imported by**: `backend/app/core/territorial_rbac.py`, `backend/app/models/delegation.py`, `backend/app/api/v1/endpoints/administrative_hierarchy.py`.
   - **Public surface**: `LTree`, `LTreePath`, `AdministrativeUnit`, `AdministrativeOfficer`.

2. **Security [SEC]**:
   - Foreign key protection: `user_id` cascades on user deletion, but `administrative_unit_id` enforces `RESTRICT` to prevent orphaned officer positions.
   - GiST indexing on `path` (`lines 100, 170`) ensures fast evaluation of territorial permissions without full-table scans.

3. **Code quality [QUAL]**:
   - *Cascade Mismatch*: Line 67 specifies `ForeignKey("administrative_units.id", ondelete="RESTRICT")`, but line 90 sets `cascade="all, delete-orphan"` on `children`. If an `AdministrativeUnit` is deleted via SQLAlchemy session, ORM attempts to delete all child units, conflicting with the DB-level constraint or unintentionally wiping entire district trees.

4. **AI-generated smells [QUAL]**:
   - None observed; the dialect switching in `LTreePath` is an effective solution for SQLite test compatibility.

5. **Performance [PERF]**:
   - Excellent indexing strategy with composite indexes (`unit_level`, `parent_id`) and GiST index on `path`.

6. **Error handling & edge cases**:
   - `UniqueConstraint` on `lgd_code` prevents duplicate government directory entries.

7. **Doc accuracy [DOC]**:
   - Accurately models the 6-tier administrative hierarchy described in `docs/architecture/`.

8. **Tests**:
   - Tested in `backend/tests/test_territorial_hierarchy.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-ADH-F01** | **S2** | `[QUAL]` | `67, 90` | DB `ondelete="RESTRICT"` conflicts with ORM `cascade="all, delete-orphan"` | `cascade="all, delete-orphan"` on `children` | Remove `delete-orphan` cascade to prevent accidental tree deletion |
| **BE-ADH-F02** | **S3** | `[DOC]` | `16-37` | Undocumented prerequisite: PostgreSQL `ltree` extension required | `return "ltree"` | Document `CREATE EXTENSION IF NOT EXISTS ltree` in setup guides |
| **BE-ADH-F03** | **S4** | `[QUAL]` | `71-74` | Unstructured CSV string for postal codes | `pincode_prefixes = mapped_column(String(255))` | Consider JSON or Array column type |

---

## Suggested Patches (NOT Applied)

### Patch BE-ADH-P01 · risk of change: low · [UNTESTED]
```diff
--- a/backend/app/models/administrative_hierarchy.py
+++ b/backend/app/models/administrative_hierarchy.py
@@ -87,4 +87,4 @@ class AdministrativeUnit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     children: Mapped[List["AdministrativeUnit"]] = relationship(
         "AdministrativeUnit",
         back_populates="parent",
-        cascade="all, delete-orphan",
+        passive_deletes="all",
     )
```

---

## Verdict
**READY-WITH-FIXES** — Outstanding LGD model using PostgreSQL `ltree`; align ORM relationship cascades with database `RESTRICT` rules.
