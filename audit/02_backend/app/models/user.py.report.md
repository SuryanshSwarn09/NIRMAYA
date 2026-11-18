# Audit Report: backend/app/models/user.py

**Path:** `backend/app/models/user.py` | **Layer:** Backend (ORM Models) | **Language:** Python 3.12 (SQLAlchemy 2.0) | **LOC:** 81 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Core platform user identity and authorization entity bridging external identity providers (Supabase Auth, ABHA) with role-specific clinical and facility profiles.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** The `User` model contains no `password_hash` column despite `app/core/security.py` implementing password hashing functions; local password authentication is impossible without schema extension, leaving auth entirely reliant on Supabase or OTP.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In a modern healthcare platform, authentication (proving who you are) must be strictly decoupled from clinical roles and workflows (what you are allowed to do). A user might be a patient, a physician, a lab technician, or an administrative health officer. This file defines the central `User` identity that anchors external authentication tokens (Supabase Auth, ABHA OTP) and branches out into specific domain profiles.

### How it works, step by step
1. `User` stores the primary unique identifier (`email`), full name, and optional phone number.
2. It assigns a core system role via `role` (`UserRole`: `PATIENT`, `DOCTOR`, `LAB`, `ADMIN`).
3. It stores the external identity provider ID via `supabase_uid`.
4. It maintains account lifecycle flags: `is_active` (can log in) and `is_verified` (email/OTP verified).
5. Depending on the `role`, it links 1-to-1 to a domain profile:
   - If `role=PATIENT`: links to `patient_profile` (`PatientProfile`).
   - If `role=DOCTOR`: links to `doctor_profile` (`DoctorProfile`).
   - If `role=LAB`: links to `lab_facility` (`DiagnosticLabFacility`).

### Concepts and patterns used
- *Identity / Role Decoupling Pattern:* Keeping authentication identity minimal while delegating clinical concerns to specialized profile tables.
- *External Identity Provider Bridging:* Storing `supabase_uid` as an indexed nullable key for federated identity.
- *Strict 1-to-1 Cascading:* `uselist=False` with `cascade="all, delete-orphan"` guarantees that deleting a user removes their operational profile.

### Key lines to read first
- `user.py:15-38`: `User` class definition and role configuration.
- `user.py:39-44`: `supabase_uid` external auth bridge.
- `user.py:56-78`: 1-to-1 profile relationships.

### How to change it safely
Never remove `unique=True` on `email` or `supabase_uid`. If adding new roles (e.g., `OFFICER`, `PHARMACIST`), ensure corresponding profile models and enums are created in sync.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `typing` (TYPE_CHECKING, Optional), `sqlalchemy` (Boolean, Enum, String), `sqlalchemy.orm` (Mapped, mapped_column, relationship), `app.db.base` (Base, TimestampMixin, UUIDPrimaryKeyMixin), `app.models.enums` (UserRole).
- **Imported By:** `backend/app/models/__init__.py`, `backend/app/models/doctor.py`, `backend/app/models/lab.py`, `backend/app/models/patient.py`, `backend/app/models/delegation.py`, `backend/app/models/medication_dispense.py`, `backend/app/services/auth_service.py`, `backend/app/api/v1/endpoints/auth.py`.
- **Public Surface:** Class `User` (table `user`).

### 2. Security [SEC]
- **Architectural Auth Inconsistency (CWE-287 / CWE-306):** In `backend/app/core/security.py`, functions `get_password_hash` and `verify_password` exist. However, `User` has no `password_hash` column. If a developer attempts to implement local username/password authentication using the functions in `security.py`, there is no database column to store or retrieve the hash. The codebase is purely architected for Supabase Auth JWTs or passwordless OTP (`BE-USR-F01`).
- **Input Validation (CWE-20):** `phone_number` (`String(20)`) is indexed but lacks E.164 phone formatting validation (`BE-USR-F02`).

### 3. Code quality [QUAL]
- **Missing Relationships to Sovereign Delegations (Lines 56-78):** In `backend/app/models/delegation.py`, `AdministrativeDelegation` links to `user.id` via `delegator_user_id` and `delegatee_user_id`. `User` does not declare back-populating relationships, requiring manual filtering to query an officer's delegations (`BE-USR-F03`).
- Clean declarative mapping using SQLAlchemy 2.0 type-annotated mapped columns.

### 4. AI-generated-code smells [QUAL]
- The disconnection between `backend/app/core/security.py` (which includes password hashing) and `backend/app/models/user.py` (which has no password hash column) is a classic AI artifact where authentication utilities were generated using standard FastAPI templates while the database model was generated for a third-party auth provider (Supabase).

### 5. Performance [PERF]
- Highly efficient: `email`, `phone_number`, `role`, and `supabase_uid` are indexed.
- Lightweight table layout minimizes memory consumption during auth checks.

### 6. Error handling & edge cases
- `supabase_uid` is nullable, properly allowing administrative seed users or offline edge deployments to exist without an active Supabase cloud connection.

### 7. Doc accuracy [DOC]
- Perfectly conforms to Month 1 Day 7 auth identity specifications.

### 8. Tests
- Covered by `backend/tests/test_auth.py` and `backend/tests/test_rbac.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-USR-F01 | S2 | [SEC] | 15-55 | No password hash column exists despite hashing utilities in core | Missing `hashed_password` column in `User` | Add `hashed_password: Mapped[Optional[str]]` or delete dead hashing code |
| BE-USR-F02 | S3 | [QUAL] | 28-32 | Unvalidated phone number format | `phone_number: Mapped[Optional[str]] = mapped_column(String(20))` | Add E.164 validation constraint |
| BE-USR-F03 | S3 | [QUAL] | 56-78 | Missing relationship to administrative delegations | No back-references for delegator/delegatee roles | Add `relationship("AdministrativeDelegation", ...)` |

---

## Suggested Patches (NOT Applied)

### Patch BE-USR-F01 · Risk: Low · [UNTESTED]
Add optional password hash column to support local authentication fallback:

```diff
--- a/backend/app/models/user.py
+++ b/backend/app/models/user.py
@@ -32,2 +32,7 @@ class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     )
+    hashed_password: Mapped[Optional[str]] = mapped_column(
+        String(255),
+        nullable=True,
+    )
     role: Mapped[UserRole] = mapped_column(
```

---

## Verdict

**READY-WITH-FIXES** — Clean, well-indexed identity bridge; adding `hashed_password` or documenting pure Supabase reliance resolves the authentication architecture discrepancy.
