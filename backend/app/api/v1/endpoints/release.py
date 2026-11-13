from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Response, status

from app.core.container_security import get_container_security_headers
from app.schemas.release import (
    MasterReleaseManifest,
    Phase5CertificationReport,
    ProductionDeploymentVerification,
    ReleasePillarAudit,
)
from app.services.release_service import release_service

router = APIRouter(prefix="/release", tags=["Master Production Release v1.1.0"])


@router.get(
    "/version",
    summary="Get Production Master Version & Channel Metadata",
    description="Returns semantic versioning, build channel, and release identity for NIRMAYA.",
)
async def get_release_version(response: Response) -> Dict[str, Any]:
    """Retrieve production version information and commit metadata."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    manifest = release_service.get_master_release_manifest()
    return {
        "version": manifest.version,
        "tag_name": manifest.tag_name,
        "release_title": manifest.release_title,
        "release_channel": manifest.release_channel,
        "commit_hash": manifest.commit_hash,
        "published_at": manifest.published_at.isoformat(),
        "status": "PRODUCTION_STABLE",
    }


@router.get(
    "/manifest",
    summary="Get Master Production Release Manifest",
    description="Returns complete production master release notes, cumulative engineering metrics, major breakthroughs, and Phase 5 roadmap.",
    response_model=MasterReleaseManifest,
)
async def get_master_release_manifest(response: Response) -> MasterReleaseManifest:
    """Retrieve complete production master release manifest."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return release_service.get_master_release_manifest()


@router.get(
    "/certification",
    summary="Get Phase 5 National Scale DPI Certification Report",
    description="Returns formal regulatory compliance certification (DPDP Act Sec 9, ABDM M1-M3, GIGW 3.0, WCAG 2.1 AA).",
    response_model=Phase5CertificationReport,
)
async def get_phase5_certification(response: Response) -> Phase5CertificationReport:
    """Retrieve formal Phase 5 regulatory and interoperability compliance certification."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return release_service.get_phase5_certification()


@router.get(
    "/verification",
    summary="Execute Live Production Deployment Verification Probes",
    description="Performs 15 live diagnostic probes across PostgreSQL, Redis, FHIR R4, ABDM, and Phase 5 DPI subsystems.",
    response_model=List[ProductionDeploymentVerification],
)
async def get_production_deployment_verification(response: Response) -> List[ProductionDeploymentVerification]:
    """Execute live operational verification checks across core infrastructure."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return release_service.verify_production_deployment()


@router.get(
    "/milestones",
    summary="Get 18-Week Chronological Milestone Audit",
    description="Returns complete historical milestone audit records across all 90 days of the engineering journey.",
    response_model=List[ReleasePillarAudit],
)
async def get_milestone_audits(response: Response) -> List[ReleasePillarAudit]:
    """Retrieve complete 18-week milestone audit registry."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return release_service.get_milestone_audits()
