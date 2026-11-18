# Audit Report: backend/app/models/delegation.py

**Path:** `backend/app/models/delegation.py` | **Layer:** Backend (ORM Models) | **Language:** Python 3.12 (SQLAlchemy 2.0) | **LOC:** 151 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Models administrative delegation of authority and an append-only cryptographic ledger tracking chain-of-command transfers across India's administrative healthcare hierarchy.
- **Risk Level:** **S1 (High)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** The immutable cryptographic ledger (`DelegationAuditLedger`) specifies `ondelete="CASCADE"` on both `delegation_id` and `actor_id` foreign keys; deleting a user or delegation purges historical ledger entries, destroying legal non-repudiation and auditability.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In government healthcare administration, senior officers (e.g., District Magistrate, Chief Medical Officer) must frequently delegate operational authority to subordinates for specific geographical jurisdictions or time windows. This file provides the relational persistence structures for tracking these delegations and maintaining an audit log that records who granted authority to whom, under what jurisdiction, and when.

### How it works, step by step
1. `AdministrativeDelegation` records a formal delegation from `delegator_user_id` to `delegatee_user_id`.
2. The delegation is bounded by `administrative_unit_id` and an `LTreePath` (`jurisdiction_path`, e.g., `india.dl.newdelhi`).
3. It captures security attributes: whether Aadhaar verification was completed (`aadhaar_verified`), the official government email (`gov_email`), and an integrity SHA-256 hash (`audit_hash`).
4. If a delegation is terminated, `is_active` is toggled to `False`, and `revoked_at`, `revoked_by_user_id`, and `revocation_reason` are populated.
5. Every creation or revocation event generates a row in `DelegationAuditLedger`, recording the action (`DELEGATED`, `REVOKED`), the actor, timestamp, and a hash chain linking `audit_hash` to `previous_hash`.

### Concepts and patterns used
- *Cryptographic Hash Chaining:* Linking ledger entries via `audit_hash` and `previous_hash` to detect retroactive tampering.
- *Hierarchical LTree Indexing:* Utilizing PostgreSQL `ltree` via `LTreePath` custom type to index jurisdiction scopes.
- *Soft-State Revocation:* Recording revocation metadata (`revoked_at`, `revocation_reason`) while retaining the original record.

### Key lines to read first
- `delegation.py:13-99`: `AdministrativeDelegation` model definition and composite index on `(jurisdiction_path, is_active)`.
- `delegation.py:102-151`: `DelegationAuditLedger` immutable append-only ledger model.
- `delegation.py:107-112`: Foreign key cascade configuration on `delegation_id`.

### How to change it safely
When modifying these models, ensure that any changes to `jurisdiction_path` preserve compatibility with `LTreePath` queries. Never alter `DelegationAuditLedger` column types without a corresponding Alembic migration. If adding new actions to the ledger, ensure corresponding service-layer hash computation matches the schema.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `sqlalchemy` (Boolean, DateTime, Enum, ForeignKey, Index, String), `sqlalchemy.orm` (Mapped, mapped_column, relationship), `app.db.base` (Base, TimestampMixin, UUIDPrimaryKeyMixin), `app.models.administrative_hierarchy` (LTreePath), `app.models.enums` (GovtDesignationEnum).
- **Imported By:** `backend/app/models/__init__.py`, `backend/app/services/delegation_service.py`, `backend/app/api/v1/endpoints/delegation.py`.
- **Public Surface:** Classes `AdministrativeDelegation` (table `administrative_delegations`), `DelegationAuditLedger` (table `delegation_audit_ledger`).

### 2. Security [SEC]
- **Broken Non-Repudiation (CWE-285 / CWE-404):** `DelegationAuditLedger.delegation_id` (line 109) and `actor_id` (line 120) define `ondelete="CASCADE"`. In a regulatory environment governed by the DPDP Act 2023 and central health audits, an audit ledger must be tamper-proof and permanent. Cascading deletions allow an administrator or compromised account to wipe the ledger by deleting the parent delegation or actor user record (`BE-DEL-F01`).
- **Unconstrained String Action (CWE-20):** `DelegationAuditLedger.action` (lines 113-117) is stored as a raw `String(20)` without an `Enum` or `CheckConstraint`, permitting arbitrary or malformed action verbs (`BE-DEL-F02`).
- **Redundant Status Fields:** `status` (`String(20)`, default `"active"`) and `is_active` (`Boolean`, default `True`) exist simultaneously, introducing the possibility of split-brain states (e.g., `status="revoked"` while `is_active=True`) (`BE-DEL-F03`).

### 3. Code quality [QUAL]
- Clean declarative mapping using SQLAlchemy 2.0 `Mapped` and `mapped_column`.
- Missing explicit check constraints on `status` values.
- Indexes properly placed on query filters: `(jurisdiction_path, is_active)` and `(delegatee_user_id, is_active)`.

### 4. AI-generated-code smells [QUAL]
- The comment on line 103 calls `DelegationAuditLedger` an *"Immutable, append-only cryptographic ledger"*, but neither the database nor the ORM enforces immutability; row updates and cascade deletes are fully permitted.

### 5. Performance [PERF]
- Excellent indexing strategy with compound indexes on active delegations for fast hierarchical resolution.
- `audit_hash` and `previous_hash` are fixed-width `String(64)` matching SHA-256 output.

### 6. Error handling & edge cases
- Timezone awareness is properly handled using `DateTime(timezone=True)` and `datetime.now(timezone.utc)`.
- If a delegator is deleted, their issued delegations cascade delete (`ondelete="CASCADE"` on `delegator_user_id`), which could inadvertently revoke active subordinate powers during user lifecycle cleanups.

### 7. Doc accuracy [DOC]
- Perfectly matches the PRD and Phase 7 territorial governance architecture documentation.

### 8. Tests
- Covered indirectly by `backend/tests/test_governance.py` and `backend/tests/test_delegation.py`. Ledger deletion behavior is untested.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-DEL-F01 | S1 | [SEC] | 107-123 | Audit ledger cascades on parent deletion | `ForeignKey("administrative_delegations.id", ondelete="CASCADE")`, `ForeignKey("user.id", ondelete="CASCADE")` | Change `ondelete` to `"RESTRICT"` or use soft deletes to preserve audit history |
| BE-DEL-F02 | S2 | [QUAL] | 113-117 | Unconstrained action string in audit ledger | `action: Mapped[str] = mapped_column(String(20))` | Replace with `Enum(DelegationActionEnum)` or add check constraint |
| BE-DEL-F03 | S3 | [QUAL] | 61-72 | Redundant `status` and `is_active` flags | `status: Mapped[str] = mapped_column(...)` vs `is_active: Mapped[bool]` | Harmonize or compute `is_active` as property of `status` |

---

## Suggested Patches (NOT Applied)

### Patch BE-DEL-F01 · Risk: Medium · [UNTESTED]
Protect audit ledger integrity by enforcing `RESTRICT` on deletions of referenced delegations and users:

```diff
--- a/backend/app/models/delegation.py
+++ b/backend/app/models/delegation.py
@@ -107,17 +107,17 @@ class DelegationAuditLedger(Base, UUIDPrimaryKeyMixin):
     delegation_id: Mapped[str] = mapped_column(
         String(36),
-        ForeignKey("administrative_delegations.id", ondelete="CASCADE"),
+        ForeignKey("administrative_delegations.id", ondelete="RESTRICT"),
         nullable=False,
         index=True,
     )
     action: Mapped[str] = mapped_column(
         String(20),
         nullable=False,
         index=True,
     )  # 'DELEGATED', 'REVOKED'
     actor_id: Mapped[str] = mapped_column(
         String(36),
-        ForeignKey("user.id", ondelete="CASCADE"),
+        ForeignKey("user.id", ondelete="RESTRICT"),
         nullable=False,
         index=True,
     )
```

### Patch BE-DEL-F02 · Risk: Low · [UNTESTED]
Add enum constraint to `action` column in `DelegationAuditLedger`:

```diff
--- a/backend/app/models/delegation.py
+++ b/backend/app/models/delegation.py
@@ -113,5 +113,5 @@ class DelegationAuditLedger(Base, UUIDPrimaryKeyMixin):
     action: Mapped[str] = mapped_column(
-        String(20),
+        Enum("DELEGATED", "REVOKED", name="delegation_action_enum", native_enum=False),
         nullable=False,
         index=True,
     )  # 'DELEGATED', 'REVOKED'
```

---

## Verdict

**READY-WITH-FIXES** — Core models are well structured with appropriate LTree indexing, but the audit ledger must enforce `RESTRICT` on delete to guarantee regulatory non-repudiation.
