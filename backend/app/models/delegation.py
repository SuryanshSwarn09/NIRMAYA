"""SQLAlchemy relational models for Administrative Chain-of-Command Delegations and Audit Ledger."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.administrative_hierarchy import LTreePath
from app.models.enums import GovtDesignationEnum


class AdministrativeDelegation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents an official chain-of-command authority delegation within the sovereign hierarchy."""

    __tablename__ = "administrative_delegations"

    delegator_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delegator_designation: Mapped[GovtDesignationEnum] = mapped_column(
        Enum(GovtDesignationEnum, name="govt_designation_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    delegatee_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delegatee_designation: Mapped[GovtDesignationEnum] = mapped_column(
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
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    delegation_notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    audit_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    revocation_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    __table_args__ = (
        Index("idx_delegation_path_active", "jurisdiction_path", "is_active"),
        Index("idx_delegation_delegatee_active", "delegatee_user_id", "is_active"),
    )


class DelegationAuditLedger(Base, UUIDPrimaryKeyMixin):
    """Immutable, append-only cryptographic ledger recording all delegation and revocation transactions."""

    __tablename__ = "delegation_audit_ledger"

    delegation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("administrative_delegations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )  # 'DELEGATED', 'REVOKED'
    actor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_designation: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    jurisdiction_path: Mapped[str] = mapped_column(
        LTreePath(),
        nullable=False,
        index=True,
    )
    audit_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    previous_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("idx_delegation_audit_timestamp", "timestamp"),
    )
