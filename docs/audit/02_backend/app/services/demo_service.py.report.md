# Codebase Audit Report: `backend/app/services/demo_service.py`

**Audit Target**: `backend/app/services/demo_service.py`  
**Subsystem**: Backend - Demonstration Scenarios & Slide Deck Defense Engine (`backend/app/services/`)  
**File Lines**: 601 LOC  
**Severity Breakdown**: S0: 0 | S1: 1 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `demo_service.py` module orchestrates interactive demonstration workflows and capstone presentation materials for NIRMAYA, providing 5 reproducible scenarios (Consultation, Break-the-Glass Vault, Edge Synchronization, SQL/MED Federation, IDSP Command Center) and a 12-slide comprehensive defense presentation deck.

```
[ Capstone Evaluator / Investor Portal ]
                     │
                     ▼
             [ demo_service.py ]
   ├── 1. Scenario Catalog (5 Pre-Configured Workflows)
   │     ├── SCEN-01: Citizen Consultation & ABDM Linkage
   │     ├── SCEN-02: Emergency BTG Vault & AES-256-GCM
   │     ├── SCEN-03: Offline Edge Node & Vector Clocks
   │     ├── SCEN-04: SQL/MED Read-Only Federation
   │     └── SCEN-05: IDSP Command Center & TRBAC
   ├── 2. Live Scenario Execution & Telemetry Aggregation
   ├── 3. Sandbox State Reset Engine
   └── 4. 12-Slide Sovereign DPI Defense Slide Deck
                     │
                     ▼
   [ ScenarioExecutionResult / SlideDeckMetadata ]
```

### Import / Export Roster
- **Imports**: `hashlib`, `os`, `time`, `datetime`, `typing`, `cryptography.hazmat.primitives.ciphers.aead.AESGCM`, `app.schemas.demo`.
- **Exports**: `DemoService`, `demo_service`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Catalog Initialization**: Defines 5 scenarios with specific prerequisites, multi-step sub-workflows, expected durations, and SLA targets.
2. **Scenario Execution**: `execute_scenario()` executes the designated scenario, generating verification assertions, computing cryptographic proofs, and returning elapsed latency metrics.
3. **Slide Deck Rendering**: Provides structured presentation slides covering system vision, healthcare fragmentation, HL7 FHIR R4 models, ABDM milestones, and empirical benchmark results.
4. **Sandbox State Reset**: Resets all demonstration scenarios to `READY` state.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Synthetic Simulated Execution vs Subsystem Integration
In `execute_scenario()` (lines 488–574), the execution of scenarios does not actually call or invoke the underlying production services (`appointment`, `emergency_vault`, `edge_sync`, `legacy_his_service`, `command_center_service`). Instead, it appends hardcoded static string assertions (e.g., `"Patient Aarav Sharma (ABHA: 14-8291-0391-4821) verified..."`, `"ABDM M2 Care-Context linked successfully..."`) and returns a canned `ScenarioExecutionStatus.SUCCESS`. This presents an illusion of end-to-end integration while none of the service code paths are exercised.

### 2. Mocked Argon2id Derivation in Vault Demonstration
In `SCEN-02-BTG-VAULT` (lines 518–526), the code claims in its metadata to demonstrate memory-hard Argon2id key derivation with a 64MB memory cost. However, the execution code mocks this entirely with a standard SHA-256 digest: `hashlib.sha256(b"ARGON2ID_EMERGENCY_MASTER_KEY_SECRET").hexdigest()`, circumventing the memory-hard KDF execution.

### 3. Hardcoded Metadata & Version Stagnation
Slide items contain hardcoded dates and version numbers (`November 2026`, `v1.0.0`) that will require continuous manual maintenance.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-DEM-F01` | **S1** | `[QUAL/SEC]` | `backend/app/services/demo_service.py:488-574` | `execute_scenario()` bypasses all real backend service layers, generating hardcoded assertions and canned telemetry that simulate integration without verifying actual system state. |
| `BE-SVC-DEM-F02` | **S2** | `[QUAL]` | `backend/app/services/demo_service.py:518-526` | Claims to execute 64MB memory-hard Argon2id key derivation for emergency vault demo, but substitutes a fast SHA-256 hash. |
| `BE-SVC-DEM-F03` | **S3** | `[QUAL]` | `backend/app/services/demo_service.py:463-472` | Hardcoded static presentation metadata and dates embedded directly in application source code. |
| `BE-SVC-DEM-F04` | **S4** | `[DOC]` | `backend/app/services/demo_service.py:307-474` | Presentation slide deck is hardcoded in Python dictionaries rather than loaded from external Markdown or JSON configuration assets. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-DEM-F01` / `BE-SVC-DEM-F02`: Real Service Execution and Authentic Argon2id KDF

```diff
--- a/backend/app/services/demo_service.py
+++ b/backend/app/services/demo_service.py
@@ -515,9 +515,11 @@ class DemoService:
             # 1. Emergency declaration
             assertions_verified.append("Emergency override authenticated for Dr. Priya Sharma (ER Trauma Tier-1)")
-            # 2. Argon2id KDF
-            kdf_hash = hashlib.sha256(b"ARGON2ID_EMERGENCY_MASTER_KEY_SECRET").hexdigest()
-            cryptographic_proofs.append(f"Argon2id Derived Master Key Fingerprint: {kdf_hash[:16]}")
+            # 2. Authentic Argon2id KDF execution via emergency_vault service
+            from app.services.emergency_vault import emergency_vault_service
+            salt = os.urandom(16)
+            derived_key = emergency_vault_service.derive_master_key(passphrase="EMERGENCY_OVERRIDE_PRIYA", salt=salt)
+            cryptographic_proofs.append(f"Argon2id Derived Master Key Fingerprint: {hashlib.sha256(derived_key).hexdigest()[:16]}")
             # 3. AES-256-GCM Decryption
             aes_key = AESGCM.generate_key(bit_length=256)
             aesgcm = AESGCM(aes_key)
```
