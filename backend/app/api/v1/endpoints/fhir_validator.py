"""API endpoints for HL7 FHIR R4 Document Bundle validation and NRCES profile enforcement.

Endpoints:
- POST /api/v1/fhir/bundle/validate: Evaluates FHIR R4 bundle conformance against NRCES profiles.
- GET /api/v1/fhir/bundle/profiles: Returns catalog of supported NRCES clinical profiles.
- GET /api/v1/fhir/bundle/profiles/{profile_id}: Returns detailed profile metadata.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.fhir_validator import (
    BundleProfileType,
    BundleValidationRequest,
    BundleValidationResponse,
    ProfileMetadata,
    ProfilesCatalogResponse,
)
from app.services.fhir_validator import (
    NRCES_PROFILES,
    fhir_bundle_validator,
)

logger = logging.getLogger("nirmaya.api.fhir_validator")

router = APIRouter()


@router.post(
    "/bundle/validate",
    response_model=BundleValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate FHIR R4 Document Bundle",
    description="Validates a FHIR R4 Document Bundle for envelope structure, Composition root, "
                "referential integrity, profile cardinality, and standard clinical terminologies.",
)
def validate_fhir_bundle(
    request: BundleValidationRequest,
) -> BundleValidationResponse:
    """Validates FHIR R4 document bundle against NRCES India specifications."""
    try:
        report = fhir_bundle_validator.validate_bundle(
            bundle_data=request.bundle,
            expected_profile=request.expectedProfile,
            strict_mode=request.strictMode,
        )
        return report
    except Exception as exc:
        logger.error(f"[validate_fhir_bundle] Unexpected error during validation: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FHIR validation engine encountered an internal error: {str(exc)}",
        )


@router.get(
    "/bundle/profiles",
    response_model=ProfilesCatalogResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Supported NRCES FHIR Profiles",
    description="Retrieves the catalog of registered NRCES clinical profiles supported for ABDM exchange.",
)
def get_supported_profiles() -> ProfilesCatalogResponse:
    """Returns the list of supported NRCES clinical profiles."""
    profiles_list = fhir_bundle_validator.get_supported_profiles()
    return ProfilesCatalogResponse(
        profiles=profiles_list,
        count=len(profiles_list),
    )


@router.get(
    "/bundle/profiles/{profile_id}",
    response_model=ProfileMetadata,
    status_code=status.HTTP_200_OK,
    summary="Get NRCES Profile Specification Detail",
    description="Retrieves detailed metadata, canonical URL, and resource requirements for a single NRCES profile.",
)
def get_profile_detail(profile_id: str) -> ProfileMetadata:
    """Returns specification details for a single NRCES profile by identifier."""
    profile = NRCES_PROFILES.get(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_id}' not found. Supported profiles: {list(NRCES_PROFILES.keys())}",
        )
    return profile
