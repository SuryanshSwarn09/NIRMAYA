"""Pydantic v2 schemas for Chain-of-Command Administrative Provisioning and Scoped Territorial RBAC."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.administrative_hierarchy import AdminLevelEnum, GovtDesignationEnum


class DelegationRank:
    """Numerical authority ranking for Government of India healthcare administrative designations."""

    RANK_MAP: Dict[GovtDesignationEnum, int] = {
        GovtDesignationEnum.NATIONAL_DIRECTOR: 5,
        GovtDesignationEnum.STATE_SECRETARY: 4,
        GovtDesignationEnum.DIVISIONAL_COMMISSIONER: 3,
        GovtDesignationEnum.DISTRICT_MAGISTRATE: 2,
        GovtDesignationEnum.CHIEF_MEDICAL_OFFICER: 2,
        GovtDesignationEnum.BLOCK_MEDICAL_OFFICER: 1,
    }

    @classmethod
    def get_rank(cls, designation: GovtDesignationEnum) -> int:
        """Return numerical hierarchy rank (higher number indicates superior authority)."""
        return cls.RANK_MAP.get(designation, 0)

    @classmethod
    def is_strictly_superior(cls, delegator: GovtDesignationEnum, delegatee: GovtDesignationEnum) -> bool:
        """Verify that delegator rank is strictly greater than delegatee rank."""
        return cls.get_rank(delegator) > cls.get_rank(delegatee)


class DelegationStatusEnum(str, Enum):
    """Lifecycle status of an administrative chain-of-command delegation."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AdministrativeDelegationBase(BaseModel):
    """Core attributes for administrative chain-of-command authority delegation."""

    delegator_user_id: str = Field(..., description="UUID of delegating government authority")
    delegator_designation: GovtDesignationEnum = Field(..., description="Official designation of the delegator")
    delegatee_user_id: str = Field(..., description="UUID of appointed delegatee user")
    delegatee_designation: GovtDesignationEnum = Field(..., description="Appointed government designation")
    administrative_unit_id: str = Field(..., description="UUID of the assigned administrative unit")
    jurisdiction_path: str = Field(..., description="PostgreSQL ltree path of the assigned territory (e.g. 'india.27.492')")
    gov_email: str = Field(..., description="Official government email address ending in .gov.in or .nic.in")


class AdministrativeDelegationCreate(AdministrativeDelegationBase):
    """Request payload to delegate administrative authority down the chain of command."""

    aadhaar_number: str = Field(
        ...,
        min_length=12,
        max_length=14,
        description="12-digit Aadhaar UID of delegatee (spaces optional)",
    )
    aadhaar_otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit Aadhaar OTP for identity verification simulator",
    )
    delegation_notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Official ministry delegation order reference notes",
    )

    @field_validator("gov_email")
    @classmethod
    def validate_gov_email_domain(cls, v: str) -> str:
        """Enforce official Indian government email domain suffixes."""
        normalized = v.strip().lower()
        if "@" not in normalized:
            raise ValueError(f"Email '{v}' is not an authorized Indian government domain. Must end with .gov.in or .nic.in")
        domain = normalized.split("@")[-1]
        valid_gov_tlds = ("gov.in", "nic.in")
        if not any(domain == d or domain.endswith("." + d) for d in valid_gov_tlds):
            raise ValueError(
                f"Email '{v}' is not an authorized Indian government domain. Must end with .gov.in or .nic.in"
            )
        return normalized


class AdministrativeDelegationResponse(AdministrativeDelegationBase):
    """Response model representing a recorded administrative delegation with cryptographic audit proof."""

    id: str = Field(..., description="Unique UUID of delegation record")
    unit_name: str = Field(..., description="Name of the assigned territorial jurisdiction")
    unit_level: AdminLevelEnum = Field(..., description="Tier level of assigned unit")
    aadhaar_verified: bool = Field(..., description="Whether delegatee Aadhaar identity was verified")
    status: DelegationStatusEnum = Field(default=DelegationStatusEnum.ACTIVE, description="Lifecycle status")
    is_active: bool = Field(..., description="Whether delegation is currently active")
    audit_hash: str = Field(..., description="SHA-256 cryptographic audit hash")
    created_at: datetime = Field(..., description="Timestamp when authority was provisioned")
    revoked_at: Optional[datetime] = Field(None, description="Timestamp when authority was revoked")
    revocation_reason: Optional[str] = Field(None, description="Official reason for delegation revocation")

    model_config = ConfigDict(from_attributes=True)


class DelegationRevokeRequest(BaseModel):
    """Request payload to revoke an active administrative delegation."""

    delegation_id: Optional[str] = Field(None, description="UUID of delegation record (optional if provided via URL path)")
    revoked_by_user_id: str = Field(..., description="UUID of the authority initiating revocation")
    reason: str = Field(..., min_length=5, max_length=500, description="Official rationale for revocation")


class TerritorialScopeValidationRequest(BaseModel):
    """Request to validate an officer's jurisdictional scope against a target healthcare facility path."""

    officer_jurisdiction_path: str = Field(
        ..., description="PostgreSQL ltree assigned path of officer (e.g. 'india.27.492')"
    )
    target_resource_path: str = Field(
        ..., description="Target clinical resource or facility path (e.g. 'india.27.492.4182')"
    )
    action_type: Optional[str] = Field(
        default="READ", description="Target administrative action (e.g. READ, AUDIT, OVERRIDE)"
    )


class TerritorialScopeValidationResponse(BaseModel):
    """Evaluation result of sub-2ms scoped territorial RBAC validation."""

    authorized: bool = Field(..., description="Whether access is granted within territorial boundaries")
    officer_jurisdiction_path: str = Field(..., description="Evaluated officer scope path")
    target_resource_path: str = Field(..., description="Evaluated resource path")
    action_type: str = Field(..., description="Evaluated action")
    reason: str = Field(..., description="Explanation of authorization decision")
    checked_at: datetime = Field(..., description="UTC timestamp of evaluation")
    evaluation_latency_ms: float = Field(..., description="Execution duration in milliseconds")


class GovEmailValidationResult(BaseModel):
    """Result of official government email domain verification."""

    email: str = Field(..., description="Supplied email address")
    is_valid_gov_domain: bool = Field(..., description="Whether domain conforms to Indian government standards")
    domain: str = Field(..., description="Parsed domain segment")
    normalized_email: str = Field(..., description="Lowercased sanitized email")


class DelegationAuditRecord(BaseModel):
    """Immutable audit record entry for administrative provisioning and revocation events."""

    id: str = Field(..., description="Unique UUID of audit record")
    delegation_id: str = Field(..., description="Target delegation identifier")
    action: str = Field(..., description="Action performed ('DELEGATED', 'REVOKED')")
    actor_id: str = Field(..., description="UUID of user executing the action")
    actor_designation: str = Field(..., description="Designation of acting authority")
    jurisdiction_path: str = Field(..., description="Assigned territorial path")
    timestamp: datetime = Field(..., description="UTC occurrence timestamp")
    audit_hash: str = Field(..., description="SHA-256 cryptographic hash of this transaction")
    previous_hash: Optional[str] = Field(None, description="SHA-256 hash of preceding audit ledger block")

    model_config = ConfigDict(from_attributes=True)
