# Codebase Audit Report: `backend/app/services/cds_rules.py`

**Audit Target**: `backend/app/services/cds_rules.py`  
**Subsystem**: Backend - Clinical Decision Support Engine (`backend/app/services/`)  
**File Lines**: 598 LOC  
**Severity Breakdown**: S0: 0 | S1: 1 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `cds_rules.py` module encapsulates the rule definitions, catalog of known Drug-Drug Interactions (DDIs), drug-condition contraindications, and rule evaluation logic for NIRMAYA's Clinical Decision Support (CDS) pipeline.

```
[ Doctor Prescription UI / API ]
               │
               ▼
   [ cds_safety.py Engine ]
               │
               ▼
      [ cds_rules.py ]
   ├── Static DDI Matrix (Warfarin, NSAIDs, Metformin, ACEi, etc.)
   ├── Contraindication Catalog (Pregnancy, Renal, Hepatic)
   ├── Pediatric / Geriatric Dosage Boundary Rules
   └── Rule Evaluation Engine
               │
               ▼
   [ CDS Alerts / Intervention Warnings ]
```

### Import / Export Roster
- **Imports**: `typing` (`Dict`, `List`, `Optional`, `Set`, `Tuple`), `dataclasses`, `enum`, `logging`, `re`.
- **Exports**: `CDSRuleRegistry`, `InteractionSeverity`, `DDIInteraction`, `ContraindicationRule`, `evaluate_interactions()`, `evaluate_contraindications()`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Rule Representation**: Rules are modeled via dataclasses (`DDIInteraction`, `ContraindicationRule`) describing interaction pairs, severity classifications (`CONTRAINDICATED`, `CRITICAL`, `SIGNIFICANT`, `INFORMATIONAL`), physiological mechanism of action, and recommended clinical management.
2. **Interaction Matrix Catalog**: Hardcoded dictionaries represent well-known clinical interactions:
   - Warfarin + NSAIDs / Fluconazole / Clopidogrel (hemorrhage risk).
   - Metformin + Contrast Media (lactic acidosis risk).
   - ACE Inhibitors + Spironolactone / Potassium supplements (hyperkalemia risk).
   - Macrolides + QT-prolonging antiarrhythmics (torsades de pointes).
3. **Evaluation Loop**: The evaluator accepts a list of proposed medications alongside the patient's existing active medication list and runs pairwise cross-checks against the matrix.
4. **Contraindication Evaluation**: Compares proposed drugs against active patient problem lists (ICD-10 / SNOMED codes) and physiological parameters (eGFR, pregnancy status).

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. In-Memory Static DDI Matrix vs Pharmacopeia Sync
The clinical rules are hardcoded directly into Python dictionaries. In a production healthcare system managing thousands of active chemical entities, generic formulations, and commercial brand variations, hardcoding ~25 pairwise interactions creates a false sense of safety. If an unlisted dangerous combination is prescribed, the CDS engine returns a green checkmark (`safe=True`), risking fatal patient events.

### 2. Literal Substring Matching vs RxNorm / ATC Ontologies
The matching algorithm relies on normalized lowercase string inclusion. Prescribing `"Glucophage"` (brand name for Metformin) will fail to trigger the Metformin interaction checks unless every commercial brand alias is manually registered in the code. Standard CDS architectures require mapping to RxCUI (RxNorm Concept Unique Identifier) or WHO ATC (Anatomical Therapeutic Chemical) codes.

### 3. Concurrency & Performance
The pairwise nested loop operates in $O(M \times N)$ or $O((M+N)^2)$ where $M$ is active medications and $N$ is proposed medications. For typical prescriptions ($N \le 10$), latency is $< 1\text{ms}$. However, the absence of caching or precomputed bitmasks on large inpatient polypharmacy lists (e.g. ICU patients on 30+ concurrent infusions) scales quadratically.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-CDR-F01` | **S1** | `[SEC/MED]` | `backend/app/services/cds_rules.py:120-250` | Hardcoded static DDI matrix in RAM with no database or external pharmacopeial synchronization, creating dangerous blindspots for unlisted drug combinations. |
| `BE-SVC-CDR-F02` | **S2** | `[QUAL/MED]` | `backend/app/services/cds_rules.py:310-345` | Literal string comparison without phonetic indexing or ontology resolution (RxNorm/ATC) allows typos and brand synonyms to bypass critical safety rules. |
| `BE-SVC-CDR-F03` | **S3** | `[PERF]` | `backend/app/services/cds_rules.py:420-460` | Quadratic $O(N^2)$ pairwise loop lacks memoization or set-intersection optimization for polypharmacy profiles. |
| `BE-SVC-CDR-F04` | **S4** | `[DOC]` | `backend/app/services/cds_rules.py:1-40` | Missing formal documentation on adherence to HL7 CDS Hooks 1.0 specifications and CDS Intervention grading schemes. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-CDR-F01` / `BE-SVC-CDR-F02`: Ontology-Aware Normalized Drug Matching & Extensible Registry

```diff
--- a/backend/app/services/cds_rules.py
+++ b/backend/app/services/cds_rules.py
@@ -125,12 +125,26 @@ class CDSRuleRegistry:
     def __init__(self) -> None:
         self._ddi_matrix = DDI_MATRIX
         self._contraindications = CONTRAINDICATION_RULES
+        self._concept_synonyms = DRUG_CONCEPT_SYNONYMS
+
+    def normalize_drug_concept(self, drug_identifier: str) -> str:
+        """Normalize brand name or chemical entity to canonical RxNorm/ATC active ingredient."""
+        cleaned = drug_identifier.strip().lower()
+        # Lookup normalized concept or alias mapping
+        return self._concept_synonyms.get(cleaned, cleaned)
 
     def check_pairwise_ddi(
         self, drug_a: str, drug_b: str
     ) -> Optional[DDIInteraction]:
-        key1 = (drug_a.lower(), drug_b.lower())
-        key2 = (drug_b.lower(), drug_a.lower())
+        norm_a = self.normalize_drug_concept(drug_a)
+        norm_b = self.normalize_drug_concept(drug_b)
+        
+        key1 = (norm_a, norm_b)
+        key2 = (norm_b, norm_a)
         return self._ddi_matrix.get(key1) or self._ddi_matrix.get(key2)
```
