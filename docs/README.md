# Welcome to NIRMAYA

**NIRMAYA**: **N**etworked **I**nteroperable **R**ecords **M**edical **A**ssets & **Y**our **A**rchives

> A Unified Digital Health Interoperability Platform & Longitudinal Patient Vault built on modern healthcare data standards: **HL7 FHIR Release 4** and the **Ayushman Bharat Digital Mission (ABDM)** ecosystem.
>
> 🌐 **Live Deployed Web Portal:** [https://nirmaya-tau.vercel.app/](https://nirmaya-tau.vercel.app/)  
> 📖 **Official GitBook Documentation:** [https://suryanshs-projects.gitbook.io/nirmaya-docs](https://suryanshs-projects.gitbook.io/nirmaya-docs)


---

## The Vision at a Glance

Healthcare data worldwide—and particularly in expanding digital health ecosystems—suffers from severe fragmentation. When a patient visits multiple clinics, diagnostic labs, or hospital systems, their medical records are trapped in disparate database silos:
- Paper prescriptions get lost or degraded.
- Diagnostic lab results remain locked in unsearchable, unstructured PDF attachments.
- Doctors must treat patients with zero visibility into historical diagnoses, drug allergies, or concurrent medications.

**NIRMAYA** is engineered as a final-year major project to solve this exact dilemma. Rather than building a conventional, isolated CRUD web application, NIRMAYA implements an enterprise-grade interoperability network that treats medical data as structured, standardized, and patient-sovereign assets.

---

## Key Pillars of NIRMAYA

```
                      +---------------------------------------+
                      |            NIRMAYA PLATFORM           |
                      +---------------------------------------+
                                         |
     +-----------------------------------+-----------------------------------+
     |                                   |                                   |
     v                                   v                                   v
+-------------------------+ +-------------------------+ +-------------------------+
|   Patient Health Vault  | |   Provider (Doctor) EMR | | Diagnostic Lab Gateway  |
| (Appointments, Records, | | (Encounter Notes, Rx,   | | (Report Uploads,        |
|  ABHA ID, Timeline)     | |  Clinical History)      | |  Structured Parameters) |
+-------------------------+ +-------------------------+ +-------------------------+
     |                                   |                                   |
     +-----------------------------------+-----------------------------------+
                                         |
                                         v
                            HL7 FHIR R4 & ABDM Network
```

1. **Patient Health Vault:** A self-sovereign locker where patients own their complete longitudinal medical history, control consent-based data sharing with doctors, and link their simulated 14-digit ABHA identity.
2. **Provider (Doctor) EMR:** An electronic medical record console enabling clinicians to review verified historical timelines, document clinical encounters, and issue structured e-prescriptions conforming to FHIR `MedicationRequest`.
3. **Diagnostic (Lab) Gateway:** A secured channel for accredited laboratories to upload both human-readable PDF reports and machine-readable FHIR `Observation` values directly into patient records.

---

## Documentation Structure

This GitBook documentation captures both the architectural blueprint and the live, daily development journal of NIRMAYA across a planned 4-month (16-week, 80-day) implementation timeline:

- **Part I: System Vision & Architecture:** The problem analysis, solution architecture, and technology selections.
- **Part II: Healthcare Standards:** In-depth mappings of HL7 FHIR R4 and simulated ABDM consent flows.
- **Part III: The 4-Month Development Journey:** Day-by-day micro-commit logs, architectural decisions, and technical milestones.
