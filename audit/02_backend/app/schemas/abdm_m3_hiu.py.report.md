# Audit Report: backend/app/schemas/abdm_m3_hiu.py

**Path:** `backend/app/schemas/abdm_m3_hiu.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 149 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation models for the ABDM Milestone 3 (M3) Health Information User (HIU) consumer engine, covering request initiation, ephemeral session state, and structured parsing of decrypted FHIR clinical resources.
- **Risk Level:** **S1 (High)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `HIURequestSession.hiuPrivateKey` is stored as an unmasked plain string field without `repr=False` or `SecretStr`. Serializing session models in application logs or tracebacks exposes the HIU's ephemeral Curve25519 private key, breaking end-to-end forward secrecy (CWE-312 / CWE-532).

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
When acting as an HIU (Health Information User), NIRMAYA requests a patient's historical medical records from other health facilities (HIPs) under an approved ABDM consent artefact. Once the encrypted FHIR records are received and decrypted using ECDH and AES-GCM, the raw FHIR JSON documents must be parsed into clear, typed clinical entities (encounters, diagnostic reports, prescriptions, observations) so doctors can review them in a clean longitudinal timeline. This file defines the initiation models, session tracker, and parsed clinical entities.

### How it works, step by step
1. `HIUDataRequestInitiate` accepts a clinician's command to fetch data, specifying the `consentId`, `patientId`, `dateRangeFrom`, `dateRangeTo`, and requested `hiTypes`.
2. `HIURequestSession` persists active request state along with the ephemeral Curve25519 key pair (`hiuPrivateKey`, `hiuPublicKey`, `hiuNonce`) needed to decrypt the inbound payload when it arrives.
3. `ParsedEncounter`, `ParsedDiagnosticReport`, `ParsedPrescription`, and `ParsedObservation` represent clean, typed projections extracted from incoming FHIR R4 bundles.
4. `DecryptedClinicalBundle` aggregates the parsed resources alongside the original `rawFhirJson` for forensic auditing.
5. `HIUPatientRecordsResponse` formats the complete longitudinal medical record returned to frontend clinician consoles.

### Concepts and patterns used
- *Clinical Resource Projections:* Translating deeply nested FHIR R4 JSON into flattened, typed Python models suitable for UI rendering.
- *Ephemeral Session State:* Associating incoming asynchronous data pushes with the corresponding private key via `transactionId`.
- *Longitudinal Patient Timeline:* Consolidating disparate health information types into a unified view.

### Key lines to read first
- `abdm_m3_hiu.py:19-36`: `HIUDataRequestInitiate` request model.
- `abdm_m3_hiu.py:38-57`: `HIURequestSession` ephemeral key tracking.
- `abdm_m3_hiu.py:63-115`: Parsed clinical models (`ParsedEncounter`, `ParsedDiagnosticReport`, `ParsedPrescription`, `ParsedObservation`).
- `abdm_m3_hiu.py:117-131`: `DecryptedClinicalBundle` container.
- `abdm_m3_hiu.py:133-149`: `HIUPatientRecordsResponse` aggregated response.

### How to change it safely
Ensure `HIURequestSession.hiuPrivateKey` is always masked with `repr=False`. When adding new FHIR resource parsers (e.g. Immunization or Procedure), define corresponding `Parsed*` schemas following the established naming conventions.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `typing`, `uuid`, `pydantic` (BaseModel, Field, ConfigDict), `app.schemas.abdm_m3_crypto.KeyMaterial`.
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/abdm_m3_hiu_service.py`, `backend/app/api/v1/endpoints/abdm_m3.py`.
- **Public Surface:** `HIUDataRequestInitiate`, `HIURequestSession`, `ParsedEncounter`, `ParsedDiagnosticReport`, `ParsedPrescription`, `ParsedObservation`, `DecryptedClinicalBundle`, `HIUPatientRecordsResponse`.

### 2. Security [SEC]
- **Ephemeral Private Key Disclosure (CWE-312 / CWE-532):** `HIURequestSession.hiuPrivateKey` (line 44) is defined as `str` without `repr=False`. Logging session objects exposes the private key used to decrypt patient health data (`BE-HIU-F01`).
- **Unredacted Raw FHIR Health Data in Logs (`BE-HIU-F02`):** `DecryptedClinicalBundle.rawFhirJson` (line 128) contains full decrypted clinical bundles as a raw string. If an unhandled exception or debug logger prints `DecryptedClinicalBundle`, full protected health information (PHI) is written to application logs. Adding `repr=False` prevents unintentional log spillage.

### 3. Code quality [QUAL]
- **Unconstrained FHIR Status Strings (`BE-HIU-F03`):** `ParsedEncounter.status` (line 67), `ParsedDiagnosticReport.status` (line 85), and `ParsedPrescription.status` (line 98) use plain strings rather than enums or `Literal` types matching standard FHIR R4 value sets (`"finished"`, `"active"`, `"final"`).
- Clean separation between raw FHIR payloads and parsed domain representations.

### 4. AI-generated-code smells [QUAL]
- None; the schema represents a clean, production-grade clinical ingest pipeline.

### 5. Performance [PERF]
- Flattened parsed models ensure fast JSON serialization for UI clients without needing recursive FHIR bundle traversals on each render.

### 6. Error handling & edge cases
- All parsed clinical dates and identifiers are properly typed as `Optional` to gracefully tolerate incomplete FHIR records from legacy hospital systems.

### 7. Doc accuracy [DOC]
- Accurately aligns with ABDM HIU data flow requirements.

### 8. Tests
- Covered by `backend/tests/test_abdm_m3_hiu.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-HIU-F01 | S1 | [SEC] | 44 | HIU ephemeral private key exposed in string `repr` | `hiuPrivateKey: str = Field(...)` | Add `repr=False` to prevent logging private key |
| BE-HIU-F02 | S2 | [SEC] | 128 | Raw decrypted clinical FHIR JSON logged in string `repr` | `rawFhirJson: str = Field(...)` | Add `repr=False` to prevent PHI leakage in logs |
| BE-HIU-F03 | S3 | [QUAL] | 67, 85, 98 | Unconstrained clinical status strings | Uses arbitrary `str` instead of FHIR R4 value sets | Use `Literal` types for standard status values |

---

## Suggested Patches (NOT Applied)

### Patch BE-HIU-F01 · Risk: Low · [UNTESTED]
Protect private key and raw clinical JSON from string representations and logging:

```diff
--- a/backend/app/schemas/abdm_m3_hiu.py
+++ b/backend/app/schemas/abdm_m3_hiu.py
@@ -41,7 +41,7 @@ class HIURequestSession(BaseModel):
     transactionId: str = Field(description="Unique correlation transaction UUID")
     consentId: str = Field(description="Associated consent artefact UUID")
     patientId: str = Field(description="Patient ABHA identifier")
-    hiuPrivateKey: str = Field(description="Base64-encoded HIU ephemeral Curve25519 private key")
+    hiuPrivateKey: str = Field(description="Base64-encoded HIU ephemeral Curve25519 private key", repr=False)
     hiuPublicKey: str = Field(description="Base64-encoded HIU ephemeral Curve25519 public key")
     hiuNonce: str = Field(description="Base64-encoded HIU CSPRNG 32-byte nonce")
     status: str = Field(default="REQUESTED", description="Status: REQUESTED | TRANSFERRED | PROCESSED | FAILED")
@@ -125,7 +125,7 @@ class DecryptedClinicalBundle(BaseModel):
     diagnosticReports: List[ParsedDiagnosticReport] = Field(default_factory=list)
     prescriptions: List[ParsedPrescription] = Field(default_factory=list)
     observations: List[ParsedObservation] = Field(default_factory=list)
-    rawFhirJson: str = Field(description="Raw decrypted FHIR R4 Document Bundle JSON")
+    rawFhirJson: str = Field(description="Raw decrypted FHIR R4 Document Bundle JSON", repr=False)
 
     model_config = ConfigDict(from_attributes=True)
