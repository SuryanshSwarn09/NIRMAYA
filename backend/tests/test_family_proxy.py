import os
from datetime import date, datetime, timezone
import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.schemas.family_proxy import (
    FamilyProxyCreateRequest,
    FamilyProxyResponse,
    ProxyAccessScopeEnum,
    ProxyAuditLogItem,
    ProxyRelationshipStatusEnum,
    RelationshipTypeEnum,
    VerificationAuthorityEnum,
)
from app.services.family_proxy_service import FamilyProxyService, family_proxy_service


# =============================================================================
# 1. Schema & Validation Tests
# =============================================================================

def test_proxy_schemas_valid_instantiation():
    """Verify that FamilyProxyCreateRequest and Response instantiate with valid fields."""
    req = FamilyProxyCreateRequest(
        guardian_patient_id="pat-guardian-01",
        dependent_patient_id="pat-child-02",
        relationship_type=RelationshipTypeEnum.CHILD_MINOR,
        verification_tier=VerificationAuthorityEnum.DIGILOCKER_BIRTH_CERTIFICATE,
        verification_document_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
        guardian_consent_attestation=True,
        dependent_dob_iso="2018-06-15",
    )
    assert req.guardian_patient_id == "pat-guardian-01"
    assert req.relationship_type == RelationshipTypeEnum.CHILD_MINOR
    assert req.guardian_consent_attestation is True

    res = FamilyProxyResponse(
        relationship_id="rel-test-01",
        guardian_patient_id="pat-guardian-01",
        dependent_patient_id="pat-child-02",
        relationship_type=RelationshipTypeEnum.CHILD_MINOR,
        verification_tier=VerificationAuthorityEnum.DIGILOCKER_BIRTH_CERTIFICATE,
        verification_document_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
        status=ProxyRelationshipStatusEnum.ACTIVE,
        authorized_at=datetime.now(timezone.utc),
        zero_contamination_isolated=True,
    )
    assert res.relationship_id == "rel-test-01"
    assert res.zero_contamination_isolated is True


def test_proxy_schemas_invalid_enum():
    """Verify that unsupported enum values trigger validation error."""
    with pytest.raises(ValidationError):
        FamilyProxyCreateRequest(
            guardian_patient_id="pat-g-01",
            dependent_patient_id="pat-d-02",
            relationship_type="INVALID_RELATIONSHIP",  # type: ignore
            verification_tier=VerificationAuthorityEnum.DIGILOCKER_BIRTH_CERTIFICATE,
            access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
            guardian_consent_attestation=True,
        )


# =============================================================================
# 2. Service Logic & Invariant Tests
# =============================================================================

def test_service_seed_data_loaded():
    """Verify default seeded proxy relationships and forensic audit logs."""
    service = FamilyProxyService()
    assert len(service._relationships) >= 2
    assert "rel-proxy-child-001" in service._relationships
    assert "rel-proxy-senior-002" in service._relationships

    child_rel = service._relationships["rel-proxy-child-001"]
    assert child_rel.relationship_type == RelationshipTypeEnum.CHILD_MINOR
    assert child_rel.zero_contamination_isolated is True

    logs = service.get_audit_logs()
    assert len(logs) >= 2


def test_service_zero_contamination_self_proxy_prevented():
    """Verify invariant: Guardian and dependent must be distinct identities."""
    service = FamilyProxyService()
    req = FamilyProxyCreateRequest(
        guardian_patient_id="pat-same-01",
        dependent_patient_id="pat-same-01",
        relationship_type=RelationshipTypeEnum.CHILD_MINOR,
        verification_tier=VerificationAuthorityEnum.DIGILOCKER_BIRTH_CERTIFICATE,
        access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
        guardian_consent_attestation=True,
    )
    with pytest.raises(ValueError) as exc_info:
        service.establish_proxy_relationship(req)
    assert "Zero-Contamination Invariant Violation" in str(exc_info.value)


def test_service_dpdp_act_sec9_consent_mandated():
    """Verify invariant: DPDP Act 2023 Sec 9 mandates verifiable guardian consent."""
    service = FamilyProxyService()
    req = FamilyProxyCreateRequest(
        guardian_patient_id="pat-guardian-01",
        dependent_patient_id="pat-child-02",
        relationship_type=RelationshipTypeEnum.CHILD_MINOR,
        verification_tier=VerificationAuthorityEnum.DIGILOCKER_BIRTH_CERTIFICATE,
        access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
        guardian_consent_attestation=False,  # Absent consent
    )
    with pytest.raises(ValueError) as exc_info:
        service.establish_proxy_relationship(req)
    assert "DPDP Act Sec 9 Violation" in str(exc_info.value)


def test_service_age_of_majority_enforcement():
    """Verify invariant: Child minor relationship requires dependent age < 18."""
    service = FamilyProxyService()
    # DOB: 25 years ago
    req = FamilyProxyCreateRequest(
        guardian_patient_id="pat-guardian-01",
        dependent_patient_id="pat-adult-02",
        relationship_type=RelationshipTypeEnum.CHILD_MINOR,
        verification_tier=VerificationAuthorityEnum.DIGILOCKER_BIRTH_CERTIFICATE,
        access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
        guardian_consent_attestation=True,
        dependent_dob_iso="2000-01-01",
    )
    with pytest.raises(ValueError) as exc_info:
        service.establish_proxy_relationship(req)
    assert "Age-of-Majority Invariant" in str(exc_info.value)


def test_service_establish_valid_child_minor_proxy():
    """Verify successful establishment of verified child minor proxy."""
    service = FamilyProxyService()
    req = FamilyProxyCreateRequest(
        guardian_patient_id="pat-guardian-10",
        dependent_patient_id="pat-child-20",
        relationship_type=RelationshipTypeEnum.CHILD_MINOR,
        verification_tier=VerificationAuthorityEnum.DIGILOCKER_BIRTH_CERTIFICATE,
        verification_document_hash="9a012b48c081294801928409182409182b0412984109481b049182b041298410",
        access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
        guardian_consent_attestation=True,
        dependent_dob_iso="2020-04-10",
    )
    rel = service.establish_proxy_relationship(req)
    assert rel.relationship_id.startswith("rel-proxy-")
    assert rel.status == ProxyRelationshipStatusEnum.ACTIVE
    assert rel.zero_contamination_isolated is True
    assert rel.dependent_age is not None and rel.dependent_age < 18

    # Verify audit log was appended
    logs = service.get_audit_logs(relationship_id=rel.relationship_id)
    assert len(logs) == 1
    assert logs[0].action_performed == "ESTABLISH_FAMILY_PROXY_RELATIONSHIP"


def test_service_establish_valid_senior_proxy():
    """Verify successful establishment of senior parent proxy."""
    service = FamilyProxyService()
    req = FamilyProxyCreateRequest(
        guardian_patient_id="pat-son-10",
        dependent_patient_id="pat-senior-father-20",
        relationship_type=RelationshipTypeEnum.PARENT_SENIOR,
        verification_tier=VerificationAuthorityEnum.AADHAAR_DEMOGRAPHIC_EKYC,
        verification_document_hash="b192840192840192840192840192840192840192840192840192840192840192",
        access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
        guardian_consent_attestation=True,
        dependent_dob_iso="1955-08-20",
    )
    rel = service.establish_proxy_relationship(req)
    assert rel.relationship_type == RelationshipTypeEnum.PARENT_SENIOR
    assert rel.status == ProxyRelationshipStatusEnum.ACTIVE


def test_service_list_dependents_for_guardian():
    """Verify retrieval of active dependents registered under guardian."""
    service = FamilyProxyService()
    dependents = service.list_dependents_for_guardian("pat-priya-sharma-01")
    assert len(dependents) >= 2
    dep_ids = [d.dependent_patient_id for d in dependents]
    assert "pat-aarav-sharma-02" in dep_ids
    assert "pat-kavita-sharma-03" in dep_ids


def test_service_revoke_relationship_success():
    """Verify that revoking a proxy updates status to REVOKED and appends audit entry."""
    service = FamilyProxyService()
    rel = service.revoke_proxy_relationship(
        relationship_id="rel-proxy-child-001",
        actor_id="pat-priya-sharma-01",
        reason="Child reached age of majority",
    )
    assert rel.status == ProxyRelationshipStatusEnum.REVOKED

    # Ensure it no longer appears in active list
    active = service.list_dependents_for_guardian("pat-priya-sharma-01")
    assert not any(d.relationship_id == "rel-proxy-child-001" for d in active)

    # Ensure revocation is in audit log
    logs = service.get_audit_logs("rel-proxy-child-001")
    revocation_logs = [l for l in logs if "REVOKE_PROXY_RELATIONSHIP" in l.action_performed]
    assert len(revocation_logs) == 1


def test_service_revoke_relationship_not_found():
    """Verify error raised when attempting to revoke non-existent relationship."""
    service = FamilyProxyService()
    with pytest.raises(KeyError):
        service.revoke_proxy_relationship("rel-nonexistent-999", "pat-actor-01")


def test_service_verify_access_permission_full_management():
    """Verify access permission evaluation for FULL_MANAGEMENT scope."""
    service = FamilyProxyService()
    allowed = service.verify_proxy_access_permission(
        guardian_id="pat-priya-sharma-01",
        dependent_id="pat-aarav-sharma-02",
        requested_action="VIEW_LAB_RESULTS",
    )
    assert allowed is True


def test_service_verify_access_permission_appointments_only_restriction():
    """Verify access scope restriction: APPOINTMENTS_ONLY rejects clinical notes view."""
    service = FamilyProxyService()
    # Create an appointments-only relationship
    req = FamilyProxyCreateRequest(
        guardian_patient_id="pat-g-appt-01",
        dependent_patient_id="pat-d-appt-02",
        relationship_type=RelationshipTypeEnum.SPOUSE,
        verification_tier=VerificationAuthorityEnum.SELF_ATTESTED_EMERGENCY,
        access_scope=ProxyAccessScopeEnum.APPOINTMENTS_ONLY,
        guardian_consent_attestation=True,
    )
    service.establish_proxy_relationship(req)

    # Scheduling appointment is allowed
    assert service.verify_proxy_access_permission(
        guardian_id="pat-g-appt-01",
        dependent_id="pat-d-appt-02",
        requested_action="SCHEDULE_APPOINTMENT",
    ) is True

    # Viewing clinical diagnostic records is denied
    assert service.verify_proxy_access_permission(
        guardian_id="pat-g-appt-01",
        dependent_id="pat-d-appt-02",
        requested_action="VIEW_CLINICAL_NOTES",
    ) is False


def test_service_verify_access_permission_unregistered_guardian_denied():
    """Verify that an unauthorized guardian is denied and logged in forensic ledger."""
    service = FamilyProxyService()
    allowed = service.verify_proxy_access_permission(
        guardian_id="pat-stranger-99",
        dependent_id="pat-aarav-sharma-02",
        requested_action="VIEW_PEDIATRIC_RECORDS",
    )
    assert allowed is False

    logs = service.get_audit_logs()
    denied_logs = [l for l in logs if l.actor_guardian_id == "pat-stranger-99" and not l.authorized]
    assert len(denied_logs) == 1


# =============================================================================
# 3. FastAPI Endpoint Integration Tests
# =============================================================================

@pytest.mark.asyncio
async def test_api_list_proxy_relationships(client: AsyncClient):
    """Verify GET /api/v1/patients/proxy/relationships endpoint."""
    resp = await client.get("/api/v1/patients/proxy/relationships")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_api_list_dependents_for_guardian(client: AsyncClient):
    """Verify GET /api/v1/patients/proxy/dependents endpoint."""
    resp = await client.get("/api/v1/patients/proxy/dependents?guardian_id=pat-priya-sharma-01")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert all(d["guardian_patient_id"] == "pat-priya-sharma-01" for d in data)


@pytest.mark.asyncio
async def test_api_establish_relationship_success(client: AsyncClient):
    """Verify POST /api/v1/patients/proxy/relationships creates relationship."""
    payload = {
        "guardian_patient_id": "pat-priya-sharma-01",
        "dependent_patient_id": "pat-diya-sharma-04",
        "relationship_type": "CHILD_MINOR",
        "verification_tier": "DIGILOCKER_BIRTH_CERTIFICATE",
        "verification_document_hash": "f1029481b049182b0412984109481b049182b0412984109481b049182b041298",
        "access_scope": "FULL_MANAGEMENT",
        "guardian_consent_attestation": True,
        "dependent_dob_iso": "2021-03-12",
    }
    resp = await client.post("/api/v1/patients/proxy/relationships", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["relationship_id"].startswith("rel-proxy-")
    assert data["zero_contamination_isolated"] is True
    assert data["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_api_establish_relationship_validation_failure(client: AsyncClient):
    """Verify POST /api/v1/patients/proxy/relationships returns 400 when invariants violated."""
    # Guardian == Dependent
    payload = {
        "guardian_patient_id": "pat-same-01",
        "dependent_patient_id": "pat-same-01",
        "relationship_type": "CHILD_MINOR",
        "verification_tier": "DIGILOCKER_BIRTH_CERTIFICATE",
        "access_scope": "FULL_MANAGEMENT",
        "guardian_consent_attestation": True,
    }
    resp = await client.post("/api/v1/patients/proxy/relationships", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    error_text = data.get("message") or data.get("detail", "")
    assert "Zero-Contamination Invariant" in error_text


@pytest.mark.asyncio
async def test_api_get_relationship_by_id(client: AsyncClient):
    """Verify GET /api/v1/patients/proxy/relationships/{id} returns details."""
    resp = await client.get("/api/v1/patients/proxy/relationships/rel-proxy-child-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["relationship_id"] == "rel-proxy-child-001"
    assert data["dependent_patient_id"] == "pat-aarav-sharma-02"


@pytest.mark.asyncio
async def test_api_get_relationship_not_found(client: AsyncClient):
    """Verify GET /api/v1/patients/proxy/relationships/{id} returns 404 for unknown ID."""
    resp = await client.get("/api/v1/patients/proxy/relationships/rel-unknown-999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_api_revoke_relationship(client: AsyncClient):
    """Verify POST /api/v1/patients/proxy/relationships/{id}/revoke updates status."""
    payload = {
        "actor_id": "pat-priya-sharma-01",
        "reason": "Family proxy update",
    }
    resp = await client.post(
        "/api/v1/patients/proxy/relationships/rel-proxy-senior-002/revoke",
        json=payload,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "REVOKED"


@pytest.mark.asyncio
async def test_api_get_audit_trail(client: AsyncClient):
    """Verify GET /api/v1/patients/proxy/relationships/{id}/audit returns logs."""
    resp = await client.get("/api/v1/patients/proxy/relationships/rel-proxy-child-001/audit")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["relationship_id"] == "rel-proxy-child-001"


@pytest.mark.asyncio
async def test_api_authorize_action(client: AsyncClient):
    """Verify POST /api/v1/patients/proxy/authorize-action validates permission."""
    payload = {
        "guardian_id": "pat-priya-sharma-01",
        "dependent_id": "pat-aarav-sharma-02",
        "action": "SCHEDULE_PEDIATRIC_OPD",
    }
    resp = await client.post("/api/v1/patients/proxy/authorize-action", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["authorized"] is True
    assert data["action"] == "SCHEDULE_PEDIATRIC_OPD"


# =============================================================================
# 4. Documentation & Architectural Proof Checks
# =============================================================================

def test_family_proxy_architecture_doc_exists():
    """Verify that docs/reports/nirmaya-family-proxy-access-architecture.md exists and is valid."""
    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "docs",
        "reports",
        "nirmaya-family-proxy-access-architecture.md",
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "DPDP Act 2023" in content
    assert "Section 9" in content
    assert "Zero Record Contamination" in content
    assert "Multi-Tier Verification Authority" in content


def test_week_17_journey_doc_exists():
    """Verify that docs/journey/month-4/week-17.md exists and outlines Week 17."""
    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "docs",
        "journey",
        "month-4",
        "week-17.md",
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Week 17: Dependent & Family Health Proxy" in content
    assert "Day 81" in content

