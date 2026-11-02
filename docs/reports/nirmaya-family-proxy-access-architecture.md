# NIRMAYA Family Proxy Access and Zero-Contamination Architecture

**Document Version:** 1.0.0  
**Effective Date:** 2026-11-02  
**Classification:** Technical Architecture Specification  
**Regulatory Standard:** Digital Personal Data Protection (DPDP) Act 2023 Section 9; ABDM Unified Health Interface (UHI) Proxy Guidelines

---

## 1. Executive Summary and Legal Framework

In India's healthcare landscape, a substantial proportion of clinical interactions occur through family proxies: parents managing care for minor children, and adult children managing care for senior or incapacitated parents.

The Indian Digital Personal Data Protection (DPDP) Act 2023 introduces strict legal obligations regarding the processing of personal data for individuals under 18 years of age and persons with disabilities:

> **DPDP Act 2023, Section 9(1):**  
> *"The Data Fiduciary shall, before processing any personal data of a child or a person with disability who has a lawful guardian, obtain verifiable consent of the parent of such child or the lawful guardian, as the case may be, in such manner as may be prescribed."*

Furthermore, Section 9(2) explicitly prohibits tracking, behavioral monitoring, or targeted advertising directed at children, and Section 9(3) prohibits any processing of personal data likely to cause detrimental effects on child well-being.

To fulfill these legal imperatives and maintain pristine clinical safety, NIRMAYA implements a **Zero-Contamination Family Proxy Architecture**.

---

## 2. Threat Model: Clinical Cross-Contamination Risks

Legacy Electronic Medical Record (EMR) systems often allow guardians to add dependents as informal sub-profiles or append dependent notes into the guardian's own record. This architectural flaw presents catastrophic clinical risks:

| Risk Category | Legacy Failure Mode | NIRMAYA Architectural Remediation |
|---|---|---|
| **Diagnostic Contamination** | Pediatric asthma diagnosis recorded in mother's profile leads to incorrect adult triage. | Strict entity segregation: Every human possesses an independent `PatientProfile` with distinct UUID and ABHA address. |
| **Allergy Inversion** | Child's severe penicillin anaphylaxis is recorded on parent's chart; child is subsequently administered penicillin at school. | Zero data colocation: Allergies and intolerance lists belong strictly to the dependent's FHIR vault. |
| **Identity Conflation** | Diagnostic lab reports for elderly parent overwrite son's cardiac history. | Proxy relationship table acts purely as an access delegation bridge; health data is never duplicated or colocated. |
| **Audit Ambiguity** | Doctor cannot discern whether appointment was booked by patient or proxy. | Every write and read operation via proxy records actor guardian ID, target dependent ID, and access rationale in an immutable forensic ledger. |

---

## 3. Data Model and Entity Isolation

The NIRMAYA Zero-Contamination architecture maintains absolute boundary isolation between guardian and dependent entities.

```
+------------------------------------+          +------------------------------------+
|       Guardian PatientProfile      |          |       Dependent PatientProfile     |
| - patient_id: pat-priya-sharma-01  |          | - patient_id: pat-aarav-sharma-02  |
| - name: Dr. Priya Sharma           |          | - name: Aarav Sharma               |
| - abha_address: priya@abdm         |          | - abha_address: aarav@abdm         |
| - clinical_vault: [Records A, B]   |          | - clinical_vault: [Records X, Y]   |
+-----------------+------------------+          +------------------+-----------------+
                  |                                                |
                  |          +----------------------------+        |
                  +--------->|  PatientProxyRelationship  |<-------+
                             | - relationship_id          |
                             | - relationship_type        |
                             | - verification_tier        |
                             | - access_scope             |
                             | - status (ACTIVE/REVOKED)  |
                             | - verification_doc_hash    |
                             +----------------------------+
```

### 3.1 Architectural Invariant: Zero Record Contamination
A dependent's clinical records (Observations, Conditions, MedicationRequests, DiagnosticReports) are linked exclusively to the dependent's `patient_id`. Under no circumstances may a guardian's `patient_id` be written to the `subject` field of a dependent clinical resource.

---

## 4. Multi-Tier Verification Authority

Proxy privileges grant access to sensitive health information. NIRMAYA enforces a four-tier verification taxonomy prior to granting active proxy status:

1. **Tier 1: DigiLocker Verified Birth Certificate (`DIGILOCKER_BIRTH_CERTIFICATE`)**
   - Direct integration with DigiLocker API to verify Government-issued birth certificates linking parent and child.
   - SHA-256 cryptographic hash of the digitally signed document is recorded.
2. **Tier 2: Aadhaar Demographic Matching (`AADHAAR_DEMOGRAPHIC_EKYC`)**
   - Demographic cross-matching via Aadhaar e-KYC (shared guardian address and matching parent name).
3. **Tier 3: Judicial Court Order (`COURT_LEGAL_GUARDIANSHIP_ORDER`)**
   - Required for legal guardians, foster care, or adult guardianship for incapacitated individuals.
   - Court order document hash and case number attested by administrative registry.
4. **Tier 4: Self-Declaration (`SELF_DECLARATION_PROVISIONAL`)**
   - Provisional access with restricted scope (emergency or temporary) pending formal cryptographic verification within 14 days.

---

## 5. Granular Access Scopes and Security Interceptor

Access granted to a proxy is strictly bounded by explicit scopes:

| Access Scope | Permitted Actions | Prohibited Actions |
|---|---|---|
| `FULL_MANAGEMENT` | View records, schedule appointments, order diagnostics, consent delegation | Transfer ownership, delete historical audit logs |
| `APPOINTMENTS_ONLY` | Schedule, reschedule, cancel OPD consultations | View clinical notes, laboratory results, medications |
| `RECORDS_VIEW_ONLY` | Read-only access to immunization cards, diagnostic reports, discharge summaries | Write new observations, book appointments, cancel treatments |
| `EMERGENCY_ONLY` | Temporary break-the-glass access during verified acute care admissions | Standard elective care management |

### 5.1 Enforcement Interceptor
Every API invocation on a dependent record passes through `verify_proxy_access_permission()`. If the guardian does not hold an active delegation matching the requested operation, the request is terminated with `HTTP 403 Forbidden` and flagged in the forensic ledger.

---

## 6. Forensic Audit Ledger Specifications

Under DPDP Act 2023 and ISO/IEC 27001 standards, all proxy interactions are recorded in an append-only forensic audit trail.

Each audit event records:
- `log_id`: Unique identifier of the audit entry.
- `relationship_id`: Active proxy linkage ID.
- `actor_guardian_id`: Identification of the guardian performing the operation.
- `target_dependent_id`: Identification of the dependent whose record is accessed.
- `action_performed`: Verb representing operation (e.g., `VIEW_PEDIATRIC_IMMUNIZATION_RECORD`).
- `resource_accessed`: Specific FHIR or system URI accessed.
- `ip_address`: Network origin of the transaction.
- `timestamp`: UTC timestamp of the transaction.
- `authorized`: Boolean indicating whether access was permitted or denied.

---

## 7. Architectural Invariant Scorecard

| Invariant ID | Description | Verification Method | Status |
|---|---|---|---|
| **INV-PROXY-01** | Zero Record Contamination: Dependent and guardian IDs are strictly segregated. | Schema and service layer checks | Verified |
| **INV-PROXY-02** | Verifiable Consent: Child proxy creation mandates parental consent attestation. | DPDP Act Sec 9 validator | Verified |
| **INV-PROXY-03** | Age of Majority: Minor child relationships require dependent age under 18. | ISO date validator | Verified |
| **INV-PROXY-04** | Document Provenance: All non-provisional linkages record SHA-256 document hash. | Cryptographic hash check | Verified |
| **INV-PROXY-05** | Immutable Audit: Every proxy action appends to forensic ledger. | Audit service verification | Verified |
