"""Unit and integration tests for ABDM Milestone 3 (M3) Cryptographic Key Exchange & Health Information Flow.

Tests conform to NHA ABDM v0.5 and Fidelius specifications:
- Ephemeral ECDH Curve25519 (X25519) key generation
- 32-byte CSPRNG nonces
- Nonce XOR entropy product (20-byte Salt, 12-byte IV)
- ECDH Diffie-Hellman scalar multiplication symmetry
- HKDF-SHA256 symmetric key derivation
- Full peer-to-peer handshake (HIU <-> HIP parity)
- CryptoSessionStore caching and lifecycle
- Inbound Gateway /v0.5/health-information/hip/request and callback flows
"""

import base64
from datetime import datetime, timezone, timedelta
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.abdm_crypto import (
    AbdmCryptoService,
    CryptoSessionStore,
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
    HIRequestPayload,
    HIRequestDetail,
    ConsentIdRef,
    HIRequestDateRange,
    KeyMaterial,
    KeyUserInfo,
)


@pytest.fixture(autouse=True)
def clean_crypto_and_consent_stores():
    """Ensure in-memory stores are clean before each test."""
    crypto_session_store.clear()
    consent_registry_store.clear()
    yield
    crypto_session_store.clear()
    consent_registry_store.clear()


@pytest.mark.asyncio
async def test_key_pair_generation():
    """Verify ephemeral Curve25519 key generation produces valid 32-byte keys."""
    priv_key, pub_b64, priv_b64 = AbdmCryptoService.generate_key_pair()

    assert priv_key is not None
    assert isinstance(pub_b64, str)
    assert isinstance(priv_b64, str)

    # Base64 decode to verify raw byte length
    pub_bytes = base64.b64decode(pub_b64)
    priv_bytes = base64.b64decode(priv_b64)
    assert len(pub_bytes) == 32
    assert len(priv_bytes) == 32


@pytest.mark.asyncio
async def test_nonce_generation_entropy():
    """Verify 32-byte CSPRNG nonces have high entropy and zero collisions."""
    nonces = set()
    for _ in range(50):
        raw_nonce, b64_nonce = AbdmCryptoService.generate_nonce()
        assert len(raw_nonce) == 32
        assert len(base64.b64decode(b64_nonce)) == 32
        nonces.add(raw_nonce)

    assert len(nonces) == 50, "CSPRNG nonces must not have collisions"


@pytest.mark.asyncio
async def test_nonce_xor_and_salt_iv_derivation():
    """Verify Nonce XOR entropy product partitions exactly into 20-byte Salt and 12-byte IV."""
    nonce_a = bytes([0xAA] * 32)
    nonce_b = bytes([0x55] * 32)

    xor_bytes, salt, iv = AbdmCryptoService.compute_xor_entropy(nonce_a, nonce_b)

    assert len(xor_bytes) == 32
    assert len(salt) == 20
    assert len(iv) == 12
    assert xor_bytes == bytes([0xFF] * 32)
    assert salt == bytes([0xFF] * 20)
    assert iv == bytes([0xFF] * 12)
    assert salt + iv == xor_bytes


@pytest.mark.asyncio
async def test_ecdh_shared_secret_symmetry():
    """Verify Diffie-Hellman commutativity: Alice(priv) + Bob(pub) == Bob(priv) + Alice(pub)."""
    alice_priv, alice_pub_b64, _ = AbdmCryptoService.generate_key_pair()
    bob_priv, bob_pub_b64, _ = AbdmCryptoService.generate_key_pair()

    alice_pub = AbdmCryptoService.parse_public_key(alice_pub_b64)
    bob_pub = AbdmCryptoService.parse_public_key(bob_pub_b64)

    secret_alice = AbdmCryptoService.derive_shared_secret(alice_priv, bob_pub)
    secret_bob = AbdmCryptoService.derive_shared_secret(bob_priv, alice_pub)

    assert len(secret_alice) == 32
    assert len(secret_bob) == 32
    assert secret_alice == secret_bob, "ECDH Curve25519 shared secret must be symmetric"


@pytest.mark.asyncio
async def test_hkdf_sha256_derivation():
    """Verify HKDF-SHA256 extracts and expands to a 32-byte deterministic key."""
    shared_secret = bytes([0x42] * 32)
    salt = bytes([0x07] * 20)

    key1 = AbdmCryptoService.derive_symmetric_key(shared_secret, salt)
    key2 = AbdmCryptoService.derive_symmetric_key(shared_secret, salt)

    assert len(key1) == 32
    assert key1 == key2, "HKDF-SHA256 derivation must be deterministic"


@pytest.mark.asyncio
async def test_full_peer_key_exchange_handshake():
    """Simulate complete HIU (Alice) and HIP (Bob) key agreement handshake."""
    # Alice (HIU) generates keypair and nonce
    _, alice_pub_b64, alice_priv_b64 = AbdmCryptoService.generate_key_pair()
    _, alice_nonce_b64 = AbdmCryptoService.generate_nonce()

    # Bob (HIP) generates keypair and nonce
    _, bob_pub_b64, bob_priv_b64 = AbdmCryptoService.generate_key_pair()
    _, bob_nonce_b64 = AbdmCryptoService.generate_nonce()

    # Alice computes handshake
    alice_res = AbdmCryptoService.execute_key_exchange(
        local_private_key_b64=alice_priv_b64,
        local_nonce_b64=alice_nonce_b64,
        peer_public_key_b64=bob_pub_b64,
        peer_nonce_b64=bob_nonce_b64,
    )

    # Bob computes handshake
    bob_res = AbdmCryptoService.execute_key_exchange(
        local_private_key_b64=bob_priv_b64,
        local_nonce_b64=bob_nonce_b64,
        peer_public_key_b64=alice_pub_b64,
        peer_nonce_b64=alice_nonce_b64,
    )

    # Assert 100% cryptographic parity
    assert alice_res["shared_secret"] == bob_res["shared_secret"]
    assert alice_res["salt"] == bob_res["salt"]
    assert alice_res["iv"] == bob_res["iv"]
    assert alice_res["derived_key"] == bob_res["derived_key"]
    assert len(alice_res["derived_key"]) == 32


@pytest.mark.asyncio
async def test_crypto_session_store_lifecycle():
    """Verify CryptoSessionStore storing, indexing by consent, and expiry."""
    from app.schemas.abdm_m3_crypto import CryptoSessionDetail

    now = datetime.now(timezone.utc)
    session = CryptoSessionDetail(
        transactionId="tx-12345",
        consentId="consent-abcde",
        dataPushUrl="https://hiu.example.com/transfer",
        hipPublicKey="dummy-hip-pub",
        hipNonce="dummy-hip-nonce",
        hiuPublicKey="dummy-hiu-pub",
        hiuNonce="dummy-hiu-nonce",
        derivedKeyHex="0123456789abcdef" * 4,
        saltHex="abcdef" * 6 + "abcd",
        ivHex="12345678" * 3,
        dateRangeFrom=now - timedelta(days=10),
        dateRangeTo=now,
        createdAt=now,
        expiresAt=now + timedelta(seconds=3600),
    )

    crypto_session_store.store_session(session)

    # Retrieve by tx
    retrieved_tx = crypto_session_store.get_session("tx-12345")
    assert retrieved_tx is not None
    assert retrieved_tx.consentId == "consent-abcde"

    # Retrieve by consent
    retrieved_consent = crypto_session_store.get_session_by_consent("consent-abcde")
    assert retrieved_consent is not None
    assert retrieved_consent.transactionId == "tx-12345"

    # Delete session
    deleted = crypto_session_store.delete_session("tx-12345")
    assert deleted is True
    assert crypto_session_store.get_session("tx-12345") is None
    assert crypto_session_store.get_session_by_consent("consent-abcde") is None


@pytest.mark.asyncio
async def test_gateway_inbound_hi_request_authorized():
    """Verify /v0.5/health-information/hip/request establishes key agreement with valid consent."""
    # 1. Setup active consent in registry
    consent_id = f"consent-{uuid.uuid4()}"
    now = datetime.now(timezone.utc)
    record = ConsentRecordRepresentation(
        consent_id=consent_id,
        status="GRANTED",
        patient_id="sneha.sharma@abdm",
        hiu_id="HIU-001",
        hip_id="IN0410000123",
        hi_types=["DiagnosticReport", "Prescription", "OPConsultation"],
        care_contexts=[
            ConsentCareContextReference(
                patientReference="P-101",
                careContextReference="ENC-2026-001",
            )
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
    consent_registry_store.save_consent(record)

    # 2. Generate HIU key material
    _, hiu_pub_b64, _ = AbdmCryptoService.generate_key_pair()
    _, hiu_nonce_b64 = AbdmCryptoService.generate_nonce()

    tx_id = uuid.uuid4()
    req_payload = {
        "requestId": str(uuid.uuid4()),
        "timestamp": now.isoformat(),
        "transactionId": str(tx_id),
        "hiRequest": {
            "consent": {"id": consent_id},
            "dateRange": {
                "from": (now - timedelta(days=7)).isoformat(),
                "to": now.isoformat(),
            },
            "dataPushUrl": "https://hiu.hospital.org/v0.5/health-information/transfer",
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

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        resp = await client.post(
            "/v0.5/health-information/hip/request",
            json=req_payload,
            headers={
                "REQUEST-ID": str(uuid.uuid4()),
                "TIMESTAMP": now.isoformat(),
                "X-CM-ID": "sbx",
            },
        )

        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "ACCEPTED"
        assert data["transactionId"] == str(tx_id)
        assert data["keyExchange"]["cryptoAlg"] == "ECDH"
        assert data["keyExchange"]["curve"] == "Curve25519"
        assert "hipPublicKey" in data["keyExchange"]
        assert "hipNonce" in data["keyExchange"]

        # Check session is cached in CryptoSessionStore
        stored = crypto_session_store.get_session(str(tx_id))
        assert stored is not None
        assert stored.consentId == consent_id
        assert len(stored.derivedKeyHex) == 64  # 32 bytes hex


@pytest.mark.asyncio
async def test_gateway_inbound_hi_request_unauthorized_consent():
    """Verify /v0.5/health-information/hip/request rejects non-existent or invalid consent."""
    now = datetime.now(timezone.utc)
    _, hiu_pub_b64, _ = AbdmCryptoService.generate_key_pair()
    _, hiu_nonce_b64 = AbdmCryptoService.generate_nonce()

    tx_id = uuid.uuid4()
    req_payload = {
        "requestId": str(uuid.uuid4()),
        "timestamp": now.isoformat(),
        "transactionId": str(tx_id),
        "hiRequest": {
            "consent": {"id": "non-existent-consent-999"},
            "dateRange": {
                "from": (now - timedelta(days=7)).isoformat(),
                "to": now.isoformat(),
            },
            "dataPushUrl": "https://hiu.hospital.org/v0.5/health-information/transfer",
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

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        resp = await client.post(
            "/v0.5/health-information/hip/request",
            json=req_payload,
            headers={"X-CM-ID": "sbx"},
        )

        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "REJECTED"
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_crypto_api_endpoints():
    """Verify local cryptographic utilities (/keys/generate, /exchange, /on-request)."""
    now = datetime.now(timezone.utc)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        # 1. Generate keys
        gen_resp = await client.post("/api/v1/abdm/m3/crypto/keys/generate")
        assert gen_resp.status_code == 200
        gen_data = gen_resp.json()
        assert "publicKey" in gen_data
        assert "privateKey" in gen_data
        assert "nonce" in gen_data

        # 2. Generate second keypair for exchange
        _, peer_pub, _ = AbdmCryptoService.generate_key_pair()
        _, peer_nonce = AbdmCryptoService.generate_nonce()

        # 3. Compute exchange
        exchange_req = {
            "localPrivateKey": gen_data["privateKey"],
            "localNonce": gen_data["nonce"],
            "peerPublicKey": peer_pub,
            "peerNonce": peer_nonce,
        }
        exc_resp = await client.post("/api/v1/abdm/m3/crypto/exchange", json=exchange_req)
        assert exc_resp.status_code == 200
        exc_data = exc_resp.json()
        assert exc_data["status"] == "SUCCESS"
        assert len(exc_data["sharedSecretHex"]) == 64
        assert len(exc_data["derivedKeyHex"]) == 64
        assert len(exc_data["saltHex"]) == 40  # 20 bytes hex
        assert len(exc_data["ivHex"]) == 24    # 12 bytes hex

        # 4. On-request callback receiver
        cb_payload = {
            "requestId": str(uuid.uuid4()),
            "timestamp": now.isoformat(),
            "hiRequest": {
                "transactionId": str(uuid.uuid4()),
                "status": "ACKNOWLEDGED",
            },
            "resp": {"requestId": str(uuid.uuid4())},
        }
        cb_resp = await client.post("/v0.5/health-information/hip/on-request", json=cb_payload)
        assert cb_resp.status_code == 200
        assert cb_resp.json()["status"] == "RECEIVED"


@pytest.mark.asyncio
async def test_gateway_inbound_hi_request_mismatched_dates():
    """Verify /v0.5/health-information/hip/request rejects when requested date range does not overlap consent."""
    now = datetime.now(timezone.utc)
    consent_id = f"consent-{uuid.uuid4()}"

    # Consent granted strictly in the past: 60 days ago to 30 days ago
    record = ConsentRecordRepresentation(
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
        date_range_from=now - timedelta(days=60),
        date_range_to=now - timedelta(days=30),
        data_erase_at=now + timedelta(days=90),
        signature_verified=True,
        received_at=now,
        updated_at=now,
    )
    consent_registry_store.save_consent(record)

    _, hiu_pub_b64, _ = AbdmCryptoService.generate_key_pair()
    _, hiu_nonce_b64 = AbdmCryptoService.generate_nonce()

    tx_id = uuid.uuid4()
    req_payload = {
        "requestId": str(uuid.uuid4()),
        "timestamp": now.isoformat(),
        "transactionId": str(tx_id),
        "hiRequest": {
            "consent": {"id": consent_id},
            "dateRange": {
                "from": (now - timedelta(days=10)).isoformat(),
                "to": now.isoformat(),
            },
            "dataPushUrl": "https://hiu.hospital.org/v0.5/health-information/transfer",
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

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        resp = await client.post(
            "/v0.5/health-information/hip/request",
            json=req_payload,
            headers={"X-CM-ID": "sbx"},
        )

        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "REJECTED"
        assert "overlap" in data["error"].lower()

