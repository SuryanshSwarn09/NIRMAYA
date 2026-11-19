# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/guardian_delegation.py`
**Audited Path:** `backend/app/schemas/guardian_delegation.py`  
**Module:** `backend` | **Subsystem:** Delegated Electronic Consent & Ephemeral Proxy Tokens  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/guardian_delegation.py` formalizes the Pydantic schemas for issuing and managing delegated electronic consent artifacts and ephemeral scoped access tokens on behalf of dependents. Under the Ayushman Bharat Digital Mission (ABDM) Milestone 3 specification and India's Digital Personal Data Protection (DPDP) Act 2023, authorized family proxies can execute legal consent actions on behalf of minors or incapacitated elders. This module structures:
- ABDM-compliant clinical consent purposes (`ConsentPurposeEnum`: `CAREMGT`, `EMERGENCY`, `PUBHLTH`, `DIAGNOSTIC`).
- Delegated consent lifecycle transitions (`GRANTED`, `REVOKED`, `EXPIRED`, `REQUESTED`).
- Inbound consent authorization requests (`DelegatedConsentGrantRequest`) and generated electronic consent artifacts (`DelegatedConsentArtifactResponse`).
- Ephemeral scoped token exchanges (`ScopedProxyTokenRequest`, `ScopedProxyTokenResponse`) granting short-lived, zero-contamination access to dependent health records.
- Immutable forensic audit logs (`ConsentAuditTrailItem`) and revocation workflows (`DelegatedConsentRevokeRequest`).

#### 2. Key Components & Class Roster
- `ConsentPurposeEnum`: Standardized clinical purpose codes aligning with ABDM M3 and SNOMED CT.
- `DelegatedConsentStatusEnum`: Lifecycle states of delegated consent artifacts.
- `DelegatedConsentGrantRequest`: Inbound payload executed by a proxy guardian approving a third-party Health Information User (HIU) consent request, specifying granted FHIR health info types, valid date ranges, and digital attestation.
- `DelegatedConsentArtifactResponse`: Issued electronic consent artifact signed with the guardian's digital signature hash and verified under zero-contamination protocols.
- `ScopedProxyTokenRequest`: Ephemeral token exchange request specifying duration (default 1 hour, bounded 60s to 86400s) and granular scope (e.g. `proxy:dependent:CAREMGT`).
- `ScopedProxyTokenResponse`: Ephemeral OAuth2-style bearer token returned to the guardian client.
- `DelegatedConsentRevokeRequest`: Unilateral revocation payload invoking DPDP Act 2023 Section 9 parental withdrawal rights.
- `ConsentAuditTrailItem`: Forensic audit trail entry capturing consent actions, timestamps, and originating terminal IP addresses.

---

### Layer B: Plain-Language Developer Walkthrough

Imagine a mother taking her 7-year-old child to a specialist diagnostic clinic. The diagnostic clinic requests electronic access to the child's past hospital prescriptions and lab reports through the ABDM network. Because the child is a minor, the ABDM gateway routes the request to the mother's NIRMAYA app.

`guardian_delegation.py` sets up the technical pipeline for this approval:
1. The mother reviews the request and submits a `DelegatedConsentGrantRequest`. She can select which health information types to share (e.g., only "DiagnosticReport" and "Prescription", but not mental health notes) and sets an expiration date.
2. The system generates an official ABDM electronic consent artifact (`DelegatedConsentArtifactResponse`) sealed with a cryptographic hash of her approval.
3. When the mother or clinic needs to view the records, the application exchanges the approved consent for a short-lived bearer token via `ScopedProxyTokenRequest`. The returned `ScopedProxyTokenResponse` gives the app temporary (e.g. 1-hour) read-only access strictly bounded to that child's records.
4. If the mother changes her mind, she can submit a `DelegatedConsentRevokeRequest` at any time to immediately cancel data access.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **DPDP Act Section 9 Attestation:** `guardian_signature_attestation` enforces active legal consent attestation during consent issuance.
- **Bounded Ephemeral Tokens:** `duration_seconds` enforces strict integer limits (`ge=60, le=86400`), preventing the generation of infinite or sub-minute bearer tokens.
- **Zero-Contamination Verification:** Embeds `zero_contamination_verified` flags ensuring proxy operations maintain strict data isolation boundaries between guardian and dependent storage partitions.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Active Scoped Bearer Token Leaked in String Repr (`BE-SCH-GDL-F01`)
- **Severity:** S1 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/guardian_delegation.py:69`
- **Description:** `ScopedProxyTokenResponse.access_token` is declared as a plain string without `repr=False` or `SecretStr`. When token issuance events or proxy responses are logged during debugging or API gateway request logging, live ephemeral JWT bearer tokens are printed in cleartext to log files. Anyone with access to server logs can hijack these tokens to read dependent medical records.
- **Impact:** Credential leakage leading to unauthorized access to sensitive pediatric health data (CWE-532 / CWE-312).
- **Remediation:** Annotate `access_token` with `repr=False` in its `Field` definition.

##### Vulnerability 2: Hardcoded Loopback IP in Forensic Audit Trail (`BE-SCH-GDL-F02`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/guardian_delegation.py:94`
- **Description:** `ConsentAuditTrailItem.ip_address` defaults to `"127.0.0.1"` and lacks `IPvAnyAddress` validation. If the service layer fails to supply the actual client IP, forensic audit trails for legal consent delegations silently record loopback addresses, compromising non-repudiation during medico-legal investigations.
- **Impact:** Corrupted forensic evidence in statutory consent audit records.
- **Remediation:** Require `ip_address: IPvAnyAddress` without a `"127.0.0.1"` fallback default.

##### Vulnerability 3: Missing Date Range Consistency Validator (`BE-SCH-GDL-F03`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/guardian_delegation.py:34-36`
- **Description:** In `DelegatedConsentGrantRequest`, fields `date_range_from`, `date_range_to`, and `expiry_date` are parsed independently. There is no Pydantic model validator verifying that `date_range_from <= date_range_to` or that `expiry_date >= datetime.now(timezone.utc)`. An inverted date range (e.g. `date_range_from` in 2026 and `date_range_to` in 2020) passes schema validation.
- **Impact:** Downstream ABDM gateway rejects the consent artifact or queries fail with empty result sets.
- **Remediation:** Implement a `@model_validator(mode="after")` validating temporal ordering of all date fields.

##### Vulnerability 4: Hardcoded Commercial Entity Default in Requester HIU Name (`BE-SCH-GDL-F04`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/guardian_delegation.py:38`
- **Description:** `requester_hiu_name` defaults to `"Apollo Health Gateway"`. If a consent grant payload omits the requesting entity, the record is attributed to a specific private healthcare company rather than requiring the actual requester's name.
- **Impact:** Inaccurate clinical provenance and misleading consent records.
- **Remediation:** Make `requester_hiu_name` a mandatory field without hardcoded commercial defaults.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-GDL-F01` | S1 | `[SEC]` | `guardian_delegation.py:69` | `ScopedProxyTokenResponse.access_token` leaks active bearer tokens in `repr` |
| `BE-SCH-GDL-F02` | S2 | `[QUAL]` | `guardian_delegation.py:94` | Audit trail IP address defaults to `"127.0.0.1"` without strict IP validation |
| `BE-SCH-GDL-F03` | S2 | `[QUAL]` | `guardian_delegation.py:34-36` | Missing validator verifying `date_range_from <= date_range_to` and future `expiry_date` |
| `BE-SCH-GDL-F04` | S3 | `[QUAL]` | `guardian_delegation.py:38` | Hardcoded commercial default `"Apollo Health Gateway"` for `requester_hiu_name` |
| `BE-SCH-GDL-F05` | S3 | `[QUAL]` | `guardian_delegation.py:55` | `guardian_signature_hash` lacks 64-character hex regex validation |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/guardian_delegation.py
+++ b/backend/app/schemas/guardian_delegation.py
@@ -3,6 +3,6 @@ from datetime import datetime, timezone
 from enum import Enum
 from typing import Any, Dict, List, Optional
-from pydantic import BaseModel, Field
+from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, model_validator
 
 
@@ -34,4 +34,14 @@ class DelegatedConsentGrantRequest(BaseModel):
     date_range_from: datetime = Field(..., description="Beginning of clinical record sharing window")
     date_range_to: datetime = Field(..., description="End of clinical record sharing window")
     expiry_date: datetime = Field(..., description="Timestamp when consent artifact expires")
     guardian_signature_attestation: bool = Field(..., description="Mandatory digital consent attestation under DPDP Act 2023 Sec 9")
-    requester_hiu_name: str = Field("Apollo Health Gateway", description="Name of requesting Health Information User (HIU)")
+    requester_hiu_name: str = Field(..., description="Name of requesting Health Information User (HIU)")
+
+    @model_validator(mode="after")
+    def validate_date_intervals(self) -> "DelegatedConsentGrantRequest":
+        if self.date_range_from > self.date_range_to:
+            raise ValueError("date_range_from must be earlier than or equal to date_range_to")
+        return self
@@ -67,5 +77,7 @@ class ScopedProxyTokenResponse(BaseModel):
     """Ephemeral bearer token issued for delegated dependent access."""
+    model_config = ConfigDict(from_attributes=True)
+
-    access_token: str = Field(..., description="Signed ephemeral bearer token")
+    access_token: str = Field(..., repr=False, description="Signed ephemeral bearer token")
     token_type: str = Field("Bearer", description="HTTP authorization scheme")
@@ -92,3 +104,3 @@ class ConsentAuditTrailItem(BaseModel):
     timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
-    ip_address: str = "127.0.0.1"
+    ip_address: IPvAnyAddress
     status: str
```
