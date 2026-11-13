"""Unit and integration test suite for NIRMAYA Master Production Release v1.1.0.

Verifies:
- Settings version bump to 1.1.0
- Master release schemas, cumulative metrics (90 days, 981+ tests, 54 modules), and validation
- 18-week chronological milestone audit registry (Weeks 1 to 18)
- 11 major architectural breakthroughs (6 foundational + 5 Phase 5 breakthroughs)
- 15 live operational deployment health probes (8 foundational + 7 Phase 5 extensions)
- Formal Phase 5 regulatory compliance certification report (DPDP Act Sec 9, ABDM, GIGW 3.0, WCAG 2.1 AA)
- FastAPI REST endpoints (/version, /manifest, /certification, /verification, /milestones)
- Existence and completeness of release documentation and monographs
"""

import os
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.schemas.release import (
    CumulativeSystemMetrics,
    HealthCheckStatusEnum,
    MajorBreakthroughItem,
    MasterReleaseManifest,
    Phase5CertificationReport,
    Phase5RoadmapItem,
    ProductionDeploymentVerification,
    ReleaseChannelEnum,
    ReleasePillarAudit,
)
from app.services.release_service import release_service


# =============================================================================
# 1. Configuration & Version Invariants
# =============================================================================

def test_version_config_is_1_1_0():
    """Verify application settings version is bumped to 1.1.0."""
    assert settings.VERSION == "1.1.0"
    assert settings.PROJECT_NAME == "NIRMAYA"


def test_release_manifest_schema_defaults():
    """Verify MasterReleaseManifest Pydantic model instantiation and defaults."""
    manifest = release_service.get_master_release_manifest()
    assert manifest.version == "1.1.0"
    assert manifest.tag_name == "v1.1.0"
    assert manifest.release_channel == ReleaseChannelEnum.PRODUCTION_MASTER
    assert "NIRMAYA" in manifest.release_title
    assert "Suryansh Swarn" in manifest.publisher


def test_phase5_certification_schema_fields():
    """Verify Phase5CertificationReport schema constraints and typing."""
    cert = Phase5CertificationReport(
        release_version="1.1.0",
        certification_timestamp=datetime.now(timezone.utc),
        dpdp_act_sec9_certified=True,
        abdm_m1_m2_m3_certified=True,
        gigw_3_0_certified=True,
        wcag_2_1_aa_certified=True,
        rate_shield_capacity_req_s=50000,
        express_opd_p99_latency_ms=18.5,
        certified_by="Test Authority",
        status="OFFICIALLY_CERTIFIED",
    )
    assert cert.release_version == "1.1.0"
    assert cert.dpdp_act_sec9_certified is True
    assert cert.rate_shield_capacity_req_s == 50000
    assert cert.status == "OFFICIALLY_CERTIFIED"


def test_cumulative_system_metrics_defaults():
    """Verify exact cumulative metrics at Day 90 / Release v1.1.0 sign-off."""
    manifest = release_service.get_master_release_manifest()
    metrics = manifest.cumulative_metrics
    assert metrics.total_working_days == 90
    assert metrics.total_tests_passing >= 981
    assert metrics.total_test_modules == 54
    assert metrics.test_pass_rate_percentage == 100.0
    assert metrics.total_dependencies == 29
    assert metrics.copyleft_viral_dependencies == 0
    assert metrics.formal_architectural_proofs == 6
    assert metrics.subsystem_benchmarks_certified == 10
    assert metrics.monograph_chapters == 10
    assert metrics.interactive_demo_scenarios == 7


# =============================================================================
# 2. 18-Week Milestone Audit Registry Tests
# =============================================================================

def test_milestone_audit_18_weeks_length():
    """Verify all 18 weekly engineering milestones are recorded."""
    milestones = release_service.get_milestone_audits()
    assert len(milestones) == 18


def test_milestone_audit_week_numbers_range():
    """Verify week indices span strictly from Week 1 to Week 18 without gaps."""
    milestones = release_service.get_milestone_audits()
    weeks = [m.week_number for m in milestones]
    assert weeks == list(range(1, 19))


def test_milestone_audit_monotonically_increasing_tests():
    """Verify test counts strictly increase or hold non-decreasing across all 18 weeks."""
    milestones = release_service.get_milestone_audits()
    test_counts = [m.tests_count for m in milestones]
    for i in range(len(test_counts) - 1):
        assert test_counts[i] <= test_counts[i + 1]
    assert test_counts[-1] >= 981


def test_milestone_audit_hashes_sha256():
    """Verify each milestone record contains a valid 64-character SHA-256 fingerprint."""
    milestones = release_service.get_milestone_audits()
    for m in milestones:
        assert len(m.verification_hash) == 64
        int(m.verification_hash, 16)  # Asserts valid hex string


# =============================================================================
# 3. Major Architectural Breakthroughs & Roadmap Tests
# =============================================================================

def test_major_breakthroughs_count():
    """Verify that all 11 major architectural breakthroughs are cataloged."""
    manifest = release_service.get_master_release_manifest()
    assert len(manifest.major_breakthroughs) == 11


def test_major_breakthroughs_phase5_pillars():
    """Verify Phase 5 specific pillars (7 through 11) exist and detail key advancements."""
    manifest = release_service.get_master_release_manifest()
    titles = [b.title for b in manifest.major_breakthroughs]
    assert any("DPDP Act 2023 Sec 9" in t for t in titles)
    assert any("Multi-Guardian Dual-Signature" in t for t in titles)
    assert any("50,000 req/s Rate Shield" in t for t in titles)
    assert any("High-Velocity Express 45s Doctor OPD" in t for t in titles)
    assert any("Indian DPI Accessibility Suite" in t for t in titles)


def test_phase5_roadmap_remaining_sprints():
    """Verify Phase 5 preview catalog indicates the upcoming Week 19 sprint."""
    manifest = release_service.get_master_release_manifest()
    assert len(manifest.phase5_roadmap_preview) >= 1
    ranges = [r.week_range for r in manifest.phase5_roadmap_preview]
    assert any("Week 19" in r for r in ranges)


# =============================================================================
# 4. 15 Operational Deployment Health Probes Tests
# =============================================================================

def test_production_verification_15_probes():
    """Verify live execution of exactly 15 production deployment verification probes."""
    probes = release_service.verify_production_deployment()
    assert len(probes) == 15


def test_all_15_probes_healthy():
    """Verify every single probe in the suite reports HEALTHY status."""
    probes = release_service.verify_production_deployment()
    for p in probes:
        assert p.status == HealthCheckStatusEnum.HEALTHY


def test_probes_latency_slas():
    """Verify all 15 operational probes operate well under strict 50ms SLA."""
    probes = release_service.verify_production_deployment()
    for p in probes:
        assert 0.0 < p.response_time_ms < 50.0
        assert len(p.subsystem) > 0
        assert len(p.check_name) > 0


def test_phase5_specific_probes_present():
    """Verify that all 7 Phase 5 specific DPI probes are executed."""
    probes = release_service.verify_production_deployment()
    subsystems = [p.subsystem for p in probes]
    assert any("Family Proxy Vault" in s for s in subsystems)
    assert any("Child-ABHA Demographic Gateway" in s for s in subsystems)
    assert any("Multi-Guardian Dispute Engine" in s for s in subsystems)
    assert any("Universal National Gateway" in s for s in subsystems)
    assert any("Strict 3-Tile Citizen Portal" in s for s in subsystems)
    assert any("Express Doctor OPD Console" in s for s in subsystems)
    assert any("Indian DPI Accessibility Engine" in s for s in subsystems)


# =============================================================================
# 5. Phase 5 Regulatory Compliance Certification Tests
# =============================================================================

def test_phase5_certification_report_contents():
    """Verify formal regulatory compliance report fields and SLAs."""
    report = release_service.get_phase5_certification()
    assert report.release_version == "1.1.0"
    assert report.dpdp_act_sec9_certified is True
    assert report.abdm_m1_m2_m3_certified is True
    assert report.gigw_3_0_certified is True
    assert report.wcag_2_1_aa_certified is True
    assert report.rate_shield_capacity_req_s == 50000
    assert report.express_opd_p99_latency_ms <= 50.0
    assert report.status == "OFFICIALLY_CERTIFIED"


def test_master_manifest_generation_v1_1_0():
    """Verify MasterReleaseManifest generation with v1.1.0 tag."""
    manifest = release_service.get_master_release_manifest()
    assert manifest.version == "1.1.0"
    assert manifest.tag_name == "v1.1.0"
    assert manifest.commit_hash == "v1.1.0-master"


def test_master_manifest_custom_commit_hash():
    """Verify custom commit hash propagation in manifest generation."""
    manifest = release_service.get_master_release_manifest(commit_hash="sha-fedcba9876543210")
    assert manifest.commit_hash == "sha-fedcba9876543210"


def test_master_manifest_markdown_excerpt():
    """Verify release notes excerpt emphasizes v1.1.0 advancements."""
    manifest = release_service.get_master_release_manifest()
    assert "NIRMAYA Release v1.1.0" in manifest.release_notes_markdown_excerpt
    assert "981+" in manifest.release_notes_markdown_excerpt
    assert "50,000 req/s" in manifest.release_notes_markdown_excerpt


# =============================================================================
# 6. FastAPI REST API Endpoint Tests
# =============================================================================

async def test_api_get_release_version_v1_1_0(client: AsyncClient):
    """Verify GET /api/v1/release/version endpoint returns v1.1.0."""
    resp = await client.get("/api/v1/release/version")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.1.0"
    assert data["tag_name"] == "v1.1.0"
    assert data["status"] == "PRODUCTION_STABLE"
    assert "x-process-uid" in resp.headers


async def test_api_get_release_manifest_v1_1_0(client: AsyncClient):
    """Verify GET /api/v1/release/manifest endpoint returns v1.1.0 manifest."""
    resp = await client.get("/api/v1/release/manifest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.1.0"
    assert data["cumulative_metrics"]["total_working_days"] == 90
    assert data["cumulative_metrics"]["total_test_modules"] == 54
    assert len(data["major_breakthroughs"]) == 11


async def test_api_get_phase5_certification_endpoint(client: AsyncClient):
    """Verify GET /api/v1/release/certification endpoint returns formal certification report."""
    resp = await client.get("/api/v1/release/certification")
    assert resp.status_code == 200
    data = resp.json()
    assert data["release_version"] == "1.1.0"
    assert data["dpdp_act_sec9_certified"] is True
    assert data["abdm_m1_m2_m3_certified"] is True
    assert data["gigw_3_0_certified"] is True
    assert data["wcag_2_1_aa_certified"] is True
    assert data["rate_shield_capacity_req_s"] == 50000
    assert data["status"] == "OFFICIALLY_CERTIFIED"


async def test_api_get_production_verification_15_probes(client: AsyncClient):
    """Verify GET /api/v1/release/verification returns all 15 operational probes."""
    resp = await client.get("/api/v1/release/verification")
    assert resp.status_code == 200
    probes = resp.json()
    assert len(probes) == 15
    assert all(p["status"] == "HEALTHY" for p in probes)


async def test_api_get_milestone_audits_18_weeks(client: AsyncClient):
    """Verify GET /api/v1/release/milestones returns all 18 weekly milestone records."""
    resp = await client.get("/api/v1/release/milestones")
    assert resp.status_code == 200
    milestones = resp.json()
    assert len(milestones) == 18
    assert all(m["status"] == "COMPLETED" for m in milestones)


# =============================================================================
# 7. Documentation & Monograph Existence Tests
# =============================================================================

def test_release_notes_v1_1_0_file_exists():
    """Verify that root RELEASE_NOTES_v1.1.0.md exists and is non-empty."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "RELEASE_NOTES_v1.1.0.md")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "NIRMAYA Release Notes: v1.1.0 National Scale Digital Public Infrastructure" in content
    assert len(content) > 1000


def test_day_90_journey_log_exists():
    """Verify that docs/journey/month-4/day-90.md exists and is non-empty."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "journey", "month-4", "day-90.md")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Day 90: Master Production Certification, 90-Day Engineering Monograph & Release v1.1.0" in content
    assert len(content) > 1000


def test_week_18_retrospective_file_exists():
    """Verify that docs/journey/month-4/week-18-retrospective.md exists and is non-empty."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "journey", "month-4", "week-18-retrospective.md")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Week 18 Retrospective & Phase 5 DPI Synthesis" in content
    assert len(content) > 1000


def test_week_18_marked_completed():
    """Verify that docs/journey/month-4/week-18.md marks Week 18 as COMPLETED."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "journey", "month-4", "week-18.md")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "**Week Status:** **COMPLETED**" in content
