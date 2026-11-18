# Audit Report: backend/app/schemas/abdm_m3_transfer.py

**Path:** `backend/app/schemas/abdm_m3_transfer.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 179 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation models for the ABDM Milestone 3 (M3) encrypted health data transfer pipeline, covering encrypted push payloads, delivery confirmations, gateway status notifications, and testing utilities.
- **Risk Level:** **S1 (High)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** Utility models `DirectEncryptRequest` and `DirectDecryptRequest` expose `keyHex` and `plaintext` as plain strings without `repr=False` or `SecretStr`. If testing endpoints are invoked or if errors are logged, 256-bit AES symmetric keys and unencrypted health records are logged in cleartext (CWE-312 / CWE-532).

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
After key exchange and consent verification are completed, the Health Information Provider (HIP) packages the patient's medical records into FHIR R4 Document Bundles, encrypts each bundle using AES-256-GCM with a 128-bit authentication tag, computes a SHA-256 integrity checksum, and pushes the payload directly to the requesting HIU's `dataPushUrl`. Once delivered, the HIP notifies the ABDM Gateway (`/v0.5/health-information/notify`) confirming that transfer concluded. This file defines the transfer payloads, encrypted entries, and gateway status notifications.

### How it works, step by step
1. `EncryptedDataEntry` models an individual encrypted record bundle, containing base64 AES-256-GCM `content`, MIME `media` type, SHA-256 `checksum`, and associated `careContextReference`.
2. `DataTransferPushPayload` packages multiple `EncryptedDataEntry` items with pagination metadata (`pageNumber`, `pageCount`), correlation `transactionId`, and the HIP's ephemeral `keyMaterial`.
3. `DataTransferPushResponse` confirms delivery dispatch with destination URL and timestamp.
4. `TransferNotificationDetail` and `DataTransferNotificationPayload` format the status update dispatched to the ABDM Gateway summarizing per-care-context delivery outcomes.
5. `TransferAuditRecord` provides an audit log schema capturing transfer direction, bundle count, and completion state.
6. `DirectEncryptRequest` and `DirectDecryptRequest` provide testing fixtures for standalone cryptographic verification.

### Concepts and patterns used
- *Authenticated Encryption with Associated Data (AEAD):* AES-256-GCM ensuring both confidentiality and cryptographic tamper-evidence.
- *Tamper-Evident SHA-256 Checksums:* Independent pre-encryption plaintext hash verified by receiver after decryption.
- *Direct Peer-to-Peer Data Transfer:* Sensitive medical payloads bypass the central Gateway and travel directly from HIP to HIU.

### Key lines to read first
- `abdm_m3_transfer.py:19-28`: `EncryptedDataEntry` structure.
- `abdm_m3_transfer.py:30-40`: `DataTransferPushPayload` peer push schema.
- `abdm_m3_transfer.py:65-98`: Transfer status response and notification models.
- `abdm_m3_transfer.py:116-154`: Direct encryption and decryption utility schemas.
- `abdm_m3_transfer.py:163-179`: `TransferAuditRecord` audit trail model.

### How to change it safely
Ensure `keyHex` and `plaintext` in testing schemas are protected with `repr=False`. Maintain consistent camelCase attribute names aligned with ABDM v0.5 specifications.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `typing`, `uuid`, `pydantic` (BaseModel, Field, ConfigDict), `app.schemas.abdm_m3_crypto.KeyMaterial`.
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/abdm_m3_transfer_service.py`, `backend/app/api/v1/endpoints/abdm_m3.py`.
- **Public Surface:** 12 Pydantic models including `EncryptedDataEntry`, `DataTransferPushPayload`, `DataTransferPushResponse`, `TransferStatusNotification`, `DataTransferNotificationPayload`, and utility schemas.

### 2. Security [SEC]
- **Symmetric Key & Plaintext Leakage in String Repr (CWE-312 / CWE-532):** In `DirectEncryptRequest` (line 120), `DirectDecryptRequest` (line 140), and `DirectDecryptResponse` (line 149), `keyHex` and `plaintext` are plain `str` fields without masking (`BE-TRF-F01`). Standard logging of request/response payloads leaks AES keys and unencrypted health records.
- **Cryptographic AEAD Enforcement:** `EncryptedDataEntry.content` correctly expects the 128-bit authentication tag appended to the ciphertext, preventing ciphertext tampering.

### 3. Code quality [QUAL]
- **Inconsistent Transaction ID Types (`BE-TRF-F02`):** `DataTransferPushPayload.transactionId` is typed as `uuid.UUID` (line 35), while `DataTransferPushResponse.transactionId` (line 46) and `TransferNotificationDetail.transactionId` (line 89) are typed as `str`. Inconsistent types across interconnected models introduce conversion friction.
- **Missing Checksum Hash Validator (`BE-TRF-F03`):** `EncryptedDataEntry.checksum` (line 24) lacks validation enforcing a 64-character hexadecimal SHA-256 hash.

### 4. AI-generated-code smells [QUAL]
- None; the models closely follow NHA data transfer specifications.

### 5. Performance [PERF]
- Paginated transfers (`pageNumber`, `pageCount`) allow splitting large medical dossiers into manageable chunks, avoiding memory exhaustion.

### 6. Error handling & edge cases
- `TransferStatusResponse.hiStatus` cleanly models per-care-context failure handling (`OK | ERRORED`).

### 7. Doc accuracy [DOC]
- Conforms to NHA ABDM v0.5 Data Transfer specifications.

### 8. Tests
- Covered by `backend/tests/test_abdm_m3_transfer.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-TRF-F01 | S1 | [SEC] | 119, 120, 140, 149 | Symmetric AES keys and plaintext PHI exposed in string `repr` | `keyHex: str`, `plaintext: str` | Add `repr=False` or `SecretStr` |
| BE-TRF-F02 | S2 | [QUAL] | 35, 46, 89 | Inconsistent `transactionId` typing across schemas | `uuid.UUID` vs `str` | Standardize identifier typing |
| BE-TRF-F03 | S3 | [QUAL] | 24 | Unvalidated SHA-256 checksum format | `checksum: str` has no regex check | Add regex validator for 64-char hex string |

---

## Suggested Patches (NOT Applied)

### Patch BE-TRF-F01 · Risk: Low · [UNTESTED]
Mask cryptographic keys and decrypted plaintext in string representations:

```diff
--- a/backend/app/schemas/abdm_m3_transfer.py
+++ b/backend/app/schemas/abdm_m3_transfer.py
@@ -116,8 +116,8 @@ class DirectEncryptRequest(BaseModel):
     """Testing utility schema for direct AES-256-GCM encryption."""
 
-    plaintext: str = Field(description="Plaintext string or JSON to encrypt")
-    keyHex: str = Field(description="Hex-encoded 32-byte (256-bit) symmetric AES key")
+    plaintext: str = Field(description="Plaintext string or JSON to encrypt", repr=False)
+    keyHex: str = Field(description="Hex-encoded 32-byte (256-bit) symmetric AES key", repr=False)
     ivHex: str = Field(description="Hex-encoded 12-byte (96-bit) IV")
 
     model_config = ConfigDict(from_attributes=True)
@@ -137,7 +137,7 @@ class DirectDecryptRequest(BaseModel):
     """Testing utility schema for direct AES-256-GCM decryption."""
 
     ciphertext: str = Field(description="Base64-encoded ciphertext with appended tag")
-    keyHex: str = Field(description="Hex-encoded 32-byte symmetric AES key")
+    keyHex: str = Field(description="Hex-encoded 32-byte symmetric AES key", repr=False)
     ivHex: str = Field(description="Hex-encoded 12-byte IV")
 
     model_config = ConfigDict(from_attributes=True)
@@ -146,5 +146,5 @@ class DirectDecryptResponse(BaseModel):
     """Testing utility response for direct decryption."""
 
-    plaintext: str = Field(description="Decrypted plaintext UTF-8 string")
+    plaintext: str = Field(description="Decrypted plaintext UTF-8 string", repr=False)
     status: str = Field(default="SUCCESS")
