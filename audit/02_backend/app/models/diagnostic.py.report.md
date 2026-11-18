# Audit Report: backend/app/models/diagnostic.py

**Path:** `backend/app/models/diagnostic.py` | **Layer:** Backend (ORM Models) | **Language:** Python 3.12 (SQLAlchemy 2.0) | **LOC:** 310 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Implements relational persistence models for clinical diagnostic requisition orders (`ServiceRequest`) and diagnostic laboratory/imaging reports (`DiagnosticReport`) conforming to HL7 FHIR Release 4.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `DiagnosticOrder.reports` sets `cascade="all, delete-orphan"`, conflicting with the underlying DB foreign key (`ondelete="SET NULL"`) and causing accidental purge of immutable clinical lab reports if an order is cancelled or deleted through SQLAlchemy.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In healthcare workflows, diagnostic testing follows a two-part lifecycle: a clinician issues a laboratory or diagnostic imaging requisition (a "ServiceRequest"), and later a laboratory technician or pathologist conducts the test and issues a verified report ("DiagnosticReport") containing findings and clinical conclusions. This file models these two core clinical entities with bidirectional relationships and LOINC coding.

### How it works, step by step
1. `DiagnosticOrder` records a test requisition for a patient (`patient_id`), optionally requested by a doctor (`doctor_id`) within an encounter (`encounter_id`).
2. It captures LOINC standard codes (e.g., `code_value="24331-1"`, `code_display="Lipid Panel"`), priority (`ROUTINE`, `URGENT`, `STAT`), specimen type, and status (`ACTIVE`, `COMPLETED`, etc.).
3. Once completed, one or more `DiagnosticReport` records attach to the order.
4. `DiagnosticReport` records the issuing laboratory or pathologist (`performer_id`, `performer_name`), LOINC panel code, status (`FINAL`, `PRELIMINARY`), observation links, and structured test metrics (`report_data` JSON).
5. It flags abnormal findings with `is_abnormal=True` and includes text conclusions.

### Concepts and patterns used
- *HL7 FHIR R4 Alignment:* Direct 1-to-1 mapping to `ServiceRequest` and `DiagnosticReport` domain resources.
- *Standardized Medical Ontologies:* Native support for LOINC code systems (`http://loinc.org`) and SNOMED-CT specimen types.
- *Hybrid Relational + Document Persistence:* Relational indices on identifiers combined with JSON payload storage for varied lab assay results.

### Key lines to read first
- `diagnostic.py:35-156`: `DiagnosticOrder` entity definition and relationship configuration.
- `diagnostic.py:151-155`: `DiagnosticOrder.reports` cascade delete definition.
- `diagnostic.py:164-310`: `DiagnosticReport` entity definition.
- `diagnostic.py:214-215`: Hardcoded default commercial laboratory name.
- `diagnostic.py:251-260`: Datetime defaults using deprecated `datetime.utcnow`.

### How to change it safely
When modifying these models, do not change column nullability on `patient_id` or `status` as these are required for FHIR R4 conformance. Always maintain the reverse relationship in `app.models.patient.PatientProfile` and `app.models.observation.ClinicalObservation`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing`, `sqlalchemy` (Boolean, DateTime, Enum, ForeignKey, JSON, String, Text), `sqlalchemy.orm` (Mapped, mapped_column, relationship), `app.db.base` (Base, TimestampMixin, UUIDPrimaryKeyMixin), `app.models.enums` (DiagnosticReportStatus, ServiceRequestIntent, ServiceRequestPriority, ServiceRequestStatus, SpecimenType).
- **Imported By:** `backend/app/models/__init__.py`, `backend/app/models/patient.py`, `backend/app/models/doctor.py`, `backend/app/services/diagnostic_service.py`, `backend/app/api/v1/endpoints/diagnostics.py`.
- **Public Surface:** Classes `DiagnosticOrder` (table `diagnostic_order`), `DiagnosticReport` (table `diagnostic_report`).

### 2. Security [SEC]
- **Clinical Data Integrity / Accidental Medical Record Loss (CWE-404):** `DiagnosticOrder.reports` specifies `cascade="all, delete-orphan"` (line 154). Clinical diagnostic reports represent legal patient health records. If an order is purged or cancelled in the application layer, all associated diagnostic reports are deleted from the database rather than unlinked, violating clinical record retention guidelines (`BE-DIA-F01`).
- **Data Leakage in JSON Column (CWE-200):** `DiagnosticReport.report_data` (lines 278-282) stores arbitrary unvalidated JSON dictionaries without schema validation at the ORM layer, potentially allowing unredacted PII or raw diagnostic equipment debug traces to enter the database.

### 3. Code quality [QUAL]
- **Deprecated `datetime.utcnow` (Lines 253, 258):** In Python 3.12+, `datetime.utcnow()` is deprecated because it returns a naive datetime object. When passed to `DateTime(timezone=True)`, it can cause silent UTC offset bugs. Replace with `lambda: datetime.now(timezone.utc)` (`BE-DIA-F02`).
- **Hardcoded Third-Party Vendor Mock Default (Lines 214-215):** `performer_name` has a default value of `"Metropolis Diagnostics & Pathology Lab"`. In an open-source or national platform, embedding a specific private commercial pathology brand as the database default is a prototype artifact (`BE-DIA-F03`).

### 4. AI-generated-code smells [QUAL]
- The hardcoded default `"Metropolis Diagnostics & Pathology Lab"` is a classic AI placeholder value that was forgotten during transition to production.
- Discrepancy between DB schema (`ondelete="SET NULL"` on line 190) and ORM configuration (`cascade="all, delete-orphan"` on line 154) typically indicates disjointed AI prompt generations for the two models.

### 5. Performance [PERF]
- Well-indexed: `patient_id`, `doctor_id`, `status`, `priority`, `category`, and `is_abnormal` are indexed.
- Use of generic `JSON` instead of PostgreSQL `JSONB` means GIN indexing is not directly enabled on `report_data` if complex querying inside results is required in future.

### 6. Error handling & edge cases
- `patient_id` has `ondelete="CASCADE"`, meaning deleting a patient purges all their orders and reports. While expected in GDPR "Right to be Forgotten", clinical compliance usually requires anonymization/soft deletion.

### 7. Doc accuracy [DOC]
- Accurately implements FHIR R4 ServiceRequest and DiagnosticReport specifications.

### 8. Tests
- Covered by unit and integration tests in `backend/tests/test_diagnostic.py` and `backend/tests/test_fhir.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-DIA-F01 | S2 | [QUAL] | 151-155, 188-193 | Cascade delete removes historical medical reports | `cascade="all, delete-orphan"` on order vs `ondelete="SET NULL"` on report | Remove `all, delete-orphan` cascade to prevent report loss |
| BE-DIA-F02 | S2 | [QUAL] | 253, 258 | Deprecated `datetime.utcnow` produces naive timestamps | `default=datetime.utcnow` | Replace with `lambda: datetime.now(timezone.utc)` |
| BE-DIA-F03 | S2 | [QUAL] | 214-215 | Hardcoded commercial provider default | `default="Metropolis Diagnostics & Pathology Lab"` | Remove default; require caller or leave `None` |

---

## Suggested Patches (NOT Applied)

### Patch BE-DIA-F01 · Risk: Low · [UNTESTED]
Prevent deletion of diagnostic reports when parent order is deleted:

```diff
--- a/backend/app/models/diagnostic.py
+++ b/backend/app/models/diagnostic.py
@@ -151,5 +151,4 @@ class DiagnosticOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     reports: Mapped[List["DiagnosticReport"]] = relationship(
         "DiagnosticReport",
         back_populates="order",
-        cascade="all, delete-orphan",
     )
```

### Patch BE-DIA-F02 · Risk: Low · [UNTESTED]
Replace deprecated naive `datetime.utcnow` with timezone-aware factory:

```diff
--- a/backend/app/models/diagnostic.py
+++ b/backend/app/models/diagnostic.py
@@ -6,3 +6,3 @@
-from datetime import datetime
+from datetime import datetime, timezone
 from typing import Optional, List, Dict, Any, TYPE_CHECKING
@@ -250,9 +250,9 @@ class DiagnosticReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     # Timing
     effective_date_time: Mapped[datetime] = mapped_column(
         DateTime(timezone=True),
-        default=datetime.utcnow,
+        default=lambda: datetime.now(timezone.utc),
         nullable=False,
     )
     issued_date_time: Mapped[datetime] = mapped_column(
         DateTime(timezone=True),
-        default=datetime.utcnow,
+        default=lambda: datetime.now(timezone.utc),
         nullable=False,
     )
```

### Patch BE-DIA-F03 · Risk: Low · [UNTESTED]
Remove hardcoded private commercial vendor name:

```diff
--- a/backend/app/models/diagnostic.py
+++ b/backend/app/models/diagnostic.py
@@ -212,5 +212,4 @@ class DiagnosticReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     performer_name: Mapped[Optional[str]] = mapped_column(
         String(255),
-        default="Metropolis Diagnostics & Pathology Lab",
         nullable=True,
     )
```

---

## Verdict

**READY-WITH-FIXES** — High quality FHIR R4 entity model, but requires fixing the ORM delete cascade on medical reports and removing prototype hardcoded vendor strings.
