"""Break-The-Glass (BTG) Emergency Health Profile Vault Schemas for NIRMAYA.

Defines models for Zero-Knowledge encrypted emergency profile envelopes,
Argon2id KDF parameters, clinical emergency justification categories,
emergency override requests/responses, and immutable forensic audit trails.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class EmergencyBloodGroup(str, Enum):
    """ABO and Rh factor blood group classification."""

    O_POS = "O+"
    O_NEG = "O-"
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    UNKNOWN = "UNKNOWN"


class EmergencyAllergyItem(BaseModel):
    """Critical allergy item requiring immediate avoidance in emergency care."""

    substance: str = Field(description="Allergen substance (e.g. Penicillin, Peanuts, Latex)")
    criticality: str = Field(default="high", description="Criticality tier (e.g. high, life_threatening)")
    manifestation: str = Field(description="Physiological clinical reaction (e.g. Anaphylactic shock, Bronchospasm)")

    model_config = ConfigDict(from_attributes=True)


class EmergencyMedicationItem(BaseModel):
    """Critical ongoing medication affecting emergency procedures (e.g. anticoagulants)."""

    medicationName: str = Field(description="Brand or generic pharmaceutical name")
    dosage: str = Field(description="Active dosage strength and frequency")
    category: str = Field(description="Therapeutic class (e.g. Anticoagulant, Insulin, Immunosuppressant)")
    highRiskWarning: Optional[str] = Field(
        default=None,
        description="Clinical warning for acute emergency intervention",
    )

    model_config = ConfigDict(from_attributes=True)


class EmergencyConditionItem(BaseModel):
    """Critical medical comorbidity or surgical implant."""

    conditionName: str = Field(description="Condition or implant name (e.g. Dual-Chamber Pacemaker, Severe Hemophilia)")
    icd10Code: Optional[str] = Field(default=None, description="Optional standard ICD-10 code")
    notes: Optional[str] = Field(default=None, description="Critical guidance notes for emergency physicians")

    model_config = ConfigDict(from_attributes=True)


class EmergencyContactItem(BaseModel):
    """Next of kin or designated primary emergency contact."""

    name: str = Field(description="Full legal name of contact person")
    relationship: str = Field(description="Relationship to patient (e.g. Spouse, Parent, Sibling)")
    phone: str = Field(description="Emergency contact phone number with country code")
    isPrimary: bool = Field(default=True, description="Whether this is the primary emergency contact")

    model_config = ConfigDict(from_attributes=True)


class EmergencyProfileData(BaseModel):
    """Cleartext emergency health profile extracted or to be encrypted."""

    patientAbha: str = Field(description="14-digit national ABHA identifier")
    patientName: str = Field(description="Patient full display name")
    dateOfBirth: str = Field(description="ISO 8601 date of birth (YYYY-MM-DD)")
    gender: str = Field(description="Legal administrative sex")
    bloodGroup: EmergencyBloodGroup = Field(description="Confirmed blood group and Rh factor")
    allergies: List[EmergencyAllergyItem] = Field(default_factory=list, description="List of life-threatening allergies")
    medications: List[EmergencyMedicationItem] = Field(default_factory=list, description="Active high-risk medications")
    conditions: List[EmergencyConditionItem] = Field(default_factory=list, description="Comorbidities and surgical implants")
    emergencyContacts: List[EmergencyContactItem] = Field(default_factory=list, description="Primary emergency contacts")
    organDonorStatus: bool = Field(default=True, description="Whether patient is a registered organ donor")
    advanceDirectives: Optional[str] = Field(default=None, description="Living will or resuscitation directives (e.g. FULL_CODE, DNR)")
    updatedAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of last profile update",
    )

    model_config = ConfigDict(from_attributes=True)


class EncryptedVaultEnvelope(BaseModel):
    """Zero-Knowledge encrypted envelope storing emergency health profile."""

    vaultId: str = Field(
        default_factory=lambda: f"vlt-{uuid.uuid4().hex[:12]}",
        description="Unique vault record UUID",
    )
    patientAbha: str = Field(description="14-digit ABHA number used as AAD")
    ciphertextB64: str = Field(description="Base64-encoded AES-256-GCM ciphertext + AEAD tag")
    nonceB64: str = Field(description="Base64-encoded 12-byte CSPRNG nonce")
    saltB64: str = Field(description="Base64-encoded 16-byte Argon2id salt")
    kdfAlgorithm: str = Field(default="Argon2id", description="Key derivation function used")
    cipherAlgorithm: str = Field(default="AES-256-GCM", description="Symmetric authenticated cipher used")
    ciphertextSha256: str = Field(description="SHA-256 digest of raw ciphertext for integrity validation")
    createdAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Creation ISO 8601 UTC timestamp",
    )
    updatedAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Last modified ISO 8601 UTC timestamp",
    )

    model_config = ConfigDict(from_attributes=True)


class EmergencyJustificationCategory(str, Enum):
    """Legally sanctioned emergency justification categories for Break-The-Glass override."""

    UNCONSCIOUS_TRAUMA = "UNCONSCIOUS_TRAUMA"
    RESPIRATORY_ARREST = "RESPIRATORY_ARREST"
    MASSIVE_HEMORRHAGE = "MASSIVE_HEMORRHAGE"
    ALTERED_MENTAL_STATUS = "ALTERED_MENTAL_STATUS"
    ANAPHYLAXIS_EMERGENCY = "ANAPHYLAXIS_EMERGENCY"
    CARDIAC_ARREST_RESUSCITATION = "CARDIAC_ARREST_RESUSCITATION"
    OTHER_LIFE_THREATENING = "OTHER_LIFE_THREATENING"


class BTGOverrideRequest(BaseModel):
    """Clinician request to trigger Break-The-Glass emergency override."""

    patientAbha: str = Field(description="14-digit ABHA number of patient in acute emergency")
    doctorId: str = Field(description="Attending emergency clinician UUID")
    doctorHpr: str = Field(description="National Healthcare Professional Registry (HPR) address")
    doctorName: str = Field(description="Clinician full display name")
    facilityId: str = Field(description="Healthcare facility or trauma center ID")
    justificationCategory: EmergencyJustificationCategory = Field(
        description="Standardized clinical emergency category",
    )
    clinicalJustification: str = Field(
        min_length=15,
        description="Detailed mandatory clinical justification narrative (e.g. GCS score, trauma mechanism)",
    )
    department: str = Field(
        default="Emergency & Trauma Resuscitation",
        description="Hospital department or critical care unit",
    )

    model_config = ConfigDict(from_attributes=True)


class BTGAuditLogEntry(BaseModel):
    """Immutable forensic audit record generated upon Break-The-Glass access."""

    eventId: str = Field(
        default_factory=lambda: f"btg-evt-{uuid.uuid4().hex[:12]}",
        description="Unique forensic audit event identifier",
    )
    patientAbha: str = Field(description="Patient ABHA accessed")
    doctorId: str = Field(description="Clinician UUID")
    doctorHpr: str = Field(description="Clinician HPR address")
    doctorName: str = Field(description="Clinician name")
    facilityId: str = Field(description="Hospital or clinic facility ID")
    justificationCategory: EmergencyJustificationCategory = Field(description="Emergency category")
    clinicalJustification: str = Field(description="Documented clinical justification")
    department: str = Field(description="Attending department")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC access timestamp",
    )
    auditFingerprint: str = Field(description="SHA-256 tamper-evident cryptographic fingerprint of the event")
    ipAddress: Optional[str] = Field(default=None, description="Originating client IP address or terminal")

    model_config = ConfigDict(from_attributes=True)


class BTGOverrideResponse(BaseModel):
    """Decrypted emergency health vault response delivered under Break-The-Glass protocol."""

    overrideGranted: bool = Field(default=True, description="Whether emergency access was successfully authorized")
    eventId: str = Field(description="Audit event identifier tracking this access")
    patientAbha: str = Field(description="Patient ABHA number")
    emergencyProfile: EmergencyProfileData = Field(description="Decrypted emergency clinical profile")
    auditFingerprint: str = Field(description="Forensic SHA-256 seal of the access transaction")
    accessedAt: str = Field(description="ISO 8601 UTC timestamp of emergency override")
    warning: str = Field(
        default="EMERGENCY OVERRIDE GRANTED. All actions are cryptographically sealed in the immutable forensic audit log.",
        description="Regulatory legal notice",
    )

    model_config = ConfigDict(from_attributes=True)


class EmergencyVaultStatusResponse(BaseModel):
    """Status inquiry for a patient's emergency vault provisioning."""

    patientAbha: str = Field(description="Patient ABHA number")
    isProvisioned: bool = Field(description="Whether an encrypted emergency vault is active")
    vaultId: Optional[str] = Field(default=None, description="Vault UUID if provisioned")
    lastEncryptedAt: Optional[str] = Field(default=None, description="Timestamp of latest vault encryption")
    totalOverridesLifetime: int = Field(default=0, description="Lifetime BTG access count")

    model_config = ConfigDict(from_attributes=True)


class BTGStatsResponse(BaseModel):
    """Hospital emergency department compliance and access statistics."""

    facilityId: str = Field(description="Healthcare facility ID")
    totalBTGOverrides: int = Field(description="Total emergency overrides executed")
    distinctPatientsAccessed: int = Field(description="Distinct patients accessed under BTG")
    distinctCliniciansExecuting: int = Field(description="Distinct clinicians who triggered BTG")
    justificationDistribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Breakdown of overrides by justification category",
    )

    model_config = ConfigDict(from_attributes=True)
