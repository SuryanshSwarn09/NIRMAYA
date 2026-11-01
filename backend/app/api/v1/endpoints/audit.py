from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, Response, status

from app.core.container_security import get_container_security_headers
from app.schemas.license_audit import (
    CycloneDXManifest,
    DependencyComponentItem,
    DependencyEcosystemEnum,
    LicenseSummaryScorecard,
    LicenseTypeEnum,
    PreReleaseAuditReport,
    SystemIntegrityCheckItem,
)
from app.services.license_audit_service import license_audit_service

router = APIRouter(prefix="/audit", tags=["Pre-Release System Audit & License Compliance"])


@router.get(
    "/licenses/summary",
    summary="Get License Compliance Summary Scorecard",
    description="Returns aggregated open-source license distribution, permissive license ratio, and legal certification attestation.",
    response_model=LicenseSummaryScorecard,
)
async def get_license_summary(response: Response) -> LicenseSummaryScorecard:
    """Retrieve high-level open source license compliance scorecard."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return license_audit_service.get_license_scorecard()


@router.get(
    "/licenses/dependencies",
    summary="List Third-Party Software Dependencies",
    description="Returns verified software bill of materials catalog with optional ecosystem and license filters.",
    response_model=List[DependencyComponentItem],
)
async def list_dependencies(
    response: Response,
    ecosystem: Optional[DependencyEcosystemEnum] = Query(None, description="Filter by ecosystem (Python PyPI or Node.js npm)"),
    license_filter: Optional[LicenseTypeEnum] = Query(None, description="Filter by specific open source license"),
) -> List[DependencyComponentItem]:
    """Retrieve catalog of direct and key transitive dependencies."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return license_audit_service.list_dependencies(ecosystem=ecosystem, license_filter=license_filter)


@router.get(
    "/sbom/cyclonedx",
    summary="Export Software Bill of Materials (CycloneDX 1.5 JSON)",
    description="Emits complete, machine-readable Software Bill of Materials (SBOM) conforming to the CycloneDX 1.5 JSON standard and NTIA minimum elements.",
    response_model=CycloneDXManifest,
)
async def get_cyclonedx_sbom(response: Response) -> CycloneDXManifest:
    """Export standard CycloneDX 1.5 JSON SBOM manifest."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    response.headers["Content-Disposition"] = "attachment; filename=nirmaya-sbom-cyclonedx.json"
    return license_audit_service.generate_cyclonedx_sbom()


@router.get(
    "/system-integrity",
    summary="Get 16-Point Architectural System Integrity Scorecard",
    description="Evaluates all 16 core architectural invariants, SLAs, cryptographic boundaries, and security controls.",
    response_model=List[SystemIntegrityCheckItem],
)
async def get_system_integrity_scorecard(response: Response) -> List[SystemIntegrityCheckItem]:
    """Retrieve 16-point architectural invariant integrity evaluation."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return license_audit_service.get_system_integrity_checks()


@router.get(
    "/report",
    summary="Get Consolidated Pre-Release Audit Report",
    description="Compiles consolidated pre-release audit scorecard certifying license compliance, architectural integrity, and production tag readiness.",
    response_model=PreReleaseAuditReport,
)
async def get_pre_release_report(response: Response) -> PreReleaseAuditReport:
    """Retrieve consolidated pre-release audit report and quality gate verdict."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return license_audit_service.get_pre_release_audit_report()
