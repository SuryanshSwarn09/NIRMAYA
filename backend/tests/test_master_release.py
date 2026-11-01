import os
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from app.schemas.release import (
    CumulativeSystemMetrics,
    HealthCheckStatusEnum,
    MajorBreakthroughItem,
    MasterReleaseManifest,
    Phase5RoadmapItem,
    ProductionDeploymentVerification,
    ReleaseChannelEnum,
    ReleasePillarAudit,
)
from app.services.release_service import release_service


def test_release_schemas_serialization():
    """Verify serialization and validation of master release Pydantic models."""
    metrics = CumulativeSystemMetrics(
        total_working_days=80,
        total_tests_passing=712,
        total_test_modules=44,
        test_pass_rate_percentage=100.0,
        total_dependencies=29,
        copyleft_viral_dependencies=0,
        formal_architectural_proofs=6,
        subsystem_benchmarks_certified=6,
        monograph_chapters=10,
        interactive_demo_scenarios=5,
    )
    assert metrics.total_working_days == 80
    assert metrics.total_tests_passing == 712

    audit = ReleasePillarAudit(
        week_number=16,
        milestone_id="16-05",
        title="Production Master Release v1.0.0",
        status="COMPLETED",
        tests_count=712,
        verification_hash="hash-abc-123",
    )
    assert audit.week_number == 16
    assert audit.status == "COMPLETED"


def test_release_service_milestone_audits_count():
    """Verify all 16 weekly engineering milestones are recorded in service."""
    milestones = release_service.get_milestone_audits()
    assert len(milestones) == 16
    weeks = [m.week_number for m in milestones]
    assert weeks == list(range(1, 17))


def test_release_service_milestone_audits_progression():
    """Verify that test count increases monotonically across the 16-week journey."""
    milestones = release_service.get_milestone_audits()
    test_counts = [m.tests_count for m in milestones]
    for i in range(len(test_counts) - 1):
        assert test_counts[i] <= test_counts[i + 1]
    assert test_counts[-1] >= 712


def test_release_service_major_breakthroughs():
    """Verify that all 6 major architectural breakthroughs are cataloged."""
    manifest = release_service.get_master_release_manifest()
    assert len(manifest.major_breakthroughs) == 6

    titles = [b.title for b in manifest.major_breakthroughs]
    assert any("Sovereign Indian LGD" in t for t in titles)
    assert any("Zero-Knowledge Break-The-Glass" in t for t in titles)
    assert any("Edge Node Appliance" in t for t in titles)
    assert any("SQL/MED Legacy HIS" in t for t in titles)
    assert any("ABDM Milestones" in t for t in titles)
    assert any("Production Microservice" in t for t in titles)


def test_release_service_phase5_roadmap_items():
    """Verify that Phase 5 preview items are cataloged (Weeks 17, 18, 19)."""
    manifest = release_service.get_master_release_manifest()
    assert len(manifest.phase5_roadmap_preview) == 3

    ranges = [r.week_range for r in manifest.phase5_roadmap_preview]
    assert any("Week 17" in r for r in ranges)
    assert any("Week 18" in r for r in ranges)
    assert any("Week 19" in r for r in ranges)


def test_release_service_production_health_probes():
    """Verify live execution of production deployment verification probes."""
    probes = release_service.verify_production_deployment()
    assert len(probes) == 8
    for p in probes:
        assert p.status == HealthCheckStatusEnum.HEALTHY
        assert p.response_time_ms > 0.0
        assert len(p.subsystem) > 0
        assert len(p.check_name) > 0


def test_release_service_master_manifest_generation():
    """Verify generation of MasterReleaseManifest with v1.0.0 metadata."""
    manifest = release_service.get_master_release_manifest("git-commit-hash-v1.0.0")
    assert manifest.version == "1.0.0"
    assert manifest.tag_name == "v1.0.0"
    assert manifest.release_channel == ReleaseChannelEnum.PRODUCTION_MASTER
    assert manifest.commit_hash == "git-commit-hash-v1.0.0"
    assert "Suryansh Swarn" in manifest.publisher


def test_release_service_cumulative_metrics():
    """Verify exact cumulative metrics at v1.0.0 release sign-off."""
    manifest = release_service.get_master_release_manifest()
    m = manifest.cumulative_metrics
    assert m.total_working_days == 80
    assert m.total_tests_passing >= 712
    assert m.total_test_modules >= 44
    assert m.test_pass_rate_percentage == 100.0
    assert m.total_dependencies == 29
    assert m.copyleft_viral_dependencies == 0
    assert m.formal_architectural_proofs == 6
    assert m.subsystem_benchmarks_certified == 6
    assert m.monograph_chapters == 10
    assert m.interactive_demo_scenarios == 5


def test_release_service_manifest_markdown_excerpt():
    """Verify release notes markdown excerpt contents."""
    manifest = release_service.get_master_release_manifest()
    assert "NIRMAYA Release v1.0.0: Sovereign Master" in manifest.release_notes_markdown_excerpt
    assert "DPDP" in manifest.release_notes_markdown_excerpt
    assert "ABDM" in manifest.release_notes_markdown_excerpt


# =============================================================================
# FastAPI REST API Integration Tests
# =============================================================================

async def test_api_get_release_version(client: AsyncClient):
    """Verify GET /api/v1/release/version endpoint."""
    resp = await client.get("/api/v1/release/version")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.0.0"
    assert data["tag_name"] == "v1.0.0"
    assert data["status"] == "PRODUCTION_STABLE"
    assert "x-process-uid" in resp.headers


async def test_api_get_release_manifest(client: AsyncClient):
    """Verify GET /api/v1/release/manifest endpoint."""
    resp = await client.get("/api/v1/release/manifest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.0.0"
    assert data["cumulative_metrics"]["total_working_days"] == 80
    assert len(data["major_breakthroughs"]) == 6
    assert len(data["phase5_roadmap_preview"]) == 3


async def test_api_get_production_verification(client: AsyncClient):
    """Verify GET /api/v1/release/verification endpoint."""
    resp = await client.get("/api/v1/release/verification")
    assert resp.status_code == 200
    probes = resp.json()
    assert len(probes) == 8
    assert all(p["status"] == "HEALTHY" for p in probes)


async def test_api_get_milestone_audits(client: AsyncClient):
    """Verify GET /api/v1/release/milestones endpoint."""
    resp = await client.get("/api/v1/release/milestones")
    assert resp.status_code == 200
    milestones = resp.json()
    assert len(milestones) == 16
    assert all(m["status"] == "COMPLETED" for m in milestones)


def test_release_notes_file_exists():
    """Verify that root RELEASE_NOTES_v1.0.0.md exists and is non-empty."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "RELEASE_NOTES_v1.0.0.md")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "NIRMAYA Release Notes: v1.0.0 Sovereign Master" in content
    assert len(content) > 500


def test_month_4_retrospective_file_exists():
    """Verify that docs/journey/month-4/month-4-retrospective.md exists and is non-empty."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "journey", "month-4", "month-4-retrospective.md")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Month 4 Comprehensive Retrospective" in content
    assert len(content) > 1000
