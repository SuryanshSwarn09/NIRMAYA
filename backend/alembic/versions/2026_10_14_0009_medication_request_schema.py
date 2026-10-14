"""Electronic prescription and medication request schema migration for NIRMAYA.

Revision ID: 0009_medication_request_schema
Revises: 0008_medication_catalog_schema
Create Date: 2026-10-14 14:00:00.000000

Creates the medication_request table with HL7 FHIR R4 MedicationRequest and ABDM NRCeS aligned fields:
- Subject linkage to patient_profile
- Requester linkage to doctor_profile
- Encounter linkage to appointment
- Catalog drug reference to medication
- Structured dosage instructions and dispense constraints
- Generic substitution permissions and reasons
- Tamper-evident cryptographic SHA-256 digital signature digest
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0009_medication_request_schema"
down_revision: Union[str, None] = "0008_medication_catalog_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medication_request",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("doctor_id", sa.String(length=36), nullable=True),
        sa.Column("encounter_id", sa.String(length=36), nullable=True),
        sa.Column("medication_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("intent", sa.String(length=50), nullable=False, server_default="order"),
        sa.Column("priority", sa.String(length=50), nullable=False, server_default="routine"),
        sa.Column("dosage_text", sa.String(length=500), nullable=False),
        sa.Column("dose_quantity", sa.Float(), nullable=True),
        sa.Column("dose_unit", sa.String(length=50), nullable=True),
        sa.Column("route", sa.String(length=50), nullable=True),
        sa.Column("frequency", sa.Integer(), nullable=True),
        sa.Column("period", sa.Float(), nullable=True),
        sa.Column("period_unit", sa.String(length=20), nullable=True, server_default="d"),
        sa.Column("as_needed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("as_needed_reason", sa.String(length=255), nullable=True),
        sa.Column("additional_instructions", sa.Text(), nullable=True),
        sa.Column("dispense_quantity", sa.Float(), nullable=True),
        sa.Column("dispense_unit", sa.String(length=50), nullable=True),
        sa.Column("expected_supply_duration_days", sa.Integer(), nullable=True),
        sa.Column("number_of_repeats_allowed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("validity_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validity_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("allow_generic_substitution", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("substitution_reason", sa.String(length=255), nullable=True),
        sa.Column("reason_code", sa.String(length=50), nullable=True),
        sa.Column("reason_reference_id", sa.String(length=36), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("authored_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_signed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signature_hash", sa.String(length=128), nullable=True),
        sa.Column("cancellation_reason", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profile.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profile.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["encounter_id"], ["appointment.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["medication_id"], ["medication.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reason_reference_id"], ["clinical_condition.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_medication_request_patient_id", "medication_request", ["patient_id"], unique=False)
    op.create_index("ix_medication_request_doctor_id", "medication_request", ["doctor_id"], unique=False)
    op.create_index("ix_medication_request_encounter_id", "medication_request", ["encounter_id"], unique=False)
    op.create_index("ix_medication_request_medication_id", "medication_request", ["medication_id"], unique=False)
    op.create_index("ix_medication_request_status", "medication_request", ["status"], unique=False)
    op.create_index("ix_medication_request_is_signed", "medication_request", ["is_signed"], unique=False)
    op.create_index("ix_medication_request_reason_code", "medication_request", ["reason_code"], unique=False)
    op.create_index("ix_medication_request_reason_reference_id", "medication_request", ["reason_reference_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_medication_request_reason_reference_id", table_name="medication_request")
    op.drop_index("ix_medication_request_reason_code", table_name="medication_request")
    op.drop_index("ix_medication_request_is_signed", table_name="medication_request")
    op.drop_index("ix_medication_request_status", table_name="medication_request")
    op.drop_index("ix_medication_request_medication_id", table_name="medication_request")
    op.drop_index("ix_medication_request_encounter_id", table_name="medication_request")
    op.drop_index("ix_medication_request_doctor_id", table_name="medication_request")
    op.drop_index("ix_medication_request_patient_id", table_name="medication_request")
    op.drop_table("medication_request")
