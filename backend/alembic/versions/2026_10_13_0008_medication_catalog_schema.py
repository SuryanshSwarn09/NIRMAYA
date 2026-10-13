"""Medication catalog and formulary engine schema migration for NIRMAYA.

Revision ID: 0008_medication_catalog_schema
Revises: 0007_diagnostics_schema
Create Date: 2026-10-13 13:15:00.000000

Creates the medication table with HL7 FHIR R4 Medication and ABDM NRCeS aligned fields:
- RxNorm Concept Unique Identifier (RxCUI)
- WHO-ATC therapeutic classification
- SNOMED-CT dose form and administration route
- Healthcare insurance formulary tier and status
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0008_medication_catalog_schema"
down_revision: Union[str, None] = "0007_diagnostics_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medication",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("generic_name", sa.String(length=255), nullable=False),
        sa.Column("brand_name", sa.String(length=255), nullable=True),
        sa.Column("rxnorm_code", sa.String(length=64), nullable=False),
        sa.Column("rxnorm_display", sa.String(length=255), nullable=True),
        sa.Column("atc_code", sa.String(length=32), nullable=True),
        sa.Column("atc_display", sa.String(length=255), nullable=True),
        sa.Column("snomed_code", sa.String(length=64), nullable=True),
        sa.Column("snomed_display", sa.String(length=255), nullable=True),
        sa.Column("form", sa.String(length=50), nullable=False, server_default="tablet"),
        sa.Column("route", sa.String(length=50), nullable=False, server_default="oral"),
        sa.Column("strength", sa.String(length=64), nullable=False),
        sa.Column("active_ingredient", sa.String(length=255), nullable=False),
        sa.Column("is_prescription_required", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_controlled_substance", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("formulary_tier", sa.String(length=50), nullable=False, server_default="tier_1_generic"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("contraindications_summary", sa.Text(), nullable=True),
        sa.Column("storage_instructions", sa.String(length=255), nullable=True),
        sa.Column("package_info", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_medication_name", "medication", ["name"], unique=False)
    op.create_index("ix_medication_generic_name", "medication", ["generic_name"], unique=False)
    op.create_index("ix_medication_brand_name", "medication", ["brand_name"], unique=False)
    op.create_index("ix_medication_rxnorm_code", "medication", ["rxnorm_code"], unique=False)
    op.create_index("ix_medication_atc_code", "medication", ["atc_code"], unique=False)
    op.create_index("ix_medication_snomed_code", "medication", ["snomed_code"], unique=False)
    op.create_index("ix_medication_form", "medication", ["form"], unique=False)
    op.create_index("ix_medication_route", "medication", ["route"], unique=False)
    op.create_index("ix_medication_active_ingredient", "medication", ["active_ingredient"], unique=False)
    op.create_index("ix_medication_formulary_tier", "medication", ["formulary_tier"], unique=False)
    op.create_index("ix_medication_status", "medication", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_medication_status", table_name="medication")
    op.drop_index("ix_medication_formulary_tier", table_name="medication")
    op.drop_index("ix_medication_active_ingredient", table_name="medication")
    op.drop_index("ix_medication_route", table_name="medication")
    op.drop_index("ix_medication_form", table_name="medication")
    op.drop_index("ix_medication_snomed_code", table_name="medication")
    op.drop_index("ix_medication_atc_code", table_name="medication")
    op.drop_index("ix_medication_rxnorm_code", table_name="medication")
    op.drop_index("ix_medication_brand_name", table_name="medication")
    op.drop_index("ix_medication_generic_name", table_name="medication")
    op.drop_index("ix_medication_name", table_name="medication")
    op.drop_table("medication")
