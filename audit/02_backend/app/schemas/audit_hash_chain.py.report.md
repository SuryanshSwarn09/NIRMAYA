# Audit Report: backend/app/schemas/audit_hash_chain.py

**Path:** `backend/app/schemas/audit_hash_chain.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 135 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic validation schemas for NIRMAYA's immutable cryptographic audit hash-chain ledger, Merkle chain verification, emergency contact SMS dispatching, and high-concurrency WebSocket stress telemetry.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** Cryptographic SHA-256 hash fields (`previousHash`, `payloadDigest`, `blockHash`, `genesisHash`, `latestHash`) are defined as unconstrained strings without regex validation enforcing 64-character hexadecimal digests, permitting truncated or malformed hashes into forensic ledger blocks.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In critical healthcare operations, system audits must be cryptographically tamper-evident: if a rogue administrator or compromised database modifies a patient record or access log, the forensic hash chain must break mathematically. Additionally, emergency clinical events (such as Break-The-Glass emergency access or critical laboratory panic values) require instant SMS notification dispatch to next of kin, and high-concurrency event broadcasting across WebSocket clients must be continuously monitored. This file structures the blockchain-like audit blocks, chain integrity reports, emergency dispatch payloads, and concurrency metrics.

### How it works, step by step
1. `AuditEventType` classifies sensitive operations (`SYSTEM_GENESIS`, `EMERGENCY_BTG_ACCESS`, `LAB_PANIC_ACK`, `PHI_RECORD_EXPORT`, `CONSENT_REVOCATION`, etc.).
2. `AuditBlock` represents a sealed ledger block containing a monotonically increasing index, previous block hash, timestamp, actor identity, payload digest, and cryptographic block hash.
3. `AuditAppendRequest` accepts an arbitrary structured payload along with actor metadata to compute the next block seal.
4. `AuditChainVerificationResult` reports whether the entire ledger from Genesis to Head is unbroken, flagging the exact index of any tampered block.
5. `EmergencyDispatchMessage` and `EmergencyDispatchTestRequest` model emergency SMS notifications dispatched to patient next of kin during acute triage.
6. `ConcurrencyBenchmarkMetrics` tracks WebSocket broadcast fan-out metrics (concurrent clients, p99 latency, packet loss).

### Concepts and patterns used
- *Cryptographic Hash Chaining:* Sequential SHA-256 block linking providing immutable forensic non-repudiation.
- *Merkle Ledger Verification:* End-to-end traversal confirming mathematical integrity of audit blocks.
- *Emergency Break-The-Glass (BTG) Notification:* Automated communication workflows dispatched during emergency clinical overrides.

### Key lines to read first
- `audit_hash_chain.py:18-29`: `AuditEventType` event classifications.
- `audit_hash_chain.py:31-46`: `AuditBlock` cryptographic block schema.
- `audit_hash_chain.py:62-76`: `AuditChainVerificationResult` integrity verification output.
- `audit_hash_chain.py:79-102`: `EmergencyDispatchMessage` emergency SMS notification model.

### How to change it safely
When adding new auditable operations, register them in `AuditEventType`. Never modify the signature of `previousHash` or `blockHash` without ensuring synchronization with the hash computation logic in `audit_hash_chain_service.py`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `enum` (Enum), `typing` (Any, Dict, List, Optional), `uuid`, `pydantic` (BaseModel, ConfigDict, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/audit_hash_chain_service.py`, `backend/app/api/v1/endpoints/audit_hash_chain.py`.
- **Public Surface:** Enum `AuditEventType`; Models `AuditBlock`, `AuditAppendRequest`, `AuditChainVerificationResult`, `EmergencyDispatchMessage`, `EmergencyDispatchTestRequest`, `ConcurrencyBenchmarkMetrics`.

### 2. Security [SEC]
- **Unvalidated SHA-256 Digest Format (`BE-SCH-AHC-F01`):** In `AuditBlock.previousHash`, `AuditBlock.blockHash`, `AuditBlock.payloadDigest`, and `AuditChainVerificationResult.genesisHash`, fields are typed as plain `str` without regex validation (`pattern=r"^[a-fA-F0-9]{64}$"`). Non-hex strings or truncated digests pass validation, compromising cryptographic verification guarantees.
- **Cleartext Emergency Phone & Triage PII (`BE-SCH-AHC-F02`):** In `EmergencyDispatchMessage` (lines 89, 93) and `EmergencyDispatchTestRequest`, `contactPhone`, `departmentPhone`, and `messageText` are plain strings without `repr=False`. Emergency notification models printed in application logs expose citizen phone numbers and sensitive medical triage disclosures.

### 3. Code quality [QUAL]
- **String Types for Timestamps (`BE-SCH-AHC-F03`):** `AuditBlock.timestamp`, `AuditChainVerificationResult.verifiedAt`, `EmergencyDispatchMessage.dispatchTimestamp`, and `ConcurrencyBenchmarkMetrics.timestamp` use `str` with `isoformat()` factory rather than standard `datetime` objects.
- Clean separation between block storage representations and append requests.

### 4. AI-generated-code smells [QUAL]
- Hardcoded hospital `"AIIMS New Delhi - Apex Trauma Center"` and physician `"Dr. Ananya Sharma"` in `EmergencyDispatchTestRequest` defaults (`BE-SCH-AHC-F04`).

### 5. Performance [PERF]
- Payload digest (`payloadDigest`) decouples heavy transaction data from the core block chain, keeping block headers small and hash verification fast.

### 6. Error handling & edge cases
- `AuditChainVerificationResult` gracefully returns `tamperedBlockIndex` and `tamperingReason` without throwing exceptions when corrupted blocks are discovered.

### 7. Doc accuracy [DOC]
- Aligns with DISHA 2018 and DPDP Act 2023 forensic audit trail mandates.

### 8. Tests
- Covered by `backend/tests/test_audit_hash_chain.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-AHC-F01 | S2 | [QUAL] | 36, 43, 44, 67, 68 | Unvalidated SHA-256 digest format in audit blocks | `previousHash: str`, `blockHash: str` without constraints | Add regex pattern `^[a-f0-9]{64}$` |
| BE-SCH-AHC-F02 | S2 | [SEC] | 89, 93, 94 | Personal phone numbers and emergency text unmasked in `repr` | `contactPhone: str`, `messageText: str` | Add `repr=False` to prevent log leakage |
| BE-SCH-AHC-F03 | S3 | [QUAL] | 37, 71, 97, 130 | Timestamps typed as raw ISO strings | Uses `str` with `isoformat()` default factory | Use standard `datetime` with UTC factory |
| BE-SCH-AHC-F04 | S4 | [QUAL] | 113-115 | Hardcoded mock facility and clinician in test request | `hospitalName: default="AIIMS..."` | Move defaults to test fixture configurations |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-AHC-F01 · Risk: Low · [UNTESTED]
Add SHA-256 pattern validation to cryptographic audit blocks:

```diff
--- a/backend/app/schemas/audit_hash_chain.py
+++ b/backend/app/schemas/audit_hash_chain.py
@@ -35,3 +35,3 @@ class AuditBlock(BaseModel):
     blockId: str = Field(description="Unique block identifier")
-    previousHash: str = Field(description="SHA-256 hash digest of the preceding block in the chain")
+    previousHash: str = Field(pattern=r"^[a-fA-F0-9]{64}$", description="SHA-256 hash digest of preceding block")
     timestamp: str = Field(description="ISO 8601 UTC timestamp of block creation")
@@ -42,4 +42,4 @@ class AuditBlock(BaseModel):
     patientAbha: Optional[str] = Field(default=None, description="Subject patient ABHA identifier if applicable")
-    payloadDigest: str = Field(description="SHA-256 digest of the structured transaction payload")
-    blockHash: str = Field(description="Cryptographic SHA-256 seal of this block")
+    payloadDigest: str = Field(pattern=r"^[a-fA-F0-9]{64}$", description="SHA-256 digest of payload")
+    blockHash: str = Field(pattern=r"^[a-fA-F0-9]{64}$", description="Cryptographic SHA-256 seal")
