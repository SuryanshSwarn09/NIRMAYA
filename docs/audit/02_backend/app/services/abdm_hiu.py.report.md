# Technical Audit Report: backend/app/services/abdm_hiu.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/abdm_hiu.py` implements the ABDM Milestone 3 (M3) Health Information User (HIU) Data Consumer and FHIR Parser service. It orchestrates the recipient side of the National Health Authority (NHA) health information exchange: generating outbound data requests (`/v0.5/health-information/cm/request`), managing ephemeral Curve25519 cryptographic key pairs, receiving incoming encrypted payloads (`/v0.5/health-information/transfer`), executing AES-256-GCM decryption with dual-nonce HKDF-SHA256 key derivation, validating SHA-256 payload checksums, and parsing HL7 FHIR R4 Document Bundles into normalized clinical domain objects (Encounters, Diagnostic Reports, Prescriptions, Observations). The audit identified critical security and operational concerns: an in-memory session and bundle cache that fails across multi-worker deployments, ephemeral private keys stored unencrypted in memory, and zero persistent storage in PostgreSQL for imported patient health records.

### Architectural Roster
- **Module Name:** `backend/app/services/abdm_hiu.py`
- **Primary Responsibility:** HIU request session initiation, key agreement, incoming payload decryption, FHIR R4 bundle parsing, and clinical data aggregation.
- **Upstream Dependencies:**
  - `cryptography.hazmat.primitives.asymmetric.x25519`
  - `app.core.config.settings`
  - `app.core.exceptions.ValidationException`
  - `app.schemas.abdm_m3_hiu` (`HIURequestSession`, `DecryptedClinicalBundle`, etc.)
  - `app.services.abdm_crypto.AbdmCryptoService`
  - `app.services.abdm_transfer.AbdmTransferService`
  - `app.services.abdm_hip_bridge.NIRMAYA_HIP_ID`
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/abdm_hiu.py`
  - `backend/app/services/abdm_m3_audit.py`
- **Exported Symbols:**
  - `HIURequestStore`, `hiu_request_store`
  - `HIURecordStore`, `hiu_record_store`
  - `AbdmHIUService`

```
+-----------------------------------------------------------------------------------+
|                        ABDM HIU Consumer Data Pipeline                            |
|                                                                                   |
|  [Clinician/Patient]                                                              |
|          |                                                                        |
|          v                                                                        |
|  [AbdmHIUService.initiate_hi_request]                                             |
|          |-- Generates Ephemeral Curve25519 Key Pair & 32-byte Nonce              |
|          |-- Stores HIURequestSession in HIURequestStore (In-Memory)              |
|          +--> Dispatches /v0.5/health-information/cm/request to Gateway           |
|                                                                                   |
|  [Peer HIP Data Push /v0.5/health-information/transfer]                           |
|          |                                                                        |
|          v                                                                        |
|  [AbdmHIUService.process_inbound_transfer]                                        |
|          |-- Nonce XOR (HIU Nonce ^ HIP Nonce) -> Salt (20B), IV (12B)            |
|          |-- ECDH Scalar Mult -> Shared Secret -> HKDF-SHA256 -> AES-256 Key      |
|          |-- AES-256-GCM Authenticated Decryption -> Verify Tag                   |
|          |-- SHA-256 Checksum Validation (Tamper Prevention)                      |
|          +--> AbdmHIUService.parse_fhir_bundle -> HL7 FHIR R4 Extraction          |
|                      |                                                            |
|                      v                                                            |
|          [HIURecordStore (In-Memory)] --> Aggregated Clinical History             |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

When NIRMAYA acts as a Health Information User (HIU)—such as when a doctor reviews past medical records from external hospitals (e.g., Apollo, Fortis, or AIIMS) under patient consent—`abdm_hiu.py` governs the entire data flow.

1. **Request Initiation (`initiate_hi_request`):** The clinician initiates a fetch request under an active ABDM Consent Artefact. The service generates an ephemeral Curve25519 private/public key pair and a 32-byte CSPRNG nonce. It registers an `HIURequestSession` in `hiu_request_store` with a 1-hour time-to-live (TTL). It formats the outbound ABDM Gateway request payload, providing NIRMAYA's public key, nonce, and the designated `dataPushUrl` where the peer HIP must push the encrypted data.
2. **Inbound Transfer Handling (`process_inbound_transfer`):** When the external hospital's system pushes an encrypted payload (`DataTransferPushPayload`) to NIRMAYA's callback endpoint, this method matches the incoming `transactionId` against active sessions. It reads the peer HIP's public key and nonce, performs XOR entropy combination to extract a 20-byte salt and 12-byte IV, computes the ECDH shared secret, and derives the 256-bit symmetric AES key via HKDF-SHA256.
3. **Decryption & Tamper Verification:** For each encrypted data entry in the payload, the service calls `AbdmTransferService.decrypt_payload` using AES-256-GCM. If the authentication tag fails (indicating tampering), a validation exception is raised and recorded in `hiu_record_store.record_tamper_rejection()`. If decryption succeeds, the plaintext SHA-256 digest is calculated and compared against the entry's claimed checksum to detect data corruption or forgery.
4. **FHIR R4 Parsing (`parse_fhir_bundle`):** Plaintext FHIR bundles are parsed into domain models: `ParsedEncounter`, `ParsedDiagnosticReport`, `ParsedPrescription`, and `ParsedObservation`. SNOMED CT and LOINC codes are mapped to human-readable labels.
5. **Record Caching & Aggregation (`aggregate_patient_records`):** Parsed bundles are stored in `hiu_record_store`. The consultation cockpit queries `aggregate_patient_records` to retrieve all imported encounters and clinical observations for the patient.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Cryptographic & Data Integrity Invariants
- **Zero-Knowledge Key Agreement:** The ephemeral private key generated for an HIU session must never be shared across sessions or exported outside the host process.
- **Dual-Nonce Entropy (Fidelius Specification):** Salt and IV derivation must incorporate entropy from both the HIU and HIP nonces via bitwise XOR.
- **AEAD Authenticated Decryption:** Payload decryption must strictly reject any ciphertext whose 128-bit GCM authentication tag fails verification.
- **SHA-256 Integrity Verification:** Decrypted plaintext must match the accompanying SHA-256 checksum byte-for-byte.

### Failure Modes & Architectural Deficiencies
- **Process Memory Volatility:** Both `HIURequestStore` and `HIURecordStore` maintain state in standard Python dictionaries protected by `threading.RLock`. In production multi-process environments (e.g. Uvicorn with multiple workers or Kubernetes pods), the worker that initiates the request will not share state with the worker receiving the inbound transfer callback, causing `HIU request session not found or has expired` errors.
- **Non-Persistent Medical Records:** Decrypted clinical records are stored exclusively in RAM (`self._patient_bundles`). When the server restarts, all imported external patient history is permanently lost, requiring re-requesting and re-authorizing from the patient.
- **Plaintext Private Key Exposure in Session Store:** `HIURequestSession.hiuPrivateKey` holds the Base64-encoded raw private key directly in memory without envelope encryption or memory wiping.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-HIU-F01` | **S1** | `[SEC]` | `abdm_hiu.py:46-125` | In-memory session store lacks cross-worker distribution (Redis/Postgres); multi-worker clusters drop inbound ABDM transfers due to missing session state. |
| `BE-SVC-HIU-F02` | **S1** | `[SEC]` | `abdm_hiu.py:126-180` | In-memory clinical record store (`HIURecordStore`) drops all decrypted patient FHIR health records on container restart without database persistence. |
| `BE-SVC-HIU-F03` | **S2** | `[SEC]` | `abdm_hiu.py:216` | Ephemeral Curve25519 private key stored in plaintext in memory within `HIURequestSession`, vulnerable to memory dumps and log serialization. |
| `BE-SVC-HIU-F04` | **S2** | `[PERF]` | `abdm_hiu.py:171-174` | `get_all_bundles` performs linear full memory scan copying all clinical bundles across all transactions on every audit telemetry request. |
| `BE-SVC-HIU-F05` | **S3** | `[QUAL]` | `abdm_hiu.py:546` | `_parse_iso_datetime` uses broad exception catching without logging invalid date-time parsing errors. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Redis/DB Session & Record Persistence Guard (`BE-SVC-HIU-F01`, `BE-SVC-HIU-F02`)

```diff
--- a/backend/app/services/abdm_hiu.py
+++ b/backend/app/services/abdm_hiu.py
@@ -126,10 +126,14 @@
 class HIURecordStore:
     """Thread-safe store for imported, decrypted, and parsed longitudinal patient records."""
 
     def __init__(self) -> None:
         self._lock = threading.RLock()
         self._patient_bundles: Dict[str, List[DecryptedClinicalBundle]] = {}  # patient_id -> bundles
         self._tx_bundles: Dict[str, List[DecryptedClinicalBundle]] = {}  # tx_id -> bundles
         self._tamper_rejections: int = 0
+        logger.warning(
+            "[SECURITY] HIURecordStore is operating in ephemeral in-memory mode. "
+            "Imported clinical records will NOT survive backend process restarts."
+        )
```
