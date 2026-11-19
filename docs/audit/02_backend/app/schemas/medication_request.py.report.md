# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/medication_request.py`
**Audited Path:** `backend/app/schemas/medication_request.py`  
**Module:** `backend` | **Subsystem:** Electronic Prescribing (e-Rx) & FHIR MedicationRequest  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/medication_request.py` defines the Pydantic v2 schemas for authoring, updating, digitally signing, and cancelling electronic prescriptions in NIRMAYA. Strictly aligned with the HL7 FHIR Release 4 `MedicationRequest` resource and the Ayushman Bharat Digital Mission (ABDM) NRCES Prescription Document Profile, this module structures:
- Prescribing clinical intent (`ORDER`, `PROPOSAL`, `PLAN`) and clinical priority (`ROUTINE`, `URGENT`, `ASAP`, `STAT`).
- Complete structured dosage administration instructions, route, frequency, duration, and PRN (as-needed) indications (`MedicationRequestBase`).
- Digital signature authorization protocols with SHA-256 cryptographic seals (`MedicationRequestSignRequest`, `MedicationRequestResponse`).
- Prescription cancellation workflows with mandatory clinical justification (`MedicationRequestCancelRequest`).
- Multi-dimensional query filters for patient medication history and doctor prescription queues (`MedicationRequestFilter`).

#### 2. Key Components & Class Roster
- `MedicationRequestBase`: Core e-prescribing fields including linked `medication_id`, optional `encounter_id`, clinical intent (`MedicationRequestIntent`), priority (`MedicationRequestPriority`), human-readable `dosage_text`, numeric `dose_quantity`, administration `route`, intake `frequency`, timing `period`, PRN flags (`as_needed`, `as_needed_reason`), pharmacy dispense quantity (`dispense_quantity`), treatment duration in days (`expected_supply_duration_days`), authorized refills (`number_of_repeats_allowed`), validity period start/end timestamps, generic substitution permissions (`allow_generic_substitution`), and clinical indication diagnosis codes (`reason_code`, e.g. ICD-10 `E11.9`).
- `MedicationRequestCreate`: Payload schema for issuing a new e-prescription.
- `MedicationRequestUpdate`: Schema for revising unsigned draft prescriptions.
- `MedicationRequestSignRequest`: Clinician payload for applying digital signature certificates and signing remarks.
- `MedicationRequestCancelRequest`: Clinical discontinuation payload requiring mandatory justification (`cancellation_reason`, min 3 characters).
- `MedicationRequestResponse`: Comprehensive domain response model including doctor UUID, status, authored timestamp, digital signature hash, cancellation details, and embedded `MedicationResponse` metadata.
- `MedicationRequestFilter`: Query filter schema supporting status, signing state, doctor ID, encounter ID, and date range filters.

---

### Layer B: Plain-Language Developer Walkthrough

Paper prescriptions in India are notoriously difficult to decipher, easy to forge, and prone to severe medical errors—such as dispensing a 10x overdose or failing to notice that two prescribed drugs have dangerous interactions. Under the national ABDM digital health mission, doctors issue digital e-prescriptions that are cryptographically signed and directly transmitted to pharmacies and patient health lockers.

`medication_request.py` provides the digital blueprint for every prescription issued on NIRMAYA:
1. When a doctor prescribes a medicine, they submit a `MedicationRequestCreate` payload. It requires explicit, human-readable instructions (e.g. "Take 1 tablet orally twice daily with meals for 14 days") along with machine-readable dosage values (dose quantity, frequency, route).
2. The prescription specifies whether the pharmacist is permitted to substitute a cheaper generic alternative (`allow_generic_substitution=True`).
3. To become legally active, the attending physician submits a `MedicationRequestSignRequest`. The system binds the prescription with the doctor's certified Healthcare Professional Registry (HPR) credentials and generates a SHA-256 `signature_hash`.
4. If the patient experiences an adverse reaction or the treatment is completed, the physician can formally discontinue the medication using `MedicationRequestCancelRequest`, providing a mandatory clinical explanation (e.g., "Adverse gastrointestinal reaction; switched to linagliptin").

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **HL7 FHIR R4 Alignment:** Adheres directly to FHIR R4 MedicationRequest elements (`intent`, `priority`, `dosageInstruction`, `dispenseRequest`, `substitution`).
- **Refill Bounding:** `number_of_repeats_allowed` enforces an upper ceiling (`le=12`), preventing unauthorized infinite automated refills.
- **Mandatory Cancellation Rationale:** `cancellation_reason` in `MedicationRequestCancelRequest` enforces `min_length=3` to block empty cancellation submissions.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Missing Temporal Order Validation on Validity Period (`BE-SCH-MRQ-F01`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/medication_request.py:122-129`
- **Description:** Fields `validity_period_start` and `validity_period_end` are parsed independently without a cross-field model validator ensuring that `validity_period_start <= validity_period_end`. A prescription where the end validity date precedes the start date passes schema validation without error.
- **Impact:** Chronological corruption in electronic prescription validity windows.
- **Remediation:** Add a `@model_validator(mode="after")` enforcing that `validity_period_start <= validity_period_end`.

##### Vulnerability 2: Unvalidated Cryptographic Digital Signature Hash (`BE-SCH-MRQ-F02`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/medication_request.py:222`
- **Description:** In `MedicationRequestResponse`, `signature_hash: Optional[str]` is declared as a plain string without format constraints. In an ABDM-compliant system, this hash represents the SHA-256 digital signature of the prescription artifact and must strictly adhere to 64-character hexadecimal notation.
- **Impact:** Malformed or truncated signature hashes pass validation, weakening cryptographic non-repudiation.
- **Remediation:** Enforce `pattern=r"^[a-fA-F0-9]{64}$"` and `min_length=64, max_length=64`.

##### Vulnerability 3: Non-Positive Dose and Dispense Quantities Allowed (`BE-SCH-MRQ-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/medication_request.py:48, 98`
- **Description:** `dose_quantity` and `dispense_quantity` specify `ge=0`, which mathematically allows prescriptions with `0.0` dose or `0.0` dispense quantity. A medication order with zero quantity is clinically invalid and nonsensical.
- **Impact:** Clinically invalid zero-quantity prescriptions can be authored.
- **Remediation:** Update bounds to strict positive values (`gt=0`).

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-MRQ-F01` | S2 | `[QUAL]` | `medication_request.py:122-129` | Missing validator verifying `validity_period_start <= validity_period_end` |
| `BE-SCH-MRQ-F02` | S2 | `[QUAL]` | `medication_request.py:222` | `signature_hash` lacks 64-character hex regex validation |
| `BE-SCH-MRQ-F03` | S3 | `[QUAL]` | `medication_request.py:48, 98` | `dose_quantity` and `dispense_quantity` allow non-positive zero values (`ge=0`) |
| `BE-SCH-MRQ-F04` | S3 | `[QUAL]` | `medication_request.py:191, 200, 233` | Missing `ConfigDict(from_attributes=True)` on auxiliary request/filter models |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/medication_request.py
+++ b/backend/app/schemas/medication_request.py
@@ -6,5 +6,5 @@
 from datetime import datetime
 from typing import Any, Dict, List, Optional
-from pydantic import BaseModel, ConfigDict, Field
+from pydantic import BaseModel, ConfigDict, Field, model_validator
 
 from app.models.enums import (
@@ -46,3 +46,3 @@ class MedicationRequestBase(BaseModel):
     dose_quantity: Optional[float] = Field(
         default=None,
-        ge=0,
+        gt=0,
         description="Numerical amount of medication per single dose",
@@ -96,3 +96,3 @@ class MedicationRequestBase(BaseModel):
     dispense_quantity: Optional[float] = Field(
         default=None,
-        ge=0,
+        gt=0,
         description="Total quantity of medication authorized for pharmacy dispense",
@@ -128,4 +128,11 @@ class MedicationRequestBase(BaseModel):
         description="Expiration date/time of prescription validity",
     )
+
+    @model_validator(mode="after")
+    def validate_validity_period(self) -> "MedicationRequestBase":
+        if self.validity_period_start and self.validity_period_end:
+            if self.validity_period_start > self.validity_period_end:
+                raise ValueError("validity_period_start must be earlier than or equal to validity_period_end")
+        return self
@@ -222,3 +229,9 @@ class MedicationRequestResponse(MedicationRequestBase):
     signed_at: Optional[datetime] = None
-    signature_hash: Optional[str] = None
+    signature_hash: Optional[str] = Field(
+        default=None,
+        pattern=r"^[a-fA-F0-9]{64}$",
+        min_length=64,
+        max_length=64,
+        description="Cryptographic SHA-256 seal of authorized prescription",
+    )
     cancellation_reason: Optional[str] = None
```
