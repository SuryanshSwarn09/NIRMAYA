# Codebase Audit Report: `backend/app/services/cds_safety.py`

**Audit Target**: `backend/app/services/cds_safety.py`  
**Subsystem**: Backend - Clinical Decision Support Engine (`backend/app/services/`)  
**File Lines**: 181 LOC  
**Severity Breakdown**: S0: 0 | S1: 1 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `cds_safety.py` service orchestrates pre-prescription safety screening for NIRMAYA, coordinating interactions between prescription drafting APIs, patient records, allergy registries, and the CDS rule engine.

```
[ Prescription Drafting API / UI ]
                │
                ▼ (Pre-prescription Validation Request)
      [ cds_safety.py Service ]
        ├── 1. Allergy Screening (Cross-reactive classes: Penicillins, Sulfa)
        ├── 2. Drug-Drug Interaction Screen (via cds_rules.py)
        ├── 3. Renal & Hepatic Dosing Thresholds
        └── 4. Pregnancy & Lactation Safety Classification
                │
                ▼
      [ SafetyScreeningResult: PASS / WARN / BLOCK ]
```

### Import / Export Roster
- **Imports**: `typing`, `logging`, `app.models`, `app.schemas.cds`, `app.services.cds_rules`.
- **Exports**: `CDSSafetyService`, `cds_safety_service`, `SafetyEvaluationResult`, `evaluate_prescription_safety()`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Request Intake**: Accepts patient identifier, proposed new medications, and optional supplemental clinical context (e.g. gestational age, renal function, client-provided allergies).
2. **Allergy Validation**: Checks whether any proposed active ingredients or drug classes match known allergic triggers (e.g. Penicillin, Cephalosporins, NSAIDs, Sulfonamides).
3. **DDI Cross-Matching**: Combines proposed medications with active medications and evaluates pairwise compatibility via `cds_rules.py`.
4. **Intervention Grading**: Returns an aggregated safety decision:
   - `BLOCK`: Hard contraindications (e.g. severe anaphylactic allergy or lethal DDI).
   - `WARN`: Significant risk requiring physician override and documented rationale.
   - `INFO`: Minor advisory notes or monitoring recommendations.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Client-Payload Allergy Reliance & Database Desynchronization
At lines 111–115, the service extracts patient allergies solely from `request.supplemental_allergies`. It fails to query the authoritative `PatientProfile` or persistent `AllergyIntolerance` table in PostgreSQL. If the caller (e.g. mobile app or frontend consultation form) does not explicitly pre-fetch and re-transmit the patient's full allergy history in the POST body, life-threatening allergic contraindications (e.g., Amoxicillin prescribed to a penicillin-allergic patient) will silently pass through unflagged.

### 2. Omission of Database Active Medications
Similarly, the service evaluates DDIs against `request.current_medications`. If a patient has an ongoing prescription for Warfarin from a prior encounter that was not included in the payload by the frontend, a new prescription for Ketorolac will not trigger a bleeding alert. Authoritative CDS evaluation requires querying all active, unexpired `MedicationRequest` records from the database for the given `patient_id`.

### 3. Fail-Closed vs Fail-Open Security Model
In clinical safety engines, partial data should never trigger a silent "safe" classification. When database patient context is omitted, the engine should raise a validation error or clearly mark the evaluation as `INCOMPLETE_CONTEXT`, rather than issuing an unqualified clearance.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-CDS-F01` | **S1** | `[SEC/MED]` | `backend/app/services/cds_safety.py:111-115` | Pre-prescription allergy check evaluates only caller-supplied allergies, ignoring persistent patient allergy records in PostgreSQL and enabling fatal contraindication bypasses. |
| `BE-SVC-CDS-F02` | **S2** | `[QUAL/MED]` | `backend/app/services/cds_safety.py:130-155` | Evaluates DDI risks solely against request payload medications, ignoring active longitudinal prescriptions stored in the database. |
| `BE-SVC-CDS-F03` | **S3** | `[QUAL]` | `backend/app/services/cds_safety.py:75-90` | Missing automated eGFR calculation from recent serum creatinine observations when assessing renal dosing limits. |
| `BE-SVC-CDS-F04` | **S4** | `[DOC]` | `backend/app/services/cds_safety.py:1-35` | Lack of documentation on physician override audit logging and medicolegal retention requirements. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-CDS-F01` / `BE-SVC-CDS-F02`: Authoritative Database Context Retrieval for Allergies and Active Medications

```diff
--- a/backend/app/services/cds_safety.py
+++ b/backend/app/services/cds_safety.py
@@ -108,12 +108,27 @@ class CDSSafetyService:
         patient_id: str,
         proposed_medications: List[str],
         supplemental_allergies: Optional[List[str]] = None,
+        db: Optional[AsyncSession] = None,
     ) -> SafetyEvaluationResult:
-        allergies = set(supplemental_allergies or [])
+        allergies = set(supplemental_allergies or [])
+        active_meds = set(current_medications or [])
+        
+        # Fetch authoritative patient records from database if session available
+        if db and patient_id:
+            patient = await db.scalar(select(PatientProfile).where(PatientProfile.id == patient_id))
+            if patient and patient.allergies:
+                allergies.update(a.strip().lower() for a in patient.allergies)
+            
+            # Fetch unexpired active prescriptions
+            active_rx = await db.scalars(
+                select(MedicationRequest.medication_name)
+                .where(MedicationRequest.patient_id == patient_id, MedicationRequest.status == "ACTIVE")
+            )
+            active_meds.update(rx.strip().lower() for rx in active_rx)
 
         # 1. Screen against known allergies
         allergy_conflicts = []
         for drug in proposed_medications:
-            for allergy in allergies:
+            for allergy in allergies:
                 if self._is_allergy_contraindicated(drug, allergy):
                     allergy_conflicts.append((drug, allergy))
```
