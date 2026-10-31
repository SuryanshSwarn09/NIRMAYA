"""Pydantic schemas for OWASP ASVS Level 2 verification, SQLi/XSS defensive fuzzing,
and distributed DoS rate-limiting shield telemetry.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ASVSControlFamily(str, Enum):
    """The 14 OWASP Application Security Verification Standard (ASVS) v4.0.3 control families."""

    V1_ARCHITECTURE = "V1_ARCHITECTURE"
    V2_AUTHENTICATION = "V2_AUTHENTICATION"
    V3_SESSION_MANAGEMENT = "V3_SESSION_MANAGEMENT"
    V4_ACCESS_CONTROL = "V4_ACCESS_CONTROL"
    V5_MALICIOUS_INPUT = "V5_MALICIOUS_INPUT"
    V6_CRYPTOGRAPHY = "V6_CRYPTOGRAPHY"
    V7_ERROR_LOGGING = "V7_ERROR_LOGGING"
    V8_DATA_PROTECTION = "V8_DATA_PROTECTION"
    V9_COMMUNICATIONS = "V9_COMMUNICATIONS"
    V10_MALICIOUS_CODE = "V10_MALICIOUS_CODE"
    V11_BUSINESS_LOGIC = "V11_BUSINESS_LOGIC"
    V12_FILES_RESOURCES = "V12_FILES_RESOURCES"
    V13_API_WEB_SERVICES = "V13_API_WEB_SERVICES"
    V14_CONFIGURATION = "V14_CONFIGURATION"


class ASVSVerificationItem(BaseModel):
    """Verification entry for an individual OWASP ASVS Level 2 requirement."""

    item_id: str = Field(..., description="ASVS requirement identifier, e.g. V5.1.1")
    family: ASVSControlFamily = Field(..., description="ASVS control family classification")
    title: str = Field(..., description="Requirement title and description")
    asvs_level: int = Field(default=2, description="Target ASVS verification tier (Level 2)")
    status: str = Field(default="COMPLIANT", description="Compliance status (COMPLIANT, PARTIAL, NON_COMPLIANT)")
    verification_mechanism: str = Field(..., description="Automated or architectural verification technique")
    evidence_summary: str = Field(..., description="Direct code reference or architectural proof")

    model_config = ConfigDict(from_attributes=True)


class ASVSComplianceReport(BaseModel):
    """Aggregate OWASP ASVS Level 2 compliance assessment report."""

    audit_id: str = Field(..., description="Unique verification audit report identifier")
    audited_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of compliance evaluation",
    )
    asvs_version: str = Field(default="4.0.3", description="ASVS standard specification release")
    target_level: str = Field(
        default="Level 2 (Standard Enterprise Healthcare)",
        description="Target verification level",
    )
    total_controls: int = Field(..., ge=0, description="Total controls evaluated")
    compliant_controls: int = Field(..., ge=0, description="Controls verified as fully compliant")
    compliance_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage score")
    status: str = Field(..., description="Certification outcome (CERTIFIED, CONDITIONAL, FAILED)")
    family_summaries: Dict[str, int] = Field(default_factory=dict, description="Compliant count per family")
    items: List[ASVSVerificationItem] = Field(default_factory=list, description="Detailed control items")

    model_config = ConfigDict(from_attributes=True)


class FuzzingAttackType(str, Enum):
    """Attack classification for automated defensive fuzzing."""

    SQLI_TAUTOLOGY = "SQLI_TAUTOLOGY"
    SQLI_UNION = "SQLI_UNION"
    SQLI_STACKED = "SQLI_STACKED"
    SQLI_TIME_DELAY = "SQLI_TIME_DELAY"
    XSS_REFLECTED_SCRIPT = "XSS_REFLECTED_SCRIPT"
    XSS_EVENT_HANDLER = "XSS_EVENT_HANDLER"
    XSS_JAVASCRIPT_URI = "XSS_JAVASCRIPT_URI"
    XSS_SVG_PAYLOAD = "XSS_SVG_PAYLOAD"


class FuzzingResultItem(BaseModel):
    """Outcome of an adversarial test vector evaluation."""

    attack_type: FuzzingAttackType = Field(..., description="Attack category")
    payload: str = Field(..., description="Adversarial input payload string")
    was_detected: bool = Field(..., description="Whether defensive scanner recognized the exploit pattern")
    was_sanitized: bool = Field(..., description="Whether input was safely neutralized")
    sanitized_output: Optional[str] = Field(default=None, description="Cleaned string representation")
    defense_action: str = Field(..., description="Defensive resolution (BLOCKED, NEUTRALIZED, PASSED)")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="CVSS-equivalent exploit severity")

    model_config = ConfigDict(from_attributes=True)


class FuzzingReport(BaseModel):
    """Aggregate defensive fuzzing benchmark report."""

    fuzz_id: str = Field(..., description="Unique test run identifier")
    fuzzed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of fuzzing execution",
    )
    total_vectors_tested: int = Field(..., ge=0, description="Count of adversarial payloads evaluated")
    blocked_count: int = Field(..., ge=0, description="Payloads blocked outright")
    neutralized_count: int = Field(..., ge=0, description="Payloads neutralized via escaping")
    bypass_count: int = Field(default=0, ge=0, description="Payloads that slipped through defenses")
    effectiveness_rate_percent: float = Field(..., ge=0.0, le=100.0, description="Defensive effectiveness rate")
    status: str = Field(..., description="Security outcome (SECURE, VULNERABLE)")
    results: List[FuzzingResultItem] = Field(default_factory=list, description="Individual vector results")

    model_config = ConfigDict(from_attributes=True)


class FuzzTestRequest(BaseModel):
    """Input payload to trigger defensive fuzzing on custom strings."""

    input_text: str = Field(..., description="Candidate user input or text field to evaluate")
    target_field: Optional[str] = Field(default="clinical_note", description="Semantic field context")

    model_config = ConfigDict(from_attributes=True)


class IPJailRecord(BaseModel):
    """Tracking record for a client IP address placed in isolation penalty box."""

    ip_address: str = Field(..., description="Client IP address subject to jail penalty")
    jailed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when ban was enforced",
    )
    expires_at: datetime = Field(..., description="Timestamp when ban will automatically elapse")
    penalty_seconds: int = Field(..., ge=0, description="Total jail duration in seconds")
    infraction_count: int = Field(default=1, ge=1, description="Cumulative violations by this host")
    reason: str = Field(..., description="Trigger reason (RATE_LIMIT_EXCEEDED, SQLI_ATTEMPT, XSS_ATTEMPT)")
    is_active: bool = Field(default=True, description="Whether restriction is currently active")

    model_config = ConfigDict(from_attributes=True)


class DoSShieldStatus(BaseModel):
    """Operational telemetry for distributed DoS shield and IP jail."""

    shield_mode: str = Field(default="DISTRIBUTED_TOKEN_BUCKET", description="Active throttling strategy")
    redis_connected: bool = Field(default=False, description="Whether distributed Redis tier is active")
    total_active_jails: int = Field(default=0, ge=0, description="Number of currently banned hosts")
    total_infractions_today: int = Field(default=0, ge=0, description="Cumulative recorded violations")
    jailed_ips: List[IPJailRecord] = Field(default_factory=list, description="Currently jailed hosts")
    status: str = Field(default="PROTECTED", description="Shield health (PROTECTED, UNDER_ATTACK, DEGRADED)")

    model_config = ConfigDict(from_attributes=True)
