# Audit Report: backend/app/schemas/common.py

**Path:** `backend/app/schemas/common.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 57 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Standardized generic API response envelopes, error response models, field-level error details, and pagination metadata for the NIRMAYA platform.
- **Risk Level:** **S3 (Low)**
- **Verdict:** **READY**
- **Single Most Important Finding:** `PaginationMeta` fields (`total_pages`, `has_next`, `has_prev`) are manual fields without automated calculation from `total_count`, `page`, and `limit`, allowing manual service calculations to drift or report inconsistent pagination states.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In large-scale microservice and REST architectures, disparate endpoints often return divergent response shapes (some return bare arrays, some wrap objects in `{data: ...}`, and others use different error formats). This inconsistency complicates frontend client state management and error handling. This file establishes uniform, predictable response envelopes for all successful API operations (`APIResponse[DataT]`), paginated collections (`PaginatedResponse[DataT]`), and structured error payloads (`ErrorResponse`).

### How it works, step by step
1. `APIResponse[DataT]` provides a generic envelope containing `success` (boolean), human-readable `message`, typed payload `data: Optional[DataT]`, UTC `timestamp`, and tracing `request_id`.
2. `ErrorDetail` structures field-level validation errors, capturing the parameter `location`, human-readable `message`, and machine-readable `error_type`.
3. `ErrorResponse` encapsulates business and HTTP errors with a standardized `error_code`, high-level summary `message`, and list of `details`.
4. `PaginationMeta` captures pagination parameters (`total_count`, `page`, `limit`, `total_pages`, `has_next`, `has_prev`).
5. `PaginatedResponse[DataT]` wraps list endpoints with pagination metadata and collection items.

### Concepts and patterns used
- *Generic Pydantic Envelopes:* Using `Generic[DataT]` with `TypeVar("DataT")` to preserve strong type safety for arbitrary domain payloads.
- *Distributed Tracing Traceability:* Attaching `request_id` to both success and error responses for end-to-end log correlation.
- *Machine-Readable Error Codes:* Standard error codes (`VALIDATION_ERROR`, `NOT_FOUND`, `FORBIDDEN`) supporting localized frontend error displays.

### Key lines to read first
- `common.py:10-18`: `APIResponse[DataT]` success wrapper.
- `common.py:28-37`: `ErrorResponse` structured error model.
- `common.py:39-48`: `PaginationMeta` metadata schema.
- `common.py:50-57`: `PaginatedResponse[DataT]` paginated collection wrapper.

### How to change it safely
When modifying generic envelopes, ensure changes maintain compatibility with both Pydantic v2 type checking and FastAPI OpenAPI schema generation.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `typing` (Generic, TypeVar, Optional, List, Any), `pydantic` (BaseModel, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/core/exceptions.py`, throughout API route handlers in `backend/app/api/v1/endpoints/`.
- **Public Surface:** TypeVar `DataT`; Models `APIResponse`, `ErrorDetail`, `ErrorResponse`, `PaginationMeta`, `PaginatedResponse`.

### 2. Security [SEC]
- **Distributed Request Correlation:** In `APIResponse.request_id` and `ErrorResponse.request_id`, attaching correlation IDs enables security forensic investigation without leaking internal server state or stack traces to end users.
- **Sanitized Error Details:** `ErrorResponse` separates high-level user-facing messages from internal diagnostics, preventing disclosure of internal database schema details.

### 3. Code quality [QUAL]
- **Manual Pagination Calculation (`BE-SCH-COM-F01`):** In `PaginationMeta` (lines 39-48), `total_pages`, `has_next`, and `has_prev` are required or independent fields. Adding a `@model_validator(mode="after")` or `model_post_init` that automatically calculates `total_pages = math.ceil(total_count / limit)` and `has_next = page < total_pages` prevents service-level bugs.
- **Missing `from_attributes=True` in Generic Envelopes (`BE-SCH-COM-F02`):** `APIResponse` and `PaginatedResponse` omit `ConfigDict(from_attributes=True)`. While inner `DataT` models often define it, omitting it on the envelope can require extra dictionary unpacking during ORM response generation.

### 4. AI-generated-code smells [QUAL]
- None; the envelope schemas represent standard, clean FastAPI conventions.

### 5. Performance [PERF]
- Generics in Pydantic v2 compile to efficient C-level validation routines with zero runtime performance penalty.

### 6. Error handling & edge cases
- Bounded fields in `PaginationMeta` (`limit: ge=1, le=100`, `page: ge=1`, `total_count: ge=0`) prevent negative or unbounded pagination queries.

### 7. Doc accuracy [DOC]
- Aligns with RESTful API best practices and NIRMAYA design guidelines.

### 8. Tests
- Covered by `backend/tests/test_common.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-COM-F01 | S3 | [QUAL] | 39-48 | `PaginationMeta` requires manual calculation of pages and flags | `total_pages`, `has_next`, `has_prev` not auto-computed | Add post-init computation from count, page, and limit |
| BE-SCH-COM-F02 | S3 | [QUAL] | 10, 50 | Generic wrappers lack `from_attributes=True` | `APIResponse` and `PaginatedResponse` omit ConfigDict | Add `model_config = ConfigDict(from_attributes=True)` |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-COM-F01 · Risk: Low · [UNTESTED]
Automatically calculate pagination indicators in `PaginationMeta`:

```diff
--- a/backend/app/schemas/common.py
+++ b/backend/app/schemas/common.py
@@ -2,4 +2,5 @@
 
+import math
 from typing import Generic, TypeVar, Optional, List, Any
 from datetime import datetime, timezone
-from pydantic import BaseModel, Field
+from pydantic import BaseModel, Field, model_validator
 
@@ -43,4 +44,11 @@ class PaginationMeta(BaseModel):
     limit: int = Field(ge=1, le=100, default=20, description="Page record ceiling")
-    total_pages: int = Field(ge=0, description="Calculated total pages")
+    total_pages: int = Field(default=0, ge=0, description="Calculated total pages")
     has_next: bool = False
     has_prev: bool = False
+
+    @model_validator(mode="after")
+    def compute_pagination_flags(self) -> "PaginationMeta":
+        self.total_pages = math.ceil(self.total_count / self.limit) if self.limit > 0 else 0
+        self.has_next = self.page < self.total_pages
+        self.has_prev = self.page > 1
+        return self
