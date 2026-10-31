"""REST endpoints for OWASP ASVS Level 2 compliance verification,
SQLi/XSS defensive fuzzing benchmarks, and distributed DoS shield telemetry.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.asvs_fuzzer import (
    ASVSComplianceReport,
    DoSShieldStatus,
    FuzzingReport,
    FuzzTestRequest,
)
from app.services.asvs_audit_service import asvs_audit_service
from app.services.asvs_fuzzer import asvs_fuzzer_service
from app.services.dos_shield import dos_shield_service

router = APIRouter()


@router.get(
    "/asvs/checklist",
    response_model=ASVSComplianceReport,
    summary="Retrieve OWASP ASVS v4.0 Level 2 compliance verification report",
    description="Returns compliance audit results across all 14 ASVS control families including architecture, crypto, access control, and logging.",
)
def get_asvs_checklist() -> ASVSComplianceReport:
    """Evaluate and return OWASP ASVS Level 2 compliance scorecard."""
    return asvs_audit_service.generate_compliance_report()


@router.post(
    "/fuzz/sqli",
    response_model=FuzzingReport,
    summary="Trigger automated SQL injection defensive fuzzing benchmark",
    description="Evaluates adversarial SQL injection vectors (tautologies, union-based, stacked queries, time-delay) against defensive layers.",
)
def test_sqli_fuzzing(request: Optional[FuzzTestRequest] = None) -> FuzzingReport:
    """Execute SQL injection defensive fuzzing."""
    custom = request.input_text if request else None
    return asvs_fuzzer_service.test_sqli_defenses(custom_input=custom)


@router.post(
    "/fuzz/xss",
    response_model=FuzzingReport,
    summary="Trigger automated Cross-Site Scripting (XSS) defensive fuzzing benchmark",
    description="Evaluates reflected scripts, event handlers, and script URIs against HTML output sanitization routines.",
)
def test_xss_fuzzing(request: Optional[FuzzTestRequest] = None) -> FuzzingReport:
    """Execute XSS defensive fuzzing and HTML entity sanitization."""
    custom = request.input_text if request else None
    return asvs_fuzzer_service.test_xss_defenses(custom_input=custom)


@router.post(
    "/fuzz/all",
    response_model=FuzzingReport,
    summary="Trigger comprehensive multi-vector adversarial fuzzing suite",
    description="Runs combined SQLi and XSS adversarial test vectors calculating cumulative defense efficacy rate.",
)
def test_comprehensive_fuzzing() -> FuzzingReport:
    """Execute combined adversarial test suite."""
    return asvs_fuzzer_service.run_comprehensive_fuzz_suite()


@router.get(
    "/shield/jail",
    response_model=DoSShieldStatus,
    summary="Retrieve DoS shield operational status and active IP jail roster",
    description="Inspects active banned hosts, infraction counts, penalty expiry timestamps, and shield operational mode.",
)
def get_dos_shield_status() -> DoSShieldStatus:
    """Collect real-time DoS shield and IP jail telemetry."""
    return dos_shield_service.get_status()


@router.post(
    "/shield/jail/clear",
    summary="Reset active IP jail penalties and rate limit tracking",
    description="Administrative endpoint to clear banned hosts and reset infraction tracking counters.",
)
def clear_ip_jails() -> dict:
    """Clear all active IP jail bans."""
    dos_shield_service.clear()
    return {
        "success": True,
        "message": "All IP jail penalties and rate limit tracking cleared.",
    }
