#!/usr/bin/env python3
"""NIRMAYA CLI Database Seeder Utility.

Seeds synthetic clinical fixtures (Patients with ABHA, Doctors with HPR,
Diagnostic Labs with HFR, and Admin) into the active database.
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

# Add backend directory to module search path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings
from app.db.seeder import seed_database

# ANSI Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


async def run_seeder(database_url: Optional[str] = None, reset: bool = False, init_tables: bool = False) -> int:
    target_url = database_url or settings.DATABASE_URL

    print(f"\n{BOLD}{CYAN}================================================================{RESET}")
    print(f"{BOLD}{CYAN}          NIRMAYA Database Synthetic Clinical Fixtures Seeder   {RESET}")
    print(f"{BOLD}{CYAN}================================================================{RESET}\n")

    safe_url = target_url.split("@")[-1] if "@" in target_url else target_url
    print(f"[{BOLD}Target Database{RESET}]: {safe_url}")
    print(f"[{BOLD}Reset Mode{RESET}]:      {'ENABLED (Clearing existing data)' if reset else 'Disabled (Idempotent upsert)'}")
    if init_tables:
        print(f"[{BOLD}Init Tables{RESET}]:     ENABLED (Creating tables if missing)")
    print()

    engine = create_async_engine(target_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    try:
        if init_tables:
            from app.db.base import Base
            import app.models  # noqa: F401
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            result = await seed_database(session, reset=reset)

        print(f"[{BOLD}Execution Summary{RESET}]")
        if reset and result.get("cleared_stats"):
            c = result["cleared_stats"]
            print(f"  {YELLOW}Cleared Records{RESET}:")
            print(f"    - Users Deleted:    {c.get('users_deleted', 0)}")
            print(f"    - Patients Deleted: {c.get('patients_deleted', 0)}")
            print(f"    - Doctors Deleted:  {c.get('doctors_deleted', 0)}")
            print(f"    - Labs Deleted:     {c.get('labs_deleted', 0)}")

        print(f"  {GREEN}Seeded Records{RESET}:")
        print(f"    - Users Created:    {result['users_seeded']}")
        print(f"    - Patients Created: {result['patients_seeded']}")
        print(f"    - Doctors Created:  {result['doctors_seeded']}")
        print(f"    - Labs Created:     {result['labs_seeded']}")
        print(f"    - Total Processed:  {result['total_seeded']}")

        print(f"\n{GREEN}{BOLD}[SUCCESS] Database seeding completed successfully!{RESET}\n")
        return 0

    except Exception as exc:
        print(f"\n{RED}{BOLD}[ERROR] Database seeding failed:{RESET} {exc}\n")
        print(f"{YELLOW}Hint: Ensure database is reachable and migrations are applied:{RESET}")
        print("      alembic upgrade head\n")
        return 1

    finally:
        await engine.dispose()


def parse_args():
    parser = argparse.ArgumentParser(description="NIRMAYA Synthetic Clinical Database Seeder")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate existing core entity tables before seeding",
    )
    parser.add_argument(
        "--init-tables",
        action="store_true",
        help="Initialize metadata schema tables before seeding if not already present",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database connection string override (defaults to settings.DATABASE_URL)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exit_code = asyncio.run(run_seeder(database_url=args.db_url, reset=args.reset, init_tables=args.init_tables))
    sys.exit(exit_code)
