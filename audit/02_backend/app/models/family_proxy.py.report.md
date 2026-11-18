# Audit Report: backend/app/models/family_proxy.py

**Path:** `backend/app/models/family_proxy.py` | **Layer:** Backend (ORM Models) | **Language:** Python 3.12 (SQLAlchemy 2.0) | **LOC:** 134 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Relational models for dependent and family health proxy access delegation, enforcing zero record contamination between guardians and dependents with an accompanying forensic audit log.
- **Risk Level:** **S1 (High)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `ProxyAuditLog.relationship_id` specifies `ondelete="CASCADE"`, which deletes the entire forensic audit trail tracking who accessed a minor or senior dependent's medical records whenever a proxy relationship is revoked or deleted.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In family healthcare, parents must manage medical care for children and adult children must manage care for elderly parents. If not architected carefully, a child's clinical records (vaccinations, pediatric notes) can be accidentally merged into the parent's record. This file implements "Zero-Contamination Architecture": the dependent and guardian each have distinct, completely isolated `PatientProfile` records, and only access authority is delegated via `PatientProxyRelationship`.

### How it works, step by step
1. `PatientProxyRelationship` links a `guardian_patient_id` to a `dependent_patient_id`.
2. It captures the `relationship_type` (e.g., Parent, Legal Guardian, Adult Child) and `verification_tier` (e.g., Aadhaar verified, Court Order).
3. It stores a SHA-256 hash (`verification_document_hash`) of the legal guardianship certificate.
4. It enforces access restrictions via `access_scope` (e.g., `FULL_MANAGEMENT`, `VIEW_ONLY`, `APPOINTMENT_ONLY`) and an optional expiration date (`authorized_until`).
5. Every time a guardian switches into a dependent's profile or accesses records, an immutable row is appended to `ProxyAuditLog` recording the actor, target, action, IP address, and timestamp.

### Concepts and patterns used
- *Zero-Contamination Isolation:* Complete entity segregation between guardian and dependent health records.
- *Scoped Delegated Authority:* Granular access control enums defining permissible operations.
- *Cryptographic Document Anchoring:* Storing SHA-256 hashes of legal authorization documents to prevent tampering.

### Key lines to read first
- `family_proxy.py:15-81`: `PatientProxyRelationship` model and authority constraints.
- `family_proxy.py:83-134`: `ProxyAuditLog` forensic logging model.
- `family_proxy.py:89`: `ondelete="CASCADE"` on `relationship_id` in audit log.

### How to change it safely
Never remove the foreign keys to `patient_profile.id`. When updating enums, verify that `app.schemas.family_proxy` is updated concurrently. Ensure that `ProxyAuditLog` cannot be cleared or truncated by normal application workflows.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `uuid`, `datetime`, `typing`, `sqlalchemy` (Boolean, DateTime, Enum, ForeignKey, String, Text), `sqlalchemy.orm` (Mapped, mapped_column, relationship), `app.db.base` (Base, TimestampMixin, UUIDPrimaryKeyMixin), `app.schemas.family_proxy` (ProxyAccessScopeEnum, ProxyRelationshipStatusEnum, RelationshipTypeEnum, VerificationAuthorityEnum).
- **Imported By:** `backend/app/models/__init__.py`, `backend/app/services/family_proxy_service.py`, `backend/app/api/v1/endpoints/family_proxy.py`.
- **Public Surface:** Classes `PatientProxyRelationship` (table `patient_proxy_relationships`), `ProxyAuditLog` (table `proxy_audit_logs`).

### 2. Security [SEC]
- **Audit Trail Deletion Vulnerability (CWE-285 / CWE-404):** `ProxyAuditLog.relationship_id` (line 89) uses `ondelete="CASCADE"`. Under DPDP Act 2023 Section 9 (Processing of personal data of children), access logs to children's records must remain auditable. Cascading deletions allow a malicious or compromised guardian to purge all forensic logs of their unauthorized record access simply by deleting the relationship (`BE-FPX-F01`).
- **Duplicate Relationship Risk (CWE-20):** `PatientProxyRelationship` lacks a unique constraint or composite index on `(guardian_patient_id, dependent_patient_id)`, permitting concurrent duplicate proxy links (`BE-FPX-F02`).
- **Missing Direct ORM Navigation:** Neither `guardian_patient` nor `dependent_patient` has an explicit `relationship()` defined in `PatientProxyRelationship`, forcing manual joins across queries.

### 3. Code quality [QUAL]
- Clean use of SQLAlchemy 2.0 type-annotated mapped columns.
- Uses `lambda: datetime.now(timezone.utc)` for timezone-aware default timestamps.
- Explicit `String(64)` for SHA-256 document hashes.

### 4. AI-generated-code smells [QUAL]
- `zero_contamination_isolated` is a boolean column defaulting to `True` (line 76-80). It serves no structural purpose in SQL queries and is a redundant marketing flag rather than an active constraint.

### 5. Performance [PERF]
- Well-indexed: `guardian_patient_id`, `dependent_patient_id`, `actor_guardian_id`, `target_dependent_id`, and `timestamp` are indexed for fast forensic lookups.

### 6. Error handling & edge cases
- If `authorized_until` is in the past, authorization checks must be enforced by middleware or service layer, as SQL does not validate temporal expiration automatically.

### 7. Doc accuracy [DOC]
- Perfectly matches Day 81-85 documentation in `docs/journey/month-4/` and `docs/reports/nirmaya-family-proxy-access-architecture.md`.

### 8. Tests
- Covered by `backend/tests/test_family_proxy.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-FPX-F01 | S1 | [SEC] | 87-92 | Cascade delete destroys forensic proxy audit logs | `ForeignKey("patient_proxy_relationships.id", ondelete="CASCADE")` | Change `ondelete` to `"RESTRICT"` or `"SET NULL"` with nullable column |
| BE-FPX-F02 | S2 | [QUAL] | 23-38 | Missing unique constraint on guardian-dependent pair | No `UniqueConstraint("guardian_patient_id", "dependent_patient_id")` | Add `UniqueConstraint` in `__table_args__` |
| BE-FPX-F03 | S3 | [QUAL] | 76-80 | Redundant boolean metadata column | `zero_contamination_isolated: Mapped[bool] = mapped_column(...)` | Remove or document as informational |

---

## Suggested Patches (NOT Applied)

### Patch BE-FPX-F01 · Risk: Low · [UNTESTED]
Prevent deletion of forensic audit logs when a proxy relationship is terminated:

```diff
--- a/backend/app/models/family_proxy.py
+++ b/backend/app/models/family_proxy.py
@@ -87,7 +87,7 @@ class ProxyAuditLog(Base, UUIDPrimaryKeyMixin):
-    relationship_id: Mapped[str] = mapped_column(
-        String(36),
-        ForeignKey("patient_proxy_relationships.id", ondelete="CASCADE"),
-        nullable=False,
-        index=True,
-    )
+    relationship_id: Mapped[Optional[str]] = mapped_column(
+        String(36),
+        ForeignKey("patient_proxy_relationships.id", ondelete="SET NULL"),
+        nullable=True,
+        index=True,
+    )
```

### Patch BE-FPX-F02 · Risk: Low · [UNTESTED]
Prevent duplicate proxy relationships between the same guardian and dependent:

```diff
--- a/backend/app/models/family_proxy.py
+++ b/backend/app/models/family_proxy.py
@@ -4,4 +4,4 @@ from typing import Optional
-from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
+from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
 from sqlalchemy.orm import Mapped, mapped_column, relationship
@@ -80,2 +80,6 @@ class PatientProxyRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     )
+
+    __table_args__ = (
+        UniqueConstraint("guardian_patient_id", "dependent_patient_id", name="uq_guardian_dependent_proxy"),
+    )
```

---

## Verdict

**READY-WITH-FIXES** — Outstanding domain isolation model for minor/dependent health records; changing `relationship_id` delete cascade to `SET NULL` is required for legal audit preservation.
