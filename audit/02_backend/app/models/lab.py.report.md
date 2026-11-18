# Audit Report: backend/app/models/lab.py

**Path:** `backend/app/models/lab.py` | **Layer:** Backend (ORM Models) | **Language:** Python 3.12 (SQLAlchemy 2.0) | **LOC:** 111 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Relational persistence model for diagnostic laboratory facilities, capturing facility credentials, NABL/CAP accreditation, contact details, and ABDM Health Facility Registry (HFR) identifiers.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** The laboratory model lacks foreign key relationships to `DiagnosticReport` and `DiagnosticOrder`, creating an architectural disconnect where diagnostic orders and reports cannot be directly queried by issuing lab facility.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
To operate a multi-provider healthcare platform, diagnostic centers, pathology labs, and imaging clinics must register their institutional credentials, regulatory licensing, accreditation status (NABL, CAP, ISO 15189), and ABDM HFR registry data. This file stores facility profiles linked to lab administrator accounts.

### How it works, step by step
1. `DiagnosticLabFacility` maintains a 1-to-1 linkage to `User` via `user_id`.
2. It enforces uniqueness on `license_number` and stores the facility's official legal name.
3. It tracks laboratory accreditation through `accreditation` enum and `is_nabl_certified`.
4. It records institutional contact and geographic location: `city`, `state`, and `pincode`.
5. It captures ABDM Health Facility Registry identification via `hfr_id`.
6. Supported diagnostic test capabilities are captured in `supported_tests`.

### Concepts and patterns used
- *1-to-1 Profile Extension Pattern:* Segregating authentication credentials (`User`) from organizational facility data (`DiagnosticLabFacility`).
- *National Health Registry Mapping:* Integrating ABDM HFR identifiers for national digital health compliance.

### Key lines to read first
- `lab.py:13-24`: `DiagnosticLabFacility` definition and 1-to-1 linkage to `user.id`.
- `lab.py:31-53`: Licensing and NABL certification attributes.
- `lab.py:88-91`: `supported_tests` text column.
- `lab.py:93-99`: ABDM `hfr_id` registration.

### How to change it safely
When modifying fields, ensure that any changes to `accreditation` correspond to `app.models.enums.LabAccreditation`. Do not drop unique constraints on `license_number` or `hfr_id` as they prevent duplicate organizational registrations.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `typing` (TYPE_CHECKING, Optional), `sqlalchemy` (Boolean, Enum, ForeignKey, String, Text), `sqlalchemy.orm` (Mapped, mapped_column, relationship), `app.db.base` (Base, TimestampMixin, UUIDPrimaryKeyMixin), `app.models.enums` (LabAccreditation).
- **Imported By:** `backend/app/models/__init__.py`, `backend/app/models/user.py`, `backend/app/services/lab_service.py`, `backend/app/api/v1/endpoints/labs.py`.
- **Public Surface:** Class `DiagnosticLabFacility` (table `diagnostic_lab_facilities`).

### 2. Security [SEC]
- **Lack of Institutional Verification Tracking (CWE-285):** Like `DoctorProfile`, `DiagnosticLabFacility` stores an ABDM `hfr_id` and `is_nabl_certified`, but lacks verification metadata (e.g. `is_hfr_verified`, `verification_date`), permitting self-asserted accreditation without administrative validation tracking (`BE-LAB-F01`).
- **Input Validation on Contact Data (CWE-20):** `contact_phone` (`String(20)`) and `pincode` (`String(10)`) lack regex check constraints, permitting malformed contact numbers in the directory.

### 3. Code quality [QUAL]
- **Unstructured Test Catalog Storage (Line 88-91):** `supported_tests` is stored as an unindexed raw `Text` column. Querying labs that offer a specific test panel requires `LIKE '%Lipid%'` full table scans. It should be structured as a JSON list or a relational junction table (`BE-LAB-F02`).
- **Architectural Entity Disconnect (Lines 13-106):** In `backend/app/models/diagnostic.py`, `DiagnosticReport.performer_id` links to `doctor_profile.id`, and `performer_name` is a raw string. `DiagnosticLabFacility` has no relationship to `DiagnosticReport` or `DiagnosticOrder`, making it impossible to query all lab reports issued by a specific facility through standard ORM navigation (`BE-LAB-F03`).

### 4. AI-generated-code smells [QUAL]
- `is_nabl_certified: Mapped[bool] = mapped_column(Boolean, default=True)` is redundant when `accreditation` is already an enum whose default value is `LabAccreditation.NABL`.

### 5. Performance [PERF]
- `license_number`, `hfr_id`, and `city` are properly indexed.
- Full table scans will occur if searching labs by test capabilities due to the raw text `supported_tests` column.

### 6. Error handling & edge cases
- If `User` is deleted, `DiagnosticLabFacility` cascades (`ondelete="CASCADE"`).

### 7. Doc accuracy [DOC]
- Conforms to Month 1 Day 8 specifications.

### 8. Tests
- Covered by `backend/tests/test_lab.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-LAB-F01 | S2 | [QUAL] | 13-106 | Missing linkage between lab facilities and diagnostic reports | No `reports` relationship; `DiagnosticReport` links only to `DoctorProfile` | Add `facility_id` to `DiagnosticReport` and reverse relationship in `DiagnosticLabFacility` |
| BE-LAB-F02 | S2 | [PERF] | 88-91 | Unstructured test catalog prevents indexed capability searching | `supported_tests: Mapped[Optional[str]] = mapped_column(Text)` | Convert to `JSON` or dedicated `lab_test_catalog` relational model |
| BE-LAB-F03 | S3 | [QUAL] | 82-85 | Unvalidated Indian postal PIN code | `pincode: Mapped[str] = mapped_column(String(10))` | Add check constraint or regex for 6-digit numeric PIN |

---

## Suggested Patches (NOT Applied)

### Patch BE-LAB-F01 · Risk: Medium · [UNTESTED]
Add relationship linking diagnostic lab facilities to fulfilled reports:

```diff
--- a/backend/app/models/lab.py
+++ b/backend/app/models/lab.py
@@ -3,4 +3,4 @@
-from typing import TYPE_CHECKING, Optional
+from typing import TYPE_CHECKING, List, Optional
 from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
 from sqlalchemy.orm import Mapped, mapped_column, relationship
@@ -10,2 +10,3 @@ if TYPE_CHECKING:
     from app.models.user import User
+    from app.models.diagnostic import DiagnosticReport
 
@@ -105,2 +106,8 @@ class DiagnosticLabFacility(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     )
+
+    # Diagnostic reports performed by this facility
+    diagnostic_reports: Mapped[List["DiagnosticReport"]] = relationship(
+        "DiagnosticReport",
+        foreign_keys="DiagnosticReport.performer_id",
+    )
```

### S3 One-Line Fix
- **BE-LAB-F03:** In `__table_args__`, add `CheckConstraint("pincode ~ '^[1-9][0-9]{5}$'", name="chk_valid_pincode")`.

---

## Verdict

**READY-WITH-FIXES** — Functional facility entity, but needs structural connection to diagnostic reports and JSON conversion for supported tests.
