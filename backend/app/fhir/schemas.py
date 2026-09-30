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
