"""Clinical Decision Support (CDS) Safety Service.

Coordinates evaluation of candidate medications against:
- Active patient prescriptions (Drug-Drug Interactions)
- Longitudinal patient problem list (Condition Contraindications)
- Documented and supplemental patient allergies (Hypersensitivity Cross-Reactivity)
"""

from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.condition import ClinicalCondition
from app.models.enums import ClinicalStatus, MedicationRequestStatus
from app.models.medication import Medication
from app.models.medication_request import MedicationRequest
from app.models.patient import PatientProfile
from app.schemas.cds import SafetyAlert, SafetyCheckResponse
from app.services.cds_rules import (
    CDSSeverity,
    evaluate_allergy_cross_sensitivity,
    evaluate_condition_contraindications,
    evaluate_drug_drug_interactions,
)


class CDSSafetyService:
    """Clinical Decision Support Safety Service."""

    @staticmethod
    async def evaluate_prescription_safety(
        db: AsyncSession,
        patient_id: str,
        medication_id: str,
        supplemental_allergies: Optional[List[str]] = None,
        supplemental_conditions: Optional[List[str]] = None,
    ) -> SafetyCheckResponse:
        """Perform pre-prescription safety check for candidate medication.

        Args:
            db: Asynchronous SQLAlchemy database session.
            patient_id: UUID string of the target patient profile.
            medication_id: UUID string of the candidate medication.
            supplemental_allergies: Optional list of reported allergies.
            supplemental_conditions: Optional list of ad-hoc clinical conditions.

        Returns:
            SafetyCheckResponse with consolidated risk rating and ranked alerts.

        Raises:
            HTTPException: 404 if patient or medication does not exist.
        """
        # 1. Fetch candidate medication
        candidate_stmt = select(Medication).where(Medication.id == medication_id)
        candidate_res = await db.execute(candidate_stmt)
        candidate = candidate_res.scalar_one_or_none()
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate medication with id '{medication_id}' not found.",
            )

        # 2. Verify patient exists
        patient_stmt = select(PatientProfile).where(PatientProfile.id == patient_id)
        patient_res = await db.execute(patient_stmt)
        patient = patient_res.scalar_one_or_none()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient profile with id '{patient_id}' not found.",
            )

        # 3. Retrieve patient's active prescriptions
        rx_stmt = (
            select(MedicationRequest)
            .options(selectinload(MedicationRequest.medication))
            .where(
                MedicationRequest.patient_id == patient_id,
                MedicationRequest.status == MedicationRequestStatus.ACTIVE,
                MedicationRequest.is_signed.is_(True),
            )
        )
        rx_res = await db.execute(rx_stmt)
        active_prescriptions = rx_res.scalars().all()

        active_med_names: List[str] = []
        for rx in active_prescriptions:
            if rx.medication:
                active_med_names.append(rx.medication.name)
                active_med_names.append(rx.medication.generic_name)
                if rx.medication.brand_name:
                    active_med_names.append(rx.medication.brand_name)

        # 4. Retrieve patient's active conditions from longitudinal problem list
        cond_stmt = select(ClinicalCondition).where(
            ClinicalCondition.patient_id == patient_id,
            ClinicalCondition.clinical_status == ClinicalStatus.ACTIVE,
        )
        cond_res = await db.execute(cond_stmt)
        active_conditions_records = cond_res.scalars().all()

        active_conditions: List[str] = [
            c.code_display for c in active_conditions_records if c.code_display
        ]
        if supplemental_conditions:
            active_conditions.extend(supplemental_conditions)

        # 5. Compile patient allergies
        allergies: List[str] = []
        if supplemental_allergies:
            allergies.extend(supplemental_allergies)

        # 6. Execute rule evaluations
        raw_alerts: List[dict] = []

        # Drug-Drug Interactions
        raw_alerts.extend(
            evaluate_drug_drug_interactions(
                candidate_drug_name=f"{candidate.name} {candidate.generic_name}",
                active_drug_names=active_med_names,
            )
        )

        # Allergy Cross-Reactivity
        if allergies:
            raw_alerts.extend(
                evaluate_allergy_cross_sensitivity(
                    candidate_drug_name=f"{candidate.name} {candidate.generic_name}",
                    patient_allergies=allergies,
                )
            )

        # Condition Contraindications
        if active_conditions:
            raw_alerts.extend(
                evaluate_condition_contraindications(
                    candidate_drug_name=f"{candidate.name} {candidate.generic_name}",
                    active_conditions=active_conditions,
                )
            )

        # 7. Deduplicate and rank alerts: Critical first, then Major, then Moderate
        severity_order = {
            CDSSeverity.CRITICAL.value: 0,
            CDSSeverity.MAJOR.value: 1,
            CDSSeverity.MODERATE.value: 2,
        }

        # Deduplicate alerts based on (rule_id, offending_entity)
        seen_keys = set()
        unique_alerts: List[SafetyAlert] = []
        for a in raw_alerts:
            key = (a["rule_id"], a["offending_entity"].lower())
            if key not in seen_keys:
                seen_keys.add(key)
                unique_alerts.append(SafetyAlert(**a))

        unique_alerts.sort(key=lambda item: severity_order.get(item.severity.value, 99))

        # 8. Compute summary flags
        has_critical = any(a.severity == CDSSeverity.CRITICAL for a in unique_alerts)
        has_major = any(a.severity == CDSSeverity.MAJOR for a in unique_alerts)
        has_moderate = any(a.severity == CDSSeverity.MODERATE for a in unique_alerts)

        return SafetyCheckResponse(
            passed=(not has_critical),
            has_critical_alerts=has_critical,
            has_major_alerts=has_major,
            has_moderate_alerts=has_moderate,
            total_alerts=len(unique_alerts),
            requires_override=(has_critical or has_major),
            candidate_medication_name=candidate.name,
            candidate_generic_name=candidate.generic_name,
            alerts=unique_alerts,
        )


evaluate_prescription_safety = CDSSafetyService.evaluate_prescription_safety
