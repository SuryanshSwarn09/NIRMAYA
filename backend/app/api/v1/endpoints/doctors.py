from datetime import date, datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import (
    get_current_user,
    verify_doctor_modification_access,
)
from app.core.exceptions import (
    AppException,
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.db.session import get_db
from app.models.enums import MedicalSpecialty, SlotStatus, UserRole
from app.models.user import User
from app.schemas.appointment import (
    DoctorSlotResponse,
    SlotGenerateRequest,
    SlotGenerateResult,
    SlotHoldRequest,
    SlotHoldResponse,
    SlotReleaseResponse,
)
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.doctor import (
    DoctorProfileCreate,
    DoctorProfileResponse,
    DoctorProfileUpdate,
)
from app.services import doctor as doctor_service
from app.services import patient as patient_service
from app.services import slot_engine

router = APIRouter()




@router.post(
    "/",
    response_model=APIResponse[DoctorProfileResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Onboard or register a doctor clinical profile",
    description="Initializes a practitioner profile with licensing credentials, medical specialty, consultation fees, and optional ABDM HPR identifier.",
)
async def create_doctor(
    profile_in: DoctorProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DoctorProfileResponse]:
    """Create a new doctor clinical profile linked to a user account."""
    if current_user.role not in (UserRole.DOCTOR, UserRole.ADMIN):
        raise PermissionDeniedException(
            message=f"Role '{current_user.role.value}' is not authorized to register as a healthcare provider"
        )

    target_user_id = current_user.id
    if current_user.role == UserRole.ADMIN and profile_in.user_id:
        target_user_id = profile_in.user_id
    elif profile_in.user_id and profile_in.user_id != current_user.id:
        raise PermissionDeniedException(
            message="Cannot create doctor profile for another user account"
        )

    doctor = await doctor_service.create_doctor_profile(
        db=db,
        profile_in=profile_in,
        user_id=target_user_id,
    )
    return APIResponse(
        message="Doctor profile initialized successfully",
        data=DoctorProfileResponse.model_validate(doctor),
    )


@router.get(
    "/",
    response_model=PaginatedResponse[DoctorProfileResponse],
    summary="List, search, and filter doctor directory with pagination",
    description="Retrieve paginated doctor profiles filtered by clinical specialty, teleconsultation availability, maximum consultation fee, or text query.",
)
async def get_doctors(
    page: int = Query(default=1, ge=1, description="1-indexed page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Page limit ceiling"),
    query: Optional[str] = Query(default=None, description="Search across name, registration, council, hospital, HPR"),
    specialty: Optional[MedicalSpecialty] = Query(default=None, description="Filter by clinical medical specialty"),
    teleconsult_only: Optional[bool] = Query(default=None, description="Filter doctors offering teleconsultations"),
    max_fee: Optional[int] = Query(default=None, ge=0, description="Ceiling filter on consultation fee in INR"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[DoctorProfileResponse]:
    """List and search doctors with clinical filters and pagination."""
    skip = (page - 1) * limit
    items, total_count = await doctor_service.list_doctors(
        db=db,
        skip=skip,
        limit=limit,
        query=query,
        specialty=specialty,
        teleconsult_only=teleconsult_only,
        max_fee=max_fee,
    )

    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

    return PaginatedResponse(
        data=[DoctorProfileResponse.model_validate(d) for d in items],
        pagination=PaginationMeta(
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get(
    "/by-hpr/{hpr_id}",
    response_model=APIResponse[DoctorProfileResponse],
    summary="Resolve doctor clinical profile by ABDM HPR handle",
    description="ABDM interoperability resolution endpoint matching @hpr.abdm handle.",
)
async def get_doctor_by_hpr_identifier(
    hpr_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DoctorProfileResponse]:
    """Resolve doctor profile by ABDM HPR handle."""
    doctor = await doctor_service.get_doctor_by_hpr_id(db, hpr_id)
    if not doctor:
        raise EntityNotFoundException(entity_name="DoctorProfile (HPR)", entity_id=hpr_id)

    return APIResponse(
        message="Doctor profile resolved via ABDM HPR identity successfully",
        data=DoctorProfileResponse.model_validate(doctor),
    )


@router.get(
    "/by-reg/{registration_number}",
    response_model=APIResponse[DoctorProfileResponse],
    summary="Resolve doctor clinical profile by Medical Council registration number",
    description="Licensing resolution endpoint matching state or national medical council license.",
)
async def get_doctor_by_reg_number(
    registration_number: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DoctorProfileResponse]:
    """Resolve doctor profile by Medical Council registration number."""
    doctor = await doctor_service.get_doctor_by_registration_number(db, registration_number)
    if not doctor:
        raise EntityNotFoundException(
            entity_name="DoctorProfile (Registration)",
            entity_id=registration_number,
        )

    return APIResponse(
        message="Doctor profile resolved via registration license successfully",
        data=DoctorProfileResponse.model_validate(doctor),
    )


@router.get(
    "/{doctor_id}",
    response_model=APIResponse[DoctorProfileResponse],
    summary="Retrieve doctor clinical profile by UUID",
    description="Fetches full practitioner credentials, affiliation, and linked user identity by doctor UUID.",
)
async def get_doctor(
    doctor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DoctorProfileResponse]:
    """Fetch doctor profile by ID."""
    doctor = await doctor_service.get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise EntityNotFoundException(entity_name="DoctorProfile", entity_id=doctor_id)

    return APIResponse(
        message="Doctor profile retrieved successfully",
        data=DoctorProfileResponse.model_validate(doctor),
    )


@router.put(
    "/{doctor_id}",
    response_model=APIResponse[DoctorProfileResponse],
    summary="Update doctor practice credentials, fees, and consultation details",
    description="Updates existing doctor attributes, verifying unique registration and HPR constraints.",
)
async def update_doctor(
    doctor_id: str,
    update_in: DoctorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DoctorProfileResponse]:
    """Update doctor profile fields enforcing owner or administrator authorization."""
    await verify_doctor_modification_access(doctor_id=doctor_id, current_user=current_user, db=db)
    updated = await doctor_service.update_doctor_profile(
        db=db,
        doctor_id=doctor_id,
        update_in=update_in,
    )
    return APIResponse(
        message="Doctor profile updated successfully",
        data=DoctorProfileResponse.model_validate(updated),
    )


@router.delete(
    "/{doctor_id}",
    response_model=APIResponse[dict],
    summary="Delete a doctor clinical profile",
    description="Removes a doctor profile by UUID primary key.",
)
async def delete_doctor(
    doctor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Delete doctor profile by ID enforcing owner or administrator authorization."""
    await verify_doctor_modification_access(doctor_id=doctor_id, current_user=current_user, db=db)
    await doctor_service.delete_doctor_profile(db, doctor_id)
    return APIResponse(
        message="Doctor profile deleted successfully",
        data={"doctor_id": doctor_id, "deleted": True},
    )


# ============================================================================
# Doctor Consultation Availability Slots
# ============================================================================


@router.get(
    "/{doctor_id}/slots",
    response_model=APIResponse[List[DoctorSlotResponse]],
    summary="Query doctor consultation availability slots",
    description="Returns available or filtered time slots for a practitioner doctor.",
)
async def get_slots(
    doctor_id: str,
    target_date: Optional[date] = Query(None, description="Filter slots for a specific calendar date (YYYY-MM-DD)"),
    start_date: Optional[date] = Query(None, description="Start date window"),
    end_date: Optional[date] = Query(None, description="End date window"),
    slot_status: Optional[SlotStatus] = Query(None, description="Filter by slot status (e.g. available, booked)"),
    is_teleconsult: Optional[bool] = Query(None, description="Filter by teleconsultation readiness"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[DoctorSlotResponse]]:
    """Retrieve consultation slots for a doctor with optional status and temporal filtering."""
    slots = await slot_engine.get_doctor_slots(
        db=db,
        doctor_id=doctor_id,
        target_date=target_date,
        start_date=start_date,
        end_date=end_date,
        status=slot_status,
        is_teleconsult=is_teleconsult,
    )
    return APIResponse(
        message="Doctor consultation slots retrieved successfully",
        data=[DoctorSlotResponse.model_validate(s) for s in slots],
    )


@router.post(
    "/{doctor_id}/slots/generate",
    response_model=APIResponse[SlotGenerateResult],
    status_code=status.HTTP_201_CREATED,
    summary="Generate conflict-free consultation slots",
    description="Computes and persists discrete availability slots based on working hours and break windows.",
)
async def generate_slots(
    doctor_id: str,
    request: SlotGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SlotGenerateResult]:
    """Generate availability slots for a doctor enforcing owner doctor or administrator authorization."""
    await verify_doctor_modification_access(doctor_id=doctor_id, current_user=current_user, db=db)
    request.doctor_id = doctor_id
    result = await slot_engine.generate_slots_for_doctor(db=db, request=request)
    return APIResponse(
        message=f"Generated {result.total_generated} consultation slots ({result.total_skipped_existing} existing slots skipped)",
        data=result,
    )


@router.post(
    "/{doctor_id}/slots/{slot_id}/hold",
    response_model=APIResponse[SlotHoldResponse],
    summary="Hold a consultation slot for checkout",
    description="Places a temporary 1-30 minute lock on a consultation slot to prevent race conditions during booking checkout.",
)
async def hold_doctor_slot(
    doctor_id: str,
    slot_id: str,
    payload: Optional[SlotHoldRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SlotHoldResponse]:
    """Temporarily reserve a slot for the authenticated patient."""
    patient = await patient_service.get_patient_by_user_id(db, current_user.id)
    if not patient and current_user.role != UserRole.ADMIN:
        raise AppException(
            message="Authenticated user does not have an active patient vault profile",
            error_code="PATIENT_PROFILE_REQUIRED",
            status_code=400,
        )

    patient_id = patient.id if patient else current_user.id
    duration = payload.hold_duration_minutes if payload else 10

    slot = await slot_engine.hold_slot(
        db=db,
        slot_id=slot_id,
        patient_id=patient_id,
        duration_minutes=duration,
    )

    remaining_seconds = 0
    if slot.held_until:
        remaining_seconds = max(0, int((slot.held_until - datetime.now(timezone.utc)).total_seconds()))

    hold_data = SlotHoldResponse(
        slot_id=slot.id,
        doctor_id=slot.doctor_id,
        status=slot.status,
        held_until=slot.held_until or datetime.now(timezone.utc),
        held_by_patient_id=slot.held_by_patient_id or patient_id,
        hold_duration_seconds=remaining_seconds,
    )

    return APIResponse(
        message=f"Slot successfully reserved for {duration} minutes",
        data=hold_data,
    )


@router.post(
    "/{doctor_id}/slots/{slot_id}/release",
    response_model=APIResponse[SlotReleaseResponse],
    summary="Release a held consultation slot",
    description="Manually relinquishes a temporary slot reservation, returning the slot to available status immediately.",
)
async def release_doctor_slot_hold(
    doctor_id: str,
    slot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SlotReleaseResponse]:
    """Release a held slot back to AVAILABLE status."""
    is_admin = current_user.role == UserRole.ADMIN
    patient = await patient_service.get_patient_by_user_id(db, current_user.id)
    patient_id = patient.id if patient else current_user.id

    slot = await slot_engine.release_slot_hold(
        db=db,
        slot_id=slot_id,
        patient_id=patient_id,
        force_admin=is_admin,
    )

    return APIResponse(
        message="Consultation slot released back to available",
        data=SlotReleaseResponse(
            slot_id=slot.id,
            status=slot.status,
            released=True,
        ),
    )




