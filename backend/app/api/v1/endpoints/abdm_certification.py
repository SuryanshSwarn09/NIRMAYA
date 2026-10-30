"""API endpoints for ABDM Official Sandbox E2E Certification & Regression Test Harness.

Endpoints:
- POST /api/v1/abdm/certification/run: Executes official NHA test vectors across M1, M2, and M3.
- GET /api/v1/abdm/certification/report: Retrieves the latest certified sandbox compliance report.
- GET /api/v1/abdm/certification/vectors: Catalog of registered test vectors with NHA specification references.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.schemas.abdm_certification import (
    RunCertificationRequest,
    SandboxCertificationReport,
    VectorCatalogResponse,
)
from app.services.abdm_certification import (
    OFFICIAL_VECTOR_CATALOG,
    abdm_sandbox_certifier,
)

logger = logging.getLogger("nirmaya.api.abdm_certification")

router = APIRouter()


@router.post(
    "/run",
    response_model=SandboxCertificationReport,
    status_code=status.HTTP_200_OK,
    summary="Run ABDM Official Sandbox E2E Certification",
    description="Executes automated NHA ABDM Gateway v0.5 test vectors covering Milestone 1 (ABHA), "
                "Milestone 2 (Discovery & Linkage), and Milestone 3 (Consent & Encrypted Transfer). "
                "Computes pass rates and seals the result with a SHA-256 certificate proof.",
)
def run_certification_harness(
    request: RunCertificationRequest,
) -> SandboxCertificationReport:
    """Executes official sandbox certification harness and returns compliance report."""
    try:
        report = abdm_sandbox_certifier.run_certification(
            milestones=request.milestones,
            facility_id=request.facilityId,
            mock_network_delay=request.mockNetworkDelay,
        )
        return report
    except Exception as exc:
        logger.error(f"[run_certification_harness] Execution error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Certification harness failed during execution: {str(exc)}",
        )


@router.get(
    "/report",
    response_model=SandboxCertificationReport,
    status_code=status.HTTP_200_OK,
    summary="Get Latest ABDM Sandbox Certification Report",
    description="Retrieves the most recent official ABDM Sandbox Certification report. "
                "If no report has been generated yet, triggers an initial execution and returns it.",
)
def get_latest_certification_report() -> SandboxCertificationReport:
    """Returns the most recent certification report or runs one on demand."""
    report = abdm_sandbox_certifier.get_latest_report()
    if not report:
        # Run default certification suite if none exists in cache
        report = abdm_sandbox_certifier.run_certification()
    return report


@router.get(
    "/vectors",
    response_model=VectorCatalogResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Official Sandbox Test Vector Catalog",
    description="Retrieves the catalog of official NHA ABDM Gateway v0.5 test vectors "
                "supported by the automated certification test harness.",
)
def get_vector_catalog() -> VectorCatalogResponse:
    """Returns list of official ABDM Sandbox test vectors."""
    catalog = abdm_sandbox_certifier.get_vector_catalog()
    return VectorCatalogResponse(
        vectors=catalog,
        count=len(catalog),
    )
