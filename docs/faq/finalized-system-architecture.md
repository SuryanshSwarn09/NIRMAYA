# Project NIRMAYA: Finalized System Architecture & Ecosystem Specification

**Release Version:** `v1.0.0` (Production Master Plan)  
**Standard Compliance:** HL7 FHIR Release 4 & Ayushman Bharat Digital Mission (ABDM M1 / M2 / M3)  
**Author:** Suryansh Swarn (`suryanshswarn@gmail.com`)

---

## 1. Executive Visual Architecture (Mermaid C4 System Diagram)

```mermaid
graph TB
    %% ==========================================
    %% 1. PRESENTATION TIER: CAL.COM DESIGN SYSTEM
    %% ==========================================
    subgraph UI_TIER["1. Multi-Stakeholder UI Portals (Next.js 15 + Cal.com Design System)"]
        direction TB
        UI_PATIENT["<b>Patient Health Vault</b><br/>• ABHA ID & QR Card<br/>• Problem List & Vitals Telemetry<br/>• e-Prescription & Lab Locker<br/>• ABDM Consent Manager"]
        UI_DOCTOR["<b>Clinician EMR Workspace</b><br/>• Real-time Consultation Queue<br/>• ACID Slot Availability Engine<br/>• Structured SOAP Notes<br/>• e-Prescribing Pad & DDI CDS<br/>• Lab ServiceRequest Ordering"]
        UI_DIAG["<b>Diagnostic Lab Gateway</b><br/>• Accession & Specimen Ingest<br/>• LOINC Observation Form<br/>• Cryptographic PDF Signer<br/>• DiagnosticReport FHIR Dispatch"]
        UI_PHARM["<b>Pharmacy Fulfillment Desk</b><br/>• MedicationDispense Lifecycle<br/>• Batch & Expiry Tracker<br/>• Generic Substitution Audit<br/>• Dispense Verification Scan"]
        UI_TELE["<b>WebRTC Telehealth Suite</b><br/>• P2P Video Consultation<br/>• Real-time Audio/Video Mesh<br/>• Encrypted In-Call Chat<br/>• Co-presence Indicators"]
    end

    %% ==========================================
    %% 2. API GATEWAY & SECURITY LAYER
    %% ==========================================
    subgraph GATEWAY_TIER["2. API Gateway & Security Perimeter (FastAPI + Async Python 3.12)"]
        direction TB
        GW_REVERSE["<b>Reverse Proxy & TLS Terminator</b><br/>Nginx / Traefik • HTTP/2 • TLS 1.3"]
        GW_ROUTER["<b>FastAPI Core APIRouter (/api/v1)</b><br/>OpenAPI 3.1 • Automatic Pydantic v2 Validation"]
        GW_SEC["<b>Security & Rate Limiting</b><br/>Sliding-Window Limiter • CORS Policy • Security Headers"]
        GW_AUTH["<b>Identity & RBAC Engine</b><br/>Supabase JWT Auth • ABHA Token Broker • Multi-Role Guards"]
        GW_WS["<b>Real-Time Event Gateway</b><br/>WebSockets • WebRTC Signaling Server • Telemetry Hub"]
        GW_AUDIT["<b>Distributed Audit Logger</b><br/>W3C Trace Context • Correlation ID (X-Request-ID)"]
    end

    %% ==========================================
    %% 3. CLINICAL SERVICES ENGINE
    %% ==========================================
    subgraph CORE_TIER["3. Core Clinical Domain Services"]
        direction TB
        SRV_SLOT["<b>Appointment & Slot Engine</b><br/>• ACID Row-Level Locking (SELECT FOR UPDATE)<br/>• 10-Minute Redis Ephemeral Slot Holds<br/>• Multi-Clinician Calendar Engine"]
        SRV_PROBLEM["<b>Problem List & Condition Engine</b><br/>• SNOMED-CT Clinical Findings<br/>• ICD-10 Diagnostic Classifications<br/>• Active/Resolved Lifecycle Machine"]
        SRV_VITAL["<b>Vitals & Observation Telemetry</b><br/>• LOINC Panel Coded Telemetry<br/>• Physiological Ranges & Critical Alerts<br/>• Longitudinal Trend Analysis"]
        SRV_SOAP["<b>Structured SOAP Notes Engine</b><br/>• S-O-A-P LOINC Document Sections<br/>• Chief Complaint Coding<br/>• SHA-256 Cryptographic Note Lock"]
        SRV_DIAG["<b>Diagnostic Order & Report Engine</b><br/>• ServiceRequest Workflow<br/>• LOINC Test Requisitions<br/>• DiagnosticReport Result Delivery"]
        SRV_RX["<b>e-Prescribing & DDI Safety Engine</b><br/>• Structured Dosage & Timing Instructions<br/>• Rule-Based Drug-Drug Interactions (CDS)<br/>• Allergy & Contraindication Guardrails<br/>• SHA-256 Tamper-Evident Signatures"]
        SRV_DISPENSE["<b>Pharmacy Dispense Service</b><br/>• Preparation -> In-Progress -> Completed<br/>• Lot/Batch & Expiration Enforcement<br/>• Generic Substitution Governance"]
    end

    %% ==========================================
    %% 4. INTEROPERABILITY & ABDM LAYER
    %% ==========================================
    subgraph INTEROP_TIER["4. Healthcare Interoperability & Cryptographic Trust Layer"]
        direction TB
        FHIR_TRANS["<b>HL7 FHIR Release 4 Transformer Engine</b><br/>• Patient • Practitioner • Encounter<br/>• Condition • Observation • ServiceRequest<br/>• DiagnosticReport • Medication<br/>• MedicationRequest • MedicationDispense<br/>• Composition • Bundle (Document & Collection)"]
        ABDM_GATEWAY["<b>ABDM Connector & Sandbox Bridge</b><br/>• ABHA M1: National Health ID Verification<br/>• CareContext Discovery & Linking<br/>• HIP / HIU Role Abstractions"]
        ABDM_CONSENT["<b>Consent Manager Engine (ABDM M2)</b><br/>• Electronic Consent Artifact (ECA) Validation<br/>• Purpose-Bound Access (CAREMGT, PUBHLTH)<br/>• Granular Time & Resource Scope Filtering"]
        CRYPTO_FIDELIUS["<b>FIDELIUS Cryptographic Engine</b><br/>• Diffie-Hellman Key Exchange (X25519)<br/>• HKDF Key Derivation<br/>• AES-GCM-256 End-to-End Encryption<br/>• Health Data Push/Pull Transfer"]
    end

    %% ==========================================
    %% 5. PERSISTENCE & INFRASTRUCTURE TIER
    %% ==========================================
    subgraph INFRA_TIER["5. Persistence, Caching & Cloud Infrastructure"]
        direction TB
        DB_POSTGRES[("<b>PostgreSQL 16 Enterprise</b><br/>• Relational Multi-Tenant Schemas<br/>• 15+ Numbered Alembic Migrations<br/>• B-Tree Indexed Medical Codes<br/>• Foreign-Key Cascade Governance")]
        CACHE_REDIS[("<b>Redis 7 In-Memory Cluster</b><br/>• Slot Hold TTL Leases<br/>• WebRTC Session Ephemeral State<br/>• Rate Limit Token Buckets")]
        OBJ_STORAGE[("<b>Encrypted Object Storage (S3 / MinIO)</b><br/>• Cryptographically Signed PDF Reports<br/>• Exported FHIR Bundles<br/>• Telehealth Session Logs")]
        CONTAINER_DOCKER["<b>Docker Production Orchestration</b><br/>• Multi-Stage Next.js & FastAPI Images<br/>• Docker Compose / Kubernetes Manifests<br/>• Healthcheck Probes & Self-Healing"]
        TELEMETRY_OBS["<b>Observability & Monitoring</b><br/>• Prometheus Metrics (/metrics)<br/>• Grafana Operational Dashboards<br/>• Structured JSON Access Logs"]
    end

    %% ==========================================
    %% CONNECTIVITY FLOWS
    %% ==========================================
    UI_PATIENT -->|HTTPS / WSS| GW_REVERSE
    UI_DOCTOR -->|HTTPS / WSS| GW_REVERSE
    UI_DIAG -->|HTTPS / WSS| GW_REVERSE
    UI_PHARM -->|HTTPS / WSS| GW_REVERSE
    UI_TELE <-->|WebRTC Mesh / WSS| GW_WS

    GW_REVERSE --> GW_ROUTER
    GW_ROUTER --> GW_SEC
    GW_SEC --> GW_AUTH
    GW_AUTH --> GW_AUDIT

    GW_ROUTER --> SRV_SLOT
    GW_ROUTER --> SRV_PROBLEM
    GW_ROUTER --> SRV_VITAL
    GW_ROUTER --> SRV_SOAP
    GW_ROUTER --> SRV_DIAG
    GW_ROUTER --> SRV_RX
    GW_ROUTER --> SRV_DISPENSE

    SRV_RX --> SRV_PROBLEM
    SRV_RX --> SRV_VITAL
    SRV_DISPENSE --> SRV_RX

    SRV_SLOT --> DB_POSTGRES
    SRV_SLOT --> CACHE_REDIS
    SRV_PROBLEM --> DB_POSTGRES
    SRV_VITAL --> DB_POSTGRES
    SRV_SOAP --> DB_POSTGRES
    SRV_DIAG --> DB_POSTGRES
    SRV_DIAG --> OBJ_STORAGE
    SRV_RX --> DB_POSTGRES
    SRV_DISPENSE --> DB_POSTGRES

    SRV_SLOT -.-> FHIR_TRANS
    SRV_PROBLEM -.-> FHIR_TRANS
    SRV_VITAL -.-> FHIR_TRANS
    SRV_SOAP -.-> FHIR_TRANS
    SRV_DIAG -.-> FHIR_TRANS
    SRV_RX -.-> FHIR_TRANS
    SRV_DISPENSE -.-> FHIR_TRANS

    FHIR_TRANS <--> ABDM_GATEWAY
    ABDM_GATEWAY <--> ABDM_CONSENT
    ABDM_CONSENT <--> CRYPTO_FIDELIUS

    CRYPTO_FIDELIUS -->|Encrypted Health Data Transfer| UI_PATIENT
```

---

## 2. End-to-End Clinical Data Flow (Closed-Loop Lifecycle)

The diagram below maps the complete clinical journey across all 3 pillars of NIRMAYA: from slot reservation to consultation, AI-backed e-prescribing, diagnostic ordering, ABDM consent exchange, and pharmacy dispensing.

```mermaid
sequenceDiagram
    autonumber
    actor Patient as 👤 Patient (Vault)
    actor Doctor as 🩺 Clinician (EMR)
    actor Lab as 🔬 Lab Pathologist
    actor Pharmacy as 💊 Pharmacist
    participant Gateway as 🛡️ NIRMAYA API Gateway
    participant Core as ⚙️ Clinical Services & DDI
    participant Interop as 🌐 FHIR R4 & ABDM Engine
    participant Crypto as 🔐 FIDELIUS & Digital Signer
    participant DB as 🗄️ PostgreSQL & Redis

    %% 1. Booking
    Note over Patient, Doctor: 1. Discovery, Slot Hold & ACID Booking
    Patient->>Gateway: Request slot availability for Dr. Ananya
    Gateway->>DB: Fetch DoctorSlots (status=available)
    Patient->>Gateway: POST /slots/{id}/hold (Acquire 10-min lease)
    Gateway->>DB: Set Redis TTL lease + slot status = held
    Patient->>Gateway: POST /appointments/ (Confirm booking)
    Gateway->>DB: ACID row-level lock (FOR UPDATE) -> Status = confirmed
    Gateway-->>Patient: Appointment confirmed (FHIR Encounter ready)

    %% 2. Consultation & SOAP
    Note over Doctor, Patient: 2. Clinical Encounter & SOAP Attestation
    Doctor->>Gateway: Start Teleconsultation / Encounter Session
    Doctor->>Gateway: POST /patients/{id}/soap-notes (Record S-O-A-P)
    Gateway->>Core: Validate chief complaint & SNOMED/ICD-10 codes
    Doctor->>Gateway: POST /soap-notes/{id}/sign
    Gateway->>Crypto: Compute SHA-256 note digest & lock record
    Crypto-->>DB: Persist signed SOAP note (Immutable)

    %% 3. Clinical Decision Support & e-Prescribing
    Note over Doctor, Core: 3. CDS Safety Engine & e-Prescription Authoring
    Doctor->>Gateway: Author Rx: Atorvastatin + Clopidogrel
    Gateway->>Core: Run Drug-Drug Interaction (DDI) & Allergy Check
    Core-->>Doctor: Return CDS Safety Alert: [Moderate Risk: Bleeding / Hepatic Monitoring]
    Doctor->>Gateway: Confirm clinical override & Sign Rx
    Gateway->>Crypto: Compute deterministic SHA-256 prescription hash
    Gateway->>Interop: Transform to FHIR R4 MedicationRequest (ABDM NRCeS Profile)
    Interop-->>DB: Persist active MedicationRequest with signature digest

    %% 4. Diagnostic Lab Requisition
    Note over Doctor, Lab: 4. Diagnostic Requisition & Coded Results
    Doctor->>Gateway: POST /patients/{id}/service-requests (Order Lipid Panel)
    Gateway->>DB: Status = active (LOINC 24331-1)
    Lab->>Gateway: GET /diagnostics/worklist
    Lab->>Gateway: POST /service-requests/{id}/report (Enter Cholesterol 240 mg/dL)
    Gateway->>Interop: Generate FHIR DiagnosticReport + Observation bundle
    Gateway->>Crypto: Attach cryptographic lab digital signature
    Gateway-->>Patient: Instant notification: Lab report synced to ABHA Vault

    %% 5. ABDM Consent & Encrypted Exchange
    Note over Patient, Interop: 5. ABDM Milestone 2 Consent-Driven Interoperability
    Doctor->>Gateway: Request longitudinal records from Apollo Hospital (HIU Request)
    Gateway->>Interop: Dispatch ABDM Consent Request
    Patient->>Gateway: Grant consent via ABHA PIN (Purpose: CAREMGT)
    Interop->>Crypto: Perform Diffie-Hellman Key Exchange (X25519)
    Crypto->>Crypto: Encrypt FHIR Bundle with AES-GCM-256
    Crypto-->>Doctor: Decrypted longitudinal health history rendered in EMR

    %% 6. Closed-Loop Pharmacy Dispense
    Note over Patient, Pharmacy: 6. Pharmacy Dispensing & Cabinet Tracking
    Patient->>Pharmacy: Present digital e-prescription voucher / ABHA QR
    Pharmacy->>Gateway: Scan Rx ID -> Validate SHA-256 signature
    Pharmacy->>Gateway: POST /prescriptions/{id}/dispense (Lot #BT-9021, Exp: 2028-10)
    Gateway->>Core: Transition MedicationDispense (preparation -> completed)
    Gateway->>Interop: Emit FHIR R4 MedicationDispense record
    Gateway-->>Patient: Active Cabinet Updated (Dose reminders & refill counts active)
```

---

## 3. Core Architectural Modules & Deliverables (Full Scope)

| Architectural Pillar | Core Components | Interoperability & Security Standard |
|---|---|---|
| **1. Identity & Portals** | Patient Vault, Doctor EMR, Diagnostic Lab Gateway, Pharmacy Console, Admin Dashboard | Supabase Auth, ABHA M1 Token Broker, Cal.com Pure Modern SaaS Aesthetic |
| **2. Clinical Core** | Problem Lists, Vitals Telemetry, SOAP Encounter Documentation, Diagnostic Orders | SNOMED-CT, ICD-10, LOINC (70+ validated terms), SHA-256 note locking |
| **3. Pharmacotherapy** | Formulary Catalog (30+ drugs), e-Prescriptions, DDI Clinical Decision Support, Dispense Engine | RxNorm, WHO-ATC, FDA/CDSCO DDI rules, Lot/Batch tracking |
| **4. Interoperability** | FHIR Transformer Engine, CareContext Discovery, ABDM Consent Manager | HL7 FHIR Release 4 (NRCeS India Profiles), ABDM Milestone 1 & 2 |
| **5. Cryptography** | Tamper-evident digital signatures, Encrypted data transfer protocols | SHA-256 Hashing, FIDELIUS E2E Encryption (X25519 + AES-GCM-256) |
| **6. Real-time & Media** | Telehealth Video consultation, in-call chat, slot countdown timers | WebRTC Mesh, WebSockets, Redis TTL Ephemeral Store |
| **7. Production Infra** | Containerized micro-services, distributed telemetry, database migrations | Docker Compose, PostgreSQL 16 (15+ Alembic Revisions), Prometheus/Grafana |

---

## 4. Database Schema Entity-Relationship Map (Finalized 15+ Entities)

```mermaid
erDiagram
    USERS ||--o{ PATIENT_PROFILES : "1:1 profile"
    USERS ||--o{ DOCTOR_PROFILES : "1:1 profile"
    USERS ||--o{ LAB_FACILITIES : "1:1 facility"
    USERS ||--o{ PHARMACY_PROFILES : "1:1 pharmacy"

    PATIENT_PROFILES ||--o{ APPOINTMENTS : "books"
    DOCTOR_PROFILES ||--o{ APPOINTMENTS : "conducts"
    DOCTOR_PROFILES ||--o{ DOCTOR_SLOTS : "generates"
    APPOINTMENTS ||--o| DOCTOR_SLOTS : "reserves"

    PATIENT_PROFILES ||--o{ CLINICAL_CONDITIONS : "diagnosed with"
    PATIENT_PROFILES ||--o{ CLINICAL_OBSERVATIONS : "measures"
    APPOINTMENTS ||--o{ SOAP_NOTES : "documents"

    PATIENT_PROFILES ||--o{ SERVICE_REQUESTS : "ordered for"
    DOCTOR_PROFILES ||--o{ SERVICE_REQUESTS : "orders"
    SERVICE_REQUESTS ||--o| DIAGNOSTIC_REPORTS : "fulfills"

    MEDICATIONS ||--o{ MEDICATION_REQUESTS : "prescribes"
    PATIENT_PROFILES ||--o{ MEDICATION_REQUESTS : "receives"
    DOCTOR_PROFILES ||--o{ MEDICATION_REQUESTS : "authors"

    MEDICATION_REQUESTS ||--o{ MEDICATION_DISPENSES : "dispenses"
    PHARMACY_PROFILES ||--o{ MEDICATION_DISPENSES : "fulfills"

    PATIENT_PROFILES ||--o{ ABDM_CONSENTS : "grants"
    ABDM_CONSENTS ||--o{ CARE_CONTEXTS : "authorizes"
```
