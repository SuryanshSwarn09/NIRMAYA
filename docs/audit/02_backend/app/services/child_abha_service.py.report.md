# Codebase Audit Report: `backend/app/services/child_abha_service.py`

**Audit Target**: `backend/app/services/child_abha_service.py`  
**Subsystem**: Backend - ABDM Child ABHA & Pediatric Governance (`backend/app/services/`)  
**File Lines**: 206 LOC  
**Severity Breakdown**: S0: 0 | S1: 1 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `child_abha_service.py` module manages the generation, verification, and linkage of Child ABHA accounts (for minors under 18) under the ABDM framework, delegating consent and operational management to verified parents or legal guardians.

```
[ Guardian Mobile App / Portal ]
                │
                ▼ (Child Enrollment: Parent ABHA + Child Demographics)
   [ child_abha_service.py Engine ]
        ├── 1. Guardian Aadhaar OTP Verification
        ├── 2. Minor Age Validation (< 18 years)
        ├── 3. Child ABHA 14-Digit Generation (ABDM Format)
        ├── 4. Guardian Proxy Delegation Binding
        └── 5. In-Memory Registry vs DB Persistence
                │
                ▼
   [ ChildABHAResponse / Virtual ABHA Card ]
```

### Import / Export Roster
- **Imports**: `datetime`, `logging`, `typing`, `uuid`, `app.core.exceptions`, `app.schemas.child_abha`.
- **Exports**: `ChildABHAService`, `child_abha_service`, `create_child_abha()`, `verify_guardian_otp()`, `get_child_records()`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Enrollment Initiation**: Guardian initiates child ABHA creation by providing their own verified ABHA identifier, the child's name, gender, date of birth, and relation.
2. **Guardian OTP Authentication**: The service issues an OTP to the guardian's registered mobile number or Aadhaar.
3. **Child ABHA Generation**: Generates a 14-digit ABHA number (`XX-XXXX-XXXX-XXXX`) and an ABHA address (`<child_name><suffix>@abdm`).
4. **Proxy Linkage**: Associates the child's profile with the guardian's profile, granting the parent proxy access to view lab reports, vaccination schedules, and consultations.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Hardcoded Static OTP & Fake ABHA Minting
At lines 51 and 105, the OTP verification is hardcoded to accept `"123456"`. Furthermore, the 14-digit ABHA number is generated using `random.randint` without calculating the official Verhoeff check digit required by the National Health Authority (NHA). This allows unauthorized callers to mint counterfeit Child ABHAs without communicating with the NHA Sandbox or Production Gateway.

### 2. Ephemeral Storage & Missing Database Records
The enrolled child records and guardian linkages are stored in an in-memory dictionary (`self._child_records: Dict[str, dict] = {}`). No `PatientProfile`, `User`, or `FamilyProxy` records are inserted into PostgreSQL. Upon server restart, all pediatric enrollments and guardian proxy delegations vanish, severing care access for minors.

### 3. Guardianship Document Validation Omission
The service does not validate birth certificate numbers, hospital discharge summaries, or legal guardianship affidavits. Anyone possessing a valid adult ABHA can unilaterally register arbitrary minor identities and claim legal guardianship without proof.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-CABH-F01` | **S1** | `[SEC/MED]` | `backend/app/services/child_abha_service.py:51, 105` | Hardcoded static OTP `"123456"`, pseudo-random ABHA generation without Verhoeff check digit, and ephemeral in-memory storage without PostgreSQL persistence. |
| `BE-SVC-CABH-F02` | **S2** | `[SEC/QUAL]` | `backend/app/services/child_abha_service.py:120-145` | Missing guardianship verification or birth certificate proof, enabling unauthorized proxy claims over minors. |
| `BE-SVC-CABH-F03` | **S3** | `[QUAL]` | `backend/app/services/child_abha_service.py:70-85` | Incomplete age validation allows enrolling individuals older than 18 under child proxy status. |
| `BE-SVC-CABH-F04` | **S4** | `[DOC]` | `backend/app/services/child_abha_service.py:1-30` | Absence of documentation regarding child consent transition upon reaching majority (18 years of age). |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-CABH-F01`: Verhoeff Check Digit Enforcement & NHA Gateway Integration

```diff
--- a/backend/app/services/child_abha_service.py
+++ b/backend/app/services/child_abha_service.py
@@ -48,9 +48,15 @@ class ChildABHAService:
     async def verify_guardian_otp(self, txn_id: str, otp: str) -> bool:
         """Verify OTP sent to guardian registered mobile."""
-        if otp == "123456":
-            return True
-        return False
+        # Disallow hardcoded static OTP in non-test environments
+        from app.core.config import settings
+        if settings.ENVIRONMENT == "production":
+            # Delegate to authentic Aadhaar / ABDM OTP validation
+            from app.services.aadhaar_otp import aadhaar_otp_service
+            return await aadhaar_otp_service.verify_otp(txn_id, otp)
+        return otp == "123456" and settings.DEBUG
 
     def _generate_abha_number(self) -> str:
-        raw = "".join([str(random.randint(0, 9)) for _ in range(14)])
-        return f"{raw[:2]}-{raw[2:6]}-{raw[6:10]}-{raw[10:]}"
+        # Integrate NHA Verhoeff checksum algorithm for 14-digit identifier
+        from app.services.abdm_issuance import generate_verhoeff_abha
+        return generate_verhoeff_abha()
```
