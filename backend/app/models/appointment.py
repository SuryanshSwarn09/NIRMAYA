"""Clinical appointment scheduling and doctor slot models for NIRMAYA platform.

Aligned with HL7 FHIR Release 4 Appointment & Schedule resources.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AppointmentStatus, AppointmentType, SlotStatus

if TYPE_CHECKING:
    from app.models.condition import ClinicalCondition
    from app.models.doctor import DoctorProfile
    from app.models.observation import ClinicalObservation
    from app.models.patient import PatientProfile
    from app.models.soap_note import SoapNote


class DoctorSlot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Doctor consultation availability time slot.

    Guarantees conflict-free scheduling via unique constraint on (doctor_id, start_time).
    """

    __tablename__ = "doctor_slot"

    # Foreign Key to DoctorProfile
    doctor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("doctor_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Time boundaries (UTC timezone aware)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Availability lifecycle status
    status: Mapped[SlotStatus] = mapped_column(
        Enum(SlotStatus, name="slot_status_enum", native_enum=False),
        default=SlotStatus.AVAILABLE,
        nullable=False,
        index=True,
    )

    # Teleconsultation readiness flag
    is_teleconsult: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Temporary hold reservation lifecycle
    held_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    held_by_patient_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("patient_profile.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Concurrency and conflict guard
    __table_args__ = (
        UniqueConstraint("doctor_id", "start_time", name="uq_doctor_slot_start"),
    )

    # Bidirectional relationships
    doctor: Mapped["DoctorProfile"] = relationship(
        "DoctorProfile",
        back_populates="slots",
    )
    appointment: Mapped[Optional["Appointment"]] = relationship(
        "Appointment",
        back_populates="slot",
        uselist=False,
    )
    held_by_patient: Mapped[Optional["PatientProfile"]] = relationship(
        "PatientProfile",
        foreign_keys=[held_by_patient_id],
        back_populates="held_slots",
    )


    def __repr__(self) -> str:
        return (
            f"<DoctorSlot id={self.id} doctor_id={self.doctor_id} "
            f"start={self.start_time.isoformat()} status={self.status}>"
        )


class Appointment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Clinical encounter appointment linking a patient, practitioner doctor, and reserved slot.

    Directly models the HL7 FHIR R4 Appointment resource.
    """

    __tablename__ = "appointment"
    __table_args__ = (
        UniqueConstraint("slot_id", name="uq_appointment_slot_id"),
    )

    # 1. Patient Vault foreign key
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patient_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 2. Practitioner Doctor foreign key
    doctor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("doctor_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 3. Linked Slot foreign key (Optional for ad-hoc/walk-in encounters, 1-to-1 when linked)
    slot_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("doctor_slot.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
        index=True,
    )

    # Encounter classifications
    appointment_type: Mapped[AppointmentType] = mapped_column(
        Enum(AppointmentType, name="appointment_type_enum", native_enum=False),
        default=AppointmentType.ROUTINE_CHECKUP,
        nullable=False,
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status_enum", native_enum=False),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
        index=True,
    )

    # Scheduled consultation window
    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Clinical context & symptoms description
    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    clinical_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    teleconsultation_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Bidirectional relationships
    patient: Mapped["PatientProfile"] = relationship(
        "PatientProfile",
        back_populates="appointments",
    )
    doctor: Mapped["DoctorProfile"] = relationship(
        "DoctorProfile",
        back_populates="appointments",
    )
    slot: Mapped[Optional["DoctorSlot"]] = relationship(
        "DoctorSlot",
        back_populates="appointment",
    )
    conditions: Mapped[List["ClinicalCondition"]] = relationship(
        "ClinicalCondition",
        back_populates="encounter",
    )
    observations: Mapped[List["ClinicalObservation"]] = relationship(
        "ClinicalObservation",
        back_populates="encounter",
    )
    soap_notes: Mapped[List["SoapNote"]] = relationship(
        "SoapNote",
        back_populates="encounter",
    )

    def __repr__(self) -> str:
        return (
            f"<Appointment id={self.id} patient_id={self.patient_id} "
            f"doctor_id={self.doctor_id} status={self.status}>"
        )
