"""SQLAlchemy relational models for Indian LGD 6-Tier Administrative Hierarchy and Appointed Officers."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator, UserDefinedType

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AdminLevelEnum, GovtDesignationEnum

if TYPE_CHECKING:
    from app.models.user import User


class LTree(UserDefinedType):
    """PostgreSQL native ltree column specification."""

    def get_col_spec(self, **kw) -> str:
        return "ltree"


class LTreePath(TypeDecorator):
    """Platform-independent ltree path type decorator.

    Resolves to native PostgreSQL `ltree` in production and `String(255)` on SQLite
    during in-memory test executions.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(LTree())
        return dialect.type_descriptor(String(255))


class AdministrativeUnit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents a sovereign territorial governance unit in India's 6-tier administrative hierarchy."""

    __tablename__ = "administrative_units"

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )
    unit_level: Mapped[AdminLevelEnum] = mapped_column(
        Enum(AdminLevelEnum, name="admin_level_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    lgd_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=True,
    )
    path: Mapped[str] = mapped_column(
        LTreePath(),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("administrative_units.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    pincode_prefixes: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Hierarchical parent-child traversal
    parent: Mapped[Optional["AdministrativeUnit"]] = relationship(
        "AdministrativeUnit",
        remote_side="AdministrativeUnit.id",
        back_populates="children",
    )
    children: Mapped[List["AdministrativeUnit"]] = relationship(
        "AdministrativeUnit",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    # Appointed administrative health officers
    officers: Mapped[List["AdministrativeOfficer"]] = relationship(
        "AdministrativeOfficer",
        back_populates="administrative_unit",
    )

    __table_args__ = (
        Index("idx_admin_units_path_gist", "path", postgresql_using="gist"),
        Index("idx_admin_units_level_parent", "unit_level", "parent_id"),
    )


class AdministrativeOfficer(Base, UUIDPrimaryKeyMixin):
    """Appointed administrative officer exercising jurisdictional oversight over a territorial scope."""

    __tablename__ = "administrative_officers"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    designation: Mapped[GovtDesignationEnum] = mapped_column(
        Enum(GovtDesignationEnum, name="govt_designation_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    administrative_unit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("administrative_units.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    jurisdiction_path: Mapped[str] = mapped_column(
        LTreePath(),
        nullable=False,
        index=True,
    )
    gov_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    aadhaar_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    appointed_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("administrative_officers.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    appointed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    administrative_unit: Mapped["AdministrativeUnit"] = relationship(
        "AdministrativeUnit",
        back_populates="officers",
    )
    appointer: Mapped[Optional["AdministrativeOfficer"]] = relationship(
        "AdministrativeOfficer",
        remote_side="AdministrativeOfficer.id",
    )

    __table_args__ = (
        Index("idx_admin_officers_jurisdiction_gist", "jurisdiction_path", postgresql_using="gist"),
        Index("idx_admin_officers_unit_active", "administrative_unit_id", "is_active"),
    )
