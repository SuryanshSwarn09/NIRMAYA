"""Clinical observation and vital signs telemetry schema migration for NIRMAYA.

Revision ID: 0005_observations_schema
Revises: 0004_conditions_schema
Create Date: 2026-10-05 11:30:00.000000

Creates the clinical_observation table with HL7 FHIR R4 aligned fields:
- id: Primary key UUID string
- patient_id: Foreign key to patient_profile (CASCADE)
- encounter_id: Foreign key to appointment (SET NULL)
- performer_doctor_id: Foreign key to doctor_profile (SET NULL)
- status: registered, preliminary, final, amended, corrected, cancelled, entered-in-error, unknown
- category: vital-signs, laboratory, imaging, exam, therapy, activity, social-history
- code_coding_system: Terminology URI (e.g. LOINC http://loinc.org)
- code_value: Concept/test code (e.g. 8867-4, 85354-9)
- code_display: Human-readable concept name
- effective_date_time, issued_date_time: UTC timestamps of observation
- value_quantity, value_unit, value_system, value_code: Quantitative measurement
- value_string: Qualitative string finding
- components: JSON array for multi-component observations (e.g. Systolic & Diastolic BP)
- reference_range_low, reference_range_high, reference_range_text: Physiological reference limits
- interpretation: normal, high, low, critically-high, critically-low, abnormal
- body_site, method, note: Clinical context and diagnostic notes
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005_observations_schema"
down_revision: Union[str, None] = "0004_conditions_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------------
    # Clinical Observation Table
    # ------------------------------------------------------------------------
    op.create_table(
        "clinical_observation",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("encounter_id", sa.String(length=36), nullable=True),
        sa.Column("performer_doctor_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="final"),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="vital-signs"),
        sa.Column("code_coding_system", sa.String(length=255), nullable=False, server_default="http://loinc.org"),
        sa.Column("code_value", sa.String(length=50), nullable=False),
        sa.Column("code_display", sa.String(length=255), nullable=False),
        sa.Column("effective_date_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issued_date_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value_quantity", sa.Float(), nullable=True),
        sa.Column("value_unit", sa.String(length=50), nullable=True),
        sa.Column("value_system", sa.String(length=255), nullable=True, server_default="http://unitsofmeasure.org"),
        sa.Column("value_code", sa.String(length=50), nullable=True),
        sa.Column("value_string", sa.Text(), nullable=True),
        sa.Column("components", sa.JSON(), nullable=True),
        sa.Column("reference_range_low", sa.Float(), nullable=True),
        sa.Column("reference_range_high", sa.Float(), nullable=True),
        sa.Column("reference_range_text", sa.String(length=100), nullable=True),
        sa.Column("interpretation", sa.String(length=30), nullable=True),
        sa.Column("body_site", sa.String(length=255), nullable=True),
        sa.Column("method", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient_profile.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["appointment.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["performer_doctor_id"],
            ["doctor_profile.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinical_observation_id"), "clinical_observation", ["id"], unique=False)
    op.create_index(op.f("ix_clinical_observation_patient_id"), "clinical_observation", ["patient_id"], unique=False)
    op.create_index(op.f("ix_clinical_observation_encounter_id"), "clinical_observation", ["encounter_id"], unique=False)
    op.create_index(op.f("ix_clinical_observation_performer_doctor_id"), "clinical_observation", ["performer_doctor_id"], unique=False)
    op.create_index(op.f("ix_clinical_observation_status"), "clinical_observation", ["status"], unique=False)
    op.create_index(op.f("ix_clinical_observation_category"), "clinical_observation", ["category"], unique=False)
    op.create_index(op.f("ix_clinical_observation_code_value"), "clinical_observation", ["code_value"], unique=False)
    op.create_index(op.f("ix_clinical_observation_effective_date_time"), "clinical_observation", ["effective_date_time"], unique=False)
    op.create_index(op.f("ix_clinical_observation_interpretation"), "clinical_observation", ["interpretation"], unique=False)
    op.create_index(op.f("ix_clinical_observation_created_at"), "clinical_observation", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_observation_created_at"), table_name="clinical_observation")
    op.drop_index(op.f("ix_clinical_observation_interpretation"), table_name="clinical_observation")
    op.drop_index(op.f("ix_clinical_observation_effective_date_time"), table_name="clinical_observation")
    op.drop_index(op.f("ix_clinical_observation_code_value"), table_name="clinical_observation")
    op.drop_index(op.f("ix_clinical_observation_category"), table_name="clinical_observation")
    op.drop_index(op.f("ix_clinical_observation_status"), table_name="clinical_observation")
    op.drop_index(op.f("ix_clinical_observation_performer_doctor_id"), table_name="clinical_observation")
    op.drop_index(op.f("ix_clinical_observation_encounter_id"), table_name="clinical_observation")
    op.drop_index(op.f("ix_clinical_observation_patient_id"), table_name="clinical_observation")
    op.drop_index(op.f("ix_clinical_observation_id"), table_name="clinical_observation")
    op.drop_table("clinical_observation")
