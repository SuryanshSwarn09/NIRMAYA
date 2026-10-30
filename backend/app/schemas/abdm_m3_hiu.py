"""Pydantic schemas for ABDM Milestone 3 (M3) Health Information User (HIU) Data Consumer Engine.

Conforms to NHA ABDM v0.5 Data Flow & Fidelius Specifications:
- HIU Request Initiation (POST /v0.5/health-information/cm/request)
- HIU Request Session Tracking & Ephemeral Key Management
- Decrypted & Parsed Clinical Resources (Encounters, Diagnostics, Prescriptions, Observations)
- Longitudinal Patient Records Aggregation
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.abdm_m3_crypto import KeyMaterial


class HIUDataRequestInitiate(BaseModel):
    """Schema for clinician triggering health data fetch under approved consent."""

    consentId: str = Field(description="Authorized ABDM Consent Artefact UUID")
    patientId: str = Field(description="Patient ABHA Address or identifier (e.g. sneha.sharma@abdm)")
    dateRangeFrom: datetime = Field(description="Earliest clinical record date requested")
    dateRangeTo: datetime = Field(description="Latest clinical record date requested")
    hiTypes: List[str] = Field(
        default_factory=lambda: ["OPConsultation", "DiagnosticReport", "Prescription"],
        description="Health Information types requested",
    )
    dataPushUrl: Optional[str] = Field(
        default=None,
        description="Optional custom destination URL; defaults to NIRMAYA HIU receiver",
    )

    model_config = ConfigDict(from_attributes=True)


class HIURequestSession(BaseModel):
    """Internal session tracking an outgoing HIU request with ephemeral key material."""

    transactionId: str = Field(description="Unique correlation transaction UUID")
    consentId: str = Field(description="Associated consent artefact UUID")
    patientId: str = Field(description="Patient ABHA identifier")
    hiuPrivateKey: str = Field(description="Base64-encoded HIU ephemeral Curve25519 private key")
    hiuPublicKey: str = Field(description="Base64-encoded HIU ephemeral Curve25519 public key")
    hiuNonce: str = Field(description="Base64-encoded HIU CSPRNG 32-byte nonce")
    status: str = Field(default="REQUESTED", description="Status: REQUESTED | TRANSFERRED | PROCESSED | FAILED")
    dateRangeFrom: datetime = Field(description="Earliest requested date")
    dateRangeTo: datetime = Field(description="Latest requested date")
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of session initiation",
    )
    expiresAt: datetime = Field(description="UTC timestamp when session expires")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Structured Clinical Representation of Parsed FHIR Resources
# ============================================================================

class ParsedEncounter(BaseModel):
    """Structured representation of an imported FHIR Encounter."""

    encounterId: str = Field(description="FHIR Encounter ID")
    status: str = Field(description="Encounter status: finished | in-progress")
    encounterClass: str = Field(description="Encounter class: AMB | IMP | EMER")
    careContextReference: Optional[str] = Field(default=None, description="Linked care context reference")
    periodStart: Optional[datetime] = Field(default=None, description="Start date/time")
    periodEnd: Optional[datetime] = Field(default=None, description="End date/time")
    serviceProvider: Optional[str] = Field(default=None, description="Facility or hospital name")

    model_config = ConfigDict(from_attributes=True)


class ParsedDiagnosticReport(BaseModel):
    """Structured representation of an imported FHIR DiagnosticReport."""

    reportId: str = Field(description="FHIR DiagnosticReport ID")
    code: str = Field(description="LOINC or clinical test code")
    display: str = Field(description="Test or panel display name")
    conclusion: Optional[str] = Field(default=None, description="Clinical conclusion or findings")
    issuedDate: Optional[datetime] = Field(default=None, description="Date report was issued")
    status: str = Field(default="final", description="Report status")
    performer: Optional[str] = Field(default=None, description="Diagnostic laboratory name")

    model_config = ConfigDict(from_attributes=True)


class ParsedPrescription(BaseModel):
    """Structured representation of an imported FHIR MedicationRequest."""

    prescriptionId: str = Field(description="FHIR MedicationRequest ID")
    medicationCode: Optional[str] = Field(default=None, description="SNOMED-CT or brand code")
    medicationName: str = Field(description="Medication name and strength")
    dosageInstruction: Optional[str] = Field(default=None, description="Directions for use")
    status: str = Field(default="active", description="Prescription status")
    authoredOn: Optional[datetime] = Field(default=None, description="Prescription date")

    model_config = ConfigDict(from_attributes=True)


class ParsedObservation(BaseModel):
    """Structured representation of an imported FHIR Observation (vitals, lab value)."""

    observationId: str = Field(description="FHIR Observation ID")
    code: str = Field(description="LOINC or observation code")
    display: str = Field(description="Observation display name (e.g. Body Temperature)")
    value: Optional[str] = Field(default=None, description="Measured value")
    unit: Optional[str] = Field(default=None, description="Unit of measure")
    effectiveDateTime: Optional[datetime] = Field(default=None, description="Observation timestamp")

    model_config = ConfigDict(from_attributes=True)


class DecryptedClinicalBundle(BaseModel):
    """Container holding decrypted raw FHIR bundle and structured clinical entities."""

    bundleId: str = Field(description="FHIR Bundle ID")
    careContextReference: str = Field(description="Associated care context ID")
    compositionTitle: Optional[str] = Field(default=None, description="Document composition title")
    author: Optional[str] = Field(default=None, description="Clinician or author")
    encounters: List[ParsedEncounter] = Field(default_factory=list)
    diagnosticReports: List[ParsedDiagnosticReport] = Field(default_factory=list)
    prescriptions: List[ParsedPrescription] = Field(default_factory=list)
    observations: List[ParsedObservation] = Field(default_factory=list)
    rawFhirJson: str = Field(description="Raw decrypted FHIR R4 Document Bundle JSON")

    model_config = ConfigDict(from_attributes=True)


class HIUPatientRecordsResponse(BaseModel):
    """Longitudinal medical records response for clinician view in patient workspace."""

    patientId: str = Field(description="Patient ABHA ID")
    transactionId: Optional[str] = Field(default=None, description="Transaction ID if filtered")
    consentId: Optional[str] = Field(default=None, description="Consent ID if filtered")
    totalBundles: int = Field(description="Total clinical bundles imported")
    encounters: List[ParsedEncounter] = Field(default_factory=list)
    diagnosticReports: List[ParsedDiagnosticReport] = Field(default_factory=list)
    prescriptions: List[ParsedPrescription] = Field(default_factory=list)
    observations: List[ParsedObservation] = Field(default_factory=list)
    importedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of response",
    )

    model_config = ConfigDict(from_attributes=True)
