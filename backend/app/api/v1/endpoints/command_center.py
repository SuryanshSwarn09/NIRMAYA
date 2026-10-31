"""FastAPI REST router for District & State Public Health Command Center and Disease Surveillance."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.territorial_rbac import require_territory
from app.schemas.command_center import (
    CommandCenterOverviewResponse,
    DiseaseCategoryEnum,
    DiseaseClusterReport,
    FacilityResourceTelemetry,
    OutbreakSeverityEnum,
    PublicHealthDirectiveCreate,
    PublicHealthDirectiveResponse,
    WorkforceDutyRoster,
)
from app.services.command_center_service import command_center_service

router = APIRouter()


@router.get(
    "/overview",
    response_model=CommandCenterOverviewResponse,
    summary="Get territorial command center overview",
    description="Rolls up total active cases, ICU capacity, available ventilators, and critical outbreak alerts for a sovereign territory.",
)
async def get_command_center_overview(
    jurisdiction_path: str = Query("india.27.492", description="LGD territorial path (e.g. 'india.27.492')"),
    _authorized_scope: str = Depends(require_territory("jurisdiction_path")),
) -> CommandCenterOverviewResponse:
    """Retrieve consolidated command center metrics."""
    return command_center_service.get_overview_metrics(jurisdiction_path)


@router.get(
    "/outbreaks",
    response_model=List[DiseaseClusterReport],
    summary="Query disease surveillance outbreak clusters",
    description="Returns active disease outbreak clusters filtered by territorial jurisdiction, pathogen category, and severity.",
)
async def get_outbreak_clusters(
    jurisdiction_path: str = Query("india.27.492", description="LGD territorial path"),
    severity: Optional[OutbreakSeverityEnum] = Query(None, description="Filter by alert classification"),
    disease_category: Optional[DiseaseCategoryEnum] = Query(None, description="Filter by IDSP disease category"),
    _authorized_scope: str = Depends(require_territory("jurisdiction_path")),
) -> List[DiseaseClusterReport]:
    """Fetch disease surveillance clusters."""
    return command_center_service.get_outbreak_clusters(
        jurisdiction_path=jurisdiction_path,
        severity=severity,
        disease_category=disease_category,
    )


@router.get(
    "/outbreaks/{cluster_id}",
    response_model=DiseaseClusterReport,
    summary="Get disease cluster by UUID",
    description="Fetch single epidemiological outbreak cluster details.",
)
async def get_outbreak_by_id(cluster_id: str) -> DiseaseClusterReport:
    """Fetch disease cluster by ID."""
    record = command_center_service.get_outbreak_by_id(cluster_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disease outbreak cluster '{cluster_id}' not found.",
        )
    return record


@router.get(
    "/icu-beds",
    response_model=List[FacilityResourceTelemetry],
    summary="Critical care and ICU bed availability census",
    description="Returns facility-by-facility ICU, ventilator, and oxygen bed availability, with automated diversion indicators.",
)
async def get_icu_bed_census(
    jurisdiction_path: str = Query("india.27.492", description="LGD territorial path"),
    diverting_only: Optional[bool] = Query(None, description="Filter only institutions under admission diversion (>85%)"),
    _authorized_scope: str = Depends(require_territory("jurisdiction_path")),
) -> List[FacilityResourceTelemetry]:
    """Fetch hospital critical care census."""
    return command_center_service.get_icu_bed_census(
        jurisdiction_path=jurisdiction_path,
        diverting_only=diverting_only,
    )


@router.get(
    "/workforce",
    response_model=WorkforceDutyRoster,
    summary="Healthcare workforce deployment telemetry",
    description="Returns active physician staffing, intensivist coverage, and doctor-to-patient ratio.",
)
async def get_workforce_roster(
    jurisdiction_path: str = Query("india.27.492", description="LGD territorial path"),
    _authorized_scope: str = Depends(require_territory("jurisdiction_path")),
) -> WorkforceDutyRoster:
    """Fetch clinical duty roster."""
    return command_center_service.get_workforce_roster(jurisdiction_path)


@router.post(
    "/directives",
    response_model=PublicHealthDirectiveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue sovereign public health directive",
    description="Dispatches official containment order, hospital diversion advisory, or vector control mandate.",
)
async def issue_health_directive(
    payload: PublicHealthDirectiveCreate,
    _authorized_scope: str = Depends(require_territory("jurisdiction_path")),
) -> PublicHealthDirectiveResponse:
    """Issue public health order."""
    return command_center_service.issue_health_directive(payload)


@router.get(
    "/directives",
    response_model=List[PublicHealthDirectiveResponse],
    summary="List active public health directives",
    description="Returns active containment orders and directives governing a sovereign jurisdiction.",
)
async def list_health_directives(
    jurisdiction_path: str = Query("india.27.492", description="LGD territorial path"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    _authorized_scope: str = Depends(require_territory("jurisdiction_path")),
) -> List[PublicHealthDirectiveResponse]:
    """List directives."""
    return command_center_service.list_health_directives(
        jurisdiction_path=jurisdiction_path,
        is_active=is_active,
    )
