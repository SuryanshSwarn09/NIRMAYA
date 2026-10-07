"""Clinical Observation and Vital Signs model for NIRMAYA.

Defines the observational telemetry entity for patient vital signs, laboratory findings,
and clinical measurements, aligned with the HL7 FHIR Release 4 Observation resource specification.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    ObservationCategory,
    ObservationInterpretation,
    ObservationStatus,
)

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.diagnostic import DiagnosticReport
    from app.models.doctor import DoctorProfile
    from app.models.patient import PatientProfile


class ClinicalObservation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Clinical Observation entity aligned with HL7 FHIR Release 4 Observation.

    Tracks vital signs, physical measurements, diagnostic telemetry, and clinical findings
    with standardized LOINC coding, multi-component support (e.g. Blood Pressure systolic/diastolic),
    UCUM units, and automated reference range interpretation flags.
    """

    __tablename__ = "clinical_observation"

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

    # Clinical performer / practitioner (Doctor who took or verified measurement)
    performer_doctor_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("doctor_profile.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Diagnostic Report context (Optional link to parent laboratory diagnostic report)
    report_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("diagnostic_report.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Observation status (registered | preliminary | final | amended | corrected | etc.)
    status: Mapped[ObservationStatus] = mapped_column(
        Enum(ObservationStatus, name="observation_status_enum", native_enum=False),
        default=ObservationStatus.FINAL,
        nullable=False,
        index=True,
    )

    # Category classification (vital-signs | laboratory | imaging | exam | etc.)
    category: Mapped[ObservationCategory] = mapped_column(
        Enum(ObservationCategory, name="observation_category_enum", native_enum=False),
        default=ObservationCategory.VITAL_SIGNS,
        nullable=False,
        index=True,
    )

    # Terminology coding (default: LOINC http://loinc.org)
    code_coding_system: Mapped[str] = mapped_column(
        String(255),
        default="http://loinc.org",
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

    # Temporal context
    effective_date_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    issued_date_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Quantitative single measurement value
    value_quantity: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    value_unit: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    value_system: Mapped[Optional[str]] = mapped_column(
        String(255),
        default="http://unitsofmeasure.org",
        nullable=True,
    )
    value_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Qualitative / categorical string value
    value_string: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Multi-component measurements (e.g. Blood Pressure panel systolic and diastolic sub-values)
    components: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
    )

    # Physiological reference ranges
    reference_range_low: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    reference_range_high: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    reference_range_text: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Clinical interpretation assessment (normal | high | low | critically-high | abnormal)
    interpretation: Mapped[Optional[ObservationInterpretation]] = mapped_column(
        Enum(
            ObservationInterpretation,
            name="observation_interpretation_enum",
            native_enum=False,
        ),
        nullable=True,
        index=True,
    )

    # Anatomical site and measurement technique
    body_site: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    method: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Clinical notes and diagnostic annotations
    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    patient: Mapped["PatientProfile"] = relationship(
        "PatientProfile",
        back_populates="observations",
    )
    encounter: Mapped[Optional["Appointment"]] = relationship(
        "Appointment",
        back_populates="observations",
        foreign_keys=[encounter_id],
    )
    performer_doctor: Mapped[Optional["DoctorProfile"]] = relationship(
        "DoctorProfile",
        back_populates="performed_observations",
        foreign_keys=[performer_doctor_id],
    )
    diagnostic_report: Mapped[Optional["DiagnosticReport"]] = relationship(
        "DiagnosticReport",
        back_populates="observations",
        foreign_keys=[report_id],
    )

    def __repr__(self) -> str:
        val = f"{self.value_quantity} {self.value_unit}" if self.value_quantity is not None else "compound"
        return (
            f"<ClinicalObservation id={self.id} patient_id={self.patient_id} "
            f"code={self.code_value} ({self.code_display}) val={val}>"
        )
