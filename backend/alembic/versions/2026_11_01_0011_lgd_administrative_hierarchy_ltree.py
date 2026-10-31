"""Indian Local Government Directory (LGD) 6-Tier Administrative Hierarchy and PostgreSQL ltree migration.

Revision ID: 0011_lgd_administrative_hierarchy_ltree
Revises: 0010_medication_dispense_schema
Create Date: 2026-11-01 00:00:00.000000

Creates the sovereign administrative governance tables:
- administrative_units: 6-tier territorial governance (Country -> State -> Division -> District -> Sub-District)
  indexed with PostgreSQL ltree GIST for sub-2ms hierarchical ancestor and descendant queries.
- administrative_officers: Appointed administrative health officers with territorial jurisdiction scopes
  and official government credential metadata.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0011_lgd_administrative_hierarchy_ltree"
down_revision: Union[str, None] = "0010_medication_dispense_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Enable native ltree extension on PostgreSQL for sub-2ms GIST indexing
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS ltree;")

    # 1. Create administrative_units table
    op.create_table(
        "administrative_units",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("unit_level", sa.String(length=50), nullable=False),
        sa.Column("lgd_code", sa.String(length=20), nullable=True),
        sa.Column("path", sa.Text() if is_postgres else sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("pincode_prefixes", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true" if is_postgres else "1")),
        sa.ForeignKeyConstraint(["parent_id"], ["administrative_units.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lgd_code", name="uq_administrative_units_lgd_code"),
    )

    op.create_index("idx_admin_units_name", "administrative_units", ["name"])
    op.create_index("idx_admin_units_level", "administrative_units", ["unit_level"])
    op.create_index("idx_admin_units_parent_id", "administrative_units", ["parent_id"])
    op.create_index("idx_admin_units_path", "administrative_units", ["path"])

    if is_postgres:
        # Convert path column to native ltree type and create GIST index
        op.execute("ALTER TABLE administrative_units ALTER COLUMN path TYPE ltree USING path::ltree;")
        op.execute("CREATE INDEX IF NOT EXISTS idx_admin_units_path_gist ON administrative_units USING GIST (path);")

    # 2. Create administrative_officers table
    op.create_table(
        "administrative_officers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("designation", sa.String(length=50), nullable=False),
        sa.Column("administrative_unit_id", sa.String(length=36), nullable=False),
        sa.Column("jurisdiction_path", sa.Text() if is_postgres else sa.String(length=255), nullable=False),
        sa.Column("gov_email", sa.String(length=255), nullable=False),
        sa.Column("aadhaar_verified", sa.Boolean(), nullable=False, server_default=sa.text("true" if is_postgres else "1")),
        sa.Column("appointed_by", sa.String(length=36), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true" if is_postgres else "1")),
        sa.Column("appointed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["administrative_unit_id"], ["administrative_units.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["appointed_by"], ["administrative_officers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_admin_officers_user_id", "administrative_officers", ["user_id"])
    op.create_index("idx_admin_officers_unit_id", "administrative_officers", ["administrative_unit_id"])
    op.create_index("idx_admin_officers_gov_email", "administrative_officers", ["gov_email"])
    op.create_index("idx_admin_officers_jurisdiction", "administrative_officers", ["jurisdiction_path"])

    if is_postgres:
        op.execute("ALTER TABLE administrative_officers ALTER COLUMN jurisdiction_path TYPE ltree USING jurisdiction_path::ltree;")
        op.execute("CREATE INDEX IF NOT EXISTS idx_admin_officers_jurisdiction_gist ON administrative_officers USING GIST (jurisdiction_path);")


def downgrade() -> None:
    op.drop_table("administrative_officers")
    op.drop_table("administrative_units")
