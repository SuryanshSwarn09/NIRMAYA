# Comprehensive Principal Software Audit & Technical Documentation
# File: `backend/app/schemas/soap_note.py`
# Component: Core EMR / Clinical Documentation Engine
# Release Version: 1.1.0-RC3 · ABDM / NRCES v4.1 Compliance

---

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/schemas/soap_note.py` provides the Pydantic v2 data transfer schemas that model clinical encounter notes following the standard SOAP (Subjective, Objective, Assessment, Plan) format. The schema maps directly to HL7 FHIR Release 4 `Composition` resources and adheres to standard LOINC narrative section designations: Chief Complaint (LOINC 10154-3), Subjective (LOINC 61150-9), Objective (LOINC 61149-1), Assessment (LOINC 51848-0), and Plan of Care (LOINC 18776-5). It handles encounter note creation, incremental drafting, cryptographic signing, record serialization, and administrative filtering.

### Architectural Role & System Topology
```
           +-----------------------------------------------+
           |       Outpatient / Clinical Consultation      |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |    SoapNoteCreate / SoapNoteUpdate (Schemas)  |
           +-----------------------------------------------+
                                  |
                   (Attestation / Signature Event)
                                  v
           +-----------------------------------------------+
           |  SoapNoteSignRequest -> SHA-256 Digest Token   |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |          SoapNote (SQLAlchemy Model)          |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |          SoapNoteResponse (FHIR R4)           |
           +-----------------------------------------------+
```

### Key Import/Export Roster
- **Imports**:
  - `datetime` from `datetime`: Signature and record timestamping.
  - `Optional` from `typing`: Nullable attribute typing.
  - `BaseModel, ConfigDict, Field` from `pydantic`: Schema validation primitives and attribute decorators.
  - `ClinicalNoteStatus, ClinicalNoteType` from `app.models.enums`: Workflow state enumerations (`PRELIMINARY`, `FINAL`, `SIGNED`, etc.).
- **Exports**:
  - `SoapNoteBase`: Core shared clinical fields for SOAP documentation.
  - `SoapNoteCreate`: Encounter note creation payload.
  - `SoapNoteUpdate`: Incremental preliminary draft mutation payload.
  - `SoapNoteSignRequest`: Clinician electronic attestation payload.
  - `SoapNoteResponse`: Serialized representation of stored clinical note.
  - `SoapNoteFilter`: Query parameters for clinical encounter note searches.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Base Clinical Properties (`SoapNoteBase`)**: Establishes required narrative sections (`chief_complaint`, `subjective`, `objective`, `assessment`, `plan`) with length boundaries, as well as optional diagnosis codes (`primary_diagnosis_code`, `primary_diagnosis_display`) and discharge instructions (`follow_up_instructions`).
2. **Drafting Notes (`SoapNoteCreate`)**: Inherits base narrative fields and accepts optional `encounter_id`, `doctor_id`, and initial workflow `status` (defaulting to `ClinicalNoteStatus.PRELIMINARY`).
3. **Revising Drafts (`SoapNoteUpdate`)**: Allows clinicians to update fields in a preliminary draft before signature. All fields are marked optional so partial updates are permitted.
4. **Attestation & Cryptographic Signing (`SoapNoteSignRequest`)**: Supplies optional attestation comments when an authorized clinician approves and locks a preliminary note into a finalized, immutable legal record.
5. **Output Serialization (`SoapNoteResponse`)**: Extends base properties with database identifiers (`id`, `patient_id`), clinical linkage (`doctor_id`, `encounter_id`), signature metadata (`is_signed`, `signed_at`, `signature_hash`), and record audit timestamps (`created_at`, `updated_at`).
6. **Search & Retrieval (`SoapNoteFilter`)**: Supports filtering encounter notes by status, classification type, encounter UUID, and signature verification state.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Immutability of Finalized SOAP Records
Under clinical governance standards and HL7 FHIR Composition lifecycle, once a clinical note transitions from `PRELIMINARY` to `SIGNED`, its clinical content (`subjective`, `objective`, `assessment`, `plan`, `diagnoses`) must be strictly immutable. `SoapNoteUpdate` allows updating `status: Optional[ClinicalNoteStatus] = None`. If an update request attempts to modify fields on a signed note or set status to `SIGNED` outside the cryptographic signature endpoint, integrity is compromised. The service layer must enforce that `SoapNoteUpdate` is only processed when `existing_note.is_signed is False`.

### Invariant 2: Cryptographic Signature Digest Format
`SoapNoteResponse.signature_hash` stores the SHA-256 cryptographic attestation digest of the canonical clinical note text. The schema models this as an unconstrained `Optional[str]`. It should enforce a 64-character hexadecimal format constraint (`pattern=r"^[a-fA-F0-9]{64}$"`).

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-SOP-F01` | S2 | `[QUAL]` | `soap_note.py:63-68` | `primary_diagnosis_code` lacks standard ICD-10/SNOMED format regex validation |
| `BE-SCH-SOP-F02` | S2 | `[QUAL]` | `soap_note.py:82-99` | `SoapNoteCreate` omits `patient_id`, creating instantiation discrepancies with `SoapNoteResponse` |
| `BE-SCH-SOP-F03` | S3 | `[QUAL]` | `soap_note.py:23, 30, 37, 43, 49, 55, 61, 67, 73, 78, 88, 93, 98, 123` | Direct `example=` argument on `Field()` is deprecated in Pydantic v2 |
| `BE-SCH-SOP-F04` | S3 | `[QUAL]` | `soap_note.py:137` | `signature_hash` lacks 64-character hexadecimal regex constraint |

---

## Layer E: Unapplied Unified Diff Patches for S0–S2 Findings

```diff
--- a/backend/app/schemas/soap_note.py
+++ b/backend/app/schemas/soap_note.py
@@ -62,7 +62,8 @@
     primary_diagnosis_code: Optional[str] = Field(
         default=None,
         max_length=50,
-        description="Standard ICD-10 or SNOMED-CT primary diagnosis code",
+        pattern=r"^([A-Z][0-9][0-9A-Z](\.[0-9A-Z]{1,4})?|[1-9][0-9]{5,17})$",
+        description="Standard ICD-10 (e.g. I10, E11.9) or SNOMED-CT (6-18 digits) code",
         example="I10",
     )
     primary_diagnosis_display: Optional[str] = Field(
@@ -84,6 +85,11 @@
 class SoapNoteCreate(SoapNoteBase):
     """Schema for creating a new structured SOAP clinical note."""
 
+    patient_id: str = Field(
+        ...,
+        pattern=r"^[0-9a-fA-F-]{36}$",
+        description="Target patient profile UUID",
+    )
     encounter_id: Optional[str] = Field(
         default=None,
         description="Optional encounter / appointment UUID linkage",
```
