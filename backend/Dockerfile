# =============================================================================
# NIRMAYA Health Interoperability Platform - FastAPI Backend Container
# Multi-Stage Minimal Alpine Dockerfile (OCI / CIS Benchmark Compliant)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build & Dependency Compilation Environment
# -----------------------------------------------------------------------------
FROM python:3.12-alpine AS builder

# Install temporary build toolchain and header dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libpq-dev \
    libffi-dev \
    build-base \
    linux-headers

WORKDIR /build

# Create isolated Python virtual environment for cleanly copyable runtime artifacts
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# -----------------------------------------------------------------------------
# Stage 2: Hardened, Unprivileged Production Runtime Environment
# -----------------------------------------------------------------------------
FROM python:3.12-alpine AS runtime

LABEL maintainer="NIRMAYA Healthcare Project <engineering@nirmaya.gov.in>" \
      org.opencontainers.image.title="NIRMAYA Backend Service" \
      org.opencontainers.image.description="Unified Health Interoperability Network & Longitudinal Vault Backend" \
      org.opencontainers.image.version="0.4.0" \
      org.opencontainers.image.licenses="Apache-2.0"

# Install lightweight runtime dynamic libraries only (no compilers or development headers)
RUN apk add --no-cache \
    libpq \
    libffi \
    curl \
    tzdata \
    ca-certificates

# Enforce CIS Docker Benchmark 4.1: Ensure a non-root user is configured
# Create dedicated unprivileged system group and user: nirmaya (UID 10001, GID 10001)
RUN addgroup -g 10001 -S nirmaya && \
    adduser -u 10001 -S -G nirmaya -h /app -s /sbin/nologin nirmaya

# Copy pre-compiled virtual environment from builder stage
COPY --from=builder --chown=nirmaya:nirmaya /opt/venv /opt/venv

# Configure standard Python container environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    NIRMAYA_CONTAINER=1 \
    NIRMAYA_EXECUTION_MODE="containerized" \
    TZ="Asia/Kolkata"

WORKDIR /app

# Copy application source code with unprivileged ownership
COPY --chown=nirmaya:nirmaya . /app

# Ensure entrypoint script is executable
RUN chmod +x /app/docker-entrypoint.sh

# Configure native OCI Container Health Check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/health || exit 1

# Drop root privileges and execute as unprivileged service user
USER nirmaya:nirmaya

# Expose internal HTTP service port
EXPOSE 8000

# Use production entrypoint lifecycle script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default startup command running Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
