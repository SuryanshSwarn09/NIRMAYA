# Audit Report: backend/app/schemas/administrative_hierarchy.py

**Path:** `backend/app/schemas/administrative_hierarchy.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 129 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for the Indian Local Government Directory (LGD) territorial hierarchy, administrative officer appointments, recursive tree structures, search filters, and national metrics.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** `AdministrativeOfficerBase.gov_email` is defined as a plain string without email format validation or domain constraints (`@gov.in` / `@nic.in`), allowing arbitrary or spoofed email addresses to be registered for high-privilege territorial officers.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In the Indian public healthcare system, administrative governance operates across administrative tiers defined by the Ministry of Panchayati Raj's Local Government Directory (LGD): National, State, Division, District, and Sub-District. Territorial healthcare officers (such as Chief Medical Officers and District Magistrates) hold jurisdiction over specific territorial units represented in PostgreSQL as hierarchical `ltree` paths (e.g., `india.27.492`). This file defines the data contracts used to create, update, query, and navigate these territorial units and officer appointments.

### How it works, step by step
1. `AdminLevelEnum` enumerates territorial tiers: `country`, `state`, `division`, `district`, `sub_district`.
2. `GovtDesignationEnum` enumerates official administrative healthcare designations (`national_director`, `state_secretary`, `district_magistrate`, `chief_medical_officer`, etc.).
3. `AdministrativeUnitBase` and its subclasses (`Create`, `Update`, `Response`) structure territorial units with names, LGD codes, ltree paths, and postal code prefix lists.
4. `AdministrativeOfficerBase` and subclasses structure officer appointments, associating platform users with territorial scopes, official emails, Aadhaar verification flags, and supervising authorities.
5. `TerritorialTreeNode` provides a recursive tree structure allowing frontend client dashboards to render nested administrative dropdowns and drill-downs.
6. `TerritorialHierarchyFilter` and `TerritorialSummaryMetrics` provide search filtering parameters and national summary indicators.

### Concepts and patterns used
- *PostgreSQL LTree Scope Modeling:* Modeling hierarchical territorial containment using dot-delimited paths.
- *Self-Referencing Recursive Schemas:* `TerritorialTreeNode` referencing `List["TerritorialTreeNode"]` for nested navigation.
- *Government Directory Alignment:* LGD codes and official administrative designations aligned with Indian Digital Public Infrastructure.

### Key lines to read first
- `administrative_hierarchy.py:9-28`: `AdminLevelEnum` and `GovtDesignationEnum` definitions.
- `administrative_hierarchy.py:30-46`: `AdministrativeUnitBase` and `Create` models.
- `administrative_hierarchy.py:68-85`: `AdministrativeOfficerBase` and officer appointment parameters.
- `administrative_hierarchy.py:98-109`: `TerritorialTreeNode` recursive tree representation.

### How to change it safely
When modifying territorial schemas, ensure `path` strictly conforms to PostgreSQL `ltree` syntax (alphanumeric labels separated by dots, no hyphens or spaces). Any change to `AdminLevelEnum` must correspond with `backend/app/models/administrative_hierarchy.py`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `enum` (Enum), `typing` (List, Optional), `pydantic` (BaseModel, ConfigDict, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/administrative_hierarchy_service.py`, `backend/app/api/v1/endpoints/administrative_hierarchy.py`.
- **Public Surface:** Enums `AdminLevelEnum`, `GovtDesignationEnum`; Models `AdministrativeUnitBase`, `AdministrativeUnitCreate`, `AdministrativeUnitUpdate`, `AdministrativeUnitResponse`, `AdministrativeOfficerBase`, `AdministrativeOfficerCreate`, `AdministrativeOfficerResponse`, `TerritorialTreeNode`, `TerritorialHierarchyFilter`, `TerritorialSummaryMetrics`.

### 2. Security [SEC]
- **Unvalidated Government Email Domain (`BE-SCH-ADH-F01`):** In `AdministrativeOfficerBase.gov_email` (line 75), the field docstring states "Official @gov.in or @nic.in email address", but the type is raw `str` without `EmailStr` and without domain validation. Anyone registering an administrative officer can pass an unvalidated or commercial email domain (`gmail.com`, `tempmail.com`), breaking sovereign identity integrity.
- **Unsanitized LTree Path (`BE-SCH-ADH-F02`):** In `AdministrativeUnitBase.path` (line 36) and `AdministrativeOfficerBase.jurisdiction_path` (line 74), strings are unvalidated. PostgreSQL `ltree` only allows letters, digits, and underscores separated by periods (`^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$`). If special characters or SQL injection strings are passed, database queries using `ltree` operators will fail with unhandled 500 database errors.

### 3. Code quality [QUAL]
- **Tier Count Discrepancy in Documentation (`BE-SCH-ADH-F03`):** The module docstring and field descriptions refer to a "6-Tier Administrative Hierarchy" (lines 1, 10, 34), but `AdminLevelEnum` defines only 5 tiers (`country`, `state`, `division`, `district`, `sub_district` — missing `block` or `village`).
- Clean use of recursive self-referencing in `TerritorialTreeNode`.

### 4. AI-generated-code smells [QUAL]
- Hardcoded synthetic benchmark flags `sub_2ms_benchmark_passed: bool = True` and `ltree_index_status: str = "GIST_OPTIMIZED"` in `TerritorialSummaryMetrics` defaults (lines 128-129) (`BE-SCH-ADH-F04`).

### 5. Performance [PERF]
- Recursive schema serialization requires low recursion depth due to 5-tier limit; minimal performance overhead.

### 6. Error handling & edge cases
- `AdministrativeUnitUpdate` properly marks all fields as `Optional`, allowing partial updates.

### 7. Doc accuracy [DOC]
- Aligns with Day 85 territorial governance specification.

### 8. Tests
- Covered by `backend/tests/test_administrative_hierarchy.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-ADH-F01 | S2 | [SEC] | 75 | Government officer email lacks format & domain validation | `gov_email: str = Field(...)` | Type as `EmailStr` and add validator checking `@gov.in` / `@nic.in` |
| BE-SCH-ADH-F02 | S2 | [QUAL] | 36, 74 | Unvalidated PostgreSQL `ltree` path syntax | `path: str`, `jurisdiction_path: str` without regex | Add regex validator enforcing `^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$` |
| BE-SCH-ADH-F03 | S3 | [DOC] | 1, 10, 34 | Docstring cites 6-tier hierarchy while enum defines 5 | Cites 6 tiers, defines 5 tiers | Reconcile documentation to reflect 5 tiers |
| BE-SCH-ADH-F04 | S4 | [QUAL] | 128-129 | Hardcoded performance benchmark booleans in response schema | `sub_2ms_benchmark_passed: bool = True` | Calculate dynamically in service layer |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-ADH-F01 · Risk: Low · [UNTESTED]
Enforce email format and government domain restrictions on administrative officers:

```diff
--- a/backend/app/schemas/administrative_hierarchy.py
+++ b/backend/app/schemas/administrative_hierarchy.py
@@ -5,4 +5,4 @@
 from enum import Enum
-from typing import List, Optional
-from pydantic import BaseModel, ConfigDict, Field
+from typing import List, Optional
+from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
 
@@ -74,3 +74,9 @@ class AdministrativeOfficerBase(BaseModel):
     jurisdiction_path: str = Field(..., description="ltree scope defining the officer's territorial boundary")
-    gov_email: str = Field(..., description="Official @gov.in or @nic.in email address")
+    gov_email: EmailStr = Field(..., description="Official @gov.in or @nic.in email address")
     aadhaar_verified: bool = Field(default=True, description="Whether officer passed Aadhaar demographic e-KYC")
+
+    @field_validator("gov_email")
+    def validate_gov_domain(cls, v: str) -> str:
+        if not (v.endswith("@gov.in") or v.endswith("@nic.in")):
+            raise ValueError("Officer email must be an authorized @gov.in or @nic.in address")
+        return v
