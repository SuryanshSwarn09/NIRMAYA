# Principal Software Engineering Audit: backend/app/fhir/schemas.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/fhir/schemas.py` defines the canonical Pydantic v2 data models for HL7 FHIR Release 4 (v4.0.1) resources, data types, and Ayushman Bharat Digital Mission (ABDM) CareContext consent linkage artifacts used throughout the NIRMAYA platform. Spanning 1,169 lines of code, it implements FHIR R4 primitives (`FHIRIdentifier`, `FHIRCoding`, `FHIRCodeableConcept`, `FHIRReference`, `FHIRPeriod`, `FHIRQuantity`, `FHIRAnnotation`, `FHIRNarrative`) and clinical resources (`FHIRAppointment`, `FHIREncounter`, `FHIRCondition`, `FHIRObservation`, `FHIRComposition`, `FHIRServiceRequest`, `FHIRDiagnosticReport`, `FHIRMedication`, `FHIRMedicationRequest`, `FHIRMedicationDispense`, `FHIRBundle`, `ABDMConsentLinkage`). Critical security and standard conformance flaws include: (1) lack of XHTML sanitization on `FHIRNarrative.div`, permitting Stored Cross-Site Scripting (XSS) when downstream EHR consoles render narrative text, (2) representation of ABDM cryptographic signatures as plain SHA-256 string digests rather than asymmetric digital signatures (e.g. XML-DSig, JWS), (3) missing mutual exclusion validation on `medication[x]` choices in `FHIRMedicationRequest` and `FHIRMedicationDispense`, and (4) absence of resource ordering validation in document bundles.

### System Topology & Architectural Invariants
```
                  +-----------------------------------------------+
                  |          NIRMAYA FHIR Normalization Layer     |
                  +-----------------------+-----------------------+
                                          |
                                          v
                  +-----------------------------------------------+
                  |          app.fhir.schemas (1,169 LOC)         |
                  +-----------------------+-----------------------+
                                          |
        +-----------------+---------------+-----------------+
        |                 |               |                 |
        v                 v               v                 v
  +-----------+     +-----------+   +-----------+     +-----------+
  | Datatypes |     | Clinical  |   | Diagnostic|     | Pharmacy  |
  | & Core    |     | Resources |   | & Vitals  |     | & Orders  |
  | Primitives|     | - Appt    |   | - Observ- |     | - Medicat-|
  | - Coding  |     | - Encount-|     ation     |       ion       |
  | - Concept |       er        |   | - Service-|     | - Medicat-|
  | - Ref     |     | - Condit- |     Request   |       ionRequest|
  | - Period  |       ion       |   | - Diagnos-|     | - Medicat-|
  | - Quantity|     | - Composit|     ticReport |       ionDisp   |
  | - Narrat- |       ion       |   +-----------+     +-----------+
  |   ive     |     +-----------+         |
  +-----------+           |               v
                          +-----> +-------------------------------+
                                  | FHIRBundle (Collection/Doc)   |
                                  | ABDMConsentLinkage (Artifact) |
                                  +-------------------------------+
```

### Import / Export Surface Map
- **Upstream Dependencies:**
  - `datetime.datetime`, `datetime.timezone`: Timestamp representation.
  - `typing.Any`, `typing.Dict`, `typing.List`, `typing.Literal`, `typing.Optional`: Type hints.
  - `pydantic.BaseModel`, `pydantic.ConfigDict`, `pydantic.Field`: Data validation and schema generation.
- **Downstream Consumers:**
  - `backend/app/fhir/transformers.py`: Transforms internal ORM models into these Pydantic schemas.
  - `backend/app/api/v1/endpoints/fhir_validator.py`: Validates FHIR bundles and resources.
  - `backend/app/services/abdm_*.py`: Generates and parses ABDM health information artifacts.
- **Exported Interface:**
  - 32 standard Pydantic models conforming to HL7 FHIR R4 and NRCeS specifications.

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/fhir/schemas.py` provides strongly-typed Pydantic schemas for generating and consuming healthcare data exchanged over Indian and international health networks:
1. **Core Data Types (Lines 18-120)**: Establishes base FHIR constructs:
   - `FHIRIdentifier`: Encapsulates business/technical identifiers (such as ABHA numbers or hospital registration numbers) with `system`, `value`, and `use`.
   - `FHIRCoding` & `FHIRCodeableConcept`: Model codified clinical terms referencing standard vocabularies (SNOMED-CT, LOINC, ICD-10).
   - `FHIRReference`: References internal or external resources (`Patient/123`, `Practitioner/456`).
   - `FHIRPeriod`, `FHIRQuantity`, `FHIRAnnotation`: Standard temporal boundaries, numerical metrics with UCUM units, and clinical audit notes.
2. **Clinical Interaction Resources (Lines 123-338)**:
   - `FHIRAppointment`: Captures clinical consultation booking windows, statuses (`booked`, `fulfilled`, `cancelled`), reason codes, and multi-actor participation.
   - `FHIREncounter`: Documents the clinical interaction event, classified by act code (`AMB` for ambulatory in-person clinic, `VR` for virtual teleconsultation) with subject and practitioner bindings.
   - `FHIRCondition`: Captures problems and diagnoses, with required `clinicalStatus` and optional `verificationStatus` (aligned with HL7 R4 Condition state machine).
3. **Telemetry & Diagnostics (Lines 341-730)**:
   - `FHIRObservation`: Structures single and multi-component measurements (e.g. systolic/diastolic blood pressure panels, blood glucose, heart rates) with reference ranges and interpretation codes.
   - `FHIRServiceRequest`: Models diagnostic test requisitions.
   - `FHIRDiagnosticReport`: Represents finalized pathology/radiology interpretations linked to supporting observation references.
4. **Pharmaceuticals & Fulfillment (Lines 732-1085)**:
   - `FHIRMedication`, `FHIRMedicationRequest` (prescriptions), `FHIRMedicationDispense` (pharmacy fulfillment): Model dosage instructions, refills, substitution permissions, lot numbers, and expiration dates aligned with NRCeS India profiles.
5. **Envelopes & ABDM Artifacts (Lines 1087-1169)**:
   - `FHIRBundle`: Encloses multiple resources inside a `collection` or `document` bundle.
   - `ABDMConsentLinkage`: Pairs an ABDM CareContext reference (`APPT-XXXXXXXX`) with patient identifiers, consent artifact UUID, a SHA-256 integrity signature, and the FHIR bundle envelope.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Unsanitized XHTML Narrative Injection (Stored XSS Risk)
In `FHIRNarrative` (lines 520-531):
```python
class FHIRNarrative(BaseModel):
    status: str = Field(default="generated", ...)
    div: str = Field(description="Limited XHTML div content")
```
The `div` attribute accepts arbitrary strings without validating or sanitizing against an XHTML whitelist. When clinical text from notes, chief complaints, or user intake forms is rendered into `div`, an attacker can inject malicious HTML tags (`<script>`, `<iframe src="javascript:...">`, `<img onerror=alert(1)>`). When downstream clinician portals or third-party PHR apps render this narrative block as raw HTML, arbitrary JavaScript executes in the clinician's browser session, compromising patient records.

### Invariant 2: Pseudo-Cryptographic Digital Signature in ABDM Consent Linkage
In `ABDMConsentLinkage` (lines 1119-1153):
```python
signature: str = Field(
    description="Hex-encoded SHA-256 cryptographic digest of canonical FHIR bundle for tamper-evidence",
    example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
)
```
The field is labeled `signature` but stores a plain, unauthenticated SHA-256 hexadecimal digest. A digital signature under the Indian Information Technology Act 2000 and ABDM Milestone M3 requires an asymmetric signature (e.g. JWS or XML-DSig generated using the hospital's private key) that verifies both document integrity and author non-repudiation. Anyone can modify bundle contents and recalculate the SHA-256 digest with zero detection.

### Invariant 3: Missing Mutual Exclusion Constraint on Medication[x]
In `FHIRMedicationRequest` (lines 861-944) and `FHIRMedicationDispense` (lines 984-1085):
Both `medicationReference` and `medicationCodeableConcept` are marked as optional:
```python
medicationReference: Optional[FHIRReference] = Field(default=None, ...)
medicationCodeableConcept: Optional[FHIRCodeableConcept] = Field(default=None, ...)
```
According to the FHIR R4 specification, `MedicationRequest` and `MedicationDispense` mandate that exactly one of `medication[x]` must be provided. In this schema, a payload with neither field or with both fields is considered valid by Pydantic, violating FHIR R4 conformance and causing deserialization errors on external gateways.

### Invariant 4: Lack of Document Bundle Ordering Constraint
In `FHIRBundle` (lines 1087-1112), when `type="document"`, FHIR R4 Section 2.21 mandates that the first entry in `entry` must be a `Composition` resource. The schema has no root validator enforcing this requirement, permitting malformed document bundles to pass validation.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-FHR-SCH-F01` | **S1** | `[SEC]` | `app/fhir/schemas.py:520-531` | `FHIRNarrative.div` lacks XHTML sanitization, permitting Stored XSS when clinical narratives are rendered in client browsers. |
| `BE-FHR-SCH-F02` | **S1** | `[SEC]` | `app/fhir/schemas.py:1146-1149` | ABDM consent linkage `signature` is an unauthenticated SHA-256 hash rather than a legal asymmetric digital signature (JWS/XML-DSig). |
| `BE-FHR-SCH-F03` | **S2** | `[QUAL]` | `app/fhir/schemas.py:897-904` | `FHIRMedicationRequest` does not enforce the FHIR R4 `medication[x]` constraint (at least one of reference or codeable concept must be set). |
| `BE-FHR-SCH-F04` | **S2** | `[QUAL]` | `app/fhir/schemas.py:1022-1029` | `FHIRMedicationDispense` does not enforce the FHIR R4 `medication[x]` constraint. |
| `BE-FHR-SCH-F05` | **S2** | `[QUAL]` | `app/fhir/schemas.py:1087-1112` | `FHIRBundle` does not enforce that the first entry of a `document` bundle must be a `Composition` resource. |
| `BE-FHR-SCH-F06` | **S3** | `[QUAL]` | `app/fhir/schemas.py:72-89` | `FHIRReference.reference` lacks regex validation to ensure compliance with FHIR resource reference formats. |
| `BE-FHR-SCH-F07` | **S4** | `[DOC]` | `app/fhir/schemas.py:1-6` | Missing documentation regarding NRCeS India v2.0 StructureDefinition URL profiles for all resources. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-FHR-SCH-F03-F05`: Pydantic Model Validators for Medication[x] & Document Bundles
```diff
--- a/backend/app/fhir/schemas.py
+++ b/backend/app/fhir/schemas.py
@@ -10,6 +10,7 @@
 from datetime import datetime, timezone
 from typing import Any, Dict, List, Literal, Optional
-from pydantic import BaseModel, ConfigDict, Field
+from pydantic import BaseModel, ConfigDict, Field, model_validator
 
 
@@ -942,6 +943,12 @@
         default=None,
         description="Generic substitution permissions and rationale",
     )
+
+    @model_validator(mode="after")
+    def validate_medication_choice(self) -> "FHIRMedicationRequest":
+        if not self.medicationReference and not self.medicationCodeableConcept:
+            raise ValueError("FHIR R4 MedicationRequest requires either medicationReference or medicationCodeableConcept")
+        return self
 
 
@@ -1110,5 +1117,14 @@
         default_factory=list,
         description="Entry list containing resources",
     )
+
+    @model_validator(mode="after")
+    def validate_document_bundle(self) -> "FHIRBundle":
+        if self.type == "document":
+            if not self.entry:
+                raise ValueError("FHIR document bundle must contain at least one entry")
+            first_res = self.entry[0].resource
+            if isinstance(first_res, dict) and first_res.get("resourceType") != "Composition":
+                raise ValueError("First entry in a FHIR document bundle must be a Composition resource")
+        return self
```
