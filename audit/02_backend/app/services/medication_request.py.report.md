# Codebase Technical Audit Report: `backend/app/services/medication_request.py`

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`medication_request.py` provides the electronic prescription authoring, updating, digital signing, cancellation, and retrieval service layer for the NIRMAYA platform. It enforces HL7 FHIR Release 4 `MedicationRequest` data models and clinical standards, binding prescriptions to patients, licensed doctors, clinical encounters, problem list conditions, and formulary medications. It provides tamper-evident SHA-256 digital signature sealing and guarantees post-signature record immutability.

### System Topology & Prescription Pipeline
```
   [ Clinician Workspace ]
             |
   (Author Draft e-Rx)
             v
   +---------------------------------------+
   |        MedicationRequestService       |
   +---------------------------------------+
   | - Draft Authoring & Clinical Binding  |
   | - Pre-Signature Schema Mutation       |
   | - SHA-256 Canonical Signature Sealing |
   | - Immutability Enforcement            |
   | - Controlled Cancellation FSM         |
   +---------------------------------------+
             |                     |
     (Sign & Seal)         (Cancel / Error)
             v                     v
   [ Immutable Active e-Rx ]  [ Cancelled Record ]
   (Dispensable Artifact)     (Audit Rationale Kept)
```

### Module Metadata & Imports/Exports
- **Module Path:** `backend/app/services/medication_request.py`
- **Component Classification:** Clinical E-Prescribing & Order Management Service
- **Lines of Code:** 297 LOC
- **Imports:** `datetime`, `hashlib`, `typing`, `sqlalchemy.*`, `sqlalchemy.ext.asyncio.AsyncSession`, `app.core.exceptions.*`, `app.models.*`, `app.schemas.medication_request.*`
- **Primary Exports:** `create_prescription`, `get_prescription_by_id`, `update_prescription`, `sign_prescription`, `cancel_prescription`, `mark_entered_in_error`, `list_prescriptions`

---

## Layer B: Plain-Language Developer Walkthrough

The module implements a complete clinical e-prescription lifecycle:
1. **Draft Authoring (`create_prescription`)**: A clinician creates an e-prescription. The service verifies the existence of the patient profile, formulary medication, prescribing doctor, linked encounter/appointment, and associated clinical condition. It initializes the record in `MedicationRequestStatus.DRAFT` with `is_signed=False`.
2. **Draft Modification (`update_prescription`)**: Prior to final clinician signature, dosages, frequencies, routes, duration, or notes can be adjusted. However, the service strictly blocks modification if `prescription.is_signed` is true, raising `ConflictException("IMMUTABLE_SIGNED_RECORD")`.
3. **Digital Signature & Sealing (`sign_prescription`)**: Finalizes the prescription. The physician's identity is verified, and a canonical representation of the order is assembled:
   $$\text{Payload} = \text{"rx:"} \parallel \text{id} \parallel \text{"|patient:"} \parallel \text{patient\_id} \parallel \dots \parallel \text{"|signed\_at:"} \parallel \text{iso\_timestamp}$$
   The service hashes this string using SHA-256, sets `is_signed=True`, status to `ACTIVE`, and records the signature digest and timestamp.
4. **Discontinuation & Error Handling (`cancel_prescription` & `mark_entered_in_error`)**: For adverse reactions or discontinued treatments, clinicians cancel prescriptions with mandatory clinical rationales. Per FHIR standards, clerical mistakes transition records to `ENTERED_IN_ERROR`.
5. **Multi-Criteria Search (`list_prescriptions`)**: Provides paginated querying with filters across patient ID, doctor ID, signature state, encounter, reason code, and authored date ranges.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Post-Signature Immutability
Once a clinical order is signed and authorized by a physician, it becomes a legal artifact under the National Medical Commission (NMC) guidelines and the Information Technology Act 2000. Any subsequent modification of dosage, drug, or instructions is forbidden. Line 140 enforces this invariant by throwing a 409 Conflict if an update is attempted on a signed record.

### Invariant 2: Deterministic Canonical Signature Hashing
The signature digest is derived from a deterministic serialization of all clinical fields (drug, dose, unit, frequency, route, dispense quantity, and repeat limits). If any downstream actor attempts to tamper with the database row, the signature digest will no longer match the recalculated hash, exposing corruption during medicolegal audits.

### Invariant 3: Relational Referential Integrity
An e-prescription cannot exist in isolation. The service verifies foreign key integrity across the patient registry (`PatientProfile`), doctor registry (`DoctorProfile`), formulary (`Medication`), and optional encounter/condition entities before inserting the record into PostgreSQL.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
|---|---|---|---|---|
| `BE-SVC-MDR-F01` | **S1** | `[SEC]` | `backend/app/services/medication_request.py:175-225` | Pseudo-Digital Signature is a Plain SHA-256 Hash without Clinician Private Key Asymmetric Cryptography (DSC/PKI/eSign). `sign_prescription()` concatenates string attributes and computes `hashlib.sha256()`. This is an integrity checksum, not a legally binding digital signature under Information Technology Act 2000 Section 3 or National Medical Commission (NMC) Telemedicine Practice Guidelines! Any system component or database administrator can forge or recompute the hash without possessing the clinician's private key. |
| `BE-SVC-MDR-F02` | **S1** | `[SEC]` | `backend/app/services/medication_request.py:65-75, 185-195` | Authoring and Signing Prescriptions Permits `author_doctor_id=None` or `signing_doctor_id=None`. If `author_doctor_id` is omitted and the payload does not set it, prescriptions can be authored and even signed without any identified prescriber doctor, creating dangerous untraceable medication orders. |
| `BE-SVC-MDR-F03` | **S2** | `[SEC]` | `backend/app/services/medication_request.py:228-245` | Unrestricted Prescription Cancellation and Error Marking Without Verification of Downstream Dispensations. `cancel_prescription` and `mark_entered_in_error` do not verify if active dispensations (`MedicationDispense`) already exist. If a pharmacy has already dispensed the drug, cancelling the prescription without notifying the pharmacy or recalling stock creates serious patient safety risks. |
| `BE-SVC-MDR-F04` | **S2** | `[QUAL]` | `backend/app/services/medication_request.py:145-165` | Pre-Signature Mutation of Draft Prescription Lacks Audit Trail / Versioning. Modifying draft prescription attributes in-place deletes previous values without keeping a revision history prior to signature. |
| `BE-SVC-MDR-F05` | **S3** | `[PERF]` | `backend/app/services/medication_request.py:280-295` | Subquery Count in `list_prescriptions` Causes Full Table Materialization for Large Result Sets. |
| `BE-SVC-MDR-F06` | **S4** | `[DOC]` | `backend/app/services/medication_request.py:12-18` | Missing Clinical Decision Support (CDS) Hook Trigger Documentation (`order-select`, `order-sign`). |

---

## Layer E: Unapplied Unified Diff Patches

### Patch 1: Enforce Mandatory Doctor Attribution on Creation (`BE-SVC-MDR-F02`)
```diff
--- a/backend/app/services/medication_request.py
+++ b/backend/app/services/medication_request.py
@@ -53,4 +53,6 @@ async def create_prescription(
     # 3. Resolve and verify prescriber doctor
     effective_doctor_id = author_doctor_id
+    if not effective_doctor_id:
+        raise AppException("Prescriptions must be attributed to a valid licensed physician", error_code="MISSING_PRESCRIBER", status_code=400)
     if effective_doctor_id:
         doctor = await db.scalar(select(DoctorProfile).where(DoctorProfile.id == effective_doctor_id))
```

### Patch 2: Block Cancellation if Dispensations Already Exist (`BE-SVC-MDR-F03`)
```diff
--- a/backend/app/services/medication_request.py
+++ b/backend/app/services/medication_request.py
@@ -233,4 +233,14 @@ async def cancel_prescription(
     prescription = await get_prescription_by_id(db, prescription_id)
 
+    from app.models.medication_dispense import MedicationDispense
+    disp_count = await db.scalar(
+        select(func.count(MedicationDispense.id)).where(MedicationDispense.prescription_id == prescription_id)
+    ) or 0
+    if disp_count > 0:
+        raise ConflictException(
+            message=f"Cannot unilaterally cancel prescription: {disp_count} pharmaceutical dispensation(s) already issued. Initiate pharmacy recall protocol.",
+            error_code="DISPENSATION_ALREADY_ISSUED",
+        )
+
     prescription.status = MedicationRequestStatus.CANCELLED
     prescription.cancellation_reason = cancellation_reason
```
