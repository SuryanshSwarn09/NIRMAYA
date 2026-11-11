"""FastAPI REST API Endpoints for Day 88: Express 45-Second Doctor Consultation Mode (/doctor).

Exposes:
- GET /api/v1/doctor/express-consultation/templates (Curated complaint chips & Rx bundles)
- GET /api/v1/doctor/express-consultation/patient-safety/{patient_id} (Allergy & safety profile)
- POST /api/v1/doctor/express-consultation/check-safety (Medication cross-checking)
- POST /api/v1/doctor/express-consultation/submit (Sub-50ms atomic encounter completion & queue advance)
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Path, Query, status
from pydantic import BaseModel, Field

from app.schemas.common import APIResponse
from app.schemas.express_consultation import (
    ChiefComplaintTemplate,
    ExpressEncounterSubmitRequest,
    ExpressEncounterSubmitResponse,
    PatientAllergyProfile,
    PrescriptionBundleTemplate,
    QuickPrescriptionItem,
)
from app.services.express_consultation_service import express_consultation_service

router = APIRouter(prefix="/doctor/express-consultation", tags=["Express 45-Second Doctor Consultation"])


class ExpressTemplatesResponse(BaseModel):
    """Container for curated complaint chips and prescription bundles."""
    chief_complaints: List[ChiefComplaintTemplate]
    prescription_bundles: List[PrescriptionBundleTemplate]


class SafetyCheckRequest(BaseModel):
    """Payload to cross-check draft medication items against patient allergies."""
    patient_id: str
    medications: List[QuickPrescriptionItem]


class SafetyCheckResponse(BaseModel):
    """Safety evaluation outcome."""
    is_safe: bool
    conflicts: List[str] = Field(default_factory=list)
    alert_banner: str


@router.get(
    "/templates",
    response_model=APIResponse[ExpressTemplatesResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve curated 1-click chief complaints and Rx bundle templates",
    description="Returns pre-coded SNOMED CT and ICD-10 complaint chips and Ayushman Bharat standard treatment bundles.",
)
async def get_express_templates(
    category: Optional[str] = Query(default=None, description="Optional specialty filter (general, cardio, metabolic, pediatrics)"),
) -> APIResponse[ExpressTemplatesResponse]:
    """Fetch 1-click templates for rapid consultation execution."""
    complaints = express_consultation_service.get_chief_complaints(category=category)
    bundles = express_consultation_service.get_prescription_bundles(category=category)
    data = ExpressTemplatesResponse(
        chief_complaints=complaints,
        prescription_bundles=bundles,
    )
    return APIResponse(
        success=True,
        data=data,
        message="Curated express consultation templates loaded.",
    )


@router.get(
    "/patient-safety/{patient_id}",
    response_model=APIResponse[PatientAllergyProfile],
    status_code=status.HTTP_200_OK,
    summary="Fetch patient allergy & contraindication safety profile",
    description="Loads high-contrast safety banner, active drug allergies, and contraindications before prescribing.",
)
async def get_patient_safety_profile(
    patient_id: str = Path(..., description="Patient Profile UUID"),
) -> APIResponse[PatientAllergyProfile]:
    """Retrieve verified patient allergy alerts."""
    profile = express_consultation_service.get_patient_safety_profile(patient_id=patient_id)
    return APIResponse(
        success=True,
        data=profile,
        message="Patient safety and allergy profile loaded.",
    )


@router.post(
    "/check-safety",
    response_model=APIResponse[SafetyCheckResponse],
    status_code=status.HTTP_200_OK,
    summary="Cross-check draft medications against patient allergy history",
    description="Evaluates proposed items against Penicillin, Sulfa, and NSAID hypersensitivity markers.",
)
async def check_medication_safety(
    request: SafetyCheckRequest,
) -> APIResponse[SafetyCheckResponse]:
    """Detects immediate contraindications before encounter signing."""
    is_safe, conflicts = express_consultation_service.check_medication_safety(
        patient_id=request.patient_id,
        medications=request.medications,
    )
    profile = express_consultation_service.get_patient_safety_profile(request.patient_id)
    alert = profile.safety_alert_banner if not is_safe or profile.has_known_allergies else "NO KNOWN DRUG ALLERGIES (NKDA)"

    return APIResponse(
        success=True,
        data=SafetyCheckResponse(
            is_safe=is_safe,
            conflicts=conflicts,
            alert_banner=alert,
        ),
        message="Medication safety cross-check completed.",
    )


@router.post(
    "/submit",
    response_model=APIResponse[ExpressEncounterSubmitResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Sub-50ms fast-track encounter sign and OPD queue advancement",
    description="Cryptographically seals encounter with Doctor HPR, mints FHIR bundle, and summons next patient.",
)
async def submit_express_encounter(
    request: ExpressEncounterSubmitRequest,
) -> APIResponse[ExpressEncounterSubmitResponse]:
    """Performs atomic consultation sign & queue advance transaction."""
    response = express_consultation_service.submit_express_encounter(request=request)
    return APIResponse(
        success=True,
        data=response,
        message=f"Encounter {response.encounter_id} signed and completed in {response.latency_ms}ms.",
    )
