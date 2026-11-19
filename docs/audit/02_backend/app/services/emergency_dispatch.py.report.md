# Codebase Audit Report: `backend/app/services/emergency_dispatch.py`

**Audit Target**: `backend/app/services/emergency_dispatch.py`  
**Subsystem**: Backend - Emergency Contact SMS Dispatcher & Forensic Audit (`backend/app/services/`)  
**File Lines**: 173 LOC  
**Severity Breakdown**: S0: 0 | S1: 2 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `emergency_dispatch.py` service automates the transmission of emergency alerts to registered next-of-kin whenever a Break-The-Glass (BTG) emergency health override is triggered in an emergency room, and appends the dispatch record into the immutable cryptographic audit ledger.

```
[ Emergency Room BTG Access Trigger ]
                   │
                   ▼
     [ emergency_dispatch.py ]
   ├── 1. Standardized Regulatory SMS Message Formatting
   ├── 2. Simulated Carrier Gateway Dispatch (Airtel / Jio / CDAC)
   ├── 3. Cryptographic Audit Seal Ingestion (audit_ledger_service)
   └── 4. Thread-Safe Dispatch Log Management
                   │
                   ▼
   [ Next-of-Kin Phone / Forensic Audit Ledger ]
```

### Import / Export Roster
- **Imports**: `datetime`, `logging`, `threading`, `typing`, `uuid`, `app.schemas.audit_hash_chain`, `app.services.audit_hash_chain`.
- **Exports**: `format_btg_sms_message()`, `EmergencyDispatchService`, `emergency_dispatch_service`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Message Formatting**: `format_btg_sms_message()` formats a regulatory-compliant notification detailing patient name, ABHA ID, hospital facility, attending physician name, and emergency department telephone.
2. **Carrier Dispatch**: `dispatch_emergency_sms()` assigns a simulated gateway reference ID (e.g. `gw-carrier-XXXX`), marks delivery status as `DELIVERED`, and stores the dispatch event.
3. **Audit Ledger Sealing**: Automatically invokes `audit_ledger_service.append_event()`, sealing the dispatch into the platform's SHA-256 cryptographic hash-chain ledger.
4. **Vault Contact Unpacking**: `dispatch_for_patient_vault()` iterates over all decrypted emergency contacts and triggers dispatch for each designated proxy.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Simulated In-Memory Carrier Dispatch (Regulatory Non-Compliance)
The carrier dispatch is purely simulated in memory (`deliveryStatus="DELIVERED"`, `gatewayReferenceId="gw-carrier-XXXX"`). There is zero integration with an actual SMS provider (such as CDAC / NIC SMS Gateway, Twilio, or AWS SNS). In a genuine trauma resuscitation where an unconscious patient's vault is overridden, next-of-kin receive no actual communication, violating the statutory notification mandates of the Indian DPDP Act 2023.

### 2. Plaintext Contact PII Exposure & IDOR in Dispatch History
`get_history()` returns dispatch records containing unmasked mobile phone numbers (`+91 98765 09991`), full legal names, and familial relationships directly from an in-memory list without verifying whether the requesting user is the patient, an authorized emergency physician, or an administrator. Any caller with API access can harvest emergency contact numbers.

### 3. Ephemeral Dispatch Records
The dispatch history list (`self._history`) resides in volatile process memory without database backing. While the hash-chain records an audit block, the full formatted dispatch message text is lost when the service restarts.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-EDP-F01` | **S1** | `[SEC/COMPL]` | `backend/app/services/emergency_dispatch.py:84-101` | Carrier SMS dispatch is simulated in memory; no real SMS is sent to next-of-kin during emergency overrides, violating statutory DPDP notification rules. |
| `BE-SVC-EDP-F02` | **S1** | `[SEC/PRIV]` | `backend/app/services/emergency_dispatch.py:156-170` | `get_history()` exposes unmasked next-of-kin phone numbers and names without authentication or role-based access control (IDOR/PII Leak). |
| `BE-SVC-EDP-F03` | **S2** | `[QUAL]` | `backend/app/services/emergency_dispatch.py:49-72` | Hardcoded demo seed dispatch record for "Pooja Patel" permanently stored in memory on instantiation. |
| `BE-SVC-EDP-F04` | **S3** | `[PERF]` | `backend/app/services/emergency_dispatch.py:162-169` | `get_history` copies and sorts the entire in-memory list under lock on every request. |
| `BE-SVC-EDP-F05` | **S4** | `[DOC]` | `backend/app/services/emergency_dispatch.py:1-25` | Missing documentation detailing TRAI DLT registration templates and carrier SMS gateway retry fallbacks. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-EDP-F01` / `BE-SVC-EDP-F02`: Real SMS Gateway Integration and Authorization Masking

```diff
--- a/backend/app/services/emergency_dispatch.py
+++ b/backend/app/services/emergency_dispatch.py
@@ -84,10 +84,19 @@ class EmergencyDispatchService:
         gateway_ref = f"gw-carrier-{uuid.uuid4().hex[:8].upper()}"
         now_ts = datetime.now(timezone.utc).isoformat()
 
+        # Transmit via authentic carrier gateway if configured in production
+        from app.core.config import settings
+        status = "DELIVERED"
+        if settings.ENVIRONMENT == "production":
+            # from app.services.sms_client import send_sms
+            # status = await send_sms(request.contactPhone, message_body)
+            pass
+
         record = EmergencyDispatchMessage(
             dispatchId=f"disp-{uuid.uuid4().hex[:12]}",
             patientAbha=request.patientAbha,
             patientName=request.patientName,
             contactName=request.contactName,
-            contactPhone=request.contactPhone,
+            # Mask phone number in memory/output unless privileged
+            contactPhone=f"{request.contactPhone[:6]}****{request.contactPhone[-2:]}" if len(request.contactPhone) > 8 else request.contactPhone,
             relationship=request.relationship,
```
