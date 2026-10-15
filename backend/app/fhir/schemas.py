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


# ============================================================================
# FHIR R4 Composition Resource (Clinical Notes & Documentation)
# ============================================================================


class FHIRNarrative(BaseModel):
    """Human-readable XHTML narrative block conforming to HL7 FHIR R4 specs."""

    status: str = Field(
        default="generated",
        description="generated | extensions | additional | empty",
        example="generated",
    )
    div: str = Field(
        description="Limited XHTML div content",
    )


class FHIRCompositionSection(BaseModel):
    """Composition narrative section representing clinical document components."""

    title: Optional[str] = Field(
        default=None,
        description="Label for section (e.g. 'Subjective', 'Objective', 'Assessment', 'Plan')",
    )
    code: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Classification of section (e.g. LOINC narrative code)",
    )
    text: Optional[FHIRNarrative] = Field(
        default=None,
        description="Text summary of the section, for human interpretation",
    )


class FHIRComposition(BaseModel):
    """HL7 FHIR Release 4 Composition resource model.

    Represents a set of healthcare information that is physically assembled into a single logical package
    providing a single coherent clinical statement, such as a consultation note or SOAP note.
    Reference: http://hl7.org/fhir/R4/composition.html
    """

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Composition"] = Field(
        default="Composition",
        description="Resource type name constant",
    )
    id: str = Field(
        description="Logical id of this clinical composition artifact",
    )
    identifier: Optional[FHIRIdentifier] = Field(
        default=None,
        description="Version-independent identifier for the Composition",
    )
    status: str = Field(
        description="preliminary | final | amended | entered-in-error",
        example="final",
    )
    type: FHIRCodeableConcept = Field(
        description="Kind of composition (e.g. LOINC 11506-3 Progress note)",
    )
    category: Optional[List[FHIRCodeableConcept]] = Field(
        default=None,
        description="Categorization of Composition",
    )
    subject: FHIRReference = Field(
        description="Who and/or what the composition is about",
    )
    encounter: Optional[FHIRReference] = Field(
        default=None,
        description="Context of the Composition",
    )
    date: datetime = Field(
        description="Composition editing / signature time (UTC)",
    )
    author: List[FHIRReference] = Field(
        default_factory=list,
        description="Who and/or what authored the composition",
    )
    title: str = Field(
        description="Human Readable name/key for the document",
    )
    section: List[FHIRCompositionSection] = Field(
        default_factory=list,
        description="Composition sections for Chief Complaint, Subjective, Objective, Assessment, Plan",
    )


class FHIRServiceRequest(BaseModel):
    """HL7 FHIR Release 4 ServiceRequest resource representing a diagnostic or lab order.

    Reference: http://hl7.org/fhir/R4/servicerequest.html
    """

    resourceType: Literal["ServiceRequest"] = Field(
        default="ServiceRequest",
        description="Resource type name constant",
    )
    id: str = Field(
        description="Logical id of this service request artifact",
    )
    identifier: Optional[List[FHIRIdentifier]] = Field(
        default=None,
        description="Business identifier for this order",
    )
    status: str = Field(
        description="draft | active | on-hold | revoked | completed | entered-in-error | unknown",
        example="active",
    )
    intent: str = Field(
        description="proposal | plan | directive | order | original-order | reflex-order",
        example="order",
    )
    category: Optional[List[FHIRCodeableConcept]] = Field(
        default=None,
        description="Classification of service (e.g. laboratory)",
    )
    priority: Optional[str] = Field(
        default="routine",
        description="routine | urgent | asap | stat",
    )
    code: FHIRCodeableConcept = Field(
        description="Codified diagnostic test or panel requested (LOINC)",
    )
    subject: FHIRReference = Field(
        description="Individual or patient the service is ordered for",
    )
    encounter: Optional[FHIRReference] = Field(
        default=None,
        description="Encounter in which the request was created",
    )
    authoredOn: Optional[datetime] = Field(
        default=None,
        description="Date and time the order was authored",
    )
    requester: Optional[FHIRReference] = Field(
        default=None,
        description="Clinician / practitioner who initiated the request",
    )
    reasonCode: Optional[List[FHIRCodeableConcept]] = Field(
        default=None,
        description="Explanation/justification for why service was requested",
    )
    note: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Comments or preparation notes made about service request",
    )


class FHIRDiagnosticReport(BaseModel):
    """HL7 FHIR Release 4 DiagnosticReport resource representing findings and lab interpretations.

    Reference: http://hl7.org/fhir/R4/diagnosticreport.html
    """

    resourceType: Literal["DiagnosticReport"] = Field(
        default="DiagnosticReport",
        description="Resource type name constant",
    )
    id: str = Field(
        description="Logical id of this diagnostic report artifact",
    )
    identifier: Optional[List[FHIRIdentifier]] = Field(
        default=None,
        description="Business identifier for this report",
    )
    basedOn: Optional[List[FHIRReference]] = Field(
        default=None,
        description="Reference to ServiceRequest order this report fulfills",
    )
    status: str = Field(
        description="registered | preliminary | final | amended | corrected | appended | cancelled | entered-in-error",
        example="final",
    )
    category: Optional[List[FHIRCodeableConcept]] = Field(
        default=None,
        description="Service category (e.g. LAB, RAD)",
    )
    code: FHIRCodeableConcept = Field(
        description="Name/code for this diagnostic report (LOINC)",
    )
    subject: FHIRReference = Field(
        description="The subject of the report (Patient)",
    )
    encounter: Optional[FHIRReference] = Field(
        default=None,
        description="Clinical encounter / appointment context",
    )
    effectiveDateTime: Optional[datetime] = Field(
        default=None,
        description="Clinically relevant time for report (specimen collection/exam time)",
    )
    issued: Optional[datetime] = Field(
        default=None,
        description="DateTime this version of report was released (UTC)",
    )
    performer: Optional[List[FHIRReference]] = Field(
        default=None,
        description="Responsible diagnostic facility or pathologist",
    )
    result: Optional[List[FHIRReference]] = Field(
        default=None,
        description="Observations that are part of this diagnostic report",
    )
    conclusion: Optional[str] = Field(
        default=None,
        description="Clinical summary / conclusion of results",
    )
    conclusionCode: Optional[List[FHIRCodeableConcept]] = Field(
        default=None,
        description="Codified diagnostic interpretation/conclusion",
    )


# ============================================================================
# FHIR R4 Medication Resource
# ============================================================================


class FHIRMedicationIngredient(BaseModel):
    """Active ingredient or substance component of a medication."""

    itemCodeableConcept: FHIRCodeableConcept = Field(
        description="Codified substance or clinical active ingredient",
    )
    isActive: bool = Field(
        default=True,
        description="Whether ingredient affects physiological action",
    )
    strength: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Quantity of substance present in medication",
    )


class FHIRMedication(BaseModel):
    """HL7 FHIR Release 4 Medication resource representing clinical pharmaceuticals.

    Reference: http://hl7.org/fhir/R4/medication.html
    NRCeS Profile: https://nrces.in/ndhm/fhir/r4/StructureDefinition/Medication
    """

    resourceType: Literal["Medication"] = Field(
        default="Medication",
        description="Resource type name constant",
    )
    id: str = Field(
        description="Logical id of this medication resource",
    )
    identifier: Optional[List[FHIRIdentifier]] = Field(
        default=None,
        description="Business identifiers (e.g. RxCUI, NDC)",
    )
    code: FHIRCodeableConcept = Field(
        description="Codes that identify this medication (RxNorm, WHO-ATC, SNOMED-CT)",
    )
    status: str = Field(
        default="active",
        description="active | inactive | entered-in-error",
        example="active",
    )
    form: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Powder | tablets | capsule | syrup | injection etc.",
    )
    ingredient: Optional[List[FHIRMedicationIngredient]] = Field(
        default=None,
        description="Active or inactive pharmaceutical substances",
    )


# ============================================================================
# FHIR R4 MedicationRequest Resource
# ============================================================================


class FHIRDosageInstruction(BaseModel):
    """FHIR R4 Dosage specification for medication administration."""

    text: Optional[str] = Field(
        default=None,
        description="Free text dosage instructions",
        example="Take 1 tablet orally twice daily with meals for 14 days",
    )
    timing: Optional[Dict[str, Any]] = Field(
        default=None,
        description="When medication should be administered",
    )
    asNeededBoolean: Optional[bool] = Field(
        default=None,
        description="Take as needed (PRN)",
    )
    asNeededCodeableConcept: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Condition or trigger for taking medication PRN",
    )
    route: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="How drug should enter body",
    )
    doseAndRate: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Amount of medication administered per dose",
    )
    additionalInstruction: Optional[List[FHIRCodeableConcept]] = Field(
        default=None,
        description="Supplemental instructions or warnings",
    )


class FHIRDispenseRequest(BaseModel):
    """FHIR R4 Medication supply and dispense authorization details."""

    validityPeriod: Optional[FHIRPeriod] = Field(
        default=None,
        description="Time period supply is authorized for",
    )
    numberOfRepeatsAllowed: Optional[int] = Field(
        default=0,
        description="Number of authorized refills",
    )
    quantity: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Amount of medication to supply per dispense",
    )
    expectedSupplyDuration: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Number of days supply per dispense",
    )


class FHIRSubstitution(BaseModel):
    """FHIR R4 Generic or bioequivalent substitution allowance."""

    allowedBoolean: bool = Field(
        default=True,
        description="Whether substitution is allowed by prescriber",
    )
    reason: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Why substitution was authorized or prohibited",
    )


class FHIRMedicationRequest(BaseModel):
    """HL7 FHIR Release 4 MedicationRequest resource representing an electronic prescription.

    Reference: http://hl7.org/fhir/R4/medicationrequest.html
    NRCeS Profile: https://nrces.in/ndhm/fhir/r4/StructureDefinition/Prescription
    """

    resourceType: Literal["MedicationRequest"] = Field(
        default="MedicationRequest",
        description="Resource type name constant",
    )
    id: str = Field(
        description="Logical id of this medication request resource",
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata about the resource (profile, security, tags)",
    )
    identifier: Optional[List[FHIRIdentifier]] = Field(
        default=None,
        description="Business identifiers of this prescription",
    )
    status: str = Field(
        description="active | on-hold | cancelled | completed | entered-in-error | stopped | draft | unknown",
        example="active",
    )
    intent: str = Field(
        default="order",
        description="proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option",
        example="order",
    )
    priority: Optional[str] = Field(
        default="routine",
        description="routine | urgent | asap | stat",
        example="routine",
    )
    medicationReference: Optional[FHIRReference] = Field(
        default=None,
        description="Reference to a Medication resource",
    )
    medicationCodeableConcept: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Codified clinical medication or active ingredient",
    )
    subject: FHIRReference = Field(
        description="Patient or group the prescription is authored for",
    )
    encounter: Optional[FHIRReference] = Field(
        default=None,
        description="Encounter / Appointment context in which prescription was written",
    )
    authoredOn: Optional[str] = Field(
        default=None,
        description="When request was initially authored (ISO-8601 UTC)",
    )
    requester: Optional[FHIRReference] = Field(
        default=None,
        description="Clinician / Practitioner who authored the prescription",
    )
    reasonCode: Optional[List[FHIRCodeableConcept]] = Field(
        default=None,
        description="Clinical condition or symptom indication for the medication",
    )
    reasonReference: Optional[List[FHIRReference]] = Field(
        default=None,
        description="Reference to a Condition resource explaining the reason",
    )
    note: Optional[List[FHIRAnnotation]] = Field(
        default=None,
        description="Prescriber clinical annotations or comments",
    )
    dosageInstruction: Optional[List[FHIRDosageInstruction]] = Field(
        default=None,
        description="Structured instructions on how medication should be taken",
    )
    dispenseRequest: Optional[FHIRDispenseRequest] = Field(
        default=None,
        description="Medication supply and pharmacy dispense authorization",
    )
    substitution: Optional[FHIRSubstitution] = Field(
        default=None,
        description="Generic substitution permissions and rationale",
    )


# ============================================================================
# FHIR R4 MedicationDispense Resource
# ============================================================================


class FHIRMedicationDispensePerformer(BaseModel):
    """Actor performing or verifying the pharmaceutical dispensing action."""

    actor: FHIRReference = Field(
        description="Individual who was performing or verifying the dispense",
    )
    function: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Who performed the dispense and what they did",
    )


class FHIRMedicationDispenseSubstitution(BaseModel):
    """Deals with generic or formulary drug substitution performed by pharmacy."""

    wasSubstituted: bool = Field(
        default=False,
        description="Whether a substitution was or was not performed on the dispense",
    )
    type: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Code signifying whether a different or equivalent drug was dispensed",
    )
    reason: Optional[List[FHIRCodeableConcept]] = Field(
        default=None,
        description="Why was the substitution made",
    )
    responsibleParty: Optional[List[FHIRReference]] = Field(
        default=None,
        description="Who is responsible for the substitution",
    )


class FHIRMedicationDispense(BaseModel):
    """HL7 FHIR Release 4 MedicationDispense resource representing medication fulfillment.

    Reference: http://hl7.org/fhir/R4/medicationdispense.html
    NRCeS Profile: https://nrces.in/ndhm/fhir/r4/StructureDefinition/MedicationDispense
    """

    resourceType: Literal["MedicationDispense"] = Field(
        default="MedicationDispense",
        description="Resource type name constant",
    )
    id: str = Field(
        description="Logical id of this medication dispense resource",
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata about the resource (profile, security, tags)",
    )
    identifier: Optional[List[FHIRIdentifier]] = Field(
        default=None,
        description="Business identifiers of this medication dispense",
    )
    partOf: Optional[List[FHIRReference]] = Field(
        default=None,
        description="Event that dispense is part of",
    )
    status: str = Field(
        description="preparation | in-progress | cancelled | on-hold | completed | entered-in-error | stopped | declined | unknown",
        example="completed",
    )
    statusReasonCodeableConcept: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Why a dispense was not completed or changed",
    )
    category: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Type of medication dispense (e.g. community, inpatient, outpatient)",
    )
    medicationReference: Optional[FHIRReference] = Field(
        default=None,
        description="Reference to the dispensed Medication resource",
    )
    medicationCodeableConcept: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Codified dispensed pharmaceutical product",
    )
    subject: FHIRReference = Field(
        description="Patient for whom the medication was dispensed",
    )
    context: Optional[FHIRReference] = Field(
        default=None,
        description="Encounter associated with the dispense event",
    )
    performer: Optional[List[FHIRMedicationDispensePerformer]] = Field(
        default=None,
        description="Who performed the dispense",
    )
    authorizingPrescription: Optional[List[FHIRReference]] = Field(
        default=None,
        description="MedicationRequest authorization prescription that is fulfilled",
    )
    type: Optional[FHIRCodeableConcept] = Field(
        default=None,
        description="Trial fill, partial fill, emergency fill, etc.",
    )
    quantity: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Amount dispensed in UCUM units",
    )
    daysSupply: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Amount of medication expressed as a timing amount",
    )
    whenPrepared: Optional[str] = Field(
        default=None,
        description="When product was packaged and reviewed (ISO-8601 UTC)",
    )
    whenHandedOver: Optional[str] = Field(
        default=None,
        description="When product was given to patient or recipient (ISO-8601 UTC)",
    )
    dosageInstruction: Optional[List[FHIRDosageInstruction]] = Field(
        default=None,
        description="How the medication should be taken by patient",
    )
    substitution: Optional[FHIRMedicationDispenseSubstitution] = Field(
        default=None,
        description="Generic or formulary substitution details",
    )
    note: Optional[List[FHIRAnnotation]] = Field(
        default=None,
        description="Pharmacist annotations or fulfillment comments",
    )
    lotNumber: Optional[str] = Field(
        default=None,
        description="Lot number of the dispensed drug batch",
    )
    expirationDate: Optional[str] = Field(
        default=None,
        description="Expiry date of the dispensed drug (YYYY-MM-DD)",
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


