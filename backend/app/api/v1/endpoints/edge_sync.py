"""FastAPI REST router for Dual-Mode Edge Node Appliance & Offline Synchronization."""

from typing import Any, Dict
from fastapi import APIRouter, Query, Response, status

from app.core.container_security import get_container_security_headers
from app.schemas.edge_sync import (
    EdgeNodeConfig,
    EdgeNodeTelemetry,
    SyncBatchRequest,
    SyncBatchResponse,
)
from app.services.edge_sync_service import edge_sync_service

router = APIRouter()


@router.post(
    "/sync/push",
    response_model=SyncBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Push offline clinical event batch to central server",
    description="Ingests accumulated append-only events from an edge clinic appliance, verifying parent hash chains and payload integrity.",
)
async def push_sync_batch(request: SyncBatchRequest, response: Response) -> SyncBatchResponse:
    """Ingest offline clinical events from edge node."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return edge_sync_service.process_sync_batch_push(request)


@router.post(
    "/sync/pull",
    response_model=SyncBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Pull differential updates from central server",
    description="Fetches updated national formularies, LOINC panic ranges, and state public health directives for edge buffering.",
)
async def pull_sync_batch(
    response: Response,
    node_id: str = Query(..., description="Requesting edge node identifier"),
    since_sequence: int = Query(0, ge=0, description="Highest sequence confirmed locally"),
) -> SyncBatchResponse:
    """Retrieve downstream updates for edge node."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return edge_sync_service.generate_sync_batch_pull(node_id, since_sequence)


@router.get(
    "/status",
    response_model=EdgeNodeTelemetry,
    summary="Get edge node sync status and queue depth telemetry",
    description="Inspects online/offline connection state, pending uncommitted events count, local storage consumption, and Merkle root hash.",
)
async def get_edge_status(response: Response, node_id: str = Query(None)) -> EdgeNodeTelemetry:
    """Retrieve edge appliance operational telemetry."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return edge_sync_service.get_edge_telemetry(node_id)


@router.get(
    "/config",
    response_model=EdgeNodeConfig,
    summary="Get edge node hardware and sync configuration manifest",
    description="Returns active node identifier, facility tier, local storage engine (SQLite), and sync strategy parameters.",
)
async def get_edge_config(response: Response) -> EdgeNodeConfig:
    """Retrieve edge appliance configuration."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return edge_sync_service.get_edge_config()


@router.get(
    "/audit",
    response_model=Dict[str, Any],
    summary="Audit docker-compose.edge.yml static compliance",
    description="Statically verifies edge compose configuration against low-resource constraints (<512MB RAM) and SQLite persistence.",
)
async def audit_edge_compose(response: Response) -> Dict[str, Any]:
    """Perform static compliance audit on docker-compose.edge.yml."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return edge_sync_service.audit_edge_compose_file()
