"""Clinical Medication Catalog and Formulary API endpoints for NIRMAYA.

Provides RESTful search, retrieval, and HL7 FHIR Release 4 Medication resource serialization
for clinical drugs, active substances, and hospital formulary listings.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import PermissionDeniedException
from app.db.session import get_db
from app.fhir import FHIRMedication, to_fhir_medication
from app.models.enums import (
    AdministrationRoute,
    FormularyTier,
    MedicationForm,
    MedicationStatus,
    UserRole,
)
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.medication import (
    MedicationCreate,
    MedicationResponse,
    MedicationUpdate,
    TherapeuticClassSummary,
)
from app.services import medication as medication_service

router = APIRouter(prefix="/medications", tags=["Medications"])


def _verify_medication_admin_access(current_user: User) -> None:
    """Verify that current user possesses administrative or clinical provider authority."""
    if current_user.role not in (UserRole.ADMIN, UserRole.DOCTOR):
        raise PermissionDeniedException(
            message="Only verified healthcare providers and administrators can manage formulary medications."
        )


@router.get(
    "",
    response_model=PaginatedResponse[MedicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Search medication formulary catalog",
)
async def list_medications(
    q: Optional[str] = Query(None, description="Search term for medication name, generic, brand, ingredient, or RxNorm"),
    form: Optional[MedicationForm] = Query(None, description="Filter by dosage formulation (e.g. tablet, capsule, injection)"),
    route: Optional[AdministrationRoute] = Query(None, description="Filter by administration route (e.g. oral, subcutaneous)"),
    tier: Optional[FormularyTier] = Query(None, description="Filter by formulary tier (e.g. tier_1_generic, tier_2_preferred_brand)"),
    atc_prefix: Optional[str] = Query(None, description="Filter by WHO-ATC therapeutic category prefix (e.g. A10, C10, J01)"),
    is_prescription_required: Optional[bool] = Query(None, description="Filter by prescription legal requirement"),
    is_controlled_substance: Optional[bool] = Query(None, description="Filter by scheduled controlled substance status"),
    medication_status: Optional[MedicationStatus] = Query(None, alias="status", description="Filter by catalog availability status"),
    page: int = Query(1, ge=1, description="1-indexed page number"),
    limit: int = Query(50, ge=1, le=100, description="Page item limit"),
    offset: Optional[int] = Query(None, ge=0, description="Optional explicit offset override"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[MedicationResponse]:
    """Search and filter clinical medications with comprehensive metadata."""
    effective_offset = offset if offset is not None else (page - 1) * limit

    items, total = await medication_service.search_medications(
        db=db,
        q=q,
        form=form,
        route=route,
        tier=tier,
        atc_prefix=atc_prefix,
        is_prescription_required=is_prescription_required,
        is_controlled_substance=is_controlled_substance,
        status=medication_status,
        limit=limit,
        offset=effective_offset,
    )

    page_items = [MedicationResponse.model_validate(m) for m in items]
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    calculated_page = (effective_offset // limit) + 1 if limit > 0 else 1

    return PaginatedResponse(
        success=True,
        data=page_items,
        pagination=PaginationMeta(
            total_count=total,
            page=calculated_page,
            limit=limit,
            total_pages=total_pages,
            has_next=calculated_page < total_pages,
            has_prev=calculated_page > 1,
        ),
    )


@router.get(
    "/classes",
    response_model=APIResponse[List[TherapeuticClassSummary]],
    status_code=status.HTTP_200_OK,
    summary="List WHO-ATC therapeutic classes",
)
async def get_therapeutic_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[List[TherapeuticClassSummary]]:
    """Retrieve aggregate counts of catalog drugs grouped by WHO-ATC therapeutic systems."""
    classes = await medication_service.get_therapeutic_classes(db)
    return APIResponse(
        success=True,
        message="Retrieved WHO-ATC therapeutic class summaries",
        data=classes,
    )


@router.get(
    "/{id}",
    response_model=APIResponse[MedicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve medication details",
)
async def get_medication(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[MedicationResponse]:
    """Retrieve full clinical details for a specific medication by UUID or RxNorm CUI."""
    med = await medication_service.get_medication_by_id(db, id)
    return APIResponse(
        success=True,
        message=f"Retrieved medication {med.name}",
        data=MedicationResponse.model_validate(med),
    )


@router.get(
    "/{id}/fhir",
    response_model=APIResponse[FHIRMedication],
    status_code=status.HTTP_200_OK,
    summary="Export medication as HL7 FHIR R4 resource",
)
async def get_medication_fhir(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[FHIRMedication]:
    """Serialize internal medication model into HL7 FHIR Release 4 Medication resource."""
    med = await medication_service.get_medication_by_id(db, id)
    fhir_resource = to_fhir_medication(med)
    return APIResponse(
        success=True,
        message=f"Exported FHIR R4 Medication resource for {med.name}",
        data=fhir_resource,
    )


@router.post(
    "",
    response_model=APIResponse[MedicationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new medication formulary entry",
)
async def create_medication(
    payload: MedicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[MedicationResponse]:
    """Register a new clinical drug into the formulary catalog (Doctor or Admin only)."""
    _verify_medication_admin_access(current_user)
    med = await medication_service.create_medication(db, payload)
    return APIResponse(
        success=True,
        message=f"Successfully registered medication {med.name}",
        data=MedicationResponse.model_validate(med),
    )


@router.patch(
    "/{id}",
    response_model=APIResponse[MedicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Update medication formulary entry",
)
async def update_medication(
    id: str,
    payload: MedicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[MedicationResponse]:
    """Update properties of an existing formulary drug (Doctor or Admin only)."""
    _verify_medication_admin_access(current_user)
    med = await medication_service.update_medication(db, id, payload)
    return APIResponse(
        success=True,
        message=f"Successfully updated medication {med.name}",
        data=MedicationResponse.model_validate(med),
    )
