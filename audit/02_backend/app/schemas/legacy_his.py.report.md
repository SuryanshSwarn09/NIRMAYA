# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/legacy_his.py`
**Audited Path:** `backend/app/schemas/legacy_his.py`  
**Module:** `backend` | **Subsystem:** Legacy Hospital Information System (HIS) & SQL/MED Federation Engine  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/legacy_his.py` provides the Pydantic data schemas for NIRMAYA's foreign database federation and legacy Hospital Information System (HIS) normalization subsystem. Utilizing ISO/IEC 9075-9 SQL/MED (Management of External Data) Foreign Data Wrappers (postgres_fdw), this engine bridges legacy relational hospital databases (PostgreSQL, MySQL, Oracle, MSSQL) with modern FHIR R4 and ABDM standards. This module structures:
- Connection configurations and security policies for remote legacy hospital databases (`LegacyConnectionConfig`, `LegacySystemType`).
- Real-time foreign server connection telemetry and read-only verification probes (`ServerHealthCheckResult`, `ConnectionStatusEnum`).
- Raw legacy tabular representations of patients, encounters, lab investigations, and pharmacy prescriptions (`LegacyPatientRecord`, `LegacyEncounterRecord`, `LegacyObservationRecord`, `LegacyPrescriptionRecord`).
- Standardized HL7 FHIR R4 chronological timeline entries and federated longitudinal patient portraits (`NormalizedFhirTimelineEntry`, `FederatedPatientView`).
- Paginated multi-hospital federation search queries (`FederationQueryRequest`, `FederationQueryResponse`) and automated PostgreSQL SQL/MED DDL generation envelopes (`SqlMedDdlResponse`).

#### 2. Key Components & Class Roster
- `LegacySystemType`: Enumerates supported foreign database engines (`POSTGRES_FDW`, `MYSQL_LEGACY`, `MSSQL_LEGACY`, `ORACLE_LEGACY`, `SQLITE_LEGACY`, `SIMULATED_HIS`).
- `ConnectionStatusEnum`: Remote database operational health (`ONLINE`, `DEGRADED`, `OFFLINE`, `UNAUTHORIZED`, `READ_ONLY_VERIFIED`).
- `FhirResourceTypeEnum`: Canonical FHIR R4 target resource types produced by normalization (`Patient`, `Encounter`, `Observation`, `MedicationRequest`, `Condition`, `DocumentReference`).
- `LegacyConnectionConfig`: Foreign server connection credentials, host, port, isolated foreign schema (`foreign_his`), timeout budgets, and strict read-only enforcement flags.
- `ServerHealthCheckResult`: Health audit payload capturing ping latency, foreign table count, and read-only validation status.
- `LegacyPatientRecord`, `LegacyEncounterRecord`, `LegacyObservationRecord`, `LegacyPrescriptionRecord`: Native un-normalized legacy schema schemas mapping archaic hospital table columns (`mrn_no`, `pt_id`, `enc_no`, `rx_id`).
- `NormalizedFhirTimelineEntry`: Normalized FHIR event binding canonical JSON resources, provenance SHA-256 hashes, and clinical criticality flags.
- `FederatedPatientView`: Unified 360-degree patient dossier combining demographics, FHIR resources, and aggregated encounter counters.
- `FederationQueryRequest`, `FederationQueryResponse`, `FederationEngineTelemetry`, `SqlMedDdlResponse`: Administrative and operational federation models.

---

### Layer B: Plain-Language Developer Walkthrough

Most established district and private hospitals in India run proprietary, decades-old database systems. Some run on old Oracle installations, others on MySQL, and many on legacy PostgreSQL setups with completely non-standard table and column names (like `pt_id` instead of patient UUID, or `mrn_no` for medical record number). Replacing these legacy databases is economically and clinically impossible for many facilities.

`legacy_his.py` enables NIRMAYA to connect directly to these older databases using PostgreSQL Foreign Data Wrappers (postgres_fdw). Rather than migrating or rewriting the old database:
1. An administrator configures a `LegacyConnectionConfig`. NIRMAYA mounts the foreign database into an isolated read-only schema called `foreign_his` so the hospital's operational database cannot be modified or damaged.
2. The system queries raw rows (`LegacyPatientRecord`, `LegacyEncounterRecord`, `LegacyObservationRecord`) directly through foreign tables.
3. NIRMAYA's normalization pipeline transforms these raw rows into modern `NormalizedFhirTimelineEntry` objects conforming to international HL7 FHIR R4 and Indian ABDM standards.
4. When a physician looks up a patient, `FederatedPatientView` seamlessly aggregates their past history across multiple hospitals into a single, unified longitudinal medical record.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **Read-Only Verification:** `read_only_enforced` and `read_only_verified` guarantee that foreign server connections operate strictly under `SELECT` privileges, preventing foreign data corruption.
- **Provenance Integrity:** `NormalizedFhirTimelineEntry.provenance_hash` computes a cryptographic digest over the source row to ensure forensic traceability back to the foreign server ID.
- **SQL/MED Automation:** `SqlMedDdlResponse` dynamically structures PostgreSQL 16 DDL statements (`CREATE SERVER`, `CREATE USER MAPPING`, `IMPORT FOREIGN SCHEMA`).

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Plaintext Foreign Database Passwords in String Repr (`BE-SCH-HIS-F01`)
- **Severity:** S1 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/legacy_his.py:45`
- **Description:** In `LegacyConnectionConfig`, `password: Optional[str] = Field(None)` is declared as a standard string without `repr=False` or `SecretStr`. When remote database configurations are logged during startup, connection pool initialization, or administrative error handling, raw database passwords for remote hospital databases are printed in plaintext in log files.
- **Impact:** Critical database credential exposure allowing unauthorized access to external hospital infrastructure (CWE-532 / CWE-312).
- **Remediation:** Declare `password: Optional[SecretStr] = Field(None, repr=False)`.

##### Vulnerability 2: Unmasked Patient Demographics and Contact Details in Repr (`BE-SCH-HIS-F02`)
- **Severity:** S2 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/legacy_his.py:72, 75, 76`
- **Description:** In `LegacyPatientRecord`, `full_name`, `cell_phone`, and `legacy_abha` are plain strings without `repr=False`. When federated queries fetch and cache patient records, personal mobile numbers, patient names, and legacy health identifiers are written to server trace logs.
- **Impact:** Leaks patient Personally Identifiable Information (PII) in log pipelines (CWE-532).
- **Remediation:** Mark `full_name`, `cell_phone`, and `legacy_abha` with `repr=False`.

##### Vulnerability 3: Use of Deprecated Naive Datetime UTC Call (`BE-SCH-HIS-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/legacy_his.py:51, 65, 188`
- **Description:** Models initialize timestamps using `Field(default_factory=datetime.utcnow)`. In Python 3.12+, `datetime.utcnow()` is officially deprecated because it produces naive datetime objects without explicit UTC timezone offsets, causing timezone offset bugs when compared with timezone-aware datetimes.
- **Impact:** Runtime deprecation warnings and potential timezone offset bugs.
- **Remediation:** Replace with `Field(default_factory=lambda: datetime.now(timezone.utc))`.

##### Vulnerability 4: Missing Cryptographic Digest Format Constraints on Provenance Hash (`BE-SCH-HIS-F04`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/legacy_his.py:137`
- **Description:** `NormalizedFhirTimelineEntry.provenance_hash` is an unconstrained string without length constraints or 64-character hexadecimal pattern matching.
- **Impact:** Corrupted or invalid hash values pass validation unchecked.
- **Remediation:** Add `pattern=r"^[a-fA-F0-9]{64}$"` and `min_length=64, max_length=64`.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-HIS-F01` | S1 | `[SEC]` | `legacy_his.py:45` | Foreign database password in `LegacyConnectionConfig` lacks `repr=False`/`SecretStr` |
| `BE-SCH-HIS-F02` | S2 | `[SEC]` | `legacy_his.py:72, 75, 76` | Patient demographic name, phone, and ABHA unmasked in `repr` |
| `BE-SCH-HIS-F03` | S3 | `[QUAL]` | `legacy_his.py:51, 65, 188` | Uses deprecated naive `datetime.utcnow` instead of `lambda: datetime.now(timezone.utc)` |
| `BE-SCH-HIS-F04` | S3 | `[QUAL]` | `legacy_his.py:137` | `provenance_hash` lacks 64-character hex regex validation |
| `BE-SCH-HIS-F05` | S3 | `[QUAL]` | `legacy_his.py:36, 127, 141` | Missing `ConfigDict(from_attributes=True)` across data models |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/legacy_his.py
+++ b/backend/app/schemas/legacy_his.py
@@ -1,7 +1,7 @@
-from datetime import datetime
+from datetime import datetime, timezone
 from enum import Enum
 from typing import Any, Dict, List, Optional
-from pydantic import BaseModel, Field
+from pydantic import BaseModel, ConfigDict, Field, SecretStr
 
 
@@ -37,2 +37,4 @@ class LegacyConnectionConfig(BaseModel):
     """Connection parameters for a remote hospital database."""
+    model_config = ConfigDict(from_attributes=True)
+
     server_id: str = Field(..., description="Unique slug identifier for foreign server")
@@ -45,3 +47,3 @@ class LegacyConnectionConfig(BaseModel):
     username: str = Field(..., description="Read-only sync database user")
-    password: Optional[str] = Field(None, description="Password or secret credential token")
+    password: Optional[SecretStr] = Field(None, repr=False, description="Password or secret credential token")
     schema_prefix: str = Field(default="foreign_his", description="Isolated target schema")
@@ -51,3 +53,3 @@ class LegacyConnectionConfig(BaseModel):
     is_active: bool = Field(default=True, description="Whether server is enabled for federation")
-    created_at: datetime = Field(default_factory=datetime.utcnow)
+    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
 
@@ -72,5 +74,5 @@ class LegacyPatientRecord(BaseModel):
     mrn_no: str
-    full_name: str
+    full_name: str = Field(repr=False)
     dob_str: str
     gender_char: str = Field(..., description="'M', 'F', or 'O'")
-    cell_phone: Optional[str] = None
-    legacy_abha: Optional[str] = None
+    cell_phone: Optional[str] = Field(None, repr=False)
+    legacy_abha: Optional[str] = Field(None, repr=False)
@@ -137,3 +139,8 @@ class NormalizedFhirTimelineEntry(BaseModel):
     source_system_type: LegacySystemType
-    provenance_hash: str
+    provenance_hash: str = Field(
+        ...,
+        pattern=r"^[a-fA-F0-9]{64}$",
+        min_length=64,
+        max_length=64,
+    )
     is_critical: bool = False
```
