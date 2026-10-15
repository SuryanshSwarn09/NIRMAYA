# Engineering Case Study: Next.js 15 Monorepo Deployment Failures on Vercel
## Post-Mortem, Root Cause Analysis & Architectural Resolution

**Project:** NIRMAYA (Networked Interoperable Records Medical Assets & Your Archives)  
**Document ID:** `CS-2026-001`  
**Classification:** Infrastructure, CI/CD, and Build Systems Post-Mortem  
**Author:** Suryansh Swarn (`suryanshswarn@gmail.com`)  
**Date of Incident:** October 15, 2026  
**Status:** Resolved & Deployed  
**Impacting Commits:** `205c59c`, `62d5387`  
**Resolving Commit:** `24071db: fix(vercel): remove vercel.json root override to restore native nextjs subfolder build`  

---

## 1. Executive Summary

On October 15, 2026, the NIRMAYA continuous deployment pipeline on Vercel encountered two successive production build failures on the `main` branch:

1. **Incident 1 (`205c59c`):** Next.js production build failure with exit code `1` caused by an experimental compilation flag (`--turbopack`) invoked during the production bundle generation.
2. **Incident 2 (`62d5387`):** Build runner path resolution failure (`cd: frontend: No such file or directory`) caused by a configuration collision between the Vercel Dashboard project settings and a root-level `vercel.json` configuration file.

This case study provides a thorough technical breakdown of both failure modes, the sequence of events, deep architectural root causes, and the final zero-downtime remediation applied to ensure clean, deterministic monorepo deployments.

---

## 2. Monorepo Architecture Context

NIRMAYA is organized as a decoupled full-stack healthcare monorepo:
```text
NIRMAYA/
├── .github/
├── backend/                  # FastAPI 0.115 + SQLAlchemy 2.0 + HL7 FHIR R4 Engine
│   ├── app/
│   ├── alembic/
│   └── tests/
├── frontend/                 # Next.js 15 + React 19 + Tailwind CSS v4 (Cal.com Design System)
│   ├── src/
│   │   ├── app/              # App Router routes (/patient, /doctor, /lab, /login, /register)
│   │   ├── components/
│   │   └── lib/
│   ├── package.json          # Frontend dependencies & Next.js scripts
│   └── next.config.ts
├── docs/                     # GitBook Documentation & Engineering Logs
├── package.json              # Monorepo root scripts & dev orchestration
└── vercel.json               # (Introduced during Incident 2)
```

In the Vercel hosting platform, NIRMAYA's frontend is deployed as a managed serverless application. When importing monorepos, Vercel allows specifying a **Root Directory** setting (`frontend`), which instructs the build environment to execute all commands from that subfolder context.

---

## 3. Incident 1: The Experimental Turbopack Flag (`205c59c`)

### 3.1 Problem Statement & Symptoms
Following the authoring of Day 28 engineering documentation, the automated Vercel production deployment triggered on commit `205c59c` and abruptly failed:

```text
The production deployment for project nirmaya failed on branch main at commit 205c59c.

Build error
Command "npm run build" exited with 1
Team: Swarn's projects
Commit message: docs(journey): author day 28 engineering log, update summary, and changelog
Failed at: October 15, 2026 at 6:39 AM UTC
```

### 3.2 Root Cause Analysis
Examination of `frontend/package.json` at commit `205c59c` revealed the following script definition:

```json
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build --turbopack",
    "start": "next start",
    "typecheck": "tsc --noEmit"
  }
}
```

- **The Culprit:** The `"build": "next build --turbopack"` directive.
- **Why it failed:** In Next.js 15, Turbopack is stabilized for development environments (`next dev --turbopack`). However, for production compilation (`next build`), Turbopack remains in an experimental evaluation phase. Within Vercel's automated Linux containerized runners, the experimental Turbopack production compiler threw unhandled internal errors during page bundling and tree-shaking, resulting in process termination with exit code `1`.

### 3.3 Initial Remediation
In `frontend/package.json`, the build script was revised to the canonical Next.js production build command:
```diff
- "build": "next build --turbopack"
+ "build": "next build"
```

---

## 4. Incident 2: The Monorepo Working Directory Paradox (`62d5387`)

### 4.1 Problem Statement & Symptoms
Simultaneously with changing `frontend/package.json`, commit `62d5387` attempted to address perceived monorepo root orchestration issues by introducing a root-level `vercel.json` file. When Vercel cloned commit `62d5387`, the build failed instantly with:

```text
12:41:48.528 Running build in Washington, D.C., USA (East) – iad1
12:41:48.529 Build machine configuration: 2 cores, 8 GB
12:41:48.664 Cloning github.com/SuryanshSwarn09/NIRMAYA (Branch: main, Commit: 62d5387)
12:41:49.262 Cloning completed: 597.000ms
12:41:49.663 Restored build cache from previous deployment (HBdCX1bojwbKZZoZkpN7LuCzX3zs)
12:41:50.153 Running "vercel build"
12:41:50.168 Vercel CLI 64.0.2
12:41:50.508 Installing dependencies...
12:41:51.338 up to date in 674ms
12:41:51.338 15 packages are looking for funding
12:41:51.364 Detected Next.js version: 15.5.25
12:41:51.365 Running "cd frontend && npm install && npm run build"
12:41:51.368 sh: line 1: cd: frontend: No such file or directory
12:41:51.379 Error: [BUILD_UTILS_SPAWN_1] Command "cd frontend && npm install && npm run build" exited with 1
```

### 4.2 Root Cause Analysis
The failure log provided four critical diagnostic clues:
1. `Installing dependencies...` installed 15 packages in 674ms.
2. `Detected Next.js version: 15.5.25`.
3. `Running "cd frontend && npm install && npm run build"`.
4. `sh: line 1: cd: frontend: No such file or directory`.

#### Diagnostic Deconstruction
- **Clue A:** Root `package.json` had **zero** package dependencies (only dev scripts). Only `frontend/package.json` contained dependencies (`next`, `react`, `lucide-react`, `tailwindcss`, etc.).
- **Clue B:** Root `package.json` did **not** contain Next.js. Vercel detected `Next.js version: 15.5.25` solely because it was already operating within `frontend/package.json`.
- **The Core Conflict:**
  In the Vercel Dashboard project settings, the project's **Root Directory** was already set to `frontend`.
  Therefore, upon cloning, Vercel immediately executed `cd frontend` before invoking its build lifecycle.
  
  However, in commit `62d5387`, the following `vercel.json` was added to the repository root:
  ```json
  {
    "$schema": "https://openapi.vercel.sh/vercel.json",
    "framework": "nextjs",
    "buildCommand": "cd frontend && npm install && npm run build",
    "outputDirectory": "frontend/.next"
  }
  ```
  Vercel loaded this `buildCommand` override and executed it within the already-selected root directory (`frontend/`).
  Inside `frontend/`, there is no child directory named `frontend`. Consequently, the shell command `cd frontend` threw:
  `sh: line 1: cd: frontend: No such file or directory`.

---

## 5. Architectural Resolution

### 5.1 The Definitive Fix (`24071db`)
The fix required eliminating the root `vercel.json` file completely, allowing Vercel's native Next.js monorepo detection to function unhindered.

#### Action 1: Deletion of `vercel.json`
```bash
git rm vercel.json
```
Removing `vercel.json` eradicated both invalid configuration overrides:
- `buildCommand: "cd frontend && ..."` (which failed because the runner was already inside `frontend/`).
- `outputDirectory: "frontend/.next"` (which would have searched for `frontend/frontend/.next`).

#### Action 2: Canonical Scripts in `frontend/package.json`
Ensured `frontend/package.json` strictly adheres to standardized Next.js commands:
```json
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "clsx": "^2.1.1",
    "framer-motion": "^13.2.0",
    "lucide-react": "^1.43.0",
    "next": "15.5.25",
    "react": "19.1.0",
    "react-dom": "19.1.0",
    "tailwind-merge": "^3.6.0"
  }
}
```

#### Action 3: Fallback Scripts in Root `package.json`
Ensured the monorepo root `package.json` provides convenience commands for local developers or general CI runners executing from repository root:
```json
{
  "name": "nirmaya",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "powershell -ExecutionPolicy Bypass -File ./scripts/run-dev.ps1",
    "dev:bash": "bash ./scripts/run-dev.sh",
    "dev:frontend": "npm --prefix frontend run dev",
    "dev:backend": "cd backend && python -m uvicorn app.main:app --reload --port 8000",
    "build": "npm --prefix frontend install && npm --prefix frontend run build",
    "build:frontend": "npm --prefix frontend run build",
    "test:backend": "cd backend && python -m pytest -v",
    "test": "npm --prefix frontend run build && cd backend && python -m pytest",
    "doctor": "python scripts/doctor.py"
  }
}
```

---

## 6. Verification & Results

### 6.1 Local Build Verification
Executed direct Next.js production compilation within `frontend/`:
```bash
$ cd frontend && npm run build

> frontend@0.1.0 build
> next build

   ▲ Next.js 15.5.25

   Creating an optimized production build ...
 ✓ Compiled successfully in 17.2s
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/11) ...
   Generating static pages (2/11)
   Generating static pages (5/11)
   Generating static pages (8/11)
 ✓ Generating static pages (11/11)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    6.57 kB         123 kB
├ ○ /_not-found                            991 B         104 kB
├ ○ /doctor                              6.84 kB         159 kB
├ ○ /icon.png                                0 B            0 B
├ ○ /lab                                 6.67 kB         150 kB
├ ○ /login                               2.63 kB         129 kB
├ ○ /patient                             11.1 kB         159 kB
└ ○ /register                             2.5 kB         129 kB
+ First Load JS shared by all             103 kB

ƒ Middleware                             34.2 kB
○ (Static) prerendered as static content
```
- **Exit Code:** `0` (Success)
- **Compilation Time:** `17.2s`
- **Output:** 11/11 static pages generated with zero TypeScript or PostCSS errors.

### 6.2 Cloud CI/CD Deployment Outcome
With commit `24071db` pushed to `origin/main`, Vercel:
1. Clones the repository.
2. Changes directory to `frontend/` as specified by project configuration.
3. Automatically runs `npm install`.
4. Runs `npm run build` (`next build`).
5. Locates `.next/` and serves the production deployment globally.

---

## 7. Lessons Learned & Best Practices

1. **Never Compound Assumptions in Monorepos:**
   When troubleshooting CI/CD failures in a monorepo, always verify whether the cloud platform executes from repository root or has an active subfolder Root Directory setting before adding path-relative shell commands (`cd <folder>`).
2. **Restrict Experimental Flags to Development:**
   Next.js experimental flags (such as `--turbopack` on `next build`) must never be placed in production `build` scripts. Use `--turbopack` strictly for `next dev`.
3. **Embrace Zero-Config Framework Conventions:**
   Vercel natively understands Next.js structure. Attempting to override framework build and output commands with custom `vercel.json` parameters often breaks standard asset tracing and serverless function packaging. Keep configuration minimal.
