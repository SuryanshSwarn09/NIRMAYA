from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Response, status

from app.core.container_security import get_container_security_headers
from app.schemas.demo import (
    DemoScenario,
    ScenarioExecutionResult,
    SlideDeckMetadata,
)
from app.services.demo_service import demo_service

router = APIRouter(prefix="/demo", tags=["Interactive Guided Demo & Presentation"])


@router.get(
    "/scenarios",
    summary="List All Demonstration Scenarios",
    description="Returns the full catalog of 5 pre-configured, reproducible interactive demonstration scenarios.",
    response_model=List[DemoScenario],
)
async def list_demonstration_scenarios(response: Response) -> List[DemoScenario]:
    """Retrieve catalog of all guided demonstration scenarios."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return demo_service.list_scenarios()


@router.get(
    "/scenarios/{scenario_id}",
    summary="Get Demonstration Scenario Details",
    description="Returns step-by-step definition, prerequisites, and expected telemetry for a specific scenario.",
    response_model=DemoScenario,
)
async def get_demonstration_scenario(scenario_id: str, response: Response) -> DemoScenario:
    """Retrieve details of a specific demonstration scenario by identifier."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    scenario = demo_service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demonstration scenario '{scenario_id}' not found",
        )
    return scenario


@router.post(
    "/scenarios/{scenario_id}/execute",
    summary="Execute Live Demonstration Scenario",
    description="Triggers reproducible execution of a demonstration scenario, generating cryptographic proofs and live telemetry.",
    response_model=ScenarioExecutionResult,
)
async def execute_demonstration_scenario(scenario_id: str, response: Response) -> ScenarioExecutionResult:
    """Execute all atomic steps of a scenario and return verification assertions."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    try:
        return demo_service.execute_scenario(scenario_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demonstration scenario '{scenario_id}' not found",
        )


@router.post(
    "/reset",
    summary="Reset Demonstration Sandbox State",
    description="Restores the demonstration sandbox environment to a clean, reproducible initial baseline.",
    response_model=Dict[str, Any],
)
async def reset_sandbox_state(response: Response) -> Dict[str, Any]:
    """Reset demonstration sandbox environment."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return demo_service.reset_sandbox_state()


@router.get(
    "/slides",
    summary="Get Capstone Defense Presentation Deck",
    description="Returns structured 12-slide comprehensive defense presentation deck with ASCII architecture diagrams.",
    response_model=SlideDeckMetadata,
)
async def get_presentation_slide_deck(response: Response) -> SlideDeckMetadata:
    """Retrieve structured presentation slide deck metadata and slides."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return demo_service.get_slide_deck()
