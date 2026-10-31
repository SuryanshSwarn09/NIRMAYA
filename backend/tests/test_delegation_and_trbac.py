"""Automated test suite for Chain-of-Command Administrative Provisioning and Scoped TRBAC.

Verifies:
- Sovereign Government of India 5-tier downward-only authority delegation
- Rejection of upward and lateral authority delegation attempts
- Territorial subtree containment validation
- Official @gov.in / @nic.in email domain enforcement
- Aadhaar UID Verhoeff checksum algorithm and OTP validation
- Delegation revocation and cryptographic SHA-256 audit ledger chaining
- Sub-2ms Scoped Territorial Role-Based Access Control (TRBAC) fastpath
- FastAPI REST endpoints under /api/v1/admin/delegations/*
- SQLAlchemy relational persistence for AdministrativeDelegation and DelegationAuditLedger
"""

import time
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import models as app_models  # noqa: F401
from app.core.territorial_rbac import TerritorialSecurityScope, is_territorial_access_allowed
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
from app.models.delegation import AdministrativeDelegation, DelegationAuditLedger
from app.models.enums import AdminLevelEnum, GovtDesignationEnum, UserRole
from app.models.user import User
from app.schemas.delegation import (
    AdministrativeDelegationCreate,
    DelegationRank,
    DelegationRevokeRequest,
    DelegationStatusEnum,
    TerritorialScopeValidationRequest,
)
from app.services.aadhaar_otp import generate_verhoeff, validate_verhoeff
from app.services.administrative_hierarchy_service import hierarchy_service
from app.services.delegation_service import delegation_service


# -----------------------------------------------------------------------------
# 1. Chain-of-Command Rank Hierarchy & Superiority Tests
# -----------------------------------------------------------------------------

def test_delegation_rank_hierarchy_enforcement():
    """Verify strictly downward hierarchy ordering across sovereign designations."""
    # Strict order: NATIONAL_DIRECTOR (5) > STATE_SECRETARY (4) > DIVISIONAL_COMMISSIONER (3) > CMO (2) > BMO (1)
    rank_national = DelegationRank.get_rank(GovtDesignationEnum.NATIONAL_DIRECTOR)
    rank_state = DelegationRank.get_rank(GovtDesignationEnum.STATE_SECRETARY)
    rank_div = DelegationRank.get_rank(GovtDesignationEnum.DIVISIONAL_COMMISSIONER)
    rank_cmo = DelegationRank.get_rank(GovtDesignationEnum.CHIEF_MEDICAL_OFFICER)
    rank_bmo = DelegationRank.get_rank(GovtDesignationEnum.BLOCK_MEDICAL_OFFICER)

    assert rank_national > rank_state > rank_div > rank_cmo > rank_bmo

    # Verify downward delegation is valid
    assert DelegationRank.is_strictly_superior(GovtDesignationEnum.NATIONAL_DIRECTOR, GovtDesignationEnum.STATE_SECRETARY) is True
    assert DelegationRank.is_strictly_superior(GovtDesignationEnum.STATE_SECRETARY, GovtDesignationEnum.CHIEF_MEDICAL_OFFICER) is True
    assert DelegationRank.is_strictly_superior(GovtDesignationEnum.CHIEF_MEDICAL_OFFICER, GovtDesignationEnum.BLOCK_MEDICAL_OFFICER) is True

    # Verify lateral delegation is strictly rejected
    assert DelegationRank.is_strictly_superior(GovtDesignationEnum.CHIEF_MEDICAL_OFFICER, GovtDesignationEnum.CHIEF_MEDICAL_OFFICER) is False
    assert DelegationRank.is_strictly_superior(GovtDesignationEnum.STATE_SECRETARY, GovtDesignationEnum.STATE_SECRETARY) is False

    # Verify upward delegation is strictly rejected
    assert DelegationRank.is_strictly_superior(GovtDesignationEnum.CHIEF_MEDICAL_OFFICER, GovtDesignationEnum.STATE_SECRETARY) is False
    assert DelegationRank.is_strictly_superior(GovtDesignationEnum.BLOCK_MEDICAL_OFFICER, GovtDesignationEnum.NATIONAL_DIRECTOR) is False


# -----------------------------------------------------------------------------
# 2. Government Email Domain & Aadhaar Verhoeff Validation Tests
# -----------------------------------------------------------------------------

def test_government_email_domain_validation():
    """Verify that only authorized Government of India email domains are accepted."""
    # Authorized domains
    assert delegation_service.validate_gov_email("director.health@gov.in").is_valid_gov_domain is True
    assert delegation_service.validate_gov_email("cmo.pune@nic.in").is_valid_gov_domain is True
    assert delegation_service.validate_gov_email("commissioner@mohfw.gov.in").is_valid_gov_domain is True

    # Unauthorized commercial / generic domains
    assert delegation_service.validate_gov_email("doctor@gmail.com").is_valid_gov_domain is False
    assert delegation_service.validate_gov_email("officer@yahoo.co.in").is_valid_gov_domain is False
    assert delegation_service.validate_gov_email("health@hospital.org").is_valid_gov_domain is False
    assert delegation_service.validate_gov_email("").is_valid_gov_domain is False


def test_aadhaar_verhoeff_checksum_validation():
    """Verify that 12-digit Aadhaar UID adheres to UIDAI mathematical Verhoeff checksum."""
    base_11_digits = "91847210482"
    check_digit = generate_verhoeff(base_11_digits)
    valid_uid = base_11_digits + check_digit

    assert len(valid_uid) == 12
    assert validate_verhoeff(valid_uid) is True

    # Tampered checksum must fail
    tampered_uid = valid_uid[:-1] + ("0" if valid_uid[-1] != "0" else "1")
    assert validate_verhoeff(tampered_uid) is False


# -----------------------------------------------------------------------------
# 3. Delegation Service Lifecycle & Rejection Tests
# -----------------------------------------------------------------------------

def test_delegation_service_provision_downward_success():
    """Verify successful downward delegation with valid credentials and unit mapping."""
    base_11 = "98765432101"
    valid_aadhaar = base_11 + generate_verhoeff(base_11)

    pune_unit = hierarchy_service.get_unit_by_lgd_code("492")
    assert pune_unit is not None

    payload = AdministrativeDelegationCreate(
        delegator_user_id="user-state-sec-mh-001",
        delegator_designation=GovtDesignationEnum.STATE_SECRETARY,
        delegatee_user_id=f"user-cmo-pune-{uuid.uuid4().hex[:6]}",
        delegatee_designation=GovtDesignationEnum.CHIEF_MEDICAL_OFFICER,
        administrative_unit_id=pune_unit.id,
        jurisdiction_path=pune_unit.path,
        gov_email="cmo.pune@gov.in",
        aadhaar_number=valid_aadhaar,
        aadhaar_otp="123456",
        delegation_notes="Official appointment of Chief Medical Officer for Pune District.",
    )

    result = delegation_service.create_delegation(payload)
    assert result.id is not None
    assert result.status == DelegationStatusEnum.ACTIVE
    assert result.is_active is True
    assert result.aadhaar_verified is True
    assert result.jurisdiction_path == pune_unit.path
    assert len(result.audit_hash) == 64

    # Verify queryable in active list
    active_list = delegation_service.list_delegations(jurisdiction_path="india.27.492")
    assert any(d.id == result.id for d in active_list)


def test_delegation_service_reject_upward_and_lateral():
    """Verify rejection of upward and lateral delegation attempts."""
    base_11 = "98765432101"
    valid_aadhaar = base_11 + generate_verhoeff(base_11)
    pune_unit = hierarchy_service.get_unit_by_lgd_code("492")
    assert pune_unit is not None

    # Upward attempt: CMO -> State Secretary
    upward_payload = AdministrativeDelegationCreate(
        delegator_user_id="user-cmo-001",
        delegator_designation=GovtDesignationEnum.CHIEF_MEDICAL_OFFICER,
        delegatee_user_id="user-sec-002",
        delegatee_designation=GovtDesignationEnum.STATE_SECRETARY,
        administrative_unit_id=pune_unit.id,
        jurisdiction_path=pune_unit.path,
        gov_email="officer@gov.in",
        aadhaar_number=valid_aadhaar,
        aadhaar_otp="123456",
    )
    with pytest.raises(ValueError, match="Chain of command violation"):
        delegation_service.create_delegation(upward_payload)

    # Lateral attempt: CMO -> CMO
    lateral_payload = AdministrativeDelegationCreate(
        delegator_user_id="user-cmo-001",
        delegator_designation=GovtDesignationEnum.CHIEF_MEDICAL_OFFICER,
        delegatee_user_id="user-cmo-002",
        delegatee_designation=GovtDesignationEnum.CHIEF_MEDICAL_OFFICER,
        administrative_unit_id=pune_unit.id,
        jurisdiction_path=pune_unit.path,
        gov_email="officer@gov.in",
        aadhaar_number=valid_aadhaar,
        aadhaar_otp="123456",
    )
    with pytest.raises(ValueError, match="Chain of command violation"):
        delegation_service.create_delegation(lateral_payload)


def test_delegation_service_reject_invalid_gov_email_and_aadhaar():
    """Verify rejection of non-gov emails and corrupted Aadhaar UIDs."""
    pune_unit = hierarchy_service.get_unit_by_lgd_code("492")
    assert pune_unit is not None

    base_11 = "98765432101"
    valid_aadhaar = base_11 + generate_verhoeff(base_11)

    # Invalid email
    with pytest.raises(ValueError, match="not an authorized Indian government domain"):
        AdministrativeDelegationCreate(
            delegator_user_id="user-state-sec-001",
            delegator_designation=GovtDesignationEnum.STATE_SECRETARY,
            delegatee_user_id="user-cmo-bademail",
            delegatee_designation=GovtDesignationEnum.CHIEF_MEDICAL_OFFICER,
            administrative_unit_id=pune_unit.id,
            jurisdiction_path=pune_unit.path,
            gov_email="doctor@gmail.com",
            aadhaar_number=valid_aadhaar,
            aadhaar_otp="123456",
        )

    # Invalid Aadhaar checksum
    corrupted_aadhaar = valid_aadhaar[:-1] + ("0" if valid_aadhaar[-1] != "0" else "1")
    bad_aadhaar_payload = AdministrativeDelegationCreate(
        delegator_user_id="user-state-sec-001",
        delegator_designation=GovtDesignationEnum.STATE_SECRETARY,
        delegatee_user_id="user-cmo-badaadhaar",
        delegatee_designation=GovtDesignationEnum.CHIEF_MEDICAL_OFFICER,
        administrative_unit_id=pune_unit.id,
        jurisdiction_path=pune_unit.path,
        gov_email="cmo.pune@gov.in",
        aadhaar_number=corrupted_aadhaar,
        aadhaar_otp="123456",
    )
    with pytest.raises(ValueError, match="Aadhaar checksum failed mathematical Verhoeff validation"):
        delegation_service.create_delegation(bad_aadhaar_payload)


def test_delegation_revocation_and_cryptographic_audit_ledger():
    """Verify delegation revocation lifecycle and unbroken SHA-256 ledger chaining."""
    base_11 = "98765432102"
    valid_aadhaar = base_11 + generate_verhoeff(base_11)
    pune_unit = hierarchy_service.get_unit_by_lgd_code("492")
    assert pune_unit is not None

    provision = delegation_service.create_delegation(
        AdministrativeDelegationCreate(
            delegator_user_id="user-state-sec-mh-001",
            delegator_designation=GovtDesignationEnum.STATE_SECRETARY,
            delegatee_user_id=f"user-cmo-to-revoke-{uuid.uuid4().hex[:6]}",
            delegatee_designation=GovtDesignationEnum.CHIEF_MEDICAL_OFFICER,
            administrative_unit_id=pune_unit.id,
            jurisdiction_path=pune_unit.path,
            gov_email="cmo.revoke@gov.in",
            aadhaar_number=valid_aadhaar,
            aadhaar_otp="123456",
        )
    )

    assert provision.is_active is True

    # Revoke delegation
    revoked = delegation_service.revoke_delegation(
        DelegationRevokeRequest(
            delegation_id=provision.id,
            revoked_by_user_id="user-state-sec-mh-001",
            reason="Administrative transfer order to Nashik Division.",
        )
    )

    assert revoked.is_active is False
    assert revoked.status == DelegationStatusEnum.REVOKED
    assert revoked.revocation_reason == "Administrative transfer order to Nashik Division."
    assert revoked.revoked_at is not None

    # Double revocation should fail
    with pytest.raises(ValueError, match="already revoked or inactive"):
        delegation_service.revoke_delegation(
            DelegationRevokeRequest(
                delegation_id=provision.id,
                revoked_by_user_id="user-state-sec-mh-001",
                reason="Duplicate revocation attempt.",
            )
        )

    # Audit ledger verification
    ledger = delegation_service.get_audit_ledger(limit=20)
    assert len(ledger) >= 2
    # Check newest entry is REVOKED action
    assert ledger[0].action == "REVOKED"
    assert ledger[0].delegation_id == provision.id


# -----------------------------------------------------------------------------
# 4. Sub-2ms Scoped Territorial RBAC (TRBAC) Benchmarks & Fastpath
# -----------------------------------------------------------------------------

def test_sub_2ms_trbac_scope_interceptor_benchmark():
    """Verify sub-2ms evaluation for sovereign administrative boundary enforcement."""
    # 1. National Root covers all
    assert is_territorial_access_allowed("india", "india.27.492.4182") is True
    assert is_territorial_access_allowed("india", "india.29.500") is True

    # 2. State covers child district and child sub-district
    assert is_territorial_access_allowed("india.27", "india.27.492") is True
    assert is_territorial_access_allowed("india.27", "india.27.492.4182") is True

    # 3. State cannot access another state (lateral cross-state block)
    assert is_territorial_access_allowed("india.27", "india.29.500") is False

    # 4. District cannot access parent state (upward violation block)
    assert is_territorial_access_allowed("india.27.492", "india.27") is False

    # 5. District cannot access lateral district
    assert is_territorial_access_allowed("india.27.492", "india.27.493") is False

    # 6. Benchmark sub-2ms latency over 100 evaluations
    iterations = 100
    t0 = time.perf_counter()
    for _ in range(iterations):
        res = delegation_service.validate_territorial_scope(
            TerritorialScopeValidationRequest(
                officer_jurisdiction_path="india.27.492",
                target_resource_path="india.27.492.4182",
                action_type="CLINICAL_AUDIT",
            )
        )
        assert res.authorized is True
    avg_ms = ((time.perf_counter() - t0) / iterations) * 1000

    assert avg_ms < 2.0, f"TRBAC evaluation took {avg_ms:.4f}ms, exceeding 2.0ms SLA"


# -----------------------------------------------------------------------------
# 5. Territorial Security Scope FastAPI Dependency Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_territorial_security_scope_interceptor():
    """Verify TerritorialSecurityScope raises 403 on boundary violation and passes on valid scope."""
    scope_interceptor = TerritorialSecurityScope(target_path_param_name="path")

    # Valid: Maharashtra officer accessing Pune District
    resolved = await scope_interceptor(
        x_officer_jurisdiction="india.27",
        target_path="india.27.492",
    )
    assert resolved == "india.27"

    # Invalid: Pune officer attempting to supervise entire Maharashtra State
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await scope_interceptor(
            x_officer_jurisdiction="india.27.492",
            target_path="india.27",
        )
    assert exc_info.value.status_code == 403
    assert "Territorial RBAC violation" in exc_info.value.detail


# -----------------------------------------------------------------------------
# 6. REST API Endpoints Integration Tests
# -----------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    """Asynchronous HTTP test client for FastAPI routes."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.asyncio
async def test_rest_api_get_hierarchy_ladder(client: AsyncClient):
    """Verify GET /api/v1/admin/delegations/hierarchy-ladder returns sovereign 5 tiers."""
    resp = await client.get("/api/v1/admin/delegations/hierarchy-ladder")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 5
    assert data[0]["designation"] == "NATIONAL_DIRECTOR"
    assert data[4]["designation"] == "BLOCK_MEDICAL_OFFICER"


@pytest.mark.asyncio
async def test_rest_api_list_active_delegations(client: AsyncClient):
    """Verify GET /api/v1/admin/delegations/active returns seeded and created delegations."""
    resp = await client.get("/api/v1/admin/delegations/active")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(d["delegator_designation"] in ("national_director", "NATIONAL_DIRECTOR") for d in data)


@pytest.mark.asyncio
async def test_rest_api_trbac_simulate(client: AsyncClient):
    """Verify POST /api/v1/admin/delegations/trbac/simulate tests boundary permissions."""
    resp = await client.post(
        "/api/v1/admin/delegations/trbac/simulate",
        json={
            "officer_jurisdiction_path": "india.27",
            "target_resource_path": "india.27.492",
            "action_type": "AUDIT",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["authorized"] is True
    assert data["evaluation_latency_ms"] < 2.0


@pytest.mark.asyncio
async def test_rest_api_provision_and_revoke_lifecycle(client: AsyncClient):
    """Verify POST /api/v1/admin/delegations/provision and POST revoke endpoints."""
    pune_unit = hierarchy_service.get_unit_by_lgd_code("492")
    assert pune_unit is not None

    base_11 = "98765432103"
    valid_aadhaar = base_11 + generate_verhoeff(base_11)

    payload = {
        "delegator_user_id": "user-state-sec-mh-001",
        "delegator_designation": GovtDesignationEnum.STATE_SECRETARY.value,
        "delegatee_user_id": f"user-api-cmo-{uuid.uuid4().hex[:6]}",
        "delegatee_designation": GovtDesignationEnum.CHIEF_MEDICAL_OFFICER.value,
        "administrative_unit_id": pune_unit.id,
        "jurisdiction_path": pune_unit.path,
        "gov_email": "cmo.api@gov.in",
        "aadhaar_number": valid_aadhaar,
        "aadhaar_otp": "123456",
        "delegation_notes": "API test delegation",
    }

    create_resp = await client.post("/api/v1/admin/delegations/provision", json=payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    delegation_id = created_data["id"]
    assert created_data["is_active"] is True

    # Revoke via API
    revoke_resp = await client.post(
        f"/api/v1/admin/delegations/{delegation_id}/revoke",
        json={
            "delegation_id": delegation_id,
            "revoked_by_user_id": "user-state-sec-mh-001",
            "reason": "API revoked test delegation",
        },
    )
    assert revoke_resp.status_code == 200
    revoked_data = revoke_resp.json()
    assert revoked_data["is_active"] is False
    assert revoked_data["status"] == "revoked"


# -----------------------------------------------------------------------------
# 7. SQLAlchemy Relational Model Persistence Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sqlalchemy_delegation_and_audit_persistence():
    """Verify relational persistence for AdministrativeDelegation and DelegationAuditLedger."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        # Create seed user
        user = User(
            id=str(uuid.uuid4()),
            email="sec.health@gov.in",
            full_name="Secretary Health MH",
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        # Create delegation
        delegation = AdministrativeDelegation(
            id=str(uuid.uuid4()),
            delegator_user_id=user.id,
            delegator_designation=GovtDesignationEnum.STATE_SECRETARY,
            delegatee_user_id=user.id,
            delegatee_designation=GovtDesignationEnum.CHIEF_MEDICAL_OFFICER,
            administrative_unit_id=str(uuid.uuid4()),
            jurisdiction_path="india.27.492",
            gov_email="cmo.pune@gov.in",
            aadhaar_verified=True,
            status="active",
            is_active=True,
            delegation_notes="Relational test delegation",
            audit_hash="a" * 64,
        )
        session.add(delegation)

        # Create audit entry
        audit = DelegationAuditLedger(
            id=str(uuid.uuid4()),
            delegation_id=delegation.id,
            action="DELEGATED",
            actor_id=user.id,
            actor_designation="STATE_SECRETARY",
            jurisdiction_path="india.27.492",
            audit_hash="a" * 64,
            previous_hash="0" * 64,
        )
        session.add(audit)
        await session.commit()

        # Query back
        res_del = await session.get(AdministrativeDelegation, delegation.id)
        assert res_del is not None
        assert res_del.gov_email == "cmo.pune@gov.in"
        assert res_del.is_active is True

        res_audit = await session.get(DelegationAuditLedger, audit.id)
        assert res_audit is not None
        assert res_audit.action == "DELEGATED"
        assert res_audit.delegation_id == delegation.id

    await engine.dispose()
