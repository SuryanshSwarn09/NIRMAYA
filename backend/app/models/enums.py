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


class ClinicalNoteType(str, Enum):
    """Clinical documentation category aligned with HL7 FHIR R4 and LOINC Document Types.

    Reference: https://loinc.org/11506-3/ (Progress note)
    """

    SOAP = "soap"
    CONSULTATION = "consultation"
    PROGRESS_NOTE = "progress-note"
    DISCHARGE_SUMMARY = "discharge-summary"


class ClinicalNoteStatus(str, Enum):
    """Workflow and signature state of the clinical document aligned with HL7 FHIR R4 CompositionStatus.

    Reference: http://hl7.org/fhir/R4/valueset-composition-status.html
    """

    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    ENTERED_IN_ERROR = "entered-in-error"


class ServiceRequestStatus(str, Enum):
    """Clinical status of the diagnostic requisition aligned with HL7 FHIR R4 RequestStatus.

    Reference: http://hl7.org/fhir/R4/valueset-request-status.html
    """

    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    REVOKED = "revoked"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class ServiceRequestIntent(str, Enum):
    """Clinical intent of the service request aligned with HL7 FHIR R4 RequestIntent.

    Reference: http://hl7.org/fhir/R4/valueset-request-intent.html
    """

    PROPOSAL = "proposal"
    PLAN = "plan"
    DIRECTIVE = "directive"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"


class ServiceRequestPriority(str, Enum):
    """Clinical urgency level of the request aligned with HL7 FHIR R4 RequestPriority.

    Reference: http://hl7.org/fhir/R4/valueset-request-priority.html
    """

    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class DiagnosticReportStatus(str, Enum):
    """Lifecycle and verification state of the diagnostic report aligned with HL7 FHIR R4 DiagnosticReportStatus.

    Reference: http://hl7.org/fhir/R4/valueset-diagnostic-report-status.html
    """

    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    APPENDED = "appended"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class SpecimenType(str, Enum):
    """Biological specimen source aligned with SNOMED-CT specimen types."""

    SERUM = "serum"
    PLASMA = "plasma"
    WHOLE_BLOOD = "whole_blood"
    URINE = "urine"
    SALIVA = "saliva"
    TISSUE = "tissue"
    SWAB = "swab"
    OTHER = "other"


class MedicationForm(str, Enum):
    """Dose formulation of the medication aligned with SNOMED-CT dose form hierarchies."""

    TABLET = "tablet"
    CAPSULE = "capsule"
    SYRUP = "syrup"
    INJECTION = "injection"
    INHALER = "inhaler"
    DROPS = "drops"
    OINTMENT = "ointment"
    PATCH = "patch"
    SUSPENSION = "suspension"
    SOLUTION = "solution"
    POWDER = "powder"
    OTHER = "other"


class AdministrationRoute(str, Enum):
    """Physiological administration route aligned with HL7 FHIR R4 RouteOfAdministration and SNOMED-CT."""

    ORAL = "oral"
    INTRAVENOUS = "intravenous"
    INTRAMUSCULAR = "intramuscular"
    SUBCUTANEOUS = "subcutaneous"
    INHALATION = "inhalation"
    TOPICAL = "topical"
    OPHTHALMIC = "ophthalmic"
    OTIC = "otic"
    NASAL = "nasal"
    RECTAL = "rectal"
    SUBLINGUAL = "sublingual"
    TRANSDERMAL = "transdermal"
    OTHER = "other"


class FormularyTier(str, Enum):
    """Formulary tier and insurance coverage categorization."""

    TIER_1_GENERIC = "tier_1_generic"
    TIER_2_PREFERRED_BRAND = "tier_2_preferred_brand"
    TIER_3_NON_PREFERRED_BRAND = "tier_3_non_preferred_brand"
    TIER_4_SPECIALTY = "tier_4_specialty"
    TIER_5_OTC = "tier_5_otc"


class MedicationStatus(str, Enum):
    """Catalog and active availability status aligned with HL7 FHIR R4 MedicationStatus.

    Reference: http://hl7.org/fhir/R4/valueset-medication-status.html
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    ENTERED_IN_ERROR = "entered-in-error"


class MedicationRequestStatus(str, Enum):
    """Lifecycle status of a medication prescription aligned with HL7 FHIR R4 MedicationrequestStatus.

    Reference: http://hl7.org/fhir/R4/valueset-medicationrequest-status.html
    """

    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    STOPPED = "stopped"


class MedicationRequestIntent(str, Enum):
    """Intent of the medication prescription aligned with HL7 FHIR R4 medicationrequest-intent.

    Reference: http://hl7.org/fhir/R4/valueset-medicationrequest-intent.html
    """

    PROPOSAL = "proposal"
    PLAN = "plan"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"
    FILLER_ORDER = "filler-order"
    INSTANCE_ORDER = "instance-order"
    OPTION = "option"


class MedicationRequestPriority(str, Enum):
    """Clinical priority of the prescription aligned with HL7 FHIR R4 RequestPriority.

    Reference: http://hl7.org/fhir/R4/valueset-request-priority.html
    """

    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class CDSSeverity(str, Enum):
    """Clinical Decision Support Alert Severity Tiers."""

    CRITICAL = "critical"
    MAJOR = "major"
    MODERATE = "moderate"


class CDSAlertType(str, Enum):
    """Classification of clinical decision support safety alerts."""

    DRUG_DRUG = "drug-drug"
    DRUG_ALLERGY = "drug-allergy"
    DRUG_CONDITION = "drug-condition"


class MedicationDispenseStatus(str, Enum):
    """Fulfillment lifecycle status for HL7 FHIR Release 4 MedicationDispense.

    Reference: http://hl7.org/fhir/R4/valueset-medicationdispense-status.html
    """

    PREPARATION = "preparation"
    IN_PROGRESS = "in-progress"
    CANCELLED = "cancelled"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    STOPPED = "stopped"
    DECLINED = "declined"
    UNKNOWN = "unknown"




