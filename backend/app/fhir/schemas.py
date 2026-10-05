"""HL7 FHIR Release 4 Pydantic schemas and serialization models for NIRMAYA.

Defines standard FHIR R4 datatypes, CodeableConcepts, Appointment, Encounter,
Collection Bundles, and Ayushman Bharat Digital Mission (ABDM) CareContext
Consent Artifact linkage structures.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Core FHIR R4 Data Types & Primitives
# ============================================================================


class FHIRIdentifier(BaseModel):
    """FHIR R4 Identifier representing a technical or business identifier."""

    system: Optional[str] = Field(
        default=None,
        description="Namespace URI identifying the system assigning the identifier",
        example="https://nirmaya.health/fhir/appointment",
    )
    value: str = Field(
        description="The actual identifier string (e.g. UUID, ABHA, registration number)",
        example="91-0000-0000-0001",
    )
    use: Optional[str] = Field(
        default="official",
        description="usual | official | temp | secondary | old",
    )


class FHIRCoding(BaseModel):
    """FHIR R4 Coding representing a reference to a code defined by a terminology system."""

    system: str = Field(
        description="Identity of the terminology system (e.g. SNOMED, LOINC, HL7)",
        example="http://terminology.hl7.org/CodeSystem/v2-0276",
    )
    code: str = Field(
        description="Symbol in syntax defined by the system",
        example="ROUTINE",
    )
    display: Optional[str] = Field(
        default=None,
        description="Human readable representation of the code",
        example="Routine appointment",
    )
    version: Optional[str] = Field(
        default=None,
        description="Version of the system that defines the code",
    )


class FHIRCodeableConcept(BaseModel):
    """FHIR R4 Concept represented by one or more codified terminology systems and/or text."""

    coding: List[FHIRCoding] = Field(
        default_factory=list,
        description="Code defined by a terminology system",
    )
    text: Optional[str] = Field(
        default=None,
        description="Plain text representation of the clinical concept",
        example="Cardiovascular follow-up examination",
    )


class FHIRReference(BaseModel):
    """FHIR R4 Reference to another resource or literal URI."""

    reference: str = Field(
        description="Relative or absolute URL of the resource (e.g. 'Patient/123', 'Practitioner/456')",
        example="Patient/686523ba-744c-4bb7-925b-4f88eefcd269",
    )
    display: Optional[str] = Field(
        default=None,
        description="Text alternative for the resource",
        example="Arun Patel",
    )
    type: Optional[str] = Field(
        default=None,
        description="Type of the resource referred to",
        example="Patient",
    )


class FHIRPeriod(BaseModel):
    """FHIR R4 Time range defined by start and end date/time."""

    start: Optional[datetime] = Field(
        default=None,
        description="Starting time with inclusive boundary",
    )
    end: Optional[datetime] = Field(
        default=None,
        description="End time with inclusive boundary",
    )


class FHIRAnnotation(BaseModel):
    """FHIR R4 Annotation representing clinical notes and commentaries."""

    text: str = Field(
        description="The annotation text content",
        example="Patient reports improvement after antihypertensive therapy.",
    )
    time: Optional[datetime] = Field(
        default=None,
        description="When the annotation was recorded (UTC)",
    )
    authorString: Optional[str] = Field(
        default=None,
        description="Individual responsible for the annotation",
        example="Dr. Jane Smith",
    )


# ============================================================================
# FHIR R4 Appointment Resource
# ============================================================================


class FHIRParticipant(BaseModel):
    """Participants involved in an appointment (Patient, Practitioner, HealthcareService)."""

    type: Optional[List[FHIRCodeableConcept]] = Field(
        default=None,
        description="Role of participant in the appointment (e.g. SBJ for subject, PPRF for primary performer)",
    )
    actor: FHIRReference = Field(
        description="Person, Location/HealthcareService, or Device involved",
    )
    status: str = Field(
        default="accepted",
        description="Participation status: accepted | declined | tentative | needs-action",
    )


class FHIRAppointment(BaseModel):
    """HL7 FHIR Release 4 Appointment resource model."""

    resourceType: Literal["Appointment"] = Field(
        default="Appointment",
        description="Resource type name constant",
    )
    id: str = Field(
        description="Logical id of this clinical appointment artifact",
    )
    identifier: List[FHIRIdentifier] = Field(
        default_factory=list,
        description="External business identifiers",
    )
    status: str = Field(
        description="FHIR appointment status: booked | arrived | fulfilled | cancelled | noshow | entered-in-error",
        example="booked",
    )
    appointmentType: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Classification of appointment (routine, follow-up, telehealth, emergency)",
    )
    reasonCode: List[FHIRCodeableConcept] = Field(
        default_factory=list,
        description="Coded clinical reason this appointment is scheduled",
    )
    description: Optional[str] = Field(
        default=None,
        description="Shown on a subject line in a meeting request, or brief description",
    )
    start: datetime = Field(
        description="When appointment is to take place (UTC)",
    )
    end: datetime = Field(
        description="When appointment is to conclude (UTC)",
    )
    created: Optional[datetime] = Field(
        default=None,
        description="Date and time that the appointment was initially created",
    )
    comment: Optional[str] = Field(
        default=None,
        description="Additional clinical comments or intake instructions",
    )
    slot: Optional[List[FHIRReference]] = Field(
        default=None,
        description="The slots that this appointment is filling",
    )
    participant: List[FHIRParticipant] = Field(
        default_factory=list,
        description="List of participants involved in the appointment",
    )


# ============================================================================
# FHIR R4 Encounter Resource
# ============================================================================


class FHIREncounterParticipant(BaseModel):
    """Practitioners or actors involved in an interaction encounter."""

    individual: FHIRReference = Field(
        description="Persons involved in the encounter",
    )
    type: Optional[List[FHIRCodeableConcept]] = Field(
        default=None,
        description="Role of participant in encounter",
    )


class FHIREncounter(BaseModel):
    """HL7 FHIR Release 4 Encounter resource model."""

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Encounter"] = Field(
        default="Encounter",
        description="Resource type name constant",
    )
    id: str = Field(
        description="Logical id of this clinical encounter artifact",
    )
    identifier: List[FHIRIdentifier] = Field(
        default_factory=list,
        description="External business identifiers",
    )
    status: str = Field(
        description="planned | arrived | triaged | in-progress | onleave | finished | cancelled | entered-in-error",
        example="finished",
    )
    class_: FHIRCoding = Field(
        alias="class",
        description="Classification of patient encounter (ambulatory, virtual, inpatient)",
    )
    type: List[FHIRCodeableConcept] = Field(
        default_factory=list,
        description="Specific type of encounter (consultation, follow-up, checkup)",
    )
    subject: FHIRReference = Field(
        description="The patient or group present at the encounter",
    )
    participant: List[FHIREncounterParticipant] = Field(
        default_factory=list,
        description="List of past or active participants",
    )
    appointment: Optional[List[FHIRReference]] = Field(
        default=None,
        description="The appointment that scheduled this encounter",
    )
    period: Optional[FHIRPeriod] = Field(
        default=None,
        description="The start and end time of the encounter",
    )
    reasonCode: List[FHIRCodeableConcept] = Field(
        default_factory=list,
        description="Coded reason the encounter takes place",
    )


# ============================================================================
# FHIR R4 Condition Resource
# ============================================================================


class FHIRCondition(BaseModel):
    """HL7 FHIR Release 4 Condition resource model.

    Represents detailed clinical condition, problem, diagnosis, or health event
    aligned with FHIR R4 Condition specification.
    Reference: http://hl7.org/fhir/R4/condition.html
    """

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Condition"] = Field(
        default="Condition",
        description="Resource type name constant",
    )
    id: str = Field(
        description="Logical id of this clinical condition artifact",
    )
    identifier: List[FHIRIdentifier] = Field(
        default_factory=list,
        description="External business identifiers",
    )
    clinicalStatus: FHIRCodeableConcept = Field(
        description="active | recurrence | relapse | inactive | remission | resolved",
    )
    verificationStatus: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="unconfirmed | provisional | differential | confirmed | refuted | entered-in-error",
    )
    category: List[FHIRCodeableConcept] = Field(
        default_factory=list,
        description="problem-list-item | encounter-diagnosis | chronic-condition",
    )
    severity: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Subjective severity assessment (mild | moderate | severe)",
    )
    code: FHIRCodeableConcept = Field(
        description="Identification of the condition, problem or diagnosis (SNOMED-CT / ICD-10)",
    )
    bodySite: List[FHIRCodeableConcept] = Field(
        default_factory=list,
        description="Anatomical location, if relevant",
    )
    subject: FHIRReference = Field(
        description="Who has the condition? Reference to Patient resource",
    )
    encounter: Optional[FHIRReference] = Field(
        default=None,
        description="Encounter created as part of",
    )
    onsetDateTime: Optional[datetime] = Field(
        default=None,
        description="Estimated or actual date, date-time, or age",
    )
    abatementDateTime: Optional[datetime] = Field(
        default=None,
        description="When in resolution/remission",
    )
    recordedDate: Optional[datetime] = Field(
        default=None,
        description="Date record was first recorded (UTC)",
    )
    recorder: Optional[FHIRReference] = Field(
        default=None,
        description="Who recorded the condition (e.g. Practitioner)",
    )
    note: List[FHIRAnnotation] = Field(
        default_factory=list,
        description="Additional information about the Condition",
    )


# ============================================================================
# HL7 FHIR R4 Observation Resource & Components
# ============================================================================


class FHIRQuantity(BaseModel):
    """HL7 FHIR Release 4 Quantity datatype.

    Reference: http://hl7.org/fhir/R4/datatypes.html#Quantity
    """

    value: float = Field(
        description="Numerical value (with implicit precision)",
        example=120.0,
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit representation (e.g. mmHg, bpm, %)",
        example="mmHg",
    )
    system: Optional[str] = Field(
        default="http://unitsofmeasure.org",
        description="System that defines coded unit form (e.g. UCUM)",
        example="http://unitsofmeasure.org",
    )
    code: Optional[str] = Field(
        default=None,
        description="Coded form of the unit (UCUM code)",
        example="mm[Hg]",
    )


class FHIRObservationReferenceRange(BaseModel):
    """HL7 FHIR Release 4 Observation.referenceRange component."""

    low: Optional[FHIRQuantity] = Field(
        default=None,
        description="Low Range limit if relevant",
    )
    high: Optional[FHIRQuantity] = Field(
        default=None,
        description="High Range limit if relevant",
    )
    text: Optional[str] = Field(
        default=None,
        description="Text based reference range in an observation",
        example="60 - 100 /min",
    )


class FHIRObservationComponent(BaseModel):
    """HL7 FHIR Release 4 Observation.component for compound observations."""

    code: FHIRCodeableConcept = Field(
        description="Type of component observation (e.g. Systolic BP LOINC 8480-6)",
    )
    valueQuantity: Optional[FHIRQuantity] = Field(
        default=None,
        description="Actual component quantity result",
    )
    valueString: Optional[str] = Field(
        default=None,
        description="Actual component string result",
    )
    interpretation: List[FHIRCodeableConcept] = Field(
        default_factory=list,
        description="High, low, normal, etc. for component",
    )
    referenceRange: List[FHIRObservationReferenceRange] = Field(
        default_factory=list,
        description="Provides guide for interpretation of component result",
    )


class FHIRObservation(BaseModel):
    """HL7 FHIR Release 4 Observation Resource.

    Measurements and simple assertions made about a patient, device or other subject.
    Reference: http://hl7.org/fhir/R4/observation.html
    """

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Observation"] = Field(
        default="Observation",
        description="Resource type name constant",
    )
    id: str = Field(
        description="Logical id of this observation artifact",
    )
    identifier: List[FHIRIdentifier] = Field(
        default_factory=list,
        description="Business Identifier for observation",
    )
    status: str = Field(
        default="final",
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown",
    )
    category: List[FHIRCodeableConcept] = Field(
        default_factory=list,
        description="Classification of type of observation (vital-signs | laboratory | exam | etc.)",
    )
    code: FHIRCodeableConcept = Field(
        description="Type of observation (code / type)",
    )
    subject: FHIRReference = Field(
        description="Who and/or what the observation is about (Patient)",
    )
    encounter: Optional[FHIRReference] = Field(
        default=None,
        description="Healthcare event during which this observation is made",
    )
    effectiveDateTime: Optional[datetime] = Field(
        default=None,
        description="Clinically relevant time/time-period for observation",
    )
    issued: Optional[datetime] = Field(
        default=None,
        description="Date/Time this version was made available",
    )
    performer: List[FHIRReference] = Field(
        default_factory=list,
        description="Who is responsible for the observation (Practitioner / Doctor)",
    )
    valueQuantity: Optional[FHIRQuantity] = Field(
        default=None,
        description="Actual quantitative result",
    )
    valueString: Optional[str] = Field(
        default=None,
        description="Actual qualitative string result",
    )
    interpretation: List[FHIRCodeableConcept] = Field(
        default_factory=list,
        description="High, low, normal, etc.",
    )
    note: List[FHIRAnnotation] = Field(
        default_factory=list,
        description="Comments about the observation",
    )
    bodySite: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Observed body part",
    )
    method: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="How it was done",
    )
    referenceRange: List[FHIRObservationReferenceRange] = Field(
        default_factory=list,
        description="Provides guide for interpretation",
    )
    component: List[FHIRObservationComponent] = Field(
        default_factory=list,
        description="Component results for compound observations (e.g. Systolic & Diastolic BP)",
    )


# ============================================================================
# FHIR R4 Multi-Resource Collection Bundle
# ============================================================================


class FHIRBundleEntry(BaseModel):
    """Entry containing a single FHIR resource inside a Bundle."""

    fullUrl: str = Field(
        description="Canonical URL or urn:uuid for the resource entry",
        example="urn:uuid:686523ba-744c-4bb7-925b-4f88eefcd269",
    )
    resource: Dict[str, Any] = Field(
        description="The embedded FHIR Resource instance dictionary",
    )


class FHIRBundle(BaseModel):
    """HL7 FHIR Release 4 Collection or Document Bundle."""

    resourceType: Literal["Bundle"] = Field(
        default="Bundle",
        description="Resource type name constant",
    )
    id: str = Field(
        description="Unique identifier for the bundle envelope",
    )
    type: str = Field(
        default="collection",
        description="document | message | transaction | transaction-response | batch | batch-response | history | searchset | collection",
    )
    timestamp: datetime = Field(
        description="When the bundle was assembled (UTC)",
    )
    total: Optional[int] = Field(
        default=None,
        description="If searchset or collection, total number of matching matches",
    )
    entry: List[FHIRBundleEntry] = Field(
        default_factory=list,
        description="Entry list containing resources",
    )


# ============================================================================
# Ayushman Bharat Digital Mission (ABDM) CareContext & Consent Linkage
# ============================================================================


class ABDMConsentLinkage(BaseModel):
    """ABDM-compliant Health Information artifact with CareContext & SHA-256 signature."""

    careContextReference: str = Field(
        description="Deterministic ABDM CareContext identifier linking encounter to patient health vault",
        example="APPT-231336EC",
    )
    patientReference: str = Field(
        description="Patient ABHA identifier or internal health vault UUID",
        example="91-0000-0000-0001",
    )
    hiType: str = Field(
        default="OPConsultation",
        description="ABDM Health Information Type (e.g. OPConsultation, Prescription, DiagnosticReport)",
    )
    hipId: str = Field(
        description="ABDM Health Information Provider Registry ID",
        example="IN010000001",
    )
    consentArtifactId: Optional[str] = Field(
        default=None,
        description="Active ABDM Consent Artifact UUID granting HIU access",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of artifact generation",
    )
    signature: str = Field(
        description="Hex-encoded SHA-256 cryptographic digest of canonical FHIR bundle for tamper-evidence",
        example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    bundle: FHIRBundle = Field(
        description="Standard HL7 FHIR R4 Bundle containing Appointment and Encounter resources",
    )


class ABDMConsentLinkRequest(BaseModel):
    """Payload to simulate linking an ABDM Consent Artifact and generating an HI artifact."""

    hip_id: Optional[str] = Field(
        default="IN010000001",
        description="Optional Health Information Provider ID",
        example="IN010000001",
    )
    consent_artifact_id: Optional[str] = Field(
        default=None,
        description="Optional active ABDM Consent Artifact UUID",
        example="c7a10204-58f7-4dc1-a477-9df03da9ea60",
    )


