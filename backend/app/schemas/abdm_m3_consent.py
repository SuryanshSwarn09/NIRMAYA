"""Pydantic schemas for ABDM Milestone 3 (M3) Consent Management and Artefact Ingest.

Conforms to NHA ABDM v0.5 Data Flow Specification:
- Consent Notification (/v0.5/consents/hip/notify)
- Acknowledgement Callback (/v0.5/consents/hip/on-notify)
- Consent Artefact Structure & Permissions
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, ConfigDict


class ConsentManagerRef(BaseModel):
    """Identifier reference for Consent Manager, HIP, or HIU."""

    id: str = Field(description="Entity identifier, e.g. sbx, IN0410000123, or HIU-001")

    model_config = ConfigDict(from_attributes=True)


class ConsentPatient(BaseModel):
    """Patient identification in consent artefact."""

    id: str = Field(description="Patient ABHA ID or ABHA Address (e.g. sneha.sharma@abdm)")

    model_config = ConfigDict(from_attributes=True)


class ConsentPurpose(BaseModel):
    """Clinical purpose for which health information is requested."""

    text: str = Field(default="Care Management", description="Clinical purpose description")
    code: str = Field(
        default="CAREMGT",
        description="Standardized ABDM purpose code: CAREMGT | PUBHLTH | DSRCH | PATRQT | BTG",
    )
    refUri: Optional[str] = Field(
        default="https://nrces.in/ndhm/fhir/r4/StructureDefinition/Consent",
        description="Reference URI to standard purpose ontology",
    )

    model_config = ConfigDict(from_attributes=True)


class ConsentRequesterIdentifier(BaseModel):
    """Professional registration or license identifier of requesting clinician."""

    type: str = Field(default="REGNO", description="Identifier type (e.g. REGNO)")
    value: str = Field(description="Registration number, e.g. MCI/2018/09/12345")
    system: Optional[str] = Field(
        default="https://www.nmc.org.in",
        description="Issuing authority or register URL",
    )

    model_config = ConfigDict(from_attributes=True)


class ConsentRequester(BaseModel):
    """Healthcare practitioner or requester details requesting the health records."""

    name: str = Field(description="Name of the clinician or healthcare provider")
    identifier: Optional[ConsentRequesterIdentifier] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class ConsentDateRange(BaseModel):
    """Time window of clinical records authorized for release."""

    from_date: datetime = Field(alias="from", description="Earliest clinical record date permitted")
    to_date: datetime = Field(alias="to", description="Latest clinical record date permitted")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ConsentFrequency(BaseModel):
    """Frequency constraints for data access."""

    unit: str = Field(default="HOUR", description="Frequency unit: HOUR | DAY | WEEK | MONTH | YEAR")
    value: int = Field(default=1, description="Frequency magnitude")
    repeats: int = Field(default=0, description="Repeats count (0 = infinite / valid through date)")

    model_config = ConfigDict(from_attributes=True)


class ConsentPermission(BaseModel):
    """Detailed access permissions granted by the patient."""

    accessMode: str = Field(
        default="VIEW",
        description="Access mode granted: VIEW | STORE | STREAM | QUERY",
    )
    dateRange: ConsentDateRange = Field(description="Permitted clinical records date window")
    dataEraseAt: datetime = Field(
        description="Timestamp when HIU must erase/purge all transferred records"
    )
    frequency: ConsentFrequency = Field(
        default_factory=ConsentFrequency,
        description="Access frequency constraints",
    )

    model_config = ConfigDict(from_attributes=True)


class ConsentCareContextReference(BaseModel):
    """Specific patient reference and care context linkage authorized."""

    patientReference: str = Field(description="HIP internal patient ID (e.g. NIR-P-10023)")
    careContextReference: str = Field(description="Care context reference (e.g. ENC-2026-0042)")

    model_config = ConfigDict(from_attributes=True)


class ConsentDetail(BaseModel):
    """Core specification of the Electronic Consent Artefact."""

    schemaVersion: str = Field(default="v0.5", description="Consent schema version")
    consentId: str = Field(description="Unique consent artefact UUID")
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when consent was granted",
    )
    patient: ConsentPatient = Field(description="Patient granting consent")
    careContexts: List[ConsentCareContextReference] = Field(
        default_factory=list,
        description="List of care contexts authorized for data transfer",
    )
    purpose: ConsentPurpose = Field(default_factory=ConsentPurpose)
    hip: ConsentManagerRef = Field(description="Health Information Provider ID (e.g. IN0410000123)")
    hiu: ConsentManagerRef = Field(description="Health Information User ID requesting data")
    consentManager: ConsentManagerRef = Field(
        default_factory=lambda: ConsentManagerRef(id="sbx"),
        description="Issuing Consent Manager ID",
    )
    requester: Optional[ConsentRequester] = Field(default=None)
    hiTypes: List[str] = Field(
        default_factory=lambda: ["OPConsultation", "DiagnosticReport", "Prescription"],
        description="Health Information Types permitted under this consent",
    )
    permission: ConsentPermission = Field(description="Permissions granted")

    model_config = ConfigDict(from_attributes=True)


class ConsentArtefact(BaseModel):
    """ABDM Electronic Consent Artefact containing details and digital signature."""

    schemaVersion: str = Field(default="v0.5")
    consentId: str = Field(description="Consent identifier matching consentDetail.consentId")
    createdAt: Optional[datetime] = Field(default=None)
    patient: Optional[ConsentPatient] = Field(default=None)
    careContexts: Optional[List[ConsentCareContextReference]] = Field(default=None)
    purpose: Optional[ConsentPurpose] = Field(default=None)
    hip: Optional[ConsentManagerRef] = Field(default=None)
    hiu: Optional[ConsentManagerRef] = Field(default=None)
    consentManager: Optional[ConsentManagerRef] = Field(default=None)
    requester: Optional[ConsentRequester] = Field(default=None)
    hiTypes: Optional[List[str]] = Field(default=None)
    permission: Optional[ConsentPermission] = Field(default=None)
    consentDetail: Optional[ConsentDetail] = Field(
        default=None,
        description="Nested consent detail structure if using wrapped format",
    )
    signature: Optional[str] = Field(
        default=None,
        description="Digital signature of the Consent Manager over the consent details (SHA256withRSA/JWS)",
    )

    model_config = ConfigDict(from_attributes=True)


class ConsentNotificationDetail(BaseModel):
    """Notification body received from ABDM Gateway."""

    consentId: str = Field(description="Consent Artefact UUID")
    status: str = Field(
        description="Consent state: GRANTED | REVOKED | EXPIRED",
    )
    consentArtefact: Optional[ConsentArtefact] = Field(
        default=None,
        description="Consent artefact data (populated when status is GRANTED)",
    )

    model_config = ConfigDict(from_attributes=True)


class ConsentNotificationPayload(BaseModel):
    """Payload received from ABDM Gateway on /v0.5/consents/hip/notify."""

    requestId: str = Field(description="Unique UUID identifying this Gateway notification request")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of dispatch",
    )
    notification: ConsentNotificationDetail = Field(description="Consent notification body")

    model_config = ConfigDict(from_attributes=True)


class GatewayRespRef(BaseModel):
    """Reference to original incoming requestId matching ABDM correlation spec."""

    requestId: str = Field(description="Original incoming requestId that this callback resolves")

    model_config = ConfigDict(from_attributes=True)


class ConsentAcknowledgement(BaseModel):
    """Acknowledgement details for consent notification."""

    status: str = Field(default="OK", description="Acknowledgement status: OK")
    consentId: str = Field(description="Consent ID being acknowledged")

    model_config = ConfigDict(from_attributes=True)


class GatewayConsentError(BaseModel):
    """Standard ABDM Error representation."""

    code: int = Field(description="ABDM Error Code (e.g. 1400, 1410, 1413)")
    message: str = Field(description="Description of the error condition")

    model_config = ConfigDict(from_attributes=True)


class GatewayConsentOnNotifyCallback(BaseModel):
    """Payload dispatched to ABDM Gateway on /v0.5/consents/hip/on-notify."""

    requestId: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique UUID identifying this HIP callback response",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of callback dispatch",
    )
    acknowledgement: Optional[ConsentAcknowledgement] = Field(default=None)
    error: Optional[GatewayConsentError] = Field(default=None)
    resp: GatewayRespRef = Field(description="Reference to incoming requestId")

    model_config = ConfigDict(from_attributes=True)


class ConsentRecordRepresentation(BaseModel):
    """Internal normalized representation of a stored Consent Artefact."""

    consent_id: str
    status: str  # GRANTED | REVOKED | EXPIRED
    patient_id: str  # ABHA Address (e.g. sneha.sharma@abdm)
    hiu_id: str
    hip_id: str
    hi_types: List[str]
    care_contexts: List[ConsentCareContextReference]
    purpose_code: str
    access_mode: str
    date_range_from: datetime
    date_range_to: datetime
    data_erase_at: datetime
    signature_verified: bool
    received_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsentNotificationSimulateRequest(BaseModel):
    """Simulate receiving a consent notification for testing and dev workflows."""

    patient_id: str = Field(default="sneha.sharma@abdm", description="Patient ABHA ID")
    patient_reference: str = Field(default="NIR-P-10023", description="Patient internal reference")
    care_context_references: List[str] = Field(
        default_factory=lambda: ["ENC-2026-0042", "ENC-2026-0089"],
        description="List of care context reference IDs",
    )
    hiu_id: str = Field(default="HIU-APOLLO-001", description="Health Information User ID")
    hi_types: List[str] = Field(
        default_factory=lambda: ["OPConsultation", "DiagnosticReport", "Prescription"],
        description="Permitted health information types",
    )
    purpose_code: str = Field(default="CAREMGT", description="Purpose code")
    access_mode: str = Field(default="VIEW", description="Access mode: VIEW | STORE")
    days_valid: int = Field(default=30, description="Validity period in days")
    status: str = Field(default="GRANTED", description="Notification status: GRANTED | REVOKED")

    model_config = ConfigDict(from_attributes=True)


class ConsentNotificationSimulateResponse(BaseModel):
    """Response returned when a consent simulation is triggered."""

    consent_id: str
    status: str
    patient_id: str
    hiu_id: str
    hi_types: List[str]
    care_contexts_count: int
    signature_verified: bool
    on_notify_callback: GatewayConsentOnNotifyCallback

    model_config = ConfigDict(from_attributes=True)

