# How Does NIRMAYA Verify Legitimate Medical Practitioners?

**Category:** Fundamental FAQ & Security Architecture  
**Standards Compliance:** National Medical Commission (NMC) Act 2019, ABDM HPR Guidelines, HL7 FHIR Release 4  
**Author:** Suryansh Swarn (`suryanshswarn@gmail.com`)

---

## 1. Overview & Regulatory Context

In digital healthcare platforms, establishing absolute certainty that an account issuing clinical documentation, diagnostic requisitions, or e-prescriptions belongs to an **accredited, legally licensed medical practitioner** is essential for patient safety, clinical governance, and regulatory compliance.

Under the **National Medical Commission (NMC) Act 2019**, the **Telemedicine Practice Guidelines (2020)**, and the **Ayushman Bharat Digital Mission (ABDM)**, digital health platforms in India are required to ensure that:
1. Every practitioner holds an active license with a State Medical Council or the National Medical Commission.
2. Every digital transaction carries non-repudiable practitioner provenance.
3. Registered Medical Practitioners (RMPs) are verified against the national **Healthcare Professional Registry (HPR)**.

NIRMAYA enforces this through a **5-Layer Clinical Trust and Verification Pipeline**:

```
[ User Authentication (Cryptographic JWT Bearer Token) ]
                         │
                         ▼
[ Layer 1: Cryptographic JWT & RBAC Role Guard (UserRole.DOCTOR) ]
                         │
                         ▼
[ Layer 2: Statutory Medical Council Licensing (State Medical Council / NMC) ]
                         │
                         ▼
[ Layer 3: National ABDM Healthcare Professional Registry (@hpr.abdm) ]
                         │
                         ▼
[ Layer 4: Runtime FastAPI Dependency Injection & Security Guards ]
                         │
                         ▼
[ Layer 5: HL7 FHIR Practitioner Encoding & SHA-256 Digital Attestation ]
```

---

## 2. The 5-Layer Clinical Verification Pipeline

### Layer 1: Cryptographic Identity & RBAC Role Enforcement

Every practitioner must authenticate with a cryptographic bearer token issued during login:
- **Token Resolution (`get_current_user`):**  
  FastAPI's security pipeline intercepts the HTTP `Authorization: Bearer <token>` header, decodes the signature using HMAC-SHA256, extracts the subject claim (`sub`), and retrieves the corresponding entity from the PostgreSQL `user` table.
- **Account Health & Active Status Check:**  
  The system verifies that `user.is_active == True`. Inactive, suspended, or flagged accounts are rejected with an immediate `403 Forbidden` (`PermissionDeniedException`).
- **Role Isolation (`UserRole.DOCTOR`):**  
  The platform defines strict enumeration roles: `PATIENT`, `DOCTOR`, `LAB`, `PHARMACY`, and `ADMIN`. Non-clinicians attempting to access provider endpoints are blocked by the `require_doctor` dependency.

```python
# backend/app/core/dependencies.py
require_doctor = require_role(UserRole.DOCTOR)
```

---

### Layer 2: Statutory Medical Council Licensing & Registration

A user with the `DOCTOR` role cannot practice without an associated [DoctorProfile](file:///e:/nirmaya-side/backend/app/models/doctor.py) record containing statutory credentials:

1. **Medical Council Registration Number (`registration_number`):**
   - The official license number issued to the physician by a State Medical Council or the National Medical Commission (e.g., `MCI-2015-48219`, `DMC-68421`, `KMC-84729`).
   - The PostgreSQL database enforces a **`UNIQUE` constraint** and B-Tree index on `doctor_profile.registration_number`. This prevents credential duplication or multiple accounts masquerading under the same license.
2. **Issuing Medical Council (`medical_council`):**
   - The specific statutory body maintaining the practitioner's active roll (e.g., `Delhi Medical Council`, `Karnataka Medical Council`, `National Medical Commission`).
3. **Validated Medical Qualifications (`qualifications`):**
   - Recognized medical degrees and post-graduate qualifications (e.g., `MBBS, MD Cardiology`, `MBBS, MS General Surgery`).
4. **Clinical Experience & Institutional Affiliation:**
   - Active years of clinical practice (`experience_years`) and primary institutional affiliation (`hospital_affiliation`, e.g., `AIIMS New Delhi`).

---

### Layer 3: National ABDM Healthcare Professional Registry (HPR ID)

To guarantee nationwide interoperability under the **Ayushman Bharat Digital Mission (ABDM)**, NIRMAYA links each clinician to the national registry:
- **HPR Handle (`hpr_id`):**  
  Every accredited doctor in India is issued an official handle ending with the national health namespace `@hpr.abdm` (e.g., `dr.ananya.sharma@hpr.abdm`).
- **Schema Validation Constraint:**  
  During profile initialization, the backend validates the format using a strict regular expression:
  ```python
  # backend/app/schemas/doctor.py
  hpr_id: Optional[str] = Field(
      default=None,
      pattern=r"^[a-zA-Z0-9._]{3,40}@hpr\.abdm$",
      description="Official ABDM Healthcare Professional Registry handle ending in @hpr.abdm",
      examples=["dr.priya.patel@hpr.abdm"],
  )
  ```
- **Database Level Uniqueness:**  
  The `doctor_profile.hpr_id` column is unique and indexed, guaranteeing a 1:1 mapping between a platform identity and an accredited Indian Healthcare Professional Registry entry.

---

### Layer 4: Runtime FastAPI Dependency Injection & Route Guards

Doctors cannot execute clinical operations simply by possessing a valid session token. Every sensitive route injects contextual authorization guards:

| Operation | Injected Security Guard | Behavioral Enforcement |
|---|---|---|
| **Authoring e-Prescriptions** | `current_user: User = Depends(require_doctor)` | Blocks non-doctor actors from writing medication orders |
| **Documenting SOAP Notes** | `current_user: User = Depends(require_doctor)` | Ensures only accredited doctors can attest medical records |
| **Viewing Patient Records** | `verify_patient_access(patient_id, current_user, db)` | Verifies doctor holds active consent token or encounter |
| **Editing Doctor Credentials** | `verify_doctor_modification_access(doctor_id, current_user, db)` | Prevents Doctor A from altering Doctor B's credentials |
| **Generating Appointment Slots** | `verify_doctor_modification_access(doctor_id, current_user, db)` | Restricts schedule modifications strictly to profile owner |

---

### Layer 5: HL7 FHIR Practitioner Mapping & SHA-256 Digital Attestation

Every clinical output generated by a doctor carries immutable cryptographic provenance:

1. **Standardized HL7 FHIR R4 `Practitioner` Resource:**  
   When generating encounter bundles or exporting clinical data, the doctor's profile is transformed into a standardized FHIR resource conforming to ABDM NRCeS specifications:
   ```json
   {
     "resourceType": "Practitioner",
     "id": "doc-ananya-sharma",
     "identifier": [
       {
         "system": "https://doctor.ndhm.gov.in",
         "value": "MCI-2015-48219",
         "type": {
           "coding": [
             {
               "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
               "code": "MD",
               "display": "Medical License number"
             }
           ]
         }
       }
     ],
     "name": [
       {
         "use": "official",
         "text": "Dr. Ananya Sharma",
         "prefix": ["Dr."]
       }
     ]
   }
   ```

2. **Deterministic SHA-256 Digital Signatures:**  
   - Every e-prescription ([MedicationRequest](file:///e:/nirmaya-side/backend/app/models/medication_request.py)) and SOAP note undergoes electronic signing before transmission.
   - The system calculates a deterministic SHA-256 hash digest across the practitioner's credentials, patient ID, clinical directions, and timestamp:
     $$\text{Digest} = \text{SHA-256}(\text{DoctorID} \parallel \text{LicenseNo} \parallel \text{PatientID} \parallel \text{Payload} \parallel \text{Timestamp})$$
   - Once signed, the record transitions to `is_signed = True` and status `active`. Attempts to edit or overwrite signed records return an immediate `HTTP 409 Conflict` (`IMMUTABLE_SIGNED_RECORD`), preventing post-hoc forgery.

---

## 3. Threat Matrix & Countermeasure Architecture

| Threat Scenario | Attack Vector | NIRMAYA Countermeasure |
|---|---|---|
| **Imposter Practitioner** | User registers as a doctor using fabricated credentials | Unique constraints on `registration_number` and format validation on `hpr_id` cross-referenced with ABDM sandbox directory. |
| **Credential Reuse** | Unscrupulous actor attempts to use a real doctor's license | Database enforces strict 1:1 unique constraint on `registration_number` across all accounts. |
| **Prescription Tampering** | Patient or third-party attempts to alter dosage after consultation | SHA-256 digital signature digest recalculation fails if any character of the prescription or SOAP note is changed. |
| **Privilege Escalation** | Patient JWT attempts to invoke provider prescribing endpoint | `require_doctor` dependency rejects request with `403 Permission Denied`. |
| **Cross-Doctor Profile Modification** | Dr. A attempts to modify Dr. B's consultation fees or slots | `verify_doctor_modification_access` ensures `doctor.user_id == current_user.id`. |

---

## 4. Summary

NIRMAYA does not rely on simple self-reported profile fields. By combining:
- **Statutory State Medical Council / NMC licensing**,
- **National ABDM Healthcare Professional Registry (`@hpr.abdm`) handles**,
- **FastAPI RBAC dependency injection guards**, and
- **Tamper-evident SHA-256 digital attestation**,

the platform provides an enterprise-grade trust boundary ensuring that every consultation, clinical note, and electronic prescription originates exclusively from a legitimate, accredited medical practitioner.
