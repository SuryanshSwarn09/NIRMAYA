# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/emergency_vault.py`
**Audited Path:** `backend/app/schemas/emergency_vault.py`  
**Module:** `backend` | **Subsystem:** Break-The-Glass (BTG) Emergency Health Profile Vault  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/emergency_vault.py` provides the data contracts for NIRMAYA's Break-The-Glass (BTG) emergency health profile vault. In life-threatening clinical circumstances (e.g., massive trauma, acute unconsciousness, respiratory failure), attending physicians must bypass routine multi-step patient consent workflows to immediately review critical allergies, active medications (such as anticoagulants), blood group, and advance directives. This schema defines:
- The cleartext emergency profile structure (`EmergencyProfileData`) containing life-saving clinical indicators.
- The Zero-Knowledge encrypted vault envelope (`EncryptedVaultEnvelope`) utilizing Argon2id key derivation and AES-256-GCM symmetric authenticated encryption.
- Legally grounded clinical override requests (`BTGOverrideRequest`) and responses (`BTGOverrideResponse`).
- Immutable, tamper-evident forensic audit log records (`BTGAuditLogEntry`) backed by SHA-256 cryptographic fingerprints.
- Facility-wide compliance and usage telemetry (`BTGStatsResponse`, `EmergencyVaultStatusResponse`).

#### 2. Key Components & Class Roster
- `EmergencyBloodGroup`: Enumeration of ABO and Rh factor phenotypes (`O+`, `O-`, `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `UNKNOWN`).
- `EmergencyAllergyItem`: Allergen substance, criticality tier (`high`, `life_threatening`), and physiological manifestations (e.g. anaphylaxis).
- `EmergencyMedicationItem`: Critical ongoing pharmacotherapy, dosage, class, and high-risk acute intervention flags (e.g. warfarin/heparin warnings).
- `EmergencyConditionItem`: Critical comorbidities, pacemakers, and implants, optionally keyed with ICD-10 codes.
- `EmergencyContactItem`: Designated next-of-kin legal contact person, relationship, and emergency phone number.
- `EmergencyProfileData`: Core clinical payload aggregating allergies, medications, conditions, contacts, organ donor status, and advance directives (living wills / DNR).
- `EncryptedVaultEnvelope`: Zero-knowledge storage record containing base64 AES-256-GCM ciphertext, CSPRNG nonce, Argon2id salt, and SHA-256 integrity digest.
- `EmergencyJustificationCategory`: Medico-legal categories justifying consent override (`UNCONSCIOUS_TRAUMA`, `RESPIRATORY_ARREST`, `MASSIVE_HEMORRHAGE`, `ALTERED_MENTAL_STATUS`, `ANAPHYLAXIS_EMERGENCY`, `CARDIAC_ARREST_RESUSCITATION`, `OTHER_LIFE_THREATENING`).
- `BTGOverrideRequest`: Attending clinician request specifying doctor ID, HPR address, trauma unit, justification category, and a mandatory narrative (min 15 characters).
- `BTGAuditLogEntry`: Immutable forensic audit record linking the clinician, facility, justification, timestamp, originating IP address, and SHA-256 audit fingerprint.
- `BTGOverrideResponse`: Decrypted profile payload delivered to the resuscitation room under strict regulatory disclaimer warnings.
- `EmergencyVaultStatusResponse` & `BTGStatsResponse`: Operational and administrative monitoring schemas.

---

### Layer B: Plain-Language Developer Walkthrough

When an unconscious patient arrives at an emergency department or trauma bay, doctors cannot wait for the patient to unlock their phone, receive an OTP, or provide consent to share their medical records. Every second counts: administering penicillin to someone with a severe anaphylactic allergy or performing emergency surgery without knowing the patient is on blood thinners can be lethal.

`emergency_vault.py` sets up a special "Break-The-Glass" system. During normal times, a patient's emergency data is sealed inside an `EncryptedVaultEnvelope`. When a true emergency strikes, a certified physician can trigger a `BTGOverrideRequest`. The doctor must state their identity, their Healthcare Professional Registry (HPR) credentials, and the exact clinical reason (such as "UNCONSCIOUS_TRAUMA" with a documented Glasgow Coma Scale score).

The system then delivers the decrypted profile (`BTGOverrideResponse`) directly to the trauma team so they immediately know the patient's blood type, allergies, and implants. Crucially, the system instantly logs a permanent, tamper-evident record (`BTGAuditLogEntry`) containing the doctor's name, timestamp, justification, and terminal IP address. This audit record is cryptographically sealed, guaranteeing that any unauthorized or fraudulent "break-the-glass" access can be detected during hospital compliance audits.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **Cryptographic Specifications:** Explicit metadata fields (`kdfAlgorithm="Argon2id"`, `cipherAlgorithm="AES-256-GCM"`) enforce authenticated encryption with associated data (AEAD) where `patientAbha` acts as Additional Authenticated Data.
- **Narrative Justification Guard:** `clinicalJustification` enforces `min_length=15` preventing empty or single-character token entries during clinical overrides.
- **Forensic Hash Integrity:** `auditFingerprint` in `BTGAuditLogEntry` binds the clinician identity, facility, and event into an immutable SHA-256 hash.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Unmasked Next-of-Kin Phone Numbers and Advance Directives in Repr (`BE-SCH-EMV-F01`)
- **Severity:** S2 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/emergency_vault.py:69, 78, 88`
- **Description:** `EmergencyContactItem.phone`, `EmergencyProfileData.patientAbha`, and `EmergencyProfileData.advanceDirectives` are typed as regular `str` fields without `repr=False`. When an emergency profile is logged during trauma review, server debugging, or audit serializations, next-of-kin private mobile numbers, patient ABHA identifiers, and sensitive living wills (e.g., Do Not Resuscitate / DNR orders) are written in plaintext to server logs and trace aggregators.
- **Impact:** Violates patient privacy regulations and leaks personal contact data (CWE-532).
- **Remediation:** Annotate `phone`, `patientAbha`, and `advanceDirectives` with `repr=False` in their `Field` declarations.

##### Vulnerability 2: Unvalidated IP Address in Forensic Audit Trail (`BE-SCH-EMV-F02`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/emergency_vault.py:178`
- **Description:** `BTGAuditLogEntry.ipAddress` is declared as `Optional[str]` without format validation. An attacker or faulty client could inject arbitrary text, oversized payloads, or newline characters (log injection/crlf) into the forensic audit schema.
- **Impact:** Jeopardizes the forensic reliability of legal audit trails used in Break-The-Glass investigations.
- **Remediation:** Enforce `ipAddress: Optional[IPvAnyAddress]` or apply strict IPv4/IPv6 regex validation.

##### Vulnerability 3: Inconsistent Datetime String Serializations (`BE-SCH-EMV-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/emergency_vault.py:89-92, 111-118, 173-176`
- **Description:** Multiple models (`EmergencyProfileData`, `EncryptedVaultEnvelope`, `BTGAuditLogEntry`) use `str` fields initialized via `default_factory=lambda: datetime.now(timezone.utc).isoformat()` instead of native `datetime` fields. This bypasses Pydantic's built-in datetime parsing, timezone normalization, and OpenAPI schema typing (`type: string, format: date-time`).
- **Impact:** Inconsistent timestamp formatting across client SDKs and lost type validation.
- **Remediation:** Standardize timestamp fields to native `datetime` typed with `default_factory=lambda: datetime.now(timezone.utc)`.

##### Vulnerability 4: Missing Base64 Encoding Validation on Cryptographic Artifacts (`BE-SCH-EMV-F04`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/emergency_vault.py:105-107`
- **Description:** `ciphertextB64`, `nonceB64`, and `saltB64` in `EncryptedVaultEnvelope` are unvalidated strings. If an unencoded binary string or corrupt payload is posted to the vault endpoint, it passes schema validation and only fails later in decryption routines.
- **Impact:** Latent cryptographic exceptions in backend decryption services.
- **Remediation:** Add regex pattern constraints or Pydantic field validators ensuring valid standard base64 encoding.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-EMV-F01` | S2 | `[SEC]` | `emergency_vault.py:69, 78, 88` | Unmasked next-of-kin phone numbers and advance directives in string `repr` |
| `BE-SCH-EMV-F02` | S2 | `[QUAL]` | `emergency_vault.py:178` | `BTGAuditLogEntry.ipAddress` uses unvalidated string instead of strict IP type |
| `BE-SCH-EMV-F03` | S3 | `[QUAL]` | `emergency_vault.py:89-92, 111-118, 173-176` | Timestamps declared as ISO strings instead of native timezone-aware `datetime` |
| `BE-SCH-EMV-F04` | S3 | `[QUAL]` | `emergency_vault.py:105-107` | Base64 cryptographic artifacts lack encoding and length format constraints |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/emergency_vault.py
+++ b/backend/app/schemas/emergency_vault.py
@@ -10,7 +10,7 @@ from datetime import datetime, timezone
 from enum import Enum
 from typing import Dict, List, Optional
 import uuid
-from pydantic import BaseModel, ConfigDict, Field
+from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress
 
 
 class EmergencyBloodGroup(str, Enum):
@@ -66,7 +66,7 @@ class EmergencyContactItem(BaseModel):
     name: str = Field(description="Full legal name of contact person")
     relationship: str = Field(description="Relationship to patient (e.g. Spouse, Parent, Sibling)")
-    phone: str = Field(description="Emergency contact phone number with country code")
+    phone: str = Field(repr=False, description="Emergency contact phone number with country code")
     isPrimary: bool = Field(default=True, description="Whether this is the primary emergency contact")
 
     model_config = ConfigDict(from_attributes=True)
@@ -75,7 +75,7 @@ class EmergencyContactItem(BaseModel):
 class EmergencyProfileData(BaseModel):
     """Cleartext emergency health profile extracted or to be encrypted."""
 
-    patientAbha: str = Field(description="14-digit national ABHA identifier")
+    patientAbha: str = Field(repr=False, description="14-digit national ABHA identifier")
     patientName: str = Field(description="Patient full display name")
     dateOfBirth: str = Field(description="ISO 8601 date of birth (YYYY-MM-DD)")
     gender: str = Field(description="Legal administrative sex")
@@ -85,11 +85,11 @@ class EmergencyProfileData(BaseModel):
     medications: List[EmergencyMedicationItem] = Field(default_factory=list, description="Active high-risk medications")
     conditions: List[EmergencyConditionItem] = Field(default_factory=list, description="Comorbidities and surgical implants")
     emergencyContacts: List[EmergencyContactItem] = Field(default_factory=list, description="Primary emergency contacts")
     organDonorStatus: bool = Field(default=True, description="Whether patient is a registered organ donor")
-    advanceDirectives: Optional[str] = Field(default=None, description="Living will or resuscitation directives (e.g. FULL_CODE, DNR)")
-    updatedAt: str = Field(
-        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
-        description="ISO 8601 UTC timestamp of last profile update",
+    advanceDirectives: Optional[str] = Field(default=None, repr=False, description="Living will or resuscitation directives (e.g. FULL_CODE, DNR)")
+    updatedAt: datetime = Field(
+        default_factory=lambda: datetime.now(timezone.utc),
+        description="UTC timestamp of last profile update",
     )
 
     model_config = ConfigDict(from_attributes=True)
@@ -175,7 +175,7 @@ class BTGAuditLogEntry(BaseModel):
     auditFingerprint: str = Field(description="SHA-256 tamper-evident cryptographic fingerprint of the event")
-    ipAddress: Optional[str] = Field(default=None, description="Originating client IP address or terminal")
+    ipAddress: Optional[IPvAnyAddress] = Field(default=None, description="Originating client IP address or terminal")
 
     model_config = ConfigDict(from_attributes=True)
```
