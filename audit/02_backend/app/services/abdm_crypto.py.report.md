# Comprehensive Principal Software Audit & Technical Documentation
# File: `backend/app/services/abdm_crypto.py`
# Component: ABDM Milestone 3 Fidelius Cryptographic Key Exchange Engine
# Release Version: 1.1.0-RC3 · ABDM / NRCES v4.1 Compliance

---

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/abdm_crypto.py` implements the cryptographic key agreement and session management protocol mandated by the National Health Authority (NHA) Fidelius specifications for end-to-end encrypted health information transfer. It generates ephemeral Curve25519 (X25519) key pairs, computes XOR entropy over 32-byte CSPRNG nonces to derive 20-byte salts and 12-byte initialization vectors (IV), performs Diffie-Hellman scalar multiplication, and derives 256-bit symmetric encryption keys via RFC 5869 HKDF-SHA256.

### Architectural Role & System Topology
```
           +-----------------------------------------------+
           |   Inbound Health Information Request (Gateway)|
           |  POST /v0.5/health-information/hip/request    |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |    AbdmCryptoService.process_inbound_hi_request|
           +-----------------------------------------------+
                                  |
                     (ECDH Curve25519 Agreement)
                                  v
           +-----------------------------------------------+
           |  HIP Ephemeral Keypair + Nonce XOR -> Salt/IV  |
           |  Shared Secret -> HKDF-SHA256 -> 32-Byte Key  |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |  CryptoSessionStore (Cache Session for Push)  |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           | dispatch_hi_on_request (POST Gateway Callback)|
           +-----------------------------------------------+
```

### Key Import/Export Roster
- **Imports**:
  - `cryptography.hazmat.primitives.asymmetric.x25519`: X25519 key classes and scalar multiplication.
  - `cryptography.hazmat.primitives.kdf.hkdf.HKDF`: HKDF-SHA256 key derivation.
  - `secrets, base64, httpx, threading`: Randomness, encoding, network I/O, and thread locking.
  - Crypto schemas from `app.schemas.abdm_m3_crypto`.
  - Consent store from `app.services.abdm_consent`.
- **Exports**:
  - `CryptoSessionStore`, `crypto_session_store`: In-memory thread-safe session cache.
  - `AbdmCryptoService`: Static cryptographic routines for key generation, parsing, XOR entropy, and HKDF.
  - `dispatch_hi_on_request`: Outbound gateway `/on-request` callback dispatcher.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Ephemeral Key Generation**: `generate_key_pair()` generates a fresh 32-byte raw Curve25519 private key and extracts its public key, serializing both to Base64 strings.
2. **Nonce Generation**: `generate_nonce()` produces 32 cryptographically secure random bytes via `secrets.token_bytes(32)`.
3. **XOR Entropy Extraction**: `compute_xor_entropy()` XORs the HIP and HIU nonces byte-by-byte. The first 20 bytes serve as the HKDF salt, and the remaining 12 bytes serve as the AES-256-GCM initialization vector.
4. **Key Derivation**: `derive_shared_secret()` computes the Diffie-Hellman scalar multiplication point $K = \text{priv}_{\text{local}} \times \text{pub}_{\text{peer}}$. `derive_symmetric_key()` feeds $K$ and the 20-byte salt into HKDF-SHA256 to output a 256-bit symmetric key.
5. **Session Ingestion**: `process_inbound_hi_request()` verifies consent in `ConsentRegistryStore`, parses HIU key material, executes the handshake, and stores session state in `CryptoSessionStore`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Unconditional Callback Dispatch Bypass (CWE-489)
In `dispatch_hi_on_request` (line 415):
```python
if getattr(settings, "ENVIRONMENT", "development") in ["test", "development"] or True:
    logger.info(...)
    return True
```
The expression `or True` permanently disables outbound network dispatch to the ABDM Gateway `/v0.5/health-information/hip/on-request` across all environments. In production, the gateway never receives the asynchronous acknowledgement indicating that the HIP has accepted the transfer request.

### Invariant 2: In-Memory Session Partitioning in Multi-Worker Environments
`CryptoSessionStore` caches session details (including the derived symmetric key and IV) in an in-memory dictionary (`self._sessions_by_tx`). Because health information requests and subsequent data transfer pushes occur in separate HTTP requests, in a multi-worker deployment (e.g., Uvicorn with 4 workers), the push request will hit a different worker that lacks the cached crypto session, causing data transfer failures.

### Invariant 3: Plaintext Symmetric Keys in Memory Model Objects
In line 377, `CryptoSessionDetail` stores `derivedKeyHex=derived_key.hex()`. Storing raw 256-bit symmetric encryption keys in unencrypted hex strings within Pydantic model instances risks leaking key material if the object is logged or returned via diagnostics endpoints.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SVC-CRY-F01` | S1 | `[QUAL]` | `abdm_crypto.py:415` | `or True` in `dispatch_hi_on_request` permanently disables outbound gateway callbacks |
| `BE-SVC-CRY-F02` | S2 | `[PERF]` | `abdm_crypto.py:71-72` | In-memory `CryptoSessionStore` fails to share sessions across multi-worker ASGI processes |
| `BE-SVC-CRY-F03` | S2 | `[SEC]` | `abdm_crypto.py:377` | 256-bit symmetric encryption keys stored in plaintext hex in `CryptoSessionDetail` |
| `BE-SVC-CRY-F04` | S3 | `[QUAL]` | `abdm_crypto.py:63` | Hardcoded default session TTL of 3600 seconds lacks configuration override |

---

## Layer E: Unapplied Unified Diff Patches for S0–S2 Findings

```diff
--- a/backend/app/services/abdm_crypto.py
+++ b/backend/app/services/abdm_crypto.py
@@ -412,7 +412,7 @@
     logger.info(f"[dispatch_hi_on_request] Emitting on-request for correlation req={callback.resp.requestId}")
 
     # Simulated environment mode
-    if getattr(settings, "ENVIRONMENT", "development") in ["test", "development"] or True:
+    if getattr(settings, "ENVIRONMENT", "development") in ["test", "development", "sandbox"]:
         logger.info(
             f"[dispatch_hi_on_request] Sandbox simulated callback success for {gateway_url} (req={callback.requestId})"
         )
```
