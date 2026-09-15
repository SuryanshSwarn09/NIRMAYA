"""Database package exporting declarative base, session factories, seeder, and fixtures."""

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.fixtures import (
    ADMIN_FIXTURE,
    DOCTOR_FIXTURES,
    LAB_FIXTURES,
    PATIENT_FIXTURES,
    get_all_fixtures,
)
from app.db.seeder import clear_database, seed_database
from app.db.session import (
    AsyncSessionLocal,
    async_engine,
    check_db_health,
    get_db,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "async_engine",
    "AsyncSessionLocal",
    "get_db",
    "check_db_health",
    "seed_database",
    "clear_database",
    "get_all_fixtures",
    "ADMIN_FIXTURE",
    "PATIENT_FIXTURES",
    "DOCTOR_FIXTURES",
    "LAB_FIXTURES",
]
