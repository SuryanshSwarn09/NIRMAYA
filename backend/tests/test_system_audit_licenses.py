from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from app.schemas.license_audit import (
    ComplianceStatusEnum,
    CycloneDXComponent,
    CycloneDXManifest,
    CycloneDXMetadata,
    DependencyComponentItem,
    DependencyEcosystemEnum,
    IntegrityCheckStatusEnum,
    LicenseSummaryScorecard,
    LicenseTypeEnum,
    PreReleaseAuditReport,
    SystemIntegrityCheckItem,
)
from app.services.license_audit_service import license_audit_service


def test_license_audit_schemas_serialization():
    """Verify serialization and validation of license audit Pydantic models."""
    dep = DependencyComponentItem(
        name="test-pkg",
        version="1.0.0",
        ecosystem=DependencyEcosystemEnum.PYTHON_PYPI,
        license=LicenseTypeEnum.MIT,
        license_url="https://example.com/license",
        copyleft_risk=False,
        direct_dependency=True,
        description="Test dependency description.",
    )
    assert dep.name == "test-pkg"
    assert dep.license == LicenseTypeEnum.MIT

    scorecard = LicenseSummaryScorecard(
        total_dependencies=1,
        permissive_count=1,
        copyleft_count=0,
        permissive_percentage=100.0,
        compliance_status=ComplianceStatusEnum.CERTIFIED,
        license_distribution={"MIT": 1},
        legal_signoff_attestation="Attestation statement.",
    )
    assert scorecard.compliance_status == ComplianceStatusEnum.CERTIFIED

    chk = SystemIntegrityCheckItem(
        check_id="INT-TEST",
        subsystem="Test Subsystem",
        invariant_verified="Latency < 5ms",
        compliance_status=IntegrityCheckStatusEnum.PASSED,
        target_sla_or_bound="5.0 ms",
        achieved_metric="3.2 ms",
    )
    assert chk.compliance_status == IntegrityCheckStatusEnum.PASSED


def test_license_service_dependency_catalog_counts():
    """Verify total count and ecosystem breakdown in dependency catalog."""
    deps = license_audit_service.list_dependencies()
    assert len(deps) == 29

    python_deps = [d for d in deps if d.ecosystem == DependencyEcosystemEnum.PYTHON_PYPI]
    node_deps = [d for d in deps if d.ecosystem == DependencyEcosystemEnum.NODE_NPM]

    assert len(python_deps) == 20
    assert len(node_deps) == 9


def test_license_service_zero_copyleft_invariant():
    """Formally verify zero copyleft (GPL, AGPL) dependencies in catalog."""
    deps = license_audit_service.list_dependencies()
    copyleft_deps = [d for d in deps if d.copyleft_risk]
    assert len(copyleft_deps) == 0

    for d in deps:
        assert d.license != LicenseTypeEnum.COPYLEFT_FLAGGED
        assert "GPL" not in d.license.value.upper()
        assert "AGPL" not in d.license.value.upper()


def test_license_service_ecosystem_filter():
    """Verify filtering dependencies by ecosystem via service."""
    py_deps = license_audit_service.list_dependencies(ecosystem=DependencyEcosystemEnum.PYTHON_PYPI)
    assert len(py_deps) == 20
    assert all(d.ecosystem == DependencyEcosystemEnum.PYTHON_PYPI for d in py_deps)

    npm_deps = license_audit_service.list_dependencies(ecosystem=DependencyEcosystemEnum.NODE_NPM)
    assert len(npm_deps) == 9
    assert all(d.ecosystem == DependencyEcosystemEnum.NODE_NPM for d in npm_deps)


def test_license_service_license_type_filter():
    """Verify filtering dependencies by license classification."""
    mit_deps = license_audit_service.list_dependencies(license_filter=LicenseTypeEnum.MIT)
    assert len(mit_deps) == 15
    assert all(d.license == LicenseTypeEnum.MIT for d in mit_deps)

    apache_deps = license_audit_service.list_dependencies(license_filter=LicenseTypeEnum.APACHE_2_0)
    assert len(apache_deps) == 9

    bsd_deps = license_audit_service.list_dependencies(license_filter=LicenseTypeEnum.BSD_3_CLAUSE)
    assert len(bsd_deps) == 4

    isc_deps = license_audit_service.list_dependencies(license_filter=LicenseTypeEnum.ISC)
    assert len(isc_deps) == 1


def test_license_scorecard_metrics():
    """Verify calculated legal scorecard metrics."""
    scorecard = license_audit_service.get_license_scorecard()
    assert scorecard.total_dependencies == 29
    assert scorecard.permissive_count == 29
    assert scorecard.copyleft_count == 0
    assert scorecard.permissive_percentage == 100.0
    assert scorecard.compliance_status == ComplianceStatusEnum.CERTIFIED
    assert "LEGAL COMPLIANCE ATTESTATION" in scorecard.legal_signoff_attestation
    assert scorecard.license_distribution["MIT"] == 15
    assert scorecard.license_distribution["Apache-2.0"] == 9


def test_cyclonedx_sbom_generation_ntia_elements():
    """Verify CycloneDX 1.5 SBOM manifest conforms to NTIA minimum elements."""
    sbom = license_audit_service.generate_cyclonedx_sbom()
    assert sbom.bomFormat == "CycloneDX"
    assert sbom.specVersion == "1.5"
    assert sbom.serialNumber.startswith("urn:uuid:")
    assert sbom.version == 1
    assert len(sbom.components) == 29

    # Check NTIA minimum elements on each component
    for c in sbom.components:
        assert len(c.name) > 0
        assert len(c.version) > 0
        assert len(c.purl) > 0
        assert c.purl.startswith("pkg:")
        assert len(c.licenses) > 0
        assert "license" in c.licenses[0]


def test_system_integrity_16_checks_structure():
    """Verify all 16 system integrity checks pass."""
    checks = license_audit_service.get_system_integrity_checks()
    assert len(checks) == 16
    for c in checks:
        assert c.compliance_status == IntegrityCheckStatusEnum.PASSED
        assert len(c.subsystem) > 0
        assert len(c.invariant_verified) > 0
        assert len(c.achieved_metric) > 0


def test_system_integrity_subsystem_coverage():
    """Verify key architectural subsystems are covered in integrity checks."""
    checks = license_audit_service.get_system_integrity_checks()
    subsystems = [c.subsystem for c in checks]

    assert any("PostgreSQL" in s for s in subsystems)
    assert any("Redlock" in s or "Lock" in s for s in subsystems)
    assert any("FHIR" in s for s in subsystems)
    assert any("ABDM" in s or "Crypto" in s for s in subsystems)
    assert any("WebSocket" in s for s in subsystems)
    assert any("Merkle" in s or "Audit" in s for s in subsystems)
    assert any("TRBAC" in s or "Governance" in s for s in subsystems)
    assert any("Container" in s or "OCI" in s for s in subsystems)
    assert any("Next.js" in s for s in subsystems)
    assert any("Edge" in s for s in subsystems)
    assert any("SQL/MED" in s or "Federation" in s for s in subsystems)


def test_pre_release_audit_report_verdict():
    """Verify consolidated pre-release audit report evaluates to production ready."""
    rep = license_audit_service.get_pre_release_audit_report()
    assert rep.project_name == "NIRMAYA"
    assert rep.release_candidate == "v1.0.0-rc1"
    assert rep.total_checks_count == 16
    assert rep.total_checks_passed == 16
    assert rep.all_checks_passed is True
    assert rep.release_readiness == "READY_FOR_PRODUCTION_TAG"
    assert rep.license_scorecard.compliance_status == ComplianceStatusEnum.CERTIFIED


# =============================================================================
# FastAPI REST API Integration Tests
# =============================================================================

async def test_api_get_license_summary(client: AsyncClient):
    """Verify GET /api/v1/audit/licenses/summary endpoint."""
    resp = await client.get("/api/v1/audit/licenses/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_dependencies"] == 29
    assert data["permissive_percentage"] == 100.0
    assert data["compliance_status"] == "CERTIFIED"
    assert "x-process-uid" in resp.headers


async def test_api_list_dependencies_all(client: AsyncClient):
    """Verify GET /api/v1/audit/licenses/dependencies endpoint."""
    resp = await client.get("/api/v1/audit/licenses/dependencies")
    assert resp.status_code == 200
    deps = resp.json()
    assert len(deps) == 29
    assert all(d["copyleft_risk"] is False for d in deps)


async def test_api_list_dependencies_filtered(client: AsyncClient):
    """Verify GET /api/v1/audit/licenses/dependencies with ecosystem and license queries."""
    resp_py = await client.get("/api/v1/audit/licenses/dependencies?ecosystem=Python%20(PyPI)")
    assert resp_py.status_code == 200
    py_deps = resp_py.json()
    assert len(py_deps) == 20

    resp_mit = await client.get("/api/v1/audit/licenses/dependencies?license_filter=MIT")
    assert resp_mit.status_code == 200
    mit_deps = resp_mit.json()
    assert len(mit_deps) == 15


async def test_api_get_cyclonedx_sbom(client: AsyncClient):
    """Verify GET /api/v1/audit/sbom/cyclonedx endpoint."""
    resp = await client.get("/api/v1/audit/sbom/cyclonedx")
    assert resp.status_code == 200
    assert "attachment; filename=nirmaya-sbom-cyclonedx.json" in resp.headers.get("content-disposition", "")
    manifest = resp.json()
    assert manifest["bomFormat"] == "CycloneDX"
    assert manifest["specVersion"] == "1.5"
    assert len(manifest["components"]) == 29


async def test_api_get_system_integrity(client: AsyncClient):
    """Verify GET /api/v1/audit/system-integrity endpoint."""
    resp = await client.get("/api/v1/audit/system-integrity")
    assert resp.status_code == 200
    checks = resp.json()
    assert len(checks) == 16
    assert all(c["compliance_status"] == "PASSED" for c in checks)


async def test_api_get_pre_release_report(client: AsyncClient):
    """Verify GET /api/v1/audit/report endpoint."""
    resp = await client.get("/api/v1/audit/report")
    assert resp.status_code == 200
    rep = resp.json()
    assert rep["all_checks_passed"] is True
    assert rep["release_readiness"] == "READY_FOR_PRODUCTION_TAG"
    assert rep["total_checks_passed"] == 16
    assert "x-process-uid" in resp.headers
