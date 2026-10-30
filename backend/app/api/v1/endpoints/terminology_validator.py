"""API endpoints for Medical Ontology Binding Audit & Clinical Terminology Validation.

Endpoints:
- POST /api/v1/fhir/ontology/audit: Evaluates bundle semantic compliance and computes compliance score.
- GET /api/v1/fhir/ontology/lookup: Resolves and validates a single concept code against standard registries.
- GET /api/v1/fhir/ontology/suggest: Provides ranked standard concept suggestions for a natural language term.
- GET /api/v1/fhir/ontology/systems: Returns catalog of authorized healthcare terminology systems.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.terminology_validator import (
    BundleOntologyAuditRequest,
    ConceptLookupResponse,
    ConceptSuggestionResponse,
    OntologyAuditReport,
    TerminologySystemsResponse,
)
from app.services.terminology_validator import medical_ontology_validator

logger = logging.getLogger("nirmaya.api.terminology_validator")

router = APIRouter()


@router.post(
    "/audit",
    response_model=OntologyAuditReport,
    status_code=status.HTTP_200_OK,
    summary="Audit Medical Ontology Bindings in FHIR Bundle",
    description="Inspects all clinical concepts in a FHIR Document Bundle, categorizes their binding "
                "conformance (FULLY_BOUND, UNRECOGNIZED_CODE, INVALID_SYSTEM, MISSING_BINDING, DISPLAY_MISMATCH), "
                "and computes a weighted Ontology Compliance Score (0-100%).",
)
def audit_bundle_ontology(
    request: BundleOntologyAuditRequest,
) -> OntologyAuditReport:
    """Audits FHIR R4 Bundle for medical ontology bindings."""
    try:
        report = medical_ontology_validator.audit_bundle_concepts(
            bundle_data=request.bundle,
            strict_display_check=request.strictDisplayCheck,
        )
        return report
    except Exception as exc:
        logger.error(f"[audit_bundle_ontology] Error during ontology audit: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Medical ontology audit engine encountered an error: {str(exc)}",
        )


@router.get(
    "/lookup",
    response_model=ConceptLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Lookup and Verify Clinical Concept",
    description="Resolves a single clinical concept by system URI and code, verifying if it is valid "
                "and returning its authoritative official display nomenclature.",
)
def lookup_concept(
    system: str = Query(..., description="Canonical terminology system URI (e.g. http://snomed.info/sct)"),
    code: str = Query(..., description="Concept code to resolve"),
) -> ConceptLookupResponse:
    """Verifies and resolves a single clinical concept code."""
    return medical_ontology_validator.lookup_concept(system=system, code=code)


@router.get(
    "/suggest",
    response_model=ConceptSuggestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Suggest Standard Clinical Concepts",
    description="Searches standard SNOMED-CT, LOINC, and ICD-10 registries for concepts matching a "
                "natural language term or keyword.",
)
def suggest_concepts(
    query: str = Query(..., min_length=1, description="Clinical search keyword (e.g. 'hypertension', 'fever')"),
    system: Optional[str] = Query(None, description="Optional system URI filter"),
    limit: int = Query(5, ge=1, le=25, description="Maximum suggestions to return"),
) -> ConceptSuggestionResponse:
    """Returns ranked standard concept suggestions for a clinical term."""
    suggestions = medical_ontology_validator.suggest_concepts(
        query=query,
        system=system,
        limit=limit,
    )
    return ConceptSuggestionResponse(
        query=query,
        count=len(suggestions),
        suggestions=suggestions,
    )


@router.get(
    "/systems",
    response_model=TerminologySystemsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Authorized Terminology Systems",
    description="Returns the catalog of authorized healthcare terminology systems supported by NIRMAYA.",
)
def get_authorized_systems() -> TerminologySystemsResponse:
    """Returns the list of authorized healthcare terminology systems."""
    systems_list = medical_ontology_validator.get_registered_systems()
    return TerminologySystemsResponse(
        systems=systems_list,
        count=len(systems_list),
    )
