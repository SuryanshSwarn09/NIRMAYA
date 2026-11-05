from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status

from app.core.container_security import get_container_security_headers
from app.schemas.workflow_isolation import (
    DependentContextSummary,
    GeriatricAssessmentProfile,
    PediatricGrowthObservation,
    PediatricImmunizationMilestone,
    WorkflowSwitchRequest,
    WorkflowSwitchResponse,
)
from app.services.workflow_isolation_service import workflow_isolation_service

router = APIRouter(
    prefix="/patients/proxy/workflow",
    tags=["Workflow Isolation & Dependent EHR View Segmentation"],
)


@router.get(
    "/contexts",
    summary="List Available Clinical Vault Contexts",
    description="Enumerates switchable clinical personas for the authenticated user, including personal vault and verified family proxy dependents.",
    response_model=List[DependentContextSummary],
)
async def list_available_contexts(
    response: Response,
    user_id: str = Query("pat-priya-sharma-01", description="Guardian user ID"),
) -> List[DependentContextSummary]:
    """Retrieve switchable patient contexts."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    response.headers["X-Dependent-Context-Isolated"] = "true"

    return workflow_isolation_service.list_available_contexts(user_id)


@router.post(
    "/switch",
    summary="Switch Active Vault Context with Zero-Contamination Enforcement",
    description="Transitions active session context to a target dependent or self, returning isolated EHR view configurations under DPDP Act 2023 Sec 9.",
    response_model=WorkflowSwitchResponse,
)
async def switch_vault_context(
    payload: WorkflowSwitchRequest,
    response: Response,
) -> WorkflowSwitchResponse:
    """Switch active vault session context."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    response.headers["X-Dependent-Context-Isolated"] = "true"

    try:
        return workflow_isolation_service.switch_active_context(
            user_id=payload.requested_by_user_id,
            target_patient_id=payload.target_patient_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/pediatric/{child_id}/immunizations",
    summary="Retrieve National Universal Immunization Programme (UIP) Timeline",
    description="Fetches standard Indian UIP vaccination schedule, administration history, and upcoming milestones for a pediatric dependent.",
    response_model=List[PediatricImmunizationMilestone],
)
async def get_pediatric_immunizations(
    child_id: str,
    response: Response,
) -> List[PediatricImmunizationMilestone]:
    """Fetch pediatric immunization timeline."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    response.headers["X-Dependent-Context-Isolated"] = "true"

    return workflow_isolation_service.get_pediatric_immunizations(child_id)


@router.post(
    "/pediatric/{child_id}/immunizations",
    summary="Record or Update UIP Vaccination Administration",
    description="Logs an administered vaccination dose with batch number and administering facility.",
    response_model=PediatricImmunizationMilestone,
    status_code=status.HTTP_201_CREATED,
)
async def record_pediatric_immunization(
    child_id: str,
    payload: PediatricImmunizationMilestone,
    response: Response,
) -> PediatricImmunizationMilestone:
    """Record vaccination milestone."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    response.headers["X-Dependent-Context-Isolated"] = "true"

    return workflow_isolation_service.record_immunization(child_id, payload)


@router.get(
    "/pediatric/{child_id}/growth",
    summary="Retrieve WHO Percentile Growth Observation History",
    description="Fetches anthropometric growth tracking observations for a child dependent mapped against WHO growth standards.",
    response_model=List[PediatricGrowthObservation],
)
async def get_pediatric_growth_history(
    child_id: str,
    response: Response,
) -> List[PediatricGrowthObservation]:
    """Fetch pediatric growth trajectory."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    response.headers["X-Dependent-Context-Isolated"] = "true"

    return workflow_isolation_service.get_pediatric_growth_history(child_id)


@router.get(
    "/geriatric/{senior_id}/assessment",
    summary="Retrieve Comprehensive Geriatric Assessment (CGA) and Polypharmacy Evaluation",
    description="Fetches multidimensional geriatric evaluation including Beers Criteria drug safety alerts, Timed Up and Go (TUG) fall risk, and Katz ADL scores.",
    response_model=GeriatricAssessmentProfile,
)
async def get_geriatric_assessment(
    senior_id: str,
    response: Response,
) -> GeriatricAssessmentProfile:
    """Fetch comprehensive geriatric assessment."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    response.headers["X-Dependent-Context-Isolated"] = "true"

    return workflow_isolation_service.get_geriatric_assessment(senior_id)


@router.post(
    "/geriatric/{senior_id}/assessment",
    summary="Update Comprehensive Geriatric Assessment and Fall Risk Scoring",
    description="Updates senior clinical evaluation metrics, polypharmacy alerts, and caregiver notes.",
    response_model=GeriatricAssessmentProfile,
)
async def update_geriatric_assessment(
    senior_id: str,
    payload: GeriatricAssessmentProfile,
    response: Response,
) -> GeriatricAssessmentProfile:
    """Update geriatric assessment."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    response.headers["X-Dependent-Context-Isolated"] = "true"

    return workflow_isolation_service.update_geriatric_assessment(senior_id, payload)
