import hashlib
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.schemas.guardian_conflict import (
    ConflictResolutionPolicyEnum,
    CustodyModeEnum,
    DualSignConsentArtifactRequest,
    DualSignConsentArtifactResponse,
    DualSignCounterSignatureRequest,
    DualSignStatusEnum,
    GuardianActionTypeEnum,
    GuardianConflictResolutionRequest,
    GuardianConflictResolutionResponse,
    GuardianDisputeStatusEnum,
    MultiGuardianRelationshipSummary,
)
from app.services.guardian_conflict_service import (
    GuardianConflictService,
    guardian_conflict_service,
)


@pytest.fixture(autouse=True)
def reset_conflict_service_state():
    """Ensure clean service state before and after each test."""
    guardian_conflict_service.reset_state()
    yield
    guardian_conflict_service.reset_state()


# ==============================================================================
# 1. Multi-Guardian Discovery Tests
# ==============================================================================

def test_get_guardians_for_dependent_pediatric_seed():
    """Verify concurrent guardians Dr. Priya Sharma and Vikram Sharma are discovered for Aarav Sharma."""
    summary = guardian_conflict_service.get_guardians_for_dependent("pat-aarav-sharma-02")
    assert summary.dependent_patient_id == "pat-aarav-sharma-02"
    assert summary.dependent_name == "Aarav Sharma"
    assert len(summary.active_guardians) == 2

    mother = next((g for g in summary.active_guardians if g.relationship_type == "MOTHER"), None)
    father = next((g for g in summary.active_guardians if g.relationship_type == "FATHER"), None)

    assert mother is not None
    assert mother.name == "Dr. Priya Sharma"
    assert mother.verification_tier == "DIGILOCKER_BIRTH_CERTIFICATE"
    assert mother.priority_tier == 1

    assert father is not None
    assert father.name == "Vikram Sharma"
    assert father.verification_tier == "AADHAAR_DEMOGRAPHIC_EKYC"
    assert father.priority_tier == 1

    assert summary.custody_mode == CustodyModeEnum.JOINT_CONCURRENT
    assert summary.dispute_flag_active is False
    assert summary.active_dispute_ticket_id is None


def test_get_guardians_for_dependent_alias_resolution():
    """Verify alias 'pat-pediatric-001' maps cleanly to Aarav Sharma."""
    summary = guardian_conflict_service.get_guardians_for_dependent("pat-pediatric-001")
    assert summary.dependent_patient_id == "pat-aarav-sharma-02"
    assert summary.dependent_name == "Aarav Sharma"
    assert len(summary.active_guardians) == 2


def test_get_guardians_for_senior_dependent():
    """Verify senior Kavita Sharma has registered daughter Dr. Priya Sharma."""
    summary = guardian_conflict_service.get_guardians_for_dependent("pat-kavita-sharma-03")
    assert summary.dependent_patient_id == "pat-kavita-sharma-03"
    assert summary.dependent_name == "Kavita Sharma"
    assert len(summary.active_guardians) == 1
    assert summary.active_guardians[0].relationship_type == "DAUGHTER"
    assert summary.custody_mode == CustodyModeEnum.JOINT_CONCURRENT


def test_get_guardians_for_unregistered_arbitrary_dependent():
    """Verify fallback summary generation for unknown patient ID."""
    summary = guardian_conflict_service.get_guardians_for_dependent("pat-unknown-999")
    assert summary.dependent_patient_id == "pat-unknown-999"
    assert len(summary.active_guardians) >= 1
    assert summary.custody_mode == CustodyModeEnum.JOINT_CONCURRENT
    assert summary.dispute_flag_active is False


# ==============================================================================
# 2. Concurrency Arbitration & Pessimistic Revocation Invariant Tests
# ==============================================================================

def test_pessimistic_revocation_prevalence_unilateral():
    """Verify that any verified guardian can unilaterally and immediately revoke consent."""
    req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-vikram-sharma-01",  # Father revokes
        action_type=GuardianActionTypeEnum.REVOKE_CONSENT,
        target_artifact_id="art-delegated-001",
        proposed_policy=ConflictResolutionPolicyEnum.PESSIMISTIC_REVOCATION_PREVALENCE,
        justification="Parent withdrew consent for data sharing with external clinic",
        guardian_signature_attestation=True,
    )
    result = guardian_conflict_service.arbitrate_action(req)

    assert result.action_type == GuardianActionTypeEnum.REVOKE_CONSENT
    assert result.effective_policy == ConflictResolutionPolicyEnum.PESSIMISTIC_REVOCATION_PREVALENCE
    assert result.dispute_status == GuardianDisputeStatusEnum.RESOLVED
    assert "Pessimistic Revocation Prevailed" in result.arbitrated_action_result
    assert len(result.audit_hash) == 64


def test_pessimistic_revocation_prevails_even_during_active_dispute():
    """Verify that even when custody is contested, a revocation action is honored for privacy protection."""
    # First raise a dispute to freeze custody
    disp_req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-vikram-sharma-01",
        action_type=GuardianActionTypeEnum.RAISE_LEGAL_DISPUTE,
        justification="Custody dispute ongoing",
        guardian_signature_attestation=True,
    )
    guardian_conflict_service.arbitrate_action(disp_req)

    # Now attempt pessimistic revocation
    rev_req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-priya-sharma-01",
        action_type=GuardianActionTypeEnum.REVOKE_CONSENT,
        target_artifact_id="art-delegated-001",
        justification="Revoking consent during litigation",
        guardian_signature_attestation=True,
    )
    result = guardian_conflict_service.arbitrate_action(rev_req)
    assert result.effective_policy == ConflictResolutionPolicyEnum.PESSIMISTIC_REVOCATION_PREVALENCE
    assert "Pessimistic Revocation Prevailed" in result.arbitrated_action_result


def test_arbitrate_signature_attestation_mandatory():
    """Verify that omitting digital signature attestation raises ValueError under DPDP Act Sec 9."""
    req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-priya-sharma-01",
        action_type=GuardianActionTypeEnum.GRANT_CONSENT,
        justification="Routine consent grant",
        guardian_signature_attestation=False,  # Invalid
    )
    with pytest.raises(ValueError, match="Digital signature attestation is mandatory"):
        guardian_conflict_service.arbitrate_action(req)


def test_arbitrate_unilateral_grant_under_joint_concurrent():
    """Verify that unilateral consent grant succeeds when custody is in JOINT_CONCURRENT mode."""
    req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-priya-sharma-01",
        action_type=GuardianActionTypeEnum.GRANT_CONSENT,
        justification="Routine pediatric diagnostic consent",
        guardian_signature_attestation=True,
    )
    result = guardian_conflict_service.arbitrate_action(req)
    assert result.effective_policy == ConflictResolutionPolicyEnum.PRIMARY_GUARDIAN_ARBITRATION
    assert result.dispute_status == GuardianDisputeStatusEnum.RESOLVED
    assert "JOINT_CONCURRENT" in result.arbitrated_action_result
    assert len(result.locked_resources) == 0


def test_arbitrate_unilateral_grant_blocked_when_dual_sign_required():
    """Verify that unilateral consent grant is blocked when governance requires dual signatures."""
    # Switch to DUAL_SIGNATURE_REQUIRED
    mode_req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-priya-sharma-01",
        action_type=GuardianActionTypeEnum.CHANGE_CUSTODY_MODE,
        justification="Enforcing dual sign policy",
        guardian_signature_attestation=True,
    )
    guardian_conflict_service.arbitrate_action(mode_req)

    # Now attempt unilateral grant
    grant_req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-priya-sharma-01",
        action_type=GuardianActionTypeEnum.GRANT_CONSENT,
        justification="Unilateral major surgery consent attempt",
        guardian_signature_attestation=True,
    )
    result = guardian_conflict_service.arbitrate_action(grant_req)
    assert result.effective_policy == ConflictResolutionPolicyEnum.DUAL_GUARDIAN_CO_SIGNING
    assert result.dispute_status == GuardianDisputeStatusEnum.PENDING_MUTUAL_APPROVAL
    assert "Unilateral consent blocked: Dual-Signature required" in result.arbitrated_action_result


# ==============================================================================
# 3. Custodial Legal Dispute & Sub-Judice Freeze Tests
# ==============================================================================

def test_raise_custodial_dispute_active_dispute():
    """Verify that raising a dispute transitions dependent to DISPUTED_LOCKED and locks proxy resources."""
    req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-vikram-sharma-01",
        action_type=GuardianActionTypeEnum.RAISE_LEGAL_DISPUTE,
        justification="Contesting medical proxy authority under Guardians and Wards Act 1890",
        guardian_signature_attestation=True,
    )
    result = guardian_conflict_service.arbitrate_action(req)

    assert result.dispute_status == GuardianDisputeStatusEnum.ACTIVE_DISPUTE
    assert result.effective_policy == ConflictResolutionPolicyEnum.DISPUTED_CUSTODY_FREEZE
    assert len(result.locked_resources) > 0
    assert any("/records" in r for r in result.locked_resources)

    # Verify dependent summary reflects dispute
    summary = guardian_conflict_service.get_guardians_for_dependent("pat-aarav-sharma-02")
    assert summary.custody_mode == CustodyModeEnum.DISPUTED_LOCKED
    assert summary.dispute_flag_active is True
    assert summary.active_dispute_ticket_id == result.ticket_id


def test_raise_custodial_dispute_court_sub_judice():
    """Verify that providing legal_order_reference marks dispute status as COURT_SUB_JUDICE."""
    req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-vikram-sharma-01",
        action_type=GuardianActionTypeEnum.RAISE_LEGAL_DISPUTE,
        legal_order_reference="HC-DEL-FAM-2026-90412",
        justification="Interim stay by Delhi High Court Family Division",
        guardian_signature_attestation=True,
    )
    result = guardian_conflict_service.arbitrate_action(req)

    assert result.dispute_status == GuardianDisputeStatusEnum.COURT_SUB_JUDICE
    assert result.effective_policy == ConflictResolutionPolicyEnum.DISPUTED_CUSTODY_FREEZE


def test_arbitrate_non_revocation_blocked_during_active_dispute():
    """Verify that non-emergency actions (like GRANT_CONSENT) are rejected during active custody dispute."""
    # 1. Raise dispute
    disp_req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-vikram-sharma-01",
        action_type=GuardianActionTypeEnum.RAISE_LEGAL_DISPUTE,
        legal_order_reference="HC-DEL-2026",
        justification="Sub judice contest",
        guardian_signature_attestation=True,
    )
    guardian_conflict_service.arbitrate_action(disp_req)

    # 2. Attempt GRANT_CONSENT
    grant_req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-priya-sharma-01",
        action_type=GuardianActionTypeEnum.GRANT_CONSENT,
        justification="Trying to share records despite contest",
        guardian_signature_attestation=True,
    )
    result = guardian_conflict_service.arbitrate_action(grant_req)
    assert result.effective_policy == ConflictResolutionPolicyEnum.DISPUTED_CUSTODY_FREEZE
    assert result.dispute_status == GuardianDisputeStatusEnum.COURT_SUB_JUDICE
    assert "Action rejected: Dependent custody is actively contested" in result.arbitrated_action_result
    assert len(result.locked_resources) > 0


def test_resolve_custodial_dispute_restores_joint_concurrent():
    """Verify that resolving a dispute clears the lock and restores JOINT_CONCURRENT mode."""
    # 1. Raise dispute
    guardian_conflict_service.arbitrate_action(
        GuardianConflictResolutionRequest(
            dependent_patient_id="pat-aarav-sharma-02",
            initiating_guardian_id="pat-vikram-sharma-01",
            action_type=GuardianActionTypeEnum.RAISE_LEGAL_DISPUTE,
            justification="Custody dispute",
            guardian_signature_attestation=True,
        )
    )

    # 2. Resolve dispute
    resolve_req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-priya-sharma-01",
        action_type=GuardianActionTypeEnum.RESOLVE_DISPUTE,
        legal_order_reference="SETTLEMENT-DECREE-2026-01",
        justification="Mutual consent agreement entered in court",
        guardian_signature_attestation=True,
    )
    res = guardian_conflict_service.arbitrate_action(resolve_req)
    assert res.action_type == GuardianActionTypeEnum.RESOLVE_DISPUTE
    assert res.dispute_status == GuardianDisputeStatusEnum.RESOLVED
    assert "Dispute successfully resolved" in res.arbitrated_action_result

    # Verify summary
    summary = guardian_conflict_service.get_guardians_for_dependent("pat-aarav-sharma-02")
    assert summary.custody_mode == CustodyModeEnum.JOINT_CONCURRENT
    assert summary.dispute_flag_active is False


# ==============================================================================
# 4. Two-Phase Dual-Signing Lifecycle Tests
# ==============================================================================

def test_create_dual_sign_request_lifecycle():
    """Verify initiation of two-phase co-signing consent artifact."""
    req = DualSignConsentArtifactRequest(
        artifact_id="art-dual-test-001",
        dependent_patient_id="pat-aarav-sharma-02",
        primary_guardian_id="pat-priya-sharma-01",
        co_guardian_id="pat-vikram-sharma-01",
        purpose="CAREMGT",
        hi_types=["DiagnosticReport", "Prescription"],
        primary_signature_attestation=True,
    )
    artifact = guardian_conflict_service.create_dual_sign_request(req)

    assert artifact.artifact_id == "art-dual-test-001"
    assert artifact.status == DualSignStatusEnum.PENDING_CO_SIGNATURE
    assert artifact.primary_signature_hash is not None
    assert len(artifact.primary_signature_hash) == 64
    assert artifact.co_signature_hash is None
    assert artifact.composite_signature_hash is None
    assert artifact.authorized_at is None


def test_create_dual_sign_request_attestation_required():
    """Verify primary digital signature attestation is required under DPDP Act Sec 9."""
    req = DualSignConsentArtifactRequest(
        artifact_id="art-dual-test-002",
        dependent_patient_id="pat-aarav-sharma-02",
        primary_guardian_id="pat-priya-sharma-01",
        co_guardian_id="pat-vikram-sharma-01",
        primary_signature_attestation=False,
    )
    with pytest.raises(ValueError, match="Primary guardian digital signature attestation is required"):
        guardian_conflict_service.create_dual_sign_request(req)


def test_counter_sign_dual_artifact_success():
    """Verify co-guardian can counter-sign, computing composite hash and reaching FULLY_AUTHORIZED status."""
    # Create request
    init_req = DualSignConsentArtifactRequest(
        artifact_id="art-dual-test-003",
        dependent_patient_id="pat-aarav-sharma-02",
        primary_guardian_id="pat-priya-sharma-01",
        co_guardian_id="pat-vikram-sharma-01",
        purpose="CAREMGT",
        primary_signature_attestation=True,
    )
    guardian_conflict_service.create_dual_sign_request(init_req)

    # Counter-sign
    counter_req = DualSignCounterSignatureRequest(
        artifact_id="art-dual-test-003",
        co_guardian_id="pat-vikram-sharma-01",
        co_signature_attestation=True,
        comments="Approved joint management of minor pediatric records",
    )
    authorized = guardian_conflict_service.counter_sign_dual_artifact(counter_req)

    assert authorized.status == DualSignStatusEnum.FULLY_AUTHORIZED
    assert authorized.co_signature_hash is not None
    assert len(authorized.co_signature_hash) == 64
    assert authorized.composite_signature_hash is not None
    assert len(authorized.composite_signature_hash) == 64
    assert authorized.authorized_at is not None


def test_counter_sign_unauthorized_signer_rejected():
    """Verify that a stranger/unauthorized guardian cannot counter-sign."""
    init_req = DualSignConsentArtifactRequest(
        artifact_id="art-dual-test-004",
        dependent_patient_id="pat-aarav-sharma-02",
        primary_guardian_id="pat-priya-sharma-01",
        co_guardian_id="pat-vikram-sharma-01",
        primary_signature_attestation=True,
    )
    guardian_conflict_service.create_dual_sign_request(init_req)

    unauthorized_req = DualSignCounterSignatureRequest(
        artifact_id="art-dual-test-004",
        co_guardian_id="pat-stranger-999",
        co_signature_attestation=True,
    )
    with pytest.raises(ValueError, match="does not match designated co-guardian"):
        guardian_conflict_service.counter_sign_dual_artifact(unauthorized_req)


def test_counter_sign_nonexistent_artifact_fails():
    """Verify that counter-signing a nonexistent artifact raises ValueError."""
    req = DualSignCounterSignatureRequest(
        artifact_id="art-nonexistent-999",
        co_guardian_id="pat-vikram-sharma-01",
        co_signature_attestation=True,
    )
    with pytest.raises(ValueError, match="not found"):
        guardian_conflict_service.counter_sign_dual_artifact(req)


def test_counter_sign_attestation_required():
    """Verify that counter-signing without digital attestation raises ValueError."""
    req = DualSignCounterSignatureRequest(
        artifact_id="art-dual-seed-001",
        co_guardian_id="pat-vikram-sharma-01",
        co_signature_attestation=False,
    )
    with pytest.raises(ValueError, match="Co-guardian digital signature attestation is required"):
        guardian_conflict_service.counter_sign_dual_artifact(req)


def test_counter_sign_already_authorized_artifact_fails():
    """Verify that an artifact already FULLY_AUTHORIZED cannot be counter-signed again."""
    counter_req = DualSignCounterSignatureRequest(
        artifact_id="art-dual-seed-001",
        co_guardian_id="pat-vikram-sharma-01",
        co_signature_attestation=True,
    )
    guardian_conflict_service.counter_sign_dual_artifact(counter_req)

    # Attempt to sign again
    with pytest.raises(ValueError, match="not pending co-signature"):
        guardian_conflict_service.counter_sign_dual_artifact(counter_req)


# ==============================================================================
# 5. Dispute Listing & Audit Ledger Tests
# ==============================================================================

def test_list_dispute_tickets_filtering():
    """Verify dispute tickets can be listed and filtered by dependent patient ID."""
    req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-vikram-sharma-01",
        action_type=GuardianActionTypeEnum.RAISE_LEGAL_DISPUTE,
        justification="Test dispute",
        guardian_signature_attestation=True,
    )
    guardian_conflict_service.arbitrate_action(req)

    all_tickets = guardian_conflict_service.list_dispute_tickets()
    assert len(all_tickets) >= 1

    aarav_tickets = guardian_conflict_service.list_dispute_tickets("pat-aarav-sharma-02")
    assert len(aarav_tickets) >= 1

    other_tickets = guardian_conflict_service.list_dispute_tickets("pat-kavita-sharma-03")
    assert len(other_tickets) == 0


def test_audit_ledger_immutable_trail():
    """Verify audit ledger captures arbitration and dual-signing events with SHA-256 hashes."""
    req = GuardianConflictResolutionRequest(
        dependent_patient_id="pat-aarav-sharma-02",
        initiating_guardian_id="pat-priya-sharma-01",
        action_type=GuardianActionTypeEnum.REVOKE_CONSENT,
        justification="Revoking for audit verification",
        guardian_signature_attestation=True,
    )
    guardian_conflict_service.arbitrate_action(req)

    ledger = guardian_conflict_service.get_audit_ledger("pat-aarav-sharma-02")
    assert len(ledger) >= 1
    last_entry = ledger[-1]
    assert last_entry["event_type"] == "CONFLICT_ARBITRATION"
    assert "audit_hash" in last_entry
    assert len(last_entry["audit_hash"]) == 64


# ==============================================================================
# 6. FastAPI REST Endpoints Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_api_get_guardians_endpoint():
    """Test GET /api/v1/patients/proxy/conflict/dependents/{id}/guardians."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/patients/proxy/conflict/dependents/pat-aarav-sharma-02/guardians")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["dependent_patient_id"] == "pat-aarav-sharma-02"
        assert len(data["active_guardians"]) == 2
        assert resp.headers.get("X-Multi-Guardian-Engine") == "active"
        assert resp.headers.get("X-Custody-Governance") == "JOINT_CONCURRENT"


@pytest.mark.asyncio
async def test_api_arbitrate_pessimistic_revocation_endpoint():
    """Test POST /api/v1/patients/proxy/conflict/arbitrate for unilateral revocation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "dependent_patient_id": "pat-aarav-sharma-02",
            "initiating_guardian_id": "pat-vikram-sharma-01",
            "action_type": "REVOKE_CONSENT",
            "target_artifact_id": "art-delegated-001",
            "proposed_policy": "PESSIMISTIC_REVOCATION_PREVALENCE",
            "justification": "Parental revocation of external clinic access",
            "guardian_signature_attestation": True,
        }
        resp = await client.post("/api/v1/patients/proxy/conflict/arbitrate", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["effective_policy"] == "PESSIMISTIC_REVOCATION_PREVALENCE"
        assert resp.headers.get("X-Conflict-Arbitration-Ticket") is not None
        assert resp.headers.get("X-Pessimistic-Resolution") == "PESSIMISTIC_REVOCATION_PREVALENCE"


@pytest.mark.asyncio
async def test_api_arbitrate_missing_attestation_fails():
    """Test POST /api/v1/patients/proxy/conflict/arbitrate rejects un-attested request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "dependent_patient_id": "pat-aarav-sharma-02",
            "initiating_guardian_id": "pat-priya-sharma-01",
            "action_type": "GRANT_CONSENT",
            "justification": "Missing signature attestation",
            "guardian_signature_attestation": False,
        }
        resp = await client.post("/api/v1/patients/proxy/conflict/arbitrate", json=payload)
        assert resp.status_code == 400
        error_text = str(resp.json()).lower()
        assert "attestation" in error_text


@pytest.mark.asyncio
async def test_api_raise_and_resolve_dispute_endpoint():
    """Test POST /dispute/raise and POST /dispute/resolve endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Raise dispute
        raise_payload = {
            "dependent_patient_id": "pat-aarav-sharma-02",
            "initiating_guardian_id": "pat-vikram-sharma-01",
            "justification": "Filing contest in family court",
            "legal_order_reference": "HC-FAM-2026-8812",
            "guardian_signature_attestation": True,
        }
        raise_resp = await client.post("/api/v1/patients/proxy/conflict/dispute/raise", json=raise_payload)
        assert raise_resp.status_code == 200
        raise_data = raise_resp.json()["data"]
        assert raise_data["dispute_status"] == "COURT_SUB_JUDICE"
        assert raise_data["effective_policy"] == "DISPUTED_CUSTODY_FREEZE"

        # 2. List disputes
        list_resp = await client.get("/api/v1/patients/proxy/conflict/disputes?dependent_patient_id=pat-aarav-sharma-02")
        assert list_resp.status_code == 200
        assert len(list_resp.json()["data"]) >= 1

        # 3. Resolve dispute
        resolve_payload = {
            "dependent_patient_id": "pat-aarav-sharma-02",
            "initiating_guardian_id": "pat-priya-sharma-01",
            "justification": "Parties entered into registered settlement agreement",
            "legal_order_reference": "HC-FAM-SETTLE-2026",
            "guardian_signature_attestation": True,
        }
        resolve_resp = await client.post("/api/v1/patients/proxy/conflict/dispute/resolve", json=resolve_payload)
        assert resolve_resp.status_code == 200
        resolve_data = resolve_resp.json()["data"]
        assert resolve_data["dispute_status"] == "RESOLVED"
        assert "restored to JOINT_CONCURRENT" in resolve_data["arbitrated_action_result"]


@pytest.mark.asyncio
async def test_api_dual_sign_e2e_flow():
    """Test POST /dual-sign/create and POST /dual-sign/{id}/counter-sign endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create dual sign
        create_payload = {
            "artifact_id": "art-dual-api-001",
            "dependent_patient_id": "pat-aarav-sharma-02",
            "primary_guardian_id": "pat-priya-sharma-01",
            "co_guardian_id": "pat-vikram-sharma-01",
            "purpose": "CAREMGT",
            "hi_types": ["DiagnosticReport"],
            "primary_signature_attestation": True,
        }
        c_resp = await client.post("/api/v1/patients/proxy/conflict/dual-sign/create", json=create_payload)
        assert c_resp.status_code == 200
        c_data = c_resp.json()["data"]
        assert c_data["status"] == "PENDING_CO_SIGNATURE"
        assert c_data["primary_signature_hash"] is not None

        # Counter sign
        counter_payload = {
            "artifact_id": "art-dual-api-001",
            "co_guardian_id": "pat-vikram-sharma-01",
            "co_signature_attestation": True,
            "comments": "Approved counter signature via API",
        }
        s_resp = await client.post(
            "/api/v1/patients/proxy/conflict/dual-sign/art-dual-api-001/counter-sign",
            json=counter_payload,
        )
        assert s_resp.status_code == 200
        s_data = s_resp.json()["data"]
        assert s_data["status"] == "FULLY_AUTHORIZED"
        assert s_data["composite_signature_hash"] is not None
        assert s_data["authorized_at"] is not None


@pytest.mark.asyncio
async def test_api_audit_ledger_endpoint():
    """Test GET /api/v1/patients/proxy/conflict/audit-ledger."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/patients/proxy/conflict/audit-ledger?dependent_patient_id=pat-aarav-sharma-02")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
