# Comprehensive Principal Software Audit & Technical Documentation
# File: `backend/app/services/aadhaar_otp.py`
# Component: ABDM Milestone 1 Direct Aadhaar OTP & Demographic Sync
# Release Version: 1.1.0-RC3 · ABDM / NRCES v4.1 Compliance

---

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/aadhaar_otp.py` implements the service layer for ABDM Milestone 1 Aadhaar-based citizen identification, direct OTP authentication, and unified patient profile synchronization. It provides the Verhoeff dihedral group D5 checksum algorithm, manages ephemeral OTP verification sessions with TTL and attempt limits, simulates e-KYC claims extraction, and updates local `PatientProfile` and `User` database records upon successful verification.

### Architectural Role & System Topology
```
           +-----------------------------------------------+
           |       Client / Citizen Portal (POST /otp)     |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |   generate_aadhaar_otp (RSA-OAEP Encrypt)     |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |       AadhaarSessionManager (In-Memory)       |
           |             (10-Minute TTL, 3 Attempts)       |
           +-----------------------------------------------+
                                  |
                   (Citizen Submits 6-digit OTP)
                                  v
           +-----------------------------------------------+
           |   verify_aadhaar_otp -> Demographics Claims   |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |   sync_unified_patient_profile (DB Commit)    |
           +-----------------------------------------------+
```

### Key Import/Export Roster
- **Imports**:
  - `re, uuid, datetime, timezone, timedelta, date`: Standard validation and temporal parsing.
  - `AsyncSession`: Async SQLAlchemy database session.
  - `get_abdm_encryption_manager`: RSA-OAEP SHA-256 demographic encryptor.
  - `PatientProfile, Gender`: ORM models and enums.
  - `AadhaarAddress, AadhaarDemographicData, ...`: Pydantic transfer schemas.
- **Exports**:
  - `validate_verhoeff`: Dihedral D5 checksum verification.
  - `generate_verhoeff`: Calculates check digit for numeric string.
  - `AadhaarSessionManager`, `aadhaar_session_manager`: Ephemeral transaction manager.
  - `generate_aadhaar_otp`: Initiates verification session.
  - `verify_aadhaar_otp`: Verifies OTP and generates auth token.
  - `sync_unified_patient_profile`: Atomically syncs e-KYC claims into PostgreSQL.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Verhoeff Checksum**: Implements the standard dihedral group $D_5$ algorithm (`D_TABLE`, `P_TABLE`, `INV_TABLE`) required by UIDAI to catch transposition and transcription errors in 12-digit Aadhaar numbers.
2. **Session Creation**: Cleans the Aadhaar string, masks it, encrypts the raw Aadhaar payload using RSA-OAEP SHA-256 via `get_abdm_encryption_manager()`, and records an active transaction in memory with a 10-minute TTL.
3. **OTP Verification**: Validates the 6-digit code against maximum allowed attempts (3). Upon success, returns verified demographic claims (name, gender, date of birth, residential address).
4. **Profile Synchronization**: Binds verified claims to an existing `PatientProfile`, updating street address, city, state, pincode, gender enum, and birth date in PostgreSQL.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Hardcoded Master OTP Bypass (CWE-287 / CWE-798)
In line 169:
```python
if otp != "123456" and otp != session["mock_otp"]:
```
The string `"123456"` is hardcoded and unconditionally accepted as valid for every transaction, irrespective of environment settings (`settings.ENVIRONMENT`). If deployed in a production setting, any adversary can authenticate any 12-digit Aadhaar number by supplying `"123456"`, completely bypassing OTP verification.

### Invariant 2: Static Mock Demographics Overwriting Real Patient Records (CWE-489)
In lines 182–202, `verify_otp` unconditionally returns hardcoded mock demographic data:
```python
name="Arun Kumar Patel", address="Flat 402, Shanti Heights... Koramangala 4th Block..."
```
When `sync_unified_patient_profile` is called following verification, it writes these mock values directly into the database. Consequently, any citizen verifying their Aadhaar has their legal name permanently overwritten with "Arun Kumar Patel" and their address set to Koramangala, causing severe clinical record corruption.

### Invariant 3: Omission of Verhoeff Checksum in OTP Generation
Although `validate_verhoeff` is defined (line 55), `generate_aadhaar_otp` (line 218) only verifies `len(clean) != 12`. It never invokes `validate_verhoeff(clean)`. As a result, malformed Aadhaar numbers with invalid check digits are permitted to initiate authentication sessions.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SVC-AOT-F01` | S1 | `[SEC]` | `aadhaar_otp.py:169` | Hardcoded simulation OTP `'123456'` accepted unconditionally, allowing auth bypass in production |
| `BE-SVC-AOT-F02` | S1 | `[QUAL]` | `aadhaar_otp.py:182-202, 272-309` | `verify_otp` returns static mock demographic claims that overwrite real patient data in PostgreSQL |
| `BE-SVC-AOT-F03` | S2 | `[QUAL]` | `aadhaar_otp.py:218-220` | `generate_aadhaar_otp` omits `validate_verhoeff`, accepting numbers with invalid check digits |
| `BE-SVC-AOT-F04` | S2 | `[SEC]` | `aadhaar_otp.py:242` | Returns pseudo-JWT token (`f"nirmaya_aadhaar_auth_jwt_{uuid.uuid4().hex}"`) lacking cryptographic signatures |
| `BE-SVC-AOT-F05` | S3 | `[PERF]` | `aadhaar_otp.py:100` | In-memory session store is not shared across multi-worker ASGI processes |

---

## Layer E: Unapplied Unified Diff Patches for S0–S2 Findings

```diff
--- a/backend/app/services/aadhaar_otp.py
+++ b/backend/app/services/aadhaar_otp.py
@@ -166,7 +166,10 @@
             raise AppException("Maximum OTP verification attempts exceeded. Please generate a new OTP.")
 
-        # Verify OTP (accept standard simulation OTP '123456' or session's mock_otp)
-        if otp != "123456" and otp != session["mock_otp"]:
+        # Verify OTP (strictly guard simulation bypass in non-production environments)
+        is_dev = settings.ENVIRONMENT in ["test", "development", "sandbox"]
+        valid_otp = (otp == session["mock_otp"]) or (is_dev and otp == "123456")
+        if not valid_otp:
             remaining = self.max_attempts - session["attempts"]
             if remaining <= 0:
                 del self._sessions[txn_id]
@@ -218,6 +221,8 @@
     clean = re.sub(r"\D", "", aadhaar_number.strip())
     if len(clean) != 12:
         raise AppException("Aadhaar number must contain exactly 12 numeric digits")
+    if not validate_verhoeff(clean):
+        raise AppException("Aadhaar number failed Verhoeff checksum validation")
 
     txn_id, masked_phone, _ = aadhaar_session_manager.create_session(clean)
```
