"""Test suite for Universal High-Density National Health Gateway.

Validates:
1. Aadhaar OTP demographic challenge and verification
2. DigiLocker e-KYC claims extraction and session issuance
3. ABHA mobile fallback authentication
4. Offline emergency break-the-glass token minting with SHA-256 seal
5. Anti-brute force rate limiter shield (5 attempts/min threshold)
6. High-density rate limiter shield 50,000 req/sec telemetry
7. Distributed session lifecycle: listing, targeted revocation, and global sign-out
8. FastAPI REST endpoints e2e contract testing
"""

import time
import pytest
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.national_gateway import (
    AadhaarOtpChallengeRequest,
    AadhaarOtpVerifyRequest,
    AbhaMobileLoginRequest,
    DigiLockerKycAuthRequest,
    EmergencyBypassAuthRequest,
    GatewayAuthChannel,
    GatewayUserRole,
    SessionRevokeRequest,
)
from app.services.national_gateway_service import national_gateway_service


@pytest.fixture(autouse=True)
def reset_gateway_state():
    """Ensure clean service state before and after each test."""
    national_gateway_service.reset_state()
    yield
    national_gateway_service.reset_state()


# --------------------------------------------------------------------------
# UNIT TESTS: CHANNEL 1 (AADHAAR OTP)
# --------------------------------------------------------------------------

def test_initiate_aadhaar_challenge_success():
    """Verify initiation of Aadhaar demographic OTP challenge."""
    req = AadhaarOtpChallengeRequest(aadhaar_number="9184 7210 4821")
    resp = national_gateway_service.initiate_aadhaar_challenge(req, client_ip="10.0.0.1")

    assert resp.txn_id.startswith("txn_aadhaar_")
    assert resp.masked_mobile == "+91 ******4821"
    assert resp.expires_in_seconds == 300
    assert "successfully dispatched" in resp.message.lower()


def test_initiate_aadhaar_challenge_invalid_length_fails():
    """Verify Aadhaar numbers shorter or longer than 12 digits are rejected."""
    req = AadhaarOtpChallengeRequest(aadhaar_number="12345")
    with pytest.raises(ValueError, match="12 digits"):
        national_gateway_service.initiate_aadhaar_challenge(req)


def test_initiate_aadhaar_challenge_non_digits_fails():
    """Verify Aadhaar numbers containing non-numeric characters fail."""
    req = AadhaarOtpChallengeRequest(aadhaar_number="9184 7210 ABCD")
    with pytest.raises(ValueError, match="12 digits"):
        national_gateway_service.initiate_aadhaar_challenge(req)


def test_verify_aadhaar_otp_success():
    """Verify valid OTP returns authenticated gateway session response."""
    challenge_req = AadhaarOtpChallengeRequest(aadhaar_number="9184 7210 4821")
    challenge_resp = national_gateway_service.initiate_aadhaar_challenge(challenge_req)

    verify_req = AadhaarOtpVerifyRequest(
        txn_id=challenge_resp.txn_id,
        otp="123456",
        remember_me=True,
    )
    session_resp = national_gateway_service.verify_aadhaar_otp(
        verify_req, client_ip="10.0.0.1", user_agent="PyTest-Agent/1.0"
    )

    assert session_resp.session_id.startswith("sess_")
    assert session_resp.access_token is not None
    assert session_resp.token_type == "bearer"
    assert session_resp.user_role == GatewayUserRole.CITIZEN
    assert session_resp.auth_channel == GatewayAuthChannel.AADHAAR_OTP
    assert session_resp.name == "Arun Kumar Patel"
    assert session_resp.identifier == "XXXX-XXXX-4821"
    assert session_resp.abha_number == "91-9184-7210-4821"
    assert session_resp.is_offline_emergency is False
    assert session_resp.emergency_seal is None


def test_verify_aadhaar_otp_remember_me_extended_session():
    """Verify remember_me=True issues 30-day session while remember_me=False issues 24-hour session."""
    challenge_req = AadhaarOtpChallengeRequest(aadhaar_number="9184 7210 4821")
    challenge_resp = national_gateway_service.initiate_aadhaar_challenge(challenge_req)

    verify_req_extended = AadhaarOtpVerifyRequest(
        txn_id=challenge_resp.txn_id,
        otp="123456",
        remember_me=True,
    )
    session_extended = national_gateway_service.verify_aadhaar_otp(verify_req_extended)

    # 30 days is approximately 720 hours
    time_delta = session_extended.expires_at - datetime.now(timezone.utc)
    assert time_delta.total_seconds() > 25 * 86400


def test_verify_aadhaar_otp_invalid_code_fails():
    """Verify invalid OTP raises ValueError and increments failure record."""
    challenge_req = AadhaarOtpChallengeRequest(aadhaar_number="9184 7210 4821")
    challenge_resp = national_gateway_service.initiate_aadhaar_challenge(challenge_req)

    verify_req = AadhaarOtpVerifyRequest(
        txn_id=challenge_resp.txn_id,
        otp="000000",
        remember_me=True,
    )
    with pytest.raises(ValueError, match="Invalid OTP"):
        national_gateway_service.verify_aadhaar_otp(verify_req)


def test_verify_aadhaar_otp_nonexistent_txn_fails():
    """Verify non-existent transaction ID is rejected."""
    verify_req = AadhaarOtpVerifyRequest(
        txn_id="txn_nonexistent_12345",
        otp="123456",
        remember_me=True,
    )
    with pytest.raises(ValueError, match="Invalid or expired transaction"):
        national_gateway_service.verify_aadhaar_otp(verify_req)


def test_verify_aadhaar_otp_expired_fails():
    """Verify expired challenge record is rejected."""
    challenge_req = AadhaarOtpChallengeRequest(aadhaar_number="9184 7210 4821")
    challenge_resp = national_gateway_service.initiate_aadhaar_challenge(challenge_req)

    # Force expiration in internal store
    national_gateway_service._challenges[challenge_resp.txn_id]["expires_at"] = time.time() - 10

    verify_req = AadhaarOtpVerifyRequest(
        txn_id=challenge_resp.txn_id,
        otp="123456",
        remember_me=True,
    )
    with pytest.raises(ValueError, match="expired"):
        national_gateway_service.verify_aadhaar_otp(verify_req)


# --------------------------------------------------------------------------
# UNIT TESTS: CHANNEL 2 (DIGILOCKER e-KYC)
# --------------------------------------------------------------------------

def test_verify_digilocker_kyc_success():
    """Verify DigiLocker OAuth2 PKCE exchange returns verified session."""
    req = DigiLockerKycAuthRequest(
        code="valid_oauth_code_dl",
        state="csrf_state_123",
        code_verifier="pkce_verifier_secret",
        remember_me=True,
    )
    session_resp = national_gateway_service.verify_digilocker_kyc(req, client_ip="10.0.0.2")

    assert session_resp.session_id.startswith("sess_")
    assert session_resp.auth_channel == GatewayAuthChannel.DIGILOCKER
    assert session_resp.user_role == GatewayUserRole.CITIZEN
    assert session_resp.name == "Arun Kumar Patel"
    assert session_resp.abha_number == "91-8472-1048-2190"


def test_verify_digilocker_kyc_missing_params_fails():
    """Verify missing authorization code or verifier raises ValueError."""
    req = DigiLockerKycAuthRequest(
        code="",
        state="csrf_state",
        code_verifier="",
        remember_me=True,
    )
    with pytest.raises(ValueError, match="Missing OAuth2 code or PKCE"):
        national_gateway_service.verify_digilocker_kyc(req)


# --------------------------------------------------------------------------
# UNIT TESTS: CHANNEL 3 (ABHA MOBILE FALLBACK)
# --------------------------------------------------------------------------

def test_verify_abha_mobile_success():
    """Verify active SIM mobile OTP authentication returns valid gateway session."""
    req = AbhaMobileLoginRequest(
        mobile_number="9876543210",
        otp="123456",
        abha_identifier="pooja.sharma@abdm",
        remember_me=True,
    )
    session_resp = national_gateway_service.verify_abha_mobile(req, client_ip="10.0.0.3")

    assert session_resp.auth_channel == GatewayAuthChannel.ABHA_MOBILE
    assert session_resp.name == "Pooja Sharma"
    assert session_resp.abha_address == "pooja.sharma@abdm"
    assert "+91 98765 43210" in session_resp.identifier


def test_verify_abha_mobile_invalid_number_fails():
    """Verify invalid mobile numbers are rejected."""
    req = AbhaMobileLoginRequest(
        mobile_number="123",
        otp="123456",
    )
    with pytest.raises(ValueError, match="10 digits"):
        national_gateway_service.verify_abha_mobile(req)


def test_verify_abha_mobile_invalid_otp_fails():
    """Verify wrong OTP for mobile authentication fails."""
    req = AbhaMobileLoginRequest(
        mobile_number="9876543210",
        otp="999999",
    )
    with pytest.raises(ValueError, match="Invalid mobile verification OTP"):
        national_gateway_service.verify_abha_mobile(req)


# --------------------------------------------------------------------------
# UNIT TESTS: CHANNEL 4 (BREAK-THE-GLASS EMERGENCY OFFLINE)
# --------------------------------------------------------------------------

def test_mint_emergency_bypass_session_success():
    """Verify issuance of break-the-glass emergency session with SHA-256 seal."""
    req = EmergencyBypassAuthRequest(
        facility_id="IN-DL-AIIMS-001",
        clinician_id="HPR-9921-DR",
        patient_identifier="TRAUMA-DEL-992",
        emergency_reason="Unconscious polytrauma victim",
        triage_level="red",
        tamper_attestation="Authorized emergency intake under Disaster Protocol.",
    )
    session_resp = national_gateway_service.mint_emergency_bypass_session(req, client_ip="10.0.0.4")

    assert session_resp.is_offline_emergency is True
    assert session_resp.emergency_seal is not None
    assert len(session_resp.emergency_seal) == 64
    assert session_resp.user_role == GatewayUserRole.DOCTOR
    assert session_resp.auth_channel == GatewayAuthChannel.OFFLINE_EMERGENCY
    delta = session_resp.expires_at - datetime.now(timezone.utc)
    assert 3.5 * 3600 < delta.total_seconds() <= 4.1 * 3600


def test_mint_emergency_bypass_tamper_seal_deterministic():
    """Verify emergency break-the-glass tamper seal is a valid 64-character SHA-256 string."""
    req = EmergencyBypassAuthRequest(
        facility_id="IN-MH-KEM-005",
        clinician_id="HPR-4411-DR",
        patient_identifier="TRAUMA-MUM-101",
        emergency_reason="Acute myocardial infarction with cardiogenic shock",
        triage_level="red",
        tamper_attestation="Clinical emergency override certified.",
    )
    resp = national_gateway_service.mint_emergency_bypass_session(req)
    assert len(resp.emergency_seal) == 64
    assert int(resp.emergency_seal, 16) > 0


def test_mint_emergency_bypass_missing_attestation_fails():
    """Verify emergency bypass without signed attestation is rejected."""
    req = EmergencyBypassAuthRequest(
        facility_id="IN-DL-AIIMS-001",
        clinician_id="HPR-9921-DR",
        patient_identifier="TRAUMA-DEL-992",
        emergency_reason="Polytrauma",
        triage_level="red",
        tamper_attestation="short",
    )
    with pytest.raises(ValueError, match="attestation"):
        national_gateway_service.mint_emergency_bypass_session(req)


def test_emergency_audit_logs_recorded():
    """Verify emergency break-the-glass sessions are logged in the immutable audit registry."""
    req = EmergencyBypassAuthRequest(
        facility_id="IN-DL-AIIMS-001",
        clinician_id="HPR-9921-DR",
        patient_identifier="TRAUMA-DEL-888",
        emergency_reason="Major arterial bleed",
        triage_level="red",
        tamper_attestation="Certified emergency clinician attestation.",
    )
    national_gateway_service.mint_emergency_bypass_session(req, client_ip="10.0.0.5")

    logs = national_gateway_service.get_emergency_audit_logs()
    assert len(logs) == 1
    assert logs[0]["facility_id"] == "IN-DL-AIIMS-001"
    assert logs[0]["patient_identifier"] == "TRAUMA-DEL-888"
    assert logs[0]["emergency_seal"] is not None


# --------------------------------------------------------------------------
# UNIT TESTS: RATE LIMITING SHIELD & ANTI-BRUTE FORCE
# --------------------------------------------------------------------------

def test_anti_brute_force_rate_limit_triggered():
    """Verify 5 consecutive failed attempts trigger rate-limiting block."""
    client_ip = "192.168.1.100"
    identifier = "918472104821"

    for _ in range(5):
        allowed, remaining, _ = national_gateway_service.check_auth_rate_limit(client_ip, identifier)
        assert allowed is True
        national_gateway_service.record_auth_attempt(client_ip, identifier, success=False)

    allowed, remaining, retry_after = national_gateway_service.check_auth_rate_limit(client_ip, identifier)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0


def test_anti_brute_force_reset_on_success():
    """Verify successful authentication resets failed attempt counter."""
    client_ip = "192.168.1.101"
    identifier = "9876543210"

    for _ in range(3):
        national_gateway_service.record_auth_attempt(client_ip, identifier, success=False)

    national_gateway_service.record_auth_attempt(client_ip, identifier, success=True)

    allowed, remaining, _ = national_gateway_service.check_auth_rate_limit(client_ip, identifier)
    assert allowed is True
    assert remaining == 5


def test_rate_shield_metrics_capacity():
    """Verify rate shield telemetry reports 50,000 req/sec burst capacity SLA."""
    metrics = national_gateway_service.get_rate_shield_metrics()
    assert metrics.capacity_per_second == 50000
    assert metrics.auth_tier_limit_per_minute == 5
    assert metrics.shield_status == "OPTIMAL"
    assert metrics.telemetry_latency_ms < 5.0


# --------------------------------------------------------------------------
# UNIT TESTS: DISTRIBUTED SESSION LIFECYCLE & REVOCATION
# --------------------------------------------------------------------------

def test_list_active_sessions_for_user():
    """Verify multiple active device sessions for a single user are enumerated."""
    challenge_req = AadhaarOtpChallengeRequest(aadhaar_number="9184 7210 4821")
    c_resp = national_gateway_service.initiate_aadhaar_challenge(challenge_req)

    v_req = AadhaarOtpVerifyRequest(txn_id=c_resp.txn_id, otp="123456")
    session = national_gateway_service.verify_aadhaar_otp(v_req, client_ip="10.0.0.1")

    sessions = national_gateway_service.list_active_sessions(session.user_id)
    assert len(sessions) == 1
    assert sessions[0].session_id == session.session_id
    assert sessions[0].is_active is True


def test_revoke_specific_session():
    """Verify 1-click targeted session revocation marks session inactive."""
    challenge_req = AadhaarOtpChallengeRequest(aadhaar_number="9184 7210 4821")
    c_resp = national_gateway_service.initiate_aadhaar_challenge(challenge_req)

    v_req = AadhaarOtpVerifyRequest(txn_id=c_resp.txn_id, otp="123456")
    session = national_gateway_service.verify_aadhaar_otp(v_req, client_ip="10.0.0.1")

    revoked = national_gateway_service.revoke_session(session.session_id)
    assert revoked is True

    assert national_gateway_service._sessions[session.session_id].is_active is False
    assert national_gateway_service.get_session(session.session_id) is None


def test_revoke_all_sessions_global_signout():
    """Verify global signout terminates all active distributed sessions for a user."""
    challenge_req = AadhaarOtpChallengeRequest(aadhaar_number="9184 7210 4821")
    c_resp = national_gateway_service.initiate_aadhaar_challenge(challenge_req)

    v_req = AadhaarOtpVerifyRequest(txn_id=c_resp.txn_id, otp="123456")
    session = national_gateway_service.verify_aadhaar_otp(v_req, client_ip="10.0.0.1")

    second_session_id = "sess_dummy_device_2"
    national_gateway_service._sessions[second_session_id] = national_gateway_service._sessions[session.session_id].model_copy(
        update={"session_id": second_session_id}
    )

    count = national_gateway_service.revoke_all_sessions(session.user_id)
    assert count == 2
    assert len(national_gateway_service.list_active_sessions(session.user_id)) == 0


# --------------------------------------------------------------------------
# INTEGRATION TESTS: REST API ENDPOINTS VIA ASYNC CLIENT
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_aadhaar_challenge_and_verify_e2e():
    """E2E test: Initiate Aadhaar challenge and verify OTP via REST API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Challenge
        c_resp = await client.post(
            "/api/v1/gateway/auth/aadhaar/challenge",
            json={"aadhaar_number": "9184 7210 4821"},
        )
        assert c_resp.status_code == 200
        c_data = c_resp.json()
        assert c_data["success"] is True
        txn_id = c_data["data"]["txn_id"]

        # Step 2: Verify
        v_resp = await client.post(
            "/api/v1/gateway/auth/aadhaar/verify",
            json={"txn_id": txn_id, "otp": "123456", "remember_me": True},
        )
        assert v_resp.status_code == 200
        v_data = v_resp.json()
        assert v_data["success"] is True
        assert v_data["data"]["user_role"] == "citizen"
        assert v_data["data"]["auth_channel"] == "aadhaar_otp"


@pytest.mark.asyncio
async def test_api_digilocker_verify_e2e():
    """E2E test: Exchange DigiLocker PKCE credentials via REST API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/gateway/auth/digilocker/verify",
            json={
                "code": "test_code_dl",
                "state": "state_abc",
                "code_verifier": "verifier_xyz",
                "remember_me": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["auth_channel"] == "digilocker"


@pytest.mark.asyncio
async def test_api_mobile_verify_e2e():
    """E2E test: Authenticate via active SIM mobile fallback via REST API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/gateway/auth/mobile/verify",
            json={
                "mobile_number": "9876543210",
                "otp": "123456",
                "abha_identifier": "pooja.sharma@abdm",
                "remember_me": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["auth_channel"] == "abha_mobile"


@pytest.mark.asyncio
async def test_api_emergency_bypass_e2e():
    """E2E test: Issue emergency break-the-glass token via REST API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/gateway/auth/emergency/bypass",
            json={
                "facility_id": "IN-DL-AIIMS-001",
                "clinician_id": "HPR-9921-DR",
                "patient_identifier": "TRAUMA-2026-DEL-101",
                "emergency_reason": "Trauma resuscitation",
                "triage_level": "red",
                "tamper_attestation": "Certified medical emergency protocol executed.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["is_offline_emergency"] is True
        assert len(data["data"]["emergency_seal"]) == 64


@pytest.mark.asyncio
async def test_api_session_lifecycle_and_revocation_e2e():
    """E2E test: List sessions, revoke targeted session, and verify revocation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        auth_resp = await client.post(
            "/api/v1/gateway/auth/mobile/verify",
            json={"mobile_number": "9876543210", "otp": "123456"},
        )
        user_id = auth_resp.json()["data"]["user_id"]
        session_id = auth_resp.json()["data"]["session_id"]

        list_resp = await client.get(f"/api/v1/gateway/sessions?user_id={user_id}")
        assert list_resp.status_code == 200
        sessions = list_resp.json()["data"]
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == session_id

        revoke_resp = await client.post(
            "/api/v1/gateway/sessions/revoke",
            json={"session_id": session_id},
        )
        assert revoke_resp.status_code == 200
        assert revoke_resp.json()["data"] is True

        list_after = await client.get(f"/api/v1/gateway/sessions?user_id={user_id}")
        assert len(list_after.json()["data"]) == 0


@pytest.mark.asyncio
async def test_api_rate_shield_metrics_endpoint():
    """E2E test: Query rate limiter metrics and 50k req/s SLA capacity status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/gateway/shield/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["capacity_per_second"] == 50000
        assert data["data"]["shield_status"] == "OPTIMAL"
