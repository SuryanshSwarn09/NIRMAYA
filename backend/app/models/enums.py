"""Clinical and authorization enumerations for NIRMAYA relational models."""

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
