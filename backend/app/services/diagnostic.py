"""Diagnostic service requests and diagnostic reports service layer for NIRMAYA.

Provides business logic for placing laboratory/diagnostic orders, tracking fulfillment,
issuing verified diagnostic reports, linking clinical observations, and managing
clinical statuses aligned with HL7 FHIR Release 4.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException, EntityNotFoundException
from app.models.appointment import Appointment
from app.models.diagnostic import DiagnosticOrder, DiagnosticReport
from app.models.doctor import DoctorProfile
from app.models.enums import (
    DiagnosticReportStatus,
    ObservationInterpretation,
    ServiceRequestStatus,
)
from app.models.observation import ClinicalObservation
from app.models.patient import PatientProfile
from app.schemas.diagnostic import (
    DiagnosticOrderCreate,
    DiagnosticOrderFilter,
    DiagnosticOrderUpdate,
    DiagnosticReportCreate,
    DiagnosticReportUpdate,
)


# ============================================================================
# Diagnostic Order (ServiceRequest) Operations
# ============================================================================

async def create_diagnostic_order(
    db: AsyncSession,
    patient_id: str,
    payload: DiagnosticOrderCreate,
    ordering_doctor_id: Optional[str] = None,
) -> DiagnosticOrder:
    """Create a new diagnostic service request / laboratory order for a patient."""
    # 1. Verify patient exists
    patient = await db.scalar(select(PatientProfile).where(PatientProfile.id == patient_id))
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    # 2. Verify ordering doctor
    effective_doctor_id = payload.doctor_id or ordering_doctor_id
    if effective_doctor_id:
        doctor = await db.scalar(select(DoctorProfile).where(DoctorProfile.id == effective_doctor_id))
        if not doctor:
            raise EntityNotFoundException("Doctor", effective_doctor_id)

    # 3. Verify encounter context if provided
    if payload.encounter_id:
        appt = await db.scalar(select(Appointment).where(Appointment.id == payload.encounter_id))
        if not appt:
            raise EntityNotFoundException("Appointment", payload.encounter_id)

    # 4. Instantiate entity
    order = DiagnosticOrder(
        patient_id=patient_id,
        doctor_id=effective_doctor_id,
        encounter_id=payload.encounter_id,
        status=payload.status or ServiceRequestStatus.ACTIVE,
        intent=payload.intent,
        priority=payload.priority,
        category=payload.category,
        code_coding_system=payload.code_coding_system,
        code_value=payload.code_value,
        code_display=payload.code_display,
        reason_code=payload.reason_code,
        reason_description=payload.reason_description,
        specimen_type=payload.specimen_type,
        notes=payload.notes,
    )

    db.add(order)
    await db.commit()

    return await get_diagnostic_order(db, order.id)  # type: ignore[return-value]


async def get_diagnostic_order(
    db: AsyncSession,
    order_id: str,
) -> Optional[DiagnosticOrder]:
    """Retrieve a diagnostic order by UUID with eager-loaded relationships."""
    stmt = (
        select(DiagnosticOrder)
        .where(DiagnosticOrder.id == order_id)
        .options(
            selectinload(DiagnosticOrder.patient).selectinload(PatientProfile.user),
            selectinload(DiagnosticOrder.doctor).selectinload(DoctorProfile.user),
            selectinload(DiagnosticOrder.encounter),
            selectinload(DiagnosticOrder.reports),
        )
    )
    return await db.scalar(stmt)


async def list_patient_diagnostic_orders(
    db: AsyncSession,
    patient_id: str,
    filters: Optional[DiagnosticOrderFilter] = None,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[DiagnosticOrder], int]:
    """Query paginated diagnostic orders for a patient with optional filters."""
    # Verify patient exists
    patient = await db.scalar(select(PatientProfile).where(PatientProfile.id == patient_id))
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    query = select(DiagnosticOrder).where(DiagnosticOrder.patient_id == patient_id)

    if filters:
        if filters.status:
            query = query.where(DiagnosticOrder.status == filters.status)
        if filters.priority:
            query = query.where(DiagnosticOrder.priority == filters.priority)
        if filters.category:
            query = query.where(DiagnosticOrder.category == filters.category)
        if filters.code_value:
            query = query.where(DiagnosticOrder.code_value == filters.code_value)
        if filters.encounter_id:
            query = query.where(DiagnosticOrder.encounter_id == filters.encounter_id)

    # Count total
    count_stmt = select(func.count()).select_from(query.subquery())
    total_count = (await db.scalar(count_stmt)) or 0

    # Paginate and order newest first
    offset = (page - 1) * limit
    paged_stmt = (
        query.order_by(DiagnosticOrder.created_at.desc())
        .offset(offset)
        .limit(limit)
        .options(
            selectinload(DiagnosticOrder.patient).selectinload(PatientProfile.user),
            selectinload(DiagnosticOrder.doctor).selectinload(DoctorProfile.user),
            selectinload(DiagnosticOrder.reports),
        )
    )
    result = await db.scalars(paged_stmt)
    return list(result.all()), total_count


async def update_diagnostic_order(
    db: AsyncSession,
    order_id: str,
    payload: DiagnosticOrderUpdate,
) -> DiagnosticOrder:
    """Update status, priority, or notes on an existing diagnostic order."""
    order = await get_diagnostic_order(db, order_id)
    if not order:
        raise EntityNotFoundException("DiagnosticOrder", order_id)

    if payload.status is not None:
        order.status = payload.status
    if payload.priority is not None:
        order.priority = payload.priority
    if payload.notes is not None:
        order.notes = payload.notes
    if payload.reason_description is not None:
        order.reason_description = payload.reason_description

    await db.commit()
    await db.refresh(order)
    return order


# ============================================================================
# Diagnostic Report Operations
# ============================================================================

async def create_diagnostic_report(
    db: AsyncSession,
    patient_id: str,
    payload: DiagnosticReportCreate,
    performer_doctor_id: Optional[str] = None,
) -> DiagnosticReport:
    """Issue a verified diagnostic report fulfilling an order or standalone test."""
    # 1. Verify patient exists
    patient = await db.scalar(select(PatientProfile).where(PatientProfile.id == patient_id))
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    # 2. Check and link order if provided
    order = None
    if payload.order_id:
        order = await get_diagnostic_order(db, payload.order_id)
        if not order:
            raise EntityNotFoundException("DiagnosticOrder", payload.order_id)
        if order.patient_id != patient_id:
            raise AppException("Diagnostic order belongs to a different patient", error_code="VALIDATION_ERROR")
        # Automatically mark fulfilled order as COMPLETED
        order.status = ServiceRequestStatus.COMPLETED

    # 3. Verify performer doctor if provided
    effective_performer_id = payload.performer_id or performer_doctor_id
    if effective_performer_id:
        doc = await db.scalar(select(DoctorProfile).where(DoctorProfile.id == effective_performer_id))
        if not doc:
            raise EntityNotFoundException("Doctor", effective_performer_id)

    # 4. Check encounter
    if payload.encounter_id:
        appt = await db.scalar(select(Appointment).where(Appointment.id == payload.encounter_id))
        if not appt:
            raise EntityNotFoundException("Appointment", payload.encounter_id)

    now = datetime.now(timezone.utc)
    effective_dt = payload.effective_date_time or now

    # 5. Check linked observations
    linked_observations: List[ClinicalObservation] = []
    has_abnormal_observation = False
    if payload.observation_ids:
        for obs_id in payload.observation_ids:
            obs = await db.scalar(select(ClinicalObservation).where(ClinicalObservation.id == obs_id))
            if not obs:
                raise EntityNotFoundException("ClinicalObservation", obs_id)
            if obs.patient_id != patient_id:
                raise AppException(f"Observation {obs_id} belongs to a different patient", error_code="VALIDATION_ERROR")
            linked_observations.append(obs)
            if obs.interpretation in (
                ObservationInterpretation.HIGH,
                ObservationInterpretation.LOW,
                ObservationInterpretation.CRITICALLY_HIGH,
                ObservationInterpretation.CRITICALLY_LOW,
                ObservationInterpretation.ABNORMAL,
            ):
                has_abnormal_observation = True

    is_abnormal_final = payload.is_abnormal or has_abnormal_observation

    # 6. Create report entity
    report = DiagnosticReport(
        patient_id=patient_id,
        order_id=payload.order_id,
        encounter_id=payload.encounter_id,
        performer_id=effective_performer_id,
        performer_name=payload.performer_name or "Metropolis Diagnostics & Pathology Lab",
        status=payload.status or DiagnosticReportStatus.FINAL,
        category=payload.category,
        code_coding_system=payload.code_coding_system,
        code_value=payload.code_value,
        code_display=payload.code_display,
        effective_date_time=effective_dt,
        issued_date_time=now,
        conclusion=payload.conclusion,
        conclusion_code=payload.conclusion_code,
        is_abnormal=is_abnormal_final,
        report_data=payload.report_data,
    )

    db.add(report)
    await db.flush()  # Generate report.id

    # Link observations to this report
    for obs in linked_observations:
        obs.report_id = report.id

    await db.commit()

    return await get_diagnostic_report(db, report.id)  # type: ignore[return-value]


async def get_diagnostic_report(
    db: AsyncSession,
    report_id: str,
) -> Optional[DiagnosticReport]:
    """Retrieve a diagnostic report by UUID with eager-loaded patient and observations."""
    stmt = (
        select(DiagnosticReport)
        .where(DiagnosticReport.id == report_id)
        .options(
            selectinload(DiagnosticReport.patient).selectinload(PatientProfile.user),
            selectinload(DiagnosticReport.performer).selectinload(DoctorProfile.user),
            selectinload(DiagnosticReport.order),
            selectinload(DiagnosticReport.observations),
        )
    )
    return await db.scalar(stmt)


async def list_patient_diagnostic_reports(
    db: AsyncSession,
    patient_id: str,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[DiagnosticReport], int]:
    """Query paginated diagnostic reports for a patient."""
    patient = await db.scalar(select(PatientProfile).where(PatientProfile.id == patient_id))
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    query = select(DiagnosticReport).where(DiagnosticReport.patient_id == patient_id)
    count_stmt = select(func.count()).select_from(query.subquery())
    total_count = (await db.scalar(count_stmt)) or 0

    offset = (page - 1) * limit
    paged_stmt = (
        query.order_by(DiagnosticReport.effective_date_time.desc())
        .offset(offset)
        .limit(limit)
        .options(
            selectinload(DiagnosticReport.patient).selectinload(PatientProfile.user),
            selectinload(DiagnosticReport.performer).selectinload(DoctorProfile.user),
            selectinload(DiagnosticReport.order),
            selectinload(DiagnosticReport.observations),
        )
    )
    result = await db.scalars(paged_stmt)
    return list(result.all()), total_count


async def update_diagnostic_report(
    db: AsyncSession,
    report_id: str,
    payload: DiagnosticReportUpdate,
) -> DiagnosticReport:
    """Update or amend an existing diagnostic report."""
    report = await get_diagnostic_report(db, report_id)
    if not report:
        raise EntityNotFoundException("DiagnosticReport", report_id)

    if payload.status is not None:
        report.status = payload.status
    if payload.conclusion is not None:
        report.conclusion = payload.conclusion
    if payload.conclusion_code is not None:
        report.conclusion_code = payload.conclusion_code
    if payload.is_abnormal is not None:
        report.is_abnormal = payload.is_abnormal
    if payload.report_data is not None:
        report.report_data = payload.report_data

    await db.commit()
    await db.refresh(report)
    return report
