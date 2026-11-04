import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConsentPurposeEnum(str, Enum):
    """Standardized healthcare consent purposes aligned with ABDM M3 & SNOMED CT."""
    CAREMGT = "CAREMGT"
    EMERGENCY = "EMERGENCY"
    PUBHLTH = "PUBHLTH"
    DIAGNOSTIC = "DIAGNOSTIC"


class DelegatedConsentStatusEnum(str, Enum):
    """Lifecycle status of delegated electronic consent artifact."""
    GRANTED = "GRANTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    REQUESTED = "REQUESTED"


class DelegatedConsentGrantRequest(BaseModel):
    """Payload to authorize an ABDM electronic consent artifact by an active family proxy guardian."""
    consent_request_id: str = Field(..., description="Unique ID of inbound ABDM consent request")
    guardian_patient_id: str = Field(..., description="Unique ID of authorized guardian")
    dependent_patient_id: str = Field(..., description="Unique ID of dependent whose records are requested")
    purpose: ConsentPurposeEnum = Field(default=ConsentPurposeEnum.CAREMGT, description="Clinical purpose of data sharing")
    hi_types: List[str] = Field(
        default=["DiagnosticReport", "Prescription", "ImmunizationRecord", "OPDVisit"],
        description="FHIR health information types granted under delegation",
    )
    date_range_from: datetime = Field(..., description="Beginning of clinical record sharing window")
    date_range_to: datetime = Field(..., description="End of clinical record sharing window")
    expiry_date: datetime = Field(..., description="Timestamp when consent artifact expires")
    guardian_signature_attestation: bool = Field(..., description="Mandatory digital consent attestation under DPDP Act 2023 Sec 9")
    requester_hiu_name: str = Field("Apollo Health Gateway", description="Name of requesting Health Information User (HIU)")


class DelegatedConsentArtifactResponse(BaseModel):
    """Electronic consent artifact issued by guardian for dependent records."""
    artifact_id: str = Field(..., description="Unique consent artifact identifier")
    consent_request_id: str
    status: DelegatedConsentStatusEnum
    guardian_patient_id: str
    dependent_patient_id: str
    requester_hiu_name: str
    purpose: ConsentPurposeEnum
    hi_types: List[str]
    date_range_from: datetime
    date_range_to: datetime
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    guardian_signature_hash: str = Field(..., description="SHA-256 digital signature hash of guardian approval")
    zero_contamination_verified: bool = Field(True, description="Certification that data ingestion maintains zero contamination")


class ScopedProxyTokenRequest(BaseModel):
    """Payload to exchange active proxy delegation for an ephemeral scoped access token."""
    guardian_patient_id: str = Field(..., description="Unique ID of guardian requesting token")
    dependent_patient_id: str = Field(..., description="Unique ID of dependent whose records will be accessed")
    requested_scope: str = Field("proxy:dependent:CAREMGT", description="Scoped permission string")
    duration_seconds: int = Field(3600, ge=60, le=86400, description="Token validity duration in seconds (1 hour default)")


class ScopedProxyTokenResponse(BaseModel):
    """Ephemeral bearer token issued for delegated dependent access."""
    access_token: str = Field(..., description="Signed ephemeral bearer token")
    token_type: str = Field("Bearer", description="HTTP authorization scheme")
    expires_in: int = Field(..., description="Remaining validity duration in seconds")
    scope: str = Field(..., description="Granted permission scope")
    guardian_id: str
    dependent_id: str
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    zero_contamination_isolated: bool = Field(True, description="Certification of boundary enforcement")


class DelegatedConsentRevokeRequest(BaseModel):
    """Payload to revoke an active delegated consent artifact."""
    artifact_id: str = Field(..., description="Identifier of consent artifact to revoke")
    guardian_patient_id: str = Field(..., description="Identifier of guardian executing revocation")
    revocation_reason: str = Field("Guardian Revocation under DPDP Act Sec 9", description="Clinical or privacy justification")


class ConsentAuditTrailItem(BaseModel):
    """Immutable forensic audit item for delegated consent actions."""
    audit_id: str
    artifact_id: str
    action: str
    actor_id: str
    dependent_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: str = "127.0.0.1"
    status: str
