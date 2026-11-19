# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/family_proxy.py`
**Audited Path:** `backend/app/schemas/family_proxy.py`  
**Module:** `backend` | **Subsystem:** Family Proxy & Dependent Health Access Control  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/family_proxy.py` defines the Pydantic schemas governing family health proxy relationships and dependent health records access in NIRMAYA. Aligned with India's Digital Personal Data Protection (DPDP) Act 2023 (Section 9 — Processing of personal data of children and persons with disabilities), this module manages:
- Familial and legal dependency relationships (`CHILD_MINOR`, `PARENT_SENIOR`, `SPOUSE`, `LEGAL_WARD`, `SIBLING`).
- Multi-tier verification authority mechanisms (`DIGILOCKER_BIRTH_CERTIFICATE`, `AADHAAR_DEMOGRAPHIC_EKYC`, `LEGAL_GUARDIANSHIP_ORDER`, `SELF_ATTESTED_EMERGENCY`).
- Granular, time-bounded proxy permission scopes (`FULL_MANAGEMENT`, `APPOINTMENTS_ONLY`, `RECORDS_VIEW_ONLY`, `EMERGENCY_RESTRICTED`).
- Verifiable guardian consent attestations, zero-contamination boundary certifications, and access audit records (`ProxyAuditLogItem`).

#### 2. Key Components & Class Roster
- `RelationshipTypeEnum`: Enumerates dependent and familial relationship categories.
- `VerificationAuthorityEnum`: Formal verification mechanisms used to validate legal guardianship.
- `ProxyAccessScopeEnum`: Granular permission tiers granted to proxy actors.
- `ProxyRelationshipStatusEnum`: Lifecycle states (`ACTIVE`, `PENDING_VERIFICATION`, `REVOKED`, `EXPIRED_AGE_OF_MAJORITY`).
- `FamilyProxyCreateRequest`: Inbound payload establishing a proxy relationship, specifying guardian/dependent IDs, relationship type, DigiLocker verification document hash, and DPDP Act Sec 9 consent attestation.
- `FamilyProxyResponse`: Representation of an authorized proxy link tracking validity timestamps (`authorized_until`), dependent age, and zero-contamination isolation certificates.
- `ProxyAuditLogItem`: Forensic audit record generated whenever a guardian accesses dependent records.

---

### Layer B: Plain-Language Developer Walkthrough

Children, elderly parents, and incapacitated wards often cannot operate smartphones or manage their own electronic health records. Under Indian law (DPDP Act 2023), processing medical data of minors requires verifiable parental or lawful guardian consent. Furthermore, when a child turns 18 (age of majority), parental proxy access must automatically terminate so the young adult gains full privacy over their medical history.

`family_proxy.py` provides the formal blueprints for establishing and regulating these proxy links:
1. When a parent registers a minor child, they submit a `FamilyProxyCreateRequest`. This includes the child's profile ID, the verification mechanism (e.g. pulling a birth certificate from DigiLocker), and a legal consent attestation checkbox.
2. The system stores the proxy link (`FamilyProxyResponse`) and records the child's date of birth so the proxy can automatically transition to `EXPIRED_AGE_OF_MAJORITY` when the minor reaches adulthood.
3. Every time a guardian views the dependent's records or books an appointment on their behalf, a `ProxyAuditLogItem` is logged, ensuring complete forensic accountability while maintaining strict zero-contamination data boundaries.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **DPDP Act Compliance:** `guardian_consent_attestation` enforces mandatory parental consent pursuant to Section 9 of the DPDP Act 2023.
- **Age-of-Majority Awareness:** `dependent_dob_iso` and `EXPIRED_AGE_OF_MAJORITY` status provide the foundation for automatic sunsetting of parental proxy access upon the dependent turning 18.
- **Isolation Guarantees:** `zero_contamination_isolated` ensures dependent clinical records remain strictly partitionable from the guardian's personal health locker.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Missing Self-Delegation Guard Validator (`BE-SCH-FPX-F01`)
- **Severity:** S1 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/family_proxy.py:43-44`
- **Description:** `FamilyProxyCreateRequest` accepts `guardian_patient_id` and `dependent_patient_id` as arbitrary strings. While the docstring states `(must be distinct)`, there is no Pydantic `@model_validator` verifying that `guardian_patient_id != dependent_patient_id`. A malicious user or client bug could submit an identical UUID for both fields, creating a circular self-guardian relationship that could bypass adult privacy restrictions or confound downstream access queries.
- **Impact:** Logic bypass and unauthorized self-guardianship states (CWE-840).
- **Remediation:** Implement a `@model_validator(mode="after")` enforcing that `guardian_patient_id` and `dependent_patient_id` are strictly distinct.

##### Vulnerability 2: Unmasked Dependent ABHA in String Repr (`BE-SCH-FPX-F02`)
- **Severity:** S2 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/family_proxy.py:67`
- **Description:** `FamilyProxyResponse.dependent_abha` is an unmasked string without `repr=False`. When proxy linkages are serialized or logged during authorization audits, dependent/minor ABHA numbers are written to server logs in plaintext.
- **Impact:** Leaks sensitive national health IDs of minors (CWE-532).
- **Remediation:** Add `repr=False` to `dependent_abha`.

##### Vulnerability 3: Hardcoded Localhost Fallback in Audit Logs (`BE-SCH-FPX-F03`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/family_proxy.py:80`
- **Description:** `ProxyAuditLogItem.ip_address` defaults to the string literal `"127.0.0.1"` and lacks `IPvAnyAddress` validation. If the calling service fails to extract the client IP, the audit record silently records a loopback address, destroying forensic non-repudiation.
- **Impact:** Falsified or uninformative forensic audit records.
- **Remediation:** Remove the `"127.0.0.1"` default; require `ip_address: IPvAnyAddress`.

##### Vulnerability 4: Missing Pydantic ConfigDict from_attributes (`BE-SCH-FPX-F04`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/family_proxy.py:41, 54, 72`
- **Description:** None of the schemas in this module declare `model_config = ConfigDict(from_attributes=True)`. Attempting to serialize SQLAlchemy ORM models (`FamilyProxyRelationship`, `ProxyAuditLog`) using `FamilyProxyResponse.model_validate(orm_obj)` raises a runtime `ValidationError`.
- **Impact:** Runtime serialization crashes during database retrieval in endpoint handlers.
- **Remediation:** Add `model_config = ConfigDict(from_attributes=True)` to all response and audit models.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-FPX-F01` | S1 | `[SEC]` | `family_proxy.py:43-44` | Missing validator ensuring `guardian_patient_id != dependent_patient_id` |
| `BE-SCH-FPX-F02` | S2 | `[SEC]` | `family_proxy.py:67` | Unmasked dependent ABHA identifier exposed in `repr` |
| `BE-SCH-FPX-F03` | S2 | `[QUAL]` | `family_proxy.py:80` | Audit log IP address defaults to `"127.0.0.1"` without IP validation |
| `BE-SCH-FPX-F04` | S3 | `[QUAL]` | `family_proxy.py:41, 54, 72` | Missing `ConfigDict(from_attributes=True)` prevents ORM deserialization |
| `BE-SCH-FPX-F05` | S3 | `[QUAL]` | `family_proxy.py:48` | `verification_document_hash` defaults to all zeros and lacks hex pattern checks |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/family_proxy.py
+++ b/backend/app/schemas/family_proxy.py
@@ -3,6 +3,6 @@ from datetime import datetime, timezone
 from enum import Enum
 from typing import Any, Dict, List, Optional
-from pydantic import BaseModel, Field
+from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, model_validator
 
 
 class RelationshipTypeEnum(str, Enum):
@@ -42,6 +42,8 @@ class FamilyProxyCreateRequest(BaseModel):
     guardian_patient_id: str = Field(..., description="Unique ID of guardian patient profile")
     dependent_patient_id: str = Field(..., description="Unique ID of dependent patient profile (must be distinct)")
+
+    @model_validator(mode="after")
+    def validate_distinct_parties(self) -> "FamilyProxyCreateRequest":
+        if self.guardian_patient_id == self.dependent_patient_id:
+            raise ValueError("guardian_patient_id and dependent_patient_id must be distinct")
+        return self
@@ -54,6 +56,8 @@ class FamilyProxyResponse(BaseModel):
     """Detailed model representing an active family proxy linkage."""
+    model_config = ConfigDict(from_attributes=True)
+
     relationship_id: str = Field(..., description="Unique proxy relationship identifier")
@@ -67,5 +71,5 @@ class FamilyProxyResponse(BaseModel):
     dependent_name: Optional[str] = None
-    dependent_abha: Optional[str] = None
+    dependent_abha: Optional[str] = Field(None, repr=False)
     dependent_age: Optional[int] = None
@@ -73,6 +77,8 @@ class ProxyAuditLogItem(BaseModel):
     """Audit entry recording access to a dependent patient record by a guardian."""
+    model_config = ConfigDict(from_attributes=True)
+
     log_id: str
     relationship_id: str
@@ -80,4 +86,4 @@ class ProxyAuditLogItem(BaseModel):
-    ip_address: str = "127.0.0.1"
+    ip_address: IPvAnyAddress
     timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```
