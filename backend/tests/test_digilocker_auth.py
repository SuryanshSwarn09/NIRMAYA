"""Automated test suite for DigiLocker OAuth 2.0 PKCE & e-Aadhaar Verification Service.

Verifies:
- RFC 7636 PKCE code_verifier and code_challenge S256 generation
- Authorization URL synthesis with state, client_id, and redirect_uri
- e-Aadhaar XML parsing for UIDAI POI, POA, PHT, and X.509 signature elements
- FastAPI endpoints:
  - GET /api/v1/auth/digilocker/authorize-url
  - POST /api/v1/auth/digilocker/verify
  - POST /api/v1/auth/digilocker/sync-patient/{patient_id}
"""

import base64
import hashlib
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import Gender, UserRole
from app.models.patient import PatientProfile
from app.models.user import User
from app.services.digilocker import (
    SIMULATED_EAADHAAR_XML,
    exchange_code_for_token,
    generate_authorization_url,
    generate_pkce_pair,
    parse_eaadhaar_xml,
    verify_digilocker_callback,
)


@pytest_asyncio.fixture
async def digilocker_test_env():
    """Isolated in-memory SQLite database environment for DigiLocker tests."""
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


def test_pkce_pair_generation():
    """Verify PKCE code_verifier and code_challenge comply with RFC 7636."""
    verifier, challenge = generate_pkce_pair()

    assert len(verifier) >= 43
    assert len(challenge) >= 43
    assert "=" not in challenge  # Unpadded base64url

    # Verify SHA-256 relationship
    expected_digest = hashlib.sha256(verifier.encode("ascii")).digest()
    expected_challenge = base64.urlsafe_b64encode(expected_digest).decode("ascii").rstrip("=")
    assert challenge == expected_challenge


def test_generate_authorization_url():
    """Verify DigiLocker authorization URL contains all mandatory OAuth 2.0 PKCE parameters."""
    custom_state = "test_custom_csrf_state_12345"
    resp, verifier = generate_authorization_url(state=custom_state)

    assert resp.state == custom_state
    assert resp.code_challenge_method == "S256"
    assert resp.code_challenge is not None
    assert f"client_id={settings.DIGILOCKER_CLIENT_ID}" in resp.authorize_url
    assert "response_type=code" in resp.authorize_url
    assert f"state={custom_state}" in resp.authorize_url
    assert f"code_challenge={resp.code_challenge}" in resp.authorize_url
    assert "code_challenge_method=S256" in resp.authorize_url


def test_parse_eaadhaar_xml_success():
    """Verify e-Aadhaar XML parsing correctly extracts UIDAI demographic claims."""
    demographics = parse_eaadhaar_xml(SIMULATED_EAADHAAR_XML)

    assert demographics.name == "Arun Kumar Patel"
    assert demographics.gender == "male"
    assert demographics.date_of_birth == "1990-06-04"
    assert demographics.masked_aadhaar == "XXXX-XXXX-4821"
    assert demographics.photo_base64 is not None
    assert demographics.signature_valid is True
    assert demographics.issuer == "UIDAI"

    assert demographics.address.district == "Bengaluru Urban"
    assert demographics.address.state == "Karnataka"
    assert demographics.address.pincode == "560034"
    assert "Koramangala 4th Block" in demographics.address.formatted_address


def test_parse_eaadhaar_xml_malformed():
    """Verify e-Aadhaar XML parser rejects malformed XML."""
    with pytest.raises(AppException) as exc_info:
        parse_eaadhaar_xml("<NotEvenValidXML>>>")
    assert "Invalid e-Aadhaar XML payload" in str(exc_info.value)


@pytest.mark.asyncio
async def test_digilocker_token_exchange_simulation():
    """Verify token exchange returns valid mock token in simulation mode."""
    token = await exchange_code_for_token("mock_auth_code_987", "mock_verifier")
    assert token.access_token.startswith("mock_dl_bearer_")
    assert token.token_type == "bearer"
    assert token.digilocker_id == "DL-IND-98472109"


@pytest.mark.asyncio
async def test_verify_digilocker_callback():
    """Verify end-to-end verification helper produces complete DigiLockerVerificationResult."""
    result = await verify_digilocker_callback(
        code="mock_auth_code_abc",
        state="test_state_123",
        code_verifier="mock_verifier",
    )
    assert result.verified is True
    assert result.digilocker_id == "DL-IND-98472109"
    assert result.demographics.name == "Arun Kumar Patel"
    assert result.demographics.masked_aadhaar == "XXXX-XXXX-4821"


@pytest.mark.asyncio
async def test_endpoint_authorize_url(digilocker_test_env):
    """Verify GET /api/v1/auth/digilocker/authorize-url returns HTTP 200 and PKCE URL."""
    client, _ = digilocker_test_env
    response = await client.get("/api/v1/auth/digilocker/authorize-url?state=test_flow_state")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    payload = data["data"]
    assert "authorize_url" in payload
    assert payload["state"] == "test_flow_state"
    assert payload["code_challenge_method"] == "S256"


@pytest.mark.asyncio
async def test_endpoint_verify_callback(digilocker_test_env):
    """Verify POST /api/v1/auth/digilocker/verify returns verified e-Aadhaar claims."""
    client, _ = digilocker_test_env
    req_body = {
        "code": "mock_test_code_xyz",
        "state": "test_flow_state",
        "code_verifier": "mock_verifier_xyz",
    }
    response = await client.post("/api/v1/auth/digilocker/verify", json=req_body)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    result = data["data"]
    assert result["verified"] is True
    assert result["digilocker_id"] == "DL-IND-98472109"
    assert result["demographics"]["name"] == "Arun Kumar Patel"
    assert result["demographics"]["gender"] == "male"
    assert result["demographics"]["masked_aadhaar"] == "XXXX-XXXX-4821"


@pytest.mark.asyncio
async def test_endpoint_sync_patient_identity(digilocker_test_env):
    """Verify POST /api/v1/auth/digilocker/sync-patient/{patient_id} updates patient record."""
    client, session_factory = digilocker_test_env

    # 1. Create a patient user and profile in the test database
    patient_user_id = str(uuid.uuid4())
    patient_profile_id = str(uuid.uuid4())

    async with session_factory() as session:
        user = User(
            id=patient_user_id,
            email="arun.patient@example.com",
            full_name="Old Name",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        patient = PatientProfile(
            id=patient_profile_id,
            user_id=patient_user_id,
            gender=Gender.UNKNOWN,
        )
        session.add(user)
        session.add(patient)
        await session.commit()

    # 2. Authenticate as the patient
    token = create_access_token(
        data={"sub": patient_user_id, "role": UserRole.PATIENT.value, "email": "arun.patient@example.com"}
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Call /verify endpoint to get verified payload
    verify_resp = await client.post(
        "/api/v1/auth/digilocker/verify",
        json={"code": "mock_sync_code", "state": "test_sync", "code_verifier": "mock_ver"},
    )
    assert verify_resp.status_code == 200
    verified_data = verify_resp.json()["data"]

    # 4. Call /sync-patient/{patient_id}
    sync_resp = await client.post(
        f"/api/v1/auth/digilocker/sync-patient/{patient_profile_id}",
        json=verified_data,
        headers=headers,
    )
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["success"] is True
    assert sync_data["data"]["patient_id"] == patient_profile_id
    assert sync_data["data"]["name"] == "Arun Kumar Patel"
    assert sync_data["data"]["masked_aadhaar"] == "XXXX-XXXX-4821"
    assert sync_data["data"]["is_identity_verified"] is True

    # 5. Verify database was updated
    async with session_factory() as session:
        updated_patient = await session.get(PatientProfile, patient_profile_id)
        assert updated_patient is not None
        assert updated_patient.gender == Gender.MALE
        assert updated_patient.city == "Bengaluru Urban"
        assert updated_patient.state == "Karnataka"
        assert updated_patient.pincode == "560034"
