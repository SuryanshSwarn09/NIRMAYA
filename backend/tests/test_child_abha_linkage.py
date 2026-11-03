import os
from datetime import date, datetime, timezone
import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.schemas.child_abha import (
    ChildAbhaOtpRequest,
    ChildAbhaOtpResponse,
    ChildAbhaRegistrationRequest,
    ChildAbhaRegistrationResponse,
    ChildGenderEnum,
    DigiLockerDocumentVerificationRequest,
    DigiLockerDocumentVerificationResponse,
    FhirRelatedPersonRepresentation,
)
from app.services.child_abha_service import ChildAbhaService, child_abha_service


# =============================================================================
# 1. Schema & Validation Tests
# =============================================================================

def test_child_gender_enum_values():
    """Verify supported administrative gender values for child registration."""
    assert ChildGenderEnum.MALE.value == "MALE"
    assert ChildGenderEnum.FEMALE.value == "FEMALE"
    assert ChildGenderEnum.OTHER.value == "OTHER"


def test_child_abha_otp_schemas():
    """Verify validation and serialization of OTP request and response schemas."""
    req = ChildAbhaOtpRequest(
        guardian_patient_id="pat-guardian-01",
        guardian_aadhaar_number="548190284821",
        guardian_consent_attestation=True,
    )
    assert req.guardian_aadhaar_number == "548190284821"

    res = ChildAbhaOtpResponse(
        transaction_id="txn-test-01",
        masked_mobile_number="XXXXXX4821",
        expires_in_seconds=600,
        message="Aadhaar OTP dispatched",
    )
    assert res.expires_in_seconds == 600


def test_child_abha_registration_schemas():
    """Verify serialization of registration request and response schemas."""
    req = ChildAbhaRegistrationRequest(
        transaction_id="txn-test-01",
        otp_code="123456",
        guardian_patient_id="pat-guardian-01",
        child_full_name="Diya Sharma",
        child_gender=ChildGenderEnum.FEMALE,
        child_dob_iso="2021-04-18",
        preferred_abha_address="diya.sharma",
    )
    assert req.child_full_name == "Diya Sharma"

    res = ChildAbhaRegistrationResponse(
        child_patient_id="pat-child-01",
        child_abha_number="14-8291-0391-4821",
        child_abha_address="diya.sharma@abdm",
        relationship_id="rel-test-01",
        guardian_patient_id="pat-guardian-01",
        verification_tier="DIGILOCKER_BIRTH_CERTIFICATE",
        verification_document_hash="8f12a048c081294801928409182409182b0412984109481b049182b041298410",
        qr_code_payload="ABDM:CHILD:14-8291-0391-4821:diya.sharma@abdm",
        zero_contamination_isolated=True,
    )
    assert res.zero_contamination_isolated is True


def test_digilocker_verification_schemas():
    """Verify DigiLocker verification request and response models."""
    req = DigiLockerDocumentVerificationRequest(
        document_id="DOC-BIRTH-2021-001",
        doc_type="BIRTH_CERTIFICATE",
    )
    assert req.document_id == "DOC-BIRTH-2021-001"

    res = DigiLockerDocumentVerificationResponse(
        document_id="DOC-BIRTH-2021-001",
        verified=True,
        document_sha256="hash-abc",
        issuer_authority="GOVT_OF_INDIA_DIGILOCKER",
        status_message="Valid",
    )
    assert res.verified is True


def test_fhir_related_person_schema():
    """Verify NRCeS HL7 FHIR R4 RelatedPerson representation model."""
    fhir = FhirRelatedPersonRepresentation(
        id="related-person-rel-01",
        patient_reference="Patient/pat-child-01",
        relationship_code="PRN",
        relationship_display="parent",
        name="Dr. Priya Sharma",
        period_start=datetime.now(timezone.utc).isoformat(),
    )
    assert fhir.resourceType == "RelatedPerson"
    assert fhir.relationship_code == "PRN"


# =============================================================================
# 2. Service Logic & Invariant Tests
# =============================================================================

def test_service_request_otp_consent_mandated():
    """Verify invariant: DPDP Act Sec 9 requires guardian consent attestation."""
    service = ChildAbhaService()
    req = ChildAbhaOtpRequest(
        guardian_patient_id="pat-guardian-01",
        guardian_aadhaar_number="548190284821",
        guardian_consent_attestation=False,  # Absent consent
    )
    with pytest.raises(ValueError) as exc:
        service.request_guardian_otp_for_child_abha(req)
    assert "DPDP Act Sec 9 Violation" in str(exc.value)


def test_service_request_otp_invalid_aadhaar():
    """Verify error raised when Aadhaar format is invalid."""
    with pytest.raises(ValidationError):
        ChildAbhaOtpRequest(
            guardian_patient_id="pat-guardian-01",
            guardian_aadhaar_number="1234",  # Too short
            guardian_consent_attestation=True,
        )


def test_service_request_otp_success():
    """Verify successful Aadhaar OTP challenge dispatch."""
    service = ChildAbhaService()
    req = ChildAbhaOtpRequest(
        guardian_patient_id="pat-guardian-01",
        guardian_aadhaar_number="548190284821",
        guardian_consent_attestation=True,
    )
    res = service.request_guardian_otp_for_child_abha(req)
    assert res.transaction_id.startswith("txn-child-abha-")
    assert res.masked_mobile_number == "XXXXXX4821"
    assert res.expires_in_seconds == 600


def test_service_verify_and_issue_invalid_transaction():
    """Verify error raised when transaction ID is unknown."""
    service = ChildAbhaService()
    req = ChildAbhaRegistrationRequest(
        transaction_id="txn-invalid-999",
        otp_code="123456",
        guardian_patient_id="pat-guardian-01",
        child_full_name="Diya Sharma",
        child_gender=ChildGenderEnum.FEMALE,
        child_dob_iso="2021-04-18",
    )
    with pytest.raises(ValueError) as exc:
        service.verify_and_issue_child_abha(req)
    assert "Invalid or expired" in str(exc.value)


def test_service_verify_and_issue_wrong_otp():
    """Verify error raised when OTP is incorrect."""
    service = ChildAbhaService()
    otp_resp = service.request_guardian_otp_for_child_abha(
        ChildAbhaOtpRequest(
            guardian_patient_id="pat-guardian-01",
            guardian_aadhaar_number="548190284821",
            guardian_consent_attestation=True,
        )
    )

    req = ChildAbhaRegistrationRequest(
        transaction_id=otp_resp.transaction_id,
        otp_code="999999",  # Wrong OTP
        guardian_patient_id="pat-guardian-01",
        child_full_name="Diya Sharma",
        child_gender=ChildGenderEnum.FEMALE,
        child_dob_iso="2021-04-18",
    )
    with pytest.raises(ValueError) as exc:
        service.verify_and_issue_child_abha(req)
    assert "Invalid Aadhaar OTP" in str(exc.value)


def test_service_verify_and_issue_age_of_majority_enforcement():
    """Verify invariant: Child ABHA cannot be issued to adults (age >= 18)."""
    service = ChildAbhaService()
    otp_resp = service.request_guardian_otp_for_child_abha(
        ChildAbhaOtpRequest(
            guardian_patient_id="pat-guardian-01",
            guardian_aadhaar_number="548190284821",
            guardian_consent_attestation=True,
        )
    )

    req = ChildAbhaRegistrationRequest(
        transaction_id=otp_resp.transaction_id,
        otp_code="123456",
        guardian_patient_id="pat-guardian-01",
        child_full_name="Adult User",
        child_gender=ChildGenderEnum.MALE,
        child_dob_iso="2000-01-01",  # 26 years old
    )
    with pytest.raises(ValueError) as exc:
        service.verify_and_issue_child_abha(req)
    assert "Age-of-Majority Invariant" in str(exc.value)


def test_service_verify_and_issue_child_abha_success():
    """Verify successful minting of Child ABHA with sovereign profile."""
    service = ChildAbhaService()
    otp_resp = service.request_guardian_otp_for_child_abha(
        ChildAbhaOtpRequest(
            guardian_patient_id="pat-guardian-01",
            guardian_aadhaar_number="548190284821",
            guardian_consent_attestation=True,
        )
    )

    req = ChildAbhaRegistrationRequest(
        transaction_id=otp_resp.transaction_id,
        otp_code="123456",
        guardian_patient_id="pat-guardian-01",
        child_full_name="Diya Sharma",
        child_gender=ChildGenderEnum.FEMALE,
        child_dob_iso="2021-04-18",
        preferred_abha_address="diya.sharma",
    )
    res = service.verify_and_issue_child_abha(req)

    assert res.child_abha_number.startswith("14-")
    assert res.child_abha_address == "diya.sharma@abdm"
    assert res.zero_contamination_isolated is True
    assert res.relationship_id.startswith("rel-proxy-")
    assert res.guardian_patient_id == "pat-guardian-01"


def test_service_verify_and_issue_with_digilocker_certificate():
    """Verify DigiLocker birth certificate attachment elevates verification tier."""
    service = ChildAbhaService()
    otp_resp = service.request_guardian_otp_for_child_abha(
        ChildAbhaOtpRequest(
            guardian_patient_id="pat-guardian-01",
            guardian_aadhaar_number="548190284821",
            guardian_consent_attestation=True,
        )
    )

    req = ChildAbhaRegistrationRequest(
        transaction_id=otp_resp.transaction_id,
        otp_code="123456",
        guardian_patient_id="pat-guardian-01",
        child_full_name="Rohan Sharma",
        child_gender=ChildGenderEnum.MALE,
        child_dob_iso="2022-09-10",
        digilocker_document_id="DOC-DL-BIRTH-89102",
    )
    res = service.verify_and_issue_child_abha(req)
    assert res.verification_tier == "DIGILOCKER_BIRTH_CERTIFICATE"
    assert len(res.verification_document_hash) == 64


def test_service_verify_digilocker_certificate():
    """Verify standalone DigiLocker adapter document verification."""
    service = ChildAbhaService()
    req = DigiLockerDocumentVerificationRequest(
        document_id="NDMC-BIRTH-2021-981240",
        doc_type="BIRTH_CERTIFICATE",
    )
    res = service.verify_digilocker_certificate(req)
    assert res.verified is True
    assert res.issuer_authority == "GOVT_OF_INDIA_DIGILOCKER"
    assert len(res.document_sha256) == 64


def test_service_verify_digilocker_blank_id():
    """Verify error raised on empty DigiLocker document ID."""
    service = ChildAbhaService()
    req = DigiLockerDocumentVerificationRequest(
        document_id="   ",
    )
    with pytest.raises(ValueError):
        service.verify_digilocker_certificate(req)


def test_service_serialize_fhir_related_person():
    """Verify HL7 FHIR R4 RelatedPerson serialization for existing proxy."""
    res = child_abha_service.serialize_to_fhir_related_person("rel-proxy-child-001")
    assert res.resourceType == "RelatedPerson"
    assert res.patient_reference == "Patient/pat-aarav-sharma-02"
    assert res.relationship_code == "PRN"
    assert res.relationship_display == "parent"


def test_service_serialize_fhir_related_person_not_found():
    """Verify KeyError raised when relationship ID is absent."""
    with pytest.raises(KeyError):
        child_abha_service.serialize_to_fhir_related_person("rel-nonexistent-000")


# =============================================================================
# 3. FastAPI Endpoint Integration Tests
# =============================================================================

@pytest.mark.asyncio
async def test_api_request_child_abha_otp(client: AsyncClient):
    """Verify POST /api/v1/patients/proxy/child-abha/otp-request endpoint."""
    payload = {
        "guardian_patient_id": "pat-priya-sharma-01",
        "guardian_aadhaar_number": "548190284821",
        "guardian_consent_attestation": True,
    }
    resp = await client.post("/api/v1/patients/proxy/child-abha/otp-request", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "transaction_id" in data
    assert data["masked_mobile_number"] == "XXXXXX4821"


@pytest.mark.asyncio
async def test_api_request_child_abha_otp_validation_error(client: AsyncClient):
    """Verify POST /api/v1/patients/proxy/child-abha/otp-request fails without consent."""
    payload = {
        "guardian_patient_id": "pat-priya-sharma-01",
        "guardian_aadhaar_number": "548190284821",
        "guardian_consent_attestation": False,
    }
    resp = await client.post("/api/v1/patients/proxy/child-abha/otp-request", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_api_verify_and_issue_child_abha_success(client: AsyncClient):
    """Verify POST /api/v1/patients/proxy/child-abha/verify-and-create endpoint."""
    # First, request OTP
    otp_resp = await client.post(
        "/api/v1/patients/proxy/child-abha/otp-request",
        json={
            "guardian_patient_id": "pat-priya-sharma-01",
            "guardian_aadhaar_number": "548190284821",
            "guardian_consent_attestation": True,
        },
    )
    txn_id = otp_resp.json()["transaction_id"]

    # Verify and issue
    payload = {
        "transaction_id": txn_id,
        "otp_code": "123456",
        "guardian_patient_id": "pat-priya-sharma-01",
        "child_full_name": "Kavya Sharma",
        "child_gender": "FEMALE",
        "child_dob_iso": "2022-01-15",
        "preferred_abha_address": "kavya.sharma",
    }
    resp = await client.post("/api/v1/patients/proxy/child-abha/verify-and-create", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["child_abha_number"].startswith("14-")
    assert data["child_abha_address"] == "kavya.sharma@abdm"
    assert data["zero_contamination_isolated"] is True


@pytest.mark.asyncio
async def test_api_verify_and_issue_child_abha_wrong_otp(client: AsyncClient):
    """Verify POST /api/v1/patients/proxy/child-abha/verify-and-create rejects wrong OTP."""
    otp_resp = await client.post(
        "/api/v1/patients/proxy/child-abha/otp-request",
        json={
            "guardian_patient_id": "pat-priya-sharma-01",
            "guardian_aadhaar_number": "548190284821",
            "guardian_consent_attestation": True,
        },
    )
    txn_id = otp_resp.json()["transaction_id"]

    payload = {
        "transaction_id": txn_id,
        "otp_code": "000000",  # Invalid OTP
        "guardian_patient_id": "pat-priya-sharma-01",
        "child_full_name": "Kavya Sharma",
        "child_gender": "FEMALE",
        "child_dob_iso": "2022-01-15",
    }
    resp = await client.post("/api/v1/patients/proxy/child-abha/verify-and-create", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_api_verify_digilocker_document(client: AsyncClient):
    """Verify POST /api/v1/patients/proxy/child-abha/digilocker/verify endpoint."""
    payload = {
        "document_id": "NDMC-BIRTH-2021-981240",
        "doc_type": "BIRTH_CERTIFICATE",
    }
    resp = await client.post("/api/v1/patients/proxy/child-abha/digilocker/verify", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert len(data["document_sha256"]) == 64


@pytest.mark.asyncio
async def test_api_export_fhir_related_person(client: AsyncClient):
    """Verify GET /api/v1/patients/proxy/child-abha/{relationship_id}/fhir-related-person."""
    resp = await client.get("/api/v1/patients/proxy/child-abha/rel-proxy-child-001/fhir-related-person")
    assert resp.status_code == 200
    data = resp.json()
    assert data["resourceType"] == "RelatedPerson"
    assert data["relationship_code"] == "PRN"
    assert data["patient_reference"] == "Patient/pat-aarav-sharma-02"


@pytest.mark.asyncio
async def test_api_export_fhir_related_person_404(client: AsyncClient):
    """Verify GET /api/v1/patients/proxy/child-abha/{relationship_id}/fhir-related-person returns 404."""
    resp = await client.get("/api/v1/patients/proxy/child-abha/rel-nonexistent-000/fhir-related-person")
    assert resp.status_code == 404
