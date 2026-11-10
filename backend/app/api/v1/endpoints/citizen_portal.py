"""FastAPI endpoints for the Strict CoWIN/DigiLocker 3-Tile Citizen Portal.

Exposes:
- GET /api/v1/patient/citizen-portal/tiles (Aggregated 3-tile payload)
- GET /api/v1/patient/citizen-portal/qr-token (OPD Counter check-in token)
- GET /api/v1/patient/citizen-portal/medicines (Plain language active medicines)
- GET /api/v1/patient/citizen-portal/visits (Chronological doctor visits and reports)
"""

from typing import List, Optional
from fastapi import APIRouter, Query, status

from app.schemas.common import APIResponse
from app.schemas.citizen_portal import (
    CitizenActiveMedicineItem,
    CitizenHealthIdSummary,
    CitizenThreeTileResponse,
    CitizenVisitReportItem,
    HospitalCheckInQrResponse,
)
from app.services.citizen_portal_service import citizen_portal_service

router = APIRouter(prefix="/patient/citizen-portal", tags=["Strict 3-Tile Citizen Portal"])


@router.get(
    "/tiles",
    response_model=APIResponse[CitizenThreeTileResponse],
    status_code=status.HTTP_200_OK,
    summary="Fetch aggregated 3-Tile citizen layout payload",
    description="Sub-10ms atomic aggregation of Tile 1 (My Health ID), Tile 2 (Active Medicines), and Tile 3 (Doctor Visits & Reports).",
)
async def get_citizen_three_tiles(
    patient_id: str = Query(
        default="pat-arun-kumar-01",
        description="Patient Profile UUID or dependent context identifier",
    ),
) -> APIResponse[CitizenThreeTileResponse]:
    """Retrieve full 3-tile payload for primary adult or dependent profile."""
    three_tiles = citizen_portal_service.get_citizen_three_tiles(patient_id=patient_id)
    return APIResponse(
        success=True,
        data=three_tiles,
        message="Citizen 3-tile health profile loaded successfully.",
    )


@router.get(
    "/qr-token",
    response_model=APIResponse[HospitalCheckInQrResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate high-contrast hospital counter check-in QR token",
)
async def get_hospital_checkin_qr(
    patient_id: str = Query(
        default="pat-arun-kumar-01",
        description="Patient Profile UUID to generate check-in QR for",
    ),
    facility_context: Optional[str] = Query(
        default=None,
        description="Target hospital or OPD desk code",
    ),
) -> APIResponse[HospitalCheckInQrResponse]:
    """Issues high-contrast scannable QR payload for hospital OPD registration scanners."""
    qr_response = citizen_portal_service.generate_hospital_checkin_qr(
        patient_id=patient_id,
        facility_context=facility_context,
    )
    return APIResponse(
        success=True,
        data=qr_response,
        message="Hospital OPD counter check-in QR token generated.",
    )



@router.get(
    "/medicines",
    response_model=APIResponse[List[CitizenActiveMedicineItem]],
    status_code=status.HTTP_200_OK,
    summary="Fetch plain language active medication schedule",
)
async def get_active_medicines(
    patient_id: str = Query(
        default="pat-arun-kumar-01",
        description="Patient Profile UUID",
    ),
) -> APIResponse[List[CitizenActiveMedicineItem]]:
    """Returns Tile 2 plain medication schedule without Latin abbreviations."""
    medicines = citizen_portal_service.get_active_medicines_tile(patient_id=patient_id)
    return APIResponse(
        success=True,
        data=medicines,
        message=f"Retrieved {len(medicines)} active prescription items.",
    )


@router.get(
    "/visits",
    response_model=APIResponse[List[CitizenVisitReportItem]],
    status_code=status.HTTP_200_OK,
    summary="Fetch chronological doctor visits and diagnostic reports",
)
async def get_past_visits(
    patient_id: str = Query(
        default="pat-arun-kumar-01",
        description="Patient Profile UUID",
    ),
) -> APIResponse[List[CitizenVisitReportItem]]:
    """Returns Tile 3 past clinical encounters with plain diagnoses and signed PDFs."""
    visits = citizen_portal_service.get_past_visits_tile(patient_id=patient_id)
    return APIResponse(
        success=True,
        data=visits,
        message=f"Retrieved {len(visits)} past clinical consultations.",
    )
