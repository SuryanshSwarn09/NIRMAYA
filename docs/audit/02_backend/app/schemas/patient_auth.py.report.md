# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/patient_auth.py`
**Audited Path:** `backend/app/schemas/patient_auth.py`  
**Module:** `backend` | **Subsystem:** Unified Passwordless Patient Authentication & SIM Fallback Gateway  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/patient_auth.py` defines the Pydantic v2 schemas for NIRMAYA's unified passwordless patient authentication gateway. Enabling friction-free citizen onboarding through Government of India Digital Public Infrastructure (DPI), this module processes verified demographic claims from:
- DigiLocker OAuth2 PKCE authorization exchanges.
- Aadhaar direct OTP demographic verification (`aadhaar_otp`).
- Active SIM mobile fallback login (`mobile_fallback`) for citizens whose current mobile number differs from their historical Aadhaar-registered SIM.
- 30-day extended session token issuance and ABHA identifier binding (`PatientUnifiedAuthResponse`).

#### 2. Key Components & Class Roster
- `PatientUnifiedAuthRequest`: Inbound payload ingesting verified identity claims from DigiLocker, Aadhaar OTP, or mobile fallback, specifying patient legal name, gender, date of birth, masked Aadhaar (`XXXX-XXXX-4821`), active mobile, email, address components (district, state, pincode), transaction UUID (`txn_id`), and 30-day extended session flags (`remember_me`).
- `PatientMobileFallbackLoginRequest`: Fallback authentication request for patients needing active SIM verification with 6-digit OTP and optional ABHA identifier lookup.
- `PatientUnifiedAuthResponse`: Master authentication response returning JWT Bearer access token, expiration duration in seconds, new-user registration indicator, patient profile UUID, user UUID, certified name, masked Aadhaar, 14-digit ABHA number, and `@abdm` handle.

---

### Layer B: Plain-Language Developer Walkthrough

Most citizens in India do not want to remember another complex password just to book a doctor's appointment or view their lab results. Instead, NIRMAYA allows citizens to log in passwordlessly using their government-verified digital identities: either by authenticating through DigiLocker or by entering their Aadhaar number and receiving a one-time password (OTP). Furthermore, if a citizen changed their SIM card years ago and cannot receive Aadhaar SMS, the system provides a smart "mobile fallback" channel.

`patient_auth.py` defines the technical contracts for this passwordless front door:
1. When a citizen verifies their identity via DigiLocker or Aadhaar OTP, the frontend packages their verified demographic claims into a `PatientUnifiedAuthRequest`.
2. The backend provisions or fetches their account and returns a `PatientUnifiedAuthResponse` containing their cryptographic JWT bearer token and linked ABHA details.
3. If they select "Remember Me", the token is configured with a 30-day extended validity window (`expires_in_seconds = 2592000`), allowing patients to quickly access their medical records without having to re-authenticate on every visit.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **Multi-Source Discrimination:** `source: Literal["digilocker", "aadhaar_otp", "mobile_fallback"]` restricts authentication channels to sanctioned DPI verification pathways.
- **Friction-Free Onboarding:** Automatically indicates whether the login triggered a fresh profile registration via `is_new_user: bool`.
- **Consistent Pydantic v2 Configuration:** Uses `model_config = ConfigDict(from_attributes=True)` across all request and response envelopes.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Active Access Tokens and Live Verification OTPs Leaked in Repr (`BE-SCH-PAU-F01`)
- **Severity:** S1 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/patient_auth.py:39, 49`
- **Description:** `PatientMobileFallbackLoginRequest.otp` and `PatientUnifiedAuthResponse.access_token` are declared as plain `str` fields without `repr=False` or `SecretStr`. When authentication payloads or gateway responses are logged during debugging or API gateway request logging, live 6-digit verification OTPs and active 30-day JWT bearer access tokens are written in plaintext to server logs.
- **Impact:** Critical credential leakage allowing session hijacking and unauthorized access to patient medical records (CWE-532 / CWE-312).
- **Remediation:** Annotate `otp` and `access_token` with `repr=False`.

##### Vulnerability 2: Missing Indian Mobile Number and PIN Code Format Constraints (`BE-SCH-PAU-F02`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/patient_auth.py:21, 27, 38`
- **Description:** `mobile_number` in both models is typed as an unconstrained string without regex validation, and `pincode` in `PatientUnifiedAuthRequest` lacks Indian 6-digit PIN code regex validation (`pattern=r"^[1-9][0-9]{5}$"`). Non-numeric or invalid mobile numbers can pass validation into the database.
- **Impact:** Malformed SMS gateway dispatches and unformatted database records.
- **Remediation:** Enforce `pattern=r"^[6-9]\d{9}$"` on mobile numbers and `pattern=r"^[1-9][0-9]{5}$"` on postal PIN codes.

##### Vulnerability 3: Patient Demographic Name Unmasked in Repr (`BE-SCH-PAU-F03`)
- **Severity:** S2 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/patient_auth.py:14, 56`
- **Description:** `name` in `PatientUnifiedAuthRequest` and `PatientUnifiedAuthResponse` is an unmasked string without `repr=False`. When authentications are logged, citizen full legal names are exposed in cleartext in server logs.
- **Impact:** Leaks patient Personally Identifiable Information (PII) in log aggregators (CWE-532).
- **Remediation:** Annotate `name` with `repr=False`.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-PAU-F01` | S1 | `[SEC]` | `patient_auth.py:39, 49` | Active JWT access token and live verification OTP unmasked in string `repr` |
| `BE-SCH-PAU-F02` | S2 | `[QUAL]` | `patient_auth.py:21, 27, 38` | `mobile_number` and `pincode` lack standard Indian regex validation |
| `BE-SCH-PAU-F03` | S2 | `[SEC]` | `patient_auth.py:14, 56` | Citizen legal demographic name unmasked in string `repr` |
| `BE-SCH-PAU-F04` | S3 | `[QUAL]` | `patient_auth.py:51` | `expires_in_seconds` lacks `gt=0` strict positive integer constraint |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/patient_auth.py
+++ b/backend/app/schemas/patient_auth.py
@@ -14,5 +14,5 @@ class PatientUnifiedAuthRequest(BaseModel):
-    name: str = Field(description="Certified legal full name", example="Arun Kumar Patel")
+    name: str = Field(repr=False, description="Certified legal full name", example="Arun Kumar Patel")
     gender: Optional[str] = Field(default="other", description="Gender: male | female | other")
     date_of_birth: Optional[str] = Field(default=None, description="Date of birth YYYY-MM-DD")
     masked_aadhaar: Optional[str] = Field(
         default=None,
@@ -21,7 +21,7 @@ class PatientUnifiedAuthRequest(BaseModel):
-    mobile_number: Optional[str] = Field(default=None, description="Active mobile number if provided")
+    mobile_number: Optional[str] = Field(default=None, pattern=r"^[6-9]\d{9}$", description="Active mobile number if provided")
     email: Optional[str] = Field(default=None, description="Contact email if provided")
 
     formatted_address: Optional[str] = Field(default=None, description="Formatted residential address")
     district: Optional[str] = Field(default=None, description="District or City")
     state: Optional[str] = Field(default=None, description="State or Union Territory")
-    pincode: Optional[str] = Field(default=None, description="6-digit postal PIN code")
+    pincode: Optional[str] = Field(default=None, pattern=r"^[1-9][0-9]{5}$", description="6-digit postal PIN code")
 
@@ -38,3 +38,3 @@ class PatientMobileFallbackLoginRequest(BaseModel):
-    mobile_number: str = Field(description="10-digit Indian mobile number", example="9876543210")
-    otp: str = Field(description="6-digit verification OTP", example="123456")
+    mobile_number: str = Field(pattern=r"^[6-9]\d{9}$", description="10-digit Indian mobile number", example="9876543210")
+    otp: str = Field(repr=False, description="6-digit verification OTP", example="123456")
     abha_identifier: Optional[str] = Field(default=None, description="Optional ABHA Number or @abdm handle")
@@ -49,3 +49,3 @@ class PatientUnifiedAuthResponse(BaseModel):
-    access_token: str = Field(description="JWT Bearer access token")
+    access_token: str = Field(repr=False, description="JWT Bearer access token")
     token_type: str = Field(default="bearer", description="Token scheme")
-    expires_in_seconds: int = Field(description="Token expiry window in seconds (e.g. 2592000 for 30 days)")
+    expires_in_seconds: int = Field(gt=0, description="Token expiry window in seconds (e.g. 2592000 for 30 days)")
     is_new_user: bool = Field(description="Whether a new patient profile was created")
@@ -56,3 +56,3 @@ class PatientUnifiedAuthResponse(BaseModel):
-    name: str = Field(description="Patient legal name")
+    name: str = Field(repr=False, description="Patient legal name")
     masked_aadhaar: Optional[str] = Field(default=None, description="Masked Aadhaar representation")
```
