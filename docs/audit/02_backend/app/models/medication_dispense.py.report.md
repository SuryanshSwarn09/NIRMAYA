# Audit Report: backend/app/models/medication_dispense.py

**Path:** `backend/app/models/medication_dispense.py` | **Layer:** Backend (ORM Models) | **Language:** Python 3.12 (SQLAlchemy 2.0) | **LOC:** 184 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Relational persistence model for pharmacy medication dispensing and fulfillment, tracking batch lot numbers, drug expiration dates, substitution audits, and delivery to patients conforming to HL7 FHIR R4 `MedicationDispense`.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `quantity_dispensed` has no check constraint enforcing a positive value (`> 0`), permitting negative or zero quantities that could corrupt pharmacy inventory calculations and clinical safety telemetry.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Prescribing a medication is only the first step; a licensed pharmacy or hospital dispensary must fulfill the prescription. The dispensing event must record exactly which physical drug batch was handed to the patient, the batch expiration date, whether a generic substitution was performed, and the dispensing pharmacist's identity. This file tracks that physical fulfillment lifecycle.

### How it works, step by step
1. `MedicationDispense` generates a unique business tracking number (`dispense_number`, e.g., `DISP-2026-00042`).
2. It links to the authorizing prescription (`prescription_id`), patient (`patient_id`), and medication (`medication_id`).
3. It identifies the dispensing pharmacist via `dispenser_id`.
4. It tracks fulfillment state via `MedicationDispenseStatus` (`PREPARATION`, `IN_PROGRESS`, `COMPLETED`, `DECLINED`).
5. It captures critical batch governance metadata: `lot_number` and `expiration_date` for drug recall traceability.
6. It audits generic drug substitutions (`was_substituted`, `substitution_type`, `substitution_reason`).
7. It records exact timing: `when_prepared` and `when_handed_over`.

### Concepts and patterns used
- *HL7 FHIR Release 4 Alignment:* Direct modeling of the `MedicationDispense` resource.
- *Pharmaceutical Batch Governance:* Lot number and expiration tracking for drug recall safety.
- *Pharmacovigilance & Substitution Audit:* Auditing why a brand-name drug was substituted for a generic equivalent.

### Key lines to read first
- `medication_dispense.py:36-47`: `MedicationDispense` class and unique `dispense_number`.
- `medication_dispense.py:49-56`: Authorizing prescription foreign key with `ondelete="RESTRICT"`.
- `medication_dispense.py:116-126`: Pharmaceutical lot and expiration date tracking.
- `medication_dispense.py:138-152`: Generic substitution audit fields.

### How to change it safely
Never change `ondelete="RESTRICT"` on `prescription_id` or `medication_id`; active pharmacy fulfillment records must legally lock the authorizing prescription against deletion.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing`, `sqlalchemy` (Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text), `sqlalchemy.orm` (Mapped, mapped_column, relationship), `app.db.base` (Base, TimestampMixin, UUIDPrimaryKeyMixin), `app.models.enums` (MedicationDispenseStatus).
- **Imported By:** `backend/app/models/__init__.py`, `backend/app/models/medication_request.py`, `backend/app/services/pharmacy_service.py`, `backend/app/api/v1/endpoints/pharmacy.py`.
- **Public Surface:** Class `MedicationDispense` (table `medication_dispense`).

### 2. Security [SEC]
- **Inventory & Billing Tampering (CWE-20):** `quantity_dispensed: Mapped[float]` (line 100-103) lacks an SQL check constraint enforcing `quantity_dispensed > 0`. A negative quantity could be exploited to manipulate pharmacy inventory levels or create fraudulent billing refunds (`BE-DISP-F01`).
- **Pharmacovigilance Audit Trail:** Proper `RESTRICT` on delete prevents deletion of prescriptions with dispensed medications, ensuring non-repudiation.

### 3. Code quality [QUAL]
- **Missing Non-Negative Constraint on Days of Supply:** `days_supply: Mapped[Optional[int]]` (lines 111-114) lacks a check constraint enforcing positive values (`BE-DISP-F02`).
- Excellent declarative mapping with clean foreign key integrity.

### 4. AI-generated-code smells [QUAL]
- None; the model shows thorough domain modeling of hospital and retail pharmacy workflows.

### 5. Performance [PERF]
- Well-indexed: `dispense_number`, `prescription_id`, `patient_id`, `medication_id`, `dispenser_id`, `status`, and `lot_number` are indexed for fast dispensary searches and recall batch queries.

### 6. Error handling & edge cases
- If `patient_id` cascades, dispense records are purged. In clinical pharmacy regulations (e.g. Schedule H/X drug logs), fulfillment records must be retained even if the patient account is closed.

### 7. Doc accuracy [DOC]
- Accurately fulfills Month 2 Day 29 pharmacy fulfillment specifications.

### 8. Tests
- Covered by `backend/tests/test_pharmacy.py` and `backend/tests/test_medication_dispense.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-DISP-F01 | S2 | [QUAL] | 100-103 | No constraint ensuring positive dispensed quantity | `quantity_dispensed: Mapped[float] = mapped_column(Float, nullable=False)` | Add `CheckConstraint("quantity_dispensed > 0")` |
| BE-DISP-F02 | S3 | [QUAL] | 111-114 | No constraint ensuring positive days of supply | `days_supply: Mapped[Optional[int]] = mapped_column(...)` | Add `CheckConstraint("days_supply > 0")` |

---

## Suggested Patches (NOT Applied)

### Patch BE-DISP-F01 · Risk: Low · [UNTESTED]
Enforce positive dispense quantities at the database constraint level:

```diff
--- a/backend/app/models/medication_dispense.py
+++ b/backend/app/models/medication_dispense.py
@@ -13,4 +13,5 @@ from sqlalchemy import (
     Boolean,
+    CheckConstraint,
     Date,
     DateTime,
@@ -179,2 +180,6 @@ class MedicationDispense(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     )
+
+    __table_args__ = (
+        CheckConstraint("quantity_dispensed > 0", name="chk_dispense_qty_positive"),
+    )
```

---

## Verdict

**READY-WITH-FIXES** — Robust pharmacy fulfillment model; adding a check constraint on `quantity_dispensed` prevents data entry and inventory calculation errors.
