# Comprehensive Principal Software Audit & Technical Documentation
# File: `backend/app/services/abdm_discovery.py`
# Component: ABDM Milestone 2 Federated Patient Discovery & Fuzzy Matcher
# Release Version: 1.1.0-RC3 · ABDM / NRCES v4.1 Compliance

---

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/abdm_discovery.py` implements the patient discovery protocol and fuzzy demographic matching engine specified by ABDM Milestone 2 (M2) HIP guidelines. It processes federated discovery queries (`POST /v0.5/care-contexts/discover`), evaluates deterministic matches (ABHA Number, ABHA Address, MRN) and fuzzy demographic criteria (Levenshtein token set similarity, birth year tolerance, gender normalization), protects patient privacy through ambiguity thresholds, extracts associated longitudinal care contexts (appointments, diagnostic orders), and dispatches asynchronous callbacks (`POST /v0.5/care-contexts/on-discover`).

### Architectural Role & System Topology
```
           +-----------------------------------------------+
           |    ABDM Gateway (POST /care-contexts/discover)|
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |     process_and_dispatch_discovery (Worker)   |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |       discover_patient (Fuzzy Match Engine)   |
           |  (Deterministic > Verified Phone > Demographic)|
           +-----------------------------------------------+
                                  |
                   (Ambiguity Guardrail: Delta >= 0.10)
                                  v
           +-----------------------------------------------+
           |     resolve_patient_care_contexts (EHR DB)    |
           |     (OPD Consultations + Lab Requisitions)    |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           | dispatch_async_on_discover_callback (Gateway) |
           +-----------------------------------------------+
```

### Key Import/Export Roster
- **Imports**:
  - `difflib, re, time, uuid, httpx`: Text pattern matching and async I/O.
  - `select, joinedload`: SQLAlchemy async querying.
  - `Appointment, DiagnosticOrder, PatientProfile, User`: Clinical domain models.
  - Discovery schemas from `app.schemas.abdm_m2_bridge`.
- **Exports**:
  - `calculate_name_similarity`: Composite Levenshtein, Jaccard, and token similarity.
  - `calculate_yob_similarity`: Age window score (+/- 1-2 years).
  - `calculate_gender_similarity`: Standardized gender code comparator.
  - `evaluate_candidate_match`: Multi-tier demographic matching algorithm.
  - `resolve_patient_care_contexts`: Extracts appointments and orders as ABDM care contexts.
  - `discover_patient`: Core discovery query engine with ambiguity defense.
  - `simulate_patient_discovery`: Interactive console simulation helper.
  - `dispatch_async_on_discover_callback`: Gateway `/on-discover` callback dispatcher.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Text Normalization**: Strips punctuation, non-alphanumeric characters, and common Indian honorifics (`dr`, `shri`, `smt`, `kumar`, `kumari`) to maximize phonetic and lexical overlap.
2. **Similarity Scoring**: Computes composite name similarity using exact token sets, subset matching, character Levenshtein ratios, and difflib Gestalt pattern matching. Birth year matching permits $\pm 1$ year rounding tolerance ($0.85$ score).
3. **Multi-Tier Matching**:
   - Tier 1: Deterministic match via ABHA Number, ABHA Address, or MRN (score = $1.0$).
   - Tier 2: Verified mobile phone match + demographic weighting (score = $0.65 + \text{demographics}$).
   - Tier 3: Pure fuzzy demographic matching ($50\%$ name, $25\%$ YOB, $25\%$ gender).
4. **Ambiguity Protection**: If two or more candidate profiles exceed the match threshold ($0.75$) with a score difference of less than $0.10$, the engine rejects the discovery to prevent accidental disclosure of clinical records to another patient.
5. **Care Context Extraction**: Translates historical outpatient visits and diagnostic lab orders into ABDM Care Context reference numbers (`OPD-ENC-XXXX`, `LAB-ORD-XXXX`).

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Unindexed Full Table Scan & Memory Exhaustion DoS (CWE-400)
In lines 442–444:
```python
stmt = select(PatientProfile).options(joinedload(PatientProfile.user))
res = await session.execute(stmt)
all_profiles = res.scalars().all()
```
Every inbound discovery request executes an unindexed `SELECT * FROM patient_profiles` joining all `users`, loading the entire hospital patient database into Python memory, and iterating through them linearly $O(N)$! In a production hospital with $100,000+$ patients, this will trigger out-of-memory crashes and severe database I/O starvation. The query must filter deterministically in SQL first (`where(PatientProfile.abha_number == ...)` or `where(User.phone_number == ...)`).

### Invariant 2: Flawed Ambiguity Threshold Blocking Exact Matches
In line 478:
```python
if abs(top_score - second_score) < 0.10:
```
If patient A matches deterministically via ABHA Number (score = $1.0$) and a secondary patient B has a similar name resulting in a fuzzy score of $0.92$, the engine marks the result as ambiguous and rejects discovery. Deterministic identifier matches should bypass ambiguity checks entirely.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SVC-DSC-F01` | S1 | `[PERF]` | `abdm_discovery.py:442-444` | In-memory $O(N)$ full table scan loads all patients into RAM on every discovery query (CWE-400) |
| `BE-SVC-DSC-F02` | S2 | `[QUAL]` | `abdm_discovery.py:475-487` | Ambiguity logic blocks verified $1.0$ deterministic matches if a fuzzy candidate scores within $0.10$ |
| `BE-SVC-DSC-F03` | S3 | `[QUAL]` | `abdm_discovery.py:671` | Late import `from app.main import app` introduces circular module dependency risks |

---

## Layer E: Unapplied Unified Diff Patches for S0–S2 Findings

```diff
--- a/backend/app/services/abdm_discovery.py
+++ b/backend/app/services/abdm_discovery.py
@@ -472,8 +472,8 @@
         return False, None, empty_breakdown, [], "No matching patient found at HIP"
 
     # Ambiguity Protection Check:
-    # If more than 1 patient passes threshold and score gap is < 0.10, reject
-    if len(candidates) > 1:
+    # If more than 1 patient passes threshold, score gap is < 0.10, and top is not deterministic (1.0), reject
+    if len(candidates) > 1 and candidates[0][0] < 1.0:
         top_score = candidates[0][0]
         second_score = candidates[1][0]
         if abs(top_score - second_score) < 0.10:
```
