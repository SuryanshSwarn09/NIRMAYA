"""SQLAlchemy 2.0 entity models for diagnostic lab service requests and diagnostic reports.

Directly models the HL7 FHIR Release 4 ServiceRequest and DiagnosticReport resources.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    DiagnosticReportStatus,
    ServiceRequestIntent,
    ServiceRequestPriority,
    ServiceRequestStatus,
    SpecimenType,
)

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.doctor import DoctorProfile
    from app.models.observation import ClinicalObservation
    from app.models.patient import PatientProfile


class DiagnosticOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Clinical diagnostic service request / laboratory requisition order.

    Directly maps to the HL7 FHIR Release 4 ServiceRequest resource:
    - code: LOINC diagnostic panel/test code (e.g., 24331-1 Lipid Panel, 4548-4 HbA1c)
    - subject: PatientProfile
    - requester: DoctorProfile
    - encounter: Appointment
    - priority: routine | urgent | asap | stat
    - status: draft | active | on-hold | revoked | completed | entered-in-error
    """

    __tablename__ = "diagnostic_order"

    # Patient Vault foreign key
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patient_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Ordering practitioner doctor foreign key
    doctor_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("doctor_profile.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Encounter context (Optional link to appointment)
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("appointment.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Workflow status & intent
    status: Mapped[ServiceRequestStatus] = mapped_column(
        Enum(ServiceRequestStatus, name="service_request_status_enum", native_enum=False),
        default=ServiceRequestStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    intent: Mapped[ServiceRequestIntent] = mapped_column(
        Enum(ServiceRequestIntent, name="service_request_intent_enum", native_enum=False),
        default=ServiceRequestIntent.ORDER,
        nullable=False,
    )
    priority: Mapped[ServiceRequestPriority] = mapped_column(
        Enum(ServiceRequestPriority, name="service_request_priority_enum", native_enum=False),
        default=ServiceRequestPriority.ROUTINE,
        nullable=False,
        index=True,
    )

    # Requisition classification (e.g., laboratory, diagnostic_imaging, pathology)
    category: Mapped[str] = mapped_column(
        String(100),
        default="laboratory",
        nullable=False,
        index=True,
    )

    # Terminology coding (default: LOINC http://loinc.org)
    code_coding_system: Mapped[str] = mapped_column(
        String(100),
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

    # Clinical indication / justification
    reason_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    reason_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Specimen metadata
    specimen_type: Mapped[Optional[SpecimenType]] = mapped_column(
        Enum(SpecimenType, name="specimen_type_enum", native_enum=False),
        nullable=True,
    )

    # Additional instructions / clinical notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Bidirectional relationships
    patient: Mapped["PatientProfile"] = relationship(
        "PatientProfile",
        back_populates="diagnostic_orders",
    )
    doctor: Mapped[Optional["DoctorProfile"]] = relationship(
        "DoctorProfile",
        back_populates="diagnostic_orders",
    )
    encounter: Mapped[Optional["Appointment"]] = relationship(
        "Appointment",
        back_populates="diagnostic_orders",
    )
    reports: Mapped[List["DiagnosticReport"]] = relationship(
        "DiagnosticReport",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<DiagnosticOrder id={self.id} patient_id={self.patient_id} "
            f"code={self.code_value} status={self.status}>"
        )


class DiagnosticReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Clinical diagnostic report issued by a laboratory or imaging center.

    Directly maps to the HL7 FHIR Release 4 DiagnosticReport resource:
    - basedOn: DiagnosticOrder (ServiceRequest)
    - subject: PatientProfile
    - performer: DoctorProfile (Pathologist / Lab Director)
    - status: registered | preliminary | final | amended | corrected | cancelled | entered-in-error
    - code: LOINC diagnostic report code
    - result: Observations
    - conclusion: Diagnostic summary narrative
    """

    __tablename__ = "diagnostic_report"

    # Patient Vault foreign key
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patient_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Diagnostic order foreign key (requisition source)
    order_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("diagnostic_order.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Clinical encounter context
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("appointment.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Sign-off pathologist / practitioner foreign key
    performer_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("doctor_profile.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Performer display name (e.g. Diagnostic Center / Pathologist Name)
    performer_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        default="Metropolis Diagnostics & Pathology Lab",
        nullable=True,
    )

    # Report verification status
    status: Mapped[DiagnosticReportStatus] = mapped_column(
        Enum(DiagnosticReportStatus, name="diagnostic_report_status_enum", native_enum=False),
        default=DiagnosticReportStatus.FINAL,
        nullable=False,
        index=True,
    )

    # Diagnostic service category (e.g., LAB, MB, CH, RAD)
    category: Mapped[str] = mapped_column(
        String(100),
        default="LAB",
        nullable=False,
        index=True,
    )

    # Diagnostic panel coding (LOINC)
    code_coding_system: Mapped[str] = mapped_column(
        String(100),
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

    # Timing
    effective_date_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    issued_date_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Clinical conclusion & abnormal flag
    conclusion: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    conclusion_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    is_abnormal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # Structured test metrics payload (JSON summary for fast retrieval)
    report_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    # Bidirectional relationships
    patient: Mapped["PatientProfile"] = relationship(
        "PatientProfile",
        back_populates="diagnostic_reports",
    )
    order: Mapped[Optional["DiagnosticOrder"]] = relationship(
        "DiagnosticOrder",
        back_populates="reports",
    )
    encounter: Mapped[Optional["Appointment"]] = relationship(
        "Appointment",
        back_populates="diagnostic_reports",
    )
    performer: Mapped[Optional["DoctorProfile"]] = relationship(
        "DoctorProfile",
        back_populates="performed_diagnostic_reports",
    )
    observations: Mapped[List["ClinicalObservation"]] = relationship(
        "ClinicalObservation",
        back_populates="diagnostic_report",
    )

    def __repr__(self) -> str:
        return (
            f"<DiagnosticReport id={self.id} patient_id={self.patient_id} "
            f"code={self.code_value} status={self.status} abnormal={self.is_abnormal}>"
        )
