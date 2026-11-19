# Audit Report: backend/app/schemas/delegation.py

**Path:** `backend/app/schemas/delegation.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 164 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for administrative chain-of-command authority provisioning, numerical designation ranking, scoped territorial RBAC validation, and cryptographically hashed delegation audit ledgers.
- **Risk Level:** **S1 (High)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** In `AdministrativeDelegationCreate`, `aadhaar_number` and `aadhaar_otp` are stored as unmasked strings without `repr=False` or `SecretStr`. Standard logging or exception traces serialize appointed officers' 12-digit Aadhaar numbers and live verification OTPs directly into plaintext logs in violation of UIDAI regulations (CWE-532 / CWE-359).

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In government healthcare administration, statutory powers (such as issuing containment zone directives or reallocating hospital beds) can only be exercised through authorized administrative delegations. A superior officer (e.g. State Health Secretary) delegates authority to a subordinate officer (e.g. District Magistrate or Chief Medical Officer) within a strictly bounded territorial jurisdiction. This delegation must be verified via Aadhaar e-KYC, restricted to authorized `@gov.in` / `@nic.in` domains, verified against PostgreSQL `ltree` spatial containment, and recorded into an immutable audit ledger. This file structures the delegation creation, revocation, scope verification, and audit models.

### How it works, step by step
1. `DelegationRank` maps Government of India administrative designations to numerical tiers (National Director = 5, State Secretary = 4, Divisional Commissioner = 3, District Magistrate / CMO = 2, Block Medical Officer = 1) and defines strict superiority checks.
2. `AdministrativeDelegationBase` and `AdministrativeDelegationCreate` structure authority transfers down the chain of command, validating government email domains via `validate_gov_email_domain`.
3. `AdministrativeDelegationResponse` formats active delegation records with cryptographic SHA-256 audit hashes and LGD unit tiers.
4. `DelegationRevokeRequest` captures official revocation actions with mandatory rationale descriptions.
5. `TerritorialScopeValidationRequest` and `TerritorialScopeValidationResponse` evaluate whether an officer's assigned ltree path authorizes access to a specific clinical resource or hospital facility path.
6. `GovEmailValidationResult` and `DelegationAuditRecord` structure domain validation proofs and immutable hash-linked audit ledger entries.

### Concepts and patterns used
- *Hierarchical Chain-of-Command Ranking:* Numerical authority mapping ensuring only superior officers can appoint subordinates.
- *Strict Government Domain Whitelisting:* Regex and suffix validation requiring `@gov.in` or `@nic.in`.
- *PostgreSQL LTree Scoped Authorization:* Path containment evaluation (`officer_jurisdiction_path` ancestor of `target_resource_path`).

### Key lines to read first
- `delegation.py:11-32`: `DelegationRank` numerical hierarchy mapping.
- `delegation.py:54-89`: `AdministrativeDelegationCreate` and government email validator.
- `delegation.py:91-106`: `AdministrativeDelegationResponse` with audit proof.
- `delegation.py:116-140`: `TerritorialScopeValidationRequest` and response.
- `delegation.py:151-164`: `DelegationAuditRecord` ledger schema.

### How to change it safely
Ensure `aadhaar_number` and `aadhaar_otp` are masked with `repr=False`. When adding new designations to `GovtDesignationEnum`, update `DelegationRank.RANK_MAP` accordingly.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `enum` (Enum), `typing` (Dict, List, Optional), `pydantic` (BaseModel, ConfigDict, Field, field_validator), `app.schemas.administrative_hierarchy` (AdminLevelEnum, GovtDesignationEnum).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/delegation_service.py`, `backend/app/api/v1/endpoints/delegation.py`.
- **Public Surface:** Classes `DelegationRank`, `DelegationStatusEnum`, `AdministrativeDelegationBase`, `AdministrativeDelegationCreate`, `AdministrativeDelegationResponse`, `DelegationRevokeRequest`, `TerritorialScopeValidationRequest`, `TerritorialScopeValidationResponse`, `GovEmailValidationResult`, `DelegationAuditRecord`.

### 2. Security [SEC]
- **Plaintext Aadhaar & OTP Exposure (CWE-359 / CWE-532):** In `AdministrativeDelegationCreate` (lines 57-68), `aadhaar_number` and `aadhaar_otp` are plain `str` fields (`BE-SCH-DEL-F01`). Request logging will persist full 12-digit Aadhaar numbers and live OTPs in application log stores, violating UIDAI security regulations.
- **Unenforced Superiority Check in Schema (`BE-SCH-DEL-F02`):** Although `DelegationRank.is_strictly_superior` is implemented (line 29), `AdministrativeDelegationCreate` never calls it in a `@model_validator(mode="after")`. This permits invalid delegation payloads where `delegator_designation <= delegatee_designation` to pass schema validation and rely entirely on service-level enforcement.

### 3. Code quality [QUAL]
- **Unvalidated SHA-256 Digest Format (`BE-SCH-DEL-F03`):** In `DelegationAuditRecord.audit_hash` and `previous_hash` (lines 161-162), strings lack regex validation (`^[a-fA-F0-9]{64}$`).
- **Unvalidated LTree Path Syntax (`BE-SCH-DEL-F04`):** In `AdministrativeDelegationBase.jurisdiction_path` (line 50) and `TerritorialScopeValidationRequest`, paths lack regex checks for PostgreSQL `ltree` label syntax.
- Clean and robust email domain validator in `validate_gov_email_domain` (lines 75-88).

### 4. AI-generated-code smells [QUAL]
- None; the model cleanly represents sovereign Indian chain-of-command governance.

### 5. Performance [PERF]
- Sub-millisecond evaluation latency; `TerritorialScopeValidationResponse.evaluation_latency_ms` tracks microsecond-level performance.

### 6. Error handling & edge cases
- Bounded strings (`reason: min_length=5, max_length=500` in `DelegationRevokeRequest`) prevent empty revocation rationales.

### 7. Doc accuracy [DOC]
- Aligns with Day 85 territorial RBAC and delegation architecture.

### 8. Tests
- Covered by `backend/tests/test_delegation.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-DEL-F01 | S1 | [SEC] | 57-68 | Plaintext Aadhaar and OTP exposed in string `repr` | `aadhaar_number: str`, `aadhaar_otp: str` without `repr=False` | Add `repr=False` to prevent log leakage |
| BE-SCH-DEL-F02 | S2 | [SEC] | 54-89 | Superiority check not enforced in schema validator | `DelegationRank.is_strictly_superior` not invoked in model validator | Add `@model_validator(mode="after")` enforcing strict rank superiority |
| BE-SCH-DEL-F03 | S3 | [QUAL] | 161-162 | Audit hashes lack SHA-256 regex pattern | `audit_hash: str`, `previous_hash: Optional[str]` | Add regex pattern `^[a-f0-9]{64}$` |
| BE-SCH-DEL-F04 | S3 | [QUAL] | 50, 120 | LTree paths lack syntax validation | `jurisdiction_path: str` without pattern | Add regex validator for ltree label format |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-DEL-F01 · Risk: Low · [UNTESTED]
Mask delegatee Aadhaar number and OTP code in string representations:

```diff
--- a/backend/app/schemas/delegation.py
+++ b/backend/app/schemas/delegation.py
@@ -60,2 +60,3 @@ class AdministrativeDelegationCreate(AdministrativeDelegationBase):
         max_length=14,
         description="12-digit Aadhaar UID of delegatee (spaces optional)",
+        repr=False,
     )
@@ -66,2 +67,3 @@ class AdministrativeDelegationCreate(AdministrativeDelegationBase):
         max_length=6,
         description="6-digit Aadhaar OTP for identity verification simulator",
+        repr=False,
     )
