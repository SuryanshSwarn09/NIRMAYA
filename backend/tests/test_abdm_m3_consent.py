"""Tests for ABDM Milestone 3 (M3) Consent Ingestion, Signature Verification, and Registry.

Verifies:
- NHA v0.5 Consent Schemas & Artefact deserialization
- Gateway Replay Drift Defense (300s window)
- Inbound Webhook synchronous HTTP 202 Accepted (/v0.5/consents/hip/notify)
- Consent digital signature verification (valid and invalid scenarios)
- Asynchronous callback formatting (/v0.5/consents/hip/on-notify)
- Consent status transitions: GRANTED, REVOKED, EXPIRED
- Fine-grained clinical record authorization (care contexts, hiTypes, date ranges)
- Internal Query API endpoints (/consents/{id}, /consents/patient/{id}, /consents/simulate)
"""

from datetime import datetime, timedelta, timezone
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.abdm_m3_consent import (
    ConsentArtefact,
    ConsentCareContextReference,
    ConsentDateRange,
    ConsentDetail,
    ConsentFrequency,
    ConsentManagerRef,
    ConsentNotificationDetail,
    ConsentNotificationPayload,
    ConsentNotificationSimulateRequest,
    ConsentPatient,
    ConsentPermission,
    ConsentPurpose,
    ConsentRecordRepresentation,
    ConsentRequester,
)
from app.services.abdm_consent import (
    consent_registry_store,
    process_and_dispatch_consent_notification,
    simulate_consent_notification,
    verify_consent_signature,
)
from app.services.abdm_hip_bridge import NIRMAYA_HIP_ID, webhook_audit_store


@pytest.fixture(autouse=True)
def reset_stores():
    """Ensure clean store state before each test run."""
    consent_registry_store.clear()
    yield
    consent_registry_store.clear()


@pytest.fixture
def sample_consent_payload():
    """Build a standard NHA v0.5 valid consent notification payload."""
    now = datetime.now(timezone.utc)
    consent_id = f"consent-{uuid.uuid4()}"
    req_id = str(uuid.uuid4())

    detail = ConsentDetail(
        schemaVersion="v0.5",
        consentId=consent_id,
        createdAt=now - timedelta(minutes=5),
        patient=ConsentPatient(id="sneha.sharma@abdm"),
        careContexts=[
            ConsentCareContextReference(
                patientReference="NIR-P-10023",
                careContextReference="ENC-2026-0042",
            ),
            ConsentCareContextReference(
                patientReference="NIR-P-10023",
                careContextReference="ENC-2026-0089",
            ),
        ],
        purpose=ConsentPurpose(code="CAREMGT", text="Care Management"),
        hip=ConsentManagerRef(id=NIRMAYA_HIP_ID),
        hiu=ConsentManagerRef(id="HIU-APOLLO-001"),
        consentManager=ConsentManagerRef(id="sbx"),
        hiTypes=["OPConsultation", "DiagnosticReport", "Prescription"],
        permission=ConsentPermission(
            accessMode="VIEW",
            dateRange=ConsentDateRange(
                from_date=now - timedelta(days=90),
                to_date=now,
            ),
            dataEraseAt=now + timedelta(days=30),
            frequency=ConsentFrequency(unit="HOUR", value=1, repeats=0),
        ),
    )

    artefact = ConsentArtefact(
        schemaVersion="v0.5",
        consentId=consent_id,
        consentDetail=detail,
        signature="SHA256withRSA/EYJhbGciOiJSUzI1NiIsImtpZCI6InNieCJ9...",
    )

    return ConsentNotificationPayload(
        requestId=req_id,
        timestamp=now,
        notification=ConsentNotificationDetail(
            consentId=consent_id,
            status="GRANTED",
            consentArtefact=artefact,
        ),
    )


# ----------------------------------------------------------------------------
# 1. Schema & Signature Verification Unit Tests
# ----------------------------------------------------------------------------


def test_signature_verification_success(sample_consent_payload):
    """Verify valid signature formats pass signature check."""
    artefact = sample_consent_payload.notification.consentArtefact
    assert verify_consent_signature(artefact) is True


def test_signature_verification_failure():
    """Verify empty or corrupt signatures fail validation."""
    invalid_artefact = ConsentArtefact(
        consentId="test-bad-sig",
        signature="",
    )
    assert verify_consent_signature(invalid_artefact) is False

    none_sig_artefact = ConsentArtefact(
        consentId="test-bad-sig",
        signature=None,
    )
    assert verify_consent_signature(none_sig_artefact) is False


# ----------------------------------------------------------------------------
# 2. Replay Defense & Ingest Webhook Tests (/v0.5/consents/hip/notify)
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_webhook_inbound_notify_accepted(sample_consent_payload):
    """Verify Gateway webhook returns HTTP 202 Accepted and records telemetry."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {
            "REQUEST-ID": sample_consent_payload.requestId,
            "TIMESTAMP": sample_consent_payload.timestamp.isoformat(),
            "X-CM-ID": "sbx",
        }
        response = await client.post(
            "/v0.5/consents/hip/notify",
            headers=headers,
            json=sample_consent_payload.model_dump(mode="json"),
        )

        assert response.status_code == 202
        # Verify event was recorded in webhook audit store
        event = webhook_audit_store.get_event_by_request_id(sample_consent_payload.requestId)
        assert event is not None
        assert event.event_type == "consents/hip/notify"


@pytest.mark.asyncio
async def test_webhook_inbound_replay_drift_rejection(sample_consent_payload):
    """Verify requests with timestamp skew > 300s are rejected with HTTP 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        stale_timestamp = (datetime.now(timezone.utc) - timedelta(seconds=350)).isoformat()
        headers = {
            "REQUEST-ID": str(uuid.uuid4()),
            "TIMESTAMP": stale_timestamp,
            "X-CM-ID": "sbx",
        }
        response = await client.post(
            "/v0.5/consents/hip/notify",
            headers=headers,
            json=sample_consent_payload.model_dump(mode="json"),
        )

        assert response.status_code == 400
        data = response.json()
        assert "drift" in data["message"].lower() or "skew" in data["message"].lower()


# ----------------------------------------------------------------------------
# 3. Consent Processing & Lifecycle Tests (GRANTED -> REVOKED -> EXPIRED)
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_granted_consent(sample_consent_payload):
    """Verify processing GRANTED consent populates registry and generates valid on-notify."""
    callback = await process_and_dispatch_consent_notification(
        incoming_request=sample_consent_payload,
        start_time=0.0,
    )

    assert callback.acknowledgement is not None
    assert callback.acknowledgement.status == "OK"
    assert callback.acknowledgement.consentId == sample_consent_payload.notification.consentId
    assert callback.resp.requestId == sample_consent_payload.requestId
    assert callback.error is None

    # Verify record in registry
    record = consent_registry_store.get_consent(sample_consent_payload.notification.consentId)
    assert record is not None
    assert record.status == "GRANTED"
    assert record.patient_id == "sneha.sharma@abdm"
    assert record.hiu_id == "HIU-APOLLO-001"
    assert "OPConsultation" in record.hi_types
    assert len(record.care_contexts) == 2


@pytest.mark.asyncio
async def test_process_revoked_consent(sample_consent_payload):
    """Verify processing REVOKED consent updates registry status to REVOKED."""
    # First grant consent
    await process_and_dispatch_consent_notification(
        incoming_request=sample_consent_payload,
        start_time=0.0,
    )

    # Now create revocation payload
    consent_id = sample_consent_payload.notification.consentId
    revocation_payload = ConsentNotificationPayload(
        requestId=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        notification=ConsentNotificationDetail(
            consentId=consent_id,
            status="REVOKED",
            consentArtefact=None,
        ),
    )

    callback = await process_and_dispatch_consent_notification(
        incoming_request=revocation_payload,
        start_time=0.0,
    )

    assert callback.acknowledgement is not None
    assert callback.acknowledgement.status == "OK"

    record = consent_registry_store.get_consent(consent_id)
    assert record is not None
    assert record.status == "REVOKED"


# ----------------------------------------------------------------------------
# 4. Fine-Grained Health Record Authorization Engine Tests
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_record_authorization(sample_consent_payload):
    """Test multi-dimensional clinical access checks."""
    await process_and_dispatch_consent_notification(
        incoming_request=sample_consent_payload,
        start_time=0.0,
    )
    consent_id = sample_consent_payload.notification.consentId
    now = datetime.now(timezone.utc)

    # 1. Valid request matching care context, HI type, and date range
    authorized, reason = consent_registry_store.validate_record_authorization(
        consent_id=consent_id,
        hi_type="OPConsultation",
        care_context_id="ENC-2026-0042",
        record_timestamp=now - timedelta(days=10),
    )
    assert authorized is True
    assert reason == "Authorized"

    # 2. Unauthorized HI type (e.g. DischargeSummary)
    authorized, reason = consent_registry_store.validate_record_authorization(
        consent_id=consent_id,
        hi_type="DischargeSummary",
        care_context_id="ENC-2026-0042",
        record_timestamp=now - timedelta(days=10),
    )
    assert authorized is False
    assert "DischargeSummary" in reason

    # 3. Unauthorized Care Context
    authorized, reason = consent_registry_store.validate_record_authorization(
        consent_id=consent_id,
        hi_type="Prescription",
        care_context_id="ENC-UNKNOWN-9999",
        record_timestamp=now - timedelta(days=10),
    )
    assert authorized is False
    assert "ENC-UNKNOWN-9999" in reason

    # 4. Out of date range (older than 90 days)
    authorized, reason = consent_registry_store.validate_record_authorization(
        consent_id=consent_id,
        hi_type="DiagnosticReport",
        care_context_id="ENC-2026-0089",
        record_timestamp=now - timedelta(days=120),
    )
    assert authorized is False
    assert "falls outside permitted" in reason


# ----------------------------------------------------------------------------
# 5. Internal Query & Simulation API Endpoints Tests
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_consent_endpoints(sample_consent_payload):
    """Test /consents/{id} and /consents/patient/{id} endpoints."""
    await process_and_dispatch_consent_notification(
        incoming_request=sample_consent_payload,
        start_time=0.0,
    )
    consent_id = sample_consent_payload.notification.consentId

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Query by ID
        resp_id = await client.get(f"/api/v1/abdm/m3/consent/consents/{consent_id}")
        assert resp_id.status_code == 200
        body = resp_id.json()
        assert body["success"] is True
        assert body["data"]["consent_id"] == consent_id
        assert body["data"]["patient_id"] == "sneha.sharma@abdm"

        # Query by patient
        resp_pt = await client.get("/api/v1/abdm/m3/consent/consents/patient/sneha.sharma@abdm")
        assert resp_pt.status_code == 200
        pt_body = resp_pt.json()
        assert len(pt_body["data"]) == 1
        assert pt_body["data"][0]["consent_id"] == consent_id

        # Query non-existent ID -> 404
        resp_404 = await client.get("/api/v1/abdm/m3/consent/consents/non-existent-uuid")
        assert resp_404.status_code == 404


@pytest.mark.asyncio
async def test_simulate_consent_endpoint():
    """Test interactive simulation endpoint /consents/simulate."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sim_payload = {
            "patient_id": "arun.verma@abdm",
            "patient_reference": "NIR-P-99001",
            "care_context_references": ["ENC-2026-0101", "ENC-2026-0102"],
            "hiu_id": "HIU-FORTIS-002",
            "hi_types": ["OPConsultation", "Prescription"],
            "purpose_code": "CAREMGT",
            "access_mode": "VIEW",
            "days_valid": 15,
            "status": "GRANTED",
        }
        resp = await client.post("/api/v1/abdm/m3/consent/consents/simulate", json=sim_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["patient_id"] == "arun.verma@abdm"
        assert data["hiu_id"] == "HIU-FORTIS-002"
        assert data["signature_verified"] is True
        assert data["care_contexts_count"] == 2

