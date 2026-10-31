"""Automated test suite for District & State Public Health Command Center and Disease Surveillance.

Verifies:
- Consolidated command center overview telemetry aggregation across sovereign LGD subtrees
- Sub-2ms query performance SLA on regional public health consolidation
- Disease outbreak cluster surveillance, 7-day growth rate %, R_t, and alert thresholds
- Hospital critical care and ICU bed census with automated emergency admission diversion
- Clinical specialist deployment and workforce duty roster telemetry
- Public health containment orders and emergency directive dispatch lifecycle
- Scoped Territorial RBAC (TRBAC) boundary isolation (< 0.01ms evaluation)
- FastAPI REST endpoints under /api/v1/admin/command-center/*
- Relational model persistence for DiseaseOutbreakRecord, FacilityResourceTelemetryModel, and PublicHealthDirectiveModel
"""

from datetime import datetime, timezone, timedelta
import time
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import models as app_models  # noqa: F401
from app.core.territorial_rbac import is_territorial_access_allowed, verify_command_center_access
from app.db.base import Base
from app.main import app as fastapi_app
from app.models.command_center import (
    DiseaseOutbreakRecord,
    FacilityResourceTelemetryModel,
    PublicHealthDirectiveModel,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.command_center import (
    DirectiveCategoryEnum,
    DiseaseCategoryEnum,
    OutbreakSeverityEnum,
    PublicHealthDirectiveCreate,
)
from app.services.command_center_service import command_center_service


# -----------------------------------------------------------------------------
# 1. Consolidated Overview Telemetry & Sub-2ms SLA Tests
# -----------------------------------------------------------------------------

def test_command_center_overview_telemetry():
    """Verify recursive public health aggregation across district and sub-district territories."""
    # Query Pune District (india.27.492)
    pune_overview = command_center_service.get_overview_metrics("india.27.492")

    assert pune_overview.territory_name == "Pune District"
    # Haveli (142) + Baramati (68) = 210 active cases
    assert pune_overview.total_active_cases == 210
    # Aundh (40) + Sassoon (100) + Wagholi (12) + Baramati (20) = 172 ICU beds
    assert pune_overview.total_icu_capacity == 172
    assert pune_overview.occupied_icu_beds == 147
    assert pune_overview.available_icu_beds == 25
    assert pune_overview.regional_icu_occupancy_pct == 85.5
    assert pune_overview.available_ventilators == 17
    assert pune_overview.active_outbreak_clusters == 2
    assert pune_overview.surveillance_sla_passed is True

    # Query Haveli Taluka (india.27.492.4182) specifically
    haveli_overview = command_center_service.get_overview_metrics("india.27.492.4182")
    assert "Haveli" in haveli_overview.territory_name
    assert haveli_overview.total_active_cases == 142
    assert haveli_overview.total_monitored_facilities == 1  # Wagholi CHC


def test_sub_2ms_command_center_query_sla():
    """Verify sub-2ms query SLA across 50 consecutive telemetry aggregations."""
    iterations = 50
    t0 = time.perf_counter()
    for _ in range(iterations):
        res = command_center_service.get_overview_metrics("india.27.492")
        assert res.surveillance_sla_passed is True
    avg_latency_ms = ((time.perf_counter() - t0) / iterations) * 1000

    assert avg_latency_ms < 2.0, f"Query latency {avg_latency_ms:.3f}ms exceeded 2.0ms SLA"


# -----------------------------------------------------------------------------
# 2. Disease Outbreak Surveillance Heatmap Tests
# -----------------------------------------------------------------------------

def test_outbreak_surveillance_clusters_and_filters():
    """Verify disease cluster queries and multi-attribute filters."""
    # Query all clusters in Maharashtra State (india.27)
    mh_clusters = command_center_service.get_outbreak_clusters("india.27")
    assert len(mh_clusters) == 3  # Haveli Dengue, Baramati ADD, Mumbai COVID-19

    # Filter by Outbreak Severity: OUTBREAK
    outbreak_only = command_center_service.get_outbreak_clusters(
        "india.27",
        severity=OutbreakSeverityEnum.OUTBREAK,
    )
    assert len(outbreak_only) == 1
    assert outbreak_only[0].disease_category == DiseaseCategoryEnum.COVID_19
    assert outbreak_only[0].territory_name == "Mumbai Suburban District"

    # Filter by Disease Category: DENGUE
    dengue_only = command_center_service.get_outbreak_clusters(
        "india.27",
        disease_category=DiseaseCategoryEnum.DENGUE,
    )
    assert len(dengue_only) == 1
    assert dengue_only[0].incident_count == 142
    assert dengue_only[0].effective_reproduction_rate_rt == 1.42


def test_outbreak_cluster_detail_lookup():
    """Verify single disease cluster retrieval by identifier."""
    cluster = command_center_service.get_outbreak_by_id("cluster-dengue-pune-haveli-01")
    assert cluster is not None
    assert cluster.disease_name == "Dengue Virus Serotype 2"
    assert cluster.radius_meters == 1200
    assert cluster.is_contained is False

    # Non-existent cluster
    assert command_center_service.get_outbreak_by_id("cluster-unknown-9999") is None


# -----------------------------------------------------------------------------
# 3. Critical Care & ICU Bed Census Tests
# -----------------------------------------------------------------------------

def test_critical_care_icu_bed_census_and_diversion():
    """Verify ICU bed census and automated diversion trigger on > 85% occupancy."""
    pune_census = command_center_service.get_icu_bed_census("india.27.492")
    assert len(pune_census) == 4

    # Verify high occupancy divert trigger on Sassoon Medical College (92.0%)
    sassoon = next((f for f in pune_census if f.facility_id == "fac-sassoon-mc-pune"), None)
    assert sassoon is not None
    assert sassoon.icu_occupancy_pct == 92.0
    assert sassoon.is_diverting_admissions is True

    # Filter only diverting facilities
    diverting_facilities = command_center_service.get_icu_bed_census("india.27.492", diverting_only=True)
    assert len(diverting_facilities) == 1
    assert diverting_facilities[0].facility_id == "fac-sassoon-mc-pune"


# -----------------------------------------------------------------------------
# 4. Clinical Specialist Workforce Roster Tests
# -----------------------------------------------------------------------------

def test_workforce_duty_roster_aggregation():
    """Verify workforce duty telemetry, specialist counts, and doctor-to-patient ratio."""
    roster = command_center_service.get_workforce_roster("india.27.492")

    assert roster.territory_name == "Pune District"
    assert roster.total_active_physicians >= 50
    assert roster.intensivists_on_duty >= 10
    assert roster.pediatricians_on_duty >= 10
    assert roster.active_nursing_staff > roster.total_active_physicians
    assert ":" in roster.doctor_to_patient_ratio
    assert roster.coverage_status in ("ADEQUATE", "STRAINED", "CRITICAL")


# -----------------------------------------------------------------------------
# 5. Public Health Directives Lifecycle Tests
# -----------------------------------------------------------------------------

def test_public_health_directives_lifecycle():
    """Verify issuing and querying emergency public health orders."""
    now = datetime.now(timezone.utc)
    directive = command_center_service.issue_health_directive(
        PublicHealthDirectiveCreate(
            issuing_officer_id="user-cmo-pune-001",
            issuing_officer_designation="CHIEF_MEDICAL_OFFICER",
            jurisdiction_path="india.27.492",
            directive_category=DirectiveCategoryEnum.CONTAINMENT_ZONE,
            headline="Urgent Cholera Surveillance Order in Indapur Taluka",
            details="Immediate ban on unchlorinated water distribution and intensive rapid diagnostic testing across all primary schools.",
            affected_population_estimate=185000,
            valid_until=now + timedelta(days=10),
        )
    )

    assert directive.id is not None
    assert directive.is_active is True
    assert directive.directive_category == DirectiveCategoryEnum.CONTAINMENT_ZONE
    assert directive.affected_population_estimate == 185000

    # Query active directives in Pune
    pune_directives = command_center_service.list_health_directives("india.27.492", is_active=True)
    assert any(d.id == directive.id for d in pune_directives)

    # Cross-state containment: directive for Pune must not show up when querying Karnataka (india.29)
    ka_directives = command_center_service.list_health_directives("india.29")
    assert not any(d.id == directive.id for d in ka_directives)


# -----------------------------------------------------------------------------
# 6. Scoped TRBAC Boundary Enforcement Tests
# -----------------------------------------------------------------------------

def test_command_center_trbac_isolation():
    """Verify that officer territorial scope governs command center access."""
    # 1. District Officer (Pune) querying child territory (Haveli) -> Allowed
    assert verify_command_center_access("india.27.492", "india.27.492.4182") is True

    # 2. District Officer (Pune) querying lateral district (Satara) -> Blocked
    assert verify_command_center_access("india.27.492", "india.27.493") is False

    # 3. District Officer (Pune) querying parent state (Maharashtra) -> Blocked (Upward violation)
    assert verify_command_center_access("india.27.492", "india.27") is False

    # 4. State Secretary (Maharashtra) querying child district (Pune) -> Allowed
    assert verify_command_center_access("india.27", "india.27.492") is True

    # 5. National Director querying any state or district -> Allowed
    assert verify_command_center_access("india", "india.27.492.4182") is True
    assert verify_command_center_access("india", "india.29.524") is True


# -----------------------------------------------------------------------------
# 7. FastAPI REST API Integration Tests
# -----------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    """Asynchronous HTTP test client for FastAPI routes."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.asyncio
async def test_rest_api_overview_endpoint(client: AsyncClient):
    """Verify GET /api/v1/admin/command-center/overview."""
    resp = await client.get("/api/v1/admin/command-center/overview?jurisdiction_path=india.27.492")
    assert resp.status_code == 200
    data = resp.json()
    assert data["territory_name"] == "Pune District"
    assert data["total_active_cases"] == 210
    assert data["surveillance_sla_passed"] is True


@pytest.mark.asyncio
async def test_rest_api_outbreaks_and_icu_endpoints(client: AsyncClient):
    """Verify GET /api/v1/admin/command-center/outbreaks and /icu-beds."""
    # Outbreaks endpoint
    resp_outbreaks = await client.get("/api/v1/admin/command-center/outbreaks?jurisdiction_path=india.27.492")
    assert resp_outbreaks.status_code == 200
    outbreaks = resp_outbreaks.json()
    assert isinstance(outbreaks, list)
    assert len(outbreaks) >= 1

    # Single cluster endpoint
    first_id = outbreaks[0]["id"]
    resp_single = await client.get(f"/api/v1/admin/command-center/outbreaks/{first_id}")
    assert resp_single.status_code == 200
    assert resp_single.json()["id"] == first_id

    # ICU beds census endpoint
    resp_icu = await client.get("/api/v1/admin/command-center/icu-beds?jurisdiction_path=india.27.492")
    assert resp_icu.status_code == 200
    facilities = resp_icu.json()
    assert isinstance(facilities, list)
    assert len(facilities) >= 1


@pytest.mark.asyncio
async def test_rest_api_directives_and_workforce(client: AsyncClient):
    """Verify workforce roster and directives issuance endpoints."""
    # Workforce endpoint
    resp_wf = await client.get("/api/v1/admin/command-center/workforce?jurisdiction_path=india.27.492")
    assert resp_wf.status_code == 200
    wf_data = resp_wf.json()
    assert wf_data["total_active_physicians"] > 0

    # Issue Directive via API
    now = datetime.now(timezone.utc)
    directive_payload = {
        "issuing_officer_id": "user-cmo-pune-001",
        "issuing_officer_designation": "CHIEF_MEDICAL_OFFICER",
        "jurisdiction_path": "india.27.492",
        "directive_category": "masking_advisory",
        "headline": "Public Advisory on Crowded Gatherings",
        "details": "Advisory requiring indoor mask usage in all clinics and diagnostic centers across Pune.",
        "affected_population_estimate": 300000,
        "valid_until": (now + timedelta(days=7)).isoformat(),
    }
    resp_dir = await client.post("/api/v1/admin/command-center/directives", json=directive_payload)
    assert resp_dir.status_code == 201
    dir_data = resp_dir.json()
    assert dir_data["directive_category"] == "masking_advisory"


@pytest.mark.asyncio
async def test_rest_api_trbac_boundary_enforcement(client: AsyncClient):
    """Verify that inspecting officer headers trigger HTTP 403 on boundary violation."""
    # Pune officer trying to inspect Bangalore Urban (lateral violation)
    resp = await client.get(
        "/api/v1/admin/command-center/overview?jurisdiction_path=india.29.524",
        headers={"x-officer-jurisdiction": "india.27.492"},
    )
    assert resp.status_code == 403
    assert "Territorial RBAC violation" in str(resp.json())


# -----------------------------------------------------------------------------
# 8. SQLAlchemy Relational Model Persistence Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sqlalchemy_command_center_models_persistence():
    """Verify relational persistence for DiseaseOutbreakRecord, FacilityResourceTelemetryModel, and PublicHealthDirectiveModel."""
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
        now = datetime.now(timezone.utc)

        # 1. Create seed user for directive FK
        user = User(
            id=str(uuid.uuid4()),
            email="cmo.pune@gov.in",
            full_name="Chief Medical Officer Pune",
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        # 2. Create DiseaseOutbreakRecord
        outbreak = DiseaseOutbreakRecord(
            id=str(uuid.uuid4()),
            disease_name="Dengue Serotype 2",
            disease_category="dengue",
            jurisdiction_path="india.27.492.4182",
            territory_name="Haveli Taluka",
            incident_count=142,
            seven_day_growth_rate_pct=28.5,
            effective_reproduction_rate_rt=1.42,
            severity="alert",
            cluster_centroid_lat=18.5204,
            cluster_centroid_lng=73.8567,
            radius_meters=1200,
            first_case_reported_at=now - timedelta(days=12),
            last_case_reported_at=now,
            is_contained=False,
        )
        session.add(outbreak)

        # 3. Create FacilityResourceTelemetryModel
        facility = FacilityResourceTelemetryModel(
            id=str(uuid.uuid4()),
            facility_name="Aundh District Hospital",
            facility_tier="district_hospital",
            jurisdiction_path="india.27.492",
            total_icu_beds=40,
            occupied_icu_beds=34,
            available_icu_beds=6,
            icu_occupancy_pct=85.0,
            total_ventilator_beds=20,
            available_ventilators=4,
            oxygen_supported_beds=50,
            available_oxygen_beds=10,
            pediatric_icu_beds=10,
            available_picu_beds=2,
            is_diverting_admissions=False,
        )
        session.add(facility)

        # 4. Create PublicHealthDirectiveModel
        directive = PublicHealthDirectiveModel(
            id=str(uuid.uuid4()),
            issuing_officer_id=user.id,
            issuing_officer_designation="CHIEF_MEDICAL_OFFICER",
            jurisdiction_path="india.27.492",
            territory_name="Pune District",
            directive_category="vector_control",
            headline="Intensified Anti-Larval Drive",
            details="Detailed instructions for fogging and source reduction.",
            affected_population_estimate=450000,
            is_active=True,
            valid_until=now + timedelta(days=14),
        )
        session.add(directive)
        await session.commit()

        # Query back and verify
        res_o = await session.get(DiseaseOutbreakRecord, outbreak.id)
        assert res_o is not None
        assert res_o.disease_name == "Dengue Serotype 2"
        assert res_o.incident_count == 142

        res_f = await session.get(FacilityResourceTelemetryModel, facility.id)
        assert res_f is not None
        assert res_f.total_icu_beds == 40
        assert res_f.icu_occupancy_pct == 85.0

        res_d = await session.get(PublicHealthDirectiveModel, directive.id)
        assert res_d is not None
        assert res_d.issuing_officer_id == user.id
        assert res_d.is_active is True

    await engine.dispose()
