"""NIRMAYA CLI Database Connectivity and Pre-Flight Diagnostic Validator."""

import asyncio
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.config import settings
from app.db.session import check_db_health


async def main() -> int:
    print("\n" + "=" * 60)
    print("      NIRMAYA Database Diagnostic & Connectivity Probe      ")
    print("=" * 60 + "\n")

    print(f"[Configuration]")
    print(f"  Target URL:        {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print(f"  Sync Migration URL:{settings.sync_database_url.split('@')[-1] if '@' in settings.sync_database_url else settings.sync_database_url}")
    print(f"  Pool Size:         {settings.DATABASE_POOL_SIZE}")
    print(f"  Max Overflow:      {settings.DATABASE_MAX_OVERFLOW}")
    print(f"  Pool Timeout:      {settings.DATABASE_POOL_TIMEOUT}s")
    print(f"  Pool Recycle:      {settings.DATABASE_POOL_RECYCLE}s\n")

    print("[Probe Status]")
    print("  Pinging database connection with 'SELECT 1'...")

    probe = await check_db_health()

    if probe["status"] == "healthy":
        print(f"  [OK] Status:      HEALTHY")
        print(f"  [OK] Latency:     {probe['latency_ms']} ms")
        print(f"  [OK] Dialect:     {probe['database_type']}")
        print("\n[OK] Database connectivity probe SUCCESSFUL!\n")
        return 0
    else:
        print(f"  [!] Status:       UNREACHABLE / DEGRADED")
        print(f"  [!] Latency:      {probe['latency_ms']} ms")
        print(f"  [!] Error:        {probe['error']}")
        print("\n[NOTE] Ensure PostgreSQL service is running or start with Docker:\n")
        print("       docker run --name nirmaya-pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=nirmaya -p 5432:5432 -d postgres:16-alpine\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
