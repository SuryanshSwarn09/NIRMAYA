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

