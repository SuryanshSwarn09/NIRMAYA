"""Unit and integration tests for ABDM Milestone 3 (M3) Health Information User (HIU) Data Consumer Engine.

Tests conform to NHA ABDM v0.5 and Fidelius specifications:
- HIU Request Initiation & Ephemeral Curve25519 Key Generation
- Nonce XOR + ECDH Key Agreement + HKDF-SHA256 Derivation on inbound transfer
- AES-256-GCM authenticated decryption and 128-bit tag verification
- Tamper-evident SHA-256 checksum verification
- Clinical FHIR R4 Document Bundle parser (Encounter, DiagnosticReport, Prescription, Observation)
- Longitudinal Patient Record Store and Aggregation API
- Inbound Transfer Receiver (/api/v1/abdm/m3/hiu/transfer & /v0.5/health-information/transfer)
"""

import base64
from datetime import datetime, timezone, timedelta
import hashlib
import json
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.abdm_hiu import (
    AbdmHIUService,
    hiu_record_store,
    hiu_request_store,
)
from app.services.abdm_crypto import AbdmCryptoService
from app.services.abdm_transfer import AbdmTransferService, transfer_audit_store
from app.schemas.abdm_m3_hiu import (
    HIUDataRequestInitiate,
    HIURequestSession,
)
from app.schemas.abdm_m3_crypto import KeyMaterial, KeyUserInfo
from app.schemas.abdm_m3_transfer import DataTransferPushPayload, EncryptedDataEntry


@pytest.fixture(autouse=True)
def clean_hiu_stores():
    """Reset HIU in-memory stores before and after each test."""
    hiu_request_store.clear()
    hiu_record_store.clear()
    transfer_audit_store.clear()
    yield
    hiu_request_store.clear()
    hiu_record_store.clear()
    transfer_audit_store.clear()


@pytest.mark.asyncio
async def test_hiu_request_initiation():
    """Verify HIU request generates ephemeral Curve25519 keypair, 32-byte nonce, and caches session."""
    now = datetime.now(timezone.utc)
    req = HIUDataRequestInitiate(
        consentId=f"consent-{uuid.uuid4()}",
        patientId="sneha.sharma@abdm",
        dateRangeFrom=now - timedelta(days=60),
        dateRangeTo=now,
        hiTypes=["OPConsultation", "DiagnosticReport"],
    )

    session, gateway_payload = AbdmHIUService.initiate_hi_request(req)

    assert session is not None
    assert session.patientId == "sneha.sharma@abdm"
    assert session.status == "REQUESTED"
    assert len(base64.b64decode(session.hiuPublicKey)) == 32
    assert len(base64.b64decode(session.hiuNonce)) == 32

    # Check cached in HIURequestStore
    cached = hiu_request_store.get_session(session.transactionId)
    assert cached is not None
    assert cached.consentId == req.consentId

    # Verify Gateway payload format
    assert "hiRequest" in gateway_payload
    assert gateway_payload["hiRequest"]["consent"]["id"] == req.consentId
    assert gateway_payload["hiRequest"]["keyMaterial"]["cryptoAlg"] == "ECDH"
    assert gateway_payload["hiRequest"]["keyMaterial"]["curve"] == "Curve25519"


@pytest.mark.asyncio
async def test_hiu_inbound_transfer_decryption():
    """Simulate peer HIP encrypting FHIR bundle and verify HIU correctly derives key and decrypts payload."""
    now = datetime.now(timezone.utc)
    req = HIUDataRequestInitiate(
        consentId=f"consent-{uuid.uuid4()}",
        patientId="sneha.sharma@abdm",
        dateRangeFrom=now - timedelta(days=30),
        dateRangeTo=now,
    )
    hiu_session, _ = AbdmHIUService.initiate_hi_request(req)

    # Simulate Peer HIP
    _, hip_pub_b64, hip_priv_b64 = AbdmCryptoService.generate_key_pair()
    hip_nonce_bytes, hip_nonce_b64 = AbdmCryptoService.generate_nonce()

    # Peer HIP calculates shared secret and key
    hiu_pub = AbdmCryptoService.parse_public_key(hiu_session.hiuPublicKey)
    hip_priv = AbdmCryptoService.parse_private_key(hip_priv_b64)
    hiu_nonce_bytes = AbdmCryptoService.parse_nonce(hiu_session.hiuNonce)

    _, salt, iv = AbdmCryptoService.compute_xor_entropy(hip_nonce_bytes, hiu_nonce_bytes)
    shared_secret = AbdmCryptoService.derive_shared_secret(hip_priv, hiu_pub)
    derived_key = AbdmCryptoService.derive_symmetric_key(shared_secret, salt)

    # HIP encrypts sample clinical bundle
    sample_bundle_json = AbdmTransferService.generate_clinical_bundle_json(
        care_context_ref="ENC-2026-0099",
        hi_type="DiagnosticReport",
        patient_id="sneha.sharma@abdm",
    )
    b64_ciphertext, checksum = AbdmTransferService.encrypt_payload(
        plaintext=sample_bundle_json,
        derived_key=derived_key,
        iv=iv,
    )

    push_payload = DataTransferPushPayload(
        pageNumber=1,
        pageCount=1,
        transactionId=uuid.UUID(hiu_session.transactionId),
        entries=[
            EncryptedDataEntry(
                content=b64_ciphertext,
                media="application/fhir+json",
                checksum=checksum,
                careContextReference="ENC-2026-0099",
            )
        ],
        keyMaterial=KeyMaterial(
            cryptoAlg="ECDH",
            curve="Curve25519",
            userInfo=KeyUserInfo(
                publicKey=hip_pub_b64,
                nonce=hip_nonce_b64,
            ),
        ),
    )

    # HIU processes inbound transfer
    success, error_msg, bundles = AbdmHIUService.process_inbound_transfer(push_payload)

    assert success is True
    assert error_msg is None
    assert len(bundles) == 1
    assert bundles[0].careContextReference == "ENC-2026-0099"
    assert len(bundles[0].encounters) >= 1
    assert len(bundles[0].diagnosticReports) >= 1

    # Check session updated to PROCESSED
    updated_session = hiu_request_store.get_session(hiu_session.transactionId)
    assert updated_session.status == "PROCESSED"

    # Check saved in HIURecordStore
    saved_records = hiu_record_store.get_patient_records("sneha.sharma@abdm")
    assert len(saved_records) == 1


@pytest.mark.asyncio
async def test_hiu_inbound_transfer_checksum_mismatch():
    """Verify transfer is rejected if payload checksum does not match decrypted bundle."""
    now = datetime.now(timezone.utc)
    req = HIUDataRequestInitiate(
        consentId="consent-checksum-test",
        patientId="sneha.sharma@abdm",
        dateRangeFrom=now - timedelta(days=10),
        dateRangeTo=now,
    )
    hiu_session, _ = AbdmHIUService.initiate_hi_request(req)

    # Peer HIP encrypts
    _, hip_pub_b64, hip_priv_b64 = AbdmCryptoService.generate_key_pair()
    hip_nonce_bytes, hip_nonce_b64 = AbdmCryptoService.generate_nonce()
    hiu_pub = AbdmCryptoService.parse_public_key(hiu_session.hiuPublicKey)
    hip_priv = AbdmCryptoService.parse_private_key(hip_priv_b64)
    hiu_nonce_bytes = AbdmCryptoService.parse_nonce(hiu_session.hiuNonce)

    _, salt, iv = AbdmCryptoService.compute_xor_entropy(hip_nonce_bytes, hiu_nonce_bytes)
    shared_secret = AbdmCryptoService.derive_shared_secret(hip_priv, hiu_pub)
    derived_key = AbdmCryptoService.derive_symmetric_key(shared_secret, salt)

    b64_ciphertext, _ = AbdmTransferService.encrypt_payload(
        plaintext=json.dumps({"resourceType": "Bundle"}),
        derived_key=derived_key,
        iv=iv,
    )

    # Provide falsified checksum
    push_payload = DataTransferPushPayload(
        pageNumber=1,
        pageCount=1,
        transactionId=uuid.UUID(hiu_session.transactionId),
        entries=[
            EncryptedDataEntry(
                content=b64_ciphertext,
                media="application/fhir+json",
                checksum="falsified-checksum-sha256-digest-value",
                careContextReference="ENC-BAD-01",
            )
        ],
        keyMaterial=KeyMaterial(
            cryptoAlg="ECDH",
            curve="Curve25519",
            userInfo=KeyUserInfo(publicKey=hip_pub_b64, nonce=hip_nonce_b64),
        ),
    )

    success, error_msg, bundles = AbdmHIUService.process_inbound_transfer(push_payload)
    assert success is False
    assert "checksum mismatch" in error_msg.lower()
    assert len(bundles) == 0


@pytest.mark.asyncio
async def test_hiu_inbound_transfer_invalid_tag():
    """Verify tampered ciphertext is rejected with tag mismatch error."""
    now = datetime.now(timezone.utc)
    req = HIUDataRequestInitiate(
        consentId="consent-tag-test",
        patientId="sneha.sharma@abdm",
        dateRangeFrom=now - timedelta(days=10),
        dateRangeTo=now,
    )
    hiu_session, _ = AbdmHIUService.initiate_hi_request(req)

    _, hip_pub_b64, _ = AbdmCryptoService.generate_key_pair()
    _, hip_nonce_b64 = AbdmCryptoService.generate_nonce()

    # Provide garbage ciphertext
    push_payload = DataTransferPushPayload(
        pageNumber=1,
        pageCount=1,
        transactionId=uuid.UUID(hiu_session.transactionId),
        entries=[
            EncryptedDataEntry(
                content=base64.b64encode(b"invalid-ciphertext-bytes-without-valid-tag-000").decode("utf-8"),
                media="application/fhir+json",
                checksum="dummy-checksum",
                careContextReference="ENC-BAD-02",
            )
        ],
        keyMaterial=KeyMaterial(
            cryptoAlg="ECDH",
            curve="Curve25519",
            userInfo=KeyUserInfo(publicKey=hip_pub_b64, nonce=hip_nonce_b64),
        ),
    )

    success, error_msg, bundles = AbdmHIUService.process_inbound_transfer(push_payload)
    assert success is False
    assert "decryption failed" in error_msg.lower() or "authentication tag" in error_msg.lower()


@pytest.mark.asyncio
async def test_fhir_bundle_parser_composition_encounter():
    """Verify FHIR parser extracts Composition and Encounter records into high-level models."""
    sample_json = json.dumps({
        "resourceType": "Bundle",
        "id": "bundle-001",
        "entry": [
            {
                "resource": {
                    "resourceType": "Composition",
                    "title": "Outpatient Consultation Note",
                    "author": [{"display": "Dr. Rohit Sen"}]
                }
            },
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": "enc-001",
                    "status": "finished",
                    "class": {"code": "AMB"},
                    "period": {"start": "2026-10-15T09:30:00Z", "end": "2026-10-15T10:00:00Z"},
                    "serviceProvider": {"display": "NIRMAYA Apex Hospital"}
                }
            }
        ]
    })

    bundle = AbdmHIUService.parse_fhir_bundle(sample_json, "CARE-CTX-100")

    assert bundle.bundleId == "bundle-001"
    assert bundle.compositionTitle == "Outpatient Consultation Note"
    assert bundle.author == "Dr. Rohit Sen"
    assert len(bundle.encounters) == 1
    assert bundle.encounters[0].encounterClass == "AMB"
    assert bundle.encounters[0].status == "finished"
    assert bundle.encounters[0].serviceProvider == "NIRMAYA Apex Hospital"


@pytest.mark.asyncio
async def test_fhir_bundle_parser_diagnostic_report():
    """Verify FHIR parser extracts DiagnosticReport details."""
    sample_json = json.dumps({
        "resourceType": "Bundle",
        "id": "bundle-002",
        "entry": [
            {
                "resource": {
                    "resourceType": "DiagnosticReport",
                    "id": "diag-001",
                    "status": "final",
                    "code": {
                        "coding": [
                            {"code": "24357-6", "display": "Urinalysis macro panel"}
                        ]
                    },
                    "conclusion": "No abnormalities detected",
                    "performer": [{"display": "Metropolis Diagnostic Labs"}]
                }
            }
        ]
    })

    bundle = AbdmHIUService.parse_fhir_bundle(sample_json, "CARE-CTX-101")
    assert len(bundle.diagnosticReports) == 1
    assert bundle.diagnosticReports[0].code == "24357-6"
    assert bundle.diagnosticReports[0].display == "Urinalysis macro panel"
    assert bundle.diagnosticReports[0].conclusion == "No abnormalities detected"
    assert bundle.diagnosticReports[0].performer == "Metropolis Diagnostic Labs"


@pytest.mark.asyncio
async def test_fhir_bundle_parser_prescription():
    """Verify FHIR parser extracts MedicationRequest details."""
    sample_json = json.dumps({
        "resourceType": "Bundle",
        "id": "bundle-003",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "med-001",
                    "status": "active",
                    "medicationCodeableConcept": {
                        "coding": [
                            {"code": "387207008", "display": "Paracetamol 500mg tablet"}
                        ]
                    },
                    "dosageInstruction": [{"text": "1 tablet twice daily after meals"}]
                }
            }
        ]
    })

    bundle = AbdmHIUService.parse_fhir_bundle(sample_json, "CARE-CTX-102")
    assert len(bundle.prescriptions) == 1
    assert bundle.prescriptions[0].medicationCode == "387207008"
    assert bundle.prescriptions[0].medicationName == "Paracetamol 500mg tablet"
    assert bundle.prescriptions[0].dosageInstruction == "1 tablet twice daily after meals"


@pytest.mark.asyncio
async def test_hiu_patient_records_aggregation():
    """Verify clinician can query aggregated records across multiple care contexts."""
    bundle1 = AbdmHIUService.parse_fhir_bundle(
        json.dumps({
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Encounter",
                        "id": "enc-1",
                        "status": "finished",
                        "class": {"code": "AMB"}
                    }
                }
            ]
        }),
        "CTX-01"
    )
    bundle2 = AbdmHIUService.parse_fhir_bundle(
        json.dumps({
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "DiagnosticReport",
                        "id": "rep-1",
                        "status": "final",
                        "code": {"coding": [{"code": "TEST", "display": "CBC Panel"}]},
                        "conclusion": "Normal"
                    }
                }
            ]
        }),
        "CTX-02"
    )

    hiu_record_store.save_records("sneha.sharma@abdm", "tx-test-agg", [bundle1, bundle2])

    resp = AbdmHIUService.aggregate_patient_records("sneha.sharma@abdm")
    assert resp.patientId == "sneha.sharma@abdm"
    assert resp.totalBundles == 2
    assert len(resp.encounters) == 1
    assert len(resp.diagnosticReports) == 1


@pytest.mark.asyncio
async def test_hiu_api_endpoints_full_lifecycle():
    """Verify end-to-end API flow: /request -> /transfer -> /records/patient/{patient_id}."""
    now = datetime.now(timezone.utc)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        # 1. Initiate HIU Request
        init_req = {
            "consentId": f"consent-{uuid.uuid4()}",
            "patientId": "sneha.sharma@abdm",
            "dateRangeFrom": (now - timedelta(days=30)).isoformat(),
            "dateRangeTo": now.isoformat(),
            "hiTypes": ["OPConsultation", "Prescription"],
        }
        res_init = await client.post("/api/v1/abdm/m3/hiu/request", json=init_req)
        assert res_init.status_code == 202
        init_data = res_init.json()
        assert init_data["status"] == "INITIATED"
        tx_id = init_data["transactionId"]
        hiu_pub_b64 = init_data["keyMaterial"]["publicKey"]
        hiu_nonce_b64 = init_data["keyMaterial"]["nonce"]

        # 2. Simulate Peer HIP encrypting bundle
        _, hip_pub_b64, hip_priv_b64 = AbdmCryptoService.generate_key_pair()
        hip_nonce_bytes, hip_nonce_b64 = AbdmCryptoService.generate_nonce()
        hiu_pub = AbdmCryptoService.parse_public_key(hiu_pub_b64)
        hip_priv = AbdmCryptoService.parse_private_key(hip_priv_b64)
        hiu_nonce_bytes = AbdmCryptoService.parse_nonce(hiu_nonce_b64)

        _, salt, iv = AbdmCryptoService.compute_xor_entropy(hip_nonce_bytes, hiu_nonce_bytes)
        shared_secret = AbdmCryptoService.derive_shared_secret(hip_priv, hiu_pub)
        derived_key = AbdmCryptoService.derive_symmetric_key(shared_secret, salt)

        sample_bundle = AbdmTransferService.generate_clinical_bundle_json(
            care_context_ref="ENC-API-TEST-01",
            hi_type="Prescription",
            patient_id="sneha.sharma@abdm",
        )
        b64_cipher, checksum = AbdmTransferService.encrypt_payload(sample_bundle, derived_key, iv)

        transfer_payload = {
            "pageNumber": 1,
            "pageCount": 1,
            "transactionId": tx_id,
            "entries": [
                {
                    "content": b64_cipher,
                    "media": "application/fhir+json",
                    "checksum": checksum,
                    "careContextReference": "ENC-API-TEST-01",
                }
            ],
            "keyMaterial": {
                "cryptoAlg": "ECDH",
                "curve": "Curve25519",
                "userInfo": {
                    "publicKey": hip_pub_b64,
                    "nonce": hip_nonce_b64,
                },
            },
        }

        # 3. Post to HIU transfer receiver
        res_transfer = await client.post("/api/v1/abdm/m3/hiu/transfer", json=transfer_payload)
        assert res_transfer.status_code == 200
        transfer_data = res_transfer.json()
        assert transfer_data["status"] == "PROCESSED"
        assert transfer_data["bundlesImported"] == 1
        assert transfer_data["totalPrescriptions"] >= 1

        # 4. Query patient records
        res_records = await client.get("/api/v1/abdm/m3/hiu/records/patient/sneha.sharma@abdm")
        assert res_records.status_code == 200
        records_data = res_records.json()
        assert records_data["patientId"] == "sneha.sharma@abdm"
        assert records_data["totalBundles"] >= 1
        assert len(records_data["prescriptions"]) >= 1

        # 5. List sessions
        res_sessions = await client.get("/api/v1/abdm/m3/hiu/sessions")
        assert res_sessions.status_code == 200
        assert len(res_sessions.json()) >= 1
