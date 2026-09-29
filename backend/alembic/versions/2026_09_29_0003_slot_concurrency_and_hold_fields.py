"""Slot concurrency and hold tracking schema migration for NIRMAYA.

Revision ID: 0003_slot_concurrency_and_hold_fields
Revises: 0002_appointments_and_slots_schema
Create Date: 2026-09-29 17:25:00.000000

Adds concurrency control and Cal.com-style temporary hold attributes to doctor_slot:
- held_until: UTC expiration timestamp for active reservation holds
- held_by_patient_id: Foreign key to patient_profile holding the slot
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_slot_concurrency_and_hold_fields"
down_revision: Union[str, None] = "0002_appointments_and_slots_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------------
    # Add held_until and held_by_patient_id to doctor_slot
    # ------------------------------------------------------------------------
    with op.batch_alter_table("doctor_slot") as batch_op:
        batch_op.add_column(
            sa.Column("held_until", sa.DateTime(timezone=True), nullable=True),
        )
        batch_op.add_column(
            sa.Column("held_by_patient_id", sa.String(length=36), nullable=True),
        )
        batch_op.create_index(
            batch_op.f("ix_doctor_slot_held_until"),
            ["held_until"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_doctor_slot_held_by_patient_id"),
            ["held_by_patient_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_doctor_slot_held_by_patient",
            "patient_profile",
            ["held_by_patient_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    # ------------------------------------------------------------------------
    # Drop foreign key, indexes, and columns
    # ------------------------------------------------------------------------
    with op.batch_alter_table("doctor_slot") as batch_op:
        batch_op.drop_constraint("fk_doctor_slot_held_by_patient", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_doctor_slot_held_by_patient_id"))
        batch_op.drop_index(batch_op.f("ix_doctor_slot_held_until"))
        batch_op.drop_column("held_by_patient_id")
        batch_op.drop_column("held_until")
