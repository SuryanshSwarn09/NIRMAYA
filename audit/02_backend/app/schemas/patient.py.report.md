# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/patient.py`
**Audited Path:** `backend/app/schemas/patient.py`  
**Module:** `backend` | **Subsystem:** Patient Demographics, Clinical Profile & ABDM ABHA Identification  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/patient.py` defines the Pydantic v2 schemas for patient clinical profiles, geographic demographic records, emergency contact designations, and official Ayushman Bharat Digital Mission (ABDM) national health identifiers in NIRMAYA. Operating as the primary identity anchor for all electronic medical records, this module structures:
- Patient clinical attributes, date of birth, FHIR-aligned administrative gender, and ABO/Rh blood groups (`PatientProfileBase`).
- Indian geographic residential addresses, cities, states, and 6-digit postal PIN codes.
- Emergency next-of-kin contact details (name, phone, relationship).
- ABDM national health identifiers: 14-digit ABHA Numbers (`XX-XXXX-XXXX-XXXX`) and reserved `@abdm` PHR handles.
- Patient onboarding payloads (`PatientProfileCreate`), profile modification schemas (`PatientProfileUpdate`), and rich API responses with linked user account summaries (`PatientProfileResponse`).

#### 2. Key Components & Class Roster
- `PatientProfileBase`: Base attributes covering date of birth (`date_of_birth`), gender (`Gender.UNKNOWN`), blood group (`BloodGroup.UNKNOWN`), residential street address, city, state, postal PIN code (`pincode`), emergency contact information (name, phone, relationship), 14-digit ABHA number, and ABHA address handle.
- `PatientProfileCreate`: Initialization schema linking an optional `user_id` to bind the clinical profile to a platform user.
- `PatientProfileUpdate`: Optional-field patch schema for updating demographics and contact details.
- `PatientProfileResponse`: Primary domain output model returning persistent UUID, user UUID, creation/modification timestamps, and embedded `UserResponse` summary.

---

### Layer B: Plain-Language Developer Walkthrough

In any healthcare platform, the patient's demographic profile is the foundation upon which all other medical records (prescriptions, lab tests, doctor encounters) rest. Under India's national ABDM architecture, every citizen can possess an ABHA Number (a unique 14-digit national health identifier formatted like `12-3456-7890-1234`) and an ABHA address handle (like `rahul.sharma@abdm`) that acts like a personal medical email address for receiving health records.

`patient.py` provides the canonical blueprints for these patient profiles:
1. When a patient registers, they provide their date of birth, gender, blood type, and residential address.
2. The schema validates national data standards: for example, the `pincode` must match a valid 6-digit Indian Postal PIN code without leading zeros, the `abha_number` must match the official national hyphenated pattern, and the `abha_address` must end with `@abdm`.
3. It stores critical safety information, such as designated next-of-kin emergency contacts, so hospital emergency departments can reach family members during acute medical crises.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **National Identifier Patterns:** Enforces strict regex validation on ABHA numbers (`r"^\d{2}-\d{4}-\d{4}-\d{4}$"`) and ABHA handles (`r"^[a-zA-Z0-9._]{3,30}@abdm$"`).
- **Postal PIN Code Guard:** Restricts `pincode` to valid Indian postal codes starting with digits 1-9 (`r"^[1-9][0-9]{5}$"`).
- **ORM Attribute Extraction:** Employs `ConfigDict(from_attributes=True)` on `PatientProfileResponse` for clean serialization from SQLAlchemy `PatientProfile` models.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Patient ABHA and Emergency Phone Number Exposed in String Repr (`BE-SCH-PAT-F01`)
- **Severity:** S2 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/patient.py:58-62, 70-75`
- **Description:** In `PatientProfileBase`, fields `emergency_contact_phone` and `abha_number` are declared as plain strings without `repr=False`. When patient profiles are serialized in server logs, exception handlers, or APM traces, citizen national ABHA numbers and next-of-kin personal contact phone numbers are dumped in plaintext into disk logs.
- **Impact:** Violation of patient confidentiality regulations and risk of identity harvesting (CWE-532).
- **Remediation:** Annotate `emergency_contact_phone` and `abha_number` with `repr=False`.

##### Vulnerability 2: Schema-to-ORM Nullability Mismatch on user_id (`BE-SCH-PAT-F02`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/patient.py:87-90`
- **Description:** In `PatientProfileCreate`, `user_id` is declared as `Optional[str] = Field(default=None)`. However, the corresponding database model `PatientProfile.user_id` (`backend/app/models/patient.py:38`) is defined as a non-nullable unique foreign key: `ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True`. If an endpoint handler attempts to create a profile without providing `user_id` (or if caller session extraction fails), the database insert crashes with an unhandled `IntegrityError`.
- **Impact:** Potential runtime crash and 500 errors on patient registration endpoints (CWE-754).
- **Remediation:** Make `user_id` mandatory in `PatientProfileCreate` or document strict injection from the authenticated session.

##### Vulnerability 3: Missing Validation on Future Date of Birth (`BE-SCH-PAT-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/patient.py:13-17`
- **Description:** `date_of_birth: Optional[date]` has no model validator ensuring that `date_of_birth <= date.today()`. A client could submit a future birth date (e.g. 2035-01-01), creating an impossible demographic record that distorts pediatric age calculations.
- **Impact:** Erroneous clinical age and dosage calculation metrics.
- **Remediation:** Add a field validator verifying `date_of_birth <= date.today()`.

##### Vulnerability 4: Missing ConfigDict on PatientProfileUpdate (`BE-SCH-PAT-F04`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/patient.py:93`
- **Description:** `PatientProfileUpdate` omits `model_config = ConfigDict(from_attributes=True)`.
- **Impact:** Inconsistent configuration across schemas.
- **Remediation:** Add `model_config = ConfigDict(from_attributes=True)`.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-PAT-F01` | S2 | `[SEC]` | `patient.py:58-62, 70-75` | Patient ABHA number and emergency phone unmasked in string `repr` |
| `BE-SCH-PAT-F02` | S2 | `[QUAL]` | `patient.py:87-90` | `user_id` optional in create schema despite NOT NULL constraint in ORM |
| `BE-SCH-PAT-F03` | S3 | `[QUAL]` | `patient.py:13-17` | `date_of_birth` lacks validator ensuring date is not in the future |
| `BE-SCH-PAT-F04` | S3 | `[QUAL]` | `patient.py:93` | `PatientProfileUpdate` lacks `ConfigDict(from_attributes=True)` |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/patient.py
+++ b/backend/app/schemas/patient.py
@@ -3,4 +3,4 @@
 from datetime import date, datetime
 from typing import Optional
-from pydantic import BaseModel, ConfigDict, Field
+from pydantic import BaseModel, ConfigDict, Field, field_validator
 from app.models.enums import BloodGroup, Gender
@@ -17,2 +17,9 @@ class PatientProfileBase(BaseModel):
     )
+
+    @field_validator("date_of_birth")
+    @classmethod
+    def validate_dob_not_future(cls, v: Optional[date]) -> Optional[date]:
+        if v and v > date.today():
+            raise ValueError("date_of_birth cannot be in the future")
+        return v
     gender: Gender = Field(
@@ -58,3 +65,4 @@ class PatientProfileBase(BaseModel):
     emergency_contact_phone: Optional[str] = Field(
         default=None,
+        repr=False,
         pattern=r"^\+?[0-9\s\-()]{7,20}$",
@@ -70,3 +78,4 @@ class PatientProfileBase(BaseModel):
     abha_number: Optional[str] = Field(
         default=None,
+        repr=False,
         pattern=r"^\d{2}-\d{4}-\d{4}-\d{4}$",
@@ -93,2 +102,4 @@ class PatientProfileUpdate(BaseModel):
     """Payload for updating existing patient clinical and contact details."""
+    model_config = ConfigDict(from_attributes=True)
+
     date_of_birth: Optional[date] = None
```
