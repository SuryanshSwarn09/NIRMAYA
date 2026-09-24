# NIRMAYA Frontend Portal

**Technology Stack:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS v4, Framer Motion  
**Design System:** Cal.com-inspired modern SaaS aesthetic with pure white canvas, `#111111` primary CTAs, and embedded product UI chrome.

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

- `/` — Cal.com 7/5 Hero, NavPillGroup pillar switcher, clinical booking mockup.
- `/login` — One-click clinical demo personas (Dr. Sharma, Arun Patel, Apollo Labs, Root Admin).
- `/register` — ABDM 14-digit ABHA ID onboarding workflow.
- `/patient` — Longitudinal Patient Vault, ABHA Health ID card, consent delegation manager.
- `/doctor` — Provider EMR Console, clinical appointment schedule, FHIR MedicationRequest authoring.
