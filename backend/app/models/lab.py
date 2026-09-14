"""Diagnostic laboratory facility and test accreditation model for NIRMAYA."""

from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import LabAccreditation

if TYPE_CHECKING:
    from app.models.user import User


class DiagnosticLabFacility(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Accredited diagnostic testing center, lab credentials, and ABDM HFR profile."""

    # 1-to-1 linkage to Lab administrator/technician User identity
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Facility Identity & Licensing
    facility_name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    license_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    # Accreditation (NABL / CAP / ISO 15189)
    accreditation: Mapped[LabAccreditation] = mapped_column(
        Enum(LabAccreditation, name="lab_accreditation_enum", native_enum=False),
        default=LabAccreditation.NABL,
        nullable=False,
    )
    accreditation_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    is_nabl_certified: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Administrative & Contact Information
    contact_person: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    contact_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    contact_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Geographic & Facility Location
    address_line: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    city: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    pincode: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    # Testing Catalog & Capabilities
    supported_tests: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Ayushman Bharat Digital Mission (ABDM) Health Facility Registry
    hfr_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=True,
    )

    # Relationship back to User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="lab_facility",
    )

    def __repr__(self) -> str:
        return (
            f"<DiagnosticLabFacility id={self.id} user_id={self.user_id} "
            f"facility={self.facility_name} accreditation={self.accreditation}>"
        )
