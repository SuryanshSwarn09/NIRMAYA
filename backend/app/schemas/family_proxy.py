import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RelationshipTypeEnum(str, Enum):
    """Categorization of dependent and family proxy relationships."""
    CHILD_MINOR = "CHILD_MINOR"
    PARENT_SENIOR = "PARENT_SENIOR"
    SPOUSE = "SPOUSE"
    LEGAL_WARD = "LEGAL_WARD"
    SIBLING = "SIBLING"


class VerificationAuthorityEnum(str, Enum):
    """Authority mechanism validating familial or legal guardianship relationship."""
    DIGILOCKER_BIRTH_CERTIFICATE = "DIGILOCKER_BIRTH_CERTIFICATE"
    AADHAAR_DEMOGRAPHIC_EKYC = "AADHAAR_DEMOGRAPHIC_EKYC"
    LEGAL_GUARDIANSHIP_ORDER = "LEGAL_GUARDIANSHIP_ORDER"
    SELF_ATTESTED_EMERGENCY = "SELF_ATTESTED_EMERGENCY"


class ProxyAccessScopeEnum(str, Enum):
    """Granular permission scope granted to the guardian."""
    FULL_MANAGEMENT = "FULL_MANAGEMENT"
    APPOINTMENTS_ONLY = "APPOINTMENTS_ONLY"
    RECORDS_VIEW_ONLY = "RECORDS_VIEW_ONLY"
    EMERGENCY_RESTRICTED = "EMERGENCY_RESTRICTED"


class ProxyRelationshipStatusEnum(str, Enum):
    """Lifecycle state of family proxy relationship."""
    ACTIVE = "ACTIVE"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    REVOKED = "REVOKED"
    EXPIRED_AGE_OF_MAJORITY = "EXPIRED_AGE_OF_MAJORITY"


class FamilyProxyCreateRequest(BaseModel):
    """Request payload to establish a family health proxy relationship."""
    guardian_patient_id: str = Field(..., description="Unique ID of guardian patient profile")
    dependent_patient_id: str = Field(..., description="Unique ID of dependent patient profile (must be distinct)")
    relationship_type: RelationshipTypeEnum
    verification_tier: VerificationAuthorityEnum
    verification_document_id: Optional[str] = Field(None, description="External verification document reference (e.g. DigiLocker doc ID)")
    verification_document_hash: str = Field(..., description="SHA-256 fingerprint of relationship verification proof")
    access_scope: ProxyAccessScopeEnum = Field(default=ProxyAccessScopeEnum.FULL_MANAGEMENT)
    dependent_dob_iso: Optional[str] = Field(None, description="Dependent date of birth YYYY-MM-DD for age-of-majority evaluation")
    guardian_consent_attestation: bool = Field(..., description="Verifiable consent attestation complying with DPDP Act Sec 9")


class FamilyProxyResponse(BaseModel):
    """Detailed model representing an active family proxy linkage."""
    relationship_id: str = Field(..., description="Unique proxy relationship identifier")
    guardian_patient_id: str
    dependent_patient_id: str
    relationship_type: RelationshipTypeEnum
    verification_tier: VerificationAuthorityEnum
    verification_document_hash: str
    access_scope: ProxyAccessScopeEnum
    status: ProxyRelationshipStatusEnum
    authorized_at: datetime
    authorized_until: Optional[datetime] = None
    dependent_name: Optional[str] = None
    dependent_abha: Optional[str] = None
    dependent_age: Optional[int] = None
    zero_contamination_isolated: bool = Field(default=True, description="Certification that dependent records are strictly isolated")


class ProxyAuditLogItem(BaseModel):
    """Audit entry recording access to a dependent patient record by a guardian."""
    log_id: str
    relationship_id: str
    actor_guardian_id: str
    target_dependent_id: str
    action_performed: str
    resource_accessed: Optional[str] = None
    ip_address: str = "127.0.0.1"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    authorized: bool = True
