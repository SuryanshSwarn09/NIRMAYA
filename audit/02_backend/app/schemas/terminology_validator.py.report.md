# Comprehensive Principal Software Audit & Technical Documentation
# File: `backend/app/schemas/terminology_validator.py`
# Component: Medical Ontology Binding & Terminology Engine
# Release Version: 1.1.0-RC3 · ABDM / NRCES v4.1 Compliance

---

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/schemas/terminology_validator.py` defines the Pydantic v2 schemas supporting the NIRMAYA Medical Ontology Binding Audit & Clinical Terminology Validation subsystem. The schemas model evaluation pipelines for standard healthcare ontologies—SNOMED-CT, LOINC, ICD-10, HL7 Standard CodeSystems, and RxNorm / WHO-ATC. The models define concept binding status classifications, concept suggestion candidates, audit items within FHIR resources, aggregated bundle compliance reports, concept lookup payloads, and authorized terminology catalog metadata.

### Architectural Role & System Topology
```
           +-----------------------------------------------+
           |       Incoming FHIR R4 Bundle / Resource      |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |         BundleOntologyAuditRequest            |
           +-----------------------------------------------+
                                  |
                   (Ontology Validation Engine)
                                  v
           +-----------------------------------------------+
           |        ConceptAuditItem (System/Code/Display) |
           |        + ConceptSuggestion (Mapping Candidates)|
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |          OntologyAuditReport                  |
           |   (complianceScore, isCompliant, auditItems)  |
           +-----------------------------------------------+
```

### Key Import/Export Roster
- **Imports**:
  - `Enum` from `enum`: Standard enumeration base class.
  - `Any, Dict, List, Optional` from `typing`: Type annotations.
  - `BaseModel, Field, ConfigDict` from `pydantic`: Schema modeling and attribute validation.
- **Exports**:
  - `ConceptBindingStatus`: Enumeration of binding states (`FULLY_BOUND`, `UNRECOGNIZED_CODE`, `INVALID_SYSTEM`, `MISSING_BINDING`, `DISPLAY_MISMATCH`).
  - `ConceptSuggestion`: Recommended standard ontology mapping.
  - `ConceptAuditItem`: Individual audit finding for a coded element.
  - `OntologyAuditReport`: Aggregated bundle compliance evaluation.
  - `BundleOntologyAuditRequest`: Inbound payload for whole-bundle auditing.
  - `ConceptLookupRequest`, `ConceptLookupResponse`: Single-concept verification models.
  - `ConceptSuggestionRequest`, `ConceptSuggestionResponse`: Natural language search query and ranked results.
  - `TerminologySystemInfo`, `TerminologySystemsResponse`: Authorized terminology registry models.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Binding Classification (`ConceptBindingStatus`)**: Classifies the fidelity of clinical terms into five states: valid code and system with matching display (`FULLY_BOUND`), unknown code in recognized system (`UNRECOGNIZED_CODE`), unauthorized system URI (`INVALID_SYSTEM`), free text lacking coded representation (`MISSING_BINDING`), or valid code with erroneous text label (`DISPLAY_MISMATCH`).
2. **Concept Suggestions (`ConceptSuggestion`)**: Encapsulates standard concept recommendations containing the authoritative system URI, standard code, preferred display name, clinical category, and match confidence score.
3. **Element-Level Audit Findings (`ConceptAuditItem`)**: Tracks the exact JSONPath/element location, declared coding, binding status, official display text, suggestions, and diagnostic remediation message.
4. **Aggregated Bundle Evaluation (`OntologyAuditReport`)**: Evaluates complete FHIR bundles, aggregating total concepts, individual categorization counts, an overall compliance percentage score (0–100%), compliance status flag (`isCompliant`), audit items, and clinical recommendations.
5. **Lookup & Discovery (`ConceptLookupRequest`, `ConceptSuggestionRequest`)**: Provides programmatic facilities to verify exact code validity against authoritative system URIs and to execute natural language fuzzy searches for standard clinical codes.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Unconstrained Bundle Deserialization Memory Exhaustion
`BundleOntologyAuditRequest` defines `bundle: Dict[str, Any] = Field(..., description="FHIR R4 Document Bundle object represented as a dictionary")`. Accepting arbitrary unbounded nested dictionary trees without schema structure, recursive depth limits, or byte size enforcement allows malicious clients to submit multi-megabyte payloads containing deeply nested trees, causing excessive memory consumption and thread starvation during AST traversal.

### Invariant 2: Mathematical Invariants of Audit Aggregation
In `OntologyAuditReport`, `totalConceptsAudited` must equal or exceed the sum of distinct category counts:
$$\text{totalConceptsAudited} \ge \text{fullyBoundCount} + \text{unrecognizedCodeCount} + \text{invalidSystemCount} + \text{missingBindingCount} + \text{displayMismatchCount}$$
Furthermore, `complianceScore` is modeled as an unconstrained `float`, which should be bounded strictly between `0.0` and `100.0`. Similarly, `ConceptSuggestion.confidence` must be bounded between `0.0` and `1.0`.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-TRM-F01` | S2 | `[SEC]` | `terminology_validator.py:90-93` | `BundleOntologyAuditRequest.bundle` accepts arbitrary `Dict[str, Any]` without size or depth bounds |
| `BE-SCH-TRM-F02` | S2 | `[QUAL]` | `terminology_validator.py:33, 67-70` | `confidence` and `complianceScore` lack float range bounds (`0.0..1.0` and `0.0..100.0`) |
| `BE-SCH-TRM-F03` | S3 | `[QUAL]` | `terminology_validator.py:127` | `ConceptSuggestionRequest.query` lacks length constraints (`min_length=1, max_length=200`) |
| `BE-SCH-TRM-F04` | S3 | `[QUAL]` | `terminology_validator.py:61-66` | Category count fields in `OntologyAuditReport` lack `ge=0` non-negative integer bounds |

---

## Layer E: Unapplied Unified Diff Patches for S0–S2 Findings

```diff
--- a/backend/app/schemas/terminology_validator.py
+++ b/backend/app/schemas/terminology_validator.py
@@ -30,7 +30,7 @@
     code: str = Field(..., description="Target standard concept code")
     display: str = Field(..., description="Authoritative standard concept display name")
     category: str = Field(..., description="Clinical category (e.g. condition, observation, procedure)")
-    confidence: float = Field(default=1.0, description="Match confidence score between 0.0 and 1.0")
+    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Match confidence score between 0.0 and 1.0")
 
     model_config = ConfigDict(from_attributes=True)
 
@@ -66,7 +66,7 @@
     displayMismatchCount: int = Field(default=0, description="Count of valid codes with mismatched display text")
     complianceScore: float = Field(
         ...,
-        description="Weighted ontology compliance score (0.0 to 100.0%)",
+        ge=0.0, le=100.0, description="Weighted ontology compliance score (0.0 to 100.0%)",
     )
     isCompliant: bool = Field(
         ...,
@@ -87,7 +87,8 @@
 class BundleOntologyAuditRequest(BaseModel):
     """Request payload for evaluating an entire FHIR R4 Bundle for medical ontology bindings."""
 
-    bundle: Dict[str, Any] = Field(
+    bundle: Dict[str, Any] = Field(
         ...,
         description="FHIR R4 Document Bundle object represented as a dictionary",
     )
```
