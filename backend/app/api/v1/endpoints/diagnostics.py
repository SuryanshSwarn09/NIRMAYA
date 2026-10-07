"""Diagnostic service requests and diagnostic reports API endpoints for NIRMAYA.

Provides RESTful operations for clinician lab requisitions (FHIR ServiceRequest)
and diagnostic laboratory reports (FHIR DiagnosticReport).
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException
from app.db.session import get_db
from app.fhir import (
    FHIRDiagnosticReport,
    FHIRServiceRequest,
    to_fhir_diagnostic_report,
    to_fhir_service_request,
)
from app.models.enums import (
    DiagnosticReportStatus,
    ServiceRequestPriority,
    ServiceRequestStatus,
    UserRole,
)
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.diagnostic import (
    DiagnosticOrderCreate,
    DiagnosticOrderFilter,
    DiagnosticOrderResponse,
    DiagnosticOrderUpdate,
    DiagnosticReportCreate,
    DiagnosticReportResponse,
    DiagnosticReportUpdate,
    DiagnosticReportWithObservationsResponse,
)
from app.schemas.observation import ObservationResponse
from app.services import (
    create_diagnostic_order,
    create_diagnostic_report,
    get_diagnostic_order,
    get_diagnostic_report,
    list_patient_diagnostic_orders,
    list_patient_diagnostic_reports,
    update_diagnostic_order,
    update_diagnostic_report,
)
from app.services import doctor as doctor_service
from app.services import patient as patient_service

router = APIRouter()


async def _verify_patient_access(
    db: AsyncSession,
    patient_id: str,
    current_user: User,
) -> None:
    """Verify read access for patient health records."""
    if current_user.role in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB):
        return

    patient = await patient_service.get_patient_by_id(db, patient_id)
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    if patient.user_id != current_user.id:
        raise PermissionDeniedException(
            message="You are not authorized to view this patient's diagnostic records"
        )


async def _verify_doctor_access(
    db: AsyncSession,
    current_user: User,
) -> Optional[str]:
    """Verify clinician authorization to requisition diagnostic tests."""
    if current_user.role == UserRole.ADMIN:
        return None

    if current_user.role != UserRole.DOCTOR:
        raise PermissionDeniedException(
            message="Only healthcare providers (doctors) or administrators can order diagnostic tests."
        )

    doctor = await doctor_service.get_doctor_by_user_id(db, current_user.id)
    return doctor.id if doctor else None


# ============================================================================
# 1. Diagnostic Order Endpoints (ServiceRequest)
# ============================================================================

@router.post(
    "/patients/{patient_id}/diagnostic-orders",
    response_model=APIResponse[DiagnosticOrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Requisition a new diagnostic test / laboratory order",
)
async def create_order_endpoint(
    patient_id: str,
    payload: DiagnosticOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[DiagnosticOrderResponse]:
    ordering_doctor_id = await _verify_doctor_access(db, current_user)
    order = await create_diagnostic_order(
        db=db,
        patient_id=patient_id,
        payload=payload,
        ordering_doctor_id=ordering_doctor_id,
    )
    return APIResponse(
        success=True,
        message="Diagnostic order successfully requisitioned",
        data=DiagnosticOrderResponse.model_validate(order),
    )


@router.get(
    "/patients/{patient_id}/diagnostic-orders",
    response_model=PaginatedResponse[DiagnosticOrderResponse],
    summary="List diagnostic orders for a patient",
)
async def list_orders_endpoint(
    patient_id: str,
    status_filter: Optional[ServiceRequestStatus] = Query(None, alias="status"),
    priority: Optional[ServiceRequestPriority] = None,
    category: Optional[str] = None,
    code_value: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[DiagnosticOrderResponse]:
    await _verify_patient_access(db, patient_id, current_user)
    filters = DiagnosticOrderFilter(
        status=status_filter,
        priority=priority,
        category=category,
        code_value=code_value,
    )
    orders, total_count = await list_patient_diagnostic_orders(
        db=db,
        patient_id=patient_id,
        filters=filters,
        page=page,
        limit=limit,
    )
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
    return PaginatedResponse(
        success=True,
        message="Diagnostic orders retrieved successfully",
        data=[DiagnosticOrderResponse.model_validate(o) for o in orders],
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
    "/diagnostic-orders/{order_id}",
    response_model=APIResponse[DiagnosticOrderResponse],
    summary="Retrieve diagnostic order by UUID",
)
async def get_order_endpoint(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[DiagnosticOrderResponse]:
    order = await get_diagnostic_order(db, order_id)
    if not order:
        raise EntityNotFoundException("DiagnosticOrder", order_id)
    await _verify_patient_access(db, order.patient_id, current_user)
    return APIResponse(
        success=True,
        message="Diagnostic order retrieved",
        data=DiagnosticOrderResponse.model_validate(order),
    )


@router.patch(
    "/diagnostic-orders/{order_id}",
    response_model=APIResponse[DiagnosticOrderResponse],
    summary="Update diagnostic order status or instructions",
)
async def update_order_endpoint(
    order_id: str,
    payload: DiagnosticOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[DiagnosticOrderResponse]:
    if current_user.role not in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB):
        raise PermissionDeniedException("Only clinical staff or lab technicians can update diagnostic orders")
    order = await update_diagnostic_order(db, order_id, payload)
    return APIResponse(
        success=True,
        message="Diagnostic order updated successfully",
        data=DiagnosticOrderResponse.model_validate(order),
    )


@router.get(
    "/diagnostic-orders/{order_id}/fhir",
    response_model=APIResponse[FHIRServiceRequest],
    summary="Export diagnostic order as HL7 FHIR Release 4 ServiceRequest resource",
)
async def export_order_fhir_endpoint(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[FHIRServiceRequest]:
    order = await get_diagnostic_order(db, order_id)
    if not order:
        raise EntityNotFoundException("DiagnosticOrder", order_id)
    await _verify_patient_access(db, order.patient_id, current_user)
    fhir_resource = to_fhir_service_request(order)
    return APIResponse(
        success=True,
        message="Diagnostic order exported as HL7 FHIR R4 ServiceRequest",
        data=fhir_resource,
    )


# ============================================================================
# 2. Diagnostic Report Endpoints (DiagnosticReport)
# ============================================================================

@router.post(
    "/patients/{patient_id}/diagnostic-reports",
    response_model=APIResponse[DiagnosticReportResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Issue a verified diagnostic report",
)
async def create_report_endpoint(
    patient_id: str,
    payload: DiagnosticReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[DiagnosticReportResponse]:
    if current_user.role not in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB):
        raise PermissionDeniedException("Only authorized laboratory or clinical staff can issue diagnostic reports")

    performer_doctor_id = None
    if current_user.role == UserRole.DOCTOR:
        doctor = await doctor_service.get_doctor_by_user_id(db, current_user.id)
        if doctor:
            performer_doctor_id = doctor.id

    report = await create_diagnostic_report(
        db=db,
        patient_id=patient_id,
        payload=payload,
        performer_doctor_id=performer_doctor_id,
    )
    return APIResponse(
        success=True,
        message="Diagnostic report issued successfully",
        data=DiagnosticReportResponse.model_validate(report),
    )


@router.get(
    "/patients/{patient_id}/diagnostic-reports",
    response_model=PaginatedResponse[DiagnosticReportResponse],
    summary="List diagnostic reports for a patient",
)
async def list_reports_endpoint(
    patient_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[DiagnosticReportResponse]:
    await _verify_patient_access(db, patient_id, current_user)
    reports, total_count = await list_patient_diagnostic_reports(
        db=db,
        patient_id=patient_id,
        page=page,
        limit=limit,
    )
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
    return PaginatedResponse(
        success=True,
        message="Diagnostic reports retrieved successfully",
        data=[DiagnosticReportResponse.model_validate(r) for r in reports],
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
    "/diagnostic-reports/{report_id}",
    response_model=APIResponse[DiagnosticReportWithObservationsResponse],
    summary="Retrieve diagnostic report by UUID with linked test observations",
)
async def get_report_endpoint(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[DiagnosticReportWithObservationsResponse]:
    report = await get_diagnostic_report(db, report_id)
    if not report:
        raise EntityNotFoundException("DiagnosticReport", report_id)
    await _verify_patient_access(db, report.patient_id, current_user)

    data = DiagnosticReportWithObservationsResponse(
        **DiagnosticReportResponse.model_validate(report).model_dump(),
        observations=[ObservationResponse.model_validate(obs) for obs in (report.observations or [])],
    )
    return APIResponse(
        success=True,
        message="Diagnostic report retrieved",
        data=data,
    )


@router.patch(
    "/diagnostic-reports/{report_id}",
    response_model=APIResponse[DiagnosticReportResponse],
    summary="Update or amend a diagnostic report",
)
async def update_report_endpoint(
    report_id: str,
    payload: DiagnosticReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[DiagnosticReportResponse]:
    if current_user.role not in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB):
        raise PermissionDeniedException("Only authorized laboratory or clinical staff can amend diagnostic reports")
    report = await update_diagnostic_report(db, report_id, payload)
    return APIResponse(
        success=True,
        message="Diagnostic report updated successfully",
        data=DiagnosticReportResponse.model_validate(report),
    )


@router.get(
    "/diagnostic-reports/{report_id}/fhir",
    response_model=APIResponse[FHIRDiagnosticReport],
    summary="Export diagnostic report as HL7 FHIR Release 4 DiagnosticReport resource",
)
async def export_report_fhir_endpoint(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[FHIRDiagnosticReport]:
    report = await get_diagnostic_report(db, report_id)
    if not report:
        raise EntityNotFoundException("DiagnosticReport", report_id)
    await _verify_patient_access(db, report.patient_id, current_user)
    fhir_resource = to_fhir_diagnostic_report(report)
    return APIResponse(
        success=True,
        message="Diagnostic report exported as HL7 FHIR R4 DiagnosticReport",
        data=fhir_resource,
    )
