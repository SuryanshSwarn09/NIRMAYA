# Codebase Audit Report: `backend/app/services/emergency_vault.py`

**Audit Target**: `backend/app/services/emergency_vault.py`  
**Subsystem**: Backend - Zero-Knowledge Emergency Vault & Break-The-Glass Engine (`backend/app/services/`)  
**File Lines**: 387 LOC  
**Severity Breakdown**: S0: 0 | S1: 2 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `emergency_vault.py` service implements the Break-The-Glass (BTG) emergency health profile vault for NIRMAYA. It uses memory-hard Argon2id key derivation and AES-256-GCM authenticated encryption with Additional Authenticated Data (AAD) bound to the patient's ABHA number, records tamper-evident SHA-256 forensic fingerprints, and broadcasts real-time WebSocket alerts to clinicians.

```
[ Attending ER Physician ]
             │
             ▼ (Emergency BTG Request: ABHA + Clinical Justification)
   [ emergency_vault.py ]
   ├── 1. Diagnostic Justification Gate (Min 15 chars mandatory)
   ├── 2. Argon2id Key Derivation (64 MiB RAM cost, 2 iterations)
   ├── 3. AES-256-GCM Decryption (AAD = patient ABHA)
   ├── 4. SHA-256 Forensic Audit Fingerprint Generation
   └── 5. Real-Time WebSocket Panic Broadcast (Doctor & Facility Queues)
             │
             ▼
   [ Decrypted Emergency Profile (Blood, Allergies, Meds, Contacts) ]
```

### Import / Export Roster
- **Imports**: `base64`, `datetime`, `hashlib`, `logging`, `os`, `threading`, `typing`, `uuid`, `cryptography.hazmat.primitives.ciphers.aead.AESGCM`, `cryptography.hazmat.primitives.kdf.argon2.Argon2id`, `app.core.exceptions`, `app.schemas.emergency_vault`, `app.schemas.websocket_events`, `app.services.websocket_manager`.
- **Exports**: `SYSTEM_DEMO_PASSPHRASE`, `derive_vault_key()`, `encrypt_emergency_profile()`, `decrypt_emergency_profile()`, `EmergencyVaultService`, `emergency_vault_service`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Key Derivation**: `derive_vault_key()` executes Argon2id with 64MB memory cost to derive a 256-bit symmetric encryption key from a passphrase and 16-byte random salt.
2. **Envelope Encryption**: `encrypt_emergency_profile()` serializes the emergency profile to JSON, binds the patient ABHA number as Additional Authenticated Data (AAD), and encrypts via AES-256-GCM with a 12-byte random nonce.
3. **Emergency Override**: `execute_emergency_override()` enforces that the attending clinician supplies at least 15 characters of diagnostic rationale, decrypts the profile, generates a SHA-256 audit fingerprint, logs the access, and fires WebSocket panic events.
4. **Audit Log Inspection**: Allows hospitals and patients to query chronological BTG access logs and aggregate departmental override metrics.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Hardcoded Default Master Key (Zero-Knowledge Invariant Breach)
At line 50:
```python
SYSTEM_DEMO_PASSPHRASE = "NIRMAYA-EMERGENCY-MASTER-OVERRIDE-KEY-2026"
```
The functions `encrypt_emergency_profile()`, `decrypt_emergency_profile()`, `store_vault()`, and `execute_emergency_override()` all set their default parameter to `passphrase: str = SYSTEM_DEMO_PASSPHRASE`. Unless a calling controller explicitly supplies an externally managed vault passphrase derived from an HSM or user credentials, every patient's emergency envelope in NIRMAYA is encrypted under this known static string, nullifying the "zero-knowledge" security claim.

### 2. In-Memory Ephemeral Storage of Encrypted Vault Envelopes & Audit Trail
`self._vaults: Dict[str, EncryptedVaultEnvelope] = {}` and `self._audit_log: List[BTGAuditLogEntry] = []` exist exclusively in process memory. A process restart completely erases all stored patient emergency profiles and destroys all forensic audit logs of clinician access, creating severe medicolegal liability.

### 3. Clinician Identity Spoofing in Override Payload
`execute_emergency_override()` relies on `request.doctorId`, `request.doctorHpr`, and `request.doctorName` provided directly in the request body. If the API endpoint does not cross-check the session JWT against the request body, an attacker can forge emergency override requests in the name of another physician.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-EMV-F01` | **S1** | `[SEC/CRYPTO]` | `backend/app/services/emergency_vault.py:50, 78, 114` | Hardcoded fallback master passphrase `SYSTEM_DEMO_PASSPHRASE` encrypts all emergency vaults by default, breaking zero-knowledge guarantees. |
| `BE-SVC-EMV-F02` | **S1** | `[DATA/SEC]` | `backend/app/services/emergency_vault.py:146-150` | Encrypted envelopes and forensic BTG audit logs reside in RAM without database persistence, losing all emergency records upon worker restart. |
| `BE-SVC-EMV-F03` | **S2** | `[SEC/AUTH]` | `backend/app/services/emergency_vault.py:255-275` | Clinician identities (`doctorId`, `doctorHpr`) in emergency overrides are trusted from client payload without JWT session verification. |
| `BE-SVC-EMV-F04` | **S3** | `[QUAL]` | `backend/app/services/emergency_vault.py:151-218` | Hardcoded emergency profile for "Arun Patel" seeded into memory on startup. |
| `BE-SVC-EMV-F05` | **S4** | `[DOC]` | `backend/app/services/emergency_vault.py:1-25` | Missing documentation detailing DPDP Act 2023 Section 9 emergency exception retention standards and HSM key management. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-EMV-F01` / `BE-SVC-EMV-F03`: Disallowing Hardcoded Passphrase in Production & Enforcing Session Auth

```diff
--- a/backend/app/services/emergency_vault.py
+++ b/backend/app/services/emergency_vault.py
@@ -75,8 +75,13 @@ def derive_vault_key(passphrase: str, salt: bytes) -> bytes:
 def encrypt_emergency_profile(
     profile: EmergencyProfileData,
-    passphrase: str = SYSTEM_DEMO_PASSPHRASE,
+    passphrase: Optional[str] = None,
 ) -> EncryptedVaultEnvelope:
+    from app.core.config import settings
+    effective_key = passphrase or getattr(settings, "VAULT_MASTER_KEY", None)
+    if not effective_key:
+        if settings.ENVIRONMENT == "production":
+            raise ValidationException("Vault master key passphrase is mandatory in production environment.")
+        effective_key = SYSTEM_DEMO_PASSPHRASE
```
