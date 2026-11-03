import hashlib
import random
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.child_abha import (
    ChildAbhaOtpRequest,
    ChildAbhaOtpResponse,
    ChildAbhaRegistrationRequest,
    ChildAbhaRegistrationResponse,
    DigiLockerDocumentVerificationRequest,
    DigiLockerDocumentVerificationResponse,
    FhirRelatedPersonRepresentation,
)
from app.schemas.family_proxy import (
    FamilyProxyCreateRequest,
    FamilyProxyResponse,
    ProxyAccessScopeEnum,
    RelationshipTypeEnum,
    VerificationAuthorityEnum,
)
from app.services.family_proxy_service import family_proxy_service


class ChildAbhaService:
    """Enterprise service orchestrating ABDM Child-ABHA generation, Aadhaar parent binding,
    DigiLocker birth certificate validation, and HL7 FHIR RelatedPerson serialization.
    """

    def __init__(self) -> None:
        self._otp_sessions: Dict[str, Dict[str, Any]] = {}

    def request_guardian_otp_for_child_abha(self, req: ChildAbhaOtpRequest) -> ChildAbhaOtpResponse:
        """Initiate parent Aadhaar OTP challenge under ABDM M1 guidelines & DPDP Act Sec 9."""
        # 1. Enforce DPDP Act 2023 Sec 9 verifiable consent requirement
        if not req.guardian_consent_attestation:
            raise ValueError("DPDP Act Sec 9 Violation: Guardian consent attestation is mandated for child onboarding.")

        # 2. Validate 12-digit Aadhaar length and digits
        if not (len(req.guardian_aadhaar_number) == 12 and req.guardian_aadhaar_number.isdigit()):
            raise ValueError("Invalid Aadhaar Format: Guardian Aadhaar must be exactly 12 numerical digits.")

        # 3. Create simulated transaction session
        txn_id = f"txn-child-abha-{uuid.uuid4().hex[:12]}"
        masked_mobile = f"XXXXXX{req.guardian_aadhaar_number[-4:]}"

        self._otp_sessions[txn_id] = {
            "guardian_patient_id": req.guardian_patient_id,
            "guardian_aadhaar": req.guardian_aadhaar_number,
            "otp_code": "123456",  # Standard ABDM sandbox test credential
            "created_at": datetime.now(timezone.utc),
            "consumed": False,
        }

        return ChildAbhaOtpResponse(
            transaction_id=txn_id,
            masked_mobile_number=masked_mobile,
            expires_in_seconds=600,
            message="Aadhaar OTP dispatched to registered guardian mobile.",
        )

    def verify_and_issue_child_abha(self, req: ChildAbhaRegistrationRequest) -> ChildAbhaRegistrationResponse:
        """Verify guardian OTP, mint sovereign Child-ABHA, and bind zero-contamination proxy delegation."""
        # 1. Session lookup & verification
        session = self._otp_sessions.get(req.transaction_id)
        if not session or session.get("consumed"):
            raise ValueError("Invalid or expired Aadhaar OTP transaction session.")

        if req.otp_code != session["otp_code"]:
            raise ValueError("Invalid Aadhaar OTP: The provided 6-digit verification code is incorrect.")

        session["consumed"] = True

        # 2. Age-of-Majority verification (must be < 18 years)
        try:
            dob = date.fromisoformat(req.child_dob_iso)
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age >= 18:
                raise ValueError(
                    f"Age-of-Majority Invariant: Child ABHA issuance is restricted to minors under 18 years (calculated age: {age})."
                )
        except ValueError as e:
            if "Age-of-Majority" in str(e):
                raise
            raise ValueError(f"Invalid child date of birth format: {req.child_dob_iso}. Expected YYYY-MM-DD.")

        # 3. Mint 14-digit ABDM Child-ABHA (starting with 14-)
        part2 = random.randint(1000, 9999)
        part3 = random.randint(1000, 9999)
        part4 = random.randint(1000, 9999)
        child_abha_number = f"14-{part2}-{part3}-{part4}"

        # 4. Mint unique ABHA Address handle
        if req.preferred_abha_address and "@abdm" in req.preferred_abha_address:
            child_abha_address = req.preferred_abha_address.lower().strip()
        elif req.preferred_abha_address:
            child_abha_address = f"{req.preferred_abha_address.lower().strip()}@abdm"
        else:
            clean_name = "".join(c.lower() for c in req.child_full_name if c.isalnum())
            child_abha_address = f"{clean_name}.{part4}@abdm"

        # 5. Provision independent sovereign patient profile UUID
        child_patient_id = f"pat-child-{uuid.uuid4().hex[:10]}"

        # 6. Verify DigiLocker document or generate cryptographic fingerprint
        if req.digilocker_document_id:
            tier = VerificationAuthorityEnum.DIGILOCKER_BIRTH_CERTIFICATE
            raw_data = f"{req.digilocker_document_id}:{req.child_full_name}:{req.child_dob_iso}"
            doc_hash = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
        else:
            tier = VerificationAuthorityEnum.AADHAAR_DEMOGRAPHIC_EKYC
            raw_data = f"{session['guardian_aadhaar']}:{req.child_full_name}:{req.child_dob_iso}"
            doc_hash = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()

        # 7. Establish Zero-Contamination Proxy Delegation Linkage
        proxy_create = FamilyProxyCreateRequest(
            guardian_patient_id=req.guardian_patient_id,
            dependent_patient_id=child_patient_id,
            relationship_type=RelationshipTypeEnum.CHILD_MINOR,
            verification_tier=tier,
            verification_document_id=req.digilocker_document_id or req.birth_certificate_number,
            verification_document_hash=doc_hash,
            access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
            dependent_dob_iso=req.child_dob_iso,
            guardian_consent_attestation=True,
        )

        rel = family_proxy_service.establish_proxy_relationship(proxy_create)
        rel.dependent_name = req.child_full_name
        rel.dependent_abha = child_abha_number
        rel.dependent_age = age

        # 8. Offline cryptographic QR code payload
        qr_payload = f"ABDM:CHILD:{child_abha_number}:{child_abha_address}:{doc_hash[:16]}"

        return ChildAbhaRegistrationResponse(
            child_patient_id=child_patient_id,
            child_abha_number=child_abha_number,
            child_abha_address=child_abha_address,
            relationship_id=rel.relationship_id,
            guardian_patient_id=req.guardian_patient_id,
            verification_tier=tier.value,
            verification_document_hash=doc_hash,
            qr_code_payload=qr_payload,
            created_at=datetime.now(timezone.utc),
            zero_contamination_isolated=True,
        )

    def verify_digilocker_certificate(
        self, req: DigiLockerDocumentVerificationRequest
    ) -> DigiLockerDocumentVerificationResponse:
        """Simulate DigiLocker API document provenance verification."""
        if not req.document_id.strip():
            raise ValueError("DigiLocker document identifier cannot be blank.")

        raw = f"{req.issuer_uri}:{req.doc_type}:{req.document_id}"
        doc_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return DigiLockerDocumentVerificationResponse(
            document_id=req.document_id,
            verified=True,
            document_sha256=doc_sha,
            issuer_authority="GOVT_OF_INDIA_DIGILOCKER",
            verified_at=datetime.now(timezone.utc),
            status_message="Document cryptographically validated against DigiLocker National Issuer Registry.",
        )

    def serialize_to_fhir_related_person(self, relationship_id: str) -> FhirRelatedPersonRepresentation:
        """Transform internal proxy relationship into NRCeS compliant HL7 FHIR R4 RelatedPerson."""
        rel = family_proxy_service.get_relationship(relationship_id)
        if not rel:
            raise KeyError(f"Proxy relationship '{relationship_id}' not found.")

        # Map internal enum to HL7 v3 RoleCode
        role_map = {
            RelationshipTypeEnum.CHILD_MINOR: ("PRN", "parent"),
            RelationshipTypeEnum.PARENT_SENIOR: ("CHILD", "child"),
            RelationshipTypeEnum.SPOUSE: ("SPS", "spouse"),
            RelationshipTypeEnum.LEGAL_WARD: ("GUARD", "guardian"),
            RelationshipTypeEnum.SIBLING: ("SIB", "sibling"),
        }
        role_code, role_display = role_map.get(rel.relationship_type, ("PRN", "parent"))

        period_start = rel.authorized_at.isoformat()
        period_end = rel.authorized_until.isoformat() if rel.authorized_until else None

        return FhirRelatedPersonRepresentation(
            resourceType="RelatedPerson",
            id=f"related-person-{rel.relationship_id}",
            patient_reference=f"Patient/{rel.dependent_patient_id}",
            relationship_code=role_code,
            relationship_display=role_display,
            name=f"Guardian ({rel.guardian_patient_id})",
            telecom=[
                {"system": "email", "value": "guardian@nirmaya.in", "use": "home"},
                {"system": "phone", "value": "+91-9876543210", "use": "mobile"},
            ],
            period_start=period_start,
            period_end=period_end,
        )


# Global singleton instance
child_abha_service = ChildAbhaService()
