# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/monograph.py`
**Audited Path:** `backend/app/schemas/monograph.py`  
**Module:** `backend` | **Subsystem:** Academic Monograph & IEEE Research Manuscript Verification Schemas  
**Severity Classification:** MEDIUM RISK (`[QUAL]` / `[SEC]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/monograph.py` defines the Pydantic schemas for NIRMAYA's academic monograph thesis, formal architectural proofs catalog, empirical performance benchmark scorecards, and the camera-ready IEEE Capstone Research Manuscript (Days 91–95, Milestones 19-01 through 19-05). Designed to structure academic rigor, reproducible systems evaluation, and empirical hypothesis testing for peer-reviewed journal submission (IEEE TKDE), this module structures:
- Monograph chapter metadata, sections, word counts, and diagram tallies (`MonographChapter`, `ChapterSection`, `MonographMetadataResponse`).
- Formal mathematical and cryptographic architectural proofs (`ArchitecturalProof`, `ProofCategoryEnum`).
- Empirical performance, latency, and resource footprint benchmarks (`BenchmarkSummary`, `BenchmarkCategoryEnum`, `BenchmarkStatusEnum`).
- IEEE, APA, and BibTeX academic citations catalog (`CitationItem`, `CitationCatalogSummary`).
- Camera-ready IEEE deliverable packets across Days 91–95:
  - Day 91: Scientific contributions, Related Works comparison matrix Table I (`IeeeManuscriptDay91Overview`, `TableIRelatedWorksMatrix`).
  - Day 92: Dolev-Yao threat models, mathematical formulations, typeset algorithms (`IeeeManuscriptDay92Overview`, `ThreatModelItem`, `AlgorithmListingItem`).
  - Day 93: Cryptographic trace table Table II, mathematical notation catalog Table III, family proxy state machine (`IeeeManuscriptDay93Overview`, `TraceTableSummary`, `NotationTableSummary`).
  - Day 94: Testbed specifications Table IV, gateway ingress benchmarks Table V (50,000 RPS), crypto transfer pipeline Table VI, LGD traversal Table VII, and paired Student's t-test / Wilcoxon signed-rank statistics Table VIII (`IeeeManuscriptDay94Overview`, `TableVIIIStatisticalSignificanceSummary`).
  - Day 95: Complete camera-ready publication overview (`IeeeManuscriptDay95Overview`).

#### 2. Key Components & Class Roster
- `ProofCategoryEnum` & `ArchitecturalProof`: Categorizes mathematical and cryptographic proofs (e.g. Verhoeff D5 group invariance, SHA-256 hash chaining, SQL/MED schema isolation).
- `BenchmarkCategoryEnum` & `BenchmarkSummary`: Tracks throughput, percentiles (P50, P95, P99), container footprint, and test coverage metrics.
- `TableIRelatedWorksMatrix`: Comparative matrix evaluating NIRMAYA against OpenMRS, Bahmni, Epic Systems, Medplum, and ABDM Reference Sandbox across 9 architectural dimensions.
- `ThreatModelItem`: Formal adversary class definitions (e.g., $A_{net}$, $A_{broker}$, $A_{edge}$) under the Dolev-Yao network attacker model.
- `TableVGatewayIngressSummary`: High-throughput gateway saturation metrics confirming 49,974 sustained requests/sec at 1.2ms latency.
- `TableVIIIStatisticalSignificanceSummary`: Two-tailed paired Student's t-test ($t$-statistic), Wilcoxon signed-rank ($z$-score), and Cohen's $d$ effect sizes ($n = 10,000$, $p < 0.001$).
- `IeeeManuscriptDay95Overview`: Camera-ready IEEE manuscript publication metadata referencing LaTeX, Markdown, and BibTeX artifacts.

---

### Layer B: Plain-Language Developer Walkthrough

Unlike standard commercial software projects where technical decisions are undocumented or justified only by developer intuition, NIRMAYA was built as a formal, peer-reviewed digital public infrastructure architecture. Every claim—from how fast it encrypts patient records to how it handles millions of concurrent requests—is backed by mathematical theorems, automated algorithmic proofs, and empirical statistical testing.

`monograph.py` is the data dictionary for this academic and scientific evaluation:
1. It tracks all chapters and sections of the thesis, ensuring word counts and diagram references match up.
2. It structures formal proofs (like `ArchitecturalProof`), recording the exact theorem, mathematical formula, code implementation file, and automated test suite that validates the proof.
3. It formalizes the entire IEEE research manuscript submitted for academic publication:
   - Comparing NIRMAYA to existing hospital systems like Epic and OpenMRS (Table I).
   - Listing formal algorithms with Big-O time and auxiliary space complexities (Algorithms 1, 2, and 3).
   - Documenting rigorous statistical tests (Table VIII) proving with 99.9% statistical confidence ($p < 0.001$) that NIRMAYA's cryptographic pipeline is 14.8x faster than Bahmni and 22.3x faster than OpenMRS.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **Statistical Invariant Verification:** Enforces rigorous academic statistical parameters ($t$-statistic, Wilcoxon $z$, Cohen's $d$, $p$-value threshold $p < 0.001$) across $n = 10,000$ paired execution runs.
- **Complexity Formulations:** `AlgorithmListingItem` documents formal asymptotic complexities ($O(1)$, $O(\log n)$, $O(n)$) alongside target source modules.
- **LaTeX / BibTeX Cross-Referencing:** Binds physical manuscript file paths (`docs/academic/latex/nirmaya_ieee_manuscript.tex`, `references.bib`) directly to metadata responses.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Use of Deprecated Naive Datetime Call (`BE-SCH-MON-F01`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/monograph.py:103`
- **Description:** `MonographMetadataResponse.timestamp` is initialized with `Field(default_factory=datetime.utcnow)`. In Python 3.12+, `datetime.utcnow()` is deprecated because it generates naive datetime objects that lack timezone awareness.
- **Impact:** Python deprecation warnings and potential timezone offset comparison errors.
- **Remediation:** Replace with `default_factory=lambda: datetime.now(timezone.utc)`.

##### Vulnerability 2: Missing Non-Negative and Percentage Boundary Constraints (`BE-SCH-MON-F02`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/monograph.py:38, 48, 325, 329`
- **Description:** `word_count` in `ChapterSection` and `MonographChapter` lacks `ge=0` bounds. In `GatewayIngressBenchmarkRow`, fields `error_rate_pct` and `cpu_utilization_pct` are declared as unbounded floats without `ge=0.0, le=100.0` percentage limits.
- **Impact:** Mathematical invariant violations in benchmark scorecards.
- **Remediation:** Add `ge=0` to word count and `ge=0.0, le=100.0` to percentage fields.

##### Vulnerability 3: Missing ConfigDict from_attributes Across Models (`BE-SCH-MON-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/monograph.py:34, 42, 54, 66, 90, 148, 212, 283, 400, 434`
- **Description:** None of the monograph models declare `model_config = ConfigDict(from_attributes=True)`. If academic benchmark summaries or proof records are stored in a database or extracted from ORM instances, runtime serialization failures will occur.
- **Impact:** Prevents ORM deserialization.
- **Remediation:** Add `model_config = ConfigDict(from_attributes=True)` to master models.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-MON-F01` | S3 | `[QUAL]` | `monograph.py:103` | Uses deprecated naive `datetime.utcnow` instead of `lambda: datetime.now(timezone.utc)` |
| `BE-SCH-MON-F02` | S3 | `[QUAL]` | `monograph.py:38, 48, 325, 329` | Missing percentage bounds (`ge=0.0, le=100.0`) and non-negative word counts |
| `BE-SCH-MON-F03` | S3 | `[QUAL]` | `monograph.py:34, 42, 54, 90` | Missing `ConfigDict(from_attributes=True)` across academic models |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/monograph.py
+++ b/backend/app/schemas/monograph.py
@@ -1,6 +1,6 @@
-from datetime import datetime
+from datetime import datetime, timezone
 from enum import Enum
 from typing import Any, Dict, List, Optional
-from pydantic import BaseModel, Field
+from pydantic import BaseModel, ConfigDict, Field
 
 
@@ -35,3 +35,5 @@ class ChapterSection(BaseModel):
     """Sub-section within an academic monograph chapter."""
+    model_config = ConfigDict(from_attributes=True)
+
     section_id: str = Field(..., description="Unique section slug (e.g., sec-2-1)")
     title: str = Field(..., description="Section title")
-    word_count: int = Field(default=0, description="Approximate word count of section")
+    word_count: int = Field(default=0, ge=0, description="Approximate word count of section")
     abstract: str = Field(..., description="Condensed overview of section concepts")
@@ -48,3 +50,3 @@ class MonographChapter(BaseModel):
     subtitle: str = Field(..., description="Descriptive subtitle")
-    word_count: int = Field(default=0, description="Chapter word count")
+    word_count: int = Field(default=0, ge=0, description="Chapter word count")
     sections: List[ChapterSection] = Field(default_factory=list)
@@ -103,3 +105,3 @@ class MonographMetadataResponse(BaseModel):
     chapters: List[MonographChapter] = Field(default_factory=list)
-    timestamp: datetime = Field(default_factory=datetime.utcnow)
+    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
 
@@ -325,2 +327,2 @@ class GatewayIngressBenchmarkRow(BaseModel):
-    error_rate_pct: float = Field(..., description="Percentage of failed or dropped requests")
+    error_rate_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of failed or dropped requests")
     latency_p50_ms: float = Field(..., description="Median latency in milliseconds")
@@ -329,2 +331,2 @@ class GatewayIngressBenchmarkRow(BaseModel):
-    cpu_utilization_pct: float = Field(..., description="Cluster CPU utilization percentage")
+    cpu_utilization_pct: float = Field(..., ge=0.0, le=100.0, description="Cluster CPU utilization percentage")
     operational_state: str = Field(..., description="System performance regime")
```
