# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/medication.py`
**Audited Path:** `backend/app/schemas/medication.py`  
**Module:** `backend` | **Subsystem:** Clinical Medication Catalog & Formulary Management  
**Severity Classification:** MEDIUM RISK (`[QUAL]` / `[SEC]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/medication.py` defines the Pydantic v2 schemas for NIRMAYA's central pharmaceutical catalog, clinical drug formulary, and multi-ontology terminology mappings. Conforming to the HL7 FHIR Release 4 Medication resource specification and National Resource Centre for EHR Standards in India (NRCES) profiles, this module structures:
- Comprehensive medication concept definitions bridging RxNorm, WHO-ATC, and SNOMED-CT ontologies (`MedicationBase`).
- New medication catalog onboarding payloads (`MedicationCreate`) and partial attribute updates (`MedicationUpdate`).
- Individual medication response representations with database primary keys and audit timestamps (`MedicationResponse`).
- Paginated catalog search results (`MedicationListResponse`) and therapeutic class distribution summaries (`TherapeuticClassSummary`).

#### 2. Key Components & Class Roster
- `MedicationBase`: Core medication attributes including clinical display name, generic moiety, proprietary brand name, RxNorm Concept Unique Identifier (`rxnorm_code`), WHO Anatomical Therapeutic Chemical classification (`atc_code`), SNOMED-CT clinical drug code (`snomed_code`), dose formulation (`MedicationForm`), administration route (`AdministrationRoute`), strength, active ingredient, prescription-required flag, controlled substance flag, insurance formulary tier (`FormularyTier`), and FHIR status (`MedicationStatus`).
- `MedicationCreate`: Subclass of `MedicationBase` used for catalog registration.
- `MedicationUpdate`: Optional-field patch schema allowing granular field updates.
- `MedicationResponse`: Output schema returning persistent UUID and creation/modification timestamps with ORM attribute extraction enabled.
- `MedicationListResponse`: Standard paginated container wrapping item lists, record totals, limits, and pagination offsets.
- `TherapeuticClassSummary`: Aggregate breakdown counting available drugs per WHO-ATC therapeutic category prefix.

---

### Layer B: Plain-Language Developer Walkthrough

In clinical medicine, prescribing the wrong drug, wrong dose, or confusing a brand name with a generic name can lead to severe adverse drug reactions or death. Furthermore, different medical systems use different coding languages: American systems often use RxNorm, global public health programs use WHO-ATC codes, and Indian digital health exchanges under ABDM require SNOMED-CT codes.

`medication.py` serves as the universal dictionary for all medicines available on NIRMAYA:
1. Every medication in the formulary (e.g., "Metformin 500mg Oral Tablet") is assigned its generic name, active pharmaceutical ingredient, dosage form (Tablet), route (Oral), and strength.
2. It simultaneously cross-references all three major medical coding systems: RxNorm (`860975`), WHO-ATC (`A10BA02`), and SNOMED-CT (`387048002`). This allows doctors, pharmacies, and national insurance platforms to understand exactly what medicine was prescribed regardless of which software system they use.
3. It tracks legal and safety flags, such as whether a prescription is legally required or whether the medication is a controlled scheduled narcotic.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **Multi-Ontology Convergence:** Implements triple-coding (RxNorm + WHO-ATC + SNOMED-CT), guaranteeing seamless translation across national and international EMR standards.
- **Enumerated Form & Route Safety:** Enforces type-safe enums (`MedicationForm`, `AdministrationRoute`, `FormularyTier`, `MedicationStatus`) defined in `app.models.enums`.
- **Length Constraints:** Defines strict `min_length` and `max_length` bounds on all string fields, preventing buffer abuse and unbounded database column storage.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Missing Regex Format Validation on International Medical Codes (`BE-SCH-MED-F01`)
- **Severity:** S2 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/medication.py:41-47, 54-59, 66-71`
- **Description:** Fields `rxnorm_code`, `atc_code`, and `snomed_code` are declared as generic strings without pattern matching. In production, RxNorm codes are purely numeric RxCUIs (`^\d+$`), WHO-ATC codes strictly follow a 7-character alphanumeric hierarchy (`^[A-Z]\d{2}[A-Z]{2}\d{2}$` or prefix), and SNOMED-CT concept IDs are 6 to 18-digit numbers (`^\d{6,18}$`). Without regex validation, invalid strings (e.g. `"N/A"`, `"INVALID"`, or random letters in RxNorm) pass schema validation and pollute the clinical formulary.
- **Impact:** Corrupted medical coding that fails downstream FHIR validation or external ABDM gateway verification.
- **Remediation:** Enforce regex patterns: `pattern=r"^\d+$"` on `rxnorm_code`, `pattern=r"^[A-Z]\d{2}[A-Z]{2}\d{2}$"` on `atc_code`, and `pattern=r"^\d{6,18}$"` on `snomed_code`.

##### Vulnerability 2: Missing Non-Negative Integer Bounds on Pagination and Counter Fields (`BE-SCH-MED-F02`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/medication.py:184-188, 195`
- **Description:** In `MedicationListResponse`, fields `total`, `limit`, and `offset` lack `ge=0` bounds. Similarly, `medication_count` in `TherapeuticClassSummary` lacks non-negative constraints.
- **Impact:** Inconsistent API contract allowing negative counts.
- **Remediation:** Add `ge=0` constraints to all integer count and pagination fields.

##### Vulnerability 3: Missing ConfigDict on Auxiliary Response Models (`BE-SCH-MED-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/medication.py:181, 190`
- **Description:** `MedicationListResponse` and `TherapeuticClassSummary` omit `model_config = ConfigDict(from_attributes=True)`.
- **Impact:** Inconsistent ORM serialization behavior.
- **Remediation:** Add `model_config = ConfigDict(from_attributes=True)`.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-MED-F01` | S2 | `[QUAL]` | `medication.py:41-71` | `rxnorm_code`, `atc_code`, and `snomed_code` lack standard regex pattern constraints |
| `BE-SCH-MED-F02` | S3 | `[QUAL]` | `medication.py:184-188, 195` | `total`, `limit`, `offset`, and `medication_count` lack `ge=0` bounds |
| `BE-SCH-MED-F03` | S3 | `[QUAL]` | `medication.py:181, 190` | Missing `ConfigDict(from_attributes=True)` on list and summary models |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/medication.py
+++ b/backend/app/schemas/medication.py
@@ -41,3 +41,4 @@ class MedicationBase(BaseModel):
     rxnorm_code: str = Field(
         ...,
+        pattern=r"^\d+$",
         min_length=1,
@@ -54,3 +55,4 @@ class MedicationBase(BaseModel):
     atc_code: Optional[str] = Field(
         default=None,
+        pattern=r"^[A-Z]([0-9]{2}([A-Z]([A-Z0-9]{2})?)?)?$",
         max_length=32,
@@ -66,3 +68,4 @@ class MedicationBase(BaseModel):
     snomed_code: Optional[str] = Field(
         default=None,
+        pattern=r"^\d{6,18}$",
         max_length=64,
@@ -181,4 +184,6 @@ class MedicationListResponse(BaseModel):
     """Paginated collection response for medication catalog queries."""
+    model_config = ConfigDict(from_attributes=True)
 
-    total: int = Field(..., description="Total matching medication records count")
+    total: int = Field(..., ge=0, description="Total matching medication records count")
     items: List[MedicationResponse] = Field(..., description="List of medication records")
-    limit: int = Field(..., description="Requested page record limit")
-    offset: int = Field(..., description="Requested page pagination offset")
+    limit: int = Field(..., ge=1, le=100, description="Requested page record limit")
+    offset: int = Field(..., ge=0, description="Requested page pagination offset")
@@ -190,4 +195,6 @@ class TherapeuticClassSummary(BaseModel):
     """Aggregate breakdown of medications by WHO-ATC therapeutic category."""
+    model_config = ConfigDict(from_attributes=True)
 
     atc_prefix: str = Field(..., description="ATC level 1 or level 2 classification prefix")
     name: str = Field(..., description="Therapeutic system category name")
-    medication_count: int = Field(..., description="Number of catalog drugs in this category")
+    medication_count: int = Field(..., ge=0, description="Number of catalog drugs in this category")
```
