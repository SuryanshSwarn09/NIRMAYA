# Day 75: PostgreSQL Foreign Data Wrapper (`postgres_fdw`) & Legacy HIS Read-Only Federation Adapter

**Milestone:** 15-05  
**Theme:** Week 15: Dual-Mode Edge Node Appliance, Docker Containerization & Cloud Deployment  
**Status:** Completed (630 Tests Passing across 39 Modules, 100% Green)

---

## Executive Summary

Across the Indian public and private healthcare ecosystem, thousands of primary health centres, district civil hospitals, and multi-specialty clinical networks already operate mission-critical **Hospital Information Systems (HIS)**, **Electronic Medical Record (EMR)** solutions, and **Laboratory Information Management Systems (LIMS)**. These installations persist decades of clinical history in heterogeneous relational database engines:
- **Legacy PostgreSQL** (e-Hospital, MedSys v9.6–v14 on-premise clusters)
- **Legacy MySQL / MariaDB** (OpenEMR, Bahmni, custom PHP/ASP.NET hospital portals)
- **Legacy SQLite / Edge Appliances** (offline clinic packages)
- **Legacy Microsoft SQL Server / Oracle** (proprietary enterprise hospital ERPs)

A destructive "rip-and-replace" or heavy ETL migration is non-viable due to medical-legal record retention mandates (7 to 10 years under Indian NMC regulations) and the impossibility of halting daily outpatient (OPD) registration and billing operations.

**Day 75 (Milestone 15-05)** delivers NIRMAYA's enterprise **PostgreSQL Foreign Data Wrapper (`postgres_fdw`) & Legacy HIS Read-Only Federation Adapter**. Built on the ISO/IEC 9075-9 SQL/MED (Management of External Data) standard and an enterprise multi-engine read-only connection pooling layer, NIRMAYA enables clinicians to query live patient demographics, past encounters, diagnostic labs, and active prescriptions from existing hospital databases in real time, with automatic on-the-fly normalization into standard **HL7 FHIR R4** resources.

---

## Key Deliverables & Architectural Implementation

### 1. ISO/IEC 9075-9 SQL/MED Specification & postgres_fdw Extension
- Configured PostgreSQL 16 `postgres_fdw` extension with dedicated `foreign_his` isolated schemas.
- Foreign server connection definition with optimized fetch sizes (`fetch_size '100'`) and remote cost estimation (`use_remote_estimate 'true'`).
- Automated DDL generator producing standard `CREATE EXTENSION`, `CREATE SERVER`, `CREATE USER MAPPING`, and `CREATE FOREIGN TABLE` statements for `legacy_patients`, `legacy_encounters`, `legacy_observations`, and `legacy_prescriptions`.

### 2. Strict Read-Only Security Guardrails
- **Transaction-Level Guardrail:** Enforces `SET TRANSACTION READ ONLY;` on all foreign connection sessions.
- **SQL AST Inspection Engine:** Prohibits any mutating SQL token (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `EXEC`, `GRANT`, `REVOKE`, `MERGE`, `UPSERT`).
- Dedicated read-only database user credentials (`readonly_nirmaya_sync`).

### 3. Bijective HL7 FHIR R4 Translation Pipeline
- **Patient Normalization:** Maps legacy demographics (`pt_id`, `mrn_no`, `gender_char`, `dob_str`) to FHIR R4 `Patient` resources with official MRN identifiers and ABHA tags.
- **Encounter Normalization:** Converts legacy visit records into FHIR R4 `Encounter` resources with outpatient/emergency classification and ICD-10 diagnosis binding.
- **Observation & Lab Normalization:** Maps legacy laboratory investigations to FHIR R4 `Observation` resources with standardized LOINC codes (e.g., Blood Glucose $\to$ `1558-6`, HbA1c $\to$ `4548-4`, Creatinine $\to$ `2160-0`, Hemoglobin $\to$ `718-7`, Potassium $\to$ `2823-3`).
- **Medication Request Normalization:** Converts legacy prescription rows into FHIR R4 `MedicationRequest` resources with structured dosage, frequency, and duration instructions.

### 4. Multi-Tier Query Caching & Telemetry Engine
- In-memory LRU cache with 300-second TTL shielding legacy hospital databases from repetitive query spikes.
- Live telemetry metrics tracking active foreign servers, total queries executed, cache hit ratio percentage, and average sub-15ms query latencies.

### 5. FastAPI REST API Endpoints (`/api/v1/his/*`)
- `GET /api/v1/his/servers`: List registered external hospital databases.
- `POST /api/v1/his/servers/test`: Ping and verify read-only connection health.
- `POST /api/v1/his/servers`: Register new foreign hospital server.
- `GET /api/v1/his/patients`: Search federated patients across foreign tables by MRN, name, phone, or ABHA.
- `GET /api/v1/his/patients/{patient_id}`: Retrieve single federated patient portrait.
- `GET /api/v1/his/patients/{patient_id}/timeline`: Retrieve chronological FHIR R4 clinical timeline.
- `POST /api/v1/his/import/fhir`: Formally import federated legacy record into native sovereign vault with cryptographic provenance hash.
- `GET /api/v1/his/telemetry`: Live federation engine telemetry metrics.
- `GET /api/v1/his/ddl`: Generate SQL/MED DDL scripts for database administrators.

### 6. Cal.com Frontend Dashboard Component (`LegacyHisFederationCard.tsx`)
- High-density card following Cal.com monochrome design tokens (`#ffffff` canvas, `#f5f5f5` card surfaces, `#111111` action buttons, `#e5e7eb` hairline borders).
- Interactive tabs:
  - **Federated Patient Explorer:** Debounced search, clinical timeline inspector, raw SQL row vs. FHIR R4 JSON preview, and "Import to Native Vault" action.
  - **Foreign Servers Fleet:** Real-time health badges (`READ_ONLY_VERIFIED`), ping latency monitor, and table mapping metrics.
  - **SQL/MED DDL Generator:** Interactive syntax-highlighted DDL script viewer.
- Mounted inside `/doctor` clinical portal with clean Next.js 15 compilation.

---

## Verification & Test Results

- **Dedicated Test Suite (`backend/tests/test_legacy_his_federation.py`):**
  - **16/16 tests passing (100% green in 1.25s)**.
- **Cumulative Regression Test Suite:**
  - **630/630 tests passing across 39 test modules (100% green)**.
- **Frontend Production Build:**
  - Next.js 15 Standalone output: **13/13 static and dynamic routes compiled cleanly** (`npm run build`).
  - TypeScript Typecheck: **100% clean compilation** (`tsc --noEmit`).
