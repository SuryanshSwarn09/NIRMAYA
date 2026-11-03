import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChildGenderEnum(str, Enum):
    """Gender categorization aligned with HL7 FHIR AdministrativeGender and ABDM standards."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class ChildAbhaOtpRequest(BaseModel):
    """Payload to request guardian Aadhaar OTP challenge for Child-ABHA issuance."""
    guardian_patient_id: str = Field(..., description="Unique ID of verified guardian patient profile")
    guardian_aadhaar_number: str = Field(..., min_length=12, max_length=12, description="12-digit Aadhaar number of parent/guardian")
    guardian_consent_attestation: bool = Field(..., description="Verifiable consent attestation under DPDP Act 2023 Sec 9")


class ChildAbhaOtpResponse(BaseModel):
    """Challenge payload returned by ABDM M1 gateway simulator."""
    transaction_id: str = Field(..., description="Transient session identifier for OTP verification")
    masked_mobile_number: str = Field(..., description="Masked guardian mobile number (e.g., XXXXXX4821)")
    expires_in_seconds: int = Field(600, description="OTP validity duration in seconds")
    message: str = Field("Aadhaar OTP dispatched to registered guardian mobile.", description="Status message")


class ChildAbhaRegistrationRequest(BaseModel):
    """Payload to verify guardian OTP, mint sovereign Child-ABHA, and bind demographic linkage."""
    transaction_id: str = Field(..., description="Transaction ID returned from OTP challenge")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    guardian_patient_id: str = Field(..., description="Unique ID of guardian patient profile")
    child_full_name: str = Field(..., min_length=2, max_length=100, description="Legal full name of minor child")
    child_gender: ChildGenderEnum = Field(..., description="Administrative gender of child")
    child_dob_iso: str = Field(..., description="Date of birth in YYYY-MM-DD format (must be < 18 years)")
    preferred_abha_address: Optional[str] = Field(None, description="Requested ABHA address handle (e.g. child@abdm)")
    birth_certificate_number: Optional[str] = Field(None, description="Municipal birth certificate registration number")
    digilocker_document_id: Optional[str] = Field(None, description="DigiLocker document URI for birth certificate")


class ChildAbhaRegistrationResponse(BaseModel):
    """Result of Child-ABHA generation, sovereign patient profile provisioning, and proxy linkage."""
    child_patient_id: str = Field(..., description="Isolated sovereign patient profile UUID for dependent")
    child_abha_number: str = Field(..., description="Newly issued 14-digit ABDM compliant ABHA (14-XXXX-XXXX-XXXX)")
    child_abha_address: str = Field(..., description="Federated ABHA address handle (e.g. aarav.sharma@abdm)")
    relationship_id: str = Field(..., description="Identifier of the resulting PatientProxyRelationship delegation")
    guardian_patient_id: str = Field(..., description="Parent or legal guardian patient UUID")
    verification_tier: str = Field(..., description="Verification tier granted to relationship")
    verification_document_hash: str = Field(..., description="SHA-256 fingerprint of verification certificate")
    qr_code_payload: str = Field(..., description="Cryptographic QR code string for offline credential presentation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    zero_contamination_isolated: bool = Field(True, description="Certification that child records are strictly isolated")


class DigiLockerDocumentVerificationRequest(BaseModel):
    """Request to verify municipal birth certificate or adoption order via DigiLocker."""
    document_id: str = Field(..., description="DigiLocker document identifier")
    doc_type: str = Field("BIRTH_CERTIFICATE", description="Type of document (e.g. BIRTH_CERTIFICATE, ADOPTION_DEED)")
    issuer_uri: str = Field("in.gov.digilocker.registry", description="Originating government certificate authority")


class DigiLockerDocumentVerificationResponse(BaseModel):
    """Proof of verification returned from DigiLocker API adapter."""
    document_id: str
    verified: bool
    document_sha256: str
    issuer_authority: str
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status_message: str


class FhirRelatedPersonRepresentation(BaseModel):
    """HL7 FHIR R4 RelatedPerson representation aligned with NRCeS guidelines."""
    resourceType: str = Field("RelatedPerson", description="FHIR resource type")
    id: str = Field(..., description="Unique FHIR resource identifier")
    patient_reference: str = Field(..., description="Reference to dependent patient resource (e.g. Patient/pat-002)")
    relationship_code: str = Field(..., description="HL7 v3 RoleCode (e.g. PRN, MTH, FTH, GUARD)")
    relationship_display: str = Field(..., description="Human-readable relationship description")
    name: str = Field(..., description="Legal name of guardian")
    telecom: List[Dict[str, str]] = Field(default_factory=list, description="Contact telecom information")
    period_start: str = Field(..., description="ISO timestamp when proxy authority commenced")
    period_end: Optional[str] = Field(None, description="Optional ISO timestamp when authority expires or null")
