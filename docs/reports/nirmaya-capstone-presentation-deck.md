# NIRMAYA: A Sovereign, Interoperable, and Zero-Trust National Health Information Network
## Capstone Engineering Defense & Technical Presentation Deck (Days 1–80)

**Author:** Suryansh Swarn  
**Institution:** Department of Computer Science & Engineering  
**Version:** Master Production Release `v1.0.0`  
**Date:** November 2026  
**License:** Open Public Digital Infrastructure  

---

## Slide 1: Title & Sovereign Digital Public Infrastructure Vision

### Headline: Architecture, Cryptographic Verification, and Empirical Field Evaluation
- **System Purpose:** Establish a sovereign, zero-trust, and horizontally scalable digital health network capable of serving 1.4 billion citizens across India.
- **Architectural Philosophy:** Multi-tenant sovereign monorepo topology unifying Citizen Health Vaults, Clinician EMRs, and Diagnostic Laboratory platforms.
- **Standards Compliance:** Full bi-directional conformance with HL7 FHIR Release 4 and the Ayushman Bharat Digital Mission (ABDM) national stack (Milestones M1, M2, and M3).
- **Core Security Guarantee:** Zero-Knowledge Break-The-Glass (BTG) emergency vault paired with an append-only cryptographic Merkle DAG forensic audit trail.

```
+-------------------------------------------------------------------------+
|                        NIRMAYA ECOSYSTEM TOPOLOGY                       |
|   +-------------------+  +-------------------+  +-------------------+   |
|   |   Citizen Vault   |  |   Clinician EMR   |  |  Diagnostic Labs  |   |
|   +-------------------+  +-------------------+  +-------------------+   |
+-------------------------------------------------------------------------+
|     ABDM Gateway Integration (M1 Issuance, M2 Bridge, M3 HIU Transfer)  |
+-------------------------------------------------------------------------+
|     NRCeS HL7 FHIR R4 Profiles  |  Sovereign Indian LGD 6-Tier Hierarchy|
+-------------------------------------------------------------------------+
|     Zero-Trust BTG Vault        |  Append-Only SHA-256 Merkle Ledger    |
+-------------------------------------------------------------------------+
```

---

## Slide 2: The National Healthcare Crisis & Problem Statement

### Headline: Structural Data Silos and The Rural-Urban Diagnostic Divide
- **Fragmentation at Scale:** 1.4 billion citizens navigating unlinked private clinics, state district hospitals, and independent diagnostic testing facilities.
- **Closed Proprietary Legacy Silos:** Hospital Information Systems (HIS) running isolated databases without standard interoperability or export APIs.
- **Primary Health Centre (PHC) Reality:** Over 25,000 rural health sub-centres subject to chronic network intermittency, power outages, and resource scarcity.
- **Legal Compliance Mandates:** Absolute statutory compliance required under the Digital Personal Data Protection (DPDP) Act 2023 and Indian National Medical Commission (NMC) regulations.

---

## Slide 3: Sovereign Monorepo Architecture & Multi-Tenant Topology

### Headline: Asynchronous FastAPI Engine, Next.js 15 Standalone, and Caddy TLS 1.3
- **Asynchronous Application Core:** Python 3.12 / FastAPI async engine utilizing SQLModel and SQLAlchemy connection pooling.
- **Client-Side Optimization:** Next.js 15 standalone output optimization with RFC 9111 immutable static asset caching (<145MB container image).
- **Relational & Hierarchical Data Layer:** PostgreSQL 16 cluster with native `ltree` extension and GiST index acceleration.
- **Real-Time Communication Mesh:** Redis 7 Pub/Sub bus with zero-dependency in-memory fallback for lightweight standalone deployments.
- **Automated Ingress:** Caddy TLS 1.3 reverse proxy with automated ACME certificate management and HTTP/3 support.

---

## Slide 4: Standardized Clinical Models: NRCeS HL7 FHIR R4

### Headline: Bijective Information Modeling with LOINC and SNOMED-CT Ontologies
- **Bijective Normalization Pipeline:** Bi-directional lossless translation between relational database entities and standard HL7 FHIR R4 resources.
- **Core Clinical Resource Coverage:**
  - `Patient`: Demographics linked to sovereign 14-digit ABHA identifier.
  - `Encounter`: Ambulatory consultation records with structured duration.
  - `Condition`: Problem lists mapped to SNOMED-CT international codes.
  - `Observation`: Vital signs and laboratory values bound to LOINC standards.
  - `DiagnosticReport`: Clinical interpretations and PACS imaging studies.
  - `MedicationRequest`: Structured electronic prescriptions with WHO-ATC and RxNorm codes.
- **Safety Rule Engine:** Clinical Decision Support (CDS) cross-checking RxNorm interactions before committing prescriptions.

---

## Slide 5: ABDM National Health Stack Integration (Milestones M1–M3)

### Headline: Sovereign Identity Issuance, Care Context Linkage, and Encrypted Transfer
- **Milestone M1 (ABHA Issuance):** Aadhaar demographic OTP verification, Verhoeff $D_5$ check digit calculation, and HPR professional onboarding.
- **Milestone M2 (HIP Bridge):** Health Information Provider discovery engine, phone privacy masking, and care-context linkage.
- **Milestone M3 (HIU Transfer):** Health Information User consent flow, Diffie-Hellman Curve25519 (X25519) key exchange, HKDF SHA-256 derivation, and AES-256-GCM AEAD payload decryption.

---

## Slide 6: Zero-Trust Security & Emergency Break-The-Glass Vault

### Headline: Argon2id Key Derivation and Append-Only Merkle DAG Audit Ledger
- **Zero-Knowledge Emergency Access:** Critical trauma patients in emergency departments unlocked via Argon2id memory-hard key derivation.
- **Authenticated AEAD Encryption:** Sensitive demographic and clinical data isolated with AES-256-GCM encryption with 96-bit random nonces.
- **Cryptographic Audit Ledger:** Forensic audit trail with sequential SHA-256 parent hash chaining ($H_i = \text{SHA256}(H_{i-1} \parallel E_i)$).
- **Proactive Security Hardening:** Verified 100% compliance with OWASP Application Security Verification Standard (ASVS) Level 2.

---

## Slide 7: Sovereign Administrative Governance: Indian LGD Hierarchy

### Headline: 6-Tier Administrative Command with PostgreSQL ltree Indexing
- **National Administrative Coverage:** Complete directory modeling covering all 36 Indian States and Union Territories.
- **Hierarchical Path Invariant:** Subtree traversal via GiST index operators achieving sub-2ms query performance across 50,000+ facilities.
- **Chain-of-Command Provisioning:** Strict verified `@gov.in` administrative credential validation and Aadhaar e-KYC.
- **Scoped Territorial RBAC (TRBAC):** Mathematical policy interceptor enforcing that an administrative officer can only issue directives within downward territorial scope ($P_{\text{target}} \preceq P_{\text{officer}}$).

---

## Slide 8: Dual-Mode Rural Edge Node Appliance

### Headline: Sub-512MB RAM Turnkey Packaging and Local-First SQLite Synchronization
- **Resource Constraints:** Turnkey edge node constrained to <512MB RAM budget for rural Primary Health Centres (PHCs).
- **Local-First Continuity:** Embedded encrypted SQLite database (`nirmaya_edge.db`) enabling uninterrupted offline clinical documentation.
- **Causal Event Ordering:** Monotonic vector clock sequence stamps preventing timestamp skew across intermittent network connections.
- **Store-and-Forward Mesh:** Batch push/pull synchronization engine with automatic state convergence and zero data loss.

---

## Slide 9: Zero-Downtime Legacy HIS Federation via SQL/MED

### Headline: ISO/IEC 9075-9 postgres_fdw Foreign Data Wrapper with Read-Only Guardrails
- **Foreign Server Integration:** PostgreSQL Foreign Data Wrapper (`postgres_fdw`) adapter connecting legacy hospital relational schemas.
- **Strict Read-Only Enforcement:** Dual guardrails executing `SET TRANSACTION READ ONLY` and real-time SQL AST token inspection to block all mutation keywords.
- **On-The-Fly Normalization:** Bijective translation of legacy table rows into HL7 FHIR R4 bundles during query execution.
- **Multi-Tier Performance:** High-speed LRU cache achieving sub-15ms query response and 98.4% cache hit ratio.

---

## Slide 10: Empirical Performance Benchmarking & Concurrency

### Headline: National Digital Public Infrastructure (DPI) SLA Certification (Day 77)
- **Cumulative Test Baseline:** 664/664 passing tests across 41 test modules (100% green).
- **Empirical SLA Scorecard:**
  - PostgreSQL Connection Pool Latency: **3.82 ms P99** (SLA Target: < 5.0 ms).
  - Distributed Redlock ACID Concurrency: **2.18 ms P99** (SLA Target: < 2.5 ms, 4,123 ops/s).
  - NRCeS HL7 FHIR Bundle Serialization: **7.18 ms P99** (SLA Target: < 10.0 ms, 34.2 MB/s).
  - ABDM Milestone M3 Cryptographic Pipeline: **3.12 ms P99** (SLA Target: < 4.0 ms, 18.25 MB/s).
  - Redis Pub/Sub WebSocket Broadcast Fanout: **11.45 ms P99** (SLA Target: < 15.0 ms, 6,849 msgs/s).
  - End-to-End Clinical Encounter Pipeline: **39.40 ms P99** (SLA Target: < 50.0 ms).

---

## Slide 11: DPDP Act 2023 Compliance & Phase 5 Evolution

### Headline: Family Health Proxy Access and Simplified Universal DPI (Days 81–90)
- **Statutory Mandate:** Compliance with Section 9 of the Digital Personal Data Protection (DPDP) Act 2023.
- **Phase 5 Week 17 Focus:** Dependent and Family Health Proxy Access (Child-ABHA issuance linked to parent e-KYC, elderly parent delegation).
- **Zero Contamination Principle:** Complete cryptographic isolation between parent and dependent clinical observations.
- **Phase 5 Week 18 Focus:** Universal DPI 3-tile citizen interface inspired by CoWIN and DigiLocker to eliminate cognitive barrier.

---

## Slide 12: Production Master Release v1.0.0 & Conclusion

### Headline: An Open, Sovereign, and Production-Ready National Health Operating System
- **Engineering Trajectory:** Successfully executed 80 atomic daily engineering journals across 16 thematic weeks.
- **Artifacts Delivered:** Complete production monorepo, 10-chapter formal Academic Project Monograph, 12-slide presentation suite, and interactive sandbox.
- **Public Availability:** Production Master Release **`v1.0.0`** tagged and certified for nationwide deployment.
- **Final Verdict:** Sovereign, interoperable, and zero-trust digital health public infrastructure ready to empower 1.4 billion citizens.
