# NIRMAYA Frontend Portal

**Technology Stack:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS v4, Framer Motion  
**Design System:** Modern SaaS aesthetic with pure white canvas, `#111111` primary CTAs, and embedded product UI chrome.

- 🌐 **Live Deployed Web Portal:** [https://nirmaya-tau.vercel.app/](https://nirmaya-tau.vercel.app/)
- 📖 **Official GitBook Documentation:** [https://suryanshs-projects.gitbook.io/nirmaya-docs](https://suryanshs-projects.gitbook.io/nirmaya-docs)
- ⚙️ **FastAPI Core Backend:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Getting Started Locally

```bash
# Install dependencies
npm install

# Run development server with Turbopack
npm run dev

# Build production bundle
npm run build
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

---

## Key Portal Routes

- `/` — Modern 7/5 Hero, NavPillGroup pillar switcher, clinical booking mockup.
- `/login` — One-click clinical demo personas (Dr. Sharma, Arun Patel, Apollo Labs, Root Admin).
- `/register` — ABDM 14-digit ABHA ID onboarding workflow.
- `/patient` — Longitudinal Patient Vault, ABHA Health ID card, consent delegation manager, ICD-10 problem list, and compound vitals timeline.
- `/doctor` — Provider EMR Console, clinical appointment schedule, SHA-256 signed SOAP clinical documentation pad, LOINC lab requisition ordering, and active problem list management.
- `/lab` — Diagnostic Laboratory Console, LOINC diagnostic observation builder, requisition queue, diagnostic order tracker, and FHIR DiagnosticReport fulfillment.

---

## Clinical Architecture Modules

- **ProblemListPanel** (`components/clinical/ProblemListPanel.tsx`): Active and resolved ICD-10-CM clinical condition manager with severity, verification status, and FHIR R4 Condition JSON inspector.
- **VitalsTelemetryPanel** (`components/clinical/VitalsTelemetryPanel.tsx`): LOINC-coded physiological observations (compound BP 85354-9, HR 8867-4, SpO2 59408-5, BMI 39156-5) with clinical alerts and FHIR Observation inspector.
- **SoapNoteEditor** (`components/clinical/SoapNoteEditor.tsx`): Structured SOAP documentation pad (Subjective, Objective, Assessment, Plan) with LOINC section bindings, SHA-256 digital signature signing, and FHIR Composition inspector.
- **DiagnosticOrderTracker** (`components/clinical/DiagnosticOrderTracker.tsx`): Real-time diagnostic requisition tracker across lifecycle states (`draft` -> `active` -> `completed`), priority badges, and FHIR DiagnosticReport fulfillment.
