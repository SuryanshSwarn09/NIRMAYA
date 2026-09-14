"""Relational models package exporting core platform entities and clinical enums."""

from app.models.doctor import DoctorProfile
from app.models.enums import (
    BloodGroup,
    Gender,
    LabAccreditation,
    MedicalSpecialty,
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
    "UserRole",
    "Gender",
    "BloodGroup",
    "MedicalSpecialty",
    "LabAccreditation",
]
