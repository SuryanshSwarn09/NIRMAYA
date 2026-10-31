# Week 15: Docker Containerization & Cloud Deployment

**Milestone Target:** Author production-grade multi-stage Dockerfiles for backend and frontend, configure automated GitHub Actions CI/CD pipelines, provision SSL/TLS ingress, and deploy to production cloud infrastructure.

---

## Daily Schedule & Architectural Focus

| Day | Milestone | Focus Area | Planned Deliverables | Status |
|---|---|---|---|---|
| **Day 71** | Milestone 15-01 | Production Multi-Stage Dockerfile | Alpine-based minimal image (<120MB), CIS non-root user (UID 10001), healthcheck | **Completed** (570 Tests) |
| **Day 72** | Milestone 15-02 | Next.js 15 Standalone Dockerfile | Standalone Next.js container, asset caching, minimal static footprint | Planned |
| **Day 73** | Milestone 15-03 | Docker Compose & Production Topology | Multi-service orchestration (FastAPI, Next.js, PostgreSQL 16 with ltree, Redis 7, Caddy TLS 1.3) | Planned |
| **Day 74** | Milestone 15-04 | Dual-Mode Edge Node Appliance | Turnkey edge node packaging (`docker-compose.edge.yml`) & Local-First SQLite sync | Planned |
| **Day 75** | Milestone 15-05 | Foreign Data Wrapper & Legacy HIS Federation | PostgreSQL `postgres_fdw` & read-only legacy HIS federation adapter | Planned |

---

## Infrastructure Highlights

- **Container Footprint:** Lightweight images (< 120MB target) with non-root security contexts (UID 10001) and minimal attack surfaces.
- **Continuous Delivery:** Automated zero-downtime deployment pipeline driven by GitHub repository tags.
- **Test Baseline:** 570/570 cumulative tests passing across 35 test modules (100% green).
