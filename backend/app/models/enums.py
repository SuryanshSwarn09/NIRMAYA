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


class SlotStatus(str, Enum):
    """Availability status lifecycle for doctor consultation time slots."""

    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"
    BLOCKED = "blocked"


class AppointmentStatus(str, Enum):
    """Clinical encounter appointment status aligned with HL7 FHIR R4 Appointment.status.

    Reference: http://hl7.org/fhir/R4/valueset-appointmentstatus.html
    """

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class AppointmentType(str, Enum):
    """Encounter classification aligned with HL7 FHIR R4 Appointment.appointmentType."""

    ROUTINE_CHECKUP = "routine_checkup"
    FOLLOW_UP = "follow_up"
    TELECONSULTATION = "teleconsultation"
    EMERGENCY = "emergency"


class ClinicalStatus(str, Enum):
    """Clinical status of the condition aligned with HL7 FHIR R4 ConditionClinicalStatusCodes.

    Reference: http://terminology.hl7.org/CodeSystem/condition-clinical
    """

    ACTIVE = "active"
    RECURRENCE = "recurrence"
    RELAPSE = "relapse"
    INACTIVE = "inactive"
    REMISSION = "remission"
    RESOLVED = "resolved"


class VerificationStatus(str, Enum):
    """Verification status of the condition aligned with HL7 FHIR R4 ConditionVerificationStatus.

    Reference: http://terminology.hl7.org/CodeSystem/condition-ver-status
    """

    UNCONFIRMED = "unconfirmed"
    PROVISIONAL = "provisional"
    DIFFERENTIAL = "differential"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    ENTERED_IN_ERROR = "entered-in-error"


class ConditionCategory(str, Enum):
    """Category classification of clinical condition aligned with HL7 FHIR R4 ConditionCategoryCodes.

    Reference: http://terminology.hl7.org/CodeSystem/condition-category
    """

    PROBLEM_LIST_ITEM = "problem-list-item"
    ENCOUNTER_DIAGNOSIS = "encounter-diagnosis"
    CHRONIC_CONDITION = "chronic-condition"


class ConditionSeverity(str, Enum):
    """Subjective severity assessment of the condition aligned with SNOMED-CT / FHIR ValueSet.

    Reference: http://hl7.org/fhir/R4/valueset-condition-severity.html
    """

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class ObservationStatus(str, Enum):
    """Status of the clinical observation aligned with HL7 FHIR R4 Observation.status.

    Reference: http://hl7.org/fhir/R4/valueset-observation-status.html
    """

    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class ObservationCategory(str, Enum):
    """High-level classification of observation aligned with HL7 FHIR R4 ObservationCategoryCodes.

    Reference: http://terminology.hl7.org/CodeSystem/observation-category
    """

    VITAL_SIGNS = "vital-signs"
    LABORATORY = "laboratory"
    IMAGING = "imaging"
    EXAM = "exam"
    THERAPY = "therapy"
    ACTIVITY = "activity"
    SOCIAL_HISTORY = "social-history"


class ObservationInterpretation(str, Enum):
    """Clinical interpretation flags for observations relative to reference ranges.

    Reference: http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation
    """

    NORMAL = "normal"
    HIGH = "high"
    LOW = "low"
    CRITICALLY_HIGH = "critically-high"
    CRITICALLY_LOW = "critically-low"
    ABNORMAL = "abnormal"

