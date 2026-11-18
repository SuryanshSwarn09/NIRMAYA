# Audit Report: backend/app/schemas/abdm_m3_crypto.py

**Path:** `backend/app/schemas/abdm_m3_crypto.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 189 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation models for ABDM Milestone 3 (M3) Fidelius cryptographic key exchange and health information data requests (`/v0.5/health-information/hip/request` and `/on-request`).
- **Risk Level:** **S1 (High)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `KeyGenerationResponse.privateKey`, `KeyExchangeComputeRequest.localPrivateKey`, and `CryptoSessionDetail.derivedKeyHex` are exposed as standard unmasked strings without `repr=False` or `SecretStr`. Standard logging or debugging of request/response models leaks Curve25519 private keys and derived AES-256 session keys in server logs (CWE-312 / CWE-532).

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Under the ABDM architecture, health records transferred between a hospital (HIP) and a requesting app (HIU) are encrypted end-to-end so that the central ABDM Gateway never sees plaintext medical records. To achieve this, the HIU sends an ephemeral public key and random nonce to the HIP. Both sides use Elliptic Curve Diffie-Hellman (ECDH) on Curve25519 and HKDF-SHA256 to derive a shared symmetric AES-256-GCM encryption key. This file models the key exchange structures, inbound health data request payloads, asynchronous gateway callbacks, and testing utilities.

### How it works, step by step
1. `KeyUserInfo` and `KeyMaterial` represent the Curve25519 public key and 32-byte CSPRNG random nonce exchanged between participants.
2. `HIRequestPayload` receives the incoming request on `/v0.5/health-information/hip/request`, containing the `transactionId`, `consent` reference, permitted `dateRange`, and HIU `keyMaterial`.
3. `HIOnRequestCallback` defines the payload sent back to `/v0.5/health-information/hip/on-request` acknowledging the request with `status: "ACKNOWLEDGED"` or an error code.
4. `KeyExchangeComputeRequest` and `KeyExchangeComputeResponse` provide verification interfaces to derive and confirm shared secrets, salt, IV, and derived symmetric keys.
5. `CryptoSessionDetail` stores the active cryptographic session attributes, public keys, and derived keys in local caches for subsequent encrypted FHIR payload assembly.

### Concepts and patterns used
- *Fidelius Specification:* Conforms to NHA's Fidelius reference cryptographic protocol (ECDH Curve25519 + HKDF-SHA256 + AES-GCM-256).
- *Ephemeral Key Exchange:* Separate key pairs generated per data exchange transaction to ensure forward secrecy.
- *Two-Phase Request-Callback:* Inbound request returns immediate 202, followed by async callback to the Gateway.

### Key lines to read first
- `abdm_m3_crypto.py:26-35`: `KeyMaterial` structure.
- `abdm_m3_crypto.py:54-63`: `HIRequestDetail` containing consent, date window, destination push URL, and HIU key material.
- `abdm_m3_crypto.py:65-83`: `HIRequestPayload` gateway request envelope.
- `abdm_m3_crypto.py:111-133`: `HIOnRequestCallback` gateway acknowledgement.
- `abdm_m3_crypto.py:170-189`: `CryptoSessionDetail` session cache structure.

### How to change it safely
When modifying cryptographic schemas, ensure that all fields holding private keys (`privateKey`, `localPrivateKey`) and derived symmetric keys (`derivedKeyHex`) use `repr=False` or `SecretStr` to prevent inadvertent disclosure in application logs or APM traces.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `typing`, `uuid`, `pydantic` (BaseModel, Field, ConfigDict).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/schemas/abdm_m3_hiu.py`, `backend/app/schemas/abdm_m3_transfer.py`, `backend/app/services/abdm_crypto_service.py`, `backend/app/api/v1/endpoints/abdm_m3.py`.
- **Public Surface:** `KeyUserInfo`, `KeyMaterial`, `ConsentIdRef`, `HIRequestDateRange`, `HIRequestDetail`, `HIRequestPayload`, `HIOnRequestAcknowledgement`, `GatewayHIError`, `GatewayRespRef`, `HIOnRequestCallback`, `KeyGenerationResponse`, `KeyExchangeComputeRequest`, `KeyExchangeComputeResponse`, `CryptoSessionDetail`.

### 2. Security [SEC]
- **Cleartext Private Key & Symmetric Secret Exposure (CWE-312 / CWE-532):**
  - `KeyGenerationResponse.privateKey` (line 139): Base64-encoded Curve25519 private key.
  - `KeyExchangeComputeRequest.localPrivateKey` (line 150): Base64-encoded local Curve25519 private key.
  - `CryptoSessionDetail.derivedKeyHex` (line 180): Hex-encoded 32-byte AES-256 encryption key.
  All three fields are plain `str` types without `repr=False` or `SecretStr` masking (`BE-CRY-F01`). When an exception occurs or when request/response payloads are serialized into access logs, cryptographic credentials that decrypt patient data are leaked.

### 3. Code quality [QUAL]
- **Inconsistent Type System for Transaction & Request IDs (`BE-CRY-F02`):** `HIRequestPayload` and `HIOnRequestCallback` type `requestId` and `transactionId` as `uuid.UUID`, whereas `CryptoSessionDetail` types them as `str`. In gateway communication where UUID strings may arrive without hyphens or non-canonical formats, this leads to unnecessary validation errors or cast mismatches across services.
- **Unvalidated Base64 & Nonce Lengths (`BE-CRY-F03`):** `KeyUserInfo` (lines 17-24) lacks string length or base64 character validators. A valid Curve25519 key must be 32 bytes (44 base64 characters with padding), and nonce must also be 32 bytes. Invalid inputs will cause cryptographic primitives to fail downstream.

### 4. AI-generated-code smells [QUAL]
- None; the model cleanly adheres to NHA Fidelius specifications.

### 5. Performance [PERF]
- Using `uuid.UUID` causes mild parsing overhead compared to string validation, but guarantees standard RFC 4122 compliance.

### 6. Error handling & edge cases
- `GatewayHIError` accurately models standard NHA error responses (1400 bad request, 1401 unauthorized, 1441 expired consent).

### 7. Doc accuracy [DOC]
- Perfectly matches NHA ABDM v0.5 Data Flow and Fidelius documentation.

### 8. Tests
- Covered by `backend/tests/test_abdm_crypto.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-CRY-F01 | S1 | [SEC] | 139, 150, 180 | Cryptographic private keys and derived keys exposed in string `repr` | `privateKey: str`, `localPrivateKey: str`, `derivedKeyHex: str` | Set `repr=False` or wrap with `SecretStr` |
| BE-CRY-F02 | S2 | [QUAL] | 68, 76, 173 | Inconsistent identifier typing across crypto models | `uuid.UUID` in request payload vs `str` in session details | Harmonize ID fields to `Union[uuid.UUID, str]` or string coercion |
| BE-CRY-F03 | S3 | [QUAL] | 17-24 | Missing validation on key/nonce lengths in `KeyUserInfo` | No validator enforcing 32-byte base64 encoding | Add field validator checking base64 length (44 chars) |

---

## Suggested Patches (NOT Applied)

### Patch BE-CRY-F01 · Risk: Low · [UNTESTED]
Mask private keys and derived secrets in string representation:

```diff
--- a/backend/app/schemas/abdm_m3_crypto.py
+++ b/backend/app/schemas/abdm_m3_crypto.py
@@ -136,7 +136,7 @@ class KeyGenerationResponse(BaseModel):
     """Ephemeral key pair and nonce response for testing or local initiation."""
 
     publicKey: str = Field(description="Base64-encoded Curve25519 public key")
-    privateKey: str = Field(description="Base64-encoded Curve25519 private key (kept secret)")
+    privateKey: str = Field(description="Base64-encoded Curve25519 private key (kept secret)", repr=False)
     nonce: str = Field(description="Base64-encoded 32-byte CSPRNG nonce")
     cryptoAlg: str = Field(default="ECDH")
     curve: str = Field(default="Curve25519")
@@ -147,7 +147,7 @@ class KeyExchangeComputeRequest(BaseModel):
     """Direct key exchange computation request for verification."""
 
-    localPrivateKey: str = Field(description="Base64-encoded local Curve25519 private key")
+    localPrivateKey: str = Field(description="Base64-encoded local Curve25519 private key", repr=False)
     localNonce: str = Field(description="Base64-encoded local 32-byte nonce")
     peerPublicKey: str = Field(description="Base64-encoded peer Curve25519 public key")
     peerNonce: str = Field(description="Base64-encoded peer 32-byte nonce")
@@ -177,7 +177,7 @@ class CryptoSessionDetail(BaseModel):
     hipNonce: str = Field(description="Base64-encoded HIP nonce")
     hiuPublicKey: str = Field(description="Base64-encoded HIU public key")
     hiuNonce: str = Field(description="Base64-encoded HIU nonce")
-    derivedKeyHex: str = Field(description="Hex-encoded 32-byte derived symmetric key")
+    derivedKeyHex: str = Field(description="Hex-encoded 32-byte derived symmetric key", repr=False)
     saltHex: str = Field(description="Hex-encoded 20-byte salt")
     ivHex: str = Field(description="Hex-encoded 12-byte IV")
