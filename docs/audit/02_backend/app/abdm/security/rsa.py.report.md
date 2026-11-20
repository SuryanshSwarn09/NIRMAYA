# Principal Software Engineering Audit: backend/app/abdm/security/rsa.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/abdm/security/rsa.py` implements the RSA-2048 cryptographic engine used to encrypt and decrypt sensitive demographic data exchanged with the National Health Authority (NHA) ABDM Gateway. It complies with official NHA specifications: RSA-2048 with Optimal Asymmetric Encryption Padding (OAEP), SHA-256 digest, and MGF1(SHA-256) mask generation function. Critical security and operational flaws include: (1) silent automated fallback to ephemeral in-memory RSA key generation when environment PEM strings are absent or malformed, causing multi-worker or restarted container replicas to generate mismatched keys that permanently fail decryption on incoming demographic callbacks, (2) exporting unencrypted PKCS8 private keys without password protection, and (3) attempting to encrypt full JSON demographic dictionaries directly with RSA-OAEP, which fails with `ValueError: Plaintext is too long` whenever the JSON payload exceeds RSA-2048's 190-byte plaintext limit.

### System Topology & Architectural Invariants
```
                  +-----------------------------------------------+
                  |          ABDM Gateway Callback Webhooks       |
                  |           (Demographic Verification / M1)     |
                  +-----------------------+-----------------------+
                                          |
                                          v
                  +-----------------------------------------------+
                  |    ABDMRSAEncryptionManager (rsa.py)          |
                  |                                               |
                  |  - Asymmetric: RSA-2048 (public_exponent=65537|
                  |  - Padding: OAEP with SHA-256 / MGF1(SHA-256) |
                  |  - Ephemeral Key Pair Generation (High Risk)  |
                  +-----------------------+-----------------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
                        v                                   v
          +---------------------------+       +---------------------------+
          | encrypt_demographic_      |       | decrypt_demographic_      |
          | payload()                 |       | payload()                 |
          | - Max Plaintext: 190 B    |       | - Base64 decode           |
          | - Base64 ciphertext export|       | - RSA OAEP Decrypt        |
          +---------------------------+       | - JSON dict deserialize   |
                                              +---------------------------+
```

### Import / Export Surface Map
- **Upstream Dependencies:**
  - `base64`, `json`, `logging`: Data serialization and transport encoding.
  - `typing.Any`, `typing.Dict`, `typing.Optional`, `typing.Tuple`, `typing.Union`: Type hints.
  - `cryptography.hazmat.primitives.hashes`: SHA-256 hash algorithms.
  - `cryptography.hazmat.primitives.serialization`: PEM and DER serialization (PKCS8 / SubjectPublicKeyInfo).
  - `cryptography.hazmat.primitives.asymmetric.padding`: OAEP and MGF1 padding.
  - `cryptography.hazmat.primitives.asymmetric.rsa`: RSA-2048 key generation and operations.
  - `app.core.config.settings`: Configuration parameters (`ABDM_ENCRYPTION_PUBLIC_KEY`, `ABDM_ENCRYPTION_PRIVATE_KEY`).
- **Downstream Consumers:**
  - `backend/app/abdm/client.py`: Verifies key configuration status via `has_private_key`.
  - `backend/app/services/abdm_discovery.py`, `abdm_linkage.py`, `patient_auth.py`: Encrypts/decrypts Aadhaar demographics.
- **Exported Interface:**
  - `ABDMRSAEncryptionManager`: Main cryptographic management class.
  - `get_abdm_encryption_manager`: Global singleton accessor.

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/abdm/security/rsa.py` manages the cryptographic lifecycle for citizen demographic verification under ABDM:
1. **Key Pair Initialization (`__init__`, `_generate_key_pair`)**: When initialized, the manager attempts to deserialize `private_key_pem` or `public_key_pem`. If neither is provided, or if deserialization raises an exception, the manager logs a warning and calls `_generate_key_pair()`, generating a random 2048-bit RSA key pair in memory.
2. **Key Serialization (`get_public_key_pem`, `get_private_key_pem`, `get_public_key_fingerprint`)**: Exports the public key in standard PEM format (`SubjectPublicKeyInfo`) or the private key in unencrypted PKCS8 format. Computes the SHA-256 fingerprint of the public key's DER encoding.
3. **Demographic Encryption (`encrypt_demographic_payload`)**: Accepts a dictionary or string, converts it to UTF-8 JSON bytes, and encrypts it using `RSA-OAEP(SHA-256, MGF1(SHA-256))` before base64-encoding the ciphertext for transport.
4. **Demographic Decryption (`decrypt_demographic_payload`)**: Accepts base64 ciphertext, decodes it, decrypts it with the loaded private key, and parses the resulting UTF-8 bytes into a Python dictionary.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Multi-Worker Desynchronization via Ephemeral Fallback Keys
In lines 41-54:
```python
except Exception as e:
    logger.warning(f"Failed to load provided private key PEM: {e}. Generating fallback key pair.")
    self._generate_key_pair()
...
else:
    self._generate_key_pair()
```
If `ABDM_ENCRYPTION_PRIVATE_KEY` is omitted or invalid, the manager silently generates an ephemeral key pair in memory. In a production cluster running multiple Uvicorn workers or container pods, each worker generates its own unique RSA key pair on startup. When NIRMAYA registers its public key with the NHA Gateway, it publishes Worker A's public key. If an inbound demographic callback from the gateway hits Worker B, Worker B attempts to decrypt the payload with its own private key, triggering immediate decryption failure (`ValueError: RSA demographic decryption failed`). Furthermore, pod restarts destroy all previously issued keys.

### Invariant 2: 190-Byte Maximum Plaintext Ceiling in RSA-OAEP Direct Encryption
In `encrypt_demographic_payload` (lines 118-126):
Under RSA-2048 with OAEP SHA-256, the maximum encryptable byte length is:
$$\text{MaxLen} = \text{KeyBytes} - 2 \times \text{HashBytes} - 2 = 256 - 2 \times 32 - 2 = 190 \text{ bytes}$$
If a caller passes a demographic dictionary containing `name`, `gender`, `date_of_birth`, `address`, and `phone` (typically 250 to 500 bytes of JSON), `self._public_key.encrypt()` fails with `ValueError: Plaintext is too long`. Standard cryptographic practice for arbitrary-length demographic payloads requires hybrid envelope encryption (generating an ephemeral AES-256-GCM symmetric key to encrypt the payload, and encrypting the 32-byte AES key with RSA-OAEP).

### Invariant 3: Unencrypted Private Key Export
In `get_private_key_pem` (lines 84-86), the private key is exported using `serialization.NoEncryption()`. If exported or logged during diagnostics, the private key is exposed in plaintext without passphrase protection.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-ABDM-RSA-F01` | **S1** | `[SEC]` | `app/abdm/security/rsa.py:41-54` | Silent fallback to ephemeral in-memory RSA key generation desynchronizes multi-worker clusters and causes decryption failures. |
| `BE-ABDM-RSA-F02` | **S1** | `[SEC]` / `[QUAL]` | `app/abdm/security/rsa.py:118-126` | Direct RSA-OAEP encryption without hybrid envelope fails on demographic JSON dictionaries exceeding 190 bytes. |
| `BE-ABDM-RSA-F03` | **S2** | `[SEC]` | `app/abdm/security/rsa.py:84-86` | Private key is exported in unencrypted PKCS8 format (`serialization.NoEncryption()`) without passphrase protection. |
| `BE-ABDM-RSA-F04` | **S3** | `[QUAL]` | `app/abdm/security/rsa.py:114` | Inconsistent JSON serialization formatting without canonical key sorting leads to non-deterministic ciphertexts. |
| `BE-ABDM-RSA-F05` | **S4** | `[DOC]` | `app/abdm/security/rsa.py:1-9` | Lacks documentation regarding NHA ABDM Public Key Registration API endpoint (`/v0.5/certificates/share`). |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-ABDM-RSA-F01`: Strict Enforced Key Loading Without Unsafe In-Memory Fallbacks
```diff
--- a/backend/app/abdm/security/rsa.py
+++ b/backend/app/abdm/security/rsa.py
@@ -40,16 +40,16 @@
                 self._public_key = self._private_key.public_key()
             except Exception as e:
-                logger.warning(f"Failed to load provided private key PEM: {e}. Generating fallback key pair.")
-                self._generate_key_pair()
+                logger.error(f"Failed to load provided private key PEM: {e}.")
+                raise ValueError(f"Invalid ABDM_ENCRYPTION_PRIVATE_KEY: {e}") from e
         elif public_key_pem and public_key_pem.strip():
             try:
                 self._public_key = serialization.load_pem_public_key(
                     public_key_pem.encode("utf-8"),
                 )  # type: ignore[assignment]
             except Exception as e:
-                logger.warning(f"Failed to load provided public key PEM: {e}. Generating fallback key pair.")
-                self._generate_key_pair()
+                logger.error(f"Failed to load provided public key PEM: {e}.")
+                raise ValueError(f"Invalid ABDM_ENCRYPTION_PUBLIC_KEY: {e}") from e
         else:
             self._generate_key_pair()
```
