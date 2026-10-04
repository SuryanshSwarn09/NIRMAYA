"""Clinical condition and problem list schema migration for NIRMAYA.

Revision ID: 0004_conditions_schema
Revises: 0003_slot_concurrency_and_hold_fields
Create Date: 2026-10-05 10:00:00.000000

Creates the clinical_condition table with longitudinal health tracking:
- id: Primary key UUID string
- patient_id: Foreign key to patient_profile (CASCADE)
- encounter_id: Foreign key to appointment (SET NULL)
- recorded_by_doctor_id: Foreign key to doctor_profile (SET NULL)
- clinical_status: active, recurrence, relapse, inactive, remission, resolved
- verification_status: unconfirmed, provisional, differential, confirmed, refuted, entered-in-error
- category: problem-list-item, encounter-diagnosis, chronic-condition
- severity: mild, moderate, severe
- code_coding_system: SNOMED-CT or ICD-10 URI
- code_value: Concept code
- code_display: Human-readable concept name
- body_site: Anatomical site
- onset_date_time, abatement_date_time, recorded_date: UTC timeline
- note: Free-text clinical notes
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_conditions_schema"
down_revision: Union[str, None] = "0003_slot_concurrency_and_hold_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------------
    # Clinical Condition Table
    # ------------------------------------------------------------------------
    op.create_table(
        "clinical_condition",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("encounter_id", sa.String(length=36), nullable=True),
        sa.Column("recorded_by_doctor_id", sa.String(length=36), nullable=True),
        sa.Column("clinical_status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="confirmed"),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="problem-list-item"),
        sa.Column("severity", sa.String(length=30), nullable=True),
        sa.Column("code_coding_system", sa.String(length=255), nullable=False, server_default="http://snomed.info/sct"),
        sa.Column("code_value", sa.String(length=50), nullable=False),
        sa.Column("code_display", sa.String(length=255), nullable=False),
        sa.Column("body_site", sa.String(length=255), nullable=True),
        sa.Column("onset_date_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("abatement_date_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_date", sa.DateTime(timezone=True), nullable=False),
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
            ["recorded_by_doctor_id"],
            ["doctor_profile.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinical_condition_id"), "clinical_condition", ["id"], unique=False)
    op.create_index(op.f("ix_clinical_condition_patient_id"), "clinical_condition", ["patient_id"], unique=False)
    op.create_index(op.f("ix_clinical_condition_encounter_id"), "clinical_condition", ["encounter_id"], unique=False)
    op.create_index(op.f("ix_clinical_condition_recorded_by_doctor_id"), "clinical_condition", ["recorded_by_doctor_id"], unique=False)
    op.create_index(op.f("ix_clinical_condition_clinical_status"), "clinical_condition", ["clinical_status"], unique=False)
    op.create_index(op.f("ix_clinical_condition_verification_status"), "clinical_condition", ["verification_status"], unique=False)
    op.create_index(op.f("ix_clinical_condition_category"), "clinical_condition", ["category"], unique=False)
    op.create_index(op.f("ix_clinical_condition_severity"), "clinical_condition", ["severity"], unique=False)
    op.create_index(op.f("ix_clinical_condition_code_value"), "clinical_condition", ["code_value"], unique=False)
    op.create_index(op.f("ix_clinical_condition_created_at"), "clinical_condition", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_condition_created_at"), table_name="clinical_condition")
    op.drop_index(op.f("ix_clinical_condition_code_value"), table_name="clinical_condition")
    op.drop_index(op.f("ix_clinical_condition_severity"), table_name="clinical_condition")
    op.drop_index(op.f("ix_clinical_condition_category"), table_name="clinical_condition")
    op.drop_index(op.f("ix_clinical_condition_verification_status"), table_name="clinical_condition")
    op.drop_index(op.f("ix_clinical_condition_clinical_status"), table_name="clinical_condition")
    op.drop_index(op.f("ix_clinical_condition_recorded_by_doctor_id"), table_name="clinical_condition")
    op.drop_index(op.f("ix_clinical_condition_encounter_id"), table_name="clinical_condition")
    op.drop_index(op.f("ix_clinical_condition_patient_id"), table_name="clinical_condition")
    op.drop_index(op.f("ix_clinical_condition_id"), table_name="clinical_condition")
    op.drop_table("clinical_condition")
