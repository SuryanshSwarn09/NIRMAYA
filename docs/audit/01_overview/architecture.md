# NIRMAYA: System Architecture & Component Interactions

**Audit Layer**: `01_overview`  
**Scope**: High-level platform topology, component decoupling, data flow, and security boundaries.  
**Citations**: `backend/app/main.py:1-94`, `backend/app/api/v1/router.py:1-127`, `frontend/src/middleware.ts:1-79`, `frontend/next.config.ts:1-68`, `docker-compose.yml:1-161`.

---

## 1. Top-Level Architectural Topology

NIRMAYA is architected as a decoupled, dual-tier healthcare platform adhering to Ayushman Bharat Digital Mission (ABDM) and HL7 FHIR Release 4 interoperability specifications. It partitions clinical workflows into four discrete security quadrants (Citizen/Patient, Clinician/Provider, Diagnostic Laboratory, and Territorial Health Administrator).

```mermaid
flowchart TD
    subgraph ClientPlane ["Client Plane (Next.js 15 App Router · Port 3000)"]
        UI_Citizen["Citizen Health Vault<br/><code>/patient</code>"]
        UI_Doctor["Express OPD & Doctor EMR<br/><code>/doctor</code>"]
        UI_Lab["Diagnostic Lab Portal<br/><code>/lab</code>"]
        UI_Admin["Command Center & Admin<br/><code>/admin</code>"]
        EdgeAuth["Edge Auth Middleware<br/><code>frontend/src/middleware.ts</code>"]
        APIClient["Typed API Client<br/><code>frontend/src/lib/api.ts</code>"]
    end

    subgraph EdgeProxy ["Edge Reverse Proxy & Security Ingress"]
        Caddy["Caddy 2 Edge Gateway<br/>(Auto HTTPS · HSTS · Rate-Limiting)"]
    end

    subgraph AppPlane ["Application Plane (FastAPI ASGI · Port 8000)"]
        MainApp["FastAPI Engine<br/><code>backend/app/main.py</code>"]
        SecMiddleware["Telemetry, Request ID & Rate Limiting<br/><code>backend/app/core/middleware.py</code>"]
        APIRouter["Master Route Aggregator (59 Modules)<br/><code>backend/app/api/v1/router.py</code>"]
        AuthService["Auth & RBAC Dependency Guard<br/><code>backend/app/core/dependencies.py</code>"]
    end

    subgraph InteropPlane ["Interoperability & Standards Engine"]
        FHIR_Trans["FHIR R4 Transformers<br/><code>backend/app/fhir/transformers.py</code>"]
        NRCES_Val["NRCES Conformance Validator<br/><code>backend/app/fhir/validators.py</code>"]
        ABDM_Bridge["ABDM M1/M2/M3 Bridge<br/><code>backend/app/services/abdm_*.py</code>"]
        CryptoEngine["Fidelius / ECDH AES-GCM Crypto<br/><code>backend/app/services/abdm_crypto_service.py</code>"]
    end

    subgraph PersistencePlane ["Persistence & Messaging Plane"]
        DBEngine["Async SQLAlchemy 2.0 Engine<br/><code>backend/app/db/session.py</code>"]
        Postgres[("PostgreSQL 16 Cluster<br/>(ACID · Row Locks · LTREE)")]
        Alembic["Alembic Migrations<br/><code>backend/alembic/versions/</code>"]
        RedisBus[("Redis Pub/Sub & In-Memory Bus<br/><code>backend/app/services/websocket_manager.py</code>")]
    end

    %% Client flows
    UI_Citizen & UI_Doctor & UI_Lab & UI_Admin --> EdgeAuth
    EdgeAuth --> APIClient
    APIClient -->|HTTP / JSON| Caddy
    APIClient -.->|WebSocket wss://| Caddy

    %% Edge to App
    Caddy --> MainApp
    MainApp --> SecMiddleware
    SecMiddleware --> APIRouter
    APIRouter --> AuthService

    %% Interop Integration
    APIRouter --> FHIR_Trans
    APIRouter --> ABDM_Bridge
    FHIR_Trans --> NRCES_Val
    ABDM_Bridge --> CryptoEngine

    %% Persistence
    APIRouter --> DBEngine
    DBEngine --> Postgres
    Alembic -.-> Postgres
    MainApp <--> RedisBus
```

---

## 2. End-to-End Clinical Data-Flow: OPD Consultation & FHIR Bundle Minting

The following sequence details an encounter lifecycle from patient discovery through consultation authoring to encrypted HL7 FHIR Bundle generation and ABDM callback dispatch.

```mermaid
sequenceDiagram
    autonumber
    actor Patient as Citizen (Patient)
    actor Doctor as Clinician (Doctor EMR)
    participant Front as Next.js Web App
    participant Edge as Edge Middleware
    participant API as FastAPI Backend
    participant FHIR as FHIR Transformer
    participant DB as PostgreSQL 16
    participant ABDM as National ABDM Gateway

    Patient->>Front: 1. Generate Aadhaar / ABHA OTP Challenge
    Front->>API: POST /api/v1/abdm/m1/generate-otp
    API->>ABDM: Forward demographic verification request
    ABDM-->>API: Challenge transaction ID
    API-->>Front: OTP Challenge Active
    Patient->>Front: Submit 6-digit OTP
    Front->>API: POST /api/v1/abdm/m1/verify-otp
    API->>DB: Mint/Retrieve Patient Vault profile
    API-->>Front: Set HTTP-Only nirmaya_token & nirmaya_role cookie

    Note over Doctor,Front: Clinician Session Active
    Doctor->>Front: Access Express OPD Console (/doctor)
    Front->>Edge: Request /doctor with nirmaya_token cookie
    Edge-->>Front: Permit (Role verified: doctor)
    Doctor->>Front: Prescribe Regimen & Diagnose (Problem List)
    Front->>API: POST /api/v1/soap-notes & POST /api/v1/medication-requests
    API->>DB: Commit Encounter, Condition & MedicationRequest rows
    API->>FHIR: Build OPD Consultation Bundle (Bundle.type = document)
    FHIR->>FHIR: Validate against NRCES Indian FHIR Profile
    FHIR-->>API: Validated FHIR JSON Document
    API->>DB: Store immutable FHIR bundle hash in audit_ledger
    API-->>Front: Prescription PDF + Signed FHIR Bundle returned
```

---

## 3. Structural Security Boundaries

1. **Edge Boundary**: Handled at `frontend/src/middleware.ts:29-68`. Enforces 4-quadrant routing (`/patient`, `/doctor`, `/lab`, `/admin`). Unauthenticated requests are bounced to `/login?returnUrl=...`. Non-admin cross-portal access is rejected via 307 temporary redirects.
2. **Transport Boundary**: Configured via Caddy (`Caddyfile:1-85`) and FastAPI CORS middleware (`backend/app/main.py:60-66`). Preflights allow origins defined in `BACKEND_CORS_ORIGINS`. Security headers (HSTS, CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff) injected via `backend/app/core/cors.py:20-45`.
3. **Application Authorization Boundary**: Enforced per-endpoint in FastAPI via dependencies in `backend/app/core/dependencies.py` (`get_current_user`, `get_current_active_doctor`, `get_current_admin`, `get_current_patient`).
4. **Data Isolation Boundary**: Enforced via tenant context (`backend/app/db/tenant_context.py`) and parameter validation preventing IDOR (Insecure Direct Object Reference) attacks between patient vaults.
