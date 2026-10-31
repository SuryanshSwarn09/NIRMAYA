#!/bin/sh
# =============================================================================
# NIRMAYA Backend - Container Lifecycle & Database Migration Entrypoint
# =============================================================================
set -e

echo "[NIRMAYA-CONTAINER] Initializing NIRMAYA Backend Service..."
echo "[NIRMAYA-CONTAINER] Effective User ID: $(id -u), Group ID: $(id -g)"

# Verify unprivileged execution context
if [ "$(id -u)" -eq 0 ]; then
    echo "[WARNING] Running as root inside container violates CIS Docker Benchmark 4.1."
fi

# Run database schema migrations if enabled
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "[NIRMAYA-CONTAINER] Checking database connection and executing Alembic migrations..."
    if command -v alembic > /dev/null 2>&1; then
        alembic upgrade head || {
            echo "[WARNING] Database migration failed or database unreachable; continuing startup..."
        }
    else
        echo "[INFO] Alembic CLI not found in path; skipping automated migration."
    fi
fi

# Handle default Uvicorn worker concurrency if not overridden
WORKERS="${WEB_CONCURRENCY:-1}"
echo "[NIRMAYA-CONTAINER] Starting application server with WEB_CONCURRENCY=${WORKERS}..."

# Replace shell process with provided command (exec for clean signal propagation)
exec "$@"
