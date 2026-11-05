import os
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport
from pydantic import ValidationError

from app.main import app
from app.schemas.workflow_isolation import (
    ContextTypeEnum,
    VaccinationStatusEnum,
    NutritionalStatusEnum,
    FallRiskCategoryEnum,
    DependentContextSummary,
    PediatricImmunizationMilestone,
    PediatricGrowthObservation,
    GeriatricAssessmentProfile,
    WorkflowSwitchRequest,
    WorkflowSwitchResponse,
)
from app.services.workflow_isolation_service import (
    WorkflowIsolationService,
    workflow_isolation_service,
)
from app.services.family_proxy_service import family_proxy_service
from app.schemas.family_proxy import (
    FamilyProxyResponse,
    ProxyAccessScopeEnum,
    ProxyRelationshipStatusEnum,
    RelationshipTypeEnum,
    VerificationAuthorityEnum,
)


@pytest.fixture(autouse=True)
def setup_workflow_test_proxies():
    """Ensure active proxy relationships exist for test guardian."""
    rel1 = FamilyProxyResponse(
        relationship_id="rel-proxy-child-001",
        guardian_patient_id="pat-priya-sharma-01",
        dependent_patient_id="pat-aarav-sharma-02",
        relationship_type=RelationshipTypeEnum.CHILD_MINOR,
        verification_tier=VerificationAuthorityEnum.DIGILOCKER_BIRTH_CERTIFICATE,
        verification_document_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
        status=ProxyRelationshipStatusEnum.ACTIVE,
        authorized_at=datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
        dependent_name="Aarav Sharma",
        dependent_abha="14-8291-0391-4821",
        dependent_age=8,
        zero_contamination_isolated=True,
    )
    family_proxy_service._relationships[rel1.relationship_id] = rel1

    rel2 = FamilyProxyResponse(
        relationship_id="rel-proxy-senior-002",
        guardian_patient_id="pat-priya-sharma-01",
        dependent_patient_id="pat-kavita-sharma-03",
        relationship_type=RelationshipTypeEnum.PARENT_SENIOR,
        verification_tier=VerificationAuthorityEnum.AADHAAR_DEMOGRAPHIC_EKYC,
        verification_document_hash="a192840192840192840192840192840192840192840192840192840192840192",
        access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
        status=ProxyRelationshipStatusEnum.ACTIVE,
        authorized_at=datetime(2026, 9, 15, 11, 30, 0, tzinfo=timezone.utc),
        dependent_name="Kavita Sharma",
        dependent_abha="14-9102-4819-2041",
        dependent_age=68,
        zero_contamination_isolated=True,
    )
    family_proxy_service._relationships[rel2.relationship_id] = rel2
    yield


# =============================================================================
# 1. Schema & Enum Validation Tests
# =============================================================================

def test_context_type_enum():
    """Verify supported workflow isolation persona contexts."""
    assert ContextTypeEnum.SELF.value == "SELF"
    assert ContextTypeEnum.PEDIATRIC_MINOR.value == "PEDIATRIC_MINOR"
    assert ContextTypeEnum.GERIATRIC_SENIOR.value == "GERIATRIC_SENIOR"


def test_vaccination_status_enum():
    """Verify UIP vaccination milestone lifecycle states."""
    assert VaccinationStatusEnum.ADMINISTERED.value == "ADMINISTERED"
    assert VaccinationStatusEnum.SCHEDULED.value == "SCHEDULED"
    assert VaccinationStatusEnum.OVERDUE.value == "OVERDUE"


def test_nutritional_status_enum():
    """Verify WHO growth nutritional categories."""
    assert NutritionalStatusEnum.NORMAL.value == "NORMAL"
    assert NutritionalStatusEnum.MODERATE_WASTING.value == "MODERATE_WASTING"
    assert NutritionalStatusEnum.SEVERE_WASTING.value == "SEVERE_WASTING"
    assert NutritionalStatusEnum.STUNTING.value == "STUNTING"
    assert NutritionalStatusEnum.OVERWEIGHT.value == "OVERWEIGHT"


def test_fall_risk_category_enum():
    """Verify Timed Up and Go (TUG) fall risk severity grades."""
    assert FallRiskCategoryEnum.LOW.value == "LOW"
    assert FallRiskCategoryEnum.MODERATE.value == "MODERATE"
    assert FallRiskCategoryEnum.HIGH.value == "HIGH"


def test_schema_dependent_context_summary_valid():
    """Verify valid DependentContextSummary serialization."""
    summary = DependentContextSummary(
        patient_id="pat-child-01",
        display_name="Aarav Sharma",
        abha_number="14-8291-0391-4821",
        context_type=ContextTypeEnum.PEDIATRIC_MINOR,
        age=8,
        gender="Male",
        proxy_relationship_id="rel-01",
        relationship_type="CHILD_MINOR",
        access_scope="FULL_MANAGEMENT",
        is_active_context=True,
    )
    assert summary.patient_id == "pat-child-01"
    assert summary.context_type == ContextTypeEnum.PEDIATRIC_MINOR
    assert summary.zero_contamination_isolated is True


def test_schema_pediatric_milestone_valid():
    """Verify PediatricImmunizationMilestone attributes."""
    milestone = PediatricImmunizationMilestone(
        milestone_id="uip-bcg-01",
        vaccine_code="BCG",
        vaccine_name="Bacillus Calmette-Guerin",
        target_age_display="At Birth",
        status=VaccinationStatusEnum.ADMINISTERED,
        dose_number=1,
        administered_date="2018-06-15",
        batch_number="SII-BCG-9021",
    )
    assert milestone.vaccine_code == "BCG"
    assert milestone.status == VaccinationStatusEnum.ADMINISTERED


def test_schema_pediatric_growth_observation_valid():
    """Verify PediatricGrowthObservation mapping to WHO percentiles."""
    obs = PediatricGrowthObservation(
        observation_id="gro-01",
        child_patient_id="pat-child-01",
        age_months=24,
        recorded_date="2020-06-15",
        weight_kg=12.2,
        height_cm=87.2,
        head_circumference_cm=48.2,
        who_weight_percentile=50,
        who_height_percentile=53,
        nutritional_status=NutritionalStatusEnum.NORMAL,
    )
    assert obs.weight_kg == 12.2
    assert obs.who_weight_percentile == 50


def test_schema_pediatric_growth_observation_bounds():
    """Verify validation failure when percentiles violate [1, 99] bounds."""
    with pytest.raises(ValidationError):
        PediatricGrowthObservation(
            observation_id="gro-02",
            child_patient_id="pat-child-01",
            age_months=24,
            recorded_date="2020-06-15",
            weight_kg=12.2,
            height_cm=87.2,
            who_weight_percentile=105,  # Out of range!
            who_height_percentile=53,
            nutritional_status=NutritionalStatusEnum.NORMAL,
        )


def test_schema_geriatric_assessment_profile_valid():
    """Verify GeriatricAssessmentProfile with Beers warnings and ADL index."""
    profile = GeriatricAssessmentProfile(
        senior_patient_id="pat-senior-01",
        assessed_date="2026-10-18T10:30:00Z",
        frailty_score=2,
        frailty_status="Pre-Frail",
        fall_risk_category=FallRiskCategoryEnum.MODERATE,
        timed_up_and_go_seconds=13.8,
        polypharmacy_count=5,
        beers_criteria_alerts=[{"medication": "Pantoprazole", "severity": "CAUTION"}],
        adl_score=5,
        cognitive_screening_result="Mini-Cog 4/5 Normal",
    )
    assert profile.frailty_score == 2
    assert profile.adl_score == 5
    assert len(profile.beers_criteria_alerts) == 1


def test_schema_geriatric_assessment_bounds():
    """Verify validation failure when frailty score > 5 or ADL > 6."""
    with pytest.raises(ValidationError):
        GeriatricAssessmentProfile(
            senior_patient_id="pat-senior-01",
            assessed_date="2026-10-18T10:30:00Z",
            frailty_score=7,  # Above max 5!
            frailty_status="Severe",
            fall_risk_category=FallRiskCategoryEnum.HIGH,
            timed_up_and_go_seconds=22.0,
            polypharmacy_count=8,
            adl_score=6,
            cognitive_screening_result="Abnormal",
        )


# =============================================================================
# 2. Service Unit Tests
# =============================================================================

def test_service_list_available_contexts_includes_self_and_dependents():
    """Verify list_available_contexts returns primary self persona and authorized dependents."""
    service = WorkflowIsolationService()
    contexts = service.list_available_contexts(user_id="pat-priya-sharma-01")

    assert len(contexts) >= 3
    # Check self
    self_ctx = [c for c in contexts if c.context_type == ContextTypeEnum.SELF]
    assert len(self_ctx) == 1
    assert "Self" in self_ctx[0].display_name

    # Check pediatric dependent
    ped_ctx = [c for c in contexts if c.context_type == ContextTypeEnum.PEDIATRIC_MINOR]
    assert len(ped_ctx) >= 1
    assert ped_ctx[0].age < 18

    # Check geriatric dependent
    ger_ctx = [c for c in contexts if c.context_type == ContextTypeEnum.GERIATRIC_SENIOR]
    assert len(ger_ctx) >= 1
    assert ger_ctx[0].age >= 60


def test_service_switch_to_pediatric_context_success():
    """Verify switching to pediatric dependent segments EHR views correctly."""
    service = WorkflowIsolationService()
    res = service.switch_active_context(
        user_id="pat-priya-sharma-01",
        target_patient_id="pat-aarav-sharma-02",
    )

    assert res.active_context.patient_id == "pat-aarav-sharma-02"
    assert res.active_context.context_type == ContextTypeEnum.PEDIATRIC_MINOR
    assert "PEDIATRIC_IMMUNIZATION_TIMELINE" in res.permitted_views
    assert "WHO_GROWTH_PERCENTILES" in res.permitted_views
    assert res.isolation_session_id.startswith("iso-sess-")
    assert res.zero_contamination_verified is True


def test_service_switch_to_geriatric_context_success():
    """Verify switching to geriatric dependent segments EHR views correctly."""
    service = WorkflowIsolationService()
    res = service.switch_active_context(
        user_id="pat-priya-sharma-01",
        target_patient_id="pat-kavita-sharma-03",
    )

    assert res.active_context.patient_id == "pat-kavita-sharma-03"
    assert res.active_context.context_type == ContextTypeEnum.GERIATRIC_SENIOR
    assert "COMPREHENSIVE_GERIATRIC_ASSESSMENT" in res.permitted_views
    assert "BEERS_POLYPHARMACY_AUDIT" in res.permitted_views
    assert "TIMED_UP_AND_GO_FALL_RISK" in res.permitted_views


def test_service_switch_to_self_success():
    """Verify switching to personal vault context returns standard adult views."""
    service = WorkflowIsolationService()
    res = service.switch_active_context(
        user_id="pat-priya-sharma-01",
        target_patient_id="pat-priya-sharma-01",
    )

    assert res.active_context.context_type == ContextTypeEnum.SELF
    assert "OVERVIEW" in res.permitted_views
    assert "PRESCRIPTIONS" in res.permitted_views
    assert "VITALS_TELEMETRY" in res.permitted_views


def test_service_switch_to_unauthorized_dependent_fails():
    """Verify switching to an unlinked patient profile raises ValueError."""
    service = WorkflowIsolationService()
    with pytest.raises(ValueError, match="Unauthorized Context Switch"):
        service.switch_active_context(
            user_id="pat-priya-sharma-01",
            target_patient_id="pat-stranger-99",
        )


def test_service_get_pediatric_immunizations():
    """Verify retrieval of Universal Immunization Programme (UIP) schedule."""
    service = WorkflowIsolationService()
    milestones = service.get_pediatric_immunizations("pat-aarav-sharma-02")

    assert len(milestones) >= 10
    bcg = [m for m in milestones if m.vaccine_code == "BCG"][0]
    assert bcg.status == VaccinationStatusEnum.ADMINISTERED
    assert bcg.dose_number == 1
    assert "AIIMS" in bcg.administered_facility


def test_service_record_immunization_dose():
    """Verify recording of a newly administered vaccine milestone."""
    service = WorkflowIsolationService()
    new_dose = PediatricImmunizationMilestone(
        milestone_id="uip-custom-je",
        vaccine_code="JE-2",
        vaccine_name="Japanese Encephalitis Dose 2",
        target_age_display="16-24 Months",
        status=VaccinationStatusEnum.ADMINISTERED,
        dose_number=2,
        administered_date="2020-02-10",
        administered_facility="Fortis Pediatric Center",
        batch_number="SII-JE-9102",
    )

    saved = service.record_immunization("pat-aarav-sharma-02", new_dose)
    assert saved.vaccine_code == "JE-2"
    assert saved.status == VaccinationStatusEnum.ADMINISTERED

    updated_list = service.get_pediatric_immunizations("pat-aarav-sharma-02")
    assert any(m.vaccine_code == "JE-2" for m in updated_list)


def test_service_get_pediatric_growth_history():
    """Verify retrieval of WHO growth percentile observations."""
    service = WorkflowIsolationService()
    growth_history = service.get_pediatric_growth_history("pat-aarav-sharma-02")

    assert len(growth_history) == 4
    obs_48m = growth_history[-1]
    assert obs_48m.age_months == 48
    assert obs_48m.weight_kg == 16.3
    assert obs_48m.who_weight_percentile == 55


def test_service_get_geriatric_assessment():
    """Verify Comprehensive Geriatric Assessment retrieval."""
    service = WorkflowIsolationService()
    cga = service.get_geriatric_assessment("pat-kavita-sharma-03")

    assert cga.senior_patient_id == "pat-kavita-sharma-03"
    assert cga.frailty_score == 2
    assert cga.fall_risk_category == FallRiskCategoryEnum.MODERATE
    assert cga.timed_up_and_go_seconds == 13.8
    assert len(cga.beers_criteria_alerts) == 2


def test_service_update_geriatric_assessment():
    """Verify updating geriatric clinical metrics."""
    service = WorkflowIsolationService()
    current = service.get_geriatric_assessment("pat-kavita-sharma-03")
    current.timed_up_and_go_seconds = 12.1
    current.caregiver_notes = "Mobility improved following physical therapy."

    updated = service.update_geriatric_assessment("pat-kavita-sharma-03", current)
    assert updated.timed_up_and_go_seconds == 12.1
    assert "physical therapy" in updated.caregiver_notes


# =============================================================================
# 3. FastAPI REST Endpoint Tests
# =============================================================================

@pytest.mark.asyncio
async def test_api_list_available_contexts():
    """Test GET /api/v1/patients/proxy/workflow/contexts endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(
            "/api/v1/patients/proxy/workflow/contexts",
            params={"user_id": "pat-priya-sharma-01"},
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        assert any(c["context_type"] == "PEDIATRIC_MINOR" for c in data)
        assert any(c["context_type"] == "GERIATRIC_SENIOR" for c in data)


@pytest.mark.asyncio
async def test_api_switch_context_to_pediatric():
    """Test POST /api/v1/patients/proxy/workflow/switch to child minor."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/patients/proxy/workflow/switch",
            json={
                "requested_by_user_id": "pat-priya-sharma-01",
                "target_patient_id": "pat-aarav-sharma-02",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["active_context"]["context_type"] == "PEDIATRIC_MINOR"
        assert "PEDIATRIC_IMMUNIZATION_TIMELINE" in data["permitted_views"]
        assert data["zero_contamination_verified"] is True


@pytest.mark.asyncio
async def test_api_switch_context_to_geriatric():
    """Test POST /api/v1/patients/proxy/workflow/switch to senior parent."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/patients/proxy/workflow/switch",
            json={
                "requested_by_user_id": "pat-priya-sharma-01",
                "target_patient_id": "pat-kavita-sharma-03",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["active_context"]["context_type"] == "GERIATRIC_SENIOR"
        assert "COMPREHENSIVE_GERIATRIC_ASSESSMENT" in data["permitted_views"]


@pytest.mark.asyncio
async def test_api_switch_context_unauthorized_fails():
    """Test POST /api/v1/patients/proxy/workflow/switch rejects unauthorized patient."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/patients/proxy/workflow/switch",
            json={
                "requested_by_user_id": "pat-priya-sharma-01",
                "target_patient_id": "pat-stranger-99",
            },
        )
        assert res.status_code == 400
        data = res.json()
        error_msg = data.get("message") or data.get("detail", "")
        assert "Unauthorized Context Switch" in error_msg


@pytest.mark.asyncio
async def test_api_get_pediatric_immunizations():
    """Test GET /api/v1/patients/proxy/workflow/pediatric/{child_id}/immunizations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patients/proxy/workflow/pediatric/pat-aarav-sharma-02/immunizations")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 10
        assert data[0]["vaccine_code"] == "BCG"


@pytest.mark.asyncio
async def test_api_record_pediatric_immunization():
    """Test POST /api/v1/patients/proxy/workflow/pediatric/{child_id}/immunizations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/patients/proxy/workflow/pediatric/pat-aarav-sharma-02/immunizations",
            json={
                "milestone_id": "uip-test-dose-01",
                "vaccine_code": "PCV-BOOSTER",
                "vaccine_name": "Pneumococcal Conjugate Booster",
                "target_age_display": "9 Months",
                "status": "ADMINISTERED",
                "dose_number": 1,
                "administered_date": "2019-03-20",
                "administered_facility": "AIIMS New Delhi",
                "batch_number": "SII-PCV-8120",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["vaccine_code"] == "PCV-BOOSTER"
        assert data["status"] == "ADMINISTERED"


@pytest.mark.asyncio
async def test_api_get_pediatric_growth_history():
    """Test GET /api/v1/patients/proxy/workflow/pediatric/{child_id}/growth."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patients/proxy/workflow/pediatric/pat-aarav-sharma-02/growth")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "who_weight_percentile" in data[0]


@pytest.mark.asyncio
async def test_api_get_geriatric_assessment():
    """Test GET /api/v1/patients/proxy/workflow/geriatric/{senior_id}/assessment."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patients/proxy/workflow/geriatric/pat-kavita-sharma-03/assessment")
        assert res.status_code == 200
        data = res.json()
        assert data["frailty_score"] == 2
        assert data["fall_risk_category"] == "MODERATE"
        assert len(data["beers_criteria_alerts"]) >= 1


@pytest.mark.asyncio
async def test_api_update_geriatric_assessment():
    """Test POST /api/v1/patients/proxy/workflow/geriatric/{senior_id}/assessment."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/patients/proxy/workflow/geriatric/pat-kavita-sharma-03/assessment",
            json={
                "senior_patient_id": "pat-kavita-sharma-03",
                "assessed_date": "2026-11-05T10:00:00Z",
                "frailty_score": 1,
                "frailty_status": "Pre-Frail (Fried Phenotype 1/5)",
                "fall_risk_category": "LOW",
                "timed_up_and_go_seconds": 10.5,
                "polypharmacy_count": 4,
                "beers_criteria_alerts": [],
                "adl_score": 6,
                "cognitive_screening_result": "Mini-Cog: 5/5 Normal",
                "caregiver_notes": "Senior recovered full unassisted mobility.",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["frailty_score"] == 1
        assert data["fall_risk_category"] == "LOW"
        assert data["adl_score"] == 6
