"""Unit and integration test suite for ABDM Security Penetration & Consent Lifecycle Audit.

Verifies:
- Automated execution of all 12 penetration attack vectors
- Anti-replay timestamp drift (>300s) and duplicate Request-ID detection
- Mid-flight dynamic consent revocation aborts data transmission and purges cryptographic keys
- Expired consent enforcement and status auto-transition
- Out-of-scope care context, HI-type, and date-range privilege escalation defense
- Malformed Curve25519 public key and degraded nonce validation
- AES-256-GCM AEAD authentication tag tamper defense (bit-flip rejection)
- SHA-256 plaintext checksum verification
- Brute-force OTP rate-limiting and account lockout
- REST API routes: POST /api/v1/abdm/security/audit/run, GET /api/v1/abdm/security/audit/report, GET /api/v1/abdm/security/audit/vectors
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.abdm_security_audit import (
    DefenseOutcome,
    PenetrationAttackCategory,
    VulnerabilitySeverity,
)
from app.services.abdm_security_audit import (
    OFFICIAL_PENETRATION_VECTORS,
    abdm_security_auditor,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit Tests: Security Penetration Engine
# ---------------------------------------------------------------------------

class TestAbdmSecurityPenetrationEngine:
    """Tests the automated execution of security penetration test vectors."""

    def test_run_full_security_penetration_suite(self):
        report = abdm_security_auditor.run_audit(
            facility_id="IN0410000123",
            facility_name="NIRMAYA National Health Demonstrator",
            simulate_network_hop=False,
        )

        assert report.totalVectors == 12
        assert report.passedVectors == 12
        assert report.vulnerabilitiesFound == 0
        assert report.overallDefenseRate == 100.0
        assert report.securityStatus == "SECURE_CONFORMING"
        assert report.facilityId == "IN0410000123"
        assert report.environment == "sbx.abdm.gov.in"

        # Check cryptographic proof
        assert len(report.securityCertificateProof) == 64
        int(report.securityCertificateProof, 16)  # Asserts valid hex string

        # Check category summaries (5 categories)
        assert len(report.categorySummaries) == 5
        cat_map = {c.category: c for c in report.categorySummaries}
        assert cat_map[PenetrationAttackCategory.GATEWAY_REPLAY].blocked == 2
        assert cat_map[PenetrationAttackCategory.CONSENT_LIFECYCLE].blocked == 2
        assert cat_map[PenetrationAttackCategory.SCOPE_ESCALATION].blocked == 3
        assert cat_map[PenetrationAttackCategory.CRYPTOGRAPHIC_INTEGRITY].blocked == 4
        assert cat_map[PenetrationAttackCategory.RATE_LIMIT_BRUTE_FORCE].blocked == 1

        for summary in report.categorySummaries:
            assert summary.defenseRate == 100.0
            assert summary.vulnerabilities == 0

        # Check vector results
        assert len(report.vectorResults) == 12
        for vec in report.vectorResults:
            assert vec.passed is True
            assert vec.defenseOutcome == DefenseOutcome.BLOCKED_AS_EXPECTED
            assert vec.severity == VulnerabilitySeverity.NONE
            assert vec.durationMs >= 0.0
            assert vec.errorDetail is None

    def test_selective_category_gateway_replay(self):
        report = abdm_security_auditor.run_audit(
            categories=[PenetrationAttackCategory.GATEWAY_REPLAY],
        )

        assert report.totalVectors == 2
        assert report.passedVectors == 2
        assert report.overallDefenseRate == 100.0
        assert report.securityStatus == "SECURE_CONFORMING"
        assert len(report.categorySummaries) == 1
        assert report.categorySummaries[0].category == PenetrationAttackCategory.GATEWAY_REPLAY
        vector_ids = [v.vectorId for v in report.vectorResults]
        assert vector_ids == ["SEC-01", "SEC-02"]

    def test_selective_category_consent_lifecycle(self):
        report = abdm_security_auditor.run_audit(
            categories=[PenetrationAttackCategory.CONSENT_LIFECYCLE],
        )

        assert report.totalVectors == 2
        assert report.passedVectors == 2
        assert report.overallDefenseRate == 100.0
        assert report.securityStatus == "SECURE_CONFORMING"
        assert len(report.categorySummaries) == 1
        assert report.categorySummaries[0].category == PenetrationAttackCategory.CONSENT_LIFECYCLE
        vector_ids = [v.vectorId for v in report.vectorResults]
        assert vector_ids == ["SEC-03", "SEC-04"]

    def test_selective_category_scope_escalation(self):
        report = abdm_security_auditor.run_audit(
            categories=[PenetrationAttackCategory.SCOPE_ESCALATION],
        )

        assert report.totalVectors == 3
        assert report.passedVectors == 3
        assert report.overallDefenseRate == 100.0
        vector_ids = [v.vectorId for v in report.vectorResults]
        assert vector_ids == ["SEC-05", "SEC-06", "SEC-07"]

    def test_selective_category_cryptographic_integrity(self):
        report = abdm_security_auditor.run_audit(
            categories=[PenetrationAttackCategory.CRYPTOGRAPHIC_INTEGRITY],
        )

        assert report.totalVectors == 4
        assert report.passedVectors == 4
        assert report.overallDefenseRate == 100.0
        vector_ids = [v.vectorId for v in report.vectorResults]
        assert vector_ids == ["SEC-08", "SEC-09", "SEC-10", "SEC-11"]

    def test_selective_category_rate_limit(self):
        report = abdm_security_auditor.run_audit(
            categories=[PenetrationAttackCategory.RATE_LIMIT_BRUTE_FORCE],
        )

        assert report.totalVectors == 1
        assert report.passedVectors == 1
        assert report.overallDefenseRate == 100.0
        vector_ids = [v.vectorId for v in report.vectorResults]
        assert vector_ids == ["SEC-12"]

    def test_get_latest_cached_report(self):
        fresh = abdm_security_auditor.run_audit()
        cached = abdm_security_auditor.get_latest_report()
        assert cached is not None
        assert cached.reportId == fresh.reportId
        assert cached.securityCertificateProof == fresh.securityCertificateProof

    def test_vector_catalog_metadata(self):
        catalog = abdm_security_auditor.get_vector_catalog()
        assert len(catalog) == 12
        for item in catalog:
            assert item.vectorId.startswith("SEC-")
            assert len(item.title) > 0
            assert len(item.attackDescription) > 0
            assert len(item.expectedDefense) > 0
            assert "Spec" in item.nhaReference or "Act" in item.nhaReference or "RFC" in item.nhaReference or "NIST" in item.nhaReference


# ---------------------------------------------------------------------------
# Integration Tests: REST API Routes (/api/v1/abdm/security)
# ---------------------------------------------------------------------------

class TestAbdmSecurityPenetrationAPI:
    """Tests the REST API routes for executing security penetration audits."""

    def test_api_run_full_audit(self):
        payload = {
            "facilityId": "IN0410000123",
            "simulateNetworkHop": False,
        }

        response = client.post("/api/v1/abdm/security/audit/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["securityStatus"] == "SECURE_CONFORMING"
        assert data["overallDefenseRate"] == 100.0
        assert data["totalVectors"] == 12
        assert data["passedVectors"] == 12
        assert data["vulnerabilitiesFound"] == 0
        assert len(data["securityCertificateProof"]) == 64

    def test_api_run_selective_categories(self):
        payload = {
            "categories": [
                PenetrationAttackCategory.CONSENT_LIFECYCLE.value,
                PenetrationAttackCategory.CRYPTOGRAPHIC_INTEGRITY.value,
            ],
            "facilityId": "IN0410000123",
            "simulateNetworkHop": False,
        }

        response = client.post("/api/v1/abdm/security/audit/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["totalVectors"] == 6
        assert data["passedVectors"] == 6
        assert data["overallDefenseRate"] == 100.0
        assert len(data["categorySummaries"]) == 2

    def test_api_get_latest_report(self):
        response = client.get("/api/v1/abdm/security/audit/report")
        assert response.status_code == 200
        data = response.json()
        assert data["securityStatus"] == "SECURE_CONFORMING"
        assert data["facilityId"] == "IN0410000123"
        assert "securityCertificateProof" in data

    def test_api_get_vector_catalog(self):
        response = client.get("/api/v1/abdm/security/audit/vectors")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 12
        assert len(data["vectors"]) == 12
        vec_ids = [v["vectorId"] for v in data["vectors"]]
        assert "SEC-01" in vec_ids
        assert "SEC-03" in vec_ids
        assert "SEC-10" in vec_ids
        assert "SEC-12" in vec_ids
