# Audit Report: backend/app/models/medication_request.py

**Path:** `backend/app/models/medication_request.py` | **Layer:** Backend (ORM Models) | **Language:** Python 3.12 (SQLAlchemy 2.0) | **LOC:** 287 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Relational persistence model for electronic prescriptions and medication requests, implementing structured dosage instructions, repeats, generic substitutions, and cryptographic digital signatures conforming to HL7 FHIR R4 `MedicationRequest`.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `MedicationRequest.dispensations` sets `cascade="all, delete-orphan"`, creating an architectural conflict with the database foreign key (`ondelete="RESTRICT"`) and risking purge of pharmacy fulfillment records when a prescription is modified or deleted in SQLAlchemy.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Electronic prescribing requires a legally binding, clinically detailed record of what medication a physician prescribed to a patient. It must capture the exact dosage schedule (e.g., "500 mg orally twice daily for 14 days"), route, quantity to dispense, allowed refills, indication (linked condition), and cryptographic proof (SHA-256 digital signature) that the prescription was not altered after authoring. This file represents the core e-prescription entity.

### How it works, step by step
1. `MedicationRequest` links a patient (`patient_id`), physician prescriber (`doctor_id`), clinical encounter (`encounter_id`), and catalog drug (`medication_id`).
2. It tracks clinical status (`DRAFT`, `ACTIVE`, `COMPLETED`, `CANCELLED`, `STOPPED`) and intent (`ORDER`).
3. It captures structured dosage instructions: `dosage_text`, `dose_quantity`, `dose_unit`, `route`, `frequency`, and `period`.
4. It specifies pharmacy dispense parameters: `dispense_quantity`, `expected_supply_duration_days`, and `number_of_repeats_allowed`.
5. It records generic substitution permissions (`allow_generic_substitution`).
6. It anchors medicolegal validity with `is_signed`, `signed_at`, and `signature_hash`.
7. It links to fulfilled pharmacy dispensations via `dispensations`.

### Concepts and patterns used
- *HL7 FHIR Release 4 Alignment:* Direct modeling of `MedicationRequest` and ABDM NRCeS Prescription StructureDefinition profiles.
- *Medicolegal Digital Signature Pattern:* Non-repudiation through SHA-256 hashing and immutable timestamping.
- *Async ORM Optimization:* Using `lazy="selectin"` across all relational joins to eliminate N+1 queries under async SQLAlchemy.

### Key lines to read first
- `medication_request.py:43-56`: Class definition and FHIR R4 resource mappings.
- `medication_request.py:123-170`: Structured dosage instruction attributes.
- `medication_request.py:229-244`: Digital signature and tamper-evident hash fields.
- `medication_request.py:276-281`: `cascade="all, delete-orphan"` on `dispensations`.

### How to change it safely
Never change `lazy="selectin"` to lazy loading, as async SQLAlchemy will raise `MissingGreenlet` errors when accessing un-awaited relationships. Do not allow modifications to dosage fields once `is_signed=True`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing`, `sqlalchemy` (Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text), `sqlalchemy.orm` (Mapped, mapped_column, relationship), `app.db.base` (Base, TimestampMixin, UUIDPrimaryKeyMixin), `app.models.enums` (AdministrationRoute, MedicationRequestStatus, MedicationRequestIntent, MedicationRequestPriority).
- **Imported By:** `backend/app/models/__init__.py`, `backend/app/models/medication.py`, `backend/app/models/medication_dispense.py`, `backend/app/models/patient.py`, `backend/app/models/doctor.py`, `backend/app/services/prescription_service.py`, `backend/app/api/v1/endpoints/prescriptions.py`.
- **Public Surface:** Class `MedicationRequest` (table `medication_request`).

### 2. Security [SEC]
- **Prescription Tampering Post-Signature (CWE-285):** The model stores `is_signed`, `signed_at`, and `signature_hash` (lines 229-244), but does not have a database-level trigger or constraint preventing column updates once `is_signed=True`. Immutability must be enforced strictly by the service layer (`BE-MRQ-F01`).
- **Cascade Deletion of Pharmacy Fulfillment Records (CWE-404):** `MedicationRequest.dispensations` specifies `cascade="all, delete-orphan"` (line 279). In contrast, `medication_dispense.py:52` defines `ondelete="RESTRICT"`. In Python, deleting a prescription will attempt to delete pharmacy dispensations, which is both a conflict with the DB constraint and an illegal destruction of pharmacy dispensing logs (`BE-MRQ-F02`).

### 3. Code quality [QUAL]
- **Missing Range Constraints:**
  - `number_of_repeats_allowed` (lines 184-188) has no check constraint enforcing non-negative values (`>= 0`) (`BE-MRQ-F03`).
  - `dose_quantity` and `dispense_quantity` lack positive checks.
- Exceptional architectural consistency with `lazy="selectin"` configured on all 6 relationships.

### 4. AI-generated-code smells [QUAL]
- The orphan cascade on `dispensations` is a copy-paste error from parent-child composite models (like appointments/slots), failing to recognize that prescriptions and dispensations are distinct legal transactions between separate parties (physician and pharmacist).

### 5. Performance [PERF]
- Highly optimized: `lazy="selectin"` prevents N+1 query overhead in async contexts.
- Key foreign keys and query filters (`patient_id`, `doctor_id`, `status`, `is_signed`, `reason_code`) are indexed.

### 6. Error handling & edge cases
- `doctor_id` and `encounter_id` use `ondelete="SET NULL"`, preserving prescriptions even if doctor profiles or appointment records are cleaned up.

### 7. Doc accuracy [DOC]
- Perfectly conforms to Month 2 Day 27 roadmap specifications.

### 8. Tests
- Covered by `backend/tests/test_prescriptions.py` and `backend/tests/test_fhir.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-MRQ-F01 | S2 | [QUAL] | 276-281 | ORM delete cascade conflicts with DB constraint on dispensations | `cascade="all, delete-orphan"` vs `ondelete="RESTRICT"` on dispense | Remove `cascade="all, delete-orphan"` from `dispensations` |
| BE-MRQ-F02 | S3 | [QUAL] | 184-188 | No non-negative check on refills allowed | `number_of_repeats_allowed: Mapped[int]` | Add `CheckConstraint("number_of_repeats_allowed >= 0")` |
| BE-MRQ-F03 | S3 | [QUAL] | 172-179 | Dispense quantity lacks positive check | `dispense_quantity: Mapped[Optional[float]]` | Add check constraint ensuring positive value when present |

---

## Suggested Patches (NOT Applied)

### Patch BE-MRQ-F01 · Risk: Low · [UNTESTED]
Remove delete cascade on pharmacy dispensations to align with database foreign key:

```diff
--- a/backend/app/models/medication_request.py
+++ b/backend/app/models/medication_request.py
@@ -276,6 +276,5 @@ class MedicationRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     dispensations: Mapped[List["MedicationDispense"]] = relationship(
         "MedicationDispense",
         back_populates="prescription",
-        cascade="all, delete-orphan",
         lazy="selectin",
     )
```

---

## Verdict

**READY-WITH-FIXES** — Comprehensive FHIR R4 e-prescription model with excellent async `selectin` loading; removing the delete cascade on dispensations resolves the schema-ORM mismatch.
