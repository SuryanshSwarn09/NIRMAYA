"""Diagnostic service requests and diagnostic reports schema migration for NIRMAYA.

Revision ID: 0007_diagnostics_schema
Revises: 0006_soap_notes_schema
Create Date: 2026-10-07 14:45:00.000000

Creates the diagnostic_order and diagnostic_report tables with HL7 FHIR R4 ServiceRequest
and DiagnosticReport aligned fields:
- diagnostic_order: Requisition orders for laboratory and diagnostic imaging panels (LOINC)
- diagnostic_report: Pathologist-verified result documents with conclusion and abnormal flags
- clinical_observation: Adds report_id foreign key linking observations to parent diagnostic reports
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0007_diagnostics_schema"
down_revision: Union[str, None] = "0006_soap_notes_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------------
    # 1. Diagnostic Order Table (FHIR ServiceRequest)
    # ------------------------------------------------------------------------
    op.create_table(
        "diagnostic_order",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("doctor_id", sa.String(length=36), nullable=True),
        sa.Column("encounter_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("intent", sa.String(length=50), nullable=False, server_default="order"),
        sa.Column("priority", sa.String(length=50), nullable=False, server_default="routine"),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="laboratory"),
        sa.Column("code_coding_system", sa.String(length=100), nullable=False, server_default="http://loinc.org"),
        sa.Column("code_value", sa.String(length=50), nullable=False),
        sa.Column("code_display", sa.String(length=255), nullable=False),
        sa.Column("reason_code", sa.String(length=50), nullable=True),
        sa.Column("reason_description", sa.String(length=500), nullable=True),
        sa.Column("specimen_type", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient_profile.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["doctor_id"],
            ["doctor_profile.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["appointment.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_diagnostic_order_id"), "diagnostic_order", ["id"], unique=False)
    op.create_index(op.f("ix_diagnostic_order_patient_id"), "diagnostic_order", ["patient_id"], unique=False)
    op.create_index(op.f("ix_diagnostic_order_doctor_id"), "diagnostic_order", ["doctor_id"], unique=False)
    op.create_index(op.f("ix_diagnostic_order_encounter_id"), "diagnostic_order", ["encounter_id"], unique=False)
    op.create_index(op.f("ix_diagnostic_order_status"), "diagnostic_order", ["status"], unique=False)
    op.create_index(op.f("ix_diagnostic_order_priority"), "diagnostic_order", ["priority"], unique=False)
    op.create_index(op.f("ix_diagnostic_order_category"), "diagnostic_order", ["category"], unique=False)
    op.create_index(op.f("ix_diagnostic_order_code_value"), "diagnostic_order", ["code_value"], unique=False)
    op.create_index(op.f("ix_diagnostic_order_created_at"), "diagnostic_order", ["created_at"], unique=False)

    # ------------------------------------------------------------------------
    # 2. Diagnostic Report Table (FHIR DiagnosticReport)
    # ------------------------------------------------------------------------
    op.create_table(
        "diagnostic_report",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=True),
        sa.Column("encounter_id", sa.String(length=36), nullable=True),
        sa.Column("performer_id", sa.String(length=36), nullable=True),
        sa.Column("performer_name", sa.String(length=255), nullable=True, server_default="Metropolis Diagnostics & Pathology Lab"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="final"),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="LAB"),
        sa.Column("code_coding_system", sa.String(length=100), nullable=False, server_default="http://loinc.org"),
        sa.Column("code_value", sa.String(length=50), nullable=False),
        sa.Column("code_display", sa.String(length=255), nullable=False),
        sa.Column("effective_date_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issued_date_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("conclusion", sa.Text(), nullable=True),
        sa.Column("conclusion_code", sa.String(length=50), nullable=True),
        sa.Column("is_abnormal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("report_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient_profile.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["diagnostic_order.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["appointment.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["performer_id"],
            ["doctor_profile.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_diagnostic_report_id"), "diagnostic_report", ["id"], unique=False)
    op.create_index(op.f("ix_diagnostic_report_patient_id"), "diagnostic_report", ["patient_id"], unique=False)
    op.create_index(op.f("ix_diagnostic_report_order_id"), "diagnostic_report", ["order_id"], unique=False)
    op.create_index(op.f("ix_diagnostic_report_encounter_id"), "diagnostic_report", ["encounter_id"], unique=False)
    op.create_index(op.f("ix_diagnostic_report_performer_id"), "diagnostic_report", ["performer_id"], unique=False)
    op.create_index(op.f("ix_diagnostic_report_status"), "diagnostic_report", ["status"], unique=False)
    op.create_index(op.f("ix_diagnostic_report_category"), "diagnostic_report", ["category"], unique=False)
    op.create_index(op.f("ix_diagnostic_report_code_value"), "diagnostic_report", ["code_value"], unique=False)
    op.create_index(op.f("ix_diagnostic_report_is_abnormal"), "diagnostic_report", ["is_abnormal"], unique=False)
    op.create_index(op.f("ix_diagnostic_report_created_at"), "diagnostic_report", ["created_at"], unique=False)

    # ------------------------------------------------------------------------
    # 3. Clinical Observation Table: Add report_id FK (Batch Mode)
    # ------------------------------------------------------------------------
    with op.batch_alter_table("clinical_observation") as batch_op:
        batch_op.add_column(sa.Column("report_id", sa.String(length=36), nullable=True))
        batch_op.create_index(batch_op.f("ix_clinical_observation_report_id"), ["report_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_clinical_observation_report_id",
            "diagnostic_report",
            ["report_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    # ------------------------------------------------------------------------
    # 3. Clinical Observation Table: Drop report_id FK (Batch Mode)
    # ------------------------------------------------------------------------
    with op.batch_alter_table("clinical_observation") as batch_op:
        batch_op.drop_constraint("fk_clinical_observation_report_id", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_clinical_observation_report_id"))
        batch_op.drop_column("report_id")

    # ------------------------------------------------------------------------
    # 2. Drop Diagnostic Report Table
    # ------------------------------------------------------------------------
    op.drop_index(op.f("ix_diagnostic_report_created_at"), table_name="diagnostic_report")
    op.drop_index(op.f("ix_diagnostic_report_is_abnormal"), table_name="diagnostic_report")
    op.drop_index(op.f("ix_diagnostic_report_code_value"), table_name="diagnostic_report")
    op.drop_index(op.f("ix_diagnostic_report_category"), table_name="diagnostic_report")
    op.drop_index(op.f("ix_diagnostic_report_status"), table_name="diagnostic_report")
    op.drop_index(op.f("ix_diagnostic_report_performer_id"), table_name="diagnostic_report")
    op.drop_index(op.f("ix_diagnostic_report_encounter_id"), table_name="diagnostic_report")
    op.drop_index(op.f("ix_diagnostic_report_order_id"), table_name="diagnostic_report")
    op.drop_index(op.f("ix_diagnostic_report_patient_id"), table_name="diagnostic_report")
    op.drop_index(op.f("ix_diagnostic_report_id"), table_name="diagnostic_report")
    op.drop_table("diagnostic_report")

    # ------------------------------------------------------------------------
    # 1. Drop Diagnostic Order Table
    # ------------------------------------------------------------------------
    op.drop_index(op.f("ix_diagnostic_order_created_at"), table_name="diagnostic_order")
    op.drop_index(op.f("ix_diagnostic_order_code_value"), table_name="diagnostic_order")
    op.drop_index(op.f("ix_diagnostic_order_category"), table_name="diagnostic_order")
    op.drop_index(op.f("ix_diagnostic_order_priority"), table_name="diagnostic_order")
    op.drop_index(op.f("ix_diagnostic_order_status"), table_name="diagnostic_order")
    op.drop_index(op.f("ix_diagnostic_order_encounter_id"), table_name="diagnostic_order")
    op.drop_index(op.f("ix_diagnostic_order_doctor_id"), table_name="diagnostic_order")
    op.drop_index(op.f("ix_diagnostic_order_patient_id"), table_name="diagnostic_order")
    op.drop_index(op.f("ix_diagnostic_order_id"), table_name="diagnostic_order")
    op.drop_table("diagnostic_order")
