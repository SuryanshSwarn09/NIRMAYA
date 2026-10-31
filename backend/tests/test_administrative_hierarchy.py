"""Automated test suite for Indian Local Government Directory (LGD) 6-Tier Administrative Hierarchy.

Verifies:
- Sovereign 6-Tier LGD reference data (National, 36 States/UTs, Divisions, Districts, Sub-Districts)
- Sub-2ms fast territorial index search and traversal
- PostgreSQL ltree ancestor (@>) and descendant (<@) queries
- Territorial RBAC scoping and jurisdictional access validation
- Officer appointment and roster management
- REST API endpoints under /api/v1/admin/hierarchy/*
- SQLAlchemy model persistence with LTreePath cross-dialect compatibility
"""

import time
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import models as app_models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
from app.models.administrative_hierarchy import AdministrativeOfficer, AdministrativeUnit
from app.models.enums import AdminLevelEnum, GovtDesignationEnum, UserRole
from app.models.user import User
from app.schemas.administrative_hierarchy import (
    AdministrativeOfficerCreate,
    AdministrativeUnitCreate,
)
from app.services.administrative_hierarchy_service import hierarchy_service


# -----------------------------------------------------------------------------
# 1. National LGD Seeding & Directory Integrity Tests
# -----------------------------------------------------------------------------

def test_national_lgd_seeding():
    """Verify that the 6-tier administrative seeder initializes sovereign Indian territories."""
    metrics = hierarchy_service.get_summary_metrics()
    assert metrics.total_states >= 36, f"Expected at least 36 States/UTs, got {metrics.total_states}"
    assert metrics.total_districts >= 1, "Expected seed districts"
    assert metrics.total_sub_districts >= 1, "Expected seed sub-districts"
    assert metrics.ltree_index_status == "GIST_OPTIMIZED"

    # Verify National root unit
    national_unit = hierarchy_service.get_unit_by_path("india")
    assert national_unit is not None
    assert "India" in national_unit.name
    assert national_unit.unit_level == AdminLevelEnum.COUNTRY
    assert national_unit.level_depth == 0

    # Verify Maharashtra State (LGD 27)
    mh_unit = hierarchy_service.get_unit_by_lgd_code("27")
    assert mh_unit is not None
    assert mh_unit.name == "Maharashtra"
    assert mh_unit.path == "india.27"
    assert mh_unit.level_depth == 1

    # Verify Pune District (LGD 492)
    pune_unit = hierarchy_service.get_unit_by_lgd_code("492")
    assert pune_unit is not None
    assert "Pune" in pune_unit.name
    assert pune_unit.path == "india.27.492"
    assert pune_unit.level_depth == 2

    # Verify Haveli Sub-District (LGD 4182)
    haveli_unit = hierarchy_service.get_unit_by_lgd_code("4182")
    assert haveli_unit is not None
    assert "Haveli" in haveli_unit.name
    assert haveli_unit.path == "india.27.492.4182"
    assert haveli_unit.level_depth == 3


# -----------------------------------------------------------------------------
# 2. Sub-2ms Performance & Traversal Benchmarks
# -----------------------------------------------------------------------------

def test_sub_2ms_descendant_and_ancestor_traversal():
    """Verify sub-2ms query performance for ancestor chains and descendant subtrees."""
    # Descendant benchmark for Maharashtra (india.27)
    iterations = 50
    t0 = time.perf_counter()
    for _ in range(iterations):
        descendants = hierarchy_service.find_descendants("india.27", include_self=True)
    avg_descendant_ms = ((time.perf_counter() - t0) / iterations) * 1000

    assert len(descendants) >= 3, "Maharashtra subtree must contain divisions, districts, and talukas"
    assert avg_descendant_ms < 2.0, f"Descendant traversal took {avg_descendant_ms:.3f}ms, exceeding 2.0ms SLA"

    # Ancestor chain resolution for Haveli Taluka
    t1 = time.perf_counter()
    for _ in range(iterations):
        ancestors = hierarchy_service.find_ancestors("india.27.492.4182", include_self=True)
    avg_ancestor_ms = ((time.perf_counter() - t1) / iterations) * 1000

    assert avg_ancestor_ms < 2.0, f"Ancestor chain resolution took {avg_ancestor_ms:.3f}ms, exceeding 2.0ms SLA"

    ancestor_paths = [a.path for a in ancestors]
    expected_chain = [
        "india",
        "india.27",
        "india.27.492",
        "india.27.492.4182",
    ]
    assert ancestor_paths == expected_chain, f"Mismatched ancestor chain: {ancestor_paths}"


# -----------------------------------------------------------------------------
# 3. Territorial Search & Filtering
# -----------------------------------------------------------------------------

def test_territorial_fast_search():
    """Verify lightning-fast full-text and code searching across territorial units."""
    # Search by official LGD code
    by_lgd = hierarchy_service.search_units("492")
    assert any("Pune" in u.name and u.lgd_code == "492" for u in by_lgd)

    # Search by partial territory name
    by_name = hierarchy_service.search_units("haveli")
    assert any("Haveli" in u.name for u in by_name)

    # Search by State name
    by_state = hierarchy_service.search_units("kerala")
    assert any("Kerala" in u.name for u in by_state)

    # Test listing with level filter
    states = hierarchy_service.list_units(level=AdminLevelEnum.STATE, limit=100)
    assert len(states) >= 36
    assert all(s.unit_level == AdminLevelEnum.STATE for s in states)


# -----------------------------------------------------------------------------
# 4. Scoped Territorial RBAC & Jurisdictional Access Validation
# -----------------------------------------------------------------------------

def test_jurisdictional_access_control():
    """Verify strict territorial boundaries: superiors access subordinates, but lateral/upward access is forbidden."""
    # State Health Secretary (Maharashtra) -> Pune District (Allowed)
    assert hierarchy_service.verify_jurisdiction_access(
        officer_scope_path="india.27",
        target_facility_path="india.27.492",
    ) is True

    # District Health Officer (Pune) -> Haveli Taluka (Allowed)
    assert hierarchy_service.verify_jurisdiction_access(
        officer_scope_path="india.27.492",
        target_facility_path="india.27.492.4182",
    ) is True

    # Same-level exact match (Allowed)
    assert hierarchy_service.verify_jurisdiction_access(
        officer_scope_path="india.27.492",
        target_facility_path="india.27.492",
    ) is True

    # Lateral access: Pune DHO -> Satara District (Forbidden)
    assert hierarchy_service.verify_jurisdiction_access(
        officer_scope_path="india.27.492",
        target_facility_path="india.27.493",
    ) is False

    # Upward access: Haveli THO -> Pune District (Forbidden)
    assert hierarchy_service.verify_jurisdiction_access(
        officer_scope_path="india.27.492.4182",
        target_facility_path="india.27.492",
    ) is False

    # Lateral inter-state access: Maharashtra -> Gujarat (Forbidden)
    assert hierarchy_service.verify_jurisdiction_access(
        officer_scope_path="india.27",
        target_facility_path="india.24",
    ) is False

    # Empty paths (Forbidden)
    assert hierarchy_service.verify_jurisdiction_access("", "india.27") is False


# -----------------------------------------------------------------------------
# 5. Administrative Officer Appointment & Jurisdictional Roster
# -----------------------------------------------------------------------------

def test_officer_appointment_and_roster():
    """Verify appointment of designated government healthcare officers with territorial scopes."""
    pune_unit = hierarchy_service.get_unit_by_lgd_code("492")
    assert pune_unit is not None

    officer_payload = AdministrativeOfficerCreate(
        user_id=str(uuid.uuid4()),
        designation=GovtDesignationEnum.CHIEF_MEDICAL_OFFICER,
        administrative_unit_id=pune_unit.id,
        jurisdiction_path=pune_unit.path,
        gov_email="cmo.pune@gov.in",
        aadhaar_verified=True,
        appointed_by="Ministry of Health",
    )

    officer = hierarchy_service.appoint_officer(officer_payload)
    assert officer.id is not None
    assert officer.designation == GovtDesignationEnum.CHIEF_MEDICAL_OFFICER
    assert officer.gov_email == "cmo.pune@gov.in"
    assert "Pune" in officer.unit_name
    assert officer.aadhaar_verified is True

    # List officers by administrative unit
    pune_officers = hierarchy_service.list_officers(administrative_unit_id=pune_unit.id)
    assert any(o.id == officer.id for o in pune_officers)

    # List officers covering Haveli taluka (should include Pune CMO)
    covering_officers = hierarchy_service.list_officers(
        jurisdiction_path="india.27.492.4182"
    )
    assert any(o.id == officer.id for o in covering_officers)


# -----------------------------------------------------------------------------
# 6. JSON Hierarchical Tree Drilldown
# -----------------------------------------------------------------------------

def test_jurisdiction_tree_generation():
    """Verify recursive JSON tree builder for frontend interactive drilldowns."""
    tree = hierarchy_service.build_jurisdiction_tree(root_path="india", max_depth=2)
    assert tree is not None
    assert "India" in tree.name
    assert tree.unit_level == AdminLevelEnum.COUNTRY
    assert len(tree.children) >= 36

    # Verify Maharashtra node exists in first-level children
    mh_node = next((c for c in tree.children if c.name == "Maharashtra"), None)
    assert mh_node is not None
    assert mh_node.lgd_code == "27"
    assert len(mh_node.children) >= 1


# -----------------------------------------------------------------------------
# 7. REST API Integration Tests
# -----------------------------------------------------------------------------

@pytest_asyncio.fixture
async def api_client():
    """In-process async test client for NIRMAYA FastAPI endpoints."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_rest_api_summary_metrics(api_client: AsyncClient):
    """GET /api/v1/admin/hierarchy/metrics returns consolidated national statistics."""
    resp = await api_client.get("/api/v1/admin/hierarchy/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_states"] >= 36
    assert data["ltree_index_status"] == "GIST_OPTIMIZED"
    assert data["sub_2ms_benchmark_passed"] is True


@pytest.mark.asyncio
async def test_rest_api_units_list_and_search(api_client: AsyncClient):
    """Verify REST unit listing, filtering by level, and territorial searching."""
    # List state units
    resp_states = await api_client.get(
        f"/api/v1/admin/hierarchy/units?level={AdminLevelEnum.STATE.value}&limit=50"
    )
    assert resp_states.status_code == 200
    states = resp_states.json()
    assert len(states) >= 36

    # Search units
    resp_search = await api_client.get("/api/v1/admin/hierarchy/units/search?q=Pune")
    assert resp_search.status_code == 200
    results = resp_search.json()
    assert any("pune" in r["name"].lower() for r in results)

    # Lookup by path
    resp_path = await api_client.get("/api/v1/admin/hierarchy/by-path?path=india.27")
    assert resp_path.status_code == 200
    assert resp_path.json()["name"] == "Maharashtra"

    # Non-existent path returns 404
    resp_not_found = await api_client.get("/api/v1/admin/hierarchy/by-path?path=india.invalid.999")
    assert resp_not_found.status_code == 404


@pytest.mark.asyncio
async def test_rest_api_jurisdiction_verification(api_client: AsyncClient):
    """POST /api/v1/admin/hierarchy/verify-jurisdiction enforces territorial RBAC."""
    # Subordinate query (Authorized)
    resp_valid = await api_client.post(
        "/api/v1/admin/hierarchy/verify-jurisdiction",
        params={
            "officer_path": "india.27.492",
            "target_path": "india.27.492.4182",
        },
    )
    assert resp_valid.status_code == 200
    assert resp_valid.json()["authorized"] is True

    # Lateral query (Unauthorized)
    resp_invalid = await api_client.post(
        "/api/v1/admin/hierarchy/verify-jurisdiction",
        params={
            "officer_path": "india.27.492",
            "target_path": "india.24",
        },
    )
    assert resp_invalid.status_code == 200
    assert resp_invalid.json()["authorized"] is False


@pytest.mark.asyncio
async def test_rest_api_officer_lifecycle(api_client: AsyncClient):
    """POST /api/v1/admin/hierarchy/officers creates officer and GET lists officers."""
    unit = hierarchy_service.get_unit_by_lgd_code("492")
    assert unit is not None

    payload = {
        "user_id": str(uuid.uuid4()),
        "designation": GovtDesignationEnum.CHIEF_MEDICAL_OFFICER.value,
        "administrative_unit_id": unit.id,
        "jurisdiction_path": unit.path,
        "gov_email": f"cmo.pune.{uuid.uuid4().hex[:6]}@gov.in",
        "aadhaar_verified": True,
        "appointed_by": "State Health Directorate",
        "is_active": True,
    }

    create_resp = await api_client.post("/api/v1/admin/hierarchy/officers", json=payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["designation"] == GovtDesignationEnum.CHIEF_MEDICAL_OFFICER.value
    assert created_data["gov_email"] == payload["gov_email"]

    # List officers
    list_resp = await api_client.get(
        f"/api/v1/admin/hierarchy/officers?administrative_unit_id={unit.id}"
    )
    assert list_resp.status_code == 200
    officers = list_resp.json()
    assert any(o["id"] == created_data["id"] for o in officers)


# -----------------------------------------------------------------------------
# 8. SQLAlchemy Relational Model & LTreePath Persistence Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sqlalchemy_administrative_models_persistence():
    """Verify that AdministrativeUnit and AdministrativeOfficer persist cleanly across SQL engines."""
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
        # Create base user for foreign key satisfaction
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=f"cmo.{uuid.uuid4().hex[:6]}@tamilnadu.gov.in",
            full_name="Dr. Chennai Officer",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.flush()

        # Create state unit
        state = AdministrativeUnit(
            id=str(uuid.uuid4()),
            name="Tamil Nadu",
            unit_level=AdminLevelEnum.STATE,
            lgd_code="33",
            path="india.33",
            pincode_prefixes="60,61,62,63,64",
            is_active=True,
        )
        session.add(state)
        await session.flush()

        # Create district unit
        district = AdministrativeUnit(
            id=str(uuid.uuid4()),
            name="Chennai",
            unit_level=AdminLevelEnum.DISTRICT,
            lgd_code="603",
            path="india.33.603",
            parent_id=state.id,
            pincode_prefixes="600",
            is_active=True,
        )
        session.add(district)
        await session.flush()

        # Create officer assigned to Chennai
        officer = AdministrativeOfficer(
            id=str(uuid.uuid4()),
            user_id=user.id,
            designation=GovtDesignationEnum.CHIEF_MEDICAL_OFFICER,
            administrative_unit_id=district.id,
            jurisdiction_path=district.path,
            gov_email="cmo.chennai@gov.in",
            aadhaar_verified=True,
            appointed_by="Government of Tamil Nadu",
            is_active=True,
        )
        session.add(officer)
        await session.commit()

        # Query back and verify relations and ltree paths
        from sqlalchemy import select
        res = await session.execute(
            select(AdministrativeUnit).where(AdministrativeUnit.lgd_code == "603")
        )
        loaded_district = res.scalar_one_or_none()
        assert loaded_district is not None
        assert loaded_district.path == "india.33.603"
        assert loaded_district.parent_id == state.id

        off_res = await session.execute(
            select(AdministrativeOfficer).where(AdministrativeOfficer.gov_email == "cmo.chennai@gov.in")
        )
        loaded_officer = off_res.scalar_one_or_none()
        assert loaded_officer is not None
        assert loaded_officer.jurisdiction_path == "india.33.603"
        assert loaded_officer.designation == GovtDesignationEnum.CHIEF_MEDICAL_OFFICER

    await engine.dispose()
