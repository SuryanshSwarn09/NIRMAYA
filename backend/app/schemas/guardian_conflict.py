import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConflictResolutionPolicyEnum(str, Enum):
    """Arbitration policy governing concurrent multi-guardian actions."""
    PESSIMISTIC_REVOCATION_PREVALENCE = "PESSIMISTIC_REVOCATION_PREVALENCE"
    DUAL_GUARDIAN_CO_SIGNING = "DUAL_GUARDIAN_CO_SIGNING"
    DISPUTED_CUSTODY_FREEZE = "DISPUTED_CUSTODY_FREEZE"
    PRIMARY_GUARDIAN_ARBITRATION = "PRIMARY_GUARDIAN_ARBITRATION"


class GuardianDisputeStatusEnum(str, Enum):
    """Lifecycle status of legal or custodial guardianship disputes."""
    RESOLVED = "RESOLVED"
    ACTIVE_DISPUTE = "ACTIVE_DISPUTE"
    COURT_SUB_JUDICE = "COURT_SUB_JUDICE"
    PENDING_MUTUAL_APPROVAL = "PENDING_MUTUAL_APPROVAL"


class CustodyModeEnum(str, Enum):
    """Operating governance mode for a dependent's health proxies."""
    JOINT_CONCURRENT = "JOINT_CONCURRENT"
    DUAL_SIGNATURE_REQUIRED = "DUAL_SIGNATURE_REQUIRED"
    DISPUTED_LOCKED = "DISPUTED_LOCKED"


class GuardianActionTypeEnum(str, Enum):
    """Action categories subject to conflict arbitration."""
    GRANT_CONSENT = "GRANT_CONSENT"
    REVOKE_CONSENT = "REVOKE_CONSENT"
    RAISE_LEGAL_DISPUTE = "RAISE_LEGAL_DISPUTE"
    RESOLVE_DISPUTE = "RESOLVE_DISPUTE"
    CHANGE_CUSTODY_MODE = "CHANGE_CUSTODY_MODE"


class DualSignStatusEnum(str, Enum):
    """Authorization phase for two-step multi-guardian consent artifacts."""
    PENDING_CO_SIGNATURE = "PENDING_CO_SIGNATURE"
    FULLY_AUTHORIZED = "FULLY_AUTHORIZED"
    REJECTED = "REJECTED"


class GuardianEntry(BaseModel):
    """Demographic and authority summary for a registered proxy guardian."""
    guardian_id: str = Field(..., description="Unique PatientProfile UUID of guardian")
    name: str = Field(..., description="Legal demographic name")
    relationship_type: str = Field(..., description="Relationship role (e.g. MOTHER, FATHER, LEGAL_GUARDIAN)")
    verification_tier: str = Field(..., description="Authority verification tier")
    priority_tier: int = Field(1, ge=1, le=5, description="Hierarchy priority tier (1=Primary natural guardian)")
    authorized_at: str = Field(..., description="ISO authorization date")


class MultiGuardianRelationshipSummary(BaseModel):
    """Comprehensive summary of concurrent guardians and active custody governance."""
    dependent_patient_id: str = Field(..., description="Target dependent PatientProfile UUID")
    dependent_name: str = Field(..., description="Legal demographic name of dependent")
    active_guardians: List[GuardianEntry] = Field(..., description="List of authorized concurrent guardians")
    custody_mode: CustodyModeEnum = Field(CustodyModeEnum.JOINT_CONCURRENT, description="Current governance mode")
    dispute_flag_active: bool = Field(False, description="Flag indicating active legal/custodial contest")
    active_dispute_ticket_id: Optional[str] = Field(None, description="Dispute ticket reference ID if contested")


class GuardianConflictResolutionRequest(BaseModel):
    """Payload to submit an action or dispute for policy arbitration."""
    dependent_patient_id: str = Field(..., description="Target dependent UUID")
    initiating_guardian_id: str = Field(..., description="Actor submitting the action")
    action_type: GuardianActionTypeEnum = Field(..., description="Proposed clinical or proxy action")
    target_artifact_id: Optional[str] = Field(None, description="Artifact ID if modifying existing consent")
    proposed_policy: ConflictResolutionPolicyEnum = Field(
        ConflictResolutionPolicyEnum.PESSIMISTIC_REVOCATION_PREVALENCE,
        description="Arbitration policy requested",
    )
    legal_order_reference: Optional[str] = Field(None, description="Court case or legal decree reference number")
    justification: str = Field(..., description="Clinical or legal rationale for the action")
    guardian_signature_attestation: bool = Field(..., description="Mandatory digital signature attestation under DPDP Act 2023 Sec 9")


class GuardianConflictResolutionResponse(BaseModel):
    """Arbitration ticket outcome and resource locking directives."""
    ticket_id: str = Field(..., description="Unique arbitration ticket ID")
    dependent_patient_id: str
    initiating_guardian_id: str
    action_type: GuardianActionTypeEnum
    dispute_status: GuardianDisputeStatusEnum
    effective_policy: ConflictResolutionPolicyEnum
    arbitrated_action_result: str = Field(..., description="Human and machine readable outcome summary")
    locked_resources: List[str] = Field(default_factory=list, description="Resource paths locked by arbitration")
    audit_hash: str = Field(..., description="SHA-256 integrity hash of arbitration decision")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DualSignConsentArtifactRequest(BaseModel):
    """Payload to initiate a two-phase co-signed consent artifact."""
    artifact_id: str = Field(..., description="Unique consent artifact ID")
    dependent_patient_id: str = Field(..., description="Target dependent UUID")
    primary_guardian_id: str = Field(..., description="Primary initiating guardian UUID")
    co_guardian_id: str = Field(..., description="Designated counter-signing co-guardian UUID")
    purpose: str = Field("CAREMGT", description="Clinical purpose code")
    hi_types: List[str] = Field(
        default_factory=lambda: ["DiagnosticReport", "Prescription"],
        description="Health information types requested",
    )
    primary_signature_attestation: bool = Field(True, description="Primary guardian digital attestation")


class DualSignCounterSignatureRequest(BaseModel):
    """Payload for co-guardian to counter-sign a pending consent artifact."""
    artifact_id: str = Field(..., description="Identifier of artifact in PENDING_CO_SIGNATURE state")
    co_guardian_id: str = Field(..., description="Counter-signing co-guardian UUID")
    co_signature_attestation: bool = Field(True, description="Co-guardian digital attestation")
    comments: Optional[str] = Field(None, description="Optional counter-signature clinical comments")


class DualSignConsentArtifactResponse(BaseModel):
    """State model for two-phase co-signed electronic consent artifact."""
    artifact_id: str
    dependent_patient_id: str
    primary_guardian_id: str
    co_guardian_id: str
    status: DualSignStatusEnum
    primary_signature_hash: str
    co_signature_hash: Optional[str] = None
    composite_signature_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    authorized_at: Optional[datetime] = None
