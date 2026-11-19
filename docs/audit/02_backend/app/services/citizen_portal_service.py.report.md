# Codebase Audit Report: `backend/app/services/citizen_portal_service.py`

**Audit Target**: `backend/app/services/citizen_portal_service.py`  
**Subsystem**: Backend - Citizen Health Portal & Ecosystem Integrations (`backend/app/services/`)  
**File Lines**: 750 LOC  
**Severity Breakdown**: S0: 0 | S1: 1 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `citizen_portal_service.py` service powers the NIRMAYA Citizen Portal dashboard, consolidating three core sovereign health tiles: CoWIN COVID-19/Universal Immunization records, DigiLocker verified digital health documents, and the ABDM longitudinal health timeline.

```
[ Citizen Mobile App / Web Portal ]
                │
                ▼
   [ citizen_portal_service.py ]
        ├── Tile 1: CoWIN Vaccination Records (Dose 1, 2, Precaution)
        ├── Tile 2: DigiLocker Health Locker (Issued Documents & Credentials)
        ├── Tile 3: ABDM PHR Health Records (Consultations, Labs, Prescriptions)
        └── Health Score & Preventative Wellness Engine
                │
                ▼
   [ CitizenOverviewDashboard / Document Download ]
```

### Import / Export Roster
- **Imports**: `datetime`, `logging`, `typing`, `uuid`, `app.core.exceptions`, `app.schemas.citizen_portal`.
- **Exports**: `CitizenPortalService`, `citizen_portal_service`, `get_citizen_overview()`, `get_vaccination_records()`, `get_digilocker_documents()`, `get_abdm_records()`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Dashboard Overview**: Fetches the consolidated citizen health card containing ABHA demographics, upcoming appointments, immunization status, and active prescriptions.
2. **Tile 1 (CoWIN Immunization)**: Retrieves COVID-19 vaccination certificates (Covishield, Covaxin, Corbevax) along with universal childhood immunizations (BCG, OPV, Pentavalent).
3. **Tile 2 (DigiLocker Integration)**: Connects to India's DigiLocker repository to pull digitally signed health cards, insurance policies, and diagnostic reports.
4. **Tile 3 (ABDM Longitudinal Timeline)**: Aggregates historical diagnostic reports, discharge summaries, and prescription slips linked via ABDM HIP care contexts.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Ubiquitous Hardcoded Mock Citizen Personas
Throughout lines 204 to 702, the service relies heavily on synthetic mock branches. If `patient_id` contains `"aarav"` or `"patel"` or `"test"`, it returns pre-fabricated vaccination certificates and mock DigiLocker URIs for fictitious individuals ("Aarav Patel", "Ramesh Patel", "Arun Patel"). Production database queries and live DigiLocker/CoWIN API integrations are bypassed, meaning real patients receive canned demonstration data instead of their authentic medical history.

### 2. IDOR Vulnerability Across Citizen Records
The public methods `get_citizen_overview(patient_id)`, `get_vaccination_records(patient_id)`, and `get_digilocker_documents(patient_id)` accept arbitrary `patient_id` parameters without validating that the authenticated caller's identity (`current_user.id` or `current_user.patient_profile_id`) matches the requested subject. Any authenticated user can enumerate patient IDs and inspect other citizens' medical documents and vaccination certificates (Insecure Direct Object Reference).

### 3. DigiLocker OAuth Token Handling
The service simulates DigiLocker token exchanges without verifying PKCE code verifiers or cryptographic signatures on JWT issuer tokens from `digilocker.gov.in`.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-CPOR-F01` | **S1** | `[SEC/MED]` | `backend/app/services/citizen_portal_service.py:204-702` | All 3 citizen tiles return hardcoded mock data ("Aarav Patel", etc.) based on substring checks, bypassing real database queries and sovereign APIs. |
| `BE-SVC-CPOR-F02` | **S2** | `[SEC]` | `backend/app/services/citizen_portal_service.py:110-140` | Missing authorization check between authenticated session user and requested `patient_id`, allowing cross-user medical record access (IDOR). |
| `BE-SVC-CPOR-F03` | **S3** | `[PERF]` | `backend/app/services/citizen_portal_service.py:480-510` | Inefficient serialization and synchronous deep copying of large mock record trees on every dashboard fetch. |
| `BE-SVC-CPOR-F04` | **S4** | `[DOC]` | `backend/app/services/citizen_portal_service.py:1-45` | Missing documentation detailing DigiLocker OAuth2 redirect URI configuration and security headers. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-CPOR-F01` / `BE-SVC-CPOR-F02`: Authorization Enforcement & Database Query Integration

```diff
--- a/backend/app/services/citizen_portal_service.py
+++ b/backend/app/services/citizen_portal_service.py
@@ -112,8 +112,14 @@ class CitizenPortalService:
     async def get_citizen_overview(
         self,
         patient_id: str,
+        current_user: User,
+        db: AsyncSession,
     ) -> CitizenOverviewResponse:
         """Retrieve complete 3-tile citizen dashboard overview."""
+        # Enforce IDOR protection: user can only view their own or authorized proxy profile
+        if current_user.role != "SUPER_ADMIN" and current_user.patient_profile_id != patient_id:
+            raise PermissionDeniedException("Access to citizen health portal is restricted to profile owner.")
+
+        # Query authoritative patient profile from database instead of mock data
+        patient = await db.scalar(select(PatientProfile).where(PatientProfile.id == patient_id))
+        if not patient:
+            raise EntityNotFoundException("PatientProfile", patient_id)
```
