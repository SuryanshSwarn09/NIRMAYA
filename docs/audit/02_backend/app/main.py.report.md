# Principal Software Engineering Audit: backend/app/main.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/main.py` is the central FastAPI application factory and entrypoint for the NIRMAYA backend service. It instantiates the `FastAPI` application object, configures lifespan event handlers (initializing and shutting down the distributed WebSocket message bus), registers custom exception handlers, sets up the middleware execution pipeline (performance telemetry, correlation IDs, token-bucket rate limiting, dynamic CORS), mounts the API v1 router, hooks ABDM `/v0.5` gateway webhook endpoints, and mounts the real-time `/ws` WebSocket stream routes. Critical architectural and security vulnerabilities include unconditional public exposure of Swagger/OpenAPI documentation in production environments, lack of database connection pool verification during lifespan startup, and late global imports inside the module scope.

### System Topology & Architectural Invariants
```
                  +-----------------------------------------------+
                  |          ASGI Container Entry / Uvicorn       |
                  |                (app.main:app)                 |
                  +-----------------------+-----------------------+
                                          |
                                          v
                  +-----------------------------------------------+
                  |        FastAPI Lifecycle (lifespan)           |
                  |  - Startup: app.state.start_time, ws_manager  |
                  |  - Shutdown: ws_manager.shutdown()            |
                  +-----------------------+-----------------------+
                                          |
                                          v
                  +-----------------------------------------------+
                  |        Middleware Execution Pipeline          |
                  |  1. CORSMiddleware (Dynamic origins)          |
                  |  2. RateLimitingMiddleware (Token Bucket)     |
                  |  3. CorrelationIdMiddleware (X-Request-ID)    |
                  |  4. PerformanceTelemetryMiddleware (Headers)  |
                  +-----------------------+-----------------------+
                                          |
        +-----------------+---------------+-----------------+
        |                 |               |                 |
        v                 v               v                 v
  +-----------+     +-----------+   +-----------+     +-----------+
  | API v1    |     | ABDM /v0.5|   | /ws       |     | Root /    |
  | Router    |     | Webhooks  |   | WebSocket |     | Discovery |
  | (/api/v1) |     | Gateways  |   | Gateway   |     +-----------+
  +-----------+     +-----------+   +-----------+
```

### Import / Export Surface Map
- **Upstream Dependencies:**
  - `contextlib.asynccontextmanager`: Async lifespan context management.
  - `fastapi.FastAPI`, `fastapi.middleware.cors.CORSMiddleware`: ASGI framework and CORS middleware.
  - `app.core.config.settings`: Configuration parameters.
  - `app.core.cors.get_allowed_origins`: Dynamic CORS origin calculation.
  - `app.core.middleware`: `PerformanceTelemetryMiddleware`, `CorrelationIdMiddleware`.
  - `app.core.rate_limit.RateLimitingMiddleware`: Token-bucket rate limiting.
  - `app.core.exceptions.register_exception_handlers`: Application exception registry.
  - `app.api.v1.router.api_router`: Central API v1 router.
  - `app.services.websocket_manager.ws_manager`: Global WebSocket connection manager.
  - `app.api.v1.endpoints`: `abdm_m2_bridge`, `abdm_m3_consent`, `abdm_m3_crypto`, `abdm_m3_transfer`, `websockets`.
- **Downstream Consumers:**
  - ASGI servers (`uvicorn`, `gunicorn`).
  - Container entrypoint (`docker-entrypoint.sh`).
- **Exported Interface:**
  - `app`: Configured `FastAPI` instance.
  - `lifespan`: Async lifecycle manager.
  - `root`: Root metadata discovery endpoint (`GET /`).

---

## Layer B: Plain-Language Developer Walkthrough

`backend/app/main.py` is the execution root that ties together all middleware, routing, and background systems:
1. **Lifespan Management (`lifespan`)**: When Uvicorn starts the application, `lifespan` runs lines 24-26, stamping `app.state.start_time` and awaiting `ws_manager.initialize()` (which connects to the Redis message bus or starts the in-memory bus). When the server receives a termination signal, execution resumes at lines 28-29, awaiting `ws_manager.shutdown()` to release client connections and Pub/Sub subscriptions.
2. **FastAPI Instance Initialization**: Instantiates `app` with metadata, API documentation paths (`/docs`, `/redoc`), and the OpenAPI schema URL (`/api/v1/openapi.json`).
3. **Middleware Pipeline**:
   - Exception Handlers: Binds custom handlers for domain exceptions (`ConflictException`, `EntityNotFoundException`, validation errors).
   - `PerformanceTelemetryMiddleware`: Adds `X-Process-Time` and GIGW 3.0 security headers (`Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`).
   - `CorrelationIdMiddleware`: Extracts or assigns `X-Request-ID` UUIDs.
   - `RateLimitingMiddleware`: Enforces tiered IP/token-bucket rate limits.
   - `CORSMiddleware`: Evaluates client origin against dynamic domain whitelists.
4. **Route Registration**: Mounts the primary `api_router` under `/api/v1`, mounts the official ABDM `/v0.5` callback webhooks at root `/v0.5` (for HIP/HIU callbacks expected by the National Health Authority), and exposes WebSocket endpoints at `/ws`.
5. **Root Discovery Endpoint (`GET /`)**: Returns basic operational telemetry (name, version, environment, active standards).

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Unconditional Public Swagger/OpenAPI Exposure in Production
In lines 40-42:
```python
docs_url="/docs",
redoc_url="/redoc",
openapi_url=f"{settings.API_V1_STR}/openapi.json",
```
Interactive API documentation (`/docs`, `/redoc`) and OpenAPI schemas are exposed unconditionally across all deployment environments. In a production healthcare system handling sensitive Protected Health Information (PHI) under DPDP Act 2023, public exposure of full API schema definitions aids attackers in reconnaissance, schema mapping, and automated exploitation. In production (`settings.ENVIRONMENT == "production"`), these parameters should evaluate to `None`.

### Invariant 2: Absence of Database Connection Verification in Lifespan
In `lifespan` (lines 21-30), the startup sequence initializes the WebSocket message bus but never attempts to connect to or query the PostgreSQL database pool. If the database credentials are misconfigured, the database host is unreachable, or the connection pool fails to initialize, the application signals `ready` to the container orchestrator (e.g., Kubernetes readiness probe passes), but the very first incoming HTTP request crashes with an unhandled database connection exception.

### Invariant 3: Late Module Imports Breaking Static Analysis
In line 72:
```python
# 6. Include ABDM Gateway /v0.5 Webhook Root Route
from app.api.v1.endpoints import abdm_m2_bridge, abdm_m3_consent, abdm_m3_crypto, abdm_m3_transfer, websockets
```
Placing module imports halfway through the file breaks standard PEP 8 import styling, risks circular import deadlocks during application bootstrap, and interferes with static analysis tools.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-APP-MAN-F01` | **S1** | `[SEC]` | `app/main.py:40-42` | Interactive API documentation (`/docs`, `/redoc`) and OpenAPI schemas are exposed in production without environment gating. |
| `BE-APP-MAN-F02` | **S2** | `[QUAL]` | `app/main.py:21-30` | Lifespan startup does not test database connection pool or run readiness verification before accepting traffic. |
| `BE-APP-MAN-F03` | **S3** | `[QUAL]` | `app/main.py:72` | Late module imports inside global file body violate PEP 8 and introduce circular import vulnerabilities. |
| `BE-APP-MAN-F04` | **S3** | `[DOC]` | `app/main.py:59` | Duplicate comment numbering (`# 4.` used twice) in middleware configuration block. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-APP-MAN-F01-F02`: Gated Documentation & Database Warmup
```diff
--- a/backend/app/main.py
+++ b/backend/app/main.py
@@ -17,14 +17,24 @@
 from app.api.v1.router import api_router
 from app.services.websocket_manager import ws_manager
+from app.db.session import engine
+from sqlalchemy import text
 
 
 @asynccontextmanager
 async def lifespan(app: FastAPI):
     """Manage application lifecycle events (startup initialization and shutdown cleanup)."""
     # Startup: Record system initialization timestamp and start real-time message bus
     app.state.start_time = time.time()
+    async with engine.begin() as conn:
+        await conn.execute(text("SELECT 1"))
     await ws_manager.initialize()
     yield
     # Shutdown: Cleanly release active WebSocket connections and message bus adapter
     await ws_manager.shutdown()
 
+is_prod = settings.ENVIRONMENT.lower() in ("production", "prod")
 
 app = FastAPI(
     title=settings.PROJECT_NAME,
@@ -39,9 +49,9 @@
     ),
     version=settings.VERSION,
-    docs_url="/docs",
-    redoc_url="/redoc",
-    openapi_url=f"{settings.API_V1_STR}/openapi.json",
+    docs_url=None if is_prod else "/docs",
+    redoc_url=None if is_prod else "/redoc",
+    openapi_url=None if is_prod else f"{settings.API_V1_STR}/openapi.json",
     debug=settings.DEBUG,
     lifespan=lifespan,
 )
```
