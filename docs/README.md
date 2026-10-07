<div align="center">

![NIRMAYA Logo](assets/icon-192.png)

# NIRMAYA: Networked Interoperable Records Medical Assets & Your Archives

[![Live Demo](https://img.shields.io/badge/Live_Demo-nirmaya--tau.vercel.app-111111.svg?style=flat&logo=vercel&logoColor=white)](https://nirmaya-tau.vercel.app/)
[![GitBook](https://img.shields.io/badge/GitBook-Documentation-3884FF.svg?style=flat&logo=gitbook&logoColor=white)](https://suryanshs-projects.gitbook.io/nirmaya-docs)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15.1-000000.svg?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![FHIR](https://img.shields.io/badge/HL7-FHIR_R4-E05A47.svg?style=flat)](https://hl7.org/fhir/R4/)
[![ABDM](https://img.shields.io/badge/ABDM-Simulated_Network-1B365D.svg?style=flat)](https://abdm.gov.in/)

**A Unified Health Interoperability Network & Longitudinal Patient Vault**  
*Built on HL7 FHIR Release 4 and Simulated Ayushman Bharat Digital Mission (ABDM) Standards*

[Live Demo Portal](https://nirmaya-tau.vercel.app/) • [GitBook Documentation](https://suryanshs-projects.gitbook.io/nirmaya-docs) • [System Architecture](ARCHITECTURE.md) • [Changelog](CHANGELOG.md)

<br/><br/>

<img src="assets/nirmaya-mockup.png" alt="NIRMAYA Modern Clinical Interoperability Platform" width="850" />

</div>

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
