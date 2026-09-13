"""Unit test suite for SQLAlchemy 2.0 declarative base and audit mixins."""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MockPatientEncounter(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Test entity for validating declarative naming and mixin capabilities."""

    summary: Mapped[str] = mapped_column(String(255), nullable=False)


class MockClinicalVitalSign(Base, UUIDPrimaryKeyMixin):
    """Test entity without timestamp mixin."""

    vital_name: Mapped[str] = mapped_column(String(100), nullable=False)


def test_declarative_base_tablename_derivation() -> None:
    """Verify PascalCase model names are automatically converted to snake_case."""
    assert MockPatientEncounter.__tablename__ == "mock_patient_encounter"
    assert MockClinicalVitalSign.__tablename__ == "mock_clinical_vital_sign"


def test_uuid_primary_key_mixin_schema() -> None:
    """Verify UUID primary key column definition and default generator."""
    id_col = MockPatientEncounter.__table__.columns["id"]
    assert id_col.primary_key is True
    assert id_col.nullable is False
    assert id_col.type.length == 36

    # Test the default callable generates valid UUID4
    generated_id = id_col.default.arg(None)
    assert generated_id is not None
    parsed = uuid.UUID(generated_id)
    assert parsed.version == 4


def test_timestamp_mixin_schema() -> None:
    """Verify timestamp mixin column definition and UTC default generator."""
    created_col = MockPatientEncounter.__table__.columns["created_at"]
    updated_col = MockPatientEncounter.__table__.columns["updated_at"]

    assert created_col.nullable is False
    assert created_col.index is True
    assert updated_col.nullable is False

    # Test default callable returns UTC datetime
    generated_time = created_col.default.arg(None)
    assert isinstance(generated_time, datetime)
    assert generated_time.tzinfo == timezone.utc


@pytest.mark.asyncio
async def test_entity_persistence_with_mixins() -> None:
    """Verify persisting an entity generates UUID and timestamps in an async database."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    test_sessionmaker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_sessionmaker() as session:
        encounter = MockPatientEncounter(summary="Cardiology Consultation")
        session.add(encounter)
        await session.commit()

        # Query back
        stmt = select(MockPatientEncounter).where(MockPatientEncounter.summary == "Cardiology Consultation")
        result = await session.execute(stmt)
        persisted = result.scalar_one()

        assert persisted.id is not None
        assert uuid.UUID(persisted.id).version == 4
        assert persisted.created_at is not None
        assert isinstance(persisted.created_at, datetime)

    await test_engine.dispose()
