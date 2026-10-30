"""Unit and integration tests for ABDM Milestone 3 (M3) Encrypted Health Data Transfer Pipeline.

Tests conform to NHA ABDM v0.5 and Fidelius specifications:
- AES-256-GCM authenticated encryption and decryption
- Authentication tag verification and tamper rejection
- Tamper-evident SHA-256 checksum integrity
- HL7 FHIR R4 Document Bundle packaging
- End-to-end data transfer push for authorized session
- Rejection of transfer on expired session or revoked consent
- Gateway transfer receiver (/v0.5/health-information/transfer)
- Gateway status notification (/v0.5/health-information/notify)
- Developer diagnostic encryption/decryption APIs
"""

import base64
from datetime import datetime, timezone, timedelta
import hashlib
import json
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.abdm_transfer import (
    AbdmTransferService,
    transfer_audit_store,
)
from app.services.abdm_crypto import (
    AbdmCryptoService,
    crypto_session_store,
)
from app.services.abdm_consent import (
    consent_registry_store,
)
from app.schemas.abdm_m3_consent import (
    ConsentCareContextReference,
    ConsentRecordRepresentation,
)
from app.schemas.abdm_m3_crypto import (
    CryptoSessionDetail,
)
from app.core.exceptions import ValidationException


@pytest.fixture(autouse=True)
def clean_stores():
    """Reset stores before and after each test."""
    transfer_audit_store.clear()
    crypto_session_store.clear()
    consent_registry_store.clear()
    yield
    transfer_audit_store.clear()
    crypto_session_store.clear()
    consent_registry_store.clear()


@pytest.mark.asyncio
async def test_aes_gcm_encrypt_decrypt_roundtrip():
    """Verify arbitrary plaintext encrypted via AES-256-GCM decrypts cleanly to identical plaintext."""
    key = bytes([0x12] * 32)  # 32-byte key
    iv = bytes([0x34] * 12)   # 12-byte IV
    plaintext = json.dumps({"resourceType": "Bundle", "status": "active", "patient": "P-101"})

    b64_cipher, checksum = AbdmTransferService.encrypt_payload(plaintext, key, iv)

    assert isinstance(b64_cipher, str)
    assert len(b64_cipher) > 0
    assert checksum == hashlib.sha256(plaintext.encode("utf-8")).hexdigest()

    decrypted = AbdmTransferService.decrypt_payload(b64_cipher, key, iv)
    assert decrypted == plaintext


@pytest.mark.asyncio
async def test_aes_gcm_tampered_ciphertext_fails():
    """Verify that tampering with ciphertext triggers authentication tag verification failure."""
    key = bytes([0x42] * 32)
    iv = bytes([0x99] * 12)
    plaintext = "Sensitive Health Record: Hemoglobin 14.2 g/dL"

    b64_cipher, _ = AbdmTransferService.encrypt_payload(plaintext, key, iv)

    # Tamper with raw ciphertext bytes
    raw_cipher = bytearray(base64.b64decode(b64_cipher))
    raw_cipher[10] ^= 0xFF  # Flip bits
    tampered_b64 = base64.b64encode(bytes(raw_cipher)).decode("utf-8")

    with pytest.raises(ValidationException) as exc_info:
        AbdmTransferService.decrypt_payload(tampered_b64, key, iv)

    assert "authentication tag" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_aes_gcm_checksum_integrity():
    """Verify SHA-256 checksum integrity of clinical payload."""
    key = bytes([0xAA] * 32)
    iv = bytes([0x55] * 12)
    payload = "FHIR R4 Diagnostic Report Payload Content"

    _, checksum = AbdmTransferService.encrypt_payload(payload, key, iv)
    expected_digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    assert checksum == expected_digest


@pytest.mark.asyncio
async def test_generate_clinical_bundle_json():
    """Verify clinical bundle builder generates valid FHIR R4 Document Bundle JSON."""
    fhir_json = AbdmTransferService.generate_clinical_bundle_json(
        care_context_ref="ENC-2026-0042",
        hi_type="Prescription",
        patient_id="sneha.sharma@abdm",
    )

    bundle_dict = json.loads(fhir_json)
    assert bundle_dict["resourceType"] == "Bundle"
    assert bundle_dict["type"] == "document"
    assert len(bundle_dict["entry"]) >= 2
    resource_types = [e["resource"]["resourceType"] for e in bundle_dict["entry"]]
    assert "Composition" in resource_types
    assert "Encounter" in resource_types
    assert "MedicationRequest" in resource_types


@pytest.mark.asyncio
async def test_execute_data_transfer_authorized_session():
    """Verify complete data packaging, encryption, and push pipeline for an authorized transaction."""
    now = datetime.now(timezone.utc)
    tx_id = str(uuid.uuid4())
    consent_id = f"consent-{uuid.uuid4()}"

    # 1. Setup active consent
    consent = ConsentRecordRepresentation(
        consent_id=consent_id,
        status="GRANTED",
        patient_id="sneha.sharma@abdm",
        hiu_id="HIU-001",
        hip_id="IN0410000123",
        hi_types=["DiagnosticReport", "OPConsultation"],
        care_contexts=[
            ConsentCareContextReference(
                patientReference="P-101",
                careContextReference="ENC-2026-001",
            ),
            ConsentCareContextReference(
                patientReference="P-101",
                careContextReference="ENC-2026-002",
            ),
        ],
        purpose_code="CAREMGT",
        access_mode="VIEW",
        date_range_from=now - timedelta(days=30),
        date_range_to=now + timedelta(days=1),
        data_erase_at=now + timedelta(days=90),
        signature_verified=True,
        received_at=now,
        updated_at=now,
    )
    consent_registry_store.save_consent(consent)

    # 2. Setup active crypto session
    derived_key = bytes([0x2A] * 32)
    iv = bytes([0x7B] * 12)
    session = CryptoSessionDetail(
        transactionId=tx_id,
        consentId=consent_id,
        dataPushUrl="https://hiu.example.com/v0.5/health-information/transfer",
        hipPublicKey="dummy-hip-pub",
        hipNonce="dummy-hip-nonce",
        hiuPublicKey="dummy-hiu-pub",
        hiuNonce="dummy-hiu-nonce",
        derivedKeyHex=derived_key.hex(),
        saltHex=bytes([0x11] * 20).hex(),
        ivHex=iv.hex(),
        dateRangeFrom=now - timedelta(days=30),
        dateRangeTo=now,
        createdAt=now,
        expiresAt=now + timedelta(seconds=3600),
    )
    crypto_session_store.store_session(session)

    # 3. Execute transfer
    result = AbdmTransferService.execute_data_transfer(tx_id)

    assert result.status == "SUCCESS"
    assert result.transactionId == tx_id
    assert result.consentId == consent_id
    assert result.entriesCount == 2
    assert result.dataPushUrl == "https://hiu.example.com/v0.5/health-information/transfer"

    # 4. Verify audit record
    audit_rec = transfer_audit_store.get_by_transaction_id(tx_id)
    assert audit_rec is not None
    assert audit_rec.entriesCount == 2
    assert audit_rec.direction == "OUTBOUND_PUSH"


@pytest.mark.asyncio
async def test_execute_data_transfer_expired_session():
    """Verify execute_data_transfer rejects transactions with expired crypto sessions."""
    now = datetime.now(timezone.utc)
    tx_id = str(uuid.uuid4())

    # Expired session
    session = CryptoSessionDetail(
        transactionId=tx_id,
        consentId="consent-expired",
        dataPushUrl="https://hiu.example.com/transfer",
        hipPublicKey="pub",
        hipNonce="nonce",
        hiuPublicKey="pub2",
        hiuNonce="nonce2",
        derivedKeyHex=bytes([0x01] * 32).hex(),
        saltHex=bytes([0x02] * 20).hex(),
        ivHex=bytes([0x03] * 12).hex(),
        dateRangeFrom=now - timedelta(days=10),
        dateRangeTo=now,
        createdAt=now - timedelta(seconds=7200),
        expiresAt=now - timedelta(seconds=3600),
    )
    crypto_session_store.store_session(session)

    with pytest.raises(ValidationException) as exc_info:
        AbdmTransferService.execute_data_transfer(tx_id)

    assert "not found or has expired" in exc_info.value.message


@pytest.mark.asyncio
async def test_execute_data_transfer_revoked_consent():
    """Verify execute_data_transfer rejects transactions if consent was revoked."""
    now = datetime.now(timezone.utc)
    tx_id = str(uuid.uuid4())
    consent_id = f"consent-{uuid.uuid4()}"

    consent = ConsentRecordRepresentation(
        consent_id=consent_id,
        status="REVOKED",
        patient_id="sneha.sharma@abdm",
        hiu_id="HIU-001",
        hip_id="IN0410000123",
        hi_types=["OPConsultation"],
        care_contexts=[],
        purpose_code="CAREMGT",
        access_mode="VIEW",
        date_range_from=now - timedelta(days=30),
        date_range_to=now,
        data_erase_at=now + timedelta(days=90),
        signature_verified=True,
        received_at=now,
        updated_at=now,
    )
    consent_registry_store.save_consent(consent)

    session = CryptoSessionDetail(
        transactionId=tx_id,
        consentId=consent_id,
        dataPushUrl="https://hiu.example.com/transfer",
        hipPublicKey="pub",
        hipNonce="nonce",
        hiuPublicKey="pub2",
        hiuNonce="nonce2",
        derivedKeyHex=bytes([0x01] * 32).hex(),
        saltHex=bytes([0x02] * 20).hex(),
        ivHex=bytes([0x03] * 12).hex(),
        dateRangeFrom=now - timedelta(days=10),
        dateRangeTo=now,
        createdAt=now,
        expiresAt=now + timedelta(seconds=3600),
    )
    crypto_session_store.store_session(session)

    with pytest.raises(ValidationException) as exc_info:
        AbdmTransferService.execute_data_transfer(tx_id)

    assert "REVOKED" in exc_info.value.message


@pytest.mark.asyncio
async def test_gateway_transfer_endpoints():
    """Verify /v0.5/health-information/transfer and /notify endpoints."""
    tx_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        # 1. Test Inbound Transfer Receiver
        transfer_payload = {
            "pageNumber": 1,
            "pageCount": 1,
            "transactionId": str(tx_id),
            "entries": [
                {
                    "content": "dGVzdC1jaXBoZXJ0ZXh0",
                    "media": "application/fhir+json",
                    "checksum": "test-checksum-sha256",
                    "careContextReference": "ENC-001",
                }
            ],
            "keyMaterial": {
                "cryptoAlg": "ECDH",
                "curve": "Curve25519",
                "userInfo": {
                    "publicKey": "test-pub-key",
                    "nonce": "test-nonce",
                },
            },
        }
        res1 = await client.post("/v0.5/health-information/transfer", json=transfer_payload)
        assert res1.status_code == 200
        assert res1.json()["status"] == "RECEIVED"
        assert res1.json()["entriesReceived"] == 1

        # 2. Test Inbound Transfer Notify
        notify_payload = {
            "requestId": str(uuid.uuid4()),
            "timestamp": now.isoformat(),
            "notification": {
                "consentId": "consent-test-01",
                "transactionId": str(tx_id),
                "doneAt": now.isoformat(),
                "notifier": {"type": "HIP", "id": "IN0410000123"},
                "statusNotification": {
                    "sessionStatus": "TRANSFERRED",
                    "hipId": "IN0410000123",
                    "statusResponses": [
                        {
                            "careContextReference": "ENC-001",
                            "hiStatus": "OK",
                            "description": "Delivered",
                        }
                    ],
                },
            },
        }
        res2 = await client.post("/v0.5/health-information/notify", json=notify_payload)
        assert res2.status_code == 200
        assert res2.json()["status"] == "ACKNOWLEDGED"


@pytest.mark.asyncio
async def test_api_encrypt_decrypt_and_push_endpoints():
    """Verify /api/v1/abdm/m3/transfer diagnostic utilities and push trigger."""
    now = datetime.now(timezone.utc)
    key_hex = bytes([0x33] * 32).hex()
    iv_hex = bytes([0x66] * 12).hex()
    sample_text = json.dumps({"test": "data", "patient": "Sneha Sharma"})

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        # 1. Direct encrypt
        enc_resp = await client.post(
            "/api/v1/abdm/m3/transfer/encrypt",
            json={"plaintext": sample_text, "keyHex": key_hex, "ivHex": iv_hex},
        )
        assert enc_resp.status_code == 200
        enc_data = enc_resp.json()
        assert enc_data["status"] == "SUCCESS"
        assert "ciphertext" in enc_data
        assert "checksum" in enc_data

        # 2. Direct decrypt
        dec_resp = await client.post(
            "/api/v1/abdm/m3/transfer/decrypt",
            json={"ciphertext": enc_data["ciphertext"], "keyHex": key_hex, "ivHex": iv_hex},
        )
        assert dec_resp.status_code == 200
        dec_data = dec_resp.json()
        assert dec_data["status"] == "SUCCESS"
        assert dec_data["plaintext"] == sample_text

        # 3. Setup session and test push endpoint
        tx_id = str(uuid.uuid4())
        consent_id = f"consent-{uuid.uuid4()}"

        consent = ConsentRecordRepresentation(
            consent_id=consent_id,
            status="GRANTED",
            patient_id="sneha.sharma@abdm",
            hiu_id="HIU-001",
            hip_id="IN0410000123",
            hi_types=["OPConsultation"],
            care_contexts=[
                ConsentCareContextReference(
                    patientReference="P-101",
                    careContextReference="ENC-2026-001",
                )
            ],
            purpose_code="CAREMGT",
            access_mode="VIEW",
            date_range_from=now - timedelta(days=30),
            date_range_to=now,
            data_erase_at=now + timedelta(days=90),
            signature_verified=True,
            received_at=now,
            updated_at=now,
        )
        consent_registry_store.save_consent(consent)

        session = CryptoSessionDetail(
            transactionId=tx_id,
            consentId=consent_id,
            dataPushUrl="https://hiu.example.com/transfer",
            hipPublicKey="pub",
            hipNonce="nonce",
            hiuPublicKey="pub2",
            hiuNonce="nonce2",
            derivedKeyHex=key_hex,
            saltHex=bytes([0x02] * 20).hex(),
            ivHex=iv_hex,
            dateRangeFrom=now - timedelta(days=10),
            dateRangeTo=now,
            createdAt=now,
            expiresAt=now + timedelta(seconds=3600),
        )
        crypto_session_store.store_session(session)

        push_resp = await client.post(
            "/api/v1/abdm/m3/transfer/push",
            json={"transactionId": tx_id},
        )
        assert push_resp.status_code == 200
        push_data = push_resp.json()
        assert push_data["status"] == "SUCCESS"
        assert push_data["entriesCount"] == 1

        # 4. Check history
        hist_resp = await client.get("/api/v1/abdm/m3/transfer/history")
        assert hist_resp.status_code == 200
        records = hist_resp.json()
        assert len(records) >= 1

