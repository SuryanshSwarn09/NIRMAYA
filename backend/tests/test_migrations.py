"""Unit and integration tests for Alembic database migrations."""

import os
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect
from alembic import command
from alembic.config import Config


@pytest.fixture
def alembic_config(tmp_path: Path) -> tuple[Config, str, str]:
    """Provide an isolated Alembic Config object pointing to a temporary SQLite database."""
    backend_dir = Path(__file__).parent.parent
    ini_path = backend_dir / "alembic.ini"
    db_file = tmp_path / "test_migration.db"
    db_file_posix = db_file.as_posix()
    async_db_url = f"sqlite+aiosqlite:///{db_file_posix}"
    sync_db_url = f"sqlite:///{db_file_posix}"

    cfg = Config(str(ini_path))
    cfg.attributes["override_url"] = async_db_url
    # Also set environment variable as fallback
    os.environ["ALEMBIC_DATABASE_URL"] = async_db_url

    yield cfg, sync_db_url, async_db_url

    os.environ.pop("ALEMBIC_DATABASE_URL", None)
    if db_file.exists():
        try:
            db_file.unlink()
        except PermissionError:
            pass


def test_migration_revision_head(alembic_config) -> None:
    """Verify Alembic script directory has a valid single head revision."""
    cfg, _, _ = alembic_config
    script = command.ScriptDirectory.from_config(cfg)
    heads = script.get_heads()

    assert len(heads) == 1
    assert heads[0] == "0006_soap_notes_schema"


def test_migration_upgrade_and_downgrade_lifecycle(alembic_config) -> None:
    """Verify that migration upgrade creates all tables and downgrade cleans them."""
    cfg, sync_db_url, _ = alembic_config

    # 1. Run upgrade to head
    command.upgrade(cfg, "head")

    # 2. Inspect created tables
    engine = create_engine(sync_db_url)
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    expected_tables = {
        "user",
        "patient_profile",
        "doctor_profile",
        "diagnostic_lab_facility",
        "doctor_slot",
        "appointment",
        "clinical_condition",
        "clinical_observation",
        "soap_note",
        "alembic_version",
    }
    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"

    # Verify key columns on 'user'
    user_cols = {col["name"] for col in inspector.get_columns("user")}
    assert {"id", "email", "full_name", "role", "is_active", "is_verified"}.issubset(user_cols)

    # Verify key columns on 'patient_profile'
    patient_cols = {col["name"] for col in inspector.get_columns("patient_profile")}
    assert {"id", "user_id", "gender", "blood_group", "abha_number", "abha_address"}.issubset(patient_cols)

    # Verify key columns on 'doctor_profile'
    doctor_cols = {col["name"] for col in inspector.get_columns("doctor_profile")}
    assert {"id", "user_id", "registration_number", "medical_council", "specialty", "hpr_id"}.issubset(doctor_cols)

    # Verify key columns on 'diagnostic_lab_facility'
    lab_cols = {col["name"] for col in inspector.get_columns("diagnostic_lab_facility")}
    assert {"id", "user_id", "facility_name", "license_number", "accreditation", "hfr_id"}.issubset(lab_cols)

    # Verify key columns on 'doctor_slot'
    slot_cols = {col["name"] for col in inspector.get_columns("doctor_slot")}
    assert {
        "id",
        "doctor_id",
        "start_time",
        "end_time",
        "status",
        "is_teleconsult",
        "held_until",
        "held_by_patient_id",
    }.issubset(slot_cols)

    # Verify key columns on 'appointment'
    appt_cols = {col["name"] for col in inspector.get_columns("appointment")}
    assert {"id", "patient_id", "doctor_id", "slot_id", "status", "scheduled_start"}.issubset(appt_cols)

    # Verify key columns on 'clinical_condition'
    condition_cols = {col["name"] for col in inspector.get_columns("clinical_condition")}
    assert {
        "id",
        "patient_id",
        "encounter_id",
        "recorded_by_doctor_id",
        "clinical_status",
        "verification_status",
        "category",
        "code_value",
        "code_display",
    }.issubset(condition_cols)

    # Verify key columns on 'clinical_observation'
    observation_cols = {col["name"] for col in inspector.get_columns("clinical_observation")}
    assert {
        "id",
        "patient_id",
        "encounter_id",
        "performer_doctor_id",
        "status",
        "category",
        "code_value",
        "code_display",
        "effective_date_time",
        "value_quantity",
        "value_unit",
        "components",
        "interpretation",
    }.issubset(observation_cols)

    # Verify key columns on 'soap_note'
    soap_cols = {col["name"] for col in inspector.get_columns("soap_note")}
    assert {
        "id",
        "patient_id",
        "doctor_id",
        "encounter_id",
        "note_type",
        "status",
        "title",
        "chief_complaint",
        "subjective",
        "objective",
        "assessment",
        "plan",
        "primary_diagnosis_code",
        "is_signed",
        "signature_hash",
    }.issubset(soap_cols)

    engine.dispose()

    # 3. Run downgrade to base
    command.downgrade(cfg, "base")

    # 4. Verify tables removed
    engine_after = create_engine(sync_db_url)
    inspector_after = inspect(engine_after)
    remaining_tables = set(inspector_after.get_table_names())
    engine_after.dispose()

    core_tables = {
        "user",
        "patient_profile",
        "doctor_profile",
        "diagnostic_lab_facility",
        "doctor_slot",
        "appointment",
        "clinical_condition",
        "clinical_observation",
        "soap_note",
    }
    assert not core_tables.intersection(remaining_tables), f"Tables not dropped: {core_tables.intersection(remaining_tables)}"

