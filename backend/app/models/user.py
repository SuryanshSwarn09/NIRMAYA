"""User identity and authorization relational model for NIRMAYA."""

from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.doctor import DoctorProfile
    from app.models.lab import DiagnosticLabFacility
    from app.models.patient import PatientProfile


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Core platform user entity bridging Supabase Auth and clinical roles."""

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        index=True,
        nullable=True,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.PATIENT,
        nullable=False,
        index=True,
    )
    supabase_uid: Mapped[Optional[str]] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # 1-to-1 relationship with PatientProfile
    patient_profile: Mapped[Optional["PatientProfile"]] = relationship(
        "PatientProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # 1-to-1 relationship with DoctorProfile
    doctor_profile: Mapped[Optional["DoctorProfile"]] = relationship(
        "DoctorProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # 1-to-1 relationship with DiagnosticLabFacility
    lab_facility: Mapped[Optional["DiagnosticLabFacility"]] = relationship(
        "DiagnosticLabFacility",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
