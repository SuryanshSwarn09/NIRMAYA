"""Healthcare provider clinical credentials and EMR profile model for NIRMAYA."""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import MedicalSpecialty

if TYPE_CHECKING:
    from app.models.appointment import Appointment, DoctorSlot
    from app.models.condition import ClinicalCondition
    from app.models.user import User


class DoctorProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):

    """Clinical credentials, medical council licensing, and consultation profile for doctors."""

    # 1-to-1 linkage to User identity
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Medical Council Licensing & Registration
    registration_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    medical_council: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Clinical Specialty & Qualifications
    specialty: Mapped[MedicalSpecialty] = mapped_column(
        Enum(MedicalSpecialty, name="medical_specialty_enum", native_enum=False),
        default=MedicalSpecialty.GENERAL_MEDICINE,
        nullable=False,
        index=True,
    )
    qualifications: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    experience_years: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Practice & Consultation Details
    consultation_fee: Mapped[int] = mapped_column(
        Integer,
        default=500,
        nullable=False,
    )
    hospital_affiliation: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    is_available_for_teleconsult: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Ayushman Bharat Digital Mission (ABDM) Healthcare Professional Registry
    hpr_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=True,
    )

    # Relationship back to User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="doctor_profile",
    )

    # Doctor consultation slots
    slots: Mapped[List["DoctorSlot"]] = relationship(
        "DoctorSlot",
        back_populates="doctor",
        cascade="all, delete-orphan",
    )

    # Clinical encounter appointments
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        back_populates="doctor",
        cascade="all, delete-orphan",
    )

    # Clinical conditions recorded/diagnosed by this doctor
    recorded_conditions: Mapped[List["ClinicalCondition"]] = relationship(
        "ClinicalCondition",
        back_populates="recorded_by_doctor",
    )

    def __repr__(self) -> str:

        return (
            f"<DoctorProfile id={self.id} user_id={self.user_id} "
            f"reg={self.registration_number} specialty={self.specialty}>"
        )
