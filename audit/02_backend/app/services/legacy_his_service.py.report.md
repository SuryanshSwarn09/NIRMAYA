# Codebase Technical Audit Report: `backend/app/services/legacy_his_service.py`

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`legacy_his_service.py` implements an enterprise PostgreSQL Foreign Data Wrapper (`postgres_fdw`) and SQL/MED (Management of External Data, ISO/IEC 9075-9) federation architecture. It bridges legacy, non-standard Hospital Information Systems (e-Hospital v12, Bahmni MySQL, MedSys, and PHC edge SQLite appliances) into NIRMAYA's unified clinical timeline. The service enforces strict read-only execution guardrails, transforms heterogeneous legacy relational tables into bijectively mapped HL7 FHIR Release 4 resources, and provides multi-tier caching with engine telemetry.

### System Topology & SQL/MED Architecture
```
  [ NIRMAYA Core Engine ]
            |
  (SQL/MED Federated Query)
            v
  +-------------------------------------------------------+
  |             LegacyHisFederationService                |
  +-------------------------------------------------------+
  | - Read-Only SQL Guardrails (Prohibited Mutation Set)  |
  | - Multi-Tier TTL In-Memory Query Cache                |
  | - HL7 FHIR R4 Normalizer (Patient/Enc/Obs/MedRx)       |
  | - SQL/MED DDL Script Synthesizer                      |
  +-------------------------------------------------------+
        |                 |                 |
  (postgres_fdw)     (MySQL FDW)       (SQLite FDW)
        v                 v                 v
  [ Delhi Civil ]   [ KEM Mumbai ]    [ Alwar PHC ]
  (e-Hospital)      (Bahmni)          (Edge Appliance)
```

### Module Metadata & Imports/Exports
- **Module Path:** `backend/app/services/legacy_his_service.py`
- **Component Classification:** Data Integration & SQL/MED Federation Engine
- **Lines of Code:** 1135 LOC
- **Imports:** `hashlib`, `json`, `re`, `time`, `datetime`, `typing`, `app.schemas.legacy_his.*`
- **Primary Export:** `legacy_his_service` (Global Singleton Instance)

---

## Layer B: Plain-Language Developer Walkthrough

The service abstracts heterogeneous legacy clinical databases through three synchronized subsystems:
1. **Server Management & Health Inspection**: Maintains connections to registered foreign servers (`his-delhi-civil-01`, `his-mumbai-kingedward-02`, `his-bangalore-victoria-03`, `his-rural-phc-alwar-04`). `check_server_health()` evaluates connectivity, simulated ping latencies (3.1 ms – 14.2 ms), and confirms read-only posture.
2. **Read-Only SQL Guardrails (`validate_read_only_query`)**: Before dispatching external queries, the SQL statement is stripped of comments and tokenized. If any prohibited mutation keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `EXEC`) appear as standalone words, a `LegacyHisSecurityException` is thrown and violation telemetry is incremented.
3. **HL7 FHIR R4 Bijective Normalization Pipeline**: Converts legacy relational tuples into standard FHIR R4 resources:
   - `normalize_patient_to_fhir()`: Maps legacy demographics and MRN to FHIR `Patient`.
   - `normalize_encounter_to_fhir()`: Maps legacy visits and ICD-10 diagnosis codes to FHIR `Encounter`.
   - `normalize_observation_to_fhir()`: Maps legacy lab results and reference ranges using a curated LOINC mapping dictionary (`GLUCOSE: 1558-6`, `HBA1C: 4548-4`, `CREATININE: 2160-0`) to FHIR `Observation`.
   - `normalize_prescription_to_fhir()`: Maps legacy drug names and schedules to FHIR `MedicationRequest`.
4. **Federated Timeline Synthesis & DDL Generation**: Aggregates records into an chronological patient portrait with provenance hashes and generates ISO/IEC 9075-9 compliant PostgreSQL DDL for setting up foreign servers, user mappings, and foreign tables.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Strict Read-Only Immutability
NIRMAYA must never mutate, corrupt, or lock historical clinical records residing in third-party hospital databases. The service enforces this at the application level via `PROHIBITED_MUTATION_KEYWORDS` and at the database level via `OPTIONS (read_only_enforced 'true')` in generated SQL/MED DDL.

### Invariant 2: Cryptographic Timeline Provenance
Every entry in a federated patient timeline includes an immutable SHA-256 provenance hash computed from its origin server, unique record identifier, and timestamp or clinical values:
$$\text{ProvenanceHash} = \text{SHA-256}(\text{source\_server\_id} \parallel \text{record\_id} \parallel \text{clinical\_data})$$
This prevents cross-hospital record tampering and enables verifiability under the ABDM ecosystem.

### Invariant 3: LOINC Standard Semantic Grounding
Legacy laboratory tests with arbitrary proprietary local names are semantically grounded into international LOINC standards using `LOINC_MAP` (lines 47–57), guaranteeing interoperability when exporting records across state and central health repositories.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
|---|---|---|---|---|
| `BE-SVC-HIS-F01` | **S1** | `[SEC]` | `backend/app/services/legacy_his_service.py:470-490` | AST-Free Regex-Based SQL Mutation Filter Bypass. `validate_read_only_query()` parses keywords with simple regex `\b[A-Z_]+\b`. An attacker can bypass regex matching via SQL obfuscation or dialect-specific features (e.g. `COPY ... FROM PROGRAM`, stored procedures, comment tricks, CTE statements like `WITH cte AS (UPDATE ... RETURNING ...)` where keywords might be escaped or in lower-case hex, or nested string literals). |
| `BE-SVC-HIS-F02` | **S1** | `[SEC]` | `backend/app/services/legacy_his_service.py:795-845, 87-95` | In-Memory Cache Has No LRU Maxsize or Eviction Strategy. `self._cache` grows unboundedly on every unique search query, enabling memory exhaustion DoS when queried with arbitrary random search terms. |
| `BE-SVC-HIS-F03` | **S2** | `[QUAL]` | `backend/app/services/legacy_his_service.py:80-90, 140-465` | Simulated Mock Data Engine Embedded in Production Service Singleton. Hardcoded mock patients (Ramesh Sharma, Sunita Patel, Arun Krishnan) and encounters run in memory alongside real federation logic instead of an abstract repository pattern with PostgreSQL engine connections. |
| `BE-SVC-HIS-F04` | **S2** | `[PERF]` | `backend/app/services/legacy_his_service.py:890-960` | Quadratic O(N*M) Unindexed Timeline Compilation. Loops over `_encounters_db`, `_observations_db`, and `_prescriptions_db` with list comprehensions for every timeline fetch without patient ID indexing. |
| `BE-SVC-HIS-F05` | **S3** | `[PERF]` | `backend/app/services/legacy_his_service.py:1010-1090` | SQL/MED DDL Generates Fixed Password Placeholder (`${LEGACY_HIS_DB_PASSWORD}`) Without Password Escaping or Role-Level Security (RLS) Grants. |
| `BE-SVC-HIS-F06` | **S4** | `[DOC]` | `backend/app/services/legacy_his_service.py:32-38` | Missing Architectural Documentation for Cross-Database Collation and Character Encoding (UTF-8 vs Latin1) Mappings across Heterogeneous HIS Systems. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch 1: Implement LRU Cache Capacity Cap (`BE-SVC-HIS-F02`)
```diff
--- a/backend/app/services/legacy_his_service.py
+++ b/backend/app/services/legacy_his_service.py
@@ -87,4 +87,5 @@ class LegacyHisFederationService:
         self._servers: Dict[str, LegacyConnectionConfig] = {}
         self._cache: Dict[str, Tuple[float, Any]] = {}
         self._cache_ttl_seconds: int = 300
+        self._cache_max_entries: int = 5000
 
@@ -840,4 +841,8 @@ class LegacyHisFederationService:
         resp = FederationQueryResponse(...)
+        if len(self._cache) >= self._cache_max_entries:
+            # Evict oldest entry
+            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
+            del self._cache[oldest_key]
         self._cache[cache_key] = (now, resp)
         return resp
```

### Patch 2: Add Blocked Execution for Stored Procedure Keywords (`BE-SVC-HIS-F01`)
```diff
--- a/backend/app/services/legacy_his_service.py
+++ b/backend/app/services/legacy_his_service.py
@@ -40,3 +40,4 @@ class LegacyHisFederationService:
         "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
         "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE", "RENAME",
-        "MERGE", "UPSERT", "REPLACE"
+        "MERGE", "UPSERT", "REPLACE", "COPY", "CALL", "DO", "VACUUM",
+        "REINDEX", "LOCK"
```
