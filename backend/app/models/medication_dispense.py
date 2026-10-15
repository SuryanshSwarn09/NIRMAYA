"""SQLAlchemy 2.0 entity model for Pharmacy Medication Dispensing & Fulfillment.

Directly models the HL7 FHIR Release 4 MedicationDispense resource:
- Authorizing prescription link: MedicationRequest reference
- Batch governance: Lot/batch numbers, drug expiration dates
- Dispense details: Quantity, days of supply, timestamp when prepared/handed over
- Generic substitution audit: was_substituted, substitution_type, substitution_reason
- Status lifecycle: preparation -> in-progress -> completed / cancelled / declined
"""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    Boolean,
    Date,
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
from app.models.enums import MedicationDispenseStatus

if TYPE_CHECKING:
    from app.models.medication import Medication
    from app.models.medication_request import MedicationRequest
    from app.models.patient import PatientProfile
    from app.models.user import User


class MedicationDispense(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Pharmacy Medication Dispense entity tracking the fulfillment of prescriptions."""

    __tablename__ = "medication_dispense"

    # Human-readable business identifier (e.g. "DISP-2026-00042")
    dispense_number: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    # Authorizing prescription (FK -> medication_request.id)
    prescription_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("medication_request.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Subject patient (FK -> patient_profile.id)
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patient_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Dispensed drug entity (FK -> medication.id)
    medication_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("medication.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Dispensing pharmacist or practitioner user (FK -> user.id)
    dispenser_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Fulfillment lifecycle status
    status: Mapped[MedicationDispenseStatus] = mapped_column(
        SQLAlchemyEnum(
            MedicationDispenseStatus,
            name="medication_dispense_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=MedicationDispenseStatus.COMPLETED,
        nullable=False,
        index=True,
    )

    # Rationale when status is cancelled, stopped, or declined
    status_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Quantity dispensed & unit of measurement
    quantity_dispensed: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    dispense_unit: Mapped[str] = mapped_column(
        String(50),
        default="units",
        nullable=False,
    )

    # Estimated supply coverage in days
    days_supply: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Pharmaceutical Batch / Lot tracking
    lot_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    expiration_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Dispense lifecycle timestamps
    when_prepared: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    when_handed_over: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True,
    )

    # Generic & formulary substitution audit
    was_substituted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    substitution_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    substitution_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Patient administration instructions at dispensing time
    dosage_instruction: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Internal clinical / pharmacy notes
    pharmacist_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # ORM Relationships
    prescription: Mapped["MedicationRequest"] = relationship(
        "MedicationRequest",
        back_populates="dispensations",
    )
    patient: Mapped["PatientProfile"] = relationship(
        "PatientProfile",
    )
    medication: Mapped["Medication"] = relationship(
        "Medication",
    )
    dispenser: Mapped[Optional["User"]] = relationship(
        "User",
    )

    def __repr__(self) -> str:
        return (
            f"<MedicationDispense id={self.id} number={self.dispense_number} "
            f"rx={self.prescription_id} status={self.status.value}>"
        )
