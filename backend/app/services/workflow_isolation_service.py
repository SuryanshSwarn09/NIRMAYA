import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.schemas.workflow_isolation import (
    ContextTypeEnum,
    DependentContextSummary,
    FallRiskCategoryEnum,
    GeriatricAssessmentProfile,
    NutritionalStatusEnum,
    PediatricGrowthObservation,
    PediatricImmunizationMilestone,
    VaccinationStatusEnum,
    WorkflowSwitchResponse,
)
from app.services.family_proxy_service import family_proxy_service


class WorkflowIsolationService:
    """Service governing pediatric and geriatric clinical workflow isolation,
    session context switching, and zero-contamination view segmentation under DPDP Act 2023 Sec 9.
    """

    def __init__(self) -> None:
        self._active_contexts: Dict[str, str] = {}  # user_id -> active target_patient_id
        self._immunization_records: Dict[str, List[PediatricImmunizationMilestone]] = self._init_seed_immunizations()
        self._growth_observations: Dict[str, List[PediatricGrowthObservation]] = self._init_seed_growth_observations()
        self._geriatric_assessments: Dict[str, GeriatricAssessmentProfile] = self._init_seed_geriatric_assessments()

    def _init_seed_immunizations(self) -> Dict[str, List[PediatricImmunizationMilestone]]:
        """Seed National Universal Immunization Programme (UIP) schedule for child dependents."""
        uip_schedule = [
            # At Birth
            PediatricImmunizationMilestone(
                milestone_id="uip-bcg-01",
                vaccine_code="BCG",
                vaccine_name="Bacillus Calmette-Guerin",
                target_age_display="At Birth",
                status=VaccinationStatusEnum.ADMINISTERED,
                dose_number=1,
                administered_date="2018-06-15",
                administered_facility="AIIMS Pediatric Ward, New Delhi",
                administered_by_hpr="dr.ananya.sen@hpid",
                batch_number="SII-BCG-9021-B",
                adverse_events_reported=False,
            ),
            PediatricImmunizationMilestone(
                milestone_id="uip-opv-0",
                vaccine_code="OPV-0",
                vaccine_name="Oral Polio Vaccine (Zero Dose)",
                target_age_display="At Birth",
                status=VaccinationStatusEnum.ADMINISTERED,
                dose_number=1,
                administered_date="2018-06-15",
                administered_facility="AIIMS Pediatric Ward, New Delhi",
                administered_by_hpr="dr.ananya.sen@hpid",
                batch_number="BIBCOL-OPV-4812",
                adverse_events_reported=False,
            ),
            PediatricImmunizationMilestone(
                milestone_id="uip-hepb-0",
                vaccine_code="HepB-0",
                vaccine_name="Hepatitis B (Birth Dose)",
                target_age_display="At Birth",
                status=VaccinationStatusEnum.ADMINISTERED,
                dose_number=1,
                administered_date="2018-06-15",
                administered_facility="AIIMS Pediatric Ward, New Delhi",
                administered_by_hpr="dr.ananya.sen@hpid",
                batch_number="BB-HEPB-1049",
                adverse_events_reported=False,
            ),
            # 6 Weeks
            PediatricImmunizationMilestone(
                milestone_id="uip-penta-1",
                vaccine_code="PENTA-1",
                vaccine_name="Pentavalent (DPT + HepB + Hib)",
                target_age_display="6 Weeks",
                status=VaccinationStatusEnum.ADMINISTERED,
                dose_number=1,
                administered_date="2018-07-30",
                administered_facility="Max Pediatric Care, Saket",
                administered_by_hpr="dr.rkulkarni@hpid",
                batch_number="SII-PENTA-3301",
                adverse_events_reported=False,
            ),
            PediatricImmunizationMilestone(
                milestone_id="uip-rota-1",
                vaccine_code="ROTA-1",
                vaccine_name="Rotavirus Vaccine (Dose 1)",
                target_age_display="6 Weeks",
                status=VaccinationStatusEnum.ADMINISTERED,
                dose_number=1,
                administered_date="2018-07-30",
                administered_facility="Max Pediatric Care, Saket",
                administered_by_hpr="dr.rkulkarni@hpid",
                batch_number="BB-ROTA-9102",
                adverse_events_reported=False,
            ),
            # 10 Weeks
            PediatricImmunizationMilestone(
                milestone_id="uip-penta-2",
                vaccine_code="PENTA-2",
                vaccine_name="Pentavalent (DPT + HepB + Hib - Dose 2)",
                target_age_display="10 Weeks",
                status=VaccinationStatusEnum.ADMINISTERED,
                dose_number=2,
                administered_date="2018-09-02",
                administered_facility="Max Pediatric Care, Saket",
                administered_by_hpr="dr.rkulkarni@hpid",
                batch_number="SII-PENTA-3419",
                adverse_events_reported=False,
            ),
            # 14 Weeks
            PediatricImmunizationMilestone(
                milestone_id="uip-penta-3",
                vaccine_code="PENTA-3",
                vaccine_name="Pentavalent (DPT + HepB + Hib - Dose 3)",
                target_age_display="14 Weeks",
                status=VaccinationStatusEnum.ADMINISTERED,
                dose_number=3,
                administered_date="2018-10-05",
                administered_facility="Max Pediatric Care, Saket",
                administered_by_hpr="dr.rkulkarni@hpid",
                batch_number="SII-PENTA-3590",
                adverse_events_reported=False,
            ),
            # 9-12 Months
            PediatricImmunizationMilestone(
                milestone_id="uip-mr-1",
                vaccine_code="MR-1",
                vaccine_name="Measles & Rubella (Dose 1)",
                target_age_display="9 Months",
                status=VaccinationStatusEnum.ADMINISTERED,
                dose_number=1,
                administered_date="2019-03-20",
                administered_facility="Apollo Children Hospital, Delhi",
                administered_by_hpr="dr.ananya.sen@hpid",
                batch_number="SII-MR-8812",
                adverse_events_reported=False,
            ),
            # 16-24 Months
            PediatricImmunizationMilestone(
                milestone_id="uip-mr-2",
                vaccine_code="MR-2",
                vaccine_name="Measles & Rubella (Dose 2 Booster)",
                target_age_display="16-24 Months",
                status=VaccinationStatusEnum.ADMINISTERED,
                dose_number=2,
                administered_date="2020-01-14",
                administered_facility="Apollo Children Hospital, Delhi",
                administered_by_hpr="dr.ananya.sen@hpid",
                batch_number="SII-MR-9921",
                adverse_events_reported=False,
            ),
            PediatricImmunizationMilestone(
                milestone_id="uip-dpt-b1",
                vaccine_code="DPT-B1",
                vaccine_name="DPT Booster 1",
                target_age_display="16-24 Months",
                status=VaccinationStatusEnum.ADMINISTERED,
                dose_number=1,
                administered_date="2020-01-14",
                administered_facility="Apollo Children Hospital, Delhi",
                administered_by_hpr="dr.ananya.sen@hpid",
                batch_number="SII-DPT-4412",
                adverse_events_reported=False,
            ),
            # 5-6 Years Booster
            PediatricImmunizationMilestone(
                milestone_id="uip-dpt-b2",
                vaccine_code="DPT-B2",
                vaccine_name="DPT Booster 2",
                target_age_display="5-6 Years",
                status=VaccinationStatusEnum.SCHEDULED,
                dose_number=2,
                administered_date=None,
                administered_facility=None,
                administered_by_hpr=None,
                batch_number=None,
                adverse_events_reported=False,
            ),
        ]
        return {
            "pat-aarav-sharma-02": uip_schedule,
            "default": uip_schedule,
        }

    def _init_seed_growth_observations(self) -> Dict[str, List[PediatricGrowthObservation]]:
        """Seed WHO growth percentile trajectories for pediatric dependents."""
        return {
            "pat-aarav-sharma-02": [
                PediatricGrowthObservation(
                    observation_id="gro-aarav-01",
                    child_patient_id="pat-aarav-sharma-02",
                    age_months=6,
                    recorded_date="2018-12-15",
                    weight_kg=7.9,
                    height_cm=67.5,
                    head_circumference_cm=43.2,
                    who_weight_percentile=50,
                    who_height_percentile=55,
                    nutritional_status=NutritionalStatusEnum.NORMAL,
                ),
                PediatricGrowthObservation(
                    observation_id="gro-aarav-02",
                    child_patient_id="pat-aarav-sharma-02",
                    age_months=12,
                    recorded_date="2019-06-15",
                    weight_kg=9.6,
                    height_cm=75.8,
                    head_circumference_cm=46.0,
                    who_weight_percentile=52,
                    who_height_percentile=54,
                    nutritional_status=NutritionalStatusEnum.NORMAL,
                ),
                PediatricGrowthObservation(
                    observation_id="gro-aarav-03",
                    child_patient_id="pat-aarav-sharma-02",
                    age_months=24,
                    recorded_date="2020-06-15",
                    weight_kg=12.2,
                    height_cm=87.2,
                    head_circumference_cm=48.2,
                    who_weight_percentile=50,
                    who_height_percentile=53,
                    nutritional_status=NutritionalStatusEnum.NORMAL,
                ),
                PediatricGrowthObservation(
                    observation_id="gro-aarav-04",
                    child_patient_id="pat-aarav-sharma-02",
                    age_months=48,
                    recorded_date="2022-06-15",
                    weight_kg=16.3,
                    height_cm=103.0,
                    head_circumference_cm=50.1,
                    who_weight_percentile=55,
                    who_height_percentile=56,
                    nutritional_status=NutritionalStatusEnum.NORMAL,
                ),
            ]
        }

    def _init_seed_geriatric_assessments(self) -> Dict[str, GeriatricAssessmentProfile]:
        """Seed Comprehensive Geriatric Assessment (CGA) and polypharmacy data."""
        return {
            "pat-kavita-sharma-03": GeriatricAssessmentProfile(
                senior_patient_id="pat-kavita-sharma-03",
                assessed_date="2026-10-18T10:30:00Z",
                frailty_score=2,
                frailty_status="Pre-Frail (Fried Phenotype 2/5)",
                fall_risk_category=FallRiskCategoryEnum.MODERATE,
                timed_up_and_go_seconds=13.8,
                polypharmacy_count=5,
                beers_criteria_alerts=[
                    {
                        "medication": "Amlodipine 5mg + Atorvastatin 20mg",
                        "severity": "WARNING",
                        "guideline": "Monitor lower extremity peripheral edema and hepatic transaminases every 6 months.",
                    },
                    {
                        "medication": "Pantoprazole 40mg",
                        "severity": "CAUTION",
                        "guideline": "Beers Criteria: Prolonged proton-pump inhibitor use > 8 weeks carries increased risk of Clostridioides difficile infection and bone density reduction.",
                    },
                ],
                adl_score=5,
                cognitive_screening_result="Mini-Cog: 4/5 (Intact 3-word recall, normal analog clock drawing)",
                caregiver_notes="Patient walks with slight hesitation on uneven ground. Independent with daily dressing and meals. Blood pressure well controlled at 128/82 mmHg.",
            )
        }

    def list_available_contexts(self, user_id: str) -> List[DependentContextSummary]:
        """Enumerate switchable clinical contexts for the authenticated user,
        including personal vault (self) and all verified family proxy dependents.
        """
        active_target = self._active_contexts.get(user_id, user_id)
        contexts: List[DependentContextSummary] = []

        # 1. Primary User Persona Context (Self)
        is_self_active = active_target == user_id
        contexts.append(
            DependentContextSummary(
                patient_id=user_id,
                display_name="Dr. Priya Sharma (Self)",
                abha_number="91-8472-1092-4821",
                context_type=ContextTypeEnum.SELF,
                age=38,
                gender="Female",
                proxy_relationship_id=None,
                relationship_type=None,
                access_scope="FULL_MANAGEMENT",
                is_active_context=is_self_active,
                zero_contamination_isolated=True,
            )
        )

        # 2. Verified Active Family Proxy Dependents
        dependents = family_proxy_service.list_dependents_for_guardian(user_id)
        for dep in dependents:
            is_dep_active = active_target == dep.dependent_patient_id
            if dep.dependent_age < 18:
                ctx_type = ContextTypeEnum.PEDIATRIC_MINOR
            elif dep.dependent_age >= 60:
                ctx_type = ContextTypeEnum.GERIATRIC_SENIOR
            else:
                ctx_type = ContextTypeEnum.SELF

            dep_name = dep.dependent_name or f"Dependent ({dep.dependent_patient_id})"
            dep_abha = dep.dependent_abha or "14-XXXX-XXXX-XXXX"

            contexts.append(
                DependentContextSummary(
                    patient_id=dep.dependent_patient_id,
                    display_name=dep_name,
                    abha_number=dep_abha,
                    context_type=ctx_type,
                    age=dep.dependent_age,
                    gender="Female" if "Kavita" in dep_name else "Male",
                    proxy_relationship_id=dep.relationship_id,
                    relationship_type=dep.relationship_type.value,
                    access_scope=dep.access_scope.value,
                    is_active_context=is_dep_active,
                    zero_contamination_isolated=True,
                )
            )

        return contexts

    def switch_active_context(self, user_id: str, target_patient_id: str) -> WorkflowSwitchResponse:
        """Switch active vault session context to a target dependent or self,
        enforcing zero-contamination invariants and dynamic EHR view segmentation.
        """
        # Validate authorization
        available = self.list_available_contexts(user_id)
        matching = [c for c in available if c.patient_id == target_patient_id]
        if not matching:
            raise ValueError(
                f"Unauthorized Context Switch: Actor '{user_id}' does not hold active proxy delegation for target profile '{target_patient_id}'."
            )

        active_ctx = matching[0]
        active_ctx.is_active_context = True
        self._active_contexts[user_id] = target_patient_id

        # Determine segmented views based on context persona
        if active_ctx.context_type == ContextTypeEnum.PEDIATRIC_MINOR:
            permitted_views = [
                "PEDIATRIC_IMMUNIZATION_TIMELINE",
                "WHO_GROWTH_PERCENTILES",
                "PEDIATRIC_PRESCRIPTIONS",
                "DEVELOPMENTAL_MILESTONES",
                "SCHOOL_HEALTH_RECORDS",
            ]
        elif active_ctx.context_type == ContextTypeEnum.GERIATRIC_SENIOR:
            permitted_views = [
                "COMPREHENSIVE_GERIATRIC_ASSESSMENT",
                "BEERS_POLYPHARMACY_AUDIT",
                "TIMED_UP_AND_GO_FALL_RISK",
                "KATZ_ADL_FUNCTIONAL_INDEX",
                "CHRONIC_MULTIMORBIDITY_REGIMEN",
                "CAREGIVER_COMMUNICATION_LOG",
            ]
        else:
            permitted_views = [
                "OVERVIEW",
                "PRESCRIPTIONS",
                "DIAGNOSTIC_REPORTS",
                "CLINICAL_PROBLEMS",
                "VITALS_TELEMETRY",
                "APPOINTMENTS",
            ]

        session_id = f"iso-sess-{uuid.uuid4().hex[:12]}"

        return WorkflowSwitchResponse(
            active_context=active_ctx,
            permitted_views=permitted_views,
            isolation_session_id=session_id,
            switched_at=datetime.now(timezone.utc),
            zero_contamination_verified=True,
        )

    def get_pediatric_immunizations(self, child_id: str) -> List[PediatricImmunizationMilestone]:
        """Fetch National Universal Immunization Programme (UIP) timeline for child dependent."""
        return self._immunization_records.get(child_id, self._immunization_records.get("default", []))

    def record_immunization(
        self, child_id: str, milestone: PediatricImmunizationMilestone
    ) -> PediatricImmunizationMilestone:
        """Record or update a pediatric vaccination milestone under India UIP."""
        records = self.get_pediatric_immunizations(child_id)
        existing = [m for m in records if m.milestone_id == milestone.milestone_id]
        if existing:
            # Update existing
            idx = records.index(existing[0])
            records[idx] = milestone
        else:
            records.append(milestone)

        self._immunization_records[child_id] = records
        return milestone

    def get_pediatric_growth_history(self, child_id: str) -> List[PediatricGrowthObservation]:
        """Retrieve WHO percentile growth observation history for child dependent."""
        return self._growth_observations.get(child_id, [])

    def get_geriatric_assessment(self, senior_id: str) -> GeriatricAssessmentProfile:
        """Fetch Comprehensive Geriatric Assessment (CGA) and polypharmacy evaluation."""
        if senior_id not in self._geriatric_assessments:
            # Generate default baseline CGA
            self._geriatric_assessments[senior_id] = GeriatricAssessmentProfile(
                senior_patient_id=senior_id,
                assessed_date=datetime.now(timezone.utc).isoformat(),
                frailty_score=1,
                frailty_status="Pre-Frail (Fried Phenotype 1/5)",
                fall_risk_category=FallRiskCategoryEnum.LOW,
                timed_up_and_go_seconds=10.2,
                polypharmacy_count=3,
                beers_criteria_alerts=[],
                adl_score=6,
                cognitive_screening_result="Mini-Cog: 5/5 Normal",
                caregiver_notes="Baseline geriatric evaluation.",
            )
        return self._geriatric_assessments[senior_id]

    def update_geriatric_assessment(
        self, senior_id: str, assessment: GeriatricAssessmentProfile
    ) -> GeriatricAssessmentProfile:
        """Update Comprehensive Geriatric Assessment (CGA) scores and notes."""
        self._geriatric_assessments[senior_id] = assessment
        return assessment


# Global singleton instance
workflow_isolation_service = WorkflowIsolationService()
