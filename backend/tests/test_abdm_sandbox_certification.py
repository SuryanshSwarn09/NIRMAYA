"""Unit and integration test suite for ABDM Official Sandbox E2E Certification Test Harness.

Verifies:
- Automated execution of all 15 official NHA ABDM Gateway v0.5 test vectors
- Milestone 1 (M1): Verhoeff D5 algorithm, Aadhaar OTP, ABHA minting, PHR reservation, HPR onboarding
- Milestone 2 (M2): Discovery with exact match, fuzzy matching, ambiguity protection (1441), link init, link confirm
- Milestone 3 (M3): Consent ingestion, Curve25519 key exchange, encrypted FHIR transfer, HIU decryption, tamper defense
- Per-milestone breakdown summaries and 100% pass rate calculation
- Deterministic SHA-256 cryptographic certificate proof generation
- REST API routes: POST /api/v1/abdm/certification/run, GET /api/v1/abdm/certification/report, GET /api/v1/abdm/certification/vectors
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.abdm_certification import (
    CertificationVectorStatus,
    RunCertificationRequest,
    SandboxMilestoneType,
)
from app.services.abdm_certification import (
    OFFICIAL_VECTOR_CATALOG,
    abdm_sandbox_certifier,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit Tests: Certification Engine Execution
# ---------------------------------------------------------------------------

class TestAbdmSandboxCertificationEngine:
    """Tests the automated execution of NHA Sandbox test vectors."""

    def test_run_full_certification_suite(self):
        report = abdm_sandbox_certifier.run_certification(
            facility_id="IN0410000123",
            facility_name="NIRMAYA National Health Demonstrator",
            mock_network_delay=False,
        )

        assert report.totalVectors == 15
        assert report.passedVectors == 15
        assert report.failedVectors == 0
        assert report.overallPassRate == 100.0
        assert report.certificationStatus == "CERTIFIED_CONFORMING"
        assert report.facilityId == "IN0410000123"
        assert report.environment == "sbx.abdm.gov.in"
        assert report.gatewayVersion == "v0.5"

        # Check cryptographic proof format
        assert len(report.certificateProof) == 64
        int(report.certificateProof, 16)  # Asserts valid hex string

        # Check milestone summaries
        assert len(report.milestoneSummaries) == 3
        m_map = {m.milestone: m for m in report.milestoneSummaries}
        assert m_map[SandboxMilestoneType.M1_ABHA].passed == 5
        assert m_map[SandboxMilestoneType.M1_ABHA].passRate == 100.0
        assert m_map[SandboxMilestoneType.M2_DISCOVERY_LINKAGE].passed == 5
        assert m_map[SandboxMilestoneType.M2_DISCOVERY_LINKAGE].passRate == 100.0
        assert m_map[SandboxMilestoneType.M3_CONSENT_DATA_TRANSFER].passed == 5
        assert m_map[SandboxMilestoneType.M3_CONSENT_DATA_TRANSFER].passRate == 100.0

        # Check vector results
        assert len(report.vectorResults) == 15
        for vec in report.vectorResults:
            assert vec.status == CertificationVectorStatus.PASSED
            assert vec.assertionsPassed > 0
            assert vec.assertionsPassed == vec.assertionsTotal
            assert vec.durationMs >= 0.0
            assert vec.errorDetail is None

    def test_run_selective_milestone_m1(self):
        report = abdm_sandbox_certifier.run_certification(
            milestones=[SandboxMilestoneType.M1_ABHA],
        )

        assert report.totalVectors == 5
        assert report.passedVectors == 5
        assert report.overallPassRate == 100.0
        assert report.certificationStatus == "CERTIFIED_CONFORMING"
        assert len(report.milestoneSummaries) == 1
        assert report.milestoneSummaries[0].milestone == SandboxMilestoneType.M1_ABHA
        vector_ids = [v.vectorId for v in report.vectorResults]
        assert vector_ids == ["V-M1-01", "V-M1-02", "V-M1-03", "V-M1-04", "V-M1-05"]

    def test_run_selective_milestone_m2(self):
        report = abdm_sandbox_certifier.run_certification(
            milestones=[SandboxMilestoneType.M2_DISCOVERY_LINKAGE],
        )

        assert report.totalVectors == 5
        assert report.passedVectors == 5
        assert report.overallPassRate == 100.0
        assert report.certificationStatus == "CERTIFIED_CONFORMING"
        assert len(report.milestoneSummaries) == 1
        assert report.milestoneSummaries[0].milestone == SandboxMilestoneType.M2_DISCOVERY_LINKAGE
        vector_ids = [v.vectorId for v in report.vectorResults]
        assert vector_ids == ["V-M2-01", "V-M2-02", "V-M2-03", "V-M2-04", "V-M2-05"]

    def test_run_selective_milestone_m3(self):
        report = abdm_sandbox_certifier.run_certification(
            milestones=[SandboxMilestoneType.M3_CONSENT_DATA_TRANSFER],
        )

        assert report.totalVectors == 5
        assert report.passedVectors == 5
        assert report.overallPassRate == 100.0
        assert report.certificationStatus == "CERTIFIED_CONFORMING"
        assert len(report.milestoneSummaries) == 1
        assert report.milestoneSummaries[0].milestone == SandboxMilestoneType.M3_CONSENT_DATA_TRANSFER
        vector_ids = [v.vectorId for v in report.vectorResults]
        assert vector_ids == ["V-M3-01", "V-M3-02", "V-M3-03", "V-M3-04", "V-M3-05"]

    def test_get_latest_cached_report(self):
        # Execute run
        fresh_report = abdm_sandbox_certifier.run_certification()
        cached_report = abdm_sandbox_certifier.get_latest_report()
        assert cached_report is not None
        assert cached_report.reportId == fresh_report.reportId
        assert cached_report.certificateProof == fresh_report.certificateProof

    def test_vector_catalog_metadata(self):
        catalog = abdm_sandbox_certifier.get_vector_catalog()
        assert len(catalog) == 15
        for item in catalog:
            assert item.vectorId.startswith("V-M")
            assert len(item.title) > 0
            assert len(item.description) > 0
            assert "Spec" in item.nhaSpecificationRef


# ---------------------------------------------------------------------------
# Integration Tests: REST API Routes (/api/v1/abdm/certification)
# ---------------------------------------------------------------------------

class TestAbdmSandboxCertificationAPI:
    """Tests the REST API routes for executing and reporting sandbox certification."""

    def test_api_run_full_certification(self):
        payload = {
            "facilityId": "IN0410000123",
            "mockNetworkDelay": False,
        }

        response = client.post("/api/v1/abdm/certification/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["certificationStatus"] == "CERTIFIED_CONFORMING"
        assert data["overallPassRate"] == 100.0
        assert data["totalVectors"] == 15
        assert data["passedVectors"] == 15
        assert data["failedVectors"] == 0
        assert len(data["certificateProof"]) == 64

    def test_api_run_selective_milestones(self):
        payload = {
            "milestones": [SandboxMilestoneType.M1_ABHA.value, SandboxMilestoneType.M3_CONSENT_DATA_TRANSFER.value],
            "facilityId": "IN0410000123",
            "mockNetworkDelay": False,
        }

        response = client.post("/api/v1/abdm/certification/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["totalVectors"] == 10
        assert data["passedVectors"] == 10
        assert data["overallPassRate"] == 100.0
        assert len(data["milestoneSummaries"]) == 2

    def test_api_get_latest_report(self):
        response = client.get("/api/v1/abdm/certification/report")
        assert response.status_code == 200
        data = response.json()
        assert data["certificationStatus"] == "CERTIFIED_CONFORMING"
        assert data["facilityId"] == "IN0410000123"
        assert "certificateProof" in data

    def test_api_get_vector_catalog(self):
        response = client.get("/api/v1/abdm/certification/vectors")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 15
        assert len(data["vectors"]) == 15
        vector_ids = [v["vectorId"] for v in data["vectors"]]
        assert "V-M1-01" in vector_ids
        assert "V-M2-03" in vector_ids
        assert "V-M3-05" in vector_ids
