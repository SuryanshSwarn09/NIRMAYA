"""Unit and integration test suite for NIRMAYA Academic Project Monograph & Engineering Thesis.

Validates chapter outlines, formal architectural proofs, empirical benchmarks, and citations.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.monograph import (
    BenchmarkCategoryEnum,
    BenchmarkStatusEnum,
    ProofCategoryEnum,
)
from app.services.monograph_service import MonographService, monograph_service


@pytest.fixture
def client() -> TestClient:
    """Fixture providing FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def fresh_service() -> MonographService:
    """Fixture providing an isolated MonographService instance."""
    return MonographService()


def test_monograph_metadata_and_overview(fresh_service: MonographService):
    """Verify global monograph title, version, chapter counts, and word count calculation."""
    overview = fresh_service.get_overview()
    assert "NIRMAYA: A Sovereign, Interoperable, and Zero-Trust" in overview.title
    assert overview.version == "1.0.0-rc1"
    assert overview.release_target == "Production Master Release v1.0.0"
    assert overview.total_chapters == 10
    assert overview.total_word_count >= 15000
    assert overview.total_diagrams >= 20
    assert overview.total_formal_proofs == 6
    assert overview.cumulative_test_count >= 630
    assert overview.cumulative_test_modules >= 39


def test_all_ten_chapters_present_with_sections(fresh_service: MonographService):
    """Verify that all 10 chapters are properly numbered, titled, and contain section breakdowns."""
    chapters = fresh_service.list_chapters()
    assert len(chapters) == 10

    for idx, ch in enumerate(chapters, start=1):
        assert ch.chapter_num == idx
        assert ch.slug.startswith(f"ch-{idx:02d}-")
        assert len(ch.title) > 0
        assert ch.word_count > 1000
        assert len(ch.sections) >= 3
        for sec in ch.sections:
            assert len(sec.title) > 0
            assert len(sec.abstract) > 0


def test_chapter_retrieval_by_slug_and_number(fresh_service: MonographService):
    """Verify retrieving chapters by slug, chapter index string, and handling not-found."""
    ch1 = fresh_service.get_chapter("ch-01-national-crisis")
    assert ch1 is not None
    assert ch1.chapter_num == 1
    assert "National Healthcare Crisis" in ch1.title

    # By number string
    ch4 = fresh_service.get_chapter("4")
    assert ch4 is not None
    assert ch4.chapter_num == 4
    assert "ABDM National Health Stack" in ch4.title

    # Non-existent chapter
    ch_invalid = fresh_service.get_chapter("non-existent-slug")
    assert ch_invalid is None


def test_architectural_proofs_count_and_schema(fresh_service: MonographService):
    """Verify that all 6 formal proofs are cataloged with complete invariant definitions."""
    proofs = fresh_service.list_proofs()
    assert len(proofs) == 6

    proof_ids = [p.proof_id for p in proofs]
    assert "PRF-01-VERHOEFF" in proof_ids
    assert "PRF-02-MERKLE" in proof_ids
    assert "PRF-03-TRBAC" in proof_ids
    assert "PRF-04-BTG-VAULT" in proof_ids
    assert "PRF-05-SQLMED" in proof_ids
    assert "PRF-06-VECTOR-CLOCK" in proof_ids

    for p in proofs:
        assert p.verified is True
        assert len(p.formal_statement) > 20
        assert len(p.implementation_file) > 0
        assert len(p.verification_suite) > 0


def test_specific_verhoeff_proof_invariants(fresh_service: MonographService):
    """Verify mathematical properties of the Dihedral Group D5 Verhoeff checksum proof."""
    p = fresh_service.get_proof("PRF-01-VERHOEFF")
    assert p is not None
    assert p.category == ProofCategoryEnum.CRYPTOGRAPHIC_INVARIANT
    assert "Dihedral Group D5" in p.title
    assert "100% detection of all single-digit" in p.formal_statement
    assert p.mathematical_expression is not None
    assert "backend/app/services/abdm_issuance_service.py" in p.implementation_file


def test_specific_merkle_proof_invariants(fresh_service: MonographService):
    """Verify mathematical properties of the append-only cryptographic ledger proof."""
    p = fresh_service.get_proof("PRF-02-MERKLE")
    assert p is not None
    assert p.category == ProofCategoryEnum.CRYPTOGRAPHIC_INVARIANT
    assert "H(B_{i-1})" in p.formal_statement
    assert "SHA-256" in p.mathematical_expression
    assert "backend/app/services/audit_ledger_service.py" in p.implementation_file


def test_specific_trbac_proof_invariants(fresh_service: MonographService):
    """Verify Scoped Territorial RBAC boundary invariant proof."""
    p = fresh_service.get_proof("PRF-03-TRBAC")
    assert p is not None
    assert p.category == ProofCategoryEnum.SOVEREIGN_HIERARCHY
    assert "territorial jurisdiction" in p.formal_statement
    assert "LGD" in p.mathematical_expression
    assert "backend/app/services/delegation_service.py" in p.implementation_file


def test_specific_btg_vault_proof_invariants(fresh_service: MonographService):
    """Verify Zero-Knowledge Break-The-Glass Argon2id vault isolation proof."""
    p = fresh_service.get_proof("PRF-04-BTG-VAULT")
    assert p is not None
    assert p.category == ProofCategoryEnum.SECURITY_GUARANTEE
    assert "Argon2id" in p.formal_statement
    assert "AES-256-GCM" in p.formal_statement
    assert "65536" in p.mathematical_expression


def test_specific_sqlmed_proof_invariants(fresh_service: MonographService):
    """Verify strict read-only Foreign Data Wrapper invariant proof."""
    p = fresh_service.get_proof("PRF-05-SQLMED")
    assert p is not None
    assert p.category == ProofCategoryEnum.SQL_MED_ISOLATION
    assert "read-only transactions" in p.formal_statement
    assert "READ ONLY" in p.mathematical_expression


def test_specific_vector_clock_proof_invariants(fresh_service: MonographService):
    """Verify monotonic sequence ordering in edge sync proof."""
    p = fresh_service.get_proof("PRF-06-VECTOR-CLOCK")
    assert p is not None
    assert p.category == ProofCategoryEnum.STORE_AND_FORWARD_SYNC
    assert "monotonically increasing sequence number" in p.formal_statement
    assert "Seq" in p.mathematical_expression


def test_empirical_benchmark_scorecard_metrics(fresh_service: MonographService):
    """Verify empirical benchmarks achieve or exceed target thresholds."""
    benchmarks = fresh_service.list_benchmarks()
    assert len(benchmarks) >= 8

    # Verify categories present
    cats = {b.category for b in benchmarks}
    assert BenchmarkCategoryEnum.TEST_COVERAGE in cats
    assert BenchmarkCategoryEnum.LATENCY_PERCENTILES in cats
    assert BenchmarkCategoryEnum.MEMORY_FOOTPRINT in cats
    assert BenchmarkCategoryEnum.CONTAINER_SIZE in cats
    assert BenchmarkCategoryEnum.STANDARDS_COMPLIANCE in cats

    # Verify all benchmarks passed
    for b in benchmarks:
        assert b.status in {BenchmarkStatusEnum.EXCEEDED, BenchmarkStatusEnum.MET}


def test_academic_citations_bibtex_and_ieee(fresh_service: MonographService):
    """Verify publication citations contain valid IEEE format and BibTeX entries."""
    citations = fresh_service.list_citations()
    assert len(citations) >= 3

    keys = [c.citation_key for c in citations]
    assert "nirmaya2026sovereign" in keys
    assert "abdm2023sandbox" in keys
    assert "hl7fhir2019r4" in keys

    for c in citations:
        assert c.bibtex.startswith("@")
        assert c.citation_key in c.bibtex
        assert len(c.ieee_format) > 10
        assert c.year >= 2019


def test_api_endpoints_overview_and_chapters(client: TestClient):
    """Verify GET /api/v1/monograph/overview and GET /api/v1/monograph/chapters."""
    overview_resp = client.get("/api/v1/monograph/overview")
    assert overview_resp.status_code == 200
    ov_data = overview_resp.json()
    assert ov_data["total_chapters"] == 10
    assert len(ov_data["chapters"]) == 10

    chapters_resp = client.get("/api/v1/monograph/chapters")
    assert chapters_resp.status_code == 200
    assert len(chapters_resp.json()) == 10


def test_api_endpoints_single_chapter_and_not_found(client: TestClient):
    """Verify GET /api/v1/monograph/chapters/{slug} with valid and invalid slugs."""
    resp = client.get("/api/v1/monograph/chapters/ch-01-national-crisis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chapter_num"] == 1
    assert len(data["sections"]) == 4

    # 404 test
    resp_404 = client.get("/api/v1/monograph/chapters/unknown-chapter")
    assert resp_404.status_code == 404
    err_msg = resp_404.json().get("message", resp_404.json().get("detail", ""))
    assert "not found" in err_msg.lower()


def test_api_endpoints_proofs_and_benchmarks(client: TestClient):
    """Verify GET /api/v1/monograph/proofs, /proofs/{id}, and /benchmarks."""
    # List proofs
    proofs_resp = client.get("/api/v1/monograph/proofs")
    assert proofs_resp.status_code == 200
    assert len(proofs_resp.json()) == 6

    # Single proof
    p_resp = client.get("/api/v1/monograph/proofs/PRF-01-VERHOEFF")
    assert p_resp.status_code == 200
    assert p_resp.json()["proof_id"] == "PRF-01-VERHOEFF"

    # Proof 404
    p_404 = client.get("/api/v1/monograph/proofs/PRF-99-INVALID")
    assert p_404.status_code == 404

    # Benchmarks
    bm_resp = client.get("/api/v1/monograph/benchmarks")
    assert bm_resp.status_code == 200
    assert len(bm_resp.json()) >= 8


def test_api_endpoints_citations(client: TestClient):
    """Verify GET /api/v1/monograph/citations."""
    resp = client.get("/api/v1/monograph/citations")
    assert resp.status_code == 200
    citations = resp.json()
    assert len(citations) >= 3
    assert any(c["citation_key"] == "nirmaya2026sovereign" for c in citations)
