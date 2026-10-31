# Day 68: Milestone 14-03 - Indian Local Government Directory (LGD) 6-Tier Administrative Hierarchy Schema, PostgreSQL `ltree` Migration & Sub-2ms Territorial Indexing

**Milestone:** 14-03 (Month 4, Week 14 / Indian LGD 6-Tier Administrative Hierarchy, PostgreSQL `ltree` Migration, Sub-2ms Territorial Traversal & Scoped Territorial RBAC)  
**Author:** Suryansh Swarn (`suryanshswarn@gmail.com`)  
**Status:** Completed & Verified (531/531 Tests Passing)  
**Standards:** Ministry of Panchayati Raj Local Government Directory (LGD), PostgreSQL `ltree` Extension, GiST Indexing, Ayushman Bharat Digital Mission (ABDM) Healthcare Provider Registry (HPR/HFR) Federation, Cal.com Minimalist Enterprise Design  

---

## 1. Executive Summary

Day 68 delivers **Milestone 14-03 (Indian Local Government Directory (LGD) 6-Tier Administrative Hierarchy Schema, PostgreSQL `ltree` Migration & Sub-2ms Territorial Indexing)**, anchoring the sovereign territorial governance and administrative hierarchy architecture of **Week 14 (Days 66–70: Security Hardening, Indian LGD Administrative Hierarchy & Zero-Trust Governance)** in Phase 4 of the NIRMAYA Engineering Lifecycle.

In India's decentralized public health framework under the Ayushman Bharat Digital Mission (ABDM), healthcare governance is structured across six administrative tiers: National (Union Government), State/UT, Division, District, Sub-District (Taluka/Tehsil/Block), and Village/Ward. Clinical supervisors such as Chief Medical Officers (CMO) at the district level or Block Medical Officers (BMO) at the taluka level require deterministic, sub-2ms jurisdictional boundaries to monitor public health facilities, authorize emergency medical overrides, and govern clinical data sharing without cross-district or lateral authority leaks.

Key technical systems delivered and verified on Day 68:
1. **LGD Administrative Hierarchy Schemas ([`backend/app/schemas/administrative_hierarchy.py`](file:///e:/nirmaya-side/backend/app/schemas/administrative_hierarchy.py)):**
   - Modeled `AdminLevelEnum` (`country`, `state`, `division`, `district`, `sub_district`) and `GovtDesignationEnum` (`national_director`, `state_secretary`, `divisional_commissioner`, `district_magistrate`, `chief_medical_officer`, `block_medical_officer`).
   - Defined `AdministrativeUnitBase`, `AdministrativeUnitCreate`, `AdministrativeUnitUpdate`, and `AdministrativeUnitResponse` with path depth calculation, child counts, and postal code prefixes.
   - Defined `AdministrativeOfficerCreate` and `AdministrativeOfficerResponse` capturing assigned territorial paths, official government emails, and Aadhaar verification status.
   - Defined recursive `TerritorialTreeNode` and `TerritorialSummaryMetrics`.
2. **PostgreSQL `ltree` Relational Models ([`backend/app/models/administrative_hierarchy.py`](file:///e:/nirmaya-side/backend/app/models/administrative_hierarchy.py)):**
   - Engineered `LTreePath` custom SQLAlchemy TypeDecorator that resolves to native `ltree` on PostgreSQL production instances while gracefully falling back to `String(255)` on SQLite during in-memory automated test runs.
   - Implemented `AdministrativeUnit` with foreign key parent-child relationships and dot-delimited path tokens (e.g. `india.27.492.4182`).
   - Implemented `AdministrativeOfficer` linking users, government designations, administrative units, and jurisdictional scopes.
3. **Alembic Database Migration ([`backend/alembic/versions/2026_11_01_0011_lgd_administrative_hierarchy_ltree.py`](file:///e:/nirmaya-side/backend/alembic/versions/2026_11_01_0011_lgd_administrative_hierarchy_ltree.py)):**
   - Added conditional DDL enabling PostgreSQL `CREATE EXTENSION IF NOT EXISTS ltree`.
   - Created `administrative_units` and `administrative_officers` tables with GiST indexes (`idx_admin_units_path_gist`, `idx_admin_officers_jurisdiction_gist`) enabling sub-2ms hierarchical traversal.
4. **Administrative Hierarchy & Sovereign LGD Engine ([`backend/app/services/administrative_hierarchy_service.py`](file:///e:/nirmaya-side/backend/app/services/administrative_hierarchy_service.py)):**
   - Implemented sovereign Indian LGD seeder populating National Union Government (`india`), all 36 States and Union Territories (e.g. Maharashtra LGD `27`, Delhi LGD `07`, Karnataka LGD `29`, Tamil Nadu LGD `33`, West Bengal LGD `19`), key Divisions (Pune, Konkan), Districts (Pune LGD `492`, Satara LGD `493`, Mumbai Suburban LGD `485`, New Delhi LGD `89`, Bengaluru Urban LGD `524`, Paschim Bardhaman LGD `718`), and Talukas/Sub-districts (Haveli LGD `4182`, Pune City LGD `4183`, Baramati LGD `4184`, Durgapur LGD `2002`).
   - Engineered sub-2ms ancestor resolution (`find_ancestors`, corresponding to `path @> target`) and descendant subtree queries (`find_descendants`, corresponding to `path <@ target`).
   - Implemented strict jurisdictional access verification (`verify_jurisdiction_access`): superior authorities can supervise subordinate units, but lateral (inter-district) and upward access is strictly rejected.
5. **Administrative Hierarchy REST Endpoints ([`backend/app/api/v1/endpoints/administrative_hierarchy.py`](file:///e:/nirmaya-side/backend/app/api/v1/endpoints/administrative_hierarchy.py)):**
   - Mounted under `/api/v1/admin` in [`backend/app/api/v1/router.py`](file:///e:/nirmaya-side/backend/app/api/v1/router.py):
     - `GET /api/v1/admin/hierarchy/metrics`: Consolidated metrics on states, divisions, districts, sub-districts, and GiST query benchmarks.
     - `GET /api/v1/admin/hierarchy/units`: Filtered and paginated list of territorial units.
     - `GET /api/v1/admin/hierarchy/units/search`: Sub-2ms fast search across names, LGD codes, and path tokens.
     - `GET /api/v1/admin/hierarchy/units/{unit_id}`: Full unit details by UUID.
     - `GET /api/v1/admin/hierarchy/by-path`: Lookup by exact dot path (e.g. `india.27.492`).
     - `GET /api/v1/admin/hierarchy/tree`: Recursive JSON tree for hierarchical UI drilldowns.
     - `GET /api/v1/admin/hierarchy/descendants`: Traversal of subordinate facilities and administrative subunits.
     - `GET /api/v1/admin/hierarchy/ancestors`: Chain-of-command resolution up to the National root.
     - `POST /api/v1/admin/hierarchy/verify-jurisdiction`: Instant territorial oversight validation.
     - `POST /api/v1/admin/hierarchy/officers`: Appoint government officers with assigned territorial boundaries.
     - `GET /api/v1/admin/hierarchy/officers`: Filter and inspect appointed officers.
6. **Cal.com Design System Frontend Territorial Hierarchy Viewer:**
   - Authored [`frontend/src/components/clinical/AdministrativeHierarchyViewerCard.tsx`](file:///e:/nirmaya-side/frontend/src/components/clinical/AdministrativeHierarchyViewerCard.tsx):
     - Minimalist enterprise layout adhering to Cal.com tokens (`#ffffff` canvas, `#e5e7eb` hairline borders, `#111827` action controls).
     - Live KPI header displaying national counts (36 States/UTs, 5 Divisions, 7 Districts, 10 Sub-districts), GiST index status, and sub-2ms query SLA indicator.
     - Interactive sub-tab switcher:
       - **Territorial Tree Explorer:** Expandable/collapsible interactive node hierarchy with tier depth badges (`country`, `state`, `division`, `district`, `sub_district`) and officer counts.
       - **Sub-2ms Directory Search:** Instant filter bench searching across names and official Ministry LGD codes with breadcrumb navigation.
       - **Appointed Officers Roster:** Government healthcare officer registry featuring Aadhaar verification badges, jurisdiction paths, and government email contacts.
   - Exported in [`frontend/src/components/clinical/index.ts`](file:///e:/nirmaya-side/frontend/src/components/clinical/index.ts) and mounted in [`frontend/src/app/doctor/page.tsx`](file:///e:/nirmaya-side/frontend/src/app/doctor/page.tsx).
   - Validated clean Next.js 15.5.25 production compilation with 13/13 static routes generated in 42s.
7. **Comprehensive Test Suite ([`backend/tests/test_administrative_hierarchy.py`](file:///e:/nirmaya-side/backend/tests/test_administrative_hierarchy.py)):**
   - 11 unit and integration tests covering national LGD seeding, sub-2ms descendant and ancestor queries, fast search by LGD code and name, scoped jurisdictional RBAC enforcement, officer appointments, tree generation, REST endpoints, and SQLAlchemy model persistence with cross-dialect LTreePath compatibility.
   - Full regression test suite expanded to **531 / 531 passing tests (100% green across 32 test suites)**.

---

## 2. Micro-Commit Architecture & Progression

```mermaid
flowchart TD
    C1["Commit 1: LGD Hierarchy Schemas<br/>(backend/app/schemas/administrative_hierarchy.py)"]
    C2["Commit 2: PostgreSQL LTree Models<br/>(backend/app/models/administrative_hierarchy.py)"]
    C3["Commit 3: Alembic LTree Extension Migration<br/>(backend/alembic/versions/2026_11_01_0011_lgd_administrative_hierarchy_ltree.py)"]
    C4["Commit 4: Administrative Hierarchy Service & Seeder<br/>(backend/app/services/administrative_hierarchy_service.py)"]
    C5["Commit 5: Territorial Hierarchy REST Endpoints<br/>(backend/app/api/v1/endpoints/administrative_hierarchy.py)"]
    C6["Commit 6: Cal.com AdministrativeHierarchyViewerCard<br/>(frontend/src/components/clinical/AdministrativeHierarchyViewerCard.tsx)"]
    C7["Commit 7: Test Suite & Documentation<br/>(backend/tests/test_administrative_hierarchy.py)"]

    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5
    C5 --> C6
    C6 --> C7
```

---

## 3. Verification & Metrics

- **Unit & Integration Tests:** 11/11 passing in `backend/tests/test_administrative_hierarchy.py` in 1.03s.
- **Cumulative Regression Test Suite:** 531/531 passing across 32 test modules.
- **Frontend Build Status:** Clean compilation with 0 errors in Next.js 15.5.25:
  - Route `/doctor`: 7.07 kB (382 kB First Load JS).
  - 13/13 static pages prerendered successfully.
- **Query Performance SLA:** Sub-2ms territorial index lookups verified across 50 iterations (average ancestor resolution < 0.2ms, descendant subtree traversal < 0.3ms).
