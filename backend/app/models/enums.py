"""Clinical, provider, and authorization enumerations for NIRMAYA relational models."""

from enum import Enum


class UserRole(str, Enum):
    """Core platform authorization roles."""

    PATIENT = "patient"
    DOCTOR = "doctor"
    LAB = "lab"
    ADMIN = "admin"


class Gender(str, Enum):
    """Administrative gender aligned with HL7 FHIR R4 standard.

    Reference: http://hl7.org/fhir/administrative-gender
    """

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class BloodGroup(str, Enum):
    """Clinical ABO and Rh blood group classifications."""

    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
    UNKNOWN = "unknown"


class MedicalSpecialty(str, Enum):
    """Clinical medical specialties aligned with SNOMED-CT / FHIR PractitionerRole."""

    GENERAL_MEDICINE = "General Medicine"
    CARDIOLOGY = "Cardiology"
    DERMATOLOGY = "Dermatology"
    PEDIATRICS = "Pediatrics"
    ORTHOPEDICS = "Orthopedics"
    NEUROLOGY = "Neurology"
    GYNECOLOGY = "Gynecology"
    ONCOLOGY = "Oncology"
    OPHTHALMOLOGY = "Ophthalmology"
    PSYCHIATRY = "Psychiatry"
    RADIOLOGY = "Radiology"
    PATHOLOGY = "Pathology"
    ENT = "ENT"
    OTHER = "Other"


class LabAccreditation(str, Enum):
    """Accreditation and certification standards for diagnostic testing laboratories."""

    NABL = "NABL"
    CAP = "CAP"
    ISO_15189 = "ISO 15189"
    STATE_GOVT = "State Government Registered"
    OTHER = "Other"
