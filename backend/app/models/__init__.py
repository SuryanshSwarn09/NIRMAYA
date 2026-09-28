"""Relational models package exporting core platform entities and clinical enums."""

from app.models.appointment import Appointment, DoctorSlot
from app.models.doctor import DoctorProfile
from app.models.enums import (
    AppointmentStatus,
    AppointmentType,
    BloodGroup,
    Gender,
    LabAccreditation,
    MedicalSpecialty,
    SlotStatus,
    UserRole,
)
from app.models.lab import DiagnosticLabFacility
from app.models.patient import PatientProfile
from app.models.user import User

__all__ = [
    "User",
    "PatientProfile",
    "DoctorProfile",
    "DiagnosticLabFacility",
    "DoctorSlot",
    "Appointment",
    "UserRole",
    "Gender",
    "BloodGroup",
    "MedicalSpecialty",
    "LabAccreditation",
    "SlotStatus",
    "AppointmentStatus",
    "AppointmentType",
]

