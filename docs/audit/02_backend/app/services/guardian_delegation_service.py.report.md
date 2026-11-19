# Codebase Technical Audit Report: `backend/app/services/guardian_delegation_service.py`

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`guardian_delegation_service.py` manages electronic consent artifact delegation, ephemeral scoped proxy token issuance, and zero-contamination clinical record ingestion under Ayushman Bharat Digital Mission (ABDM) Milestone M3 and Digital Personal Data Protection (DPDP) Act 2023 Section 9. It provides the authorization bridge between a verified legal guardian (parent/proxy) and third-party Health Information Users (HIUs) requesting medical records of dependent minors or senior citizens.

### System Topology & Token Flow
```
   [ Health Information User (HIU) ]
                 |
   (ABDM Consent Request req-abdm-*)
                 v
   [ GuardianDelegationService ] <---> [ FamilyProxyService ]
                 |                       (Authority Verification)
                 |
         +-------+-------+
         |               |
         v               v
   [ Consent Grant ]   [ Scoped Proxy Token ]
   - SHA-256 Sig       - Bearer eyJh_...
   - Temporal Bounds   - Specific Scope & TTL
   - Zero-Contam Flag  - Zero-Contamination Isolated
```

### Module Metadata & Imports/Exports
- **Module Path:** `backend/app/services/guardian_delegation_service.py`
- **Component Classification:** ABDM Consent Intermediary & Scoped Token Issuer
- **Lines of Code:** 284 LOC
- **Imports:** `hashlib`, `uuid`, `datetime`, `typing`, `app.schemas.guardian_delegation.*`, `app.services.family_proxy_service.family_proxy_service`
- **Primary Export:** `guardian_delegation_service` (Global Singleton Instance)

---

## Layer B: Plain-Language Developer Walkthrough

The service handles three core clinical workflows:
1. **Granting Delegated Consent (`grant_delegated_consent`)**: When an inbound ABDM consent request arrives for a dependent, a legal guardian reviews it. The service validates that:
   - The guardian's digital attestation flag is provided.
   - `family_proxy_service` confirms active legal proxy authority between the guardian and dependent.
   - The requested date range is topologically consistent (`from <= to`) and the expiration timestamp is strictly in the future.
   It then mints an electronic consent artifact with a deterministic SHA-256 signature hash and records the transaction in an audit trail.
2. **Revoking Delegated Consent (`revoke_delegated_consent`)**: Under DPDP Act Sec 9, a guardian can unilaterally withdraw permission. The service validates actor authorization, switches the status to `REVOKED`, and logs the revocation rationale.
3. **Minting Scoped Proxy Bearer Tokens (`generate_scoped_proxy_token`)**: For direct API access to dependent records, guardians request scoped tokens. The service verifies legal delegation and issues an ephemeral bearer string with a specified TTL and purpose scope (e.g., `records:view:pediatric`).

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Zero-Contamination Clinical Ingestion
When proxy consent is granted or tokens are minted, clinical records must remain strictly isolated within the dependent's vault without mixing into the guardian's personal health record (zero contamination). The service tags all emitted artifacts with `zero_contamination_verified=True` and `zero_contamination_isolated=True`.

### Invariant 2: Temporal Bound Invariant
To prevent unbounded data exfiltration, the service strictly enforces temporal ranges:
$$\text{date\_range\_from} \le \text{date\_range\_to} \quad \land \quad \text{expiry\_date} > T_{\text{current\_utc}}$$
Artifacts violating these bounds are rejected immediately at line 114.

### Invariant 3: Proxy Token Scoping & Non-Reusability
Proxy bearer tokens are bound to a single guardian-dependent pair and a restricted scope. A token generated for `pat-aarav-sharma-02` cannot be used to query endpoints for `pat-kavita-sharma-03`.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
|---|---|---|---|---|
| `BE-SVC-GDL-F01` | **S1** | `[SEC]` | `backend/app/services/guardian_delegation_service.py:27-32` | In-Memory Storage for ABDM Consent Artifacts, Delegated Consents, and Audit Trail. All consent authorizations, proxy tokens, and forensic records are volatile in RAM. Loss of records during restart violates DPDP Act Sec 9 statutory requirements. |
| `BE-SVC-GDL-F02` | **S1** | `[SEC]` | `backend/app/services/guardian_delegation_service.py:198-216` | Scoped Proxy Token Generation uses Pseudo-Random UUID Hex String Formatting (`nirmaya_proxy_eyJh_{token_uuid[:16]}.{req.requested_scope}.{token_uuid[16:]}`) instead of Cryptographically Signed Asymmetric JWT / Ed25519 Tokens. Token cannot be cryptographically verified statelessly by downstream microservices; tokens are stored in an unpruned in-memory dictionary. |
| `BE-SVC-GDL-F03` | **S2** | `[SEC]` | `backend/app/services/guardian_delegation_service.py:149, 183, 225` | Audit Trail Hardcodes IP Address to `"127.0.0.1"`. Bypasses real forensic network logging for consent grant and revocation actions, invalidating non-repudiation audit requirements. |
| `BE-SVC-GDL-F04` | **S2** | `[QUAL]` | `backend/app/services/guardian_delegation_service.py:101-105` | Signature Attestation is a Unvalidated Boolean Flag (`req.guardian_signature_attestation: bool`) with no verification of Aadhaar eSign or DSC certificate chain. |
| `BE-SVC-GDL-F05` | **S3** | `[PERF]` | `backend/app/services/guardian_delegation_service.py:260-280` | Linear Scan without Indexing for Listing Consents and Filtering Audit Trails. |
| `BE-SVC-GDL-F06` | **S4** | `[DOC]` | `backend/app/services/guardian_delegation_service.py:18-24` | Missing Documentation on ABDM Consent Manager (CM) Gateway Callbacks (`/v0.5/consents/on-init`, `/v0.5/consent-requests/on-status`). |

---

## Layer E: Unapplied Unified Diff Patches

### Patch 1: Capture Client IP Address in Forensic Audit Trail (`BE-SVC-GDL-F03`)
```diff
--- a/backend/app/services/guardian_delegation_service.py
+++ b/backend/app/services/guardian_delegation_service.py
@@ -100,2 +100,3 @@ class GuardianDelegationService:
-    def grant_delegated_consent(self, req: DelegatedConsentGrantRequest) -> DelegatedConsentArtifactResponse:
+    def grant_delegated_consent(
+        self, req: DelegatedConsentGrantRequest, client_ip: str = "UNKNOWN"
+    ) -> DelegatedConsentArtifactResponse:
@@ -148,3 +149,3 @@ class GuardianDelegationService:
                 timestamp=now_utc,
-                ip_address="127.0.0.1",
+                ip_address=client_ip,
                 status="SUCCESS",
```

### Patch 2: Enforce Proper Token Expiry Pruning (`BE-SVC-GDL-F02`)
```diff
--- a/backend/app/services/guardian_delegation_service.py
+++ b/backend/app/services/guardian_delegation_service.py
@@ -204,4 +204,11 @@ class GuardianDelegationService:
         now_utc = datetime.now(timezone.utc)
 
+        # Prune expired tokens before adding new entry
+        expired_keys = [
+            k for k, v in self._scoped_tokens.items()
+            if (now_utc - v["issued_at"]).total_seconds() > v["duration"]
+        ]
+        for k in expired_keys:
+            del self._scoped_tokens[k]
+
         self._scoped_tokens[token_str] = {
```
