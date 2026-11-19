# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/express_consultation.py`
**Audited Path:** `backend/app/schemas/express_consultation.py`  
**Module:** `backend` | **Subsystem:** Express 45-Second Doctor Consultation Engine  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/express_consultation.py` defines the Pydantic v2 schemas for NIRMAYA's high-velocity 45-second express consultation mode (`/doctor`). Designed to eliminate clinician documentation burnout in high-density Indian Outpatient Departments (OPD), this module structures:
- Patient drug allergy and contraindication safety banners (`PatientAllergyProfile`, `PatientAllergyItem`).
- 1-click curated chief complaint chips mapped directly to ICD-10 and SNOMED CT concepts (`ChiefComplaintTemplate`).
- Pre-configured, high-frequency medication bundles and intake schedules (`QuickPrescriptionItem`, `PrescriptionBundleTemplate`).
- Atomic sub-50ms OPD encounter submission and synchronous queue advancement payloads (`ExpressEncounterSubmitRequest`, `ExpressEncounterSubmitResponse`).

#### 2. Key Components & Class Roster
- `PatientAllergyItem`: Specific drug/food allergy with substance name, clinical reaction, severity tier (`mild`, `moderate`, `severe`, `life-threatening`), and verification status.
- `PatientAllergyProfile`: Prominently displayed safety profile aggregating active drug allergies, clinical contraindications, and high-contrast safety banner text (e.g. `NO KNOWN DRUG ALLERGIES (NKDA)`).
- `ChiefComplaintTemplate`: 1-tap chief complaint chip containing mnemonic codes, dual ICD-10 (`J06.9`) and SNOMED CT (`105590001`) ontology anchors, recommended prescription bundle IDs, and standardized patient advice.
- `QuickPrescriptionItem`: Granular medication course item detailing formulation, dosage strength, meal timing (`morning`, `afternoon`, `night`), plain frequency badges (e.g. `1-0-1`), course duration, and substance cross-allergy check tags.
- `PrescriptionBundleTemplate`: Comprehensive 1-click clinical regimen (e.g. Viral Fever & Upper Respiratory Tract Infection bundle) bundling multiple medications, lifestyle advice, and follow-up intervals.
- `ExpressEncounterSubmitRequest`: Atomic encounter finalization payload dispatched by attending physicians containing doctor HPR credentials, chief complaints, diagnostic codes, prescribed medications, and emergency escalation toggles.
- `ExpressEncounterSubmitResponse`: Rapid acknowledgment schema returning generated FHIR R4 Encounter UUID, SHA-256 digital signature seal, HPR signing timestamp, latency metrics, and next OPD queue token call.

---

### Layer B: Plain-Language Developer Walkthrough

In a government medical college hospital or district hospital in India, an OPD physician may see between 80 and 150 patients in a single morning. If an Electronic Medical Record (EMR) system requires 5 minutes of clicking and dropdown selections per patient, clinicians simply abandon the software and return to paper pads.

`express_consultation.py` provides the data contracts for an ultra-fast "express lane" consultation console. When a patient sits down:
1. The physician immediately sees their `PatientAllergyProfile` in a bold banner across the top of the screen (e.g., warning if the patient has a life-threatening penicillin allergy).
2. The doctor taps a pre-configured complaint chip (`ChiefComplaintTemplate`), such as "Viral Fever". This automatically populates the ICD-10 code (`J06.9`), SNOMED CT code (`105590001`), and standardized hydration/rest instructions.
3. The doctor can click an associated `PrescriptionBundleTemplate`, which selects standard medications like Paracetamol 650mg with plain schedule badges (`1-0-1`).
4. Upon clicking "Submit", `ExpressEncounterSubmitRequest` executes an atomic database commit in under 50 milliseconds. The system signs the clinical encounter cryptographically, advances the OPD queue, prints the next patient token, and returns `ExpressEncounterSubmitResponse` with a one-click PDF download link for the patient.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **High-Velocity Serialization:** Utilizes Pydantic v2 `ConfigDict(from_attributes=True)` across all models for rapid serialization directly from ORM instances.
- **Ontology Dual-Coding:** Every complaint template and encounter binds both ICD-10 classification codes and international SNOMED CT concept identifiers, complying with ABDM Milestone 2 and 3 guidelines.
- **Queue Pipeline Integration:** `ExpressEncounterSubmitResponse` bundles `next_token_called`, `next_patient_name`, and `queue_remaining_count`, enabling zero-latency turn-key patient flow management.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Hardcoded Fallback Production Credentials and Facility IDs (`BE-SCH-EXP-F01`)
- **Severity:** S1 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/express_consultation.py:100-101`
- **Description:** `ExpressEncounterSubmitRequest` assigns hardcoded defaults: `doctor_hpr: str = Field(default="ananya.sharma@hpr.abdm")` and `facility_id: str = Field(default="aiims-delhi-01")`. If a client API call from an external clinic, rural PHC, or another doctor's workstation omits these fields due to an integration defect, the backend silently accepts the encounter and attributes medical diagnoses and digital signatures to a real demo practitioner (`ananya.sharma@hpr.abdm`) at AIIMS Delhi!
- **Impact:** Fraudulent attribution of medical consultations, corrupted audit trails, and serious medico-legal liability under ABDM HPR compliance rules.
- **Remediation:** Remove hardcoded defaults; require `doctor_hpr` and `facility_id` as mandatory non-null fields (`...`).

##### Vulnerability 2: Unmasked Patient Names in Logging Repr (`BE-SCH-EXP-F02`)
- **Severity:** S2 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/express_consultation.py:29, 123, 133`
- **Description:** `PatientAllergyProfile.patient_name`, `ExpressEncounterSubmitResponse.patient_name`, and `next_patient_name` are plain string fields without `repr=False`. When an encounter is logged or traced in APM/ELK stacks, identifiable patient names are written to plaintext disk logs.
- **Impact:** Leaks protected health information (PHI) in log aggregators (CWE-532).
- **Remediation:** Add `repr=False` to all patient demographic name fields.

##### Vulnerability 3: Defaulting Missing Diagnoses to Viral Fever ICD-10 Code (`BE-SCH-EXP-F03`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/express_consultation.py:108`
- **Description:** `ExpressEncounterSubmitRequest.icd10_code` defaults to `"J06.9"` (Acute upper respiratory infection). If a doctor performs an express consultation for an acute abdominal condition or fracture and forgets to select a diagnosis code, the encounter is permanently stored in the ABDM longitudinal record as a viral respiratory infection.
- **Impact:** Clinical record corruption and inaccurate diagnostic epidemiology.
- **Remediation:** Remove the `"J06.9"` default; declare `icd10_code: Optional[str] = None` or require explicit selection.

##### Vulnerability 4: Unvalidated Digital Signature Hash (`BE-SCH-EXP-F04`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/express_consultation.py:125`
- **Description:** `digital_signature_hash` is an unconstrained string without length constraints or 64-character hexadecimal regex validation.
- **Impact:** Corrupted or truncated cryptographic signature digests pass schema validation.
- **Remediation:** Add `pattern=r"^[a-fA-F0-9]{64}$"` and `min_length=64, max_length=64`.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-EXP-F01` | S1 | `[SEC]` | `express_consultation.py:100-101` | Hardcoded defaults for `doctor_hpr` and `facility_id` risk misattributed clinical encounters |
| `BE-SCH-EXP-F02` | S2 | `[SEC]` | `express_consultation.py:29, 123, 133` | Unmasked patient demographic names in string `repr` expose PHI in logs |
| `BE-SCH-EXP-F03` | S2 | `[QUAL]` | `express_consultation.py:108` | `icd10_code` defaults to `"J06.9"`, risking silent clinical misclassification |
| `BE-SCH-EXP-F04` | S3 | `[QUAL]` | `express_consultation.py:125` | `digital_signature_hash` lacks 64-character hex regex validation |
| `BE-SCH-EXP-F05` | S3 | `[QUAL]` | `express_consultation.py:135` | `signed_prescription_download_url` declared as plain string instead of `HttpUrl` |
| `BE-SCH-EXP-F06` | S4 | `[NOTE]` | `express_consultation.py:72` | `QuickPrescriptionItem.duration_days` lacks upper limit validation (`le=365`) |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/express_consultation.py
+++ b/backend/app/schemas/express_consultation.py
@@ -11,7 +11,7 @@ from datetime import datetime, timezone
 from typing import Any, Dict, List, Optional
-from pydantic import BaseModel, ConfigDict, Field
+from pydantic import BaseModel, ConfigDict, Field, HttpUrl
 
 
 class PatientAllergyItem(BaseModel):
@@ -28,7 +28,7 @@ class PatientAllergyProfile(BaseModel):
     patient_id: str = Field(description="Patient Profile UUID")
-    patient_name: str = Field(description="Patient full name", example="Arun Kumar Patel")
+    patient_name: str = Field(repr=False, description="Patient full name", example="Arun Kumar Patel")
     has_known_allergies: bool = Field(default=False, description="Whether patient has active drug allergies")
 
@@ -99,14 +99,14 @@ class ExpressEncounterSubmitRequest(BaseModel):
     doctor_id: str = Field(description="Attending Doctor UUID", example="doc-ananya-sharma")
-    doctor_hpr: str = Field(default="ananya.sharma@hpr.abdm", description="Certified ABDM HPR identifier")
-    facility_id: str = Field(default="aiims-delhi-01", description="Hospital / OPD Clinic identifier")
+    doctor_hpr: str = Field(..., description="Certified ABDM HPR identifier")
+    facility_id: str = Field(..., description="Hospital / OPD Clinic identifier")
     token_number: Optional[str] = Field(default=None, description="Queue token currently being consulted")
     chief_complaints: List[str] = Field(description="Selected complaint tags or text", example=["Viral Fever", "Cough"])
     clinical_diagnosis: str = Field(
         description="Final clinical diagnosis (plain or ICD-10)",
         example="Acute upper respiratory infection [J06.9]",
     )
-    icd10_code: Optional[str] = Field(default="J06.9", description="ICD-10 clinical diagnostic code")
+    icd10_code: Optional[str] = Field(default=None, description="ICD-10 clinical diagnostic code")
 
@@ -122,8 +122,14 @@ class ExpressEncounterSubmitResponse(BaseModel):
     patient_id: str = Field(description="Patient Profile UUID")
-    patient_name: str = Field(description="Patient certified full name")
+    patient_name: str = Field(repr=False, description="Patient certified full name")
     status: str = Field(default="COMPLETED", description="Encounter status")
-    digital_signature_hash: str = Field(description="SHA-256 cryptographic seal of clinical encounter")
+    digital_signature_hash: str = Field(
+        ...,
+        pattern=r"^[a-fA-F0-9]{64}$",
+        min_length=64,
+        max_length=64,
+        description="SHA-256 cryptographic seal of clinical encounter",
+    )
     hpr_sign_seal: str = Field(description="Doctor's certified HPR digital signing seal")
@@ -132,6 +138,6 @@ class ExpressEncounterSubmitResponse(BaseModel):
     next_token_called: Optional[str] = Field(default=None, description="Sequential token of next patient called")
-    next_patient_name: Optional[str] = Field(default=None, description="Name of next patient in queue")
+    next_patient_name: Optional[str] = Field(default=None, repr=False, description="Name of next patient in queue")
     queue_remaining_count: int = Field(default=0, description="Remaining patients in OPD room queue")
-    signed_prescription_download_url: str = Field(description="1-Click download URL for signed prescription PDF")
+    signed_prescription_download_url: HttpUrl = Field(description="1-Click download URL for signed prescription PDF")
```
