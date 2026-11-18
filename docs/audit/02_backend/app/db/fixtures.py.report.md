# Audit Report: `backend/app/db/fixtures.py`

**Path**: `backend/app/db/fixtures.py` | **Layer**: `02_backend` | **Language**: Python | **LOC**: 275 | **Audit Date**: 2026-11-18

---

## Layer A — TL;DR
Synthetic clinical fixtures for database seeding and automated testing adhering to ABDM and HL7 FHIR standards · Risk: **S3 (Low Risk)** · Verdict: **READY** · High-quality, culturally realistic Indian clinical datasets for patients, clinicians, and NABL/CAP-accredited laboratories.

---

## Layer B — Explain It
- **What problem this file solves**: Provides rich, pre-configured initial data fixtures for testing, development, and system demonstrations without risking patient Protected Health Information (PHI).
- **How it works step by step**:
  1. Exports `ADMIN_FIXTURE` representing the platform root administrator.
  2. Defines `PATIENT_FIXTURES` with demographic profiles, emergency contacts, 14-digit ABHA numbers, and `@abdm` addresses across Ahmedabad, Kochi, and Bengaluru.
  3. Defines `DOCTOR_FIXTURES` with State Medical Council registrations (MCI, MMC, KMC), specialties (Cardiology, Pediatrics, Neurology), and `@hpr.abdm` IDs.
  4. Defines `LAB_FIXTURES` with NABL/CAP/ISO-15189 accreditation numbers and HFR identifiers.
  5. `get_all_fixtures()` aggregates all categories into a single dictionary.
- **Concepts & patterns used**:
  - *Data Fixture Pattern*: Decoupled test fixtures enabling deterministic database states.
  - *Synthetic PHI*: Realistic dummy records mimicking Indian healthcare ecosystem identifiers.
- **Key lines to read first**:
  - `backend/app/db/fixtures.py:14-22`: Root administrator fixture.
  - `backend/app/db/fixtures.py:27-52`: Patient demographic record with ABHA mapping.
  - `backend/app/db/fixtures.py:108-131`: Clinician profile with HPR ID.
  - `backend/app/db/fixtures.py:183-210`: Diagnostic lab facility with NABL accreditation.
- **How to change it safely**:
  - Keep foreign key links (`user_id`) coordinated when modifying or adding fixtures.

---

## Layer C — Technical Detail

1. **Role in architecture**:
   - **Imports**: `datetime.date`, `app.models.enums.*`.
   - **Imported by**: `backend/app/db/seeder.py`, `scripts/seed-db.py`, pytest test fixtures (`backend/tests/conftest.py`).
   - **Public surface**: `ADMIN_FIXTURE`, `PATIENT_FIXTURES`, `DOCTOR_FIXTURES`, `LAB_FIXTURES`, `get_all_fixtures`.

2. **Security [SEC]**:
   - Zero Real PHI: All data is completely synthetic (`@example.com`, simulated telephone numbers `+9198...`).
   - *CWE-1188 (Insecure Default Initialization of Resource)*: Fixtures include default administrative user (`admin@nirmaya.health`). If seeder is triggered in production without overriding credentials, this creates a default access vector.

3. **Code quality [QUAL]**:
   - Exceptionally detailed domain data adhering strictly to real-world Indian health standards (MCI councils, NABL certification codes).

4. **AI-generated smells [QUAL]**:
   - None observed.

5. **Performance [PERF]**:
   - Static in-memory dictionary; zero computation cost.

6. **Error handling & edge cases**:
   - Enums ensure valid database field types on insertion.

7. **Doc accuracy [DOC]**:
   - Accurately aligns with documentation claims regarding ABDM sandbox compliance.

8. **Tests**:
   - Ingested by `backend/tests/test_db_seeder.py`.

---

## Findings Table
| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **BE-FIX-F01** | **S3** | `[SEC]` | `14-22` | Static default admin email in seed dataset | `"email": "admin@nirmaya.health"` | Ensure seeder is gated by environment check |
| **BE-FIX-F02** | **S4** | `[QUAL]` | `49, 74, 99` | Mock ABHA numbers do not validate against Verhoeff checksum | `"abha_number": "91-1029-3847-5610"` | Use algorithmically valid test ABHAs |

---

## Verdict
**READY** — Exemplary synthetic clinical fixture library.
