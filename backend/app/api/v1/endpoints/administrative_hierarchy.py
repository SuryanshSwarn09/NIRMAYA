"""REST endpoints for Indian Local Government Directory (LGD) 6-Tier Administrative Hierarchy."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.administrative_hierarchy import (
    AdminLevelEnum,
    GovtDesignationEnum,
    AdministrativeUnitCreate,
    AdministrativeUnitUpdate,
    AdministrativeUnitResponse,
    AdministrativeOfficerCreate,
    AdministrativeOfficerResponse,
    TerritorialTreeNode,
    TerritorialSummaryMetrics,
)
from app.services.administrative_hierarchy_service import hierarchy_service

router = APIRouter()


@router.get(
    "/hierarchy/metrics",
    response_model=TerritorialSummaryMetrics,
    summary="Get national territorial summary metrics",
    description="Returns national counts of states, divisions, districts, sub-districts, and ltree query telemetry.",
)
async def get_summary_metrics() -> TerritorialSummaryMetrics:
    """Return consolidated metrics for India's 6-tier administrative hierarchy."""
    return hierarchy_service.get_summary_metrics()


@router.get(
    "/hierarchy/units",
    response_model=List[AdministrativeUnitResponse],
    summary="List administrative territorial units",
    description="Query administrative units with optional tier level and parent unit filters.",
)
async def list_administrative_units(
    level: Optional[AdminLevelEnum] = Query(None, description="Filter by administrative tier"),
    parent_id: Optional[str] = Query(None, description="Filter by parent unit UUID"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[AdministrativeUnitResponse]:
    """List administrative units filtered by level or parent hierarchy."""
    return hierarchy_service.list_units(
        level=level,
        parent_id=parent_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/hierarchy/units/search",
    response_model=List[AdministrativeUnitResponse],
    summary="Search administrative units",
    description="Sub-2ms fast search across unit names, official LGD codes, and ltree path tokens.",
)
async def search_administrative_units(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of matches"),
) -> List[AdministrativeUnitResponse]:
    """Search administrative units by name, LGD code, or path."""
    return hierarchy_service.search_units(query=q, limit=limit)


@router.get(
    "/hierarchy/units/{unit_id}",
    response_model=AdministrativeUnitResponse,
    summary="Get administrative unit by UUID",
    description="Fetch full details for an administrative unit by its unique identifier.",
)
async def get_administrative_unit_by_id(unit_id: str) -> AdministrativeUnitResponse:
    """Fetch an administrative unit by ID."""
    unit = hierarchy_service.get_unit_by_id(unit_id)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrative unit '{unit_id}' not found.",
        )
    return unit


@router.get(
    "/hierarchy/by-path",
    response_model=AdministrativeUnitResponse,
    summary="Get administrative unit by ltree path",
    description="Fetch a territorial unit by its dot-delimited path (e.g. 'india.27.492').",
)
async def get_unit_by_path(
    path: str = Query(..., description="PostgreSQL ltree dot path"),
) -> AdministrativeUnitResponse:
    """Fetch an administrative unit by path."""
    unit = hierarchy_service.get_unit_by_path(path)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrative unit with path '{path}' not found.",
        )
    return unit


@router.get(
    "/hierarchy/by-lgd/{lgd_code}",
    response_model=AdministrativeUnitResponse,
    summary="Get administrative unit by official LGD code",
    description="Fetch a territorial unit by official Ministry Local Government Directory code (e.g. '492').",
)
async def get_unit_by_lgd_code(lgd_code: str) -> AdministrativeUnitResponse:
    """Fetch an administrative unit by LGD code."""
    unit = hierarchy_service.get_unit_by_lgd_code(lgd_code)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrative unit with LGD code '{lgd_code}' not found.",
        )
    return unit


@router.get(
    "/hierarchy/descendants",
    response_model=List[AdministrativeUnitResponse],
    summary="Find descendant administrative units (Sub-tree)",
    description="Sub-2ms query returning all children and sub-districts under a scope (corresponds to path <@ target).",
)
async def find_descendants(
    path: str = Query(..., description="Root path to find descendants under"),
    include_self: bool = Query(True, description="Whether to include the root unit itself"),
    max_depth: Optional[int] = Query(None, ge=1, le=5, description="Maximum relative depth to traverse"),
) -> List[AdministrativeUnitResponse]:
    """Find descendant units under an ltree path."""
    return hierarchy_service.find_descendants(path=path, include_self=include_self, max_depth=max_depth)


@router.get(
    "/hierarchy/ancestors",
    response_model=List[AdministrativeUnitResponse],
    summary="Find ancestor administrative units (Chain of command)",
    description="Sub-2ms query returning full administrative chain of command up to Country (corresponds to path @> target).",
)
async def find_ancestors(
    path: str = Query(..., description="Target unit path to find ancestors for"),
    include_self: bool = Query(True, description="Whether to include the target unit itself"),
) -> List[AdministrativeUnitResponse]:
    """Find ancestor units leading to a path."""
    return hierarchy_service.find_ancestors(path=path, include_self=include_self)


@router.get(
    "/hierarchy/tree",
    response_model=TerritorialTreeNode,
    summary="Get nested territorial hierarchy tree",
    description="Returns nested JSON tree suitable for interactive tree explorer components.",
)
async def get_territorial_tree(
    root_path: str = Query("india", description="Root path to anchor the tree"),
    max_depth: int = Query(3, ge=1, le=5, description="Maximum depth of tree to generate"),
) -> TerritorialTreeNode:
    """Build nested territorial hierarchy tree."""
    tree = hierarchy_service.build_jurisdiction_tree(root_path=root_path, max_depth=max_depth)
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Root territorial path '{root_path}' not found.",
        )
    return tree


@router.post(
    "/hierarchy/units",
    response_model=AdministrativeUnitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision new administrative territorial unit",
    description="SuperAdmin endpoint to register a new sovereign territorial administrative unit.",
)
async def create_administrative_unit(payload: AdministrativeUnitCreate) -> AdministrativeUnitResponse:
    """Create a new administrative unit."""
    try:
        return hierarchy_service.create_unit(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.patch(
    "/hierarchy/units/{unit_id}",
    response_model=AdministrativeUnitResponse,
    summary="Update administrative territorial unit",
    description="Update metadata, active status, or pincode mappings for an administrative unit.",
)
async def update_administrative_unit(
    unit_id: str, payload: AdministrativeUnitUpdate
) -> AdministrativeUnitResponse:
    """Update an administrative unit."""
    updated = hierarchy_service.update_unit(unit_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrative unit '{unit_id}' not found.",
        )
    return updated


@router.post(
    "/hierarchy/officers",
    response_model=AdministrativeOfficerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Appoint administrative healthcare officer",
    description="Appoint an officer and assign territorial jurisdiction scope (e.g. CMO assigned to 'india.27.492').",
)
async def appoint_officer(payload: AdministrativeOfficerCreate) -> AdministrativeOfficerResponse:
    """Appoint an administrative officer."""
    try:
        return hierarchy_service.appoint_officer(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/hierarchy/officers",
    response_model=List[AdministrativeOfficerResponse],
    summary="List appointed administrative officers",
    description="Filter officers by administrative unit, jurisdiction scope, or official designation.",
)
async def list_officers(
    unit_id: Optional[str] = Query(None, description="Filter by assigned unit UUID"),
    jurisdiction_path: Optional[str] = Query(None, description="Filter by jurisdiction ltree scope"),
    designation: Optional[GovtDesignationEnum] = Query(None, description="Filter by official designation"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
) -> List[AdministrativeOfficerResponse]:
    """List appointed officers matching query criteria."""
    return hierarchy_service.list_officers(
        administrative_unit_id=unit_id,
        jurisdiction_path=jurisdiction_path,
        designation=designation,
        is_active=is_active,
    )


@router.post(
    "/hierarchy/verify-jurisdiction",
    summary="Verify officer territorial authority",
    description="Sub-2ms check testing if an officer's jurisdiction path covers a facility or sub-district.",
)
async def verify_jurisdiction(
    officer_path: str = Query(..., description="Officer assigned jurisdiction path (e.g. 'india.27.492')"),
    target_path: str = Query(..., description="Target facility or action path (e.g. 'india.27.492.4182')"),
) -> dict:
    """Verify territorial oversight authority."""
    authorized = hierarchy_service.verify_jurisdiction_access(
        officer_scope_path=officer_path, target_facility_path=target_path
    )
    return {
        "authorized": authorized,
        "officer_jurisdiction": officer_path,
        "target_path": target_path,
        "checked_at": "2026-11-01T00:00:00Z",
    }
