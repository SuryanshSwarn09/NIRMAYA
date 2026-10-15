"""Pharmacy medication dispense and fulfillment schema migration for NIRMAYA.

Revision ID: 0010_medication_dispense_schema
Revises: 0009_medication_request_schema
Create Date: 2026-10-15 12:00:00.000000

Creates the medication_dispense table with HL7 FHIR Release 4 MedicationDispense aligned fields:
- Authorizing prescription foreign key linkage to medication_request
- Patient subject linkage to patient_profile
- Catalog drug reference to medication
- Dispensing practitioner linkage to user (pharmacist)
- Fulfillment lifecycle status (preparation, in-progress, completed, etc.)
- Dispense quantity, units, and estimated days supply
- Pharmaceutical lot/batch tracking and drug expiration dates
- When prepared and when handed over timestamps
- Generic substitution tracking, substitution type, and clinical rationale
- Patient dosage instructions and dispenser notes
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0010_medication_dispense_schema"
down_revision: Union[str, None] = "0009_medication_request_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medication_dispense",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dispense_number", sa.String(length=64), nullable=False),
        sa.Column("prescription_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("medication_id", sa.String(length=36), nullable=False),
        sa.Column("dispenser_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="completed"),
        sa.Column("status_reason", sa.String(length=255), nullable=True),
        sa.Column("quantity_dispensed", sa.Float(), nullable=False),
        sa.Column("dispense_unit", sa.String(length=50), nullable=False, server_default="units"),
        sa.Column("days_supply", sa.Integer(), nullable=True),
        sa.Column("lot_number", sa.String(length=100), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("when_prepared", sa.DateTime(timezone=True), nullable=True),
        sa.Column("when_handed_over", sa.DateTime(timezone=True), nullable=True),
        sa.Column("was_substituted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("substitution_type", sa.String(length=50), nullable=True),
        sa.Column("substitution_reason", sa.String(length=255), nullable=True),
        sa.Column("dosage_instruction", sa.String(length=500), nullable=True),
        sa.Column("pharmacist_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["prescription_id"], ["medication_request.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profile.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["medication_id"], ["medication.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["dispenser_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dispense_number"),
    )

    op.create_index("ix_medication_dispense_dispense_number", "medication_dispense", ["dispense_number"], unique=True)
    op.create_index("ix_medication_dispense_prescription_id", "medication_dispense", ["prescription_id"], unique=False)
    op.create_index("ix_medication_dispense_patient_id", "medication_dispense", ["patient_id"], unique=False)
    op.create_index("ix_medication_dispense_medication_id", "medication_dispense", ["medication_id"], unique=False)
    op.create_index("ix_medication_dispense_dispenser_id", "medication_dispense", ["dispenser_id"], unique=False)
    op.create_index("ix_medication_dispense_status", "medication_dispense", ["status"], unique=False)
    op.create_index("ix_medication_dispense_lot_number", "medication_dispense", ["lot_number"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_medication_dispense_lot_number", table_name="medication_dispense")
    op.drop_index("ix_medication_dispense_status", table_name="medication_dispense")
    op.drop_index("ix_medication_dispense_dispenser_id", table_name="medication_dispense")
    op.drop_index("ix_medication_dispense_medication_id", table_name="medication_dispense")
    op.drop_index("ix_medication_dispense_patient_id", table_name="medication_dispense")
    op.drop_index("ix_medication_dispense_prescription_id", table_name="medication_dispense")
    op.drop_index("ix_medication_dispense_dispense_number", table_name="medication_dispense")
    op.drop_table("medication_dispense")
