"""Initial core relational schema migration for NIRMAYA.

Revision ID: 0001_initial_core_schema
Revises: None
Create Date: 2026-09-16 00:15:00.000000

Creates the foundational clinical and authorization entities:
- user: Core authentication identity, role, and Supabase UID mapping
- patient_profile: Patient demographics, residential address, and ABDM ABHA identifiers
- doctor_profile: Clinical qualifications, licensing, fees, and ABDM HPR identifier
- diagnostic_lab_facility: Lab credentials, accreditations, contacts, and ABDM HFR identifier
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_core_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------------
    # 1. User Table
    # ------------------------------------------------------------------------
    op.create_table(
        "user",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("supabase_uid", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_index(op.f("ix_user_phone_number"), "user", ["phone_number"], unique=False)
    op.create_index(op.f("ix_user_role"), "user", ["role"], unique=False)
    op.create_index(op.f("ix_user_supabase_uid"), "user", ["supabase_uid"], unique=True)

    # ------------------------------------------------------------------------
    # 2. PatientProfile Table
    # ------------------------------------------------------------------------
    op.create_table(
        "patient_profile",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=False),
        sa.Column("blood_group", sa.String(length=20), nullable=False),
        sa.Column("address_line", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("pincode", sa.String(length=10), nullable=True),
        sa.Column("emergency_contact_name", sa.String(length=100), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(length=20), nullable=True),
        sa.Column("emergency_contact_relation", sa.String(length=50), nullable=True),
        sa.Column("abha_number", sa.String(length=17), nullable=True),
        sa.Column("abha_address", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patient_profile_user_id"), "patient_profile", ["user_id"], unique=True)
    op.create_index(op.f("ix_patient_profile_city"), "patient_profile", ["city"], unique=False)
    op.create_index(op.f("ix_patient_profile_abha_number"), "patient_profile", ["abha_number"], unique=True)
    op.create_index(op.f("ix_patient_profile_abha_address"), "patient_profile", ["abha_address"], unique=True)

    # ------------------------------------------------------------------------
    # 3. DoctorProfile Table
    # ------------------------------------------------------------------------
    op.create_table(
        "doctor_profile",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("registration_number", sa.String(length=50), nullable=False),
        sa.Column("medical_council", sa.String(length=100), nullable=False),
        sa.Column("specialty", sa.String(length=50), nullable=False),
        sa.Column("qualifications", sa.String(length=255), nullable=False),
        sa.Column("experience_years", sa.Integer(), nullable=False),
        sa.Column("consultation_fee", sa.Integer(), nullable=False),
        sa.Column("hospital_affiliation", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_available_for_teleconsult", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("hpr_id", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_doctor_profile_user_id"), "doctor_profile", ["user_id"], unique=True)
    op.create_index(op.f("ix_doctor_profile_registration_number"), "doctor_profile", ["registration_number"], unique=True)
    op.create_index(op.f("ix_doctor_profile_specialty"), "doctor_profile", ["specialty"], unique=False)
    op.create_index(op.f("ix_doctor_profile_hpr_id"), "doctor_profile", ["hpr_id"], unique=True)

    # ------------------------------------------------------------------------
    # 4. DiagnosticLabFacility Table
    # ------------------------------------------------------------------------
    op.create_table(
        "diagnostic_lab_facility",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("facility_name", sa.String(length=255), nullable=False),
        sa.Column("license_number", sa.String(length=100), nullable=False),
        sa.Column("accreditation", sa.String(length=50), nullable=False),
        sa.Column("accreditation_number", sa.String(length=100), nullable=True),
        sa.Column("is_nabl_certified", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("contact_person", sa.String(length=150), nullable=False),
        sa.Column("contact_phone", sa.String(length=20), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("address_line", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("pincode", sa.String(length=10), nullable=False),
        sa.Column("supported_tests", sa.Text(), nullable=True),
        sa.Column("hfr_id", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_diagnostic_lab_facility_user_id"), "diagnostic_lab_facility", ["user_id"], unique=True)
    op.create_index(op.f("ix_diagnostic_lab_facility_facility_name"), "diagnostic_lab_facility", ["facility_name"], unique=False)
    op.create_index(op.f("ix_diagnostic_lab_facility_license_number"), "diagnostic_lab_facility", ["license_number"], unique=True)
    op.create_index(op.f("ix_diagnostic_lab_facility_city"), "diagnostic_lab_facility", ["city"], unique=False)
    op.create_index(op.f("ix_diagnostic_lab_facility_hfr_id"), "diagnostic_lab_facility", ["hfr_id"], unique=True)


def downgrade() -> None:
    # Drop diagnostic_lab_facility
    op.drop_index(op.f("ix_diagnostic_lab_facility_hfr_id"), table_name="diagnostic_lab_facility")
    op.drop_index(op.f("ix_diagnostic_lab_facility_city"), table_name="diagnostic_lab_facility")
    op.drop_index(op.f("ix_diagnostic_lab_facility_license_number"), table_name="diagnostic_lab_facility")
    op.drop_index(op.f("ix_diagnostic_lab_facility_facility_name"), table_name="diagnostic_lab_facility")
    op.drop_index(op.f("ix_diagnostic_lab_facility_user_id"), table_name="diagnostic_lab_facility")
    op.drop_table("diagnostic_lab_facility")

    # Drop doctor_profile
    op.drop_index(op.f("ix_doctor_profile_hpr_id"), table_name="doctor_profile")
    op.drop_index(op.f("ix_doctor_profile_specialty"), table_name="doctor_profile")
    op.drop_index(op.f("ix_doctor_profile_registration_number"), table_name="doctor_profile")
    op.drop_index(op.f("ix_doctor_profile_user_id"), table_name="doctor_profile")
    op.drop_table("doctor_profile")

    # Drop patient_profile
    op.drop_index(op.f("ix_patient_profile_abha_address"), table_name="patient_profile")
    op.drop_index(op.f("ix_patient_profile_abha_number"), table_name="patient_profile")
    op.drop_index(op.f("ix_patient_profile_city"), table_name="patient_profile")
    op.drop_index(op.f("ix_patient_profile_user_id"), table_name="patient_profile")
    op.drop_table("patient_profile")

    # Drop user
    op.drop_index(op.f("ix_user_supabase_uid"), table_name="user")
    op.drop_index(op.f("ix_user_role"), table_name="user")
    op.drop_index(op.f("ix_user_phone_number"), table_name="user")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
