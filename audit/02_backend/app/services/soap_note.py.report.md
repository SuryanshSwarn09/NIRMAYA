# Principal Software Engineering Audit: backend/app/services/soap_note.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/soap_note.py` governs the clinical documentation lifecycle for clinical encounters on the NIRMAYA platform. It structures clinical data into Subjective, Objective, Assessment, and Plan (SOAP) sections, validates relationships between patients, practitioners, and clinical encounters, enforces immutability on finalized notes, and applies an electronic signature digest. Critical security and regulatory deficiencies exist in its digital signing mechanism: the service computes a plain SHA-256 string hash rather than an asymmetric cryptographic digital signature (e.g., DSC, PKI, or Aadhaar eSign), which fails the legal attestation requirements of India's Information Technology Act 2000 and National Medical Commission (NMC) Telemedicine Practice Guidelines. Furthermore, draft clinical notes can be modified or permanently purged without author authorization checks, introducing IDOR and audit trail destruction risks.

### System Topology & Architectural Invariants
```
                  +-------------------------------------------------+
                  |      Clinical Documentation & Encounter API     |
                  |          (app.api.v1.endpoints.soap_notes)      |
                  +-----------------------+-------------------------+
                                          |
                                          v
                  +-------------------------------------------------+
                  |       SoapNoteService / Functions               |
                  |             (soap_note.py)                      |
                  +-----------------------+-------------------------+
                                          |
        +-----------------+---------------+-----------------+
        |                 |               |                 |
        v                 v               v                 v
  +-----------+     +-----------+   +-----------+     +-----------+
  | create_   |     | update_   |   | sign_     |     | delete_   |
  | soap_note |     | soap_note |   | soap_note |     | soap_note |
  | - Verify  |     | - Checks  |   | - Checks  |     | - If signed: |
  |   Patient,|     |   !signed |   |   !signed |     |   ENTERED_IN_ERROR
  |   Doctor, |     | - Mutates |   | - Generates|    | - If draft:|
  |   Appt    |     |   fields  |   |   SHA-256 |     |   db.delete|
  +-----------+     +-----------+   |   digest  |     +-----------+
                                    | - Sets    |
                                    |   FINAL   |
                                    +-----------+
```

### Import / Export Surface Map
- **Upstream Dependencies:**
  - `datetime.datetime`, `datetime.timezone`: Timestamp recording.
  - `hashlib`: SHA-256 message digestion.
  - `typing.List`, `typing.Optional`, `typing.Tuple`: Type annotations.
  - `sqlalchemy.func`, `sqlalchemy.select`: Query expression builders.
  - `sqlalchemy.ext.asyncio.AsyncSession`: Asynchronous database interaction.
  - `sqlalchemy.orm.selectinload`: Eager-loading of relationship graphs.
  - `app.core.exceptions`: `EntityNotFoundException`.
  - `app.models.appointment`: `Appointment`.
  - `app.models.doctor`: `DoctorProfile`.
  - `app.models.enums`: `ClinicalNoteStatus`, `ClinicalNoteType`.
  - `app.models.patient`: `PatientProfile`.
  - `app.models.soap_note`: `SoapNote`.
  - `app.schemas.soap_note`: `SoapNoteCreate`, `SoapNoteFilter`, `SoapNoteSignRequest`, `SoapNoteUpdate`.
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/soap_notes.py`: Clinical endpoints for SOAP note authoring, signing, and retrieval.
- **Exported Interface:**
  - `create_soap_note`: Validates actors and persists draft notes.
  - `get_soap_note_by_id`: Fetches note with eager-loaded relationships.
  - `list_patient_soap_notes`: Paginated longitudinal query for patient notes.
  - `update_soap_note`: Mutates draft note fields before signing.
  - `sign_soap_note`: Attests note with SHA-256 hash and locks status to `FINAL`.
  - `delete_soap_note`: Soft-deletes (entered-in-error) or purges draft.
  - `SoapNoteService`: Class-based wrapper around service functions.

---

## Layer B: Plain-Language Developer Walkthrough

The `soap_note.py` module manages medical documentation from initial encounter note taking through legal signing and archiving:
1. **Creation (`create_soap_note`)**: A physician or clinical scribe initializes a SOAP note. The function validates that the referenced `PatientProfile` exists and, if specified, verifies the `DoctorProfile` and `Appointment` encounter ID. The note is persisted in `PRELIMINARY` status with `is_signed=False`.
2. **Retrieval & Listing (`get_soap_note_by_id`, `list_patient_soap_notes`)**: Notes are loaded using SQLAlchemy's `selectinload` for the associated `patient`, `doctor`, and `encounter` models to avoid $N+1$ select queries. Paginated listing supports filtering by status, note type, encounter, or signed flag.
3. **Draft Mutation (`update_soap_note`)**: Physicians can amend notes during the clinical encounter. If `note.is_signed` is `True`, an error is raised immediately, preserving medical immutability.
4. **Attestation & Finalization (`sign_soap_note`)**: When the physician concludes the encounter, they sign the note. The engine concatenates key clinical fields (`patient_id`, `chief_complaint`, `subjective`, `objective`, `assessment`, `plan`, `primary_diagnosis_code`, timestamp) into a canonical pipe-delimited string and computes a SHA-256 digest (`note.signature_hash`). The status is promoted to `ClinicalNoteStatus.FINAL`.
5. **Retraction (`delete_soap_note`)**: If a note has already been signed, standard medical record regulations prohibit physical record deletion; the service transitions its status to `ENTERED_IN_ERROR`. If still unsigned, it is deleted from the database table.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Pseudo-Digital Signature Lacks Asymmetric Cryptography
In `sign_soap_note` (lines 184-196):
```python
signature_payload = (
    f"id:{note.id}|patient:{note.patient_id}|doctor:{note.doctor_id}|"
    f"encounter:{note.encounter_id}|cc:{note.chief_complaint}|"
    f"s:{note.subjective}|o:{note.objective}|a:{note.assessment}|p:{note.plan}|"
    f"dx:{note.primary_diagnosis_code}|signed_at:{now_iso}"
)
signature_hash = hashlib.sha256(signature_payload.encode("utf-8")).hexdigest()
```
Computing a plain SHA-256 hash does not constitute a legal digital signature. Anyone with database write access can alter note text, recompute the SHA-256 digest, and store the updated hash with zero detection. Under the Indian Information Technology Act 2000 (Section 3/3A) and ABDM guidelines, clinical documents require an asymmetric digital signature generated using an accredited Digital Signature Certificate (DSC) or Aadhaar eSign, binding the doctor's verified private key to the record.

### Invariant 2: Missing Author Authorization on Update (IDOR Vulnerability)
In `update_soap_note` (lines 143-163), the function accepts `note_id` and `payload`, but accepts no authenticated practitioner identity (`current_doctor_id`). Any authenticated user with API access can modify any other doctor's preliminary clinical notes by guessing or enumerating the `note_id`, violating clinical data integrity and confidentiality.

### Invariant 3: Hard Deletion of Unsigned Clinical Notes
In `delete_soap_note` (lines 208-218), if `note.is_signed` is `False`, the row is physically purged via `await db.delete(note)`. Clinical audit requirements mandate that all clinical documentation attempts—even discarded preliminary drafts—maintain an audit log trail for medicolegal liability investigations.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SVC-SOP-F01` | **S1** | `[SEC]` | `soap_note.py:184-196` | Electronic signature is an unauthenticated SHA-256 digest without asymmetric PKI/DSC cryptographic binding, failing IT Act 2000 standards. |
| `BE-SVC-SOP-F02` | **S1** | `[SEC]` | `soap_note.py:143-163` | `update_soap_note` lacks author attribution or RBAC verification, allowing arbitrary users to modify preliminary clinical notes (IDOR). |
| `BE-SVC-SOP-F03` | **S2** | `[SEC]` / `[QUAL]` | `soap_note.py:208-218` | Hard deletion (`db.delete`) of preliminary notes destroys clinical documentation audit trails. |
| `BE-SVC-SOP-F04` | **S2** | `[SEC]` | `soap_note.py:178-180` | `sign_soap_note` allows an arbitrary `signing_doctor_id` to attach themselves as the author if `doctor_id` was previously unset. |
| `BE-SVC-SOP-F05` | **S3** | `[PERF]` | `soap_note.py:123-125` | Subquery count in `list_patient_soap_notes` executes a separate query scan on every paginated read. |
| `BE-SVC-SOP-F06` | **S4** | `[DOC]` | `soap_note.py:1-6` | Lacks documentation on HL7 FHIR Composition resource serialization and LOINC document code mappings (`371530004` / `11488-4`). |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-SOP-F02-F03`: Author Attribution Verification & Soft Deletion
```diff
--- a/backend/app/services/soap_note.py
+++ b/backend/app/services/soap_note.py
@@ -14,6 +14,7 @@
 from sqlalchemy.ext.asyncio import AsyncSession
 from sqlalchemy.orm import selectinload
 
+from app.core.exceptions import PermissionDeniedException
 from app.core.exceptions import EntityNotFoundException
 from app.models.appointment import Appointment
 from app.models.doctor import DoctorProfile
@@ -145,9 +146,13 @@
     db: AsyncSession,
     note_id: str,
     payload: SoapNoteUpdate,
+    editor_doctor_id: Optional[str] = None,
 ) -> SoapNote:
     """Update an existing clinical note prior to final cryptographic signature."""
     note = await get_soap_note_by_id(db, note_id)
+    if editor_doctor_id and note.doctor_id and note.doctor_id != editor_doctor_id:
+        raise PermissionDeniedException("You are not authorized to edit another practitioner's clinical note")
+
     if note.is_signed:
         raise ValueError(
             "Cannot modify a finalized and digitally signed clinical note. "
@@ -213,6 +218,8 @@
     if note.is_signed:
         note.status = ClinicalNoteStatus.ENTERED_IN_ERROR
         await db.commit()
     else:
-        await db.delete(note)
+        # Soft delete draft note to preserve forensic auditability
+        note.status = ClinicalNoteStatus.ENTERED_IN_ERROR
         await db.commit()
```
