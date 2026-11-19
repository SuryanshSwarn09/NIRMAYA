# Technical Audit Report: backend/app/services/audit_hash_chain.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/audit_hash_chain.py` implements the Immutable Cryptographic Audit Hash-Chain Ledger Service for NIRMAYA. It establishes an append-only, tamper-evident forensic ledger where each audit event block is cryptographically bound to its predecessor via SHA-256 back-pointers. It includes an automated chain traversal algorithm that mathematically verifies hash continuity and detects retroactive mutations. The audit uncovered a critical **S1** vulnerability: despite claiming to be an "immutable forensic ledger", all audit blocks are stored exclusively in an in-memory Python list (`self._chain`) without PostgreSQL persistence, meaning all historical forensic audit events are erased whenever the server process restarts.

### Architectural Roster
- **Module Name:** `backend/app/services/audit_hash_chain.py`
- **Primary Responsibility:** Append-only SHA-256 hash-chaining of clinical security events, block hashing, and cryptographic integrity verification.
- **Upstream Dependencies:**
  - `hashlib`, `json`, `threading`, `uuid`
  - `app.schemas.audit_hash_chain` (`AuditAppendRequest`, `AuditBlock`, `AuditChainVerificationResult`, `AuditEventType`)
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/audit_hash_chain.py`
  - Emergency Break-The-Glass and Lab Panic Alert audit pipelines
- **Exported Symbols:**
  - `compute_payload_digest`
  - `compute_block_hash`
  - `AuditHashChainLedger`
  - `audit_ledger_service`

```
+-----------------------------------------------------------------------------------+
|                     Cryptographic Audit Hash-Chain Architecture                   |
|                                                                                   |
|  [Clinical Audit Trigger (BTG / Panic Ack / Auth)]                                |
|          |                                                                        |
|          v                                                                        |
|  [audit_ledger_service.append_event]                                              |
|          |-- 1. Compute SHA-256 digest of payload dictionary                      |
|          |-- 2. Read previous block hash (prev.blockHash)                         |
|          |-- 3. Calculate new Block Hash:                                         |
|          |       SHA-256(index : id : prev_hash : timestamp : type : actor : digest)|
|          |-- 4. Append AuditBlock to self._chain (Thread-safe)                    |
|          +--> [CRITICAL DEFECT: List is in RAM only! No PostgreSQL write!]        |
|                                                                                   |
|  [Integrity Audit: verify_chain_integrity]                                        |
|          |-- 1. Verify Genesis Block (Index 0, GENESIS_PREV_HASH)                 |
|          |-- 2. Traversal Loop (1..N):                                            |
|          |       |- Verify Index continuity (block[i].index == i)                 |
|          |       |- Verify Pointer (block[i].previousHash == block[i-1].blockHash)|
|          |       +- Recalculate block[i].blockHash and compare                    |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

This module provides mathematical proof that audit logs have not been tampered with or retroactively altered by system administrators:

1. **Genesis Initialization (`_initialize_genesis_and_seed`):** When the platform starts, it creates Block 0 (Genesis) using a fixed zero-pointer (`"0" * 64`) and an initial system manifest. It then appends two sample clinical events (an emergency Break-The-Glass record and a critical laboratory panic alert acknowledgment).
2. **Payload Digest & Block Hashing (`compute_payload_digest`, `compute_block_hash`):** Converts the arbitrary JSON payload dictionary into a canonical, alphabetically sorted JSON string (`json.dumps(payload, sort_keys=True, separators=(",", ":"))`) and takes its SHA-256 digest. It then constructs a colon-separated canonical string combining block index, unique UUID, previous block hash, ISO timestamp, event type, actor ID, and payload digest, computing the authoritative `blockHash`.
3. **Event Appending (`append_event`):** Under a `threading.Lock`, reads the latest block's hash, computes the new block's hash, and appends the new `AuditBlock` to the internal list.
4. **Integrity Verification (`verify_chain_integrity`):** Traverses the entire chain block-by-block. For every block, it recalculates the expected hash and checks that `previousHash` matches the preceding block's hash. If any administrator or malicious actor altered a single character in a payload, changed a timestamp, or deleted a block, the traversal immediately halts and identifies the exact tampered index and explanation.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Cryptographic Specifications
- **Strict Hash-Chaining Invariant:** For every block $i > 0$, $\text{block}[i].\text{previousHash} = \text{block}[i-1].\text{blockHash}$.
- **Tamper Evidence Invariant:** Any mutation of block metadata or payload invalidates the block's hash and breaks the chain pointers of all subsequent blocks.
- **Thread Exclusivity:** Appending new blocks must be strictly serialized with a mutex to prevent forks in the linear chain.

### Vulnerabilities & Operational Risks
- **Volatile In-Memory Storage:** The entire chain resides in `self._chain: List[AuditBlock] = []` in RAM. When the backend container restarts or redeploys, all dynamically logged clinical events disappear. A forensic audit ledger that does not survive process restarts fails basic evidentiary requirements under healthcare compliance laws (HIPAA, ISO 27001, Indian DPDP Act 2023).
- **Multi-Worker Desynchronization:** In multi-process Uvicorn deployments, each worker maintains its own isolated `_chain` instance. Events recorded on worker 1 do not exist on worker 2, causing `verify_chain_integrity` to report divergent chain states depending on which worker receives the HTTP request.
- **Delimiter Injection Vulnerability:** `compute_block_hash` uses `:` as a field separator (`f"{index}:{block_id}:{previous_hash}:{timestamp}:{event_type}:{actor_id}:{payload_digest}"`). If `actor_id` contains a colon, an attacker could theoretically construct a collision if fields are improperly parsed.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-AHC-F01` | **S1** | `[SEC]` | `audit_hash_chain.py:53, 159-170` | Audit hash chain is held exclusively in volatile RAM without database persistence, erasing all forensic clinical records on server restart. |
| `BE-SVC-AHC-F02` | **S2** | `[QUAL]` | `audit_hash_chain.py:52-55` | In-memory ledger cannot synchronize across multi-worker Uvicorn processes, causing divergent audit chains and failed verifications. |
| `BE-SVC-AHC-F03` | **S3** | `[SEC]` | `audit_hash_chain.py:45` | Canonical string uses unescaped colon delimiters, risking field boundary ambiguity if actor IDs or event types contain colons. |
| `BE-SVC-AHC-F04` | **S4** | `[DOC]` | `audit_hash_chain.py:86-115` | Hardcoded demo clinical payloads and fake ABHA numbers seeded directly in production code. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Persistence Warning & Delimiter Boundary Sanitization (`BE-SVC-AHC-F01`, `BE-SVC-AHC-F03`)

```diff
--- a/backend/app/services/audit_hash_chain.py
+++ b/backend/app/services/audit_hash_chain.py
@@ -44,7 +44,8 @@ def compute_block_hash(
     payload_digest: str,
 ) -> str:
     """Calculates SHA-256 block hash over canonical concatenated fields."""
-    canonical = f"{index}:{block_id}:{previous_hash}:{timestamp}:{event_type}:{actor_id}:{payload_digest}"
+    clean_actor = actor_id.replace(":", "_")
+    canonical = f"{index}:{block_id}:{previous_hash}:{timestamp}:{event_type}:{clean_actor}:{payload_digest}"
     return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
 
 
@@ -54,6 +55,10 @@ class AuditHashChainLedger:
     def __init__(self) -> None:
         self._chain: List[AuditBlock] = []
         self._lock = threading.Lock()
+        logger.warning(
+            "[SECURITY] AuditHashChainLedger is running in EPHEMERAL in-memory mode. "
+            "Audit blocks must be backed by PostgreSQL audit_ledgers table for legal non-repudiation."
+        )
         self._initialize_genesis_and_seed()
```
