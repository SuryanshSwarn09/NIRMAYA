# Audit Report: backend/app/models/soap_note.py

**Path:** `backend/app/models/soap_note.py` | **Layer:** Backend (ORM Models) | **Language:** Python 3.12 (SQLAlchemy 2.0) | **LOC:** 166 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Relational persistence model for structured SOAP clinical encounter documentation, implementing standard LOINC clinical sections and SHA-256 digital signatures conforming to HL7 FHIR R4 `Composition`.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** The model does not enforce database-level immutability once `is_signed=True`; narrative clinical text (Subjective, Objective, Assessment, Plan) can be updated post-signature if service-layer checks fail.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
During a patient consultation, doctors document clinical findings using the industry-standard SOAP framework: Subjective (what the patient reports), Objective (vital signs and physical findings), Assessment (clinical diagnosis), and Plan (treatments, prescriptions, tests). To be legally binding in telemedicine and hospital audits, the note must be cryptographically signed by the practitioner. This file stores that structured documentation.

### How it works, step by step
1. `SoapNote` links a patient (`patient_id`), physician author (`doctor_id`), and consultation encounter (`encounter_id`).
2. It tracks document status (`PRELIMINARY`, `FINAL`, `AMENDED`) and type (`SOAP`, `CONSULTATION`, `DISCHARGE_SUMMARY`).
3. It stores the chief complaint and the 4 standard SOAP sections, mapped to official LOINC identifiers:
   - Chief Complaint: LOINC 10154-3
   - Subjective: LOINC 61150-9
   - Objective: LOINC 61149-1
   - Assessment: LOINC 51848-0
   - Plan: LOINC 18776-5
4. It stores optional ICD-10 diagnostic coding (`primary_diagnosis_code`).
5. It captures follow-up instructions and discharge guidance.
6. When finalized, the doctor cryptographically signs the note, setting `is_signed=True`, `signed_at`, and `signature_hash`.

### Concepts and patterns used
- *HL7 FHIR Release 4 Alignment:* Direct mapping to the FHIR `Composition` resource.
- *Standardized Clinical Terminology:* Native LOINC section alignment.
- *Medicolegal Non-Repudiation:* SHA-256 digital signatures locking signed encounter records.
- *Async Eager Loading:* `lazy="selectin"` for non-blocking relational traversal.

### Key lines to read first
- `soap_note.py:24-34`: Class docstring and LOINC standard mappings.
- `soap_note.py:82-111`: The 4 structured SOAP narrative text sections.
- `soap_note.py:129-144`: Digital signature and tamper-evident hash fields.
- `soap_note.py:146-160`: Async `selectin` relationships.

### How to change it safely
Never modify existing SOAP note records where `is_signed=True`. If corrections are necessary, follow FHIR R4 clinical protocol: generate an amended note (`status=AMENDED`) referencing the original note.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing`, `sqlalchemy` (Boolean, DateTime, Enum, ForeignKey, String, Text), `sqlalchemy.orm` (Mapped, mapped_column, relationship), `app.db.base` (Base, TimestampMixin, UUIDPrimaryKeyMixin), `app.models.enums` (ClinicalNoteStatus, ClinicalNoteType).
- **Imported By:** `backend/app/models/__init__.py`, `backend/app/models/patient.py`, `backend/app/models/doctor.py`, `backend/app/models/appointment.py`, `backend/app/services/soap_note_service.py`, `backend/app/api/v1/endpoints/soap_notes.py`.
- **Public Surface:** Class `SoapNote` (table `soap_note`).

### 2. Security [SEC]
- **Post-Signature Tampering Risk (CWE-285):** While `is_signed`, `signed_at`, and `signature_hash` are recorded, the database schema lacks a trigger or check constraint preventing updates to narrative fields once signed. In a medicolegal dispute, proving that a SOAP note was not edited after signature requires strict tamper-proof immutability (`BE-SOP-F01`).
- **Signature Integrity (CWE-347):** The model allows `is_signed=True` with `signed_at=NULL` or `signature_hash=NULL`, which could allow incomplete signature states (`BE-SOP-F02`).

### 3. Code quality [QUAL]
- Clean declarative mapping using SQLAlchemy 2.0 type-annotated mapped columns.
- Correct use of `ondelete="SET NULL"` on `doctor_id` and `encounter_id`, ensuring medical notes survive doctor profile updates or appointment cleanups.
- Consistent application of `lazy="selectin"` on all relationships.

### 4. AI-generated-code smells [QUAL]
- None; the model represents a textbook implementation of clinical progress documentation standards.

### 5. Performance [PERF]
- Fast lookups: `patient_id`, `doctor_id`, `encounter_id`, `note_type`, `status`, and `is_signed` are properly indexed.
- `lazy="selectin"` guarantees single-roundtrip async queries.

### 6. Error handling & edge cases
- All SOAP narrative sections (`chief_complaint`, `subjective`, `objective`, `assessment`, `plan`) are marked `nullable=False`, ensuring incomplete or empty clinical notes cannot be persisted.

### 7. Doc accuracy [DOC]
- Perfectly conforms to Month 2 Day 23 EMR roadmap specifications.

### 8. Tests
- Covered by `backend/tests/test_soap_notes.py` and `backend/tests/test_fhir.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SOP-F01 | S2 | [SEC] | 130-144 | Signed clinical notes lack DB immutability guard | No trigger or constraint preventing edits when `is_signed=True` | Enforce immutability in service layer or add DB update trigger |
| BE-SOP-F02 | S3 | [QUAL] | 130-144 | Inconsistent signature states permitted | No check constraint linking `is_signed` to `signature_hash` | Add `CheckConstraint("NOT is_signed OR (signed_at IS NOT NULL AND signature_hash IS NOT NULL)")` |

---

## Suggested Patches (NOT Applied)

### Patch BE-SOP-F02 · Risk: Low · [UNTESTED]
Ensure signature metadata completeness when `is_signed=True`:

```diff
--- a/backend/app/models/soap_note.py
+++ b/backend/app/models/soap_note.py
@@ -5,4 +5,5 @@ from typing import Optional, TYPE_CHECKING
 from sqlalchemy import (
     Boolean,
+    CheckConstraint,
     DateTime,
     Enum,
@@ -160,2 +161,8 @@ class SoapNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     )
+
+    __table_args__ = (
+        CheckConstraint(
+            "NOT is_signed OR (signed_at IS NOT NULL AND signature_hash IS NOT NULL)",
+            name="chk_soap_note_signed_complete",
+        ),
+    )
```

---

## Verdict

**READY-WITH-FIXES** — Outstanding clinical encounter documentation model with LOINC narrative mapping; adding signature completeness constraints ensures medicolegal reliability.
