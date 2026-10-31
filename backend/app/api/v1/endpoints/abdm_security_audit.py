"""API endpoints for ABDM Security Penetration Testing & Consent Lifecycle Audit.

Endpoints:
- POST /api/v1/abdm/security/audit/run: Executes automated penetration attack vectors.
- GET /api/v1/abdm/security/audit/report: Retrieves the latest security penetration report.
- GET /api/v1/abdm/security/audit/vectors: Catalog of registered penetration attack vectors.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.schemas.abdm_security_audit import (
    RunSecurityAuditRequest,
    SecurityPenetrationReport,
    SecurityVectorsResponse,
)
from app.services.abdm_security_audit import (
    OFFICIAL_PENETRATION_VECTORS,
    abdm_security_auditor,
)

logger = logging.getLogger("nirmaya.api.abdm_security_audit")

router = APIRouter()


@router.post(
    "/audit/run",
    response_model=SecurityPenetrationReport,
    status_code=status.HTTP_200_OK,
    summary="Run ABDM Security Penetration Audit",
    description="Executes automated penetration attack vectors across Gateway replay attacks, "
                "mid-flight consent revocation, expired consent, scope escalation, and cryptographic AEAD tamper defense.",
)
def run_security_penetration_audit(
    request: RunSecurityAuditRequest,
) -> SecurityPenetrationReport:
    """Executes security penetration testing harness and returns audit report."""
    try:
        report = abdm_security_auditor.run_audit(
            categories=request.categories,
            facility_id=request.facilityId,
            facility_name=request.facilityName,
            simulate_network_hop=request.simulateNetworkHop,
        )
        return report
    except Exception as exc:
        logger.error(f"[run_security_penetration_audit] Execution error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security audit harness failed during execution: {str(exc)}",
        )


@router.get(
    "/audit/report",
    response_model=SecurityPenetrationReport,
    status_code=status.HTTP_200_OK,
    summary="Get Latest ABDM Security Penetration Report",
    description="Retrieves the most recent ABDM Security Penetration Audit report. "
                "If no report has been generated yet, runs the default security audit and returns it.",
)
def get_latest_security_report() -> SecurityPenetrationReport:
    """Returns the most recent security report or runs one on demand."""
    report = abdm_security_auditor.get_latest_report()
    if not report:
        report = abdm_security_auditor.run_audit()
    return report


@router.get(
    "/audit/vectors",
    response_model=SecurityVectorsResponse,
    status_code=status.HTTP_200_OK,
    summary="List Registered Penetration Attack Vectors",
    description="Returns the full catalog of registered ABDM penetration attack vectors.",
)
def get_penetration_vector_catalog() -> SecurityVectorsResponse:
    """Returns all registered security penetration attack vectors."""
    catalog = abdm_security_auditor.get_vector_catalog()
    return SecurityVectorsResponse(
        vectors=catalog,
        count=len(catalog),
    )

