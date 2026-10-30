"""FastAPI endpoint for ABDM Milestone 3 (M3) Integration Audit & Certification.

Exposes live compliance and telemetry diagnostics for ABDM M3:
- GET /api/v1/abdm/m3/audit: Live audit report compiling HIP & HIU metrics
"""

import logging
from fastapi import APIRouter, status

from app.schemas.abdm_m3_audit import AbdmM3AuditReport
from app.services.abdm_m3_audit import generate_m3_audit_report

logger = logging.getLogger("nirmaya.abdm.m3_audit_api")

router = APIRouter()


@router.get(
    "",
    response_model=AbdmM3AuditReport,
    status_code=status.HTTP_200_OK,
    summary="Get ABDM Milestone 3 Compliance Audit Report",
    description=(
        "Returns real-time aggregated metrics, cryptographic parity verification, "
        "and compliance certification telemetry across consent management, Diffie-Hellman "
        "key exchange, encrypted data transfers, and HIU consumer records."
    ),
)
@router.get(
    "/",
    response_model=AbdmM3AuditReport,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_audit_report() -> AbdmM3AuditReport:
    """Returns live ABDM Milestone 3 compliance audit report."""
    logger.info("[get_audit_report] Generating ABDM M3 compliance audit report")
    return generate_m3_audit_report()

