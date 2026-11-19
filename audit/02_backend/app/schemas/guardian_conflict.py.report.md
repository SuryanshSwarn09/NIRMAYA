# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/guardian_conflict.py`
**Audited Path:** `backend/app/schemas/guardian_conflict.py`  
**Module:** `backend` | **Subsystem:** Guardian Conflict Arbitration & Co-Signing Engine  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/guardian_conflict.py` defines the Pydantic schemas for arbitrating custodial disputes and multi-guardian concurrent actions in NIRMAYA. When multiple authorized guardians (e.g., estranged parents, court-appointed co-guardians) possess proxy authority over a dependent's electronic medical record, conflicting instructions (such as one guardian authorizing a psychiatric data transfer while the other revokes it) can arise. This module formalizes:
- Conflict arbitration policies (`PESSIMISTIC_REVOCATION_PREVALENCE`, `DUAL_GUARDIAN_CO_SIGNING`, `DISPUTED_CUSTODY_FREEZE`, `PRIMARY_GUARDIAN_ARBITRATION`).
- Custodial governance modes (`JOINT_CONCURRENT`, `DUAL_SIGNATURE_REQUIRED`, `DISPUTED_LOCKED`).
- Arbitration dispute tickets, resource locking directives, and SHA-256 integrity audits (`GuardianConflictResolutionRequest`, `GuardianConflictResolutionResponse`).
- Two-phase co-signing workflows for high-stakes electronic consent artifacts (`DualSignConsentArtifactRequest`, `DualSignCounterSignatureRequest`, `DualSignConsentArtifactResponse`).

#### 2. Key Components & Class Roster
- `ConflictResolutionPolicyEnum`: Core arbitration policies resolving concurrent disputes.
- `GuardianDisputeStatusEnum`: Lifecycle states (`RESOLVED`, `ACTIVE_DISPUTE`, `COURT_SUB_JUDICE`, `PENDING_MUTUAL_APPROVAL`).
- `CustodyModeEnum`: Operational governance modes applied to dependent proxy access.
- `GuardianActionTypeEnum`: Actions subject to conflict arbitration (`GRANT_CONSENT`, `REVOKE_CONSENT`, `RAISE_LEGAL_DISPUTE`, `RESOLVE_DISPUTE`, `CHANGE_CUSTODY_MODE`).
- `DualSignStatusEnum`: Multi-guardian consent signing stages (`PENDING_CO_SIGNATURE`, `FULLY_AUTHORIZED`, `REJECTED`).
- `GuardianEntry` & `MultiGuardianRelationshipSummary`: Aggregates active guardians, priority tiers (Tier 1 = primary natural guardian), and active legal dispute flags.
- `GuardianConflictResolutionRequest` & `GuardianConflictResolutionResponse`: Arbitration workflow interfaces establishing locked resource paths and audit hashes.
- `DualSignConsentArtifactRequest`, `DualSignCounterSignatureRequest`, `DualSignConsentArtifactResponse`: Two-phase cryptographic co-signing protocol definitions.

---

### Layer B: Plain-Language Developer Walkthrough

Consider a situation where parents are undergoing a contested divorce or custody battle, and both have legal guardianship over their child. One parent might want to share the child's therapy or hospital records with a private clinic, while the other parent strongly objects and revokes consent. Without automated governance, hospitals and software systems could be sued for releasing records improperly or caught in the middle of family disputes.

`guardian_conflict.py` provides the technical rules for handling these disputes safely:
1. It supports policies like `PESSIMISTIC_REVOCATION_PREVALENCE` (if any guardian objects, privacy and revocation always win) and `DISPUTED_CUSTODY_FREEZE` (if a court dispute is registered, records are temporarily frozen from non-emergency external sharing).
2. For sensitive records, the system can enforce `DUAL_GUARDIAN_CO_SIGNING`. Under this mode, Parent A initiates a `DualSignConsentArtifactRequest`. The consent is not valid until Parent B reviews it and submits a `DualSignCounterSignatureRequest`.
3. Every dispute resolution generates a tamper-evident audit ticket (`GuardianConflictResolutionResponse`) that locks conflicting resource endpoints and computes a SHA-256 fingerprint of the legal decision.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **Pessimistic Revocation Invariant:** Embeds `PESSIMISTIC_REVOCATION_PREVALENCE` as the safe default arbitration policy, guaranteeing that revocation always takes precedence over consent grants.
- **Hierarchical Priority Tiers:** `GuardianEntry.priority_tier` models hierarchy (`1` for primary biological guardian down to `5` for temporary delegates).
- **Two-Phase Co-Signing:** Decomposes consent authorization into separate primary and counter-signature requests, calculating independent signature hashes (`primary_signature_hash`, `co_signature_hash`) and a combined `composite_signature_hash`.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Missing Self-Co-Signing Guard in Dual-Sign Consent Request (`BE-SCH-GCF-F01`)
- **Severity:** S1 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/guardian_conflict.py:100-101`
- **Description:** In `DualSignConsentArtifactRequest`, `primary_guardian_id` and `co_guardian_id` are separate string fields. However, there is no validation check ensuring that `primary_guardian_id != co_guardian_id`. A rogue guardian who knows another co-guardian is required could supply their own UUID in both fields, or an automated client could create an artifact where the same individual acts as both primary and co-signatory.
- **Impact:** Complete bypass of dual-guardian co-signing governance (CWE-840 / CWE-287).
- **Remediation:** Add a `@model_validator(mode="after")` verifying that `primary_guardian_id` and `co_guardian_id` are strictly distinct.

##### Vulnerability 2: Unmasked Demographic Names in Logging Repr (`BE-SCH-GCF-F02`)
- **Severity:** S2 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/guardian_conflict.py:50, 60`
- **Description:** `GuardianEntry.name` and `MultiGuardianRelationshipSummary.dependent_name` are plain string fields without `repr=False`. When dispute summaries or guardian rosters are logged during conflict arbitration, full names of disputing parents and minors are exposed in application logs.
- **Impact:** Leaks sensitive family dispute details and minor identities in log pipelines (CWE-532).
- **Remediation:** Annotate `name` and `dependent_name` with `repr=False`.

##### Vulnerability 3: Unvalidated Cryptographic Signature Hashes (`BE-SCH-GCF-F03`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/guardian_conflict.py:92, 125, 126, 127`
- **Description:** Fields `audit_hash`, `primary_signature_hash`, `co_signature_hash`, and `composite_signature_hash` are declared as plain strings without format constraints. Malformed, truncated, or non-hex string digests pass validation unchecked.
- **Impact:** Weakens integrity guarantees of the dual-signature cryptographic workflow.
- **Remediation:** Enforce `pattern=r"^[a-fA-F0-9]{64}$"` and `min_length=64, max_length=64`.

##### Vulnerability 4: Missing Pydantic ConfigDict from_attributes (`BE-SCH-GCF-F04`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/guardian_conflict.py:47, 57, 82, 118`
- **Description:** None of the data models declare `model_config = ConfigDict(from_attributes=True)`. Attempting to instantiate response schemas directly from database ORM records raises runtime exceptions.
- **Impact:** Prevents clean deserialization from SQLAlchemy models.
- **Remediation:** Add `model_config = ConfigDict(from_attributes=True)` to response models.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-GCF-F01` | S1 | `[SEC]` | `guardian_conflict.py:100-101` | `primary_guardian_id` and `co_guardian_id` lack validator ensuring distinct identities |
| `BE-SCH-GCF-F02` | S2 | `[SEC]` | `guardian_conflict.py:50, 60` | Demographic names of guardians and dependents unmasked in `repr` |
| `BE-SCH-GCF-F03` | S2 | `[QUAL]` | `guardian_conflict.py:92, 125-127` | Cryptographic signature and audit hashes lack 64-character hex regex validation |
| `BE-SCH-GCF-F04` | S3 | `[QUAL]` | `guardian_conflict.py:47, 57, 82, 118` | Missing `ConfigDict(from_attributes=True)` across response models |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/guardian_conflict.py
+++ b/backend/app/schemas/guardian_conflict.py
@@ -3,5 +3,5 @@ from datetime import datetime, timezone
 from enum import Enum
 from typing import Any, Dict, List, Optional
-from pydantic import BaseModel, Field
+from pydantic import BaseModel, ConfigDict, Field, model_validator
 
 
@@ -48,4 +48,6 @@ class GuardianEntry(BaseModel):
     """Demographic and authority summary for a registered proxy guardian."""
+    model_config = ConfigDict(from_attributes=True)
+
     guardian_id: str = Field(..., description="Unique PatientProfile UUID of guardian")
-    name: str = Field(..., description="Legal demographic name")
+    name: str = Field(..., repr=False, description="Legal demographic name")
     relationship_type: str = Field(..., description="Relationship role (e.g. MOTHER, FATHER, LEGAL_GUARDIAN)")
@@ -58,4 +60,6 @@ class MultiGuardianRelationshipSummary(BaseModel):
     """Comprehensive summary of concurrent guardians and active custody governance."""
+    model_config = ConfigDict(from_attributes=True)
+
     dependent_patient_id: str = Field(..., description="Target dependent PatientProfile UUID")
-    dependent_name: str = Field(..., description="Legal demographic name of dependent")
+    dependent_name: str = Field(..., repr=False, description="Legal demographic name of dependent")
     active_guardians: List[GuardianEntry] = Field(..., description="List of authorized concurrent guardians")
@@ -83,4 +87,6 @@ class GuardianConflictResolutionResponse(BaseModel):
     """Arbitration ticket outcome and resource locking directives."""
+    model_config = ConfigDict(from_attributes=True)
+
     ticket_id: str = Field(..., description="Unique arbitration ticket ID")
@@ -91,3 +97,8 @@ class GuardianConflictResolutionResponse(BaseModel):
     locked_resources: List[str] = Field(default_factory=list, description="Resource paths locked by arbitration")
-    audit_hash: str = Field(..., description="SHA-256 integrity hash of arbitration decision")
+    audit_hash: str = Field(
+        ...,
+        pattern=r"^[a-fA-F0-9]{64}$",
+        min_length=64,
+        max_length=64,
+        description="SHA-256 integrity hash of arbitration decision",
+    )
     timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
@@ -99,4 +110,10 @@ class DualSignConsentArtifactRequest(BaseModel):
     primary_guardian_id: str = Field(..., description="Primary initiating guardian UUID")
     co_guardian_id: str = Field(..., description="Designated counter-signing co-guardian UUID")
+
+    @model_validator(mode="after")
+    def validate_distinct_signers(self) -> "DualSignConsentArtifactRequest":
+        if self.primary_guardian_id == self.co_guardian_id:
+            raise ValueError("primary_guardian_id and co_guardian_id must be distinct")
+        return self
```
