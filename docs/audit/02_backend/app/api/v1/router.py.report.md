# NIRMAYA Codebase Technical Audit Report

## File Identity
- **File Path**: `backend/app/api/v1/router.py`
- **Subsystem**: API v1 Routing Subsystem
- **Component**: Master Version 1 Router Aggregator
- **Layer**: Routing & Presentation Layer

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Module Boundary
```
                   [app/main.py]
                         │
                         ▼
             [app/api/v1/router.py]  <-- api_router = APIRouter()
                         │
       ┌─────────────────┼──────────────────┐
       │ (Prefix: "")    │ (Specific)       │ (Security)
       ▼                 ▼                  ▼
[health, meta,       [/auth, /patients, [/security (x2),
 patient_auth,        /doctors,          /emergency/btg,
 digilocker,          /admin, /edge,     /audit/ledger,
 abdm_m1, abdm,       /abdm/m2/bridge,   /abdm/security]
 observations,        /abdm/m3/*,
 soap_notes, ...]     /fhir, /queue]
```

### Imports & Exports
- **Imports**: `APIRouter` from `fastapi`, and 57 subrouter modules from `app.api.v1.endpoints`.
- **Exports**: `api_router: APIRouter`
- **Downstream Consumers**: `backend/app/main.py` (`app.include_router(api_router, prefix="/api/v1")`).

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/api/v1/router.py` is the central traffic switchboard for the entire NIRMAYA application. It instantiates `api_router = APIRouter()` and proceeds to assemble 57 submodules into a unified OpenAPI documentation schema and route table.

The registration is organized systematically:
1. Base telemetry and health: `health`, `meta`
2. Authentication & Identity: `auth`, `patient_auth`, `digilocker`
3. ABDM Milestone 1, 2, 3 suites: `abdm_m1`, `abdm_issuance`, `abdm_m2_bridge`, `abdm_m3_consent`, `abdm_m3_crypto`, `abdm_m3_transfer`, `abdm_m3_hiu`, `abdm_m3_audit`, `abdm_certification`, `abdm_security_audit`
4. Clinical Interoperability & FHIR: `fhir_validator`, `terminology_validator`
5. Real-Time & Cockpit Services: `websockets`, `opd_queue`, `clinical_alerts`, `emergency_vault`, `audit_ledger`
6. Security & ASVS: `security_scan`, `asvs_audit`
7. Clinical EMR: `patients`, `doctors`, `appointments`, `conditions`, `observations`, `soap_notes`, `diagnostics`, `medications`, `medication_requests`, `medication_dispenses`
8. Administrative Governance & Edge Sync: `administrative_hierarchy`, `delegation`, `command_center`, `container`, `orchestration`, `edge_sync`, `legacy_his`, `monograph`, `benchmarks`, `demo`, `audit`, `release`
9. DPDP Act & Citizen Portals: `family_proxy`, `child_abha`, `guardian_delegation`, `workflow_isolation`, `guardian_conflict`, `national_gateway`, `citizen_portal`, `express_consultation`, `accessibility`

---

## Layer C: Technical Deep Dive & Invariant Analysis

1. **Prefix Collusion Risk via Empty String (`prefix=""`)**: 
   Over 25 subrouters are mounted with `prefix=""`. When an APIRouter is mounted with `prefix=""`, all route paths defined inside that subrouter are bound directly at the root of `/api/v1/`. For instance, if both `conditions.router` and `observations.router` had an endpoint `@router.get("/")` or `@router.get("/summary")`, FastAPI would silently register only the first one declared, causing silent route collision and endpoint shadowing. Every endpoint file using `prefix=""` must declare unique path prefixes internally.
2. **Double Mounting on `/security` Prefix**:
   - Line 85: `api_router.include_router(security_scan.router, prefix="/security", tags=["Security & Vulnerability Auditing"])`
   - Line 86: `api_router.include_router(asvs_audit.router, prefix="/security", tags=["OWASP ASVS & DoS Shield"])`
   Both routers claim `/security`. If their internal routes overlap (e.g. both define `@router.get("/status")`), the latter will shadow the former.
3. **OpenAPI Schema Tag Organization**:
   Tags are assigned to group endpoints in Swagger UI. However, several modules share identical or similar tags (`Security & Vulnerability Auditing` vs `OWASP ASVS & DoS Shield`), creating a long 50+ item tag sidebar in the OpenAPI documentation.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-API-RTR-F01` | **S2** | `[QUAL]` | `backend/app/api/v1/router.py:63-118` | Widespread use of `prefix=""` across 25+ subrouters increases route collision and silent shadowing risk in `/api/v1/` namespace. |
| `BE-API-RTR-F02` | **S2** | `[QUAL]` | `backend/app/api/v1/router.py:85-86` | Duplicate prefix `/security` used for both `security_scan` and `asvs_audit`, creating path conflict surface. |
| `BE-API-RTR-F03` | **S3** | `[DOC]` | `backend/app/api/v1/router.py:62` | `api_router` lacks global versioning docstrings and route collision assertion guards. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-API-RTR-P01`: Disambiguate Security Route Prefixes

```diff
--- a/backend/app/api/v1/router.py
+++ b/backend/app/api/v1/router.py
@@ -82,8 +82,8 @@ api_router.include_router(opd_queue.router, prefix="/queue", tags=["OPD Consulta
 api_router.include_router(clinical_alerts.router, prefix="/alerts", tags=["Clinical Alerts & Lab Panic Values"])
 api_router.include_router(emergency_vault.router, prefix="/emergency/btg", tags=["Break-The-Glass Emergency Access"])
 api_router.include_router(audit_ledger.router, prefix="/audit/ledger", tags=["Audit Ledger & Emergency Dispatch"])
-api_router.include_router(security_scan.router, prefix="/security", tags=["Security & Vulnerability Auditing"])
-api_router.include_router(asvs_audit.router, prefix="/security", tags=["OWASP ASVS & DoS Shield"])
+api_router.include_router(security_scan.router, prefix="/security/sast", tags=["Security & Vulnerability Auditing"])
+api_router.include_router(asvs_audit.router, prefix="/security/asvs", tags=["OWASP ASVS & DoS Shield"])
 api_router.include_router(abdm.router, prefix="", tags=["ABDM Gateway & National Interoperability"])
 api_router.include_router(patients.router, prefix="/patients", tags=["Patient Vault"])
```
