"""NIRMAYA: Networked Interoperable Records Medical Assets & Your Archives
FastAPI Application Entrypoint
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.cors import get_allowed_origins
from app.core.middleware import (
    PerformanceTelemetryMiddleware,
    CorrelationIdMiddleware,
)
from app.core.rate_limit import RateLimitingMiddleware
from app.core.exceptions import register_exception_handlers
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events (startup initialization and shutdown cleanup)."""
    # Startup: Record system initialization timestamp
    app.state.start_time = time.time()
    yield
    # Shutdown: Cleanly release active connection pools and background tasks


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "**NIRMAYA: Networked Interoperable Records Medical Assets & Your Archives**\n\n"
        "An enterprise-grade Unified Health Interoperability Network and Longitudinal "
        "Patient Vault built on HL7 FHIR R4 and simulated ABDM (Ayushman Bharat Digital Mission) standards."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# 1. Register custom application & validation exception handlers
register_exception_handlers(app)

# 2. Add performance telemetry middleware (X-Process-Time, security headers)
app.add_middleware(PerformanceTelemetryMiddleware)

# 3. Add correlation ID middleware (X-Request-ID propagation)
app.add_middleware(CorrelationIdMiddleware)

# 4. Add token-bucket rate limiting middleware (DDoS & brute force mitigation)
app.add_middleware(RateLimitingMiddleware)

# 4. Set up dynamic CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    """Root metadata discovery endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} ({settings.PROJECT_FULL_NAME}) API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
        "standards": ["HL7 FHIR R4", "ABDM Simulated"],
    }
