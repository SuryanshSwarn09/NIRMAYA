"""Automated test suite for ABDM Gateway Session Client and RSA Demographic Cryptography.

Verifies:
- ABDMRSAEncryptionManager key generation, fingerprinting, and RSA-OAEP SHA-256 roundtrip
- ABDMGatewayClient token acquisition, cache lifecycle, header synthesis, and status reporting
- Endpoints: GET /api/v1/abdm/status, GET /api/v1/abdm/crypto/public-key,
  POST /api/v1/abdm/crypto/encrypt-demographics, POST /api/v1/abdm/crypto/decrypt-demographics,
  and POST /api/v1/abdm/sessions/refresh
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.abdm.client import ABDMGatewayClient
from app.abdm.security.rsa import ABDMRSAEncryptionManager
from app.core.config import settings
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import User


@pytest_asyncio.fixture
async def abdm_test_env():
    """Isolated in-memory SQLite database environment for ABDM testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, session_factory

    app.dependency_overrides.clear()
    await engine.dispose()


def test_rsa_encryption_manager_roundtrip():
    """Verify that ABDMRSAEncryptionManager generates valid keys and performs RSA-OAEP roundtrip."""
    manager = ABDMRSAEncryptionManager()
    assert manager.has_private_key is True

    pub_pem = manager.get_public_key_pem()
    assert "BEGIN PUBLIC KEY" in pub_pem
    assert "END PUBLIC KEY" in pub_pem

    fingerprint = manager.get_public_key_fingerprint()
    assert len(fingerprint) == 64  # SHA-256 hex string

    demographic_data = {
        "name": "Arun Kumar Patel",
        "gender": "M",
        "yearOfBirth": 1988,
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "pincode": "560001",
    }

    # Encrypt
    ciphertext_b64 = manager.encrypt_demographic_payload(demographic_data)
    assert isinstance(ciphertext_b64, str)
    assert len(ciphertext_b64) > 100

    # Decrypt
    decrypted = manager.decrypt_demographic_payload(ciphertext_b64)
    assert decrypted == demographic_data


def test_rsa_encryption_manager_malformed_ciphertext():
    """Verify that invalid ciphertext raises a ValueError."""
    manager = ABDMRSAEncryptionManager()
    with pytest.raises(ValueError):
        manager.decrypt_demographic_payload("not-a-valid-base64-or-ciphertext")


@pytest.mark.asyncio
async def test_abdm_gateway_client_token_lifecycle():
    """Verify ABDMGatewayClient session acquisition, caching, and header synthesis."""
    client = ABDMGatewayClient(
        client_id="SBX_TEST_001",
        client_secret="test_secret_key",
        cm_id="sbx",
    )

    # Initial state: no token cached
    assert client.is_token_valid is False
    assert client.remaining_token_seconds is None

    # Acquire session token
    token1 = await client.get_session_token()
    assert token1 is not None
    assert token1.startswith("sbx_jwt_")
    assert client.is_token_valid is True
    assert client.remaining_token_seconds is not None
    assert client.remaining_token_seconds > 3000

    # Second call should reuse cached token
    token2 = await client.get_session_token(force_refresh=False)
    assert token2 == token1

    # Force refresh should produce a fresh token
    token3 = await client.get_session_token(force_refresh=True)
    assert token3 != token1

    # Header construction
    headers = client.build_gateway_headers(token=token3)
    assert headers["Authorization"] == f"Bearer {token3}"
    assert headers["X-CM-ID"] == "sbx"
    assert "REQUEST-ID" in headers
    assert "TIMESTAMP" in headers
    assert headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_api_abdm_status_and_public_key(abdm_test_env):
    """Verify GET /api/v1/abdm/status and GET /api/v1/abdm/crypto/public-key."""
    client, _ = abdm_test_env

    # 1. Check status
    res_status = await client.get("/api/v1/abdm/status")
    assert res_status.status_code == 200
    body = res_status.json()
    assert body["success"] is True
    data = body["data"]
    assert "status" in data
    assert data["cm_id"] == "sbx"
    assert data["sandbox_mode"] is True
    assert data["rsa_key_configured"] is True

    # 2. Check public key export
    res_pub = await client.get("/api/v1/abdm/crypto/public-key")
    assert res_pub.status_code == 200
    pub_body = res_pub.json()
    assert pub_body["success"] is True
    pub_data = pub_body["data"]
    assert "BEGIN PUBLIC KEY" in pub_data["public_key_pem"]
    assert len(pub_data["fingerprint"]) == 64
    assert pub_data["algorithm"] == "RSA-OAEP-256"


@pytest.mark.asyncio
async def test_api_abdm_crypto_encrypt_decrypt_endpoints(abdm_test_env):
    """Verify POST /api/v1/abdm/crypto/encrypt-demographics and decrypt-demographics."""
    client, session_factory = abdm_test_env

    # Seed authenticated doctor user
    async with session_factory() as session:
        doctor_user = User(
            email="dr.abdm.test@nirmaya.org",
            full_name="Dr. Vikram Sarabhai",
            role=UserRole.DOCTOR,
            is_active=True,
        )
        session.add(doctor_user)
        await session.commit()
        await session.refresh(doctor_user)
        doc_token = create_access_token(
            data={
                "sub": str(doctor_user.id),
                "role": doctor_user.role.value,
                "email": doctor_user.email,
            }
        )

    auth_header = {"Authorization": f"Bearer {doc_token}"}
    test_demographics = {
        "name": "Sunita Devi",
        "gender": "F",
        "yearOfBirth": 1992,
        "abhaAddress": "sunita.devi@abdm",
    }

    # 1. Encrypt demographics
    res_enc = await client.post(
        "/api/v1/abdm/crypto/encrypt-demographics",
        json={"demographic_data": test_demographics},
    )
    assert res_enc.status_code == 200
    enc_body = res_enc.json()
    assert enc_body["success"] is True
    ciphertext = enc_body["data"]["encrypted_data"]
    assert len(ciphertext) > 50

    # 2. Decrypt demographics (authenticated)
    res_dec = await client.post(
        "/api/v1/abdm/crypto/decrypt-demographics",
        json={"ciphertext": ciphertext},
        headers=auth_header,
    )
    assert res_dec.status_code == 200
    dec_body = res_dec.json()
    assert dec_body["success"] is True
    assert dec_body["data"] == test_demographics

    # 3. Force refresh session
    res_refresh = await client.post(
        "/api/v1/abdm/sessions/refresh",
        headers=auth_header,
    )
    assert res_refresh.status_code == 200
    refresh_body = res_refresh.json()
    assert refresh_body["success"] is True
    assert refresh_body["data"]["is_authenticated"] is True
