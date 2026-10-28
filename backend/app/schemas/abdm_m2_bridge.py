"""Pydantic schemas for ABDM Milestone 2 (M2) Health Information Provider (HIP) Bridge."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class GatewayAuthInitRequester(BaseModel):
    """Requester identification inside ABDM auth init query."""

    type: str = Field(default="HIP", description="Requester entity type (e.g. HIP)")
    id: str = Field(default="IN0410000123", description="Registered HIP ID")

    model_config = ConfigDict(from_attributes=True)


class GatewayAuthInitQuery(BaseModel):
    """Query parameters for user auth init."""

    id: str = Field(description="ABHA Address or 14-digit ABHA Number (e.g. arun.patel@abdm)")
    purpose: str = Field(default="LINK", description="Auth purpose: LINK | KYC")
    authMode: str = Field(default="DIRECT_OTP", description="Requested auth mode: DIRECT_OTP | DEMOGRAPHICS | AADHAAR_OTP")
    requester: GatewayAuthInitRequester = Field(default_factory=GatewayAuthInitRequester)

    model_config = ConfigDict(from_attributes=True)


class GatewayAuthInitRequest(BaseModel):
    """Payload received from ABDM Gateway on /v0.5/users/auth/init."""

    requestId: str = Field(description="Unique UUID string identifying this gateway request")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of dispatch",
    )
    query: GatewayAuthInitQuery = Field(description="Query details for patient auth initiation")

    model_config = ConfigDict(from_attributes=True)


class GatewayRespRef(BaseModel):
    """Reference to original incoming requestId matching ABDM correlation spec."""

    requestId: str = Field(description="Original incoming requestId that this callback resolves")

    model_config = ConfigDict(from_attributes=True)


class GatewayAuthOnInitMeta(BaseModel):
    """Metadata hints returned on auth init (masked phone, expiry)."""

    hint: Optional[str] = Field(default=None, description="Masked destination hint (e.g. +91 ******4821)")
    expiry: Optional[datetime] = Field(default=None, description="OTP transaction expiration timestamp")

    model_config = ConfigDict(from_attributes=True)


class GatewayAuthOnInitAuth(BaseModel):
    """Auth transaction body for /v0.5/users/auth/on-init."""

    transactionId: str = Field(description="Unique transaction ID for subsequent OTP verification")
    mode: str = Field(description="Confirmed authentication mode (e.g. DIRECT_OTP)")
    meta: Optional[GatewayAuthOnInitMeta] = Field(default=None, description="Transaction metadata hints")

    model_config = ConfigDict(from_attributes=True)


class GatewayAuthOnInitCallback(BaseModel):
    """Payload dispatched asynchronously by HIP to ABDM Gateway /v0.5/users/auth/on-init."""

    requestId: str = Field(description="Unique UUID identifying this outbound callback")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of callback dispatch",
    )
    auth: Optional[GatewayAuthOnInitAuth] = Field(default=None, description="Auth transaction details on success")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error block if request failed")
    resp: GatewayRespRef = Field(description="Correlation reference pointing to incoming requestId")

    model_config = ConfigDict(from_attributes=True)


class WebhookEventItem(BaseModel):
    """Single audit log record of an inbound gateway webhook event."""

    id: str = Field(description="Internal log event UUID")
    request_id: str = Field(description="Gateway REQUEST-ID header")
    event_type: str = Field(description="Webhook route name (e.g. users/auth/init)")
    status: str = Field(description="Event status: ACCEPTED | CALLBACK_SENT | FAILED")
    latency_ms: float = Field(description="Processing latency from receipt to callback in ms")
    received_at: datetime = Field(description="UTC timestamp when webhook was ingested")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional context or payload summary")

    model_config = ConfigDict(from_attributes=True)


class HipBridgeStatusResponse(BaseModel):
    """Telemetry report for the Health Information Provider (HIP) Bridge."""

    status: str = Field(description="Status of HIP Bridge: online | degraded")
    hip_id: str = Field(default="IN0410000123", description="National Health Facility Registry (HFR) HIP ID")
    facility_name: str = Field(default="NIRMAYA Apex Hospital", description="Registered health facility name")
    gateway_url: str = Field(description="ABDM Gateway URL")
    cm_id: str = Field(default="sbx", description="Active Consent Manager ID")
    sandbox_mode: bool = Field(default=True, description="Whether operating in simulated sandbox mode")
    active_listeners: List[str] = Field(description="List of active inbound webhook paths")
    total_events_processed: int = Field(description="Cumulative count of ingested webhook events")
    last_heartbeat_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Current UTC timestamp of status generation",
    )

    model_config = ConfigDict(from_attributes=True)


class TestPingResponse(BaseModel):
    """Response returned when running an end-to-end Gateway test ping."""

    success: bool = Field(description="Whether test webhook and callback loop succeeded")
    request_id: str = Field(description="Generated test REQUEST-ID")
    http_status: int = Field(default=202, description="Synchronous HTTP status returned (202 Accepted)")
    message: str = Field(description="Human readable outcome message")
    callback_dispatched: bool = Field(description="Whether async callback was generated and delivered")
    callback_payload: Optional[Dict[str, Any]] = Field(default=None, description="Dispatched callback body")

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------------
# Patient Discovery Protocol Schemas (ABDM M2 /v0.5/care-contexts/discover)
# ----------------------------------------------------------------------------


class PatientIdentifier(BaseModel):
    """Verified or unverified patient identifier in ABDM discovery query."""

    type: str = Field(description="Identifier type (e.g. MOBILE, NDHM_HEALTH_NUMBER, MR, HEALTH_ID)")
    value: str = Field(description="Identifier value (e.g. +919876543210, 91-1029-3847-5610)")

    model_config = ConfigDict(from_attributes=True)


class PatientDiscoveryQuery(BaseModel):
    """Query attributes provided by ABDM Gateway in patient discovery."""

    id: str = Field(description="ABHA Address of patient (e.g. arun.patel@abdm)")
    name: Optional[str] = Field(default=None, description="Patient full name")
    gender: Optional[str] = Field(default=None, description="Gender code (M, F, O)")
    yearOfBirth: Optional[int] = Field(default=None, description="Patient birth year (e.g. 1985)")
    dateOfBirth: Optional[str] = Field(default=None, description="Patient ISO birth date (e.g. 1985-04-12)")
    verifiedIdentifiers: List[PatientIdentifier] = Field(
        default_factory=list,
        description="List of verified identifiers (e.g. MOBILE, NDHM_HEALTH_NUMBER)",
    )
    unverifiedIdentifiers: List[PatientIdentifier] = Field(
        default_factory=list,
        description="List of unverified demographic identifiers",
    )

    model_config = ConfigDict(from_attributes=True)


class GatewayPatientDiscoveryRequest(BaseModel):
    """Payload received from ABDM Gateway on POST /v0.5/care-contexts/discover."""

    requestId: str = Field(description="Unique UUID identifying this discovery request")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of dispatch",
    )
    hipId: str = Field(default="IN0410000123", description="HIP Facility ID queried")
    patient: PatientDiscoveryQuery = Field(description="Patient demographic & identifier criteria")

    model_config = ConfigDict(from_attributes=True)


class CareContextRepresentation(BaseModel):
    """Single care context episode linked to patient at this HIP."""

    referenceNumber: str = Field(description="Unique reference number at HIP (e.g. OPD-ENC-001)")
    display: str = Field(description="Human readable care context label (e.g. Cardiology Consultation)")

    model_config = ConfigDict(from_attributes=True)


class DiscoveredPatientRepresentation(BaseModel):
    """Matched patient representation returned in ABDM discovery callback."""

    referenceNumber: str = Field(description="Patient ID / MRN at this HIP (e.g. pat-arun-patel-01)")
    display: str = Field(description="Patient display name")
    careContexts: List[CareContextRepresentation] = Field(
        default_factory=list,
        description="Discovered active care context episodes",
    )
    matchedBy: List[str] = Field(
        default_factory=list,
        description="Identifiers that produced the match (e.g. NDHM_HEALTH_NUMBER, MOBILE, NAME)",
    )

    model_config = ConfigDict(from_attributes=True)


class GatewayPatientOnDiscoverCallback(BaseModel):
    """Outbound callback payload dispatched by HIP to ABDM Gateway /v0.5/care-contexts/on-discover."""

    requestId: str = Field(description="Unique UUID identifying this callback dispatch")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of dispatch",
    )
    transactionId: str = Field(description="Unique discovery transaction ID")
    patient: Optional[DiscoveredPatientRepresentation] = Field(
        default=None,
        description="Discovered patient and care contexts, or null if no match found",
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Error details if patient not found or match is ambiguous",
    )
    resp: GatewayRespRef = Field(description="Correlation reference pointing to incoming requestId")

    model_config = ConfigDict(from_attributes=True)


class DemographicMatchBreakdown(BaseModel):
    """Detailed score telemetry from fuzzy demographic matcher."""

    name_score: float = Field(description="Name similarity score (0.0 to 1.0)")
    yob_score: float = Field(description="Year of birth matching score (0.0 to 1.0)")
    gender_score: float = Field(description="Gender matching score (0.0 to 1.0)")
    composite_score: float = Field(description="Weighted overall confidence score (0.0 to 1.0)")
    matched_by: List[str] = Field(description="List of matched attribute keys")
    match_status: str = Field(description="CONFIRMED | AMBIGUOUS | NO_MATCH")

    model_config = ConfigDict(from_attributes=True)


class PatientDiscoverySimulateRequest(BaseModel):
    """Request payload for simulating patient discovery from the clinical console."""

    abha_address: Optional[str] = Field(default=None, description="Optional ABHA address (e.g. arun.patel@abdm)")
    abha_number: Optional[str] = Field(default=None, description="Optional 14-digit ABHA number")
    full_name: Optional[str] = Field(default=None, description="Full or partial/fuzzy patient name")
    gender: Optional[str] = Field(default=None, description="M, F, O, MALE, FEMALE, OTHER")
    year_of_birth: Optional[int] = Field(default=None, description="Birth year (e.g. 1985)")
    mobile: Optional[str] = Field(default=None, description="10-digit mobile or international format")
    match_threshold: float = Field(default=0.75, ge=0.5, le=1.0, description="Minimum confidence threshold")

    model_config = ConfigDict(from_attributes=True)


class PatientDiscoverySimulateResponse(BaseModel):
    """Outcome report from patient discovery simulation."""

    matched: bool = Field(description="Whether a unique high-confidence patient was discovered")
    confidence_score: float = Field(description="Final match confidence (0.0 to 1.0)")
    breakdown: DemographicMatchBreakdown = Field(description="Demographic score breakdown")
    patient_id: Optional[str] = Field(default=None, description="Matched PatientProfile ID")
    patient_name: Optional[str] = Field(default=None, description="Matched patient full name")
    abha_address: Optional[str] = Field(default=None, description="Patient ABHA Address")
    care_contexts: List[CareContextRepresentation] = Field(
        default_factory=list,
        description="Discovered clinical care contexts",
    )
    callback_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Full ABDM /v0.5/care-contexts/on-discover payload generated",
    )

    model_config = ConfigDict(from_attributes=True)

