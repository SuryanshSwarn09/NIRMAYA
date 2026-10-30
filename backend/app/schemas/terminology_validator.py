"""Pydantic schemas for Medical Ontology Binding Audit & Clinical Terminology Validation.

Supports standard healthcare terminologies:
- SNOMED-CT (Systemized Nomenclature of Medicine -- Clinical Terms)
- LOINC (Logical Observation Identifiers Names and Codes)
- ICD-10 (International Classification of Diseases, 10th Revision)
- HL7 Standard CodeSystems (ActCode, Observation Category, Condition Status)
- RxNorm / WHO-ATC for Pharmacotherapy
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ConceptBindingStatus(str, Enum):
    """Evaluation status for a clinical coded concept."""

    FULLY_BOUND = "FULLY_BOUND"
    UNRECOGNIZED_CODE = "UNRECOGNIZED_CODE"
    INVALID_SYSTEM = "INVALID_SYSTEM"
    MISSING_BINDING = "MISSING_BINDING"
    DISPLAY_MISMATCH = "DISPLAY_MISMATCH"


class ConceptSuggestion(BaseModel):
    """Standardized concept mapping suggestion for an unmapped or approximate clinical term."""

    system: str = Field(..., description="Target terminology system URI (e.g. http://snomed.info/sct)")
    code: str = Field(..., description="Target standard concept code")
    display: str = Field(..., description="Authoritative standard concept display name")
    category: str = Field(..., description="Clinical category (e.g. condition, observation, procedure)")
    confidence: float = Field(default=1.0, description="Match confidence score between 0.0 and 1.0")

    model_config = ConfigDict(from_attributes=True)


class ConceptAuditItem(BaseModel):
    """Audit evaluation for an individual clinical coding element within a FHIR resource."""

    resourceType: str = Field(..., description="FHIR resource type where concept is located")
    elementPath: str = Field(..., description="JSONPath or structural element location (e.g. Condition.code)")
    system: Optional[str] = Field(default=None, description="System URI declared in the coding")
    code: Optional[str] = Field(default=None, description="Code value declared in the coding")
    display: Optional[str] = Field(default=None, description="Display text provided in the coding")
    status: ConceptBindingStatus = Field(..., description="Assessed binding classification")
    standardDisplay: Optional[str] = Field(default=None, description="Official standard display name if recognized")
    suggestedCodes: List[ConceptSuggestion] = Field(
        default_factory=list,
        description="Suggested standard codes if current concept is unmapped or missing",
    )
    message: str = Field(..., description="Human-readable audit finding explanation")

    model_config = ConfigDict(from_attributes=True)


class OntologyAuditReport(BaseModel):
    """Aggregated report evaluating the medical ontology compliance of a FHIR document or bundle."""

    bundleId: Optional[str] = Field(default=None, description="Identifier of the evaluated bundle")
    totalConceptsAudited: int = Field(default=0, description="Total number of clinical concepts evaluated")
    fullyBoundCount: int = Field(default=0, description="Count of fully bound concepts")
    unrecognizedCodeCount: int = Field(default=0, description="Count of recognized systems with unknown codes")
    invalidSystemCount: int = Field(default=0, description="Count of concepts with invalid or non-standard systems")
    missingBindingCount: int = Field(default=0, description="Count of free-text elements lacking standard codes")
    displayMismatchCount: int = Field(default=0, description="Count of valid codes with mismatched display text")
    complianceScore: float = Field(
        ...,
        description="Weighted ontology compliance score (0.0 to 100.0%)",
    )
    isCompliant: bool = Field(
        ...,
        description="True if compliance score >= 80.0% and invalidSystemCount == 0",
    )
    auditItems: List[ConceptAuditItem] = Field(
        default_factory=list,
        description="List of all individual concept audit items",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Clinical recommendations for remediating ontology deficiencies",
    )

    model_config = ConfigDict(from_attributes=True)


class BundleOntologyAuditRequest(BaseModel):
    """Request payload for evaluating an entire FHIR R4 Bundle for medical ontology bindings."""

    bundle: Dict[str, Any] = Field(
        ...,
        description="FHIR R4 Document Bundle object represented as a dictionary",
    )
    strictDisplayCheck: bool = Field(
        default=False,
        description="When True, slight display text differences are flagged as DISPLAY_MISMATCH",
    )

    model_config = ConfigDict(from_attributes=True)


class ConceptLookupRequest(BaseModel):
    """Request to verify and resolve a single clinical concept by system and code."""

    system: str = Field(..., description="Authoritative terminology system URI")
    code: str = Field(..., description="Clinical concept code to look up")

    model_config = ConfigDict(from_attributes=True)


class ConceptLookupResponse(BaseModel):
    """Resolution details for a single clinical concept query."""

    isValid: bool = Field(..., description="True if code is registered in the specified system")
    system: str = Field(..., description="Standard terminology system URI")
    code: str = Field(..., description="Standard concept code")
    officialDisplay: Optional[str] = Field(default=None, description="Authoritative standard concept display name")
    category: Optional[str] = Field(default=None, description="Clinical concept category")
    message: str = Field(..., description="Status summary of the lookup")

    model_config = ConfigDict(from_attributes=True)


class ConceptSuggestionRequest(BaseModel):
    """Request to search for standard clinical concepts matching a natural language term."""

    query: str = Field(..., description="Clinical search term (e.g. 'hypertension', 'blood pressure')")
    system: Optional[str] = Field(
        default=None,
        description="Optional filter for specific system (e.g. 'http://snomed.info/sct')",
    )
    limit: int = Field(default=5, ge=1, le=25, description="Maximum number of suggestions to return")

    model_config = ConfigDict(from_attributes=True)


class ConceptSuggestionResponse(BaseModel):
    """Matching standard clinical concepts for an input query."""

    query: str = Field(..., description="Original search string")
    count: int = Field(..., description="Number of suggestions returned")
    suggestions: List[ConceptSuggestion] = Field(
        default_factory=list,
        description="List of ranked standard concept suggestions",
    )

    model_config = ConfigDict(from_attributes=True)


class TerminologySystemInfo(BaseModel):
    """Metadata regarding an authorized healthcare ontology system."""

    name: str = Field(..., description="Common acronym or name of the ontology")
    uri: str = Field(..., description="Canonical system URI")
    version: Optional[str] = Field(default=None, description="Current loaded version or release cycle")
    authority: str = Field(..., description="Standards developing organization (SDO) or authority")
    purpose: str = Field(..., description="Clinical domain and ABDM exchange scope")

    model_config = ConfigDict(from_attributes=True)


class TerminologySystemsResponse(BaseModel):
    """Catalog of authorized healthcare terminologies supported by the audit engine."""

    systems: List[TerminologySystemInfo] = Field(
        ...,
        description="List of registered terminology systems",
    )
    count: int = Field(..., description="Total count of authorized systems")

    model_config = ConfigDict(from_attributes=True)
