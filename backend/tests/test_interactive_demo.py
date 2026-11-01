import pytest
from httpx import AsyncClient

from app.schemas.demo import (
    DemoScenario,
    ScenarioCategoryEnum,
    ScenarioExecutionResult,
    ScenarioExecutionStatus,
    ScenarioStep,
    SlideDeckMetadata,
    SlideItem,
)
from app.services.demo_service import DemoService, demo_service


# =============================================================================
# Unit Tests: Pydantic Schemas & Data Structures
# =============================================================================

def test_demo_schemas_instantiation():
    """Verify validation and serialization of demo schemas."""
    step = ScenarioStep(
        step_number=1,
        title="Test Step",
        description="Testing step execution",
        subsystem="Test Subsystem",
        expected_duration_ms=5.0,
    )
    assert step.step_number == 1
    assert step.expected_duration_ms == 5.0

    scenario = DemoScenario(
        scenario_id="SCEN-TEST",
        title="Test Scenario",
        subtitle="Testing scenario execution",
        category=ScenarioCategoryEnum.CLINICAL_WORKFLOW,
        prerequisites=["Prereq 1"],
        steps=[step],
        sla_target_ms=50.0,
    )
    assert scenario.status == ScenarioExecutionStatus.READY
    assert len(scenario.steps) == 1

    slide = SlideItem(
        slide_number=1,
        title="Test Slide",
        subtitle="Subtitle",
        bullets=["Bullet 1", "Bullet 2"],
        key_metrics={"Metric": "100%"},
    )
    assert slide.slide_number == 1
    assert len(slide.bullets) == 2


# =============================================================================
# Unit Tests: Service Catalog, Scenario Execution & State Reset
# =============================================================================

def test_demo_service_list_and_get_scenarios():
    """Verify scenario catalog integrity and individual retrieval."""
    scenarios = demo_service.list_scenarios()
    assert len(scenarios) == 5

    scenario_ids = [s.scenario_id for s in scenarios]
    assert "SCEN-01-CONSULTATION" in scenario_ids
    assert "SCEN-02-BTG-VAULT" in scenario_ids
    assert "SCEN-03-EDGE-SYNC" in scenario_ids
    assert "SCEN-04-SQLMED-FEDERATION" in scenario_ids
    assert "SCEN-05-IDSP-COMMAND" in scenario_ids

    scen1 = demo_service.get_scenario("SCEN-01-CONSULTATION")
    assert scen1 is not None
    assert scen1.category == ScenarioCategoryEnum.CLINICAL_WORKFLOW
    assert len(scen1.steps) == 5

    assert demo_service.get_scenario("NON_EXISTENT") is None


def test_execute_consultation_scenario():
    """Verify execution of Scenario 1: Citizen Consultation & ABDM Linkage."""
    res = demo_service.execute_scenario("SCEN-01-CONSULTATION")
    assert res.status == ScenarioExecutionStatus.SUCCESS
    assert res.steps_completed == 5
    assert res.total_steps == 5
    assert res.elapsed_ms > 0
    assert any("Verhoeff" in a for a in res.assertions_verified)
    assert any("Merkle" in p for p in res.cryptographic_proofs)
    assert res.live_telemetry.get("abdm_care_context") == "CC-2026-OPD-9104"


def test_execute_btg_vault_scenario():
    """Verify execution of Scenario 2: Emergency Break-The-Glass Vault Access."""
    res = demo_service.execute_scenario("SCEN-02-BTG-VAULT")
    assert res.status == ScenarioExecutionStatus.SUCCESS
    assert res.steps_completed == 5
    assert any("Argon2id" in p for p in res.cryptographic_proofs)
    assert any("AES-256-GCM" in a for a in res.assertions_verified)
    assert any("SMS alert" in a for a in res.assertions_verified)


def test_execute_edge_sync_scenario():
    """Verify execution of Scenario 3: Rural Edge Node & Offline Sync."""
    res = demo_service.execute_scenario("SCEN-03-EDGE-SYNC")
    assert res.status == ScenarioExecutionStatus.SUCCESS
    assert res.steps_completed == 5
    assert any("vector clock" in a.lower() for a in res.assertions_verified)
    assert res.live_telemetry.get("data_loss_rate") == 0.0


def test_execute_sqlmed_federation_scenario():
    """Verify execution of Scenario 4: Legacy HIS Read-Only Federation."""
    res = demo_service.execute_scenario("SCEN-04-SQLMED-FEDERATION")
    assert res.status == ScenarioExecutionStatus.SUCCESS
    assert res.steps_completed == 5
    assert any("postgres_fdw" in a for a in res.assertions_verified)
    assert any("FHIR" in a for a in res.assertions_verified)
    assert res.live_telemetry.get("cache_hit_rate") == "98.4%"


def test_execute_idsp_command_scenario():
    """Verify execution of Scenario 5: Public Health Command Center & Surveillance."""
    res = demo_service.execute_scenario("SCEN-05-IDSP-COMMAND")
    assert res.status == ScenarioExecutionStatus.SUCCESS
    assert res.steps_completed == 5
    assert any("ltree" in a for a in res.assertions_verified)
    assert any("Rt = 1.34" in a for a in res.assertions_verified)
    assert any("Scoped TRBAC" in p for p in res.cryptographic_proofs)


def test_execute_invalid_scenario_raises_key_error():
    """Verify executing invalid scenario raises KeyError."""
    with pytest.raises(KeyError):
        demo_service.execute_scenario("NON_EXISTENT_SCENARIO")


def test_reset_sandbox_state():
    """Verify sandbox reset endpoint returns clean confirmation."""
    result = demo_service.reset_sandbox_state()
    assert result["status"] == "RESET_SUCCESSFUL"
    assert result["scenarios_reset"] == 5


def test_slide_deck_structure_and_counts():
    """Verify 12-slide comprehensive presentation deck metadata and contents."""
    deck = demo_service.get_slide_deck()
    assert deck.total_slides == 12
    assert len(deck.slides) == 12

    for idx, slide in enumerate(deck.slides, start=1):
        assert slide.slide_number == idx
        assert len(slide.title) > 0
        assert len(slide.bullets) >= 3


# =============================================================================
# Integration Tests: FastAPI REST API Endpoints
# =============================================================================

async def test_api_list_demonstration_scenarios(client: AsyncClient):
    """Verify GET /api/v1/demo/scenarios endpoint."""
    resp = await client.get("/api/v1/demo/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    assert "x-frame-options" in resp.headers


async def test_api_get_demonstration_scenario(client: AsyncClient):
    """Verify GET /api/v1/demo/scenarios/{id} with valid and invalid IDs."""
    resp = await client.get("/api/v1/demo/scenarios/SCEN-01-CONSULTATION")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario_id"] == "SCEN-01-CONSULTATION"
    assert len(data["steps"]) == 5

    # 404 test
    resp_404 = await client.get("/api/v1/demo/scenarios/UNKNOWN-SCENARIO")
    assert resp_404.status_code == 404


async def test_api_execute_demonstration_scenario(client: AsyncClient):
    """Verify POST /api/v1/demo/scenarios/{id}/execute with valid and invalid IDs."""
    resp = await client.post("/api/v1/demo/scenarios/SCEN-01-CONSULTATION/execute")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["steps_completed"] == 5
    assert len(data["assertions_verified"]) > 0

    # 404 test
    resp_404 = await client.post("/api/v1/demo/scenarios/UNKNOWN-SCENARIO/execute")
    assert resp_404.status_code == 404


async def test_api_reset_sandbox_state(client: AsyncClient):
    """Verify POST /api/v1/demo/reset endpoint."""
    resp = await client.post("/api/v1/demo/reset")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "RESET_SUCCESSFUL"


async def test_api_get_presentation_slide_deck(client: AsyncClient):
    """Verify GET /api/v1/demo/slides endpoint."""
    resp = await client.get("/api/v1/demo/slides")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_slides"] == 12
    assert len(data["slides"]) == 12
    assert "x-process-uid" in resp.headers


def test_demo_scenario_subsystem_coverage():
    """Verify all scenarios have complete subsystem mappings and non-empty telemetry."""
    scenarios = demo_service.list_scenarios()
    for s in scenarios:
        assert len(s.steps) >= 5
        assert s.sla_target_ms > 0
        for step in s.steps:
            assert len(step.subsystem) > 0
            assert isinstance(step.telemetry_output, dict)
            assert len(step.telemetry_output) > 0


async def test_api_execute_all_scenarios_integration(client: AsyncClient):
    """Verify that every catalog scenario can be executed through the API with 200 OK."""
    list_resp = await client.get("/api/v1/demo/scenarios")
    scenarios = list_resp.json()
    for item in scenarios:
        exec_resp = await client.post(f"/api/v1/demo/scenarios/{item['scenario_id']}/execute")
        assert exec_resp.status_code == 200
        result = exec_resp.json()
        assert result["status"] == "SUCCESS"
        assert result["steps_completed"] == 5

