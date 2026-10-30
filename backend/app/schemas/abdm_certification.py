"""Pydantic schemas for ABDM Official Sandbox E2E Certification & Regression Test Harness.

Conforms to National Health Authority (NHA) ABDM Gateway v0.5 Specifications:
- Milestone 1 (M1): ABHA Issuance & Healthcare Professional Registry (HPR) Onboarding
- Milestone 2 (M2): Care Context Discovery, Fuzzy Demographic Matching & Linkage
- Milestone 3 (M3): Consent Management, Diffie-Hellman Key Agreement & Encrypted FHIR Transfer
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SandboxMilestoneType(str, Enum):
    """ABDM Milestone classifications supported by the official certification harness."""

    M1_ABHA = "M1_ABHA"
    M2_DISCOVERY_LINKAGE = "M2_DISCOVERY_LINKAGE"
    M3_CONSENT_DATA_TRANSFER = "M3_CONSENT_DATA_TRANSFER"


class CertificationVectorStatus(str, Enum):
    """Execution status of an individual certification test vector."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class CertificationVectorResult(BaseModel):
    """Diagnostic outcome of executing an individual NHA sandbox test vector."""

    vectorId: str = Field(..., description="Unique test vector identifier (e.g. V-M1-01, V-M2-03)")
    milestone: SandboxMilestoneType = Field(..., description="Associated ABDM Milestone")
    title: str = Field(..., description="Human-readable title of the test vector")
    description: str = Field(..., description="Technical requirement and specification verified")
    status: CertificationVectorStatus = Field(..., description="Result status: PASSED | FAILED | SKIPPED")
    durationMs: float = Field(..., description="Execution time in milliseconds")
    assertionsPassed: int = Field(default=0, description="Count of assertions passed")
    assertionsTotal: int = Field(default=0, description="Total number of assertions evaluated")
    requestSummary: Dict[str, Any] = Field(default_factory=dict, description="Summary of simulated request parameters")
    responseSummary: Dict[str, Any] = Field(default_factory=dict, description="Summary of response payload or outcome")
    errorDetail: Optional[str] = Field(default=None, description="Diagnostic error trace if vector failed")

    model_config = ConfigDict(from_attributes=True)


class MilestoneSummary(BaseModel):
    """Aggregated compliance metrics for a specific ABDM Milestone."""

    milestone: SandboxMilestoneType = Field(..., description="ABDM Milestone")
    totalVectors: int = Field(..., description="Total test vectors in milestone")
    passed: int = Field(..., description="Number of passed vectors")
    failed: int = Field(..., description="Number of failed vectors")
    passRate: float = Field(..., description="Percentage of vectors passed (0.0 to 100.0%)")

    model_config = ConfigDict(from_attributes=True)


class SandboxCertificationReport(BaseModel):
    """Official NHA ABDM Sandbox Certification Audit Report."""

    reportId: str = Field(..., description="Unique deterministic UUID of this certification run")
    facilityId: str = Field(default="IN0410000123", description="HIP/HIU Facility ID under test")
    facilityName: str = Field(
        default="NIRMAYA National Health Interoperability Demonstrator",
        description="Official registered facility name",
    )
    environment: str = Field(default="sbx.abdm.gov.in", description="Sandbox gateway environment")
    gatewayVersion: str = Field(default="v0.5", description="ABDM Gateway protocol specification version")
    executedAt: str = Field(..., description="ISO 8601 UTC timestamp of execution conclusion")
    certificationStatus: str = Field(
        ...,
        description="Official status: CERTIFIED_CONFORMING | NON_CONFORMING",
    )
    overallPassRate: float = Field(
        ...,
        description="Overall pass percentage across all executed milestones (0.0 to 100.0%)",
    )
    totalVectors: int = Field(..., description="Total number of test vectors executed")
    passedVectors: int = Field(..., description="Total passed vectors")
    failedVectors: int = Field(..., description="Total failed vectors")
    milestoneSummaries: List[MilestoneSummary] = Field(
        default_factory=list,
        description="Per-milestone breakdown summaries",
    )
    vectorResults: List[CertificationVectorResult] = Field(
        default_factory=list,
        description="Granular results for each individual test vector",
    )
    certificateProof: str = Field(
        ...,
        description="Cryptographic SHA-256 tamper-evident digest sealing the certification outcome",
    )

    model_config = ConfigDict(from_attributes=True)


class RunCertificationRequest(BaseModel):
    """Request payload to execute the automated sandbox certification harness."""

    milestones: Optional[List[SandboxMilestoneType]] = Field(
        default=None,
        description="Optional subset of milestones to execute. If None, all M1, M2, and M3 vectors are executed",
    )
    facilityId: str = Field(
        default="IN0410000123",
        description="Authorized ABDM HIP/HIU facility identifier",
    )
    mockNetworkDelay: bool = Field(
        default=False,
        description="Whether to simulate realistic network gateway latency in vector execution",
    )

    model_config = ConfigDict(from_attributes=True)


class VectorCatalogItem(BaseModel):
    """Specification item describing an official ABDM Sandbox test vector."""

    vectorId: str = Field(..., description="Identifier of the vector (e.g. V-M1-01)")
    milestone: SandboxMilestoneType = Field(..., description="Associated milestone")
    title: str = Field(..., description="Short name of the test scenario")
    description: str = Field(..., description="Detailed description of the NHA gateway scenario")
    nhaSpecificationRef: str = Field(..., description="Reference section in official NHA ABDM documentation")

    model_config = ConfigDict(from_attributes=True)


class VectorCatalogResponse(BaseModel):
    """Catalog response listing all supported sandbox test vectors."""

    vectors: List[VectorCatalogItem] = Field(
        ...,
        description="List of official sandbox test vectors",
    )
    count: int = Field(..., description="Total number of supported test vectors")

    model_config = ConfigDict(from_attributes=True)
