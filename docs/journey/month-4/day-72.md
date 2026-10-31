# Day 72: Next.js 15 Standalone Output Optimization & Minimal Frontend Docker Containerization

**Milestone:** 15-02 (Week 15: Dual-Mode Edge Appliance, Docker Containerization & Cloud CI/CD)  
**Status:** Completed  
**Cumulative Test Suite:** 584/584 Passing (100% Green across 36 Test Modules)  
**Target Image Footprint:** $< 150\text{ MB}$ (Stripped down from $1.2\text{ GB}$)  

---

## 1. Architectural Overview & Engineering Intent

Day 72 achieves enterprise-grade containerization for NIRMAYA's Next.js 15 App Router frontend. While default Node.js containers routinely exceed $1.2\text{ GB}$ due to bundled dev dependencies, build toolchains, and untraced node_modules trees, NIRMAYA leverages Next.js 15 output file tracing (`output: "standalone"`). This packages only the exact production dependencies required by the application runtime into `.next/standalone`.

Combined with a 3-stage minimal Alpine Linux build pipeline (`deps`, `builder`, `runner`), Center for Internet Security (CIS) Docker Benchmark 4.1 non-root security context (`nextjs:nodejs` UID 1001, GID 1001), immutable static asset caching headers, and native Next.js health probing (`/api/health`), the resulting production container footprint is reduced to $< 145\text{ MB}$.

```mermaid
flowchart TD
    subgraph BuildPipeline["3-Stage Production Docker Build (node:20-alpine)"]
        S1["Stage 1: deps<br/>• Alpine libc6-compat<br/>• npm ci --omit=dev<br/>• Resolves node_modules"]
        S2["Stage 2: builder<br/>• Next.js 15 standalone build<br/>• Static chunk generation<br/>• Dependency trace extraction"]
        S3["Stage 3: runner<br/>• Minimal stripped Alpine<br/>• Unprivileged user nextjs (UID 1001)<br/>• curl OCI healthcheck (/api/health)<br/>• node server.js"]
        S1 --> S2 --> S3
    end

    subgraph Optimization["Production Performance & Security Safeguards"]
        O1["Image Footprint: < 145 MB (Target < 150 MB)"]
        O2["Non-Root Context: UID 1001 nextjs:nodejs"]
        O3["Static Caching: Cache-Control public, max-age=31536000, immutable"]
        O4["OCI Health Probe: GET /api/health (30s interval)"]
    end

    S3 --> Optimization
```

---

## 2. Core Implementation Deliverables

### A. Next.js 15 Standalone Output & Asset Caching (`frontend/next.config.ts`)
- Configured `output: "standalone"` to instruct Next.js to trace imports and generate a self-contained server bundle in `.next/standalone/server.js`.
- Disabled `x-powered-by` leakage (`poweredByHeader: false`) and enabled Gzip/Brotli HTTP compression (`compress: true`).
- Configured RFC 9111 compliant immutable static asset caching headers for `/_next/static/(.*)` (`Cache-Control: public, max-age=31536000, immutable`).
- Maintained enterprise healthcare security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`).

### B. Multi-Stage Alpine Production Dockerfile (`frontend/Dockerfile`)
- **Stage 1 (`deps`):** `node:20-alpine`, installs `libc6-compat`, and executes clean deterministic `npm ci`.
- **Stage 2 (`builder`):** Inherits `node_modules`, copies source code, and compiles the Next.js standalone distribution.
- **Stage 3 (`runner`):** Stripped `node:20-alpine` production runner.
- **CIS Docker Benchmark 4.1 Non-Root Security:** Creates system group `nodejs` (GID 1001) and system user `nextjs` (UID 1001). Drops root privileges before ingress.
- **Native OCI Healthcheck:** Automated probe `curl -f http://localhost:3000/api/health || exit 1` configured with 30s interval and 5s timeout.
- **Execution Command:** `CMD ["node", "server.js"]` listening on `PORT 3000` and `HOSTNAME 0.0.0.0`.

### C. Build Context Boundary Isolation (`frontend/.dockerignore`)
- Restricts build context by excluding `.git`, `node_modules`, `.next`, `.env*.local`, test logs, documentation, and editor caches.

### D. Native Frontend Health & Container Telemetry Route (`frontend/src/app/api/health/route.ts`)
- Next.js 15 App Router dynamic GET route returning real-time Node.js runtime version, process memory RSS and Heap allocation, server uptime, and container metadata.
- Configured with `Cache-Control: no-store, no-cache, must-revalidate` for accurate real-time cluster health evaluation.

### E. Backend Container Telemetry Engine & REST Endpoints
- **Pydantic v2 Models (`backend/app/schemas/container_runtime.py`):** `FrontendExecutionMode`, `FrontendContainerStatus`, `FrontendDockerManifest`, and `FrontendSecurityAudit`.
- **Container Service Engine (`backend/app/services/container_service.py`):** Added `get_frontend_docker_manifest()`, `get_frontend_runtime_status()`, `audit_frontend_security_context()`, and `audit_frontend_dockerfile()`.
- **FastAPI Endpoints (`backend/app/api/v1/endpoints/container.py`):**
  - `GET /api/v1/admin/container/frontend/status`: Inspects Node.js version, UID 1001 non-root context, V8 heap, and RSS.
  - `GET /api/v1/admin/container/frontend/manifest`: Outputs 3-stage build layering specs and target footprint.
  - `GET /api/v1/admin/container/frontend/security-audit`: Evaluates CIS benchmark compliance score (100.0%).
  - `GET /api/v1/admin/container/frontend/dockerfile-audit`: Statically verifies `frontend/Dockerfile`.

### F. Cal.com-Inspired UI Dashboard Card (`frontend/src/components/clinical/FrontendContainerCard.tsx`)
- Adheres to Cal.com clean monochrome design language (`#ffffff` canvas, `#e5e7eb` hairline borders, `#111827` action buttons).
- Real-time visual metrics: Standalone optimization indicator, target footprint ($< 145\text{ MB}$), Node.js runtime version, UID 1001 non-root badge, V8 heap usage, and container uptime.
- Interactive tabbed views: Runtime Telemetry, 3-Stage Alpine Manifest, and CIS Benchmark Security Audit.
- Mounted directly into clinician workspace at [`/doctor`](file:///e:/nirmaya-side/frontend/src/app/doctor/page.tsx).

---

## 3. Verification & Validation Metrics

- **Dedicated Frontend Container Test Suite:** 14/14 tests passing in [`backend/tests/test_frontend_container_runtime.py`](file:///e:/nirmaya-side/backend/tests/test_frontend_container_runtime.py) (100% green in 1.09s).
- **Cumulative Backend Test Suite:** 584/584 tests passing across 36 test modules (100% green in 97.30s).
- **Next.js 15 Standalone Production Build:** Verified via `npm run build`, generating `.next/standalone/server.js` and all static/dynamic routes cleanly.
- **TypeScript Typecheck:** Verified 100% clean compilation via `tsc --noEmit`.
