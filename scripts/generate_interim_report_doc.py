import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_report():
    doc = Document()

    # Set page margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Styles & Colors
    NAVY = RGBColor(27, 54, 93)      # #1B365D
    BLUE = RGBColor(37, 99, 235)     # #2563EB
    CHARCOAL = RGBColor(30, 41, 59)  # #1E293B
    GRAY = RGBColor(100, 116, 139)   # #64748B

    # Helper functions
    def add_title(text, subtitle=None):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(26)
        run.font.bold = True
        run.font.color.rgb = NAVY
        p.paragraph_format.space_before = Pt(36)
        p.paragraph_format.space_after = Pt(6)

        if subtitle:
            p_sub = doc.add_paragraph()
            p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_sub = p_sub.add_run(subtitle)
            run_sub.font.name = 'Arial'
            run_sub.font.size = Pt(13)
            run_sub.font.color.rgb = BLUE
            p_sub.paragraph_format.space_after = Pt(24)

    def add_heading_1(text):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = NAVY
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True

    def add_heading_2(text):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = BLUE
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True

    def add_heading_3(text):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = CHARCOAL
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True

    def add_body(text, bold_prefix=None):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            run_bp = p.add_run(bold_prefix)
            run_bp.font.name = 'Calibri'
            run_bp.font.size = Pt(11)
            run_bp.font.bold = True
            run_bp.font.color.rgb = CHARCOAL
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(11)
        run.font.color.rgb = CHARCOAL
        return p

    def add_bullet(text, bold_prefix=None):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            run_bp = p.add_run(bold_prefix)
            run_bp.font.name = 'Calibri'
            run_bp.font.size = Pt(11)
            run_bp.font.bold = True
            run_bp.font.color.rgb = CHARCOAL
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(11)
        run.font.color.rgb = CHARCOAL
        return p

    def add_callout(text, title=None):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        set_cell_background(cell, 'F1F5F9')
        set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        if title:
            run_t = p.add_run(title + "\n")
            run_t.font.name = 'Arial'
            run_t.font.size = Pt(10.5)
            run_t.font.bold = True
            run_t.font.color.rgb = BLUE
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(10.5)
        run.font.italic = True
        run.font.color.rgb = CHARCOAL
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def style_table(tbl, col_widths, col_names, data):
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        # Header Row
        hdr_cells = tbl.rows[0].cells
        for i, name in enumerate(col_names):
            hdr_cells[i].text = name
            set_cell_background(hdr_cells[i], '1B365D')
            set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = 'Arial'
                run.font.size = Pt(10)
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)

        # Data Rows
        for r_idx, row_data in enumerate(data):
            row_cells = tbl.add_row().cells
            bg_color = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
            for c_idx, val in enumerate(row_data):
                row_cells[c_idx].text = str(val)
                set_cell_background(row_cells[c_idx], bg_color)
                set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=120, right=120)
                p = row_cells[c_idx].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:
                    run.font.name = 'Calibri'
                    run.font.size = Pt(9.5)
                    run.font.color.rgb = CHARCOAL

        # Set widths
        for row in tbl.rows:
            for c_idx, w in enumerate(col_widths):
                row.cells[c_idx].width = Inches(w)

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ==================== TITLE PAGE / HEADER ====================
    add_title("NIRMAYA", "Networked Interoperable Records Medical Assets & Your Archives")
    
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p_meta.add_run("INTERIM PROJECT REPORT (MONTH 1 REVIEW)\n")
    r1.font.name = 'Arial'
    r1.font.size = Pt(14)
    r1.font.bold = True
    r1.font.color.rgb = NAVY

    r2 = p_meta.add_run("Final Year Major Project in Health Informatics & Computer Engineering\n")
    r2.font.name = 'Arial'
    r2.font.size = Pt(11)
    r2.font.bold = True
    r2.font.color.rgb = CHARCOAL

    r3 = p_meta.add_run("Milestone Release: v0.1.0 | Coverage: Weeks 1–4 (Days 1–20)\nDate of Submission: October 2026\n")
    r3.font.name = 'Calibri'
    r3.font.size = Pt(10.5)
    r3.font.color.rgb = GRAY
    p_meta.paragraph_format.space_after = Pt(20)

    # Student & Evaluation Metadata Table
    admin_tbl = doc.add_table(rows=1, cols=2)
    style_table(
        admin_tbl,
        [3.2, 3.2],
        ["Project & Student Credentials", "Institutional Evaluation Context"],
        [
            ["Student Name: Suryansh Swarn", "Academic Department: Computer Science & Engineering"],
            ["Project Title: NIRMAYA Platform", "Evaluation Tier: Final Year Major Project Review 1"],
            ["Repository: github.com/SuryanshSwarn09/NIRMAYA", "Review Scope: Foundation, Schemas, Security & Scheduling"],
            ["Specification: HL7 FHIR R4 & ABDM M1", "Live Verification: 151 / 151 Automated Tests Passed (100%)"]
        ]
    )

    doc.add_page_break()

    # ==================== 1. EXECUTIVE SUMMARY ====================
    add_heading_1("1. Executive Summary")
    add_body(
        "NIRMAYA (Networked Interoperable Records Medical Assets & Your Archives) is an enterprise-grade, "
        "federated digital health interoperability platform designed to resolve India's severe healthcare data fragmentation. "
        "Traditional healthcare delivery operates in proprietary, isolated database silos where prescriptions are lost on paper, "
        "diagnostic tests remain locked in unstructured PDFs, and treating clinicians lack longitudinal visibility into patient medical history."
    )
    add_body(
        "NIRMAYA is architected around international healthcare data protocols (HL7 FHIR Release 4) and India's national health "
        "ecosystem (Ayushman Bharat Digital Mission - ABDM). Over the course of Month 1 (a rigorous 4-week, 20-working-day development sprint), "
        "the project established a complete, production-grade clinical foundation: an asynchronous FastAPI backend, normalized PostgreSQL 16 "
        "database schema managed via Alembic migrations, Supabase Cloud authentication with 4-tier Role-Based Access Control (RBAC), "
        "an interactive patient-doctor appointment engine with ACID row-level locking to prevent double bookings, and a clean modern clinical "
        "interface built with Next.js 15 and Tailwind CSS v4."
    )
    add_callout(
        "Key Milestone Achievement (Release v0.1.0): 20 consecutive development days completed with over 210 atomic micro-commits, "
        "3 successful database schema revisions, 11 fully rendered Next.js application routes, and 151 automated tests achieving a 100% pass rate in 17.67s.",
        "Month 1 Milestone Validation"
    )

    # ==================== 2. PROBLEM STATEMENT & OBJECTIVES ====================
    add_heading_1("2. Problem Statement & System Objectives")
    add_heading_2("2.1 The Clinical Data Fragmentation Dilemma")
    add_body(
        "In typical Indian healthcare encounters, patient records are decentralized across disparate private clinics, commercial laboratories, "
        "and tertiary care hospitals. This leads to three fundamental systemic failures:"
    )
    add_bullet("Paper-based prescriptions degrade rapidly or are misplaced, preventing reliable drug interaction checking.", "1. Lost Longitudinal History: ")
    add_bullet("Laboratory findings are delivered as unstructured paper or raster PDF attachments that cannot be queried or graphed over time.", "2. Unstructured Diagnostic Silos: ")
    add_bullet("Clinicians must treat acute cases with zero verified knowledge of underlying chronic conditions or allergic reactions.", "3. Zero Clinical Continuity: ")

    add_heading_2("2.2 Month 1 Engineering Objectives")
    add_bullet("Establish a high-performance Monorepo architecture cleanly separating presentation (Next.js 15) and API layers (FastAPI).", "Objective 1 (Foundation): ")
    add_bullet("Engineer normalized relational models for Users, Patients, Doctors, and Diagnostic Facilities with 14-digit ABHA validation.", "Objective 2 (Data Persistence): ")
    add_bullet("Implement cryptographic JWT validation, session cookie handling, and declarative RBAC guards across 4 clinical roles.", "Objective 3 (Identity & Security): ")
    add_bullet("Build a conflict-free appointment scheduling engine with ACID row-level locking (SELECT FOR UPDATE) and 10-minute temporary holds.", "Objective 4 (Clinical Scheduling): ")
    add_bullet("Develop bidirectional HL7 FHIR Release 4 transformers emitting valid Encounter and Appointment JSON resources.", "Objective 5 (Interoperability): ")
    add_bullet("Enforce extreme quality assurance through a minimum of 10 atomic micro-commits daily and 100% automated test coverage.", "Objective 6 (Software Discipline): ")

    # ==================== 3. SYSTEM ARCHITECTURE & 3-PILLAR TOPOLOGY ====================
    add_heading_1("3. System Architecture & 3-Pillar Topology")
    add_body(
        "NIRMAYA is organized into three distinct stakeholder portals, unified through a high-throughput asynchronous API gateway "
        "and standards-compliant data transformation pipelines:"
    )
    add_bullet("A self-sovereign health locker where patients own their complete longitudinal medical history, control time-bound doctor access permissions, and link their simulated 14-digit ABHA identity.", "Pillar 1: Patient Health Vault (/patient) - ")
    add_bullet("A specialized consultation console enabling licensed doctors to review verified patient timelines, conduct appointments, and issue structured encounter documentation.", "Pillar 2: Provider Doctor EMR (/doctor) - ")
    add_bullet("A secure ingestion interface for accredited diagnostic laboratories to upload quantitative parameters and stamped reports.", "Pillar 3: Diagnostic Lab Gateway (/lab) - ")

    add_heading_2("3.1 Technology Stack & Architectural Rationale")
    tech_tbl = doc.add_table(rows=1, cols=3)
    style_table(
        tech_tbl,
        [1.6, 2.2, 2.6],
        ["Architecture Layer", "Technology Selection", "Role & Engineering Rationale"],
        [
            ["Frontend Client", "Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS v4", "High-efficiency server-side rendering, sub-millisecond client transitions, and strict type safety."],
            ["Backend Core", "FastAPI (Python 3.11/3.12), Pydantic v2, Uvicorn ASGI", "Asynchronous non-blocking I/O, strict schema validation, automatic OpenAPI Swagger documentation."],
            ["Data Persistence", "PostgreSQL 16, Async SQLAlchemy 2.0, Alembic", "ACID transactional integrity, connection pooling via asyncpg, declarative relational modeling, and versioned migrations."],
            ["Authentication & Storage", "Supabase Auth (RBAC) & Supabase Storage", "Cryptographic JWT verification (HS256/RS256), short-lived signed URLs for sensitive clinical assets."],
            ["Health Standards", "HL7 FHIR Release 4, Simulated ABDM M1/M2/M3", "Standardized JSON schemas for Encounter, Appointment, Patient, and Practitioner; ABHA & HPR registry compliance."]
        ]
    )

    # ==================== 4. MONTH 1 DETAILED ENGINEERING PROGRESSION ====================
    add_heading_1("4. Month 1 Detailed Engineering Progression (Days 1–20)")
    add_body(
        "Month 1 development followed a strict daily discipline of 10+ atomic micro-commits adhering to Conventional Commits. "
        "The 20-day timeline is summarized across four weekly milestones:"
    )

    add_heading_2("Week 1: Monorepo Scaffold, Telemetry & Diagnostics (Days 1–5)")
    add_bullet("Day 1: Monorepo directory scaffold established; initialized Next.js 15 with Turbopack and FastAPI ASGI application.", "Day 1: ")
    add_bullet("Day 2: Clinical design tokens created in globals.css; semantic colors configured for high-contrast accessibility.", "Day 2: ")
    add_bullet("Day 3: Custom ASGI telemetry middleware implemented injecting X-Request-ID correlation headers and microsecond X-Process-Time metrics.", "Day 3: ")
    add_bullet("Day 4: Unified clinical layout navigation shell constructed with responsive header and role switcher.", "Day 4: ")
    add_bullet("Day 5: Pre-flight diagnostic tool scripts/doctor.py authored to validate 8 subsystems (Python, Node, Venv, Database, Config, Git).", "Day 5: ")
    add_callout("Week 1 Outcome: Monorepo operational with 6 baseline tests passing; automated telemetry and pre-flight doctor check verified.", "Week 1 Milestone Close")

    add_heading_2("Week 2: Relational Data Models & Patient Vault (Days 6–10)")
    add_bullet("Day 6: Async SQLAlchemy 2.0 engine configured with asyncpg connection pooling (pool_size=10, max_overflow=20) and ping health probes.", "Day 6: ")
    add_bullet("Day 7: User and PatientProfile models created; 14-digit ABHA validation logic enforced via regex (91-XXXX-XXXX-XXXX).", "Day 7: ")
    add_bullet("Day 8: DoctorProfile (NMC registration, specialty, consultation fee, HPR ID) and DiagnosticLabFacility entities authored.", "Day 8: ")
    add_bullet("Day 9: Initial Alembic migration 0001_initial_core_schema authored; idempotent test seeder scripts/seed-db.py developed.", "Day 9: ")
    add_bullet("Day 10: Patient Vault CRUD API implemented with full pagination, filtering, and 52 passing automated tests.", "Day 10: ")
    add_callout("Week 2 Outcome: Complete relational schema deployed; Patient Vault operational with 52 tests passing (100% pass rate in 1.85s).", "Week 2 Milestone Close")

    add_heading_2("Week 3: Identity, 4-Tier RBAC & Clean SaaS UI (Days 11–15)")
    add_bullet("Day 11: Supabase Auth integrated with custom JWT middleware decoding tokens and validating user session claims.", "Day 11: ")
    add_bullet("Day 12: Declarative RoleChecker dependency implemented in FastAPI enforcing 4 distinct roles (PATIENT, DOCTOR, LAB_TECHNICIAN, ADMIN).", "Day 12: ")
    add_bullet("Day 13: Doctor EMR directory endpoints created (/api/v1/doctors) with specialty filtering and fee queries.", "Day 13: ")
    add_bullet("Day 14: Frontend migrated to clean SaaS design language (#ffffff white canvas, #111111 dark primary buttons, 1px hairline borders).", "Day 14: ")
    add_bullet("Day 15: Sliding-window token-bucket rate limiter engineered (15 req/min for auth; 60 req/min general) alongside OWASP security headers.", "Day 15: ")
    add_callout("Week 3 Outcome: Strict multi-tenant security perimeter active; UI transformed into clean SaaS interface; test suite expanded to 115 tests.", "Week 3 Milestone Close")

    add_heading_2("Week 4: Clinical Encounters, Concurrency & Release v0.1.0 (Days 16–20)")
    add_bullet("Day 16: DoctorSlot and Appointment models created; slot generation engine developed respecting working hours and break exclusions.", "Day 16: ")
    add_bullet("Day 17: ACID row-level locking implemented with SELECT ... FOR UPDATE, guaranteeing zero double-booking race conditions.", "Day 17: ")
    add_bullet("Day 18: HL7 FHIR Release 4 transformers built; ABDM CareContext deterministic linking engineered with SHA-256 cryptographic digests.", "Day 18: ")
    add_bullet("Day 19: Interactive clinical slot picker component integrated with real-time 10-minute hold countdown timer.", "Day 19: ")
    add_bullet("Day 20: Comprehensive Month 1 regression testing executed; 151/151 tests passed; official milestone release v0.1.0 tagged.", "Day 20: ")
    add_callout("Week 4 Outcome: Conflict-free scheduling engine operational; lossless FHIR export verified; Month 1 officially closed with Release v0.1.0.", "Week 4 Milestone Close")

    # ==================== 5. RELATIONAL DATABASE DESIGN ====================
    add_heading_1("5. Relational Database Design & Schema Specifications")
    add_body(
        "The database architecture consists of 6 core relational entities managed through 3 versioned Alembic migrations:"
    )
    
    schema_tbl = doc.add_table(rows=1, cols=4)
    style_table(
        schema_tbl,
        [1.3, 1.3, 1.8, 2.0],
        ["Entity Table", "Primary Key", "Key Attributes & Types", "Relational Constraints & Foreign Keys"],
        [
            ["users", "id (UUID)", "email (VARCHAR), role (ENUM), is_active (BOOL)", "UNIQUE(email), indexed on email and role."],
            ["patient_profiles", "id (UUID)", "gender (ENUM), date_of_birth (DATE), blood_group (VARCHAR), abha_number (VARCHAR)", "FK(user_id) -> users.id (CASCADE, UNIQUE), UNIQUE(abha_number), UNIQUE(abha_address)."],
            ["doctor_profiles", "id (UUID)", "registration_number (VARCHAR), specialty (ENUM), consultation_fee (INT), hpr_id (VARCHAR)", "FK(user_id) -> users.id (CASCADE, UNIQUE), UNIQUE(registration_number), UNIQUE(hpr_id)."],
            ["diagnostic_labs", "id (UUID)", "facility_name (VARCHAR), license_number (VARCHAR), nabl_acc_no (VARCHAR), hfr_id (VARCHAR)", "FK(user_id) -> users.id (CASCADE, UNIQUE), UNIQUE(license_number), UNIQUE(hfr_id)."],
            ["doctor_slots", "id (UUID)", "start_time (TIMESTAMPTZ), end_time (TIMESTAMPTZ), status (ENUM), held_until (TIMESTAMPTZ)", "FK(doctor_id) -> doctor_profiles.id, FK(held_by_patient_id) -> patient_profiles.id."],
            ["appointments", "id (UUID)", "scheduled_start (TIMESTAMPTZ), status (ENUM), reason (VARCHAR), clinical_notes (TEXT)", "FK(patient_id), FK(doctor_id), FK(slot_id) -> doctor_slots.id (UNIQUE)."]
        ]
    )

    # ==================== 6. STANDARDS COMPLIANCE ====================
    add_heading_1("6. Healthcare Standards Compliance (HL7 FHIR & ABDM)")
    add_heading_2("6.1 HL7 FHIR Release 4 Resource Mappings")
    add_body(
        "NIRMAYA avoids proprietary vendor lock-in by mapping internal relational models to international HL7 FHIR R4 JSON schemas:"
    )
    add_bullet("Mapped to FHIR Appointment (status: proposed/pending/booked/fulfilled; participant references for Patient and Practitioner).", "Appointment Mapping: ")
    add_bullet("Mapped to FHIR Encounter (class: AMB for in-person outpatient, VR for virtual teleconsultation; period start/end).", "Encounter Mapping: ")
    add_bullet("Serialized into standard FHIR Bundle (type: collection) incorporating cryptographic SHA-256 integrity signatures.", "Bundle Encapsulation: ")

    add_heading_2("6.2 Ayushman Bharat Digital Mission (ABDM) Integration")
    add_bullet("Validated against the official NHA 14-digit format (91-XXXX-XXXX-XXXX) with matching @abdm memorable handle.", "ABHA Identity: ")
    add_bullet("Mapped to India's Healthcare Professional Registry format (HP99-XXXX-XXXX).", "Healthcare Professional Registry (HPR): ")
    add_bullet("Deterministic linkage linking appointment encounters to CareContext IDs (APPT-XXXXXXXX) with cryptographic digests for consent sharing.", "CareContext Linkage: ")

    # ==================== 7. CONCURRENCY & SECURITY ====================
    add_heading_1("7. Concurrency Engineering & Security Architecture")
    add_heading_2("7.1 Eliminating Double-Booking Race Conditions")
    add_body(
        "In healthcare appointment booking, simultaneous booking attempts on the same calendar slot represent a critical ACID challenge. "
        "NIRMAYA solves this through a two-tiered reservation protocol:"
    )
    add_bullet("When a patient selects an available slot, an exclusive database row lock is acquired using SQLAlchemy with_for_update().", "Tier 1 (Row-Level Locking): ")
    add_bullet("The slot status transitions to HELD with held_until set to NOW() + 10 MINUTES. Any concurrent request instantly receives HTTP 409 Conflict.", "Tier 2 (10-Minute Hold Window): ")
    add_bullet("An automated background sweeper (sweep_expired_holds) continuously returns expired held slots back to AVAILABLE if the booking is abandoned.", "Tier 3 (Autonomous Sweeper): ")

    add_heading_2("7.2 Defense-in-Depth Security Perimeter")
    add_bullet("FastAPI dependencies (get_current_user, RoleChecker) inspect JWT bearer tokens and reject unauthorized role requests with HTTP 403 Forbidden.", "Role Guards: ")
    add_bullet("Patients can only view and modify their own health profiles; cross-patient data access is strictly blocked at the ORM layer.", "Data Isolation: ")
    add_bullet("Sliding-window token-bucket limiter blocks credential stuffing and brute-force attacks.", "Rate Limiting: ")
    add_bullet("All responses include Content-Security-Policy, HSTS, X-Frame-Options: DENY, and X-Content-Type-Options: nosniff.", "OWASP Headers: ")

    # ==================== 8. QUALITY ASSURANCE & VERIFICATION ====================
    add_heading_1("8. Verification, Testing & Quantitative Growth Metrics")
    add_body(
        "The project maintained continuous integration quality throughout Month 1, verified through comprehensive test suites:"
    )

    metrics_tbl = doc.add_table(rows=1, cols=5)
    style_table(
        metrics_tbl,
        [1.6, 1.1, 1.1, 1.2, 1.4],
        ["Audit Dimension", "Week 1", "Week 2", "Week 3", "Month 1 Finale (Week 4)"],
        [
            ["Automated Pytest Tests", "6 Tests", "52 Tests", "115 Tests", "151 Tests (100% Pass)"],
            ["Execution Runtime", "0.14s", "1.85s", "22.10s", "17.67s (Optimized)"],
            ["Frontend Next.js Routes", "2 Pages", "5 Pages", "11 Routes", "11 Routes Prerendered"],
            ["Alembic Migrations", "0 Revisions", "1 Revision", "1 Revision", "3 Revisions (Verified)"],
            ["Total Micro-Commits", "25 Commits", "85 Commits", "160 Commits", "210+ Atomic Commits"]
        ]
    )

    # ==================== 9. CHALLENGES & LESSONS ====================
    add_heading_1("9. Technical Challenges & Engineering Solutions")
    add_bullet("Challenge: Client-side timers fail if a patient closes their browser tab, leaving slots indefinitely locked. Solution: Built the server-side autonomous sweep_expired_holds background task to reconcile expired locks independently.", "1. Distributed Hold Expiration: ")
    add_bullet("Challenge: Pydantic models with reserved Python keywords (e.g. class_) failed JSON serialization for FHIR compliance. Solution: Implemented Field(alias='class') with populate_by_name=True to maintain clean internal code and valid external JSON.", "2. FHIR Schema Alias Serialization: ")
    add_bullet("Challenge: Ensuring high-concurrency booking integrity under sub-second load. Solution: Evaluated and verified SELECT ... FOR UPDATE transactions under simulated concurrent pytest race conditions.", "3. Concurrency Race Testing: ")

    # ==================== 10. MONTH 2-4 ROADMAP ====================
    add_heading_1("10. Conclusion & Subsequent Phase Roadmap")
    add_body(
        "Month 1 successfully fulfilled 100% of its foundational goals, providing an enterprise-grade platform upon which "
        "advanced clinical diagnostic and health record workflows can be constructed."
    )
    add_bullet("Clinical Problem Lists, LOINC-coded Vital Signs & Observations, Structured SOAP Encounter Notes, and Diagnostic Lab Gateway Orders & Results.", "Month 2 (Clinical Data & Observations): ")
    add_bullet("Structured E-Prescription authoring (MedicationRequest), Pharmacy dispensing simulation, and FHIR Document Bundles.", "Month 3 (Prescriptions & Advanced Exchange): ")
    add_bullet("Full ABDM M2/M3 consent network simulator, production cloud deployment, academic defense, and final thesis documentation.", "Month 4 (Hardening, Cloud & Defense): ")

    p_sign = doc.add_paragraph()
    p_sign.paragraph_format.space_before = Pt(24)
    p_sign.add_run("Submitted by: Suryansh Swarn\nFinal Year B.Tech Project Candidate\nNIRMAYA Platform Lead Developer")
    p_sign.runs[0].font.name = 'Arial'
    p_sign.runs[0].font.size = Pt(10.5)
    p_sign.runs[0].font.bold = True
    p_sign.runs[0].font.color.rgb = NAVY

    output_path = os.path.abspath("NIRMAYA_Interim_Project_Report_Month_1.docx")
    doc.save(output_path)
    print("SUCCESS: Document generated at", output_path)

if __name__ == '__main__':
    create_report()
