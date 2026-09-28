"""Appointments and doctor availability slots schema migration for NIRMAYA.

Revision ID: 0002_appointments_and_slots_schema
Revises: 0001_initial_core_schema
Create Date: 2026-09-28 20:15:00.000000

Creates the clinical encounter and scheduling entities:
- doctor_slot: Doctor availability windows, duration, teleconsultation flag, and conflict prevention
- appointment: Clinical encounter linking patient vault, practitioner doctor, and reserved slot
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_appointments_and_slots_schema"
down_revision: Union[str, None] = "0001_initial_core_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------------
    # 1. Doctor Slot Table
    # ------------------------------------------------------------------------
    op.create_table(
        "doctor_slot",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("doctor_id", sa.String(length=36), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="available"),
        sa.Column("is_teleconsult", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(
            ["doctor_id"],
            ["doctor_profile.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doctor_id", "start_time", name="uq_doctor_slot_start"),
    )
    op.create_index(op.f("ix_doctor_slot_doctor_id"), "doctor_slot", ["doctor_id"], unique=False)
    op.create_index(op.f("ix_doctor_slot_start_time"), "doctor_slot", ["start_time"], unique=False)
    op.create_index(op.f("ix_doctor_slot_status"), "doctor_slot", ["status"], unique=False)

    # ------------------------------------------------------------------------
    # 2. Appointment Table
    # ------------------------------------------------------------------------
    op.create_table(
        "appointment",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("doctor_id", sa.String(length=36), nullable=False),
        sa.Column("slot_id", sa.String(length=36), nullable=True),
        sa.Column("appointment_type", sa.String(length=30), nullable=False, server_default="routine_checkup"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="scheduled"),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("clinical_notes", sa.Text(), nullable=True),
        sa.Column("teleconsultation_url", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient_profile.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["doctor_id"],
            ["doctor_profile.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_id"],
            ["doctor_slot.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slot_id", name="uq_appointment_slot_id"),
    )
    op.create_index(op.f("ix_appointment_patient_id"), "appointment", ["patient_id"], unique=False)
    op.create_index(op.f("ix_appointment_doctor_id"), "appointment", ["doctor_id"], unique=False)
    op.create_index(op.f("ix_appointment_slot_id"), "appointment", ["slot_id"], unique=True)
    op.create_index(op.f("ix_appointment_status"), "appointment", ["status"], unique=False)
    op.create_index(op.f("ix_appointment_scheduled_start"), "appointment", ["scheduled_start"], unique=False)


def downgrade() -> None:
    # ------------------------------------------------------------------------
    # Drop in reverse topological order
    # ------------------------------------------------------------------------
    op.drop_index(op.f("ix_appointment_scheduled_start"), table_name="appointment")
    op.drop_index(op.f("ix_appointment_status"), table_name="appointment")
    op.drop_index(op.f("ix_appointment_slot_id"), table_name="appointment")
    op.drop_index(op.f("ix_appointment_doctor_id"), table_name="appointment")
    op.drop_index(op.f("ix_appointment_patient_id"), table_name="appointment")
    op.drop_table("appointment")

    op.drop_index(op.f("ix_doctor_slot_status"), table_name="doctor_slot")
    op.drop_index(op.f("ix_doctor_slot_start_time"), table_name="doctor_slot")
    op.drop_index(op.f("ix_doctor_slot_doctor_id"), table_name="doctor_slot")
    op.drop_table("doctor_slot")
