"""Clinical Condition and Problem List model for NIRMAYA.

Defines the longitudinal problem list entity for patient clinical profiles,
aligned with the HL7 FHIR Release 4 Condition resource specification.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    ClinicalStatus,
    ConditionCategory,
    ConditionSeverity,
    VerificationStatus,
)

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.doctor import DoctorProfile
    from app.models.patient import PatientProfile


class ClinicalCondition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Clinical Condition and Problem List entity aligned with HL7 FHIR R4 Condition.

    Represents diagnosed health conditions, chronic illnesses, encounter diagnoses,
    and patient-reported problems with SNOMED-CT / ICD-10 coding and status lifecycles.
    """

    # Subject patient (Foreign Key to patient_profile)
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patient_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Encounter context (Optional link to clinical appointment/encounter)
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("appointment.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Clinical recorder (Doctor who recorded/confirmed the diagnosis)
    recorded_by_doctor_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("doctor_profile.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Clinical status (active | recurrence | relapse | inactive | remission | resolved)
    clinical_status: Mapped[ClinicalStatus] = mapped_column(
        Enum(ClinicalStatus, name="clinical_status_enum", native_enum=False),
        default=ClinicalStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Verification status (unconfirmed | provisional | differential | confirmed | refuted | entered-in-error)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status_enum", native_enum=False),
        default=VerificationStatus.CONFIRMED,
        nullable=False,
        index=True,
    )

    # Category (problem-list-item | encounter-diagnosis | chronic-condition)
    category: Mapped[ConditionCategory] = mapped_column(
        Enum(ConditionCategory, name="condition_category_enum", native_enum=False),
        default=ConditionCategory.PROBLEM_LIST_ITEM,
        nullable=False,
        index=True,
    )

    # Severity assessment (mild | moderate | severe)
    severity: Mapped[Optional[ConditionSeverity]] = mapped_column(
        Enum(ConditionSeverity, name="condition_severity_enum", native_enum=False),
        nullable=True,
        index=True,
    )

    # Terminology coding (SNOMED-CT or ICD-10)
    code_coding_system: Mapped[str] = mapped_column(
        String(255),
        default="http://snomed.info/sct",
        nullable=False,
    )
    code_value: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    code_display: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Anatomical location (body site if applicable)
    body_site: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Clinical timeline timestamps
    onset_date_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    abatement_date_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    recorded_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Clinical notes / annotations
    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    patient: Mapped["PatientProfile"] = relationship(
        "PatientProfile",
        back_populates="conditions",
    )
    encounter: Mapped[Optional["Appointment"]] = relationship(
        "Appointment",
        back_populates="conditions",
        foreign_keys=[encounter_id],
    )
    recorded_by_doctor: Mapped[Optional["DoctorProfile"]] = relationship(
        "DoctorProfile",
        back_populates="recorded_conditions",
        foreign_keys=[recorded_by_doctor_id],
    )

    def __repr__(self) -> str:
        return (
            f"<ClinicalCondition id={self.id} patient_id={self.patient_id} "
            f"code={self.code_value} status={self.clinical_status.value}>"
        )
