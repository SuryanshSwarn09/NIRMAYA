# Technical Audit Report: backend/app/services/abdm_m3_audit.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/abdm_m3_audit.py` provides the integration audit and telemetry compilation service for ABDM Milestone 3 (M3). It synthesizes real-time metrics across HIP and HIU functional stores: tracking consent lifecycle transitions, active Diffie-Hellman cryptographic sessions, outbound AES-256-GCM data transfer volumes and delivery success rates, and HIU incoming bundle decryptions and tamper rejections. The audit identified that all aggregated metrics originate exclusively from transient in-memory stores without persistent storage, meaning telemetry is wiped on process restart, and compliance status is statically asserted as `"ABDM_M3_CERTIFIED"` without dynamic health verification.

### Architectural Roster
- **Module Name:** `backend/app/services/abdm_m3_audit.py`
- **Primary Responsibility:** Aggregation of ABDM M3 operational metrics, compliance reporting, and cryptographic telemetry.
- **Upstream Dependencies:**
  - `app.core.config.settings`
  - `app.schemas.abdm_m3_audit` (`AbdmM3AuditReport`, `ConsentAuditMetrics`, etc.)
  - `app.services.abdm_consent.consent_registry_store`
  - `app.services.abdm_crypto.crypto_session_store`
  - `app.services.abdm_hiu.hiu_record_store`, `hiu_request_store`
  - `app.services.abdm_transfer.transfer_audit_store`
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/abdm_m3_audit.py`
  - Administrative compliance dashboard
- **Exported Symbols:**
  - `ACTIVE_M3_WEBHOOK_LISTENERS`
  - `generate_m3_audit_report`

```
+-----------------------------------------------------------------------------------+
|                        ABDM M3 Telemetry Compilation                              |
|                                                                                   |
|  [Admin / Compliance Monitor]                                                     |
|          |                                                                        |
|          v                                                                        |
|  [generate_m3_audit_report]                                                       |
|          |-- 1. ConsentRegistryStore   --> Granted, Revoked, Expired Counts       |
|          |-- 2. CryptoSessionStore     --> Key Agreements, Active ECDH Sessions   |
|          |-- 3. TransferAuditStore     --> Outbound Transfers, Success Rate %     |
|          |-- 4. HIU Stores             --> Decrypted Bundles, Tamper Rejections   |
|          +--> Compiles AbdmM3AuditReport (Status: ABDM_M3_CERTIFIED)              |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

This module serves as the centralized observability reporting engine for ABDM M3 health data exchanges:

1. **Consent Metrics Compilation:** Queries `consent_registry_store.get_all_consents()`. It iterates over the consent collection, evaluating each record's status. For granted consents, it checks whether the current timestamp exceeds `data_erase_at` to accurately classify active vs. expired authorizations.
2. **Cryptographic Parity Aggregation:** Queries `crypto_session_store` to count active Curve25519 Diffie-Hellman key agreement sessions and total lifetime agreements. It confirms compliance with Curve25519 (X25519), HKDF-SHA256, and AES-256-GCM standards.
3. **Data Transfer Delivery Metrics:** Reads up to 500 records from `transfer_audit_store`. Filters for outbound push records, calculating total batches, successful deliveries, failed deliveries, total records transferred, and percentage delivery rate.
4. **HIU Consumer Metrics:** Reads active sessions and all decrypted bundles from `hiu_request_store` and `hiu_record_store`. Computes counts of encounters, prescriptions, diagnostic reports, and observations imported, alongside total recorded tamper rejections.
5. **Report Serialization:** Packages the sub-metrics into a comprehensive `AbdmM3AuditReport` including facility IDs, standard descriptions, environment tags, and active webhook listener routes.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Compliance Standards
- **Integrity Accounting:** Any cryptographic failure or tag verification mismatch logged during HIU inbound processing must increment the `tamperRejections` metric.
- **Delivery Rate Calculation:** Success rate must accurately reflect $\frac{\text{successful batches}}{\text{total transfers}} \times 100$, defaulting to 100.0% when total transfers is 0 to avoid division by zero.

### Vulnerabilities & Operational Risks
- **Volatile Observability:** Because all underlying audit sources (`TransferAuditStore`, `HIURecordStore`, `CryptoSessionStore`) reside in process RAM without backing database models, restarting the backend service resets all historical counters to zero, distorting audit compliance reports.
- **Static Certification Assertion:** Line 139 unconditionally hardcodes `status="ABDM_M3_CERTIFIED"` and 100% parity/integrity scores, even if multiple transfer failures or tamper rejections occurred during the auditing period.
- **Buffer Truncation:** `transfer_audit_store.get_records(limit=500)` caps metrics computation to the most recent 500 transfer events. Under high clinical loads, historical transfer rates are distorted.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-M3A-F01` | **S2** | `[QUAL]` | `abdm_m3_audit.py:46-130` | Observability metrics aggregate purely ephemeral in-memory state; audit history is lost upon server restart. |
| `BE-SVC-M3A-F02` | **S2** | `[QUAL]` | `abdm_m3_audit.py:139, 148` | Compliance status `"ABDM_M3_CERTIFIED"` and 100% integrity scores are statically hardcoded rather than dynamically evaluated against operational health. |
| `BE-SVC-M3A-F03` | **S3** | `[PERF]` | `abdm_m3_audit.py:88` | Hardcoded 500-record limit on transfer audit retrieval distorts lifetime delivery statistics in high-throughput production environments. |
| `BE-SVC-M3A-F04` | **S4** | `[DOC]` | `abdm_m3_audit.py:31-38` | `ACTIVE_M3_WEBHOOK_LISTENERS` is a static list that is not verified against registered FastAPI route handlers at runtime. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Dynamic Certification Health Status (`BE-SVC-M3A-F02`)

```diff
--- a/backend/app/services/abdm_m3_audit.py
+++ b/backend/app/services/abdm_m3_audit.py
@@ -133,9 +133,16 @@ def generate_m3_audit_report() -> AbdmM3AuditReport:
     env = getattr(settings, "ENVIRONMENT", "sandbox")
+
+    # Dynamically determine certification health status based on delivery rate & errors
+    is_healthy = transfer_metrics.deliverySuccessRatePercentage >= 95.0 and hiu_metrics.tamperRejections == 0
+    report_status = "ABDM_M3_CERTIFIED" if is_healthy else "ABDM_M3_DEGRADED"
 
     return AbdmM3AuditReport(
         hipId=hip_id,
         hiuId=hiu_id,
         gatewayConsentManagerId="sbx",
-        status="ABDM_M3_CERTIFIED",
+        status=report_status,
         milestone="Milestone 3: Health Information Exchange & Consent Management",
```
