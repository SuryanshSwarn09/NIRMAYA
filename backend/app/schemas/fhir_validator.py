"""Pydantic schemas for HL7 FHIR Release 4 (R4) Document Bundle validation and NRCES India profiles.

Conforms to:
- HL7 FHIR R4 Bundle Specification (type == "document")
- National Resource Centre for EHR Standards in India (NRCES)
- Ayushman Bharat Digital Mission (ABDM) Milestone 3 Clinical Document Profiles:
    1. OPConsultationRecord (SNOMED 371530004)
    2. PrescriptionRecord (SNOMED 440545006)
    3. DiagnosticReportRecord (SNOMED 721981007)
    4. DischargeSummaryRecord (SNOMED 373942005)
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ValidationIssueSeverity(str, Enum):
    """Severity classification for FHIR validation findings."""

    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class ValidationIssue(BaseModel):
    """Granular validation diagnostic issue in a FHIR R4 resource or bundle envelope."""

    severity: ValidationIssueSeverity = Field(
        ...,
        description="Issue severity: error indicates non-conformance, warning indicates potential risk",
    )
    code: str = Field(
        ...,
        description="Machine-readable error/warning code (e.g. missing-composition, dangling-reference)",
    )
    location: str = Field(
        ...,
        description="JSON path or structural coordinate of the violation (e.g. entry[0].resource.Composition)",
    )
    message: str = Field(
        ...,
        description="Human-readable description of the validation failure or advisory",
    )

    model_config = ConfigDict(from_attributes=True)


class BundleProfileType(str, Enum):
    """Supported NRCES India FHIR R4 document bundle profile types."""

    OP_CONSULTATION = "OPConsultationRecord"
    PRESCRIPTION = "PrescriptionRecord"
    DIAGNOSTIC_REPORT = "DiagnosticReportRecord"
    DISCHARGE_SUMMARY = "DischargeSummaryRecord"
    GENERIC_DOCUMENT = "GenericDocumentBundle"


class BundleValidationRequest(BaseModel):
    """Request payload for validating a FHIR R4 document bundle."""

    bundle: Dict[str, Any] = Field(
        ...,
        description="FHIR R4 Bundle object represented as a dictionary",
    )
    expectedProfile: Optional[BundleProfileType] = Field(
        default=None,
        description="Optional expected profile type to enforce. If omitted, automatically inferred from Composition.type",
    )
    strictMode: bool = Field(
        default=True,
        description="When True, non-standard coding systems or unresolvable external references trigger warnings/errors",
    )

    model_config = ConfigDict(from_attributes=True)


class BundleValidationResponse(BaseModel):
    """Validation report returned after multi-tier evaluation of a FHIR R4 document bundle."""

    isValid: bool = Field(
        ...,
        description="True if the bundle contains zero error-level issues; False otherwise",
    )
    bundleId: Optional[str] = Field(
        default=None,
        description="Bundle ID declared in the payload, if present",
    )
    detectedProfile: str = Field(
        ...,
        description="Inferred or asserted clinical profile name",
    )
    totalEntries: int = Field(
        default=0,
        description="Total number of resources contained within bundle.entry",
    )
    resourceCounts: Dict[str, int] = Field(
        default_factory=dict,
        description="Map of resourceType to instance count found in bundle entries",
    )
    issues: List[ValidationIssue] = Field(
        default_factory=list,
        description="Ordered list of structural, referential, or semantic validation issues",
    )
    summary: str = Field(
        ...,
        description="Executive summary of the validation outcome",
    )

    model_config = ConfigDict(from_attributes=True)


class ProfileMetadata(BaseModel):
    """NRCES India clinical profile specification metadata."""

    profileId: str = Field(..., description="Short identifier of the profile")
    name: str = Field(..., description="Official profile designation")
    canonicalUrl: str = Field(..., description="NRCES India canonical StructureDefinition URL")
    compositionSnomedCode: str = Field(..., description="Required SNOMED-CT code for Composition.type")
    compositionDisplay: str = Field(..., description="Human-readable concept display text")
    requiredResources: List[str] = Field(..., description="List of mandatory resource types required in the bundle")
    optionalResources: List[str] = Field(..., description="List of allowed/recommended auxiliary resource types")
    description: str = Field(..., description="Clinical context and ABDM exchange purpose")

    model_config = ConfigDict(from_attributes=True)


class ProfilesCatalogResponse(BaseModel):
    """Catalog of all supported NRCES FHIR R4 Document Bundle profiles."""

    profiles: List[ProfileMetadata] = Field(
        ...,
        description="List of official NRCES profiles supported by NIRMAYA",
    )
    count: int = Field(
        ...,
        description="Total number of supported clinical profiles",
    )

    model_config = ConfigDict(from_attributes=True)

