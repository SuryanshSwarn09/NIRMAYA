import os
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient, ASGITransport
from pydantic import ValidationError

from app.main import app
from app.schemas.guardian_delegation import (
    ConsentPurposeEnum,
    DelegatedConsentStatusEnum,
    DelegatedConsentGrantRequest,
    DelegatedConsentArtifactResponse,
    ScopedProxyTokenRequest,
    ScopedProxyTokenResponse,
    DelegatedConsentRevokeRequest,
    ConsentAuditTrailItem,
)
from app.services.family_proxy_service import family_proxy_service
from app.services.guardian_delegation_service import (
    GuardianDelegationService,
    guardian_delegation_service,
)


# =============================================================================
# 1. Schema & Validation Tests
# =============================================================================

def test_consent_purpose_enum_values():
    """Verify supported ABDM M3 healthcare consent purpose codes."""
    assert ConsentPurposeEnum.CAREMGT.value == "CAREMGT"
    assert ConsentPurposeEnum.EMERGENCY.value == "EMERGENCY"
    assert ConsentPurposeEnum.PUBHLTH.value == "PUBHLTH"
    assert ConsentPurposeEnum.DIAGNOSTIC.value == "DIAGNOSTIC"


def test_delegated_consent_status_enum_values():
    """Verify lifecycle state transitions for delegated consent artifacts."""
    assert DelegatedConsentStatusEnum.GRANTED.value == "GRANTED"
    assert DelegatedConsentStatusEnum.REVOKED.value == "REVOKED"
    assert DelegatedConsentStatusEnum.EXPIRED.value == "EXPIRED"
    assert DelegatedConsentStatusEnum.REQUESTED.value == "REQUESTED"


def test_schema_delegated_consent_grant_request_valid():
    """Verify schema initialization with valid parameters."""
    req = DelegatedConsentGrantRequest(
        consent_request_id="req-abdm-9901",
        guardian_patient_id="pat-priya-sharma-01",
        dependent_patient_id="pat-aarav-sharma-02",
        purpose=ConsentPurposeEnum.CAREMGT,
        hi_types=["DiagnosticReport", "Prescription"],
        date_range_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        date_range_to=datetime(2026, 11, 4, tzinfo=timezone.utc),
        expiry_date=datetime(2027, 5, 4, tzinfo=timezone.utc),
        guardian_signature_attestation=True,
        requester_hiu_name="Fortis Pediatric Care",
    )
    assert req.consent_request_id == "req-abdm-9901"
    assert req.guardian_signature_attestation is True
    assert len(req.hi_types) == 2


def test_schema_delegated_consent_grant_missing_fields():
    """Verify validation error when mandatory fields are missing."""
    with pytest.raises(ValidationError):
        DelegatedConsentGrantRequest(
            consent_request_id="req-abdm-9901",
            guardian_patient_id="pat-priya-sharma-01",
            # missing dependent_patient_id, date ranges, attestation
        )


def test_schema_scoped_proxy_token_request_valid():
    """Verify ScopedProxyTokenRequest defaults and bounds."""
    req = ScopedProxyTokenRequest(
        guardian_patient_id="pat-priya-sharma-01",
        dependent_patient_id="pat-aarav-sharma-02",
        requested_scope="proxy:dependent:CAREMGT",
        duration_seconds=1800,
    )
    assert req.duration_seconds == 1800
    assert req.requested_scope == "proxy:dependent:CAREMGT"


def test_schema_scoped_proxy_token_request_duration_bounds():
    """Verify token lifetime cannot be outside [60, 86400] seconds."""
    with pytest.raises(ValidationError):
        ScopedProxyTokenRequest(
            guardian_patient_id="pat-priya-sharma-01",
            dependent_patient_id="pat-aarav-sharma-02",
            duration_seconds=30,  # Below 60s lower bound
        )

    with pytest.raises(ValidationError):
        ScopedProxyTokenRequest(
            guardian_patient_id="pat-priya-sharma-01",
            dependent_patient_id="pat-aarav-sharma-02",
            duration_seconds=100000,  # Above 86400s upper bound
        )


def test_schema_delegated_consent_revoke_request():
    """Verify revoke payload attributes."""
    req = DelegatedConsentRevokeRequest(
        artifact_id="art-delegated-001",
        guardian_patient_id="pat-priya-sharma-01",
        revocation_reason="Parent ended tele-consultation session",
    )
    assert req.artifact_id == "art-delegated-001"
    assert "tele-consultation" in req.revocation_reason


# =============================================================================
# 2. Service Unit Tests
# =============================================================================

def test_service_grant_delegated_consent_success():
    """Test authorized proxy guardian granting ABDM consent artifact."""
    service = GuardianDelegationService()

    req = DelegatedConsentGrantRequest(
        consent_request_id="req-test-grant-01",
        guardian_patient_id="pat-priya-sharma-01",
        dependent_patient_id="pat-aarav-sharma-02",
        purpose=ConsentPurposeEnum.CAREMGT,
        hi_types=["DiagnosticReport", "Prescription", "ImmunizationRecord"],
        date_range_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        date_range_to=datetime(2026, 11, 4, tzinfo=timezone.utc),
        expiry_date=datetime(2027, 5, 4, tzinfo=timezone.utc),
        guardian_signature_attestation=True,
        requester_hiu_name="Apollo Clinic Bangalore",
    )

    artifact = service.grant_delegated_consent(req)
    assert artifact.artifact_id.startswith("art-delegated-")
    assert artifact.status == DelegatedConsentStatusEnum.GRANTED
    assert artifact.guardian_patient_id == "pat-priya-sharma-01"
    assert artifact.dependent_patient_id == "pat-aarav-sharma-02"
    assert artifact.zero_contamination_verified is True
    assert len(artifact.guardian_signature_hash) == 64


def test_service_grant_delegated_consent_fails_without_signature():
    """Test DPDP Act Sec 9 enforcement when guardian digital attestation is False."""
    service = GuardianDelegationService()

    req = DelegatedConsentGrantRequest(
        consent_request_id="req-test-grant-02",
        guardian_patient_id="pat-priya-sharma-01",
        dependent_patient_id="pat-aarav-sharma-02",
        purpose=ConsentPurposeEnum.CAREMGT,
        hi_types=["Prescription"],
        date_range_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        date_range_to=datetime(2026, 11, 4, tzinfo=timezone.utc),
        expiry_date=datetime(2027, 5, 4, tzinfo=timezone.utc),
        guardian_signature_attestation=False,
        requester_hiu_name="Apollo Clinic Bangalore",
    )

    with pytest.raises(ValueError, match="DPDP Act Sec 9 Violation"):
        service.grant_delegated_consent(req)


def test_service_grant_delegated_consent_fails_for_unauthorized_guardian():
    """Test rejection when actor lacks active proxy delegation for the dependent."""
    service = GuardianDelegationService()

    req = DelegatedConsentGrantRequest(
        consent_request_id="req-test-grant-03",
        guardian_patient_id="pat-unauthorized-99",  # Not a registered guardian!
        dependent_patient_id="pat-aarav-sharma-02",
        purpose=ConsentPurposeEnum.CAREMGT,
        hi_types=["Prescription"],
        date_range_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        date_range_to=datetime(2026, 11, 4, tzinfo=timezone.utc),
        expiry_date=datetime(2027, 5, 4, tzinfo=timezone.utc),
        guardian_signature_attestation=True,
        requester_hiu_name="Apollo Clinic Bangalore",
    )

    with pytest.raises(ValueError, match="Unauthorized Delegation"):
        service.grant_delegated_consent(req)


def test_service_grant_delegated_consent_fails_on_inverted_dates():
    """Test validation failure when date_range_from is after date_range_to."""
    service = GuardianDelegationService()

    req = DelegatedConsentGrantRequest(
        consent_request_id="req-test-grant-04",
        guardian_patient_id="pat-priya-sharma-01",
        dependent_patient_id="pat-aarav-sharma-02",
        purpose=ConsentPurposeEnum.CAREMGT,
        hi_types=["Prescription"],
        date_range_from=datetime(2026, 11, 4, tzinfo=timezone.utc),
        date_range_to=datetime(2026, 1, 1, tzinfo=timezone.utc),  # Inverted!
        expiry_date=datetime(2027, 5, 4, tzinfo=timezone.utc),
        guardian_signature_attestation=True,
        requester_hiu_name="Apollo Clinic Bangalore",
    )

    with pytest.raises(ValueError, match="Temporal Bound Invariant"):
        service.grant_delegated_consent(req)


def test_service_grant_delegated_consent_fails_on_past_expiry():
    """Test validation failure when consent expiry date is in the past."""
    service = GuardianDelegationService()

    req = DelegatedConsentGrantRequest(
        consent_request_id="req-test-grant-05",
        guardian_patient_id="pat-priya-sharma-01",
        dependent_patient_id="pat-aarav-sharma-02",
        purpose=ConsentPurposeEnum.CAREMGT,
        hi_types=["Prescription"],
        date_range_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        date_range_to=datetime(2026, 5, 1, tzinfo=timezone.utc),
        expiry_date=datetime(2026, 5, 2, tzinfo=timezone.utc),  # Past date!
        guardian_signature_attestation=True,
        requester_hiu_name="Apollo Clinic Bangalore",
    )

    with pytest.raises(ValueError, match="Expiration Invariant"):
        service.grant_delegated_consent(req)


def test_service_revoke_delegated_consent_success():
    """Test revoking an active delegated consent artifact."""
    service = GuardianDelegationService()

    # Pre-existing seed artifact 'art-delegated-001'
    revoke_req = DelegatedConsentRevokeRequest(
        artifact_id="art-delegated-001",
        guardian_patient_id="pat-priya-sharma-01",
        revocation_reason="Parent withdrawn consent",
    )

    revoked = service.revoke_delegated_consent(revoke_req)
    assert revoked.status == DelegatedConsentStatusEnum.REVOKED
    assert revoked.artifact_id == "art-delegated-001"


def test_service_revoke_consent_nonexistent_artifact():
    """Test revoking a non-existent artifact raises KeyError."""
    service = GuardianDelegationService()

    revoke_req = DelegatedConsentRevokeRequest(
        artifact_id="art-nonexistent-999",
        guardian_patient_id="pat-priya-sharma-01",
        revocation_reason="Non-existent artifact test",
    )

    with pytest.raises(KeyError, match="not found"):
        service.revoke_delegated_consent(revoke_req)


def test_service_revoke_consent_unauthorized_guardian():
    """Test revoking an artifact by an imposter guardian raises ValueError."""
    service = GuardianDelegationService()

    revoke_req = DelegatedConsentRevokeRequest(
        artifact_id="art-delegated-001",
        guardian_patient_id="pat-imposter-99",  # Not the original issuer
        revocation_reason="Imposter revocation",
    )

    with pytest.raises(ValueError, match="Unauthorized Actor"):
        service.revoke_delegated_consent(revoke_req)


def test_service_generate_scoped_proxy_token_success():
    """Test minting purpose-restricted ephemeral token for proxy consultation."""
    service = GuardianDelegationService()

    token_req = ScopedProxyTokenRequest(
        guardian_patient_id="pat-priya-sharma-01",
        dependent_patient_id="pat-aarav-sharma-02",
        requested_scope="proxy:dependent:CAREMGT",
        duration_seconds=900,
    )

    token_res = service.generate_scoped_proxy_token(token_req)
    assert token_res.token_type == "Bearer"
    assert token_res.expires_in == 900
    assert token_res.scope == "proxy:dependent:CAREMGT"
    assert token_res.guardian_id == "pat-priya-sharma-01"
    assert token_res.dependent_id == "pat-aarav-sharma-02"
    assert token_res.zero_contamination_isolated is True
    assert token_res.access_token.startswith("nirmaya_proxy_")


def test_service_generate_scoped_proxy_token_unauthorized_guardian():
    """Test token minting failure for unauthorized actor."""
    service = GuardianDelegationService()

    token_req = ScopedProxyTokenRequest(
        guardian_patient_id="pat-stranger-99",
        dependent_patient_id="pat-aarav-sharma-02",
        requested_scope="proxy:dependent:CAREMGT",
        duration_seconds=900,
    )

    with pytest.raises(ValueError, match="Unauthorized Token Request"):
        service.generate_scoped_proxy_token(token_req)


def test_service_intercept_consent_request_authorized():
    """Test interception of inbound ABDM consent request for authorized guardian."""
    service = GuardianDelegationService()

    res = service.intercept_consent_request(
        guardian_id="pat-priya-sharma-01",
        dependent_id="pat-aarav-sharma-02",
        consent_request_id="req-inbound-501",
    )

    assert res["authorized"] is True
    assert res["guardian_id"] == "pat-priya-sharma-01"
    assert res["dependent_id"] == "pat-aarav-sharma-02"
    assert res["matching_relationship"] is not None
    assert len(res["permitted_hi_types"]) > 0


def test_service_intercept_consent_request_unauthorized():
    """Test interception of inbound consent request for unauthorized user."""
    service = GuardianDelegationService()

    res = service.intercept_consent_request(
        guardian_id="pat-stranger-99",
        dependent_id="pat-aarav-sharma-02",
        consent_request_id="req-inbound-502",
    )

    assert res["authorized"] is False
    assert res["matching_relationship"] is None


def test_service_list_delegated_consents_filters():
    """Test filtering delegated consents by guardian and dependent."""
    service = GuardianDelegationService()

    all_consents = service.list_delegated_consents()
    assert len(all_consents) >= 1

    by_guardian = service.list_delegated_consents(guardian_id="pat-priya-sharma-01")
    assert len(by_guardian) >= 1

    by_mismatched = service.list_delegated_consents(guardian_id="pat-nobody-99")
    assert len(by_mismatched) == 0


def test_service_list_pending_requests():
    """Test listing seeded pending inbound ABDM requests."""
    service = GuardianDelegationService()
    pending = service.list_pending_requests()
    assert len(pending) >= 1
    assert "consent_request_id" in pending[0]
    assert "requester_hiu_name" in pending[0]


def test_service_audit_trail_logging():
    """Test immutable audit trail recording."""
    service = GuardianDelegationService()
    logs = service.get_audit_trail()
    assert len(logs) >= 1
    assert logs[0].action.startswith("CONSENT_ARTIFACT_")

    by_art = service.get_audit_trail(artifact_id="art-delegated-001")
    assert len(by_art) >= 1
    assert by_art[0].artifact_id == "art-delegated-001"


# =============================================================================
# 3. FastAPI REST API Endpoint Tests
# =============================================================================

@pytest.mark.asyncio
async def test_api_issue_scoped_proxy_token_endpoint():
    """Test POST /api/v1/patients/proxy/delegation/token endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/patients/proxy/delegation/token",
            json={
                "guardian_patient_id": "pat-priya-sharma-01",
                "dependent_patient_id": "pat-aarav-sharma-02",
                "requested_scope": "proxy:dependent:CAREMGT",
                "duration_seconds": 900,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 900
        assert data["zero_contamination_isolated"] is True
        assert "access_token" in data


@pytest.mark.asyncio
async def test_api_grant_delegated_consent_endpoint():
    """Test POST /api/v1/patients/proxy/consent/grant endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/patients/proxy/consent/grant",
            json={
                "consent_request_id": "req-api-grant-101",
                "guardian_patient_id": "pat-priya-sharma-01",
                "dependent_patient_id": "pat-aarav-sharma-02",
                "purpose": "CAREMGT",
                "hi_types": ["DiagnosticReport", "Prescription"],
                "date_range_from": "2026-01-01T00:00:00Z",
                "date_range_to": "2026-11-04T00:00:00Z",
                "expiry_date": "2027-05-04T00:00:00Z",
                "guardian_signature_attestation": True,
                "requester_hiu_name": "Fortis Child Care",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "GRANTED"
        assert data["guardian_patient_id"] == "pat-priya-sharma-01"
        assert "artifact_id" in data


@pytest.mark.asyncio
async def test_api_grant_consent_fails_without_signature():
    """Test POST /api/v1/patients/proxy/consent/grant returns 400 when un-attested."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/patients/proxy/consent/grant",
            json={
                "consent_request_id": "req-api-grant-102",
                "guardian_patient_id": "pat-priya-sharma-01",
                "dependent_patient_id": "pat-aarav-sharma-02",
                "purpose": "CAREMGT",
                "hi_types": ["Prescription"],
                "date_range_from": "2026-01-01T00:00:00Z",
                "date_range_to": "2026-11-04T00:00:00Z",
                "expiry_date": "2027-05-04T00:00:00Z",
                "guardian_signature_attestation": False,  # Missing signature!
                "requester_hiu_name": "Fortis Child Care",
            },
        )
        assert res.status_code == 400
        data = res.json()
        error_text = data.get("message") or data.get("detail", "")
        assert "DPDP Act Sec 9 Violation" in error_text


@pytest.mark.asyncio
async def test_api_revoke_delegated_consent_endpoint():
    """Test POST /api/v1/patients/proxy/consent/{artifact_id}/revoke endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First grant an artifact
        grant_res = await ac.post(
            "/api/v1/patients/proxy/consent/grant",
            json={
                "consent_request_id": "req-api-revoke-201",
                "guardian_patient_id": "pat-priya-sharma-01",
                "dependent_patient_id": "pat-aarav-sharma-02",
                "purpose": "CAREMGT",
                "hi_types": ["DiagnosticReport"],
                "date_range_from": "2026-01-01T00:00:00Z",
                "date_range_to": "2026-11-04T00:00:00Z",
                "expiry_date": "2027-05-04T00:00:00Z",
                "guardian_signature_attestation": True,
                "requester_hiu_name": "Max Healthcare",
            },
        )
        art_id = grant_res.json()["artifact_id"]

        # Now revoke it
        revoke_res = await ac.post(
            f"/api/v1/patients/proxy/consent/{art_id}/revoke",
            json={
                "artifact_id": art_id,
                "guardian_patient_id": "pat-priya-sharma-01",
                "revocation_reason": "Tele-consultation completed",
            },
        )
        assert revoke_res.status_code == 200
        assert revoke_res.json()["status"] == "REVOKED"


@pytest.mark.asyncio
async def test_api_list_delegated_consents_endpoint():
    """Test GET /api/v1/patients/proxy/consent/artifacts endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(
            "/api/v1/patients/proxy/consent/artifacts",
            params={"guardian_id": "pat-priya-sharma-01"},
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1


@pytest.mark.asyncio
async def test_api_list_pending_consent_requests_endpoint():
    """Test GET /api/v1/patients/proxy/consent/pending-requests endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patients/proxy/consent/pending-requests")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1


@pytest.mark.asyncio
async def test_api_get_consent_audit_trail_endpoint():
    """Test GET /api/v1/patients/proxy/consent/audit endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patients/proxy/consent/audit")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1


@pytest.mark.asyncio
async def test_api_intercept_inbound_consent_endpoint():
    """Test POST /api/v1/patients/proxy/consent/intercept endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/patients/proxy/consent/intercept",
            json={
                "guardian_id": "pat-priya-sharma-01",
                "dependent_id": "pat-aarav-sharma-02",
                "consent_request_id": "req-inbound-601",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["authorized"] is True
        assert data["consent_request_id"] == "req-inbound-601"
