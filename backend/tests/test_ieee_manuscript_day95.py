"""Unit test suite for Day 95 (Milestone 19-05): IEEE Capstone Research Manuscript - Camera-Ready Archival.

Validates:
1. Section V (Conclusion and Future Directions) in LaTeX source and Markdown paper
2. Complete 26-entry BibTeX database in docs/academic/latex/references.bib
3. 100% citation coverage and resolution between LaTeX manuscript and references.bib
4. Automated AST validation script scripts/validate_ieee_latex.py executes with exit code 0
5. Backend schemas and service layer methods for Day 95 deliverable packet
6. Complete 26-item peer-reviewed citation catalog and individual key lookup
7. Official release v1.2.0 archival artifacts (VERSION, RELEASE_NOTES_v1.2.0.md, day-95.md)
"""

import os
import subprocess
import sys
import pytest

from app.schemas.monograph import (
    CitationCatalogSummary,
    IeeeManuscriptDay95Overview,
)
from app.services.monograph_service import monograph_service


EXPECTED_26_KEYS = [
    "patel_opd_congestion",
    "nha_abdm_2023",
    "hl7_fhir_r4",
    "dpdp_act_2023",
    "bartunov_ltree",
    "bernstein_curve25519",
    "verhoeff_checksum",
    "iso_sql_med",
    "mandel_smart_fhir",
    "seebregts_openmrs",
    "bahmni_architecture",
    "biryukov_argon2",
    "gigw_3_0",
    "owasp_asvs",
    "krawczyk_hkdf",
    "dworkin_gcm",
    "merkle_tree",
    "diffie_hellman",
    "sandhu_rbac",
    "dolev_yao",
    "wilcoxon_1945",
    "student_1908",
    "cohen_1988",
    "mohfw_ndhb_2019",
    "gunter_hie_2014",
    "goldreich_crypto",
]


# =============================================================================
# 1. LaTeX Source Invariants for Section V and 26 Citations
# =============================================================================

def test_day95_latex_section5_conclusion_and_future_directions():
    """Verify Section V (Conclusion and Future Directions) exists in LaTeX source."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "academic", "latex", "nirmaya_ieee_manuscript.tex"
    )
    assert os.path.exists(path), f"LaTeX manuscript not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Section V heading and content
    assert r"\section{Conclusion and Future Directions}" in content
    assert r"\label{sec:conclusion}" in content
    assert "post-quantum hybrid cryptographic migration" in content
    assert "ML-KEM" in content or "FIPS 203" in content
    assert "SMART-on-FHIR" in content
    assert "syndromic surveillance" in content or "epidemiological" in content
    assert r"\bibliographystyle{IEEEtran}" in content
    assert r"\bibliography{references}" in content


def test_day95_bibtex_database_26_references():
    """Verify references.bib exists and contains all 26 required citation keys."""
    bib_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "academic", "latex", "references.bib"
    )
    assert os.path.exists(bib_path), f"references.bib not found at {bib_path}"
    with open(bib_path, "r", encoding="utf-8") as f:
        bib_content = f.read()

    for key in EXPECTED_26_KEYS:
        assert f"{{{key}," in bib_content, f"Citation key '{key}' missing from references.bib"


def test_day95_latex_all_26_keys_cited_in_text():
    """Verify that every single one of the 26 reference keys is cited in the LaTeX text."""
    tex_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "academic", "latex", "nirmaya_ieee_manuscript.tex"
    )
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    for key in EXPECTED_26_KEYS:
        assert key in content, f"Citation key '{key}' never cited in LaTeX text"


def test_day95_latex_ast_validator_executes_cleanly():
    """Verify scripts/validate_ieee_latex.py executes and exits with return code 0."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    script_path = os.path.join(repo_root, "scripts", "validate_ieee_latex.py")
    assert os.path.exists(script_path), f"Validator script not found at {script_path}"

    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    assert result.returncode == 0, f"Validator failed with output:\n{result.stdout}\n{result.stderr}"
    assert "[SUCCESS] IEEE Transactions LaTeX manuscript is 100% syntactically valid and camera-ready!" in result.stdout
    assert "100% of in-text citations resolve to valid BibTeX records." in result.stdout


# =============================================================================
# 2. Markdown Canonical Paper Parity
# =============================================================================

def test_day95_markdown_paper_section5_and_references():
    """Verify Section V and IEEE formatted references exist in canonical markdown paper."""
    md_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "academic", "nirmaya-ieee-research-paper.md"
    )
    assert os.path.exists(md_path), f"Markdown paper not found at {md_path}"
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "## Section V: Conclusion and Future Directions" in content
    assert "Post-Quantum Hybrid Cryptographic Migration" in content
    assert "Cross-Border SMART-on-FHIR Federation" in content
    assert "## References" in content

    # Check that formatted reference entries exist from [1] through [26]
    for i in range(1, 27):
        assert f"[{i}]" in content, f"Reference [{i}] missing from markdown paper"


# =============================================================================
# 3. Backend Service Layer Verification
# =============================================================================

def test_monograph_service_citation_catalog_summary():
    """Verify monograph_service.get_citation_catalog_summary() returns 26 peer-reviewed citations."""
    summary: CitationCatalogSummary = monograph_service.get_citation_catalog_summary()
    assert summary.total_citations == 26
    assert summary.peer_reviewed_count == 26
    assert summary.ieee_format_count == 26
    assert summary.bibtex_format_count == 26
    assert len(summary.citations) == 26

    # Verify keys match expected catalog
    actual_keys = [c.citation_key for c in summary.citations]
    for key in EXPECTED_26_KEYS:
        assert key in actual_keys, f"Expected key '{key}' not in catalog summary"

    # Verify every citation has valid IEEE format, BibTeX entry, and non-empty metadata
    for item in summary.citations:
        assert len(item.title) > 0
        assert len(item.authors) > 0
        assert len(item.venue) > 0
        assert len(item.doi_or_url) > 0
        assert item.bibtex.startswith("@")
        assert item.citation_key in item.bibtex
        assert len(item.ieee_format) > 15


def test_monograph_service_get_citation_individual_lookup():
    """Verify monograph_service.get_citation() retrieves individual citations correctly."""
    c_patel = monograph_service.get_citation("patel_opd_congestion")
    assert c_patel is not None
    assert c_patel.year == 2015
    assert "Assuring health coverage for all in India" in c_patel.title

    c_bernstein = monograph_service.get_citation("bernstein_curve25519")
    assert c_bernstein is not None
    assert c_bernstein.year == 2006
    assert "Curve25519" in c_bernstein.title

    c_wilcoxon = monograph_service.get_citation("wilcoxon_1945")
    assert c_wilcoxon is not None
    assert c_wilcoxon.year == 1945
    assert "Individual Comparisons by Ranking Methods" in c_wilcoxon.title

    c_none = monograph_service.get_citation("non_existent_key_999")
    assert c_none is None


def test_monograph_service_ieee_manuscript_day95_overview():
    """Verify monograph_service.get_ieee_manuscript_day95() returns complete overview."""
    ov: IeeeManuscriptDay95Overview = monograph_service.get_ieee_manuscript_day95()
    assert ov.milestone == "19-05 (Day 95)"
    assert ov.release_version == "1.2.0"
    assert ov.target_format == "IEEE Transactions 2-Column Camera-Ready"
    assert ov.total_sections_count == 5
    assert ov.total_tables_count == 8
    assert ov.total_algorithms_count == 3
    assert ov.total_citations_count == 26
    assert ov.statistical_significance_p_value == "p < 0.001"
    assert ov.cumulative_verified_tests >= 1030
    assert ov.status == "CAMERA_READY_PUBLISHED"


# =============================================================================
# 4. Official Release v1.2.0 Archival Artifacts
# =============================================================================

def test_day95_version_file_is_1_2_0():
    """Verify root VERSION file is set to 1.2.0."""
    version_path = os.path.join(os.path.dirname(__file__), "..", "..", "VERSION")
    assert os.path.exists(version_path), f"VERSION file not found at {version_path}"
    with open(version_path, "r", encoding="utf-8") as f:
        version = f.read().strip()
    assert version == "1.2.0", f"Expected version '1.2.0', got '{version}'"


def test_day95_release_notes_v1_2_0_exists():
    """Verify RELEASE_NOTES_v1.2.0.md exists and contains critical sections."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "RELEASE_NOTES_v1.2.0.md")
    assert os.path.exists(path), f"RELEASE_NOTES_v1.2.0.md not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "NIRMAYA Release Notes: v1.2.0" in content
    assert "Academic Sovereign Archival & Scientific Capstone Publication" in content
    assert "Cumulative 95-Day Engineering Metrics" in content
    assert "Phase 6 (Days 91–95) Scientific Deliverables" in content
    assert "26 Primary Sources" in content
    assert "p < 0.001" in content


def test_day95_engineering_journey_log_exists():
    """Verify docs/journey/month-5/day-95.md exists and contains day 95 documentation."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "journey", "month-5", "day-95.md"
    )
    assert os.path.exists(path), f"day-95.md not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# Day 95: Complete BibTeX Citation Database" in content
    assert "Milestone:** 19-05" in content
    assert "Target Release:** `v1.2.0`" in content
    assert "Complete 26 Peer-Reviewed Citation Catalog" in content
    assert "Automated LaTeX AST Validator Verification" in content
