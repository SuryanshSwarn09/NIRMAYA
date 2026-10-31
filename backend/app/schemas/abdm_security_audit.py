"""Pydantic schemas for ABDM Security Penetration Testing & Consent Lifecycle Audit.

Conforms to:
- NHA ABDM Gateway v0.5 Security Guidelines
- Digital Personal Data Protection (DPDP) Act 2023 Consent Lifecycle
- RFC 5869 (HKDF) & RFC 7748 (Curve25519) Cryptographic Specifications
- NIST SP 800-38D (AES-256-GCM AEAD Tag Integrity)
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PenetrationAttackCategory(str, Enum):
    """Categorization of security penetration vectors."""

    GATEWAY_REPLAY = "GATEWAY_REPLAY"
    CONSENT_LIFECYCLE = "CONSENT_LIFECYCLE"
    SCOPE_ESCALATION = "SCOPE_ESCALATION"
    CRYPTOGRAPHIC_INTEGRITY = "CRYPTOGRAPHIC_INTEGRITY"
    RATE_LIMIT_BRUTE_FORCE = "RATE_LIMIT_BRUTE_FORCE"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability risk classification."""

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DefenseOutcome(str, Enum):
    """Outcome of automated attack vector against security guardrails."""

    BLOCKED_AS_EXPECTED = "BLOCKED_AS_EXPECTED"
    VULNERABILITY_DETECTED = "VULNERABILITY_DETECTED"


class PenetrationVectorItem(BaseModel):
    """Catalog representation of an official ABDM security penetration vector."""

    vectorId: str = Field(description="Unique vector identifier (e.g. SEC-01, SEC-03)")
    category: PenetrationAttackCategory = Field(description="Security domain category")
    title: str = Field(description="Short title of the attack scenario")
    attackDescription: str = Field(description="Detailed explanation of the simulated threat")
    expectedDefense: str = Field(description="Expected security guardrail behavior")
    nhaReference: str = Field(description="NHA Specification or regulatory reference")

    model_config = ConfigDict(from_attributes=True)


class PenetrationVectorResult(BaseModel):
    """Execution result of an individual penetration attack vector."""

    vectorId: str = Field(description="Vector identifier")
    category: PenetrationAttackCategory = Field(description="Attack category")
    title: str = Field(description="Vector title")
    attackDescription: str = Field(description="Description of the attack")
    defenseOutcome: DefenseOutcome = Field(description="Whether the attack was successfully blocked")
    severity: VulnerabilitySeverity = Field(
        default=VulnerabilitySeverity.NONE,
        description="Assessed vulnerability severity (NONE if blocked)",
    )
    passed: bool = Field(description="True if attack was blocked as expected, False if vulnerable")
    durationMs: float = Field(default=0.0, description="Execution time in milliseconds")
    auditDetails: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured forensic details of the simulated payload and defense",
    )
    errorDetail: Optional[str] = Field(
        default=None,
        description="Error details if an unexpected internal failure occurred",
    )

    model_config = ConfigDict(from_attributes=True)


class SecurityCategorySummary(BaseModel):
    """Aggregated security metrics per penetration attack category."""

    category: PenetrationAttackCategory = Field(description="Attack category")
    totalVectors: int = Field(description="Total penetration vectors evaluated")
    blocked: int = Field(description="Number of attack attempts successfully blocked")
    vulnerabilities: int = Field(description="Number of security vulnerabilities detected")
    defenseRate: float = Field(description="Defense success percentage (0.0 - 100.0%)")

    model_config = ConfigDict(from_attributes=True)


class SecurityPenetrationReport(BaseModel):
    """Comprehensive ABDM Security Penetration & Consent Hardening Audit Report."""

    reportId: str = Field(description="Unique UUID for this security audit run")
    facilityId: str = Field(description="Target ABDM HIP/HIU Facility ID")
    facilityName: str = Field(description="Target facility organization name")
    environment: str = Field(default="sbx.abdm.gov.in", description="Execution target environment")
    executedAt: str = Field(description="ISO 8601 UTC timestamp of audit execution")
    securityStatus: str = Field(
        description="Audit outcome: SECURE_CONFORMING | VULNERABILITIES_DETECTED"
    )
    totalVectors: int = Field(description="Total attack vectors executed")
    passedVectors: int = Field(description="Number of vectors that successfully defended")
    vulnerabilitiesFound: int = Field(description="Count of discovered security vulnerabilities")
    overallDefenseRate: float = Field(description="Overall security defense rate (0.0 - 100.0%)")
    categorySummaries: List[SecurityCategorySummary] = Field(
        description="Breakdown of defenses across security domains"
    )
    vectorResults: List[PenetrationVectorResult] = Field(
        description="Granular result for each penetration attack vector"
    )
    securityCertificateProof: str = Field(
        description="SHA-256 cryptographic digest sealing report results"
    )

    model_config = ConfigDict(from_attributes=True)


class RunSecurityAuditRequest(BaseModel):
    """Payload to trigger execution of the security penetration testing harness."""

    categories: Optional[List[PenetrationAttackCategory]] = Field(
        default=None,
        description="Optional list of categories to test. If omitted, runs all 5 categories.",
    )
    facilityId: str = Field(default="IN0410000123", description="Target Facility ID")
    facilityName: str = Field(
        default="NIRMAYA National Health Demonstrator",
        description="Target facility name",
    )
    simulateNetworkHop: bool = Field(
        default=False,
        description="Simulate realistic network propagation delay",
    )

    model_config = ConfigDict(from_attributes=True)


class SecurityVectorsResponse(BaseModel):
    """Catalog of registered penetration test vectors."""

    vectors: List[PenetrationVectorItem] = Field(description="List of registered vectors")
    count: int = Field(description="Total registered vectors")

    model_config = ConfigDict(from_attributes=True)

