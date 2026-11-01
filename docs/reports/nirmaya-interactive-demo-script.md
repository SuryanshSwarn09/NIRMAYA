# NIRMAYA: Timed 10-Minute Interactive Demonstration Script
## Step-by-Step Defense Guide & Live Sandbox Walkthrough

**Target Audience:** Academic Examiners, Technical Juries, Healthcare Stakeholders  
**Total Running Time:** 10 Minutes (600 Seconds)  
**Environment Prerequisites:** NIRMAYA Full-Stack Cluster (FastAPI + Next.js 15 + PostgreSQL 16 + Redis 7 + Caddy)  
**Host URL:** `http://localhost:3000/doctor` or Production Domain  

---

## Demonstration Timeline & Segment Allocation

| Segment | Elapsed Time | Focus Area | Action Items & Screen Walkthrough |
| :--- | :--- | :--- | :--- |
| **Part 1** | 00:00 - 01:30 | Sovereign Monorepo & Clinical EMR | Overview of clinician portal, queue management, demographic lookup |
| **Part 2** | 01:30 - 03:30 | Citizen Consultation & HL7 FHIR R4 | Patient intake, LOINC vitals, DDI check, prescription, Merkle append |
| **Part 3** | 03:30 - 05:30 | Emergency Break-The-Glass Vault | Unconscious trauma simulation, Argon2id KDF, AES-256-GCM decryption |
| **Part 4** | 05:30 - 07:30 | Rural Edge Node & Offline Sync | Offline PHC encounter authoring, local SQLite, store-and-forward batch |
| **Part 5** | 07:30 - 09:00 | Legacy HIS Federation & Command | SQL/MED postgres_fdw read-only query, LGD IDSP disease outbreak |
| **Part 6** | 09:00 - 10:00 | Empirical SLA Scorecard & Q&A | Review 664 passing tests, sub-5ms P99 latencies, thesis monograph |

---

## Detailed Step-by-Step Script

### Part 1: Sovereign Monorepo & Clinician Portal (00:00 - 01:30)

**Presenter Talking Points:**
> "Welcome everyone. NIRMAYA is an open-source, sovereign, and zero-trust national health information network engineered for 1.4 billion Indian citizens. We are currently viewing the live clinician portal at `/doctor`. Notice the clean Cal.com minimalist monochrome interface with zero gradients and clear visual affordances designed for high-throughput OPD environments."

**Actions to Perform:**
1. Open web browser to `http://localhost:3000/doctor`.
2. Scroll to the **Subsystem Performance & Interoperability Benchmark Suite** card.
3. Highlight the **100% SLA COMPLIANT** badge and the 6 evaluated subsystems.
4. Click **Run Live Benchmark** button: demonstrate live micro-benchmark execution across all subsystems completing in under 1.5 seconds.

---

### Part 2: Citizen Consultation & HL7 FHIR R4 (01:30 - 03:30)

**Presenter Talking Points:**
> "Now let's examine our first live sandbox scenario: an end-to-end OPD consultation with real-time ABDM Milestone M2 linkage. The patient, Aarav Sharma, presents with hypertension. His 14-digit ABHA number is verified on-the-fly using the Dihedral Group D5 Verhoeff checksum algorithm."

**Actions to Perform:**
1. Navigate to the **Interactive Demonstration Sandbox** card.
2. Select **Scenario 1: End-to-End Citizen Consultation & ABDM Linkage**.
3. Click **Execute Live Scenario**:
   - Step 1: Validates ABHA `14-8291-0391-4821` via Verhoeff $D_5$.
   - Step 2: Records quantitative LOINC vital signs (Blood Pressure `85354-9`, Blood Glucose `2339-0`).
   - Step 3: Evaluates RxNorm/ATC drug interaction rules between Enalapril and Metformin (Zero contraindications).
   - Step 4: Generates SHA-256 cryptographic block and chains it into the immutable Merkle DAG audit ledger.
   - Step 5: Generates compliant NRCeS HL7 FHIR R4 Document Bundle and links care-context `CC-2026-OPD-9104`.
4. Point out the live telemetry output showing sub-50ms execution time and zero data contamination.

---

### Part 3: Emergency Break-The-Glass (BTG) Vault Access (03:30 - 05:30)

**Presenter Talking Points:**
> "In acute emergency trauma scenarios, patient consent cannot be obtained. Traditional systems either block access—endangering life—or leak records indiscriminately. NIRMAYA solves this with a Zero-Knowledge Break-The-Glass Emergency Vault combining Argon2id memory-hard key derivation with AES-256-GCM authenticated encryption."

**Actions to Perform:**
1. In the **Interactive Demonstration Sandbox** card, select **Scenario 2: Emergency Break-The-Glass (BTG) Vault Access**.
2. Click **Execute Live Scenario**:
   - Step 1: Authenticates ER attending physician and records clinical justification.
   - Step 2: Derives ephemeral 256-bit vault master key using Argon2id ($m=64\text{MB}, t=4$).
   - Step 3: Executes authenticated AES-256-GCM decryption: reveals critical blood group `O+` and Penicillin allergy in 3.12ms.
   - Step 4: Writes forensic audit record with SHA-256 parent hash chaining to prevent tampering.
   - Step 5: Simulates real-time carrier SMS dispatch to the patient's registered emergency next-of-kin.
3. Highlight that zero unencrypted demographic data persists in memory after the emergency encounter ends.

---

### Part 4: Rural Edge Node Appliance & Offline Sync (05:30 - 07:30)

**Presenter Talking Points:**
> "Over 65% of India's population relies on rural Primary Health Centres where internet connectivity is intermittent. Day 74 delivered our dual-mode edge appliance constrained to under 512MB RAM. Let us simulate authoring records completely offline."

**Actions to Perform:**
1. Select **Scenario 3: Rural Offline Edge Node & Store-and-Forward Synchronization**.
2. Click **Execute Live Scenario**:
   - Step 1: Authors patient encounter in local encrypted SQLite database (`nirmaya_edge.db`) while disconnected.
   - Step 2: Packages events into batch payload with monotonic vector clock timestamps (`phc_rampur: 142`).
   - Step 3: Detects network resumption and completes TLS 1.3 mutual handshake.
   - Step 4: Dispatches batch store-and-forward payload to the central gateway with automatic conflict detection.
   - Step 5: Cloud reconciles state: Merkle root updated with 0.00% data loss rate.

---

### Part 5: Legacy HIS Federation & IDSP Command Center (07:30 - 09:00)

**Presenter Talking Points:**
> "To prevent hospital rip-and-replace, NIRMAYA federates existing hospital databases using ISO/IEC 9075-9 SQL/MED foreign data wrappers with strict read-only AST guardrails. Simultaneously, our Public Health Command Center leverages PostgreSQL ltree indexing across all 36 Indian States and UTs."

**Actions to Perform:**
1. Select **Scenario 4: Zero-Downtime Legacy HIS Read-Only Federation via SQL/MED**.
   - Show read-only query execution over `postgres_fdw` with on-the-fly HL7 FHIR R4 mapping in 4.8ms.
2. Select **Scenario 5: Public Health Command Center & Disease Surveillance**.
   - Show recursive LGD tree traversal (`in.gov.state_09`) in 1.2ms.
   - Show IDSP syndromic aggregation identifying Dengue outbreak with effective reproduction rate $R_t = 1.34$.
   - Show Scoped TRBAC boundary enforcement and administrative directive broadcast.

---

### Part 6: Empirical SLA Scorecard & Defense Q&A (09:00 - 10:00)

**Presenter Talking Points:**
> "In conclusion, over 80 atomic engineering days, NIRMAYA has constructed a complete, sovereign healthcare operating system verified by 664 automated tests, with sub-5ms P99 latencies, and formal mathematical proofs. We now invite technical questions from the committee."

**Actions to Perform:**
1. Switch to the **Slide Deck Navigator** tab within the card.
2. Step through Slide 10 (Empirical Scorecard) and Slide 12 (Production Master Release v1.0.0).
3. Offer examiners the interactive terminal to run:
   ```powershell
   pytest backend/tests/test_interactive_demo.py -v
   ```
4. Conclude presentation and open floor for technical questions.
