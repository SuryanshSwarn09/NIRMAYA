"""Clinical Observation & Vital Signs service layer for NIRMAYA platform.

Provides business logic for recording vital signs, calculating body metrics (BMI),
evaluating physiological reference ranges, querying longitudinal telemetry, and
synthesizing latest clinical vital sign panels.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import EntityNotFoundException
from app.models.appointment import Appointment
from app.models.doctor import DoctorProfile
from app.models.enums import (
    ObservationCategory,
    ObservationInterpretation,
    ObservationStatus,
)
from app.models.observation import ClinicalObservation
from app.models.patient import PatientProfile
from app.schemas.observation import (
    ObservationCreate,
    ObservationFilter,
    ObservationUpdate,
    VitalsSummaryResponse,
)

# Standard LOINC Codes for Common Clinical Vital Signs
LOINC_BLOOD_PRESSURE_PANEL = "85354-9"
LOINC_HEART_RATE = "8867-4"
LOINC_RESPIRATORY_RATE = "9279-1"
LOINC_BODY_TEMPERATURE = "8310-5"
LOINC_OXYGEN_SATURATION = "2708-6"
LOINC_BODY_MASS_INDEX = "39156-5"
LOINC_BODY_WEIGHT = "29463-7"
LOINC_BODY_HEIGHT = "8302-2"
LOINC_FASTING_GLUCOSE = "1558-6"


def calculate_bmi(weight_kg: float, height_cm: float) -> Tuple[float, ObservationInterpretation]:
    """Calculate Body Mass Index (BMI) and determine clinical interpretation.

    Formula: BMI = weight (kg) / (height (m) ^ 2)
    Reference Ranges (WHO standard):
        Underweight: < 18.5
        Normal: 18.5 - 24.9
        Overweight: 25.0 - 29.9
        Obese: >= 30.0
    """
    height_m = height_cm / 100.0
    if height_m <= 0:
        raise ValueError("Height must be greater than zero")

    bmi = round(weight_kg / (height_m * height_m), 1)

    if bmi < 18.5:
        interpretation = ObservationInterpretation.LOW
    elif bmi <= 24.9:
        interpretation = ObservationInterpretation.NORMAL
    elif bmi < 30.0:
        interpretation = ObservationInterpretation.HIGH
    else:
        interpretation = ObservationInterpretation.CRITICALLY_HIGH

    return bmi, interpretation


async def record_observation(
    db: AsyncSession,
    patient_id: str,
    payload: ObservationCreate,
    performer_doctor_id: Optional[str] = None,
) -> ClinicalObservation:
    """Record a new observation or vital sign onto a patient's clinical file.

    Args:
        db: Async database session.
        patient_id: UUID of subject patient.
        payload: Validated observation attributes.
        performer_doctor_id: Optional UUID of recording DoctorProfile.

    Returns:
        The newly persisted ClinicalObservation instance.

    Raises:
        EntityNotFoundException: If patient, encounter, or doctor cannot be found.
    """
    # 1. Validate patient existence
    patient = await db.scalar(
        select(PatientProfile).where(PatientProfile.id == patient_id)
    )
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    # 2. Validate encounter if linked
    if payload.encounter_id:
        encounter = await db.scalar(
            select(Appointment).where(
                Appointment.id == payload.encounter_id,
                Appointment.patient_id == patient_id,
            )
        )
        if not encounter:
            raise EntityNotFoundException("Appointment encounter", payload.encounter_id)

    # 3. Validate performer doctor if linked
    if performer_doctor_id:
        doc = await db.scalar(
            select(DoctorProfile).where(DoctorProfile.id == performer_doctor_id)
        )
        if not doc:
            raise EntityNotFoundException("Doctor", performer_doctor_id)

    # 4. Serialize components to JSON dictionaries if present
    components_data = None
    if payload.components:
        components_data = [
            c.model_dump(mode="json") if hasattr(c, "model_dump") else dict(c)
            for c in payload.components
        ]

    effective_dt = payload.effective_date_time or datetime.now(timezone.utc)
    issued_dt = datetime.now(timezone.utc)

    # 5. Persist Observation
    observation = ClinicalObservation(
        patient_id=patient_id,
        encounter_id=payload.encounter_id,
        performer_doctor_id=performer_doctor_id,
        status=payload.status,
        category=payload.category,
        code_coding_system=payload.code_coding_system,
        code_value=payload.code_value,
        code_display=payload.code_display,
        effective_date_time=effective_dt,
        issued_date_time=issued_dt,
        value_quantity=payload.value_quantity,
        value_unit=payload.value_unit,
        value_system=payload.value_system,
        value_code=payload.value_code,
        value_string=payload.value_string,
        components=components_data,
        reference_range_low=payload.reference_range_low,
        reference_range_high=payload.reference_range_high,
        reference_range_text=payload.reference_range_text,
        interpretation=payload.interpretation,
        body_site=payload.body_site,
        method=payload.method,
        note=payload.note,
    )

    db.add(observation)
    await db.flush()
    return observation


async def get_observation_by_id(
    db: AsyncSession,
    observation_id: str,
) -> Optional[ClinicalObservation]:
    """Retrieve an observation by its unique UUID with loaded relationship entities."""
    stmt = (
        select(ClinicalObservation)
        .options(
            selectinload(ClinicalObservation.patient).selectinload(PatientProfile.user),
            selectinload(ClinicalObservation.performer_doctor).selectinload(DoctorProfile.user),
            selectinload(ClinicalObservation.encounter),
        )
        .where(ClinicalObservation.id == observation_id)
    )
    return await db.scalar(stmt)


async def list_patient_observations(
    db: AsyncSession,
    patient_id: str,
    filters: Optional[ObservationFilter] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[ClinicalObservation], int]:
    """Query longitudinal observations for a patient with optional category and code filters."""
    query = select(ClinicalObservation).where(ClinicalObservation.patient_id == patient_id)

    if filters:
        if filters.category:
            query = query.where(ClinicalObservation.category == filters.category)
        if filters.code_value:
            query = query.where(ClinicalObservation.code_value == filters.code_value)
        if filters.status:
            query = query.where(ClinicalObservation.status == filters.status)
        if filters.encounter_id:
            query = query.where(ClinicalObservation.encounter_id == filters.encounter_id)
        if filters.start_date:
            query = query.where(ClinicalObservation.effective_date_time >= filters.start_date)
        if filters.end_date:
            query = query.where(ClinicalObservation.effective_date_time <= filters.end_date)

    # Count total matching rows
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query) or 0

    # Execute paginated query ordered by date descending
    paged_query = (
        query.options(
            selectinload(ClinicalObservation.patient).selectinload(PatientProfile.user),
            selectinload(ClinicalObservation.performer_doctor).selectinload(DoctorProfile.user),
            selectinload(ClinicalObservation.encounter),
        )
        .order_by(ClinicalObservation.effective_date_time.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.scalars(paged_query)
    return list(result.all()), total_count


async def get_latest_vitals_summary(
    db: AsyncSession,
    patient_id: str,
) -> VitalsSummaryResponse:
    """Retrieve the single most recent reading for each standard clinical vital sign."""
    vitals_codes = [
        LOINC_BLOOD_PRESSURE_PANEL,
        LOINC_HEART_RATE,
        LOINC_RESPIRATORY_RATE,
        LOINC_BODY_TEMPERATURE,
        LOINC_OXYGEN_SATURATION,
        LOINC_BODY_MASS_INDEX,
        LOINC_BODY_WEIGHT,
        LOINC_BODY_HEIGHT,
        LOINC_FASTING_GLUCOSE,
    ]

    summary_kwargs: Dict[str, Any] = {}
    latest_timestamps: List[datetime] = []

    for code in vitals_codes:
        stmt = (
            select(ClinicalObservation)
            .options(
                selectinload(ClinicalObservation.patient).selectinload(PatientProfile.user),
                selectinload(ClinicalObservation.performer_doctor).selectinload(DoctorProfile.user),
                selectinload(ClinicalObservation.encounter),
            )
            .where(
                ClinicalObservation.patient_id == patient_id,
                ClinicalObservation.code_value == code,
            )
            .order_by(ClinicalObservation.effective_date_time.desc())
            .limit(1)
        )
        obs = await db.scalar(stmt)
        if obs:
            latest_timestamps.append(obs.effective_date_time)
            if code == LOINC_BLOOD_PRESSURE_PANEL:
                summary_kwargs["blood_pressure"] = obs
            elif code == LOINC_HEART_RATE:
                summary_kwargs["heart_rate"] = obs
            elif code == LOINC_RESPIRATORY_RATE:
                summary_kwargs["respiratory_rate"] = obs
            elif code == LOINC_BODY_TEMPERATURE:
                summary_kwargs["body_temperature"] = obs
            elif code == LOINC_OXYGEN_SATURATION:
                summary_kwargs["oxygen_saturation"] = obs
            elif code == LOINC_BODY_MASS_INDEX:
                summary_kwargs["body_mass_index"] = obs
            elif code == LOINC_BODY_WEIGHT:
                summary_kwargs["weight"] = obs
            elif code == LOINC_BODY_HEIGHT:
                summary_kwargs["height"] = obs
            elif code == LOINC_FASTING_GLUCOSE:
                summary_kwargs["blood_glucose"] = obs

    if latest_timestamps:
        summary_kwargs["last_recorded_at"] = max(latest_timestamps)

    return VitalsSummaryResponse(**summary_kwargs)


async def update_observation(
    db: AsyncSession,
    observation_id: str,
    payload: ObservationUpdate,
) -> ClinicalObservation:
    """Update observation status, clinical interpretation, or diagnostic notes."""
    observation = await get_observation_by_id(db, observation_id)
    if not observation:
        raise EntityNotFoundException("Clinical observation", observation_id)

    if payload.status is not None:
        observation.status = payload.status
    if payload.interpretation is not None:
        observation.interpretation = payload.interpretation
    if payload.note is not None:
        observation.note = payload.note

    await db.flush()
    return observation
