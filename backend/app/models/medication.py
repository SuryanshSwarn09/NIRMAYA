"""SQLAlchemy 2.0 entity model for the clinical medication catalog and formulary engine.

Directly models the HL7 FHIR Release 4 Medication resource and ABDM NRCeS Medication StructureDefinition profile:
- Identifiers: RxNorm CUI (http://www.nlm.nih.gov/research/umls/rxnorm), WHO-ATC (http://www.whocc.no/atc), SNOMED-CT (http://snomed.info/sct)
- Form: SNOMED-CT dose form hierarchies (tablet, capsule, syrup, injection, etc.)
- Route: HL7 FHIR RouteOfAdministration (oral, intravenous, subcutaneous, inhalation, etc.)
- Formulary: Generic, Preferred Brand, Non-Preferred Brand, Specialty, OTC tiers
"""

from typing import Optional, Dict, Any
from sqlalchemy import (
    Boolean,
    Enum,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    MedicationForm,
    AdministrationRoute,
    FormularyTier,
    MedicationStatus,
)


class Medication(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Clinical medication catalog and formulary entity.

    Directly maps to the HL7 FHIR Release 4 Medication resource:
    - code: RxNorm CUI, WHO-ATC classification, and SNOMED-CT concepts
    - form: Medication dose formulation
    - ingredient: Active substance ingredient and strength
    - status: active | inactive | entered-in-error
    """

    __tablename__ = "medication"

    # Human-readable clinical name (e.g. "Metformin 500mg Oral Tablet")
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # Generic pharmaceutical active moiety name (e.g. "Metformin Hydrochloride")
    generic_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # Commercial brand / trade name (e.g. "Glucophage")
    brand_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    # Standardized NLM RxNorm Concept Unique Identifier (RxCUI) (e.g. "860975")
    rxnorm_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    # RxNorm canonical concept display text
    rxnorm_display: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # WHO Anatomical Therapeutic Chemical classification code (e.g. "A10BA02")
    atc_code: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        index=True,
    )

    # WHO-ATC therapeutic classification display
    atc_display: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # SNOMED-CT clinical drug or medicinal product concept code (e.g. "387048002")
    snomed_code: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    # SNOMED-CT preferred concept display
    snomed_display: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Dose formulation
    form: Mapped[MedicationForm] = mapped_column(
        Enum(MedicationForm),
        nullable=False,
        default=MedicationForm.TABLET,
        index=True,
    )

    # Physiological administration route
    route: Mapped[AdministrationRoute] = mapped_column(
        Enum(AdministrationRoute),
        nullable=False,
        default=AdministrationRoute.ORAL,
        index=True,
    )

    # Quantitative strength specification (e.g. "500 mg", "20 mg/mL")
    strength: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    # Primary active chemical ingredient / substance
    active_ingredient: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # Prescription vs over-the-counter legal classification
    is_prescription_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Narcotic / controlled drug schedule guard
    is_controlled_substance: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Healthcare insurance formulary tier
    formulary_tier: Mapped[FormularyTier] = mapped_column(
        Enum(FormularyTier),
        default=FormularyTier.TIER_1_GENERIC,
        nullable=False,
        index=True,
    )

    # Availability lifecycle status aligned with FHIR R4 MedicationStatus
    status: Mapped[MedicationStatus] = mapped_column(
        Enum(MedicationStatus),
        default=MedicationStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Clinical pharmacology description & indications
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Known high-risk contraindications and black-box safety warnings
    contraindications_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Storage temperature and humidity directives
    storage_instructions: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Extensible packaging metadata (unit count, blister pack, manufacturer)
    package_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Medication(id='{self.id}', name='{self.name}', "
            f"rxnorm='{self.rxnorm_code}', tier='{self.formulary_tier}')>"
        )
