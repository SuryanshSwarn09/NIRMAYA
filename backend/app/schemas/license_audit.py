from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LicenseTypeEnum(str, Enum):
    """Normalized open source software license classifications."""
    MIT = "MIT"
    APACHE_2_0 = "Apache-2.0"
    BSD_2_CLAUSE = "BSD-2-Clause"
    BSD_3_CLAUSE = "BSD-3-Clause"
    ISC = "ISC"
    PSF = "Python-2.0"
    CC_BY_4_0 = "CC-BY-4.0"
    OTHER_PERMISSIVE = "Other Permissive"
    COPYLEFT_FLAGGED = "Copyleft (GPL/AGPL)"


class DependencyEcosystemEnum(str, Enum):
    """Runtime ecosystem of third-party software component."""
    PYTHON_PYPI = "Python (PyPI)"
    NODE_NPM = "Node.js (npm)"


class ComplianceStatusEnum(str, Enum):
    """Legal and regulatory licensing compliance verdict."""
    CERTIFIED = "CERTIFIED"
    NON_COMPLIANT = "NON_COMPLIANT"


class IntegrityCheckStatusEnum(str, Enum):
    """Verification status of architectural subsystem integrity check."""
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"


class DependencyComponentItem(BaseModel):
    """Software bill of materials item representing a single dependency."""
    name: str = Field(..., description="Package identifier")
    version: str = Field(..., description="Exact pinned semantic version")
    ecosystem: DependencyEcosystemEnum = Field(..., description="Runtime package repository")
    license: LicenseTypeEnum = Field(..., description="Normalized open-source license")
    license_url: str = Field(..., description="Link to authoritative license text or registry")
    copyleft_risk: bool = Field(default=False, description="Flag indicating viral/copyleft licensing risk")
    direct_dependency: bool = Field(default=True, description="Direct application dependency vs transitive")
    description: str = Field(..., description="Architectural role and functional purpose of dependency")


class LicenseSummaryScorecard(BaseModel):
    """Aggregated legal compliance metrics across all software dependencies."""
    total_dependencies: int = Field(..., ge=0, description="Total cataloged package dependencies")
    permissive_count: int = Field(..., ge=0, description="Number of permissive licensed packages")
    copyleft_count: int = Field(..., ge=0, description="Number of copyleft/GPL licensed packages")
    permissive_percentage: float = Field(..., ge=0.0, le=100.0, description="Proportion of permissive licenses")
    compliance_status: ComplianceStatusEnum = Field(..., description="Overall legal certification status")
    license_distribution: Dict[str, int] = Field(..., description="Count of packages per license type")
    certified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    legal_signoff_attestation: str = Field(..., description="Formal legal attestation of zero copyleft contamination")


class SystemIntegrityCheckItem(BaseModel):
    """Single architectural invariant verification check for release readiness."""
    check_id: str = Field(..., description="Unique check identifier (e.g., INT-01-POSTGRES-POOL)")
    subsystem: str = Field(..., description="Architectural domain under verification")
    invariant_verified: str = Field(..., description="Formal invariant or SLA verified")
    compliance_status: IntegrityCheckStatusEnum = Field(default=IntegrityCheckStatusEnum.PASSED)
    target_sla_or_bound: str = Field(..., description="Contractual or architectural bound")
    achieved_metric: str = Field(..., description="Empirically achieved verification result")
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CycloneDXComponent(BaseModel):
    """CycloneDX v1.5 standard component specification."""
    type: str = Field(default="library")
    name: str
    version: str
    description: str
    licenses: List[Dict[str, Any]]
    purl: str


class CycloneDXMetadata(BaseModel):
    """CycloneDX v1.5 document metadata."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tools: List[Dict[str, str]]
    component: Dict[str, str]


class CycloneDXManifest(BaseModel):
    """Complete Software Bill of Materials (SBOM) conforming to CycloneDX 1.5 JSON."""
    bomFormat: str = Field(default="CycloneDX")
    specVersion: str = Field(default="1.5")
    serialNumber: str
    version: int = Field(default=1)
    metadata: CycloneDXMetadata
    components: List[CycloneDXComponent]


class PreReleaseAuditReport(BaseModel):
    """Consolidated pre-release audit scorecard and quality sign-off gate."""
    project_name: str = Field(default="NIRMAYA")
    release_candidate: str = Field(default="v1.0.0-rc1")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    auditor: str = Field(default="NIRMAYA Core Engineering & Security Council")
    license_scorecard: LicenseSummaryScorecard
    integrity_checks: List[SystemIntegrityCheckItem]
    total_checks_passed: int
    total_checks_count: int
    all_checks_passed: bool
    release_readiness: str = Field(default="READY_FOR_PRODUCTION_TAG")
