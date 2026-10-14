# Week 15: Docker Containerization & Cloud Deployment

**Milestone Target:** Author production-grade multi-stage Dockerfiles for backend and frontend, configure automated GitHub Actions CI/CD pipelines, provision SSL/TLS ingress, and deploy to production cloud infrastructure.

---

## Daily Schedule & Architectural Focus

| Day | Focus Area | Planned Deliverables | Status |
|---|---|---|---|
| **Day 71** | Production Multi-Stage Dockerfiles | Alpine-based minimal image builds (<120MB backend, standalone Next.js) | Planned |
| **Day 72** | Docker Compose & Production Orchestration | Multi-service compose topology (App, DB, Redis, Caddy reverse proxy) | Planned |
| **Day 73** | Automated GitHub Actions CI/CD | Linting, test suite execution, image build, and auto-deployment pipeline | Planned |
| **Day 74** | Cloud Provisioning & SSL Setup | Production VPS configuration, automated Let's Encrypt SSL/TLS certificates | Planned |
| **Day 75** | Staging Verification & Smoke Testing | Smoke tests on live production environment, database migration dry-run | Planned |

---

## Infrastructure Highlights

- **Container Footprint:** Lightweight images with non-root security contexts and minimal attack surfaces.
- **Continuous Delivery:** Automated zero-downtime deployment pipeline driven by GitHub repository tags.
