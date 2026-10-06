"""SQLAlchemy 2.0 entity model for structured SOAP clinical encounter notes and documentation."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ClinicalNoteStatus, ClinicalNoteType

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.doctor import DoctorProfile
    from app.models.patient import PatientProfile


class SoapNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Structured SOAP clinical note generated during a clinical encounter.

    Directly maps to the HL7 FHIR Release 4 Composition resource with standard LOINC narrative sections:
    - Chief Complaint (LOINC 10154-3)
    - Subjective narrative (LOINC 61150-9)
    - Objective narrative (LOINC 61149-1)
    - Assessment & Diagnoses (LOINC 51848-0)
    - Plan of Care (LOINC 18776-5)
    """

    __tablename__ = "soap_note"

    # Patient Vault foreign key
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patient_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Practitioner doctor author foreign key
    doctor_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("doctor_profile.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Encounter context (Optional link to appointment/encounter)
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("appointment.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Clinical note classification and workflow status
    note_type: Mapped[ClinicalNoteType] = mapped_column(
        Enum(ClinicalNoteType, name="clinical_note_type_enum", native_enum=False),
        default=ClinicalNoteType.SOAP,
        nullable=False,
        index=True,
    )
    status: Mapped[ClinicalNoteStatus] = mapped_column(
        Enum(ClinicalNoteStatus, name="clinical_note_status_enum", native_enum=False),
        default=ClinicalNoteStatus.PRELIMINARY,
        nullable=False,
        index=True,
    )

    # Note header
    title: Mapped[str] = mapped_column(
        String(255),
        default="Clinical Consultation SOAP Note",
        nullable=False,
    )

    # Chief complaint / reason for encounter (LOINC 10154-3)
    chief_complaint: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # 1. Subjective narrative (LOINC 61150-9)
    subjective: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 2. Objective examination findings & vitals review (LOINC 61149-1)
    objective: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 3. Assessment & differential diagnoses (LOINC 51848-0)
    assessment: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 4. Plan of care, therapeutics, diagnostic orders (LOINC 18776-5)
    plan: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Diagnostic codings (optional primary diagnosis)
    primary_diagnosis_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    primary_diagnosis_display: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Patient follow-up & discharge instructions
    follow_up_instructions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Digital signature & tamper-evident hashing
    is_signed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    signed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    signature_hash: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )

    # ORM Relationships
    patient: Mapped["PatientProfile"] = relationship(
        "PatientProfile",
        back_populates="soap_notes",
        lazy="selectin",
    )
    doctor: Mapped[Optional["DoctorProfile"]] = relationship(
        "DoctorProfile",
        back_populates="authored_soap_notes",
        lazy="selectin",
    )
    encounter: Mapped[Optional["Appointment"]] = relationship(
        "Appointment",
        back_populates="soap_notes",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<SoapNote id={self.id} patient_id={self.patient_id} "
            f"type={self.note_type} status={self.status} signed={self.is_signed}>"
        )
