"""ABDM Milestone 3 (M3) Integration Audit & Week 11 Certification Test Suite.

Comprehensive end-to-end audit verifying full-loop interoperability between
NIRMAYA's Health Information Provider (HIP) and Health Information User (HIU) nodes
in strict accordance with NHA ABDM v0.5 and Fidelius Cryptographic Specifications:

1. Scenario 1 (Full-Loop Consent-to-Decryption):
   Patient Consent Grant -> HIU Request Initiation -> HIP Diffie-Hellman Key Exchange ->
   AES-256-GCM Encrypted FHIR Document Push -> HIU Authenticated Decryption ->
   Longitudinal Clinical History Aggregation & Rendering.

2. Scenario 2 (Granular Category Access Control):
   Enforces strict whitelisting of consented HI types (e.g., DiagnosticReport authorized,
   unauthorized Prescription and OPConsultation rejected).

3. Scenario 3 (Temporal Date Window Enforcement):
   Verifies clinical encounters outside authorized dateRange window are rejected.

4. Scenario 4 (Mid-Transit Revocation Defense):
   Verifies that revoking consent terminates in-flight data transfers and key agreements.

5. Scenario 5 (Zero-Trust Cryptographic Tamper Defense):
   Verifies that modified ciphertext bytes or forged checksums are rejected before
   reaching patient records, incrementing tamper rejection telemetry.

6. Scenario 6 (System Diagnostic Audit Engine Verification):
   Verifies GET /api/v1/abdm/m3/audit compiles live NHA v0.5 M3 certification metrics,
   100% cryptographic parity, and active webhook listener routes.
"""

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.abdm_m3_consent import (
    ConsentCareContextReference,
    ConsentRecordRepresentation,
)
from app.schemas.abdm_m3_crypto import (
    CryptoSessionDetail,
    KeyMaterial,
    KeyUserInfo,
)
from app.schemas.abdm_m3_hiu import (
    HIUDataRequestInitiate,
    HIURequestSession,
)
from app.schemas.abdm_m3_transfer import (
    DataTransferPushPayload,
    EncryptedDataEntry,
)
from app.services.abdm_consent import (
    consent_registry_store,
)
from app.services.abdm_crypto import (
    AbdmCryptoService,
    crypto_session_store,
)
from app.services.abdm_hiu import (
    AbdmHIUService,
    hiu_record_store,
    hiu_request_store,
)
from app.services.abdm_m3_audit import generate_m3_audit_report
from app.services.abdm_transfer import (
    AbdmTransferService,
    transfer_audit_store,
)
from app.core.exceptions import ValidationException


@pytest.fixture(autouse=True)
def clean_audit_environment():
    """Reset all in-memory ABDM stores before and after each audit scenario."""
    consent_registry_store.clear()
    crypto_session_store.clear()
    transfer_audit_store.clear()
    hiu_request_store.clear()
    hiu_record_store.clear()
    yield
    consent_registry_store.clear()
    crypto_session_store.clear()
    transfer_audit_store.clear()
    hiu_request_store.clear()
    hiu_record_store.clear()


# ============================================================================
# Scenario 1: Full-Loop Consent-to-Decryption Lifecycle
# ============================================================================

@pytest.mark.asyncio
async def test_scenario_1_full_loop_consent_to_decryption():
    """Scenario 1: Complete M3 data loop from Consent Grant -> HIU Request -> HIP Key Exchange ->
    AES-256-GCM Transfer -> HIU Decryption -> Longitudinal Record Access.
    """
    now = datetime.now(timezone.utc)
    patient_id = "ananya.sharma@sbx"
    consent_id = f"consent-{uuid.uuid4()}"
    care_context_1 = "CC-VISIT-2026-001"
    care_context_2 = "CC-VISIT-2026-002"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        # Step A: Ingest Approved Consent Artefact into HIP Registry
        consent_record = ConsentRecordRepresentation(
            consent_id=consent_id,
            status="GRANTED",
            patient_id=patient_id,
            hip_id="IN0410000123",
            hiu_id="IN0410000123",
            care_contexts=[
                ConsentCareContextReference(
                    patientReference=patient_id,
                    careContextReference=care_context_1,
                ),
                ConsentCareContextReference(
                    patientReference=patient_id,
                    careContextReference=care_context_2,
                ),
            ],
            hi_types=["OPConsultation", "Prescription", "DiagnosticReport"],
            purpose_code="CAREMGT",
            access_mode="VIEW",
            date_range_from=now - timedelta(days=90),
            date_range_to=now + timedelta(days=1),
            data_erase_at=now + timedelta(days=365),
            signature_verified=True,
            received_at=now,
            updated_at=now,
        )
        consent_registry_store.save_consent(consent_record)
        assert consent_registry_store.get_consent(consent_id) is not None

        # Step B: HIU Node initiates health information request
        hiu_req = {
            "consentId": consent_id,
            "patientId": patient_id,
            "dateRangeFrom": (now - timedelta(days=60)).isoformat(),
            "dateRangeTo": now.isoformat(),
            "hiTypes": ["OPConsultation", "Prescription"],
        }
        res_hiu = await client.post("/api/v1/abdm/m3/hiu/request", json=hiu_req)
        assert res_hiu.status_code == 202
        hiu_init = res_hiu.json()
        assert hiu_init["status"] == "INITIATED"
        tx_id = hiu_init["transactionId"]
        hiu_pub_b64 = hiu_init["keyMaterial"]["publicKey"]
        hiu_nonce_b64 = hiu_init["keyMaterial"]["nonce"]

        # Step C: HIP Node establishes Diffie-Hellman Key Agreement via /v0.5 Gateway endpoint
        hip_req_payload = {
            "requestId": str(uuid.uuid4()),
            "timestamp": now.isoformat(),
            "transactionId": tx_id,
            "hiRequest": {
                "consent": {"id": consent_id},
                "dateRange": {
                    "from": (now - timedelta(days=60)).isoformat(),
                    "to": now.isoformat(),
                },
                "dataPushUrl": "/api/v1/abdm/m3/hiu/transfer",
                "keyMaterial": {
                    "cryptoAlg": "ECDH",
                    "curve": "Curve25519",
                    "userInfo": {
                        "publicKey": hiu_pub_b64,
                        "nonce": hiu_nonce_b64,
                    },
                },
            },
        }
        res_hip = await client.post(
            "/v0.5/health-information/hip/request",
            json=hip_req_payload,
            headers={
                "REQUEST-ID": str(uuid.uuid4()),
                "TIMESTAMP": now.isoformat(),
                "X-CM-ID": "sbx",
            },
        )
        assert res_hip.status_code == 202
        hip_data = res_hip.json()
        assert hip_data["status"] == "ACCEPTED"
        hip_pub_b64 = hip_data["keyExchange"]["hipPublicKey"]
        hip_nonce_b64 = hip_data["keyExchange"]["hipNonce"]

        # Step D: HIP packages and encrypts clinical FHIR bundles
        push_payload = AbdmTransferService.build_transfer_push_payload(tx_id)
        assert push_payload.transactionId == uuid.UUID(tx_id)
        assert len(push_payload.entries) == 2
        assert push_payload.keyMaterial.userInfo.publicKey == hip_pub_b64
        assert push_payload.keyMaterial.userInfo.nonce == hip_nonce_b64

        # Execute data transfer pipeline (records in audit store and emits status notification)
        transfer_res = AbdmTransferService.execute_data_transfer(tx_id)
        assert transfer_res.status == "SUCCESS"
        assert transfer_res.entriesCount == 2

        # Step E: Ingest encrypted payload at HIU receiver
        res_transfer = await client.post(
            "/api/v1/abdm/m3/hiu/transfer",
            json=push_payload.model_dump(mode="json", by_alias=True),
        )
        assert res_transfer.status_code == 200
        transfer_resp = res_transfer.json()
        assert transfer_resp["status"] == "PROCESSED"
        assert transfer_resp["bundlesImported"] == 2

        # Step F: Query HIU longitudinal records for the patient
        res_records = await client.get(f"/api/v1/abdm/m3/hiu/records/patient/{patient_id}")
        assert res_records.status_code == 200
        records_resp = res_records.json()
        assert records_resp["patientId"] == patient_id
        assert records_resp["totalBundles"] == 2
        assert len(records_resp["encounters"]) >= 1
        assert records_resp["encounters"][0]["careContextReference"] in [care_context_1, care_context_2]


# ============================================================================
# Scenario 2: Granular Category Access Control
# ============================================================================

@pytest.mark.asyncio
async def test_scenario_2_granular_category_access_control():
    """Scenario 2: Consent restricts access strictly to DiagnosticReport.
    Verify Prescription and OPConsultation are denied, while DiagnosticReport is authorized.
    """
    now = datetime.now(timezone.utc)
    patient_id = "vikram.rathore@sbx"
    consent_id = f"consent-{uuid.uuid4()}"
    care_context = "CC-LAB-2026-99"

    consent_record = ConsentRecordRepresentation(
        consent_id=consent_id,
        status="GRANTED",
        patient_id=patient_id,
        hip_id="IN0410000123",
        hiu_id="HIU-APOLLO-001",
        care_contexts=[
            ConsentCareContextReference(
                patientReference=patient_id,
                careContextReference=care_context,
            )
        ],
        hi_types=["DiagnosticReport"],  # Strict single-category grant
        purpose_code="CAREMGT",
        access_mode="VIEW",
        date_range_from=now - timedelta(days=30),
        date_range_to=now + timedelta(days=1),
        data_erase_at=now + timedelta(days=180),
        signature_verified=True,
        received_at=now,
        updated_at=now,
    )
    consent_registry_store.save_consent(consent_record)

    # 1. Authorized DiagnosticReport check
    auth_ok, msg_ok = consent_registry_store.validate_record_authorization(
        consent_id=consent_id,
        hi_type="DiagnosticReport",
        care_context_id=care_context,
        record_timestamp=now - timedelta(days=5),
    )
    assert auth_ok is True
    assert msg_ok == "Authorized"

    # 2. Unauthorized Prescription check
    auth_rx, msg_rx = consent_registry_store.validate_record_authorization(
        consent_id=consent_id,
        hi_type="Prescription",
        care_context_id=care_context,
        record_timestamp=now - timedelta(days=5),
    )
    assert auth_rx is False
    assert "not permitted under consent" in msg_rx

    # 3. Unauthorized OPConsultation check
    auth_op, msg_op = consent_registry_store.validate_record_authorization(
        consent_id=consent_id,
        hi_type="OPConsultation",
        care_context_id=care_context,
        record_timestamp=now - timedelta(days=5),
    )
    assert auth_op is False
    assert "not permitted under consent" in msg_op


# ============================================================================
# Scenario 3: Temporal Date Window Enforcement
# ============================================================================

@pytest.mark.asyncio
async def test_scenario_3_temporal_date_window_enforcement():
    """Scenario 3: Clinical records outside permitted dateRange are strictly rejected."""
    now = datetime.now(timezone.utc)
    patient_id = "rajesh.patel@sbx"
    consent_id = f"consent-{uuid.uuid4()}"
    care_context = "CC-ORTHO-100"

    # Permitted window: Exactly past 30 days up to today
    window_start = now - timedelta(days=30)
    window_end = now

    consent_record = ConsentRecordRepresentation(
        consent_id=consent_id,
        status="GRANTED",
        patient_id=patient_id,
        hip_id="IN0410000123",
        hiu_id="HIU-APOLLO-001",
        care_contexts=[
            ConsentCareContextReference(
                patientReference=patient_id,
                careContextReference=care_context,
            )
        ],
        hi_types=["OPConsultation"],
        purpose_code="CAREMGT",
        access_mode="VIEW",
        date_range_from=window_start,
        date_range_to=window_end,
        data_erase_at=now + timedelta(days=90),
        signature_verified=True,
        received_at=now,
        updated_at=now,
    )
    consent_registry_store.save_consent(consent_record)

    # 1. Record inside window -> Authorized
    ok_ts = now - timedelta(days=15)
    auth_ok, _ = consent_registry_store.validate_record_authorization(
        consent_id=consent_id,
        hi_type="OPConsultation",
        care_context_id=care_context,
        record_timestamp=ok_ts,
    )
    assert auth_ok is True

    # 2. Record 60 days ago (prior to window_start) -> Rejected
    past_ts = now - timedelta(days=60)
    auth_past, msg_past = consent_registry_store.validate_record_authorization(
        consent_id=consent_id,
        hi_type="OPConsultation",
        care_context_id=care_context,
        record_timestamp=past_ts,
    )
    assert auth_past is False
    assert "falls outside permitted window" in msg_past

    # 3. Record in future (after window_end) -> Rejected
    future_ts = now + timedelta(days=5)
    auth_future, msg_future = consent_registry_store.validate_record_authorization(
        consent_id=consent_id,
        hi_type="OPConsultation",
        care_context_id=care_context,
        record_timestamp=future_ts,
    )
    assert auth_future is False
    assert "falls outside permitted window" in msg_future


# ============================================================================
# Scenario 4: Mid-Transit Revocation Defense
# ============================================================================

@pytest.mark.asyncio
async def test_scenario_4_mid_transit_revocation_defense():
    """Scenario 4: When a patient revokes consent mid-transit, in-flight transfers are aborted."""
    now = datetime.now(timezone.utc)
    patient_id = "priya.nair@sbx"
    consent_id = f"consent-{uuid.uuid4()}"
    care_context = "CC-CARDIO-401"
    tx_id = str(uuid.uuid4())

    # 1. Establish initial GRANTED consent
    consent_record = ConsentRecordRepresentation(
        consent_id=consent_id,
        status="GRANTED",
        patient_id=patient_id,
        hip_id="IN0410000123",
        hiu_id="HIU-APOLLO-001",
        care_contexts=[
            ConsentCareContextReference(
                patientReference=patient_id,
                careContextReference=care_context,
            )
        ],
        hi_types=["OPConsultation"],
        purpose_code="CAREMGT",
        access_mode="VIEW",
        date_range_from=now - timedelta(days=30),
        date_range_to=now + timedelta(days=1),
        data_erase_at=now + timedelta(days=90),
        signature_verified=True,
        received_at=now,
        updated_at=now,
    )
    consent_registry_store.save_consent(consent_record)

    # 2. Setup crypto session
    derived_key = bytes([0x5A] * 32)
    iv = bytes([0x3C] * 12)
    session = CryptoSessionDetail(
        transactionId=tx_id,
        consentId=consent_id,
        dataPushUrl="/api/v1/abdm/m3/hiu/transfer",
        hipPublicKey="pub-key",
        hipNonce="nonce",
        hiuPublicKey="hiu-pub",
        hiuNonce="hiu-nonce",
        derivedKeyHex=derived_key.hex(),
        saltHex=bytes([0x12] * 20).hex(),
        ivHex=iv.hex(),
        dateRangeFrom=now - timedelta(days=30),
        dateRangeTo=now,
        createdAt=now,
        expiresAt=now + timedelta(seconds=3600),
    )
    crypto_session_store.store_session(session)

    # 3. Patient revokes consent
    revoked = consent_registry_store.revoke_consent(consent_id)
    assert revoked is not None
    assert revoked.status == "REVOKED"

    # 4. Verify record authorization fails
    auth_rev, msg_rev = consent_registry_store.validate_record_authorization(
        consent_id=consent_id,
        hi_type="OPConsultation",
        care_context_id=care_context,
        record_timestamp=now - timedelta(days=5),
    )
    assert auth_rev is False
    assert "status is 'REVOKED'" in msg_rev

    # 5. Verify transfer packaging aborts with ValidationException
    with pytest.raises(ValidationException) as exc_info:
        AbdmTransferService.build_transfer_push_payload(tx_id)
    assert "is in status 'REVOKED', not GRANTED" in str(exc_info.value.message)


# ============================================================================
# Scenario 5: Zero-Trust Cryptographic Tamper Defense
# ============================================================================

@pytest.mark.asyncio
async def test_scenario_5_zero_trust_cryptographic_tamper_defense():
    """Scenario 5: Altered ciphertext bytes or forged checksums are rejected before
    ingestion, incrementing the tamper rejection telemetry.
    """
    now = datetime.now(timezone.utc)
    patient_id = "kavita.deshmukh@sbx"
    tx_id = str(uuid.uuid4())
    consent_id = f"consent-{uuid.uuid4()}"

    # Setup HIU session
    _, hiu_pub_b64, hiu_priv_b64 = AbdmCryptoService.generate_key_pair()
    _, hiu_nonce_b64 = AbdmCryptoService.generate_nonce()
    session = HIURequestSession(
        transactionId=tx_id,
        consentId=consent_id,
        patientId=patient_id,
        hiuPrivateKey=hiu_priv_b64,
        hiuPublicKey=hiu_pub_b64,
        hiuNonce=hiu_nonce_b64,
        status="REQUESTED",
        dateRangeFrom=now - timedelta(days=30),
        dateRangeTo=now,
        createdAt=now,
        expiresAt=now + timedelta(seconds=3600),
    )
    hiu_request_store.store_session(session)

    # Setup HIP keys & encryption
    _, hip_pub_b64, hip_priv_b64 = AbdmCryptoService.generate_key_pair()
    _, hip_nonce_b64 = AbdmCryptoService.generate_nonce()

    hiu_priv = AbdmCryptoService.parse_private_key(hiu_priv_b64)
    hiu_pub = AbdmCryptoService.parse_public_key(hiu_pub_b64)
    hip_priv = AbdmCryptoService.parse_private_key(hip_priv_b64)
    hiu_nonce_bytes = AbdmCryptoService.parse_nonce(hiu_nonce_b64)
    hip_nonce_bytes = AbdmCryptoService.parse_nonce(hip_nonce_b64)

    _, salt, iv = AbdmCryptoService.compute_xor_entropy(hip_nonce_bytes, hiu_nonce_bytes)
    shared_secret = AbdmCryptoService.derive_shared_secret(hip_priv, hiu_pub)
    derived_key = AbdmCryptoService.derive_symmetric_key(shared_secret, salt)

    sample_bundle = AbdmTransferService.generate_clinical_bundle_json(
        care_context_ref="CC-TAMPER-01",
        hi_type="OPConsultation",
        patient_id=patient_id,
    )
    b64_cipher, correct_checksum = AbdmTransferService.encrypt_payload(sample_bundle, derived_key, iv)

    # Initial tamper rejections count
    initial_rejections = hiu_record_store.tamper_rejections
    assert initial_rejections == 0

    # Tamper 1: Corrupt Ciphertext bytes (flipping bits in b64 payload)
    raw_cipher = base64.b64decode(b64_cipher)
    tampered_raw = bytearray(raw_cipher)
    tampered_raw[10] ^= 0xFF  # Flip byte 10
    tampered_b64 = base64.b64encode(bytes(tampered_raw)).decode("ascii")

    tampered_payload_1 = DataTransferPushPayload(
        pageNumber=1,
        pageCount=1,
        transactionId=uuid.UUID(tx_id),
        entries=[
            EncryptedDataEntry(
                content=tampered_b64,
                media="application/fhir+json",
                checksum=correct_checksum,
                careContextReference="CC-TAMPER-01",
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

    success_1, msg_1, _ = AbdmHIUService.process_inbound_transfer(tampered_payload_1)
    assert success_1 is False
    assert "decryption failed" in msg_1.lower()
    assert hiu_record_store.tamper_rejections == 1

    # Tamper 2: Valid Ciphertext but Forged Checksum
    forged_checksum = hashlib.sha256(b"malicious_checksum").hexdigest()
    tampered_payload_2 = DataTransferPushPayload(
        pageNumber=1,
        pageCount=1,
        transactionId=uuid.UUID(tx_id),
        entries=[
            EncryptedDataEntry(
                content=b64_cipher,
                media="application/fhir+json",
                checksum=forged_checksum,  # Forged checksum
                careContextReference="CC-TAMPER-01",
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

    success_2, msg_2, _ = AbdmHIUService.process_inbound_transfer(tampered_payload_2)
    assert success_2 is False
    assert "checksum mismatch" in msg_2.lower()
    assert hiu_record_store.tamper_rejections == 2

    # Zero corrupt records should exist in the patient's record store
    patient_records = hiu_record_store.get_patient_records(patient_id)
    assert len(patient_records) == 0


# ============================================================================
# Scenario 6: System Diagnostic Audit Engine Verification
# ============================================================================

@pytest.mark.asyncio
async def test_scenario_6_system_diagnostic_audit_engine():
    """Scenario 6: Verify GET /api/v1/abdm/m3/audit endpoint returns certified telemetry,
    100% cryptographic parity, and registered webhook listeners.
    """
    now = datetime.now(timezone.utc)
    patient_id = "deepak.chopra@sbx"
    consent_id = f"consent-{uuid.uuid4()}"

    # Populate sample operational telemetry
    consent_record = ConsentRecordRepresentation(
        consent_id=consent_id,
        status="GRANTED",
        patient_id=patient_id,
        hip_id="IN0410000123",
        hiu_id="HIU-APOLLO-001",
        care_contexts=[
            ConsentCareContextReference(
                patientReference=patient_id,
                careContextReference="CC-AUDIT-01",
            )
        ],
        hi_types=["OPConsultation"],
        purpose_code="CAREMGT",
        access_mode="VIEW",
        date_range_from=now - timedelta(days=30),
        date_range_to=now + timedelta(days=1),
        data_erase_at=now + timedelta(days=90),
        signature_verified=True,
        received_at=now,
        updated_at=now,
    )
    consent_registry_store.save_consent(consent_record)

    # Direct service call check
    report = generate_m3_audit_report()
    assert report.status == "ABDM_M3_CERTIFIED"
    assert report.hipId == "IN0410000123"
    assert report.gatewayConsentManagerId == "sbx"
    assert report.consents.totalIngested >= 1
    assert report.consents.activeGranted >= 1
    assert report.cryptography.parityScorePercentage == 100.0
    assert report.hiuConsumer.integrityScorePercentage == 100.0

    # API Endpoint call check
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        res = await client.get("/api/v1/abdm/m3/audit")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ABDM_M3_CERTIFIED"
        assert data["milestone"] == "Milestone 3: Health Information Exchange & Consent Management"
        assert data["complianceStandard"] == "NHA ABDM v0.5 Data Flow & Fidelius Cryptographic Specifications"
        assert data["hipId"] == "IN0410000123"
        assert data["version"] == "0.3.0-alpha.w11"

        # Check registered webhook listeners
        listeners = data["activeWebhookListeners"]
        assert "/v0.5/consents/hip/notify" in listeners
        assert "/v0.5/health-information/hip/request" in listeners
        assert "/v0.5/health-information/transfer" in listeners
        assert "/v0.5/health-information/notify" in listeners
        assert "/api/v1/abdm/m3/hiu/transfer" in listeners
        assert "/api/v1/abdm/m3/hiu/request" in listeners
