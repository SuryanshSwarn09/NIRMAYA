"""Structured SOAP clinical notes schema migration for NIRMAYA.

Revision ID: 0006_soap_notes_schema
Revises: 0005_observations_schema
Create Date: 2026-10-06 11:45:00.000000

Creates the soap_note table with HL7 FHIR R4 Composition aligned fields:
- id: Primary key UUID string
- patient_id: Foreign key to patient_profile (CASCADE)
- doctor_id: Foreign key to doctor_profile (SET NULL)
- encounter_id: Foreign key to appointment (SET NULL)
- note_type: soap, consultation, progress-note, discharge-summary
- status: preliminary, final, amended, entered-in-error
- title: Document header string
- chief_complaint: Patient primary complaint / encounter reason
- subjective: Patient history, symptoms, onset (LOINC 61150-9)
- objective: Physical exam and observations (LOINC 61149-1)
- assessment: Clinical impression and differential diagnoses (LOINC 51848-0)
- plan: Care plan, therapeutics, orders (LOINC 18776-5)
- primary_diagnosis_code, primary_diagnosis_display: ICD-10 / SNOMED-CT diagnosis coding
- follow_up_instructions: Patient discharge and follow-up guidance
- is_signed, signed_at, signature_hash: Digital cryptographic signature verification
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0006_soap_notes_schema"
down_revision: Union[str, None] = "0005_observations_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------------
    # SOAP Clinical Note Table
    # ------------------------------------------------------------------------
    op.create_table(
        "soap_note",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("doctor_id", sa.String(length=36), nullable=True),
        sa.Column("encounter_id", sa.String(length=36), nullable=True),
        sa.Column("note_type", sa.String(length=50), nullable=False, server_default="soap"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="preliminary"),
        sa.Column("title", sa.String(length=255), nullable=False, server_default="Clinical Consultation SOAP Note"),
        sa.Column("chief_complaint", sa.String(length=500), nullable=False),
        sa.Column("subjective", sa.Text(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("assessment", sa.Text(), nullable=False),
        sa.Column("plan", sa.Text(), nullable=False),
        sa.Column("primary_diagnosis_code", sa.String(length=50), nullable=True),
        sa.Column("primary_diagnosis_display", sa.String(length=255), nullable=True),
        sa.Column("follow_up_instructions", sa.Text(), nullable=True),
        sa.Column("is_signed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signature_hash", sa.String(length=128), nullable=True),
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
    op.create_index(op.f("ix_soap_note_id"), "soap_note", ["id"], unique=False)
    op.create_index(op.f("ix_soap_note_patient_id"), "soap_note", ["patient_id"], unique=False)
    op.create_index(op.f("ix_soap_note_doctor_id"), "soap_note", ["doctor_id"], unique=False)
    op.create_index(op.f("ix_soap_note_encounter_id"), "soap_note", ["encounter_id"], unique=False)
    op.create_index(op.f("ix_soap_note_note_type"), "soap_note", ["note_type"], unique=False)
    op.create_index(op.f("ix_soap_note_status"), "soap_note", ["status"], unique=False)
    op.create_index(op.f("ix_soap_note_is_signed"), "soap_note", ["is_signed"], unique=False)
    op.create_index(op.f("ix_soap_note_primary_diagnosis_code"), "soap_note", ["primary_diagnosis_code"], unique=False)
    op.create_index(op.f("ix_soap_note_created_at"), "soap_note", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_soap_note_created_at"), table_name="soap_note")
    op.drop_index(op.f("ix_soap_note_primary_diagnosis_code"), table_name="soap_note")
    op.drop_index(op.f("ix_soap_note_is_signed"), table_name="soap_note")
    op.drop_index(op.f("ix_soap_note_status"), table_name="soap_note")
    op.drop_index(op.f("ix_soap_note_note_type"), table_name="soap_note")
    op.drop_index(op.f("ix_soap_note_encounter_id"), table_name="soap_note")
    op.drop_index(op.f("ix_soap_note_doctor_id"), table_name="soap_note")
    op.drop_index(op.f("ix_soap_note_patient_id"), table_name="soap_note")
    op.drop_index(op.f("ix_soap_note_id"), table_name="soap_note")
    op.drop_table("soap_note")
