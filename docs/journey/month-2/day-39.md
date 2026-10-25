# Day 39: Milestone 08-04: Lab Order Requisition & PACS Viewer

**Date:** October 25, 2026  
**Milestone:** 08-04 (Month 2, Week 8)  
**Executed Micro-Commits (Strict 7-Commit Schedule):**  
1. `5df934d: feat(clinical): implement PACS / DICOM medical imaging viewer modal`
2. `4c760a2: feat(clinical): expand LOINC test catalog and imaging orders in DiagnosticOrderTracker`
3. `faeafd0: refactor(clinical): apply Cal.com geometric design tokens to diagnostic components`
4. `1a20b58: feat(doctor): integrate lab requisition and PACS imaging viewer into Doctor EMR`
5. `7200c6c: test(backend): add test suite for imaging requisitions, DICOM metadata, and FHIR export`
6. `docs(journey): record Day 39 milestone log and update Week 8 roadmap`
7. `chore(sync): verify production build, full test suite pass, and clean repo state`

---

## 1. Objectives & Architectural Context

Following the completion of Day 36 (Clinician Consultation Queue), Day 37 (Structured SOAP Note Authoring Pad), and Day 38 (Integrated Prescription Authoring & Search), **Day 39 (Milestone 08-04)** delivers the **Lab Order Requisition & PACS Viewer** experience within the NIRMAYA Doctor EMR and Diagnostic Gateway.

In modern healthcare under HL7 FHIR Release 4, DICOM 3.0, and ABDM standards, diagnostic investigation workflows require seamless coordination between clinical pathology orders (`ServiceRequest`), verified lab reports (`DiagnosticReport`), and radiological imaging studies (`ImagingStudy`). **Day 39** delivers high-fidelity medical imaging inspection and expanded LOINC diagnostic requisitioning adhering strictly to the **Cal.com design system** (`calcom-design-system` skill) and anti-vibe-coding standards:

1. **Interactive PACS / DICOM Medical Imaging Viewer Modal (`PacsViewerModal.tsx`):**
   - **Supported Diagnostic Modalities:**
     - Computed Radiography (`CR` / `DX`): Chest X-Ray 2 Views PA and Lateral (LOINC `24648-8`).
     - Electrocardiography (`ECG`): Standard 12-Lead Diagnostic Strip (LOINC `11524-6`, 25mm/s, 10mm/mV calibration).
     - Computed Tomography (`CT`): Head and Brain Axial non-contrast series (LOINC `36642-7`, 3.0mm thin slices).
     - Ultrasound (`US`): Transthoracic 2D Doppler Echocardiogram (LOINC `77484-4`, Apical 4-Chamber view).
   - **Radiologist Windowing Presets:**
     - `Native`: Standard acquisition density.
     - `Lung`: High contrast enhancement for pulmonary bronchovascular parenchymal markings.
     - `Bone`: High threshold sharpening for osseous cortex and clavicular/rib detail.
     - `Soft Tissue`: Smooth gradation for mediastinal and cardiac silhouette contours.
     - `Inverted`: Photonegative monochromatic inversion for subtle interstitial opacity detection.
   - **Pan, Zoom, and Rotation Engine:**
     - Zoom In (+25%), Zoom Out (-25%), Reset to 100%, Fit to Canvas.
     - 90-degree step rotation (`RotateCw`).
   - **Digital Measurement Caliper Tool:**
     - Interactive point-to-point digital caliper overlay with calibrated DICOM pixel-to-millimeter calculation (0.28 mm/px pitch approximation) for cardiothoracic ratio (CTR) and lesion dimension estimation.
   - **DICOM Header & Metadata Drawer:**
     - Full DICOM 3.0 tag inspector: Study Instance UID (0020,000D), Series Instance UID (0020,000E), SOP Instance UID (0008,0018), Modality (0008,0060), Accession Number (0008,0050), Photometric Interpretation (`MONOCHROME2`), and WADO-RS RESTful endpoint references.
     - Client-side JSON metadata export (`Download` action).
   - **Radiology Clinical Findings & Impression:**
     - Integrated radiologist report drawer with clinical findings narrative, impressions, and digital sign-off provenance.

2. **Expanded LOINC Diagnostic Panel Requisition (`DiagnosticOrderTracker.tsx`):**
   - Comprehensive test picker covering both Laboratory Pathology and Diagnostic Imaging:
     - Biochemistry & Hematology: Lipid Panel (`24331-1`), HbA1c (`4548-4`), CBC with Auto Diff (`58410-2`), Creatinine with eGFR (`38483-4`), Total Cholesterol (`2093-3`), Total Bilirubin (`1975-2`), TSH (`3016-3`).
     - Diagnostic Imaging: Chest X-Ray (`24648-8`), 12-Lead ECG (`11524-6`), CT Head (`36642-7`), Echocardiogram (`77484-4`).
   - Priority tier selection: Routine, Urgent, STAT (Emergency).
   - Specimen type selection (serum, whole blood, plasma, urine) and 12-hour fasting requirement checkbox.
   - One-click "Launch PACS Viewer" button on completed imaging reports.

3. **Doctor Workspace & Quick Action Rail Integration:**
   - Quick Action Rail updated with dedicated "Diagnostics & PACS" action (keyboard shortcut `4`, with "PACS" badge).
   - Doctor EMR Tab 4 synchronized with active patient context (`key={activePatient.id}`).

4. **Cal.com Geometric Polish & Anti-Vibe-Coding:**
   - Sharp geometric buttons (`rounded-[8px]`), rectangular badge chips (`rounded-[6px]`), zero pill-shaped buttons.
   - Zero purple or multi-color gradients.
   - Zero emoji icons (standard Lucide SVG icons only).
   - Zero em dashes (`—`).

5. **Automated Backend Test Suite Expansion (`backend/tests/test_diagnostics.py`):**
   - Added unit and integration tests (12/12 passing):
     - `test_imaging_requisition_service_request`: Urgent imaging requisition with FHIR R4 `ServiceRequest` serialization.
     - `test_imaging_report_dicom_metadata_persistence`: Storage and retrieval of DICOM Study/Series UIDs and windowing presets in `report_data`.
     - `test_stat_priority_and_fasting_requirement_handling`: STAT emergency priority and specimen fasting verification.

---

## 2. Engineered Component Architecture

```
e:\nirmaya-side\
├── frontend\src\
│   ├── components\clinical\
│   │   ├── PacsViewerModal.tsx          # Full-featured DICOM 3.0 PACS imaging console with windowing, zoom, calipers & metadata
│   │   ├── DiagnosticOrderTracker.tsx   # Requisition pad with expanded LOINC catalog, imaging presets, and PACS viewer launcher
│   │   ├── ClinicalQuickActionRail.tsx  # Quick-action rail updated with Diagnostics & PACS action and badge
│   │   ├── MedicationCatalogBrowser.tsx # Cal.com rounded-[6px] geometric tag chip refactor
│   │   └── index.ts                     # Barrel exports for PacsViewerModal, DicomStudy types, and presets
│   └── app\doctor\page.tsx              # Patient-synchronized EMR diagnostics tab
└── backend\
    └── tests\
        └── test_diagnostics.py          # 12 comprehensive unit and integration tests (100% green)
```

---

## 3. Verification & Compliance Evidence

1. **Frontend Typecheck:**
   - `npx tsc --noEmit` exited with code 0 (zero errors).
2. **Frontend Production Build:**
   - `npm run build` generated 13/13 static routes cleanly with zero CSS errors or warnings.
3. **Backend Test Suite:**
   - `pytest tests/test_diagnostics.py -v`: 12/12 passed (100% green in 4.64s).
4. **Anti-Vibe-Coding Audit:**
   - Zero purple gradients (`rg -i "purple|bg-gradient"`: 0).
   - Zero emoji icons (`rg "[\x{1F300}-\x{1F9FF}]"`: 0).
   - Zero em dashes (`rg "—"`: 0).
5. **Git Hygiene:**
   - Strict author configuration `--author="Suryansh Swarn <suryanshswarn@gmail.com>"`.
   - Zero release tags (Milestone release `v0.2.0` strictly reserved for Day 40).
