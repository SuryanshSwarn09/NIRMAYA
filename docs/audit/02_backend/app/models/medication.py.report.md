# Audit Report: backend/app/models/medication.py

**Path:** `backend/app/models/medication.py` | **Layer:** Backend (ORM Models) | **Language:** Python 3.12 (SQLAlchemy 2.0) | **LOC:** 197 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Relational persistence model for the clinical medication catalog and formulary engine, implementing multi-terminology coding (RxNorm, WHO-ATC, SNOMED-CT) aligned with HL7 FHIR R4 `Medication`.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `rxnorm_code` lacks a unique constraint; duplicate drug definitions sharing identical RxCUIs can be seeded or inserted, causing ambiguous prescription lookups and formulary mismatches.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
To prescribe and dispense drugs safely, an EMR requires a standardized pharmaceutical catalog. Drugs must be clearly identified by generic active ingredient, dosage form (tablets, capsules, syrups), route of administration, quantitative strength, and multi-terminology codes (RxNorm for international standard, WHO-ATC for therapeutic classification, SNOMED-CT for clinical concepts). This file provides that authoritative formulary database.

### How it works, step by step
1. `Medication` stores the clinical brand name, generic substance name, and manufacturer brand name.
2. It assigns standardized terminology identifiers: `rxnorm_code`, `atc_code`, and `snomed_code`.
3. Clinical properties are captured via enums: `form` (`MedicationForm`), `route` (`AdministrationRoute`), and `formulary_tier` (`FormularyTier`).
4. Regulatory flags indicate prescription requirement (`is_prescription_required`) and narcotic/scheduled status (`is_controlled_substance`).
5. Storage conditions, clinical contraindications, and packaging metadata are retained.
6. Links to all historical prescriptions issued for this drug via `prescriptions`.

### Concepts and patterns used
- *HL7 FHIR Release 4 Alignment:* Conforming directly to `Medication` resource specifications and ABDM NRCeS profiles.
- *Poly-Hierarchy Medical Coding:* Simultaneously anchoring drugs in RxNorm, WHO-ATC, and SNOMED-CT.
- *Formulary Governance:* Segregating drugs into tiers (Generic, Preferred Brand, Non-Preferred, Specialty, OTC).

### Key lines to read first
- `medication.py:32-42`: `Medication` class docstring and FHIR R4 resource mapping.
- `medication.py:65-70`: `rxnorm_code` field definition.
- `medication.py:105-118`: `form` and `route` enum definitions.
- `medication.py:188-191`: `prescriptions` relationship without delete cascade.

### How to change it safely
Never modify existing `rxnorm_code` values without verifying that historical `MedicationRequest` entries remain valid. Keep enum values synchronized with `app.models.enums`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `typing` (Optional, Dict, Any, List, TYPE_CHECKING), `sqlalchemy` (Boolean, Enum, JSON, String, Text), `sqlalchemy.orm` (Mapped, mapped_column, relationship), `app.db.base` (Base, TimestampMixin, UUIDPrimaryKeyMixin), `app.models.enums` (MedicationForm, AdministrationRoute, FormularyTier, MedicationStatus).
- **Imported By:** `backend/app/models/__init__.py`, `backend/app/models/medication_request.py`, `backend/app/models/medication_dispense.py`, `backend/app/services/medication_service.py`, `backend/app/api/v1/endpoints/medications.py`.
- **Public Surface:** Class `Medication` (table `medication`).

### 2. Security [SEC]
- **Controlled Substance Flagging (CWE-285):** `is_controlled_substance: Mapped[bool]` (line 141-145) flags scheduled drugs (e.g., narcotics, psychotropics). However, there is no enforcement at the model level requiring two-factor authorization or senior practitioner credentials to prescribe controlled substances; enforcement must be guaranteed at the service layer.

### 3. Code quality [QUAL]
- **Missing Unique Constraint on RxNorm (Line 65-70):** While `rxnorm_code` is indexed, it is not marked `unique=True`. Multiple catalog rows can share the same canonical RxCUI, risking duplicate drug records (`BE-MED-F01`).
- **Inconsistent Enum Configuration (Lines 106, 114, 149, 157):** Unlike other models (`diagnostic.py`, `doctor.py`, `delegation.py`) which explicitly pass `native_enum=False` and a `name=...` parameter to `Enum()`, `medication.py` uses bare `Enum(MedicationForm)` etc. In PostgreSQL, this instructs SQLAlchemy to generate native Postgres enum types rather than `VARCHAR` checks, causing cross-database dialect divergence (`BE-MED-F02`).

### 4. AI-generated-code smells [QUAL]
- None; the model displays exceptionally disciplined pharmacological ontology design.

### 5. Performance [PERF]
- Well-indexed: `name`, `generic_name`, `brand_name`, `rxnorm_code`, `atc_code`, `snomed_code`, `form`, `route`, `active_ingredient`, `formulary_tier`, and `status` are all indexed for search queries.

### 6. Error handling & edge cases
- `prescriptions` relationship correctly omits `cascade="all, delete-orphan"`, guaranteeing that deleting a drug from the catalog will not purge patient medical prescriptions.

### 7. Doc accuracy [DOC]
- Perfectly conforms to Month 2 Day 26 roadmap specifications and ABDM NRCeS profiles.

### 8. Tests
- Covered by `backend/tests/test_medication.py` and `backend/tests/test_prescriptions.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-MED-F01 | S2 | [QUAL] | 65-70 | Duplicate RxNorm codes permitted | `rxnorm_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)` | Add `unique=True` to `rxnorm_code` |
| BE-MED-F02 | S3 | [QUAL] | 106, 114, 149, 157 | Inconsistent native enum usage across dialects | `Enum(MedicationForm)` lacks `native_enum=False` | Add `native_enum=False` and explicit enum names |

---

## Suggested Patches (NOT Applied)

### Patch BE-MED-F01 · Risk: Low · [UNTESTED]
Enforce unique RxNorm codes across the medication formulary catalog:

```diff
--- a/backend/app/models/medication.py
+++ b/backend/app/models/medication.py
@@ -65,6 +65,7 @@ class Medication(Base, UUIDPrimaryKeyMixin, TimestampMixin):
     # Standardized NLM RxNorm Concept Unique Identifier (RxCUI) (e.g. "860975")
     rxnorm_code: Mapped[str] = mapped_column(
         String(64),
+        unique=True,
         nullable=False,
         index=True,
     )
```

### S3 One-Line Fix
- **BE-MED-F02:** Add `native_enum=False, name="<name>_enum"` to all `Enum()` declarations in `medication.py`.

---

## Verdict

**READY-WITH-FIXES** — Outstanding clinical formulary model; adding uniqueness to `rxnorm_code` will prevent catalog duplication.
