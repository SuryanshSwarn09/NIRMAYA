"""Patient clinical profile and ABHA identity model for NIRMAYA."""

from datetime import date
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BloodGroup, Gender

if TYPE_CHECKING:
    from app.models.appointment import Appointment, DoctorSlot
    from app.models.condition import ClinicalCondition
    from app.models.observation import ClinicalObservation
    from app.models.user import User



class PatientProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):

    """Clinical demographics and longitudinal health vault profile for patients."""

    # 1-to-1 linkage to User identity
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Core Demographics (HL7 FHIR R4 aligned)
    date_of_birth: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    gender: Mapped[Gender] = mapped_column(
        Enum(Gender, name="gender_enum", native_enum=False),
        default=Gender.UNKNOWN,
        nullable=False,
    )
    blood_group: Mapped[BloodGroup] = mapped_column(
        Enum(BloodGroup, name="blood_group_enum", native_enum=False),
        default=BloodGroup.UNKNOWN,
        nullable=False,
    )

    # Geographic & Residential Details
    address_line: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )

    # Emergency Contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    emergency_contact_relation: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Ayushman Bharat Digital Mission (ABDM) Identifiers
    abha_number: Mapped[Optional[str]] = mapped_column(
        String(17),
        unique=True,
        index=True,
        nullable=True,
    )
    abha_address: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
    )

    # Relationship back to User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="patient_profile",
    )

    # Clinical encounter appointments
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    # Consultation slots currently reserved/held by this patient
    held_slots: Mapped[List["DoctorSlot"]] = relationship(
        "DoctorSlot",
        foreign_keys="DoctorSlot.held_by_patient_id",
        back_populates="held_by_patient",
    )

    # Longitudinal clinical conditions problem list
    conditions: Mapped[List["ClinicalCondition"]] = relationship(
        "ClinicalCondition",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    # Observational telemetry and vital signs
    observations: Mapped[List["ClinicalObservation"]] = relationship(
        "ClinicalObservation",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:


        return (
            f"<PatientProfile id={self.id} user_id={self.user_id} "
            f"abha_address={self.abha_address}>"
        )
