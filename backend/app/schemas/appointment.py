"""Pydantic v2 schemas for DoctorSlot availability and clinical Appointment booking.

Aligned with HL7 FHIR Release 4 Appointment, Schedule, and Slot resources.
"""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.enums import AppointmentStatus, AppointmentType, SlotStatus


# ============================================================================
# Doctor Slot Schemas
# ============================================================================


class DoctorSlotBase(BaseModel):
    """Base fields for doctor consultation availability slots."""

    start_time: datetime = Field(
        description="UTC start timestamp of the consultation slot",
    )
    end_time: datetime = Field(
        description="UTC end timestamp of the consultation slot",
    )
    status: SlotStatus = Field(
        default=SlotStatus.AVAILABLE,
        description="Current slot availability lifecycle status",
    )
    is_teleconsult: bool = Field(
        default=False,
        description="Flag indicating teleconsultation readiness for this slot",
    )

    @model_validator(mode="after")
    def validate_time_window(self) -> "DoctorSlotBase":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class DoctorSlotCreate(BaseModel):
    """Schema for manual single slot creation."""

    start_time: datetime
    end_time: datetime
    is_teleconsult: bool = False

    @model_validator(mode="after")
    def validate_time_window(self) -> "DoctorSlotCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class DoctorSlotResponse(DoctorSlotBase):
    """Response representation for doctor availability slots."""

    id: str = Field(description="Unique UUIDv4 slot identifier")
    doctor_id: str = Field(description="UUIDv4 of the associated DoctorProfile")
    held_until: Optional[datetime] = Field(default=None, description="UTC timestamp until which the slot is held")
    held_by_patient_id: Optional[str] = Field(default=None, description="UUIDv4 of the patient holding the slot")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SlotHoldRequest(BaseModel):
    """Request payload to reserve/hold a slot for consultation checkout."""

    hold_duration_minutes: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Duration in minutes to temporarily hold the slot (1-30 minutes)",
    )


class SlotHoldResponse(BaseModel):
    """Confirmation payload returned when a slot is successfully held."""

    slot_id: str = Field(description="Unique UUIDv4 of the held slot")
    doctor_id: str = Field(description="UUIDv4 of the associated DoctorProfile")
    status: SlotStatus = Field(description="Updated slot status (HELD)")
    held_until: datetime = Field(description="UTC timestamp when the hold will expire")
    held_by_patient_id: str = Field(description="UUIDv4 of the patient holding the slot")
    hold_duration_seconds: int = Field(description="Duration of the hold in seconds")


class SlotReleaseResponse(BaseModel):
    """Response payload when a held slot is released back to available."""

    slot_id: str = Field(description="Unique UUIDv4 of the slot")
    status: SlotStatus = Field(description="Updated slot status (AVAILABLE)")
    released: bool = Field(default=True, description="Flag indicating successful release")



class SlotGenerateRequest(BaseModel):
    """Specification payload for bulk conflict-free slot generation."""

    doctor_id: str = Field(description="Target DoctorProfile UUID identifier")
    start_date: date = Field(description="Start date for slot generation (YYYY-MM-DD)")
    end_date: date = Field(description="End date for slot generation (inclusive)")

    # Daily clinical hours
    day_start_hour: int = Field(default=9, ge=0, le=23, description="Daily start hour (0-23)")
    day_start_minute: int = Field(default=0, ge=0, le=59, description="Daily start minute (0-59)")
    day_end_hour: int = Field(default=17, ge=0, le=23, description="Daily end hour (0-23)")
    day_end_minute: int = Field(default=0, ge=0, le=59, description="Daily end minute (0-59)")

    # Slot interval
    slot_duration_minutes: int = Field(
        default=30,
        ge=10,
        le=120,
        description="Duration of each consultation slot in minutes",
    )

    # Optional daily break / lunch interval
    break_start_hour: Optional[int] = Field(default=None, ge=0, le=23)
    break_start_minute: Optional[int] = Field(default=0, ge=0, le=59)
    break_end_hour: Optional[int] = Field(default=None, ge=0, le=23)
    break_end_minute: Optional[int] = Field(default=0, ge=0, le=59)

    is_teleconsult: bool = Field(default=False, description="Flag teleconsultation readiness")

    @model_validator(mode="after")
    def validate_dates_and_hours(self) -> "SlotGenerateRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")

        day_start = self.day_start_hour * 60 + self.day_start_minute
        day_end = self.day_end_hour * 60 + self.day_end_minute
        if day_end <= day_start:
            raise ValueError("Daily working hours end must be after start")

        if self.break_start_hour is not None and self.break_end_hour is not None:
            break_start = self.break_start_hour * 60 + (self.break_start_minute or 0)
            break_end = self.break_end_hour * 60 + (self.break_end_minute or 0)
            if break_end <= break_start:
                raise ValueError("Break end must be after break start")
        return self


class SlotGenerateResult(BaseModel):
    """Result summary of a bulk slot generation operation."""

    total_generated: int = Field(description="Count of new slots successfully persisted")
    total_skipped_existing: int = Field(description="Count of conflicting/existing slots skipped")
    slots: List[DoctorSlotResponse] = Field(description="List of newly created slot records")


# ============================================================================
# Clinical Appointment Schemas
# ============================================================================


class AppointmentBase(BaseModel):
    """Base fields for clinical encounter appointments."""

    appointment_type: AppointmentType = Field(
        default=AppointmentType.ROUTINE_CHECKUP,
        description="Encounter classification mapped to FHIR Appointment.appointmentType",
    )
    reason: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Chief clinical complaint or consultation purpose",
        examples=["Persistent seasonal allergy and dry cough"],
    )
    clinical_notes: Optional[str] = Field(
        default=None,
        description="Confidential clinical notes or triage observations",
    )
    teleconsultation_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Virtual video consultation link (e.g. Google Meet or WebRTC room)",
    )


class AppointmentCreate(AppointmentBase):
    """Payload to book or schedule a new clinical appointment."""

    doctor_id: str = Field(description="Target DoctorProfile UUID identifier")
    slot_id: Optional[str] = Field(
        default=None,
        description="Optional reserved DoctorSlot UUID; if provided, time window is inherited from the slot",
    )
    scheduled_start: Optional[datetime] = Field(
        default=None,
        description="Required if slot_id is omitted (ad-hoc / emergency bookings)",
    )
    scheduled_end: Optional[datetime] = Field(
        default=None,
        description="Required if slot_id is omitted",
    )

    @model_validator(mode="after")
    def validate_scheduling_specification(self) -> "AppointmentCreate":
        if not self.slot_id and not (self.scheduled_start and self.scheduled_end):
            raise ValueError("Either slot_id or both scheduled_start and scheduled_end must be provided")
        if self.scheduled_start and self.scheduled_end and self.scheduled_end <= self.scheduled_start:
            raise ValueError("scheduled_end must be strictly after scheduled_start")
        return self


class AppointmentStatusUpdate(BaseModel):
    """Payload to transition appointment status or append clinical notes."""

    status: AppointmentStatus = Field(description="Target AppointmentStatus lifecycle state")
    clinical_notes: Optional[str] = Field(default=None, description="Optional updated clinical notes")
    cancellation_reason: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Reason required when status is CANCELLED",
    )


class AppointmentResponse(AppointmentBase):
    """Full clinical appointment representation returned to clients."""

    id: str = Field(description="Unique UUIDv4 appointment identifier")
    patient_id: str = Field(description="UUIDv4 of the associated PatientProfile")
    doctor_id: str = Field(description="UUIDv4 of the associated DoctorProfile")
    slot_id: Optional[str] = Field(default=None, description="Associated DoctorSlot UUID if linked")
    status: AppointmentStatus = Field(description="Current encounter lifecycle status")
    scheduled_start: datetime = Field(description="UTC start time of the consultation")
    scheduled_end: datetime = Field(description="UTC end time of the consultation")
    created_at: datetime
    updated_at: datetime

    # Optional joined details for rich UI display
    doctor_name: Optional[str] = Field(default=None, description="Practitioner full name")
    doctor_specialty: Optional[str] = Field(default=None, description="Practitioner medical specialty")
    patient_name: Optional[str] = Field(default=None, description="Patient full name")

    model_config = ConfigDict(from_attributes=True)
