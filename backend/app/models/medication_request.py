"""SQLAlchemy 2.0 entity model for electronic prescriptions and medication requests.

Directly models the HL7 FHIR Release 4 MedicationRequest resource and ABDM NRCeS Prescription StructureDefinition profile:
- Status lifecycle: draft -> active -> completed / cancelled / entered-in-error / stopped
- Intent: order (direct clinical order)
- Dosage instruction: magnitude, unit, route, timing frequency, period, as-needed instructions
- Dispense request: quantity, unit, duration in days, refills allowed, validity period
- Generic substitution permissions and reason
- Cryptographic SHA-256 digital signature digest for medicolegal immutability
"""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLAlchemyEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AdministrationRoute,
    MedicationRequestStatus,
    MedicationRequestIntent,
    MedicationRequestPriority,
)

if TYPE_CHECKING:
    from app.models.patient import PatientProfile
    from app.models.doctor import DoctorProfile
    from app.models.appointment import Appointment
    from app.models.medication import Medication
    from app.models.condition import ClinicalCondition


class MedicationRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Electronic prescription / medication request entity.

    Directly maps to the HL7 FHIR Release 4 MedicationRequest resource:
    - subject: PatientProfile
    - requester: DoctorProfile (prescriber)
    - encounter: Appointment (encounter context)
    - medicationReference: Medication (catalog drug with RxNorm/ATC codes)
    - dosageInstruction: Structured dosage instructions
    - dispenseRequest: Quantity, supply duration, repeats/refills
    - substitution: Generic substitution allowed flag and reason
    - insurance / reasonCode: Linked problem list item or condition
    """

    __tablename__ = "medication_request"

    # Patient Vault foreign key (Subject of the prescription)
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patient_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Practitioner doctor author / prescriber foreign key (Requester)
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

    # Medication catalog entity reference (RxNorm, ATC, formulary item)
    medication_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("medication.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # HL7 FHIR R4 Status, Intent, Priority
    status: Mapped[MedicationRequestStatus] = mapped_column(
        SQLAlchemyEnum(
            MedicationRequestStatus,
            name="medication_request_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=MedicationRequestStatus.DRAFT,
        nullable=False,
        index=True,
    )

    intent: Mapped[MedicationRequestIntent] = mapped_column(
        SQLAlchemyEnum(
            MedicationRequestIntent,
            name="medication_request_intent_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=MedicationRequestIntent.ORDER,
        nullable=False,
    )

    priority: Mapped[MedicationRequestPriority] = mapped_column(
        SQLAlchemyEnum(
            MedicationRequestPriority,
            name="medication_request_priority_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=MedicationRequestPriority.ROUTINE,
        nullable=False,
    )

    # Structured Dosage Instruction (FHIR Dosage)
    dosage_text: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    dose_quantity: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    dose_unit: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    route: Mapped[Optional[AdministrationRoute]] = mapped_column(
        SQLAlchemyEnum(
            AdministrationRoute,
            name="administration_route_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
    )
    frequency: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    period: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    period_unit: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        default="d",
    )
    as_needed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    as_needed_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    additional_instructions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Dispense Request (FHIR DispenseRequest)
    dispense_quantity: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    dispense_unit: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    expected_supply_duration_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    number_of_repeats_allowed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    validity_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    validity_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Governance & Clinical Linkage
    allow_generic_substitution: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    substitution_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    reason_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    reason_reference_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("clinical_condition.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    authored_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Digital signature & cryptographic immutability
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

    # Cancellation rationale
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # ORM Relationships
    patient: Mapped["PatientProfile"] = relationship(
        "PatientProfile",
        back_populates="prescriptions",
        lazy="selectin",
    )
    doctor: Mapped[Optional["DoctorProfile"]] = relationship(
        "DoctorProfile",
        back_populates="authored_prescriptions",
        lazy="selectin",
    )
    encounter: Mapped[Optional["Appointment"]] = relationship(
        "Appointment",
        back_populates="prescriptions",
        lazy="selectin",
    )
    medication: Mapped["Medication"] = relationship(
        "Medication",
        back_populates="prescriptions",
        lazy="selectin",
    )
    reason_condition: Mapped[Optional["ClinicalCondition"]] = relationship(
        "ClinicalCondition",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<MedicationRequest id={self.id} patient_id={self.patient_id} "
            f"medication_id={self.medication_id} status={self.status} signed={self.is_signed}>"
        )
