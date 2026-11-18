# Audit Report: backend/app/schemas/abdm_m3_consent.py

**Path:** `backend/app/schemas/abdm_m3_consent.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 304 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation models for ABDM Milestone 3 (M3) Electronic Consent Management, including consent notifications (`/v0.5/consents/hip/notify`), gateway callbacks (`/v0.5/consents/hip/on-notify`), consent artefacts, date ranges, care contexts, and testing simulation fixtures.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `ConsentArtefact` permits both top-level flattened consent fields and an embedded `consentDetail: Optional[ConsentDetail]` simultaneously without validator reconciliation, leading to ambiguity and possible `None` reference errors if callers mix wrapped and flat representations.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In ABDM Milestone 3, patients grant time-limited, purpose-specific consent before any hospital or health provider can share health records. The ABDM Gateway pushes electronic consent artefacts to the Health Information Provider (HIP) via webhook callbacks (`/v0.5/consents/hip/notify`), and the HIP must validate the digital signature, record the permission parameters, and acknowledge receipt (`/v0.5/consents/hip/on-notify`). This file structures all payloads required to parse, validate, and store these consent artefacts.

### How it works, step by step
1. `ConsentNotificationPayload` models the incoming notification from the ABDM Gateway containing a `requestId`, `timestamp`, and `ConsentNotificationDetail`.
2. `ConsentNotificationDetail` carries the consent status (`GRANTED`, `REVOKED`, `EXPIRED`) and the full `ConsentArtefact`.
3. `ConsentArtefact` encapsulates the patient identity (`ConsentPatient`), issuing Consent Manager (`ConsentManagerRef`), HIP/HIU identifiers, health information types (`hiTypes`), permission window (`ConsentPermission`), and the CM digital signature (`signature`).
4. `GatewayConsentOnNotifyCallback` formats the asynchronous callback dispatched back to the ABDM Gateway confirming receipt with status `OK` or error payload.
5. `ConsentRecordRepresentation` provides an internal normalized record schema for storing validated consent state in database tables.
6. `ConsentNotificationSimulateRequest` and `ConsentNotificationSimulateResponse` enable local developer workflows to simulate receiving consent notifications without live NHA Gateway network connectivity.

### Concepts and patterns used
- *Electronic Consent Artefact Specification:* Compliant with NHA ABDM v0.5 Data Flow Specification.
- *ISO 8601 UTC Timestamps:* Using `datetime.now(timezone.utc)` for correlation timestamps.
- *Aliased Field Mapping:* `ConsentDateRange` uses `from_date = Field(alias="from")` and `to_date = Field(alias="to")` with `populate_by_name=True` to support Python keyword `from`.

### Key lines to read first
- `abdm_m3_consent.py:89-106`: `ConsentPermission` and `ConsentDateRange` definitions.
- `abdm_m3_consent.py:117-146`: `ConsentDetail` core specification.
- `abdm_m3_consent.py:148-173`: `ConsentArtefact` structure and digital signature field.
- `abdm_m3_consent.py:190-201`: `ConsentNotificationPayload` gateway ingest schema.
- `abdm_m3_consent.py:229-245`: `GatewayConsentOnNotifyCallback` response schema.

### How to change it safely
When updating consent schemas, ensure field names strictly match NHA v0.5 camelCase specifications (e.g. `consentId`, `careContexts`, `dataEraseAt`). Always preserve the `alias="from"` configuration on `ConsentDateRange`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `typing`, `uuid`, `pydantic` (BaseModel, Field, ConfigDict).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/abdm_m3_service.py`, `backend/app/api/v1/endpoints/abdm_m3.py`.
- **Public Surface:** 16 Pydantic models including `ConsentManagerRef`, `ConsentPatient`, `ConsentPurpose`, `ConsentRequester`, `ConsentDateRange`, `ConsentPermission`, `ConsentDetail`, `ConsentArtefact`, `ConsentNotificationPayload`, `GatewayConsentOnNotifyCallback`, `ConsentRecordRepresentation`, and simulation models.

### 2. Security [SEC]
- **Digital Signature Verification Requirement:** `ConsentArtefact.signature` (line 167-170) stores the SHA256withRSA/JWS signature string. The schema allows `Optional[str]` for testing flexibility, but ingestion services must strictly enforce non-null signatures in production.
- **Absence of Sensitive PII Leaks:** No unmasked Aadhaar numbers or secret keys are present in this schema; patient identification is handled via pseudonymized ABHA ID (`sneha.sharma@abdm`).

### 3. Code quality [QUAL]
- **Dual Representation Ambiguity (`BE-M3C-F01`):** In `ConsentArtefact` (lines 148-173), all fields (`patient`, `hip`, `hiu`, `hiTypes`, `permission`) are marked `Optional` alongside `consentDetail: Optional[ConsentDetail]`. If incoming JSON supplies neither or conflicting data across flat and nested structures, validation passes silently. A model validator should normalize or enforce one format.
- **Unvalidated Date Range (`BE-M3C-F02`):** `ConsentDateRange` (lines 70-77) lacks a validator confirming that `from_date <= to_date`.
- **Unconstrained Status Strings (`BE-M3C-F03`):** `ConsentNotificationDetail.status` (line 179) and `ConsentRecordRepresentation.status` (line 251) use raw `str` rather than `Literal["GRANTED", "REVOKED", "EXPIRED"]`, permitting arbitrary strings.

### 4. AI-generated-code smells [QUAL]
- Hardcoded competitor string `"HIU-APOLLO-001"` (line 278) in simulation defaults (`BE-M3C-F04`).

### 5. Performance [PERF]
- Pydantic v2 core validation overhead is minimal; model initialization is efficient.

### 6. Error handling & edge cases
- `GatewayConsentError` properly models ABDM integer error codes (`code: int`) and descriptive messages.

### 7. Doc accuracy [DOC]
- Accurately aligns with NHA ABDM v0.5 Milestone 3 Data Flow documentation.

### 8. Tests
- Covered in `backend/tests/test_abdm_m3_consent.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-M3C-F01 | S2 | [QUAL] | 148-173 | Ambiguous dual representation in `ConsentArtefact` | Both flat fields and `consentDetail` are optional | Add model validator to unpack `consentDetail` or enforce consistent structure |
| BE-M3C-F02 | S3 | [QUAL] | 70-77 | Missing date order validation in `ConsentDateRange` | No validator checking `from_date <= to_date` | Add `@model_validator(mode="after")` verifying date bounds |
| BE-M3C-F03 | S3 | [QUAL] | 179, 251 | Unconstrained status string fields | `status: str` accepts arbitrary text | Replace with `Literal["GRANTED", "REVOKED", "EXPIRED"]` |
| BE-M3C-F04 | S4 | [QUAL] | 278 | Hardcoded third-party mock ID | `default="HIU-APOLLO-001"` | Use neutral test fixture identifier `HIU-NIRMAYA-001` |

---

## Suggested Patches (NOT Applied)

### Patch BE-M3C-F02 · Risk: Low · [UNTESTED]
Add validation to `ConsentDateRange` ensuring `from_date` is earlier than or equal to `to_date`:

```diff
--- a/backend/app/schemas/abdm_m3_consent.py
+++ b/backend/app/schemas/abdm_m3_consent.py
@@ -10,7 +10,7 @@ from datetime import datetime, timezone
 from typing import Any, Dict, List, Optional
 import uuid
 
-from pydantic import BaseModel, Field, ConfigDict
+from pydantic import BaseModel, Field, ConfigDict, model_validator
 
 
 class ConsentDateRange(BaseModel):
@@ -75,4 +75,10 @@ class ConsentDateRange(BaseModel):
 
     model_config = ConfigDict(from_attributes=True, populate_by_name=True)
 
+    @model_validator(mode="after")
+    def validate_date_order(self) -> "ConsentDateRange":
+        if self.from_date > self.to_date:
+            raise ValueError("from_date cannot be greater than to_date")
+        return self
+
