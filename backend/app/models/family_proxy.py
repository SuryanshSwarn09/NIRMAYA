import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.schemas.family_proxy import (
    ProxyAccessScopeEnum,
    ProxyRelationshipStatusEnum,
    RelationshipTypeEnum,
    VerificationAuthorityEnum,
)


class PatientProxyRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Relational model linking a guardian patient profile to a dependent patient profile.

    Enforces strict zero record contamination: minor children and senior dependents have
    distinct PatientProfile records, and only access permissions are delegated here.
    """
    __tablename__ = "patient_proxy_relationships"

    # Guardian patient profile (Actor holding delegated authority)
    guardian_patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patient_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Dependent patient profile (Subject whose records are isolated)
    dependent_patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patient_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    relationship_type: Mapped[RelationshipTypeEnum] = mapped_column(
        Enum(RelationshipTypeEnum, name="relationship_type_enum", native_enum=False),
        nullable=False,
    )

    verification_tier: Mapped[VerificationAuthorityEnum] = mapped_column(
        Enum(VerificationAuthorityEnum, name="verification_authority_enum", native_enum=False),
        nullable=False,
    )

    verification_document_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    verification_document_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    access_scope: Mapped[ProxyAccessScopeEnum] = mapped_column(
        Enum(ProxyAccessScopeEnum, name="proxy_access_scope_enum", native_enum=False),
        default=ProxyAccessScopeEnum.FULL_MANAGEMENT,
        nullable=False,
    )

    status: Mapped[ProxyRelationshipStatusEnum] = mapped_column(
        Enum(ProxyRelationshipStatusEnum, name="proxy_relationship_status_enum", native_enum=False),
        default=ProxyRelationshipStatusEnum.ACTIVE,
        nullable=False,
    )

    authorized_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    zero_contamination_isolated: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


class ProxyAuditLog(Base, UUIDPrimaryKeyMixin):
    """Forensic audit log recording all access to dependent medical records by proxy guardians."""
    __tablename__ = "proxy_audit_logs"

    relationship_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patient_proxy_relationships.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    actor_guardian_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    target_dependent_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    action_performed: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_accessed: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    ip_address: Mapped[str] = mapped_column(
        String(45),
        default="127.0.0.1",
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    authorized: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
