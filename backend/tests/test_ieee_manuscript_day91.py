"""Unit test suite for Day 91 (Milestone 19-01): IEEE Capstone Research Manuscript.

Validates:
1. Title, author, and milestone metadata
2. 250-word abstract length and content invariants
3. 10 IEEE index terms verification
4. 6 Core Scientific Contributions and SLA thresholds
5. Table I comparative matrix across all 9 dimensions
6. LaTeX IEEEtran source file formatting and syntax
7. BibTeX reference database completeness
8. Canonical publication Markdown parity
9. Journey documentation existence
10. Monograph service data structures and schemas
"""

import os
import pytest

from app.schemas.monograph import (
    IeeeManuscriptDay91Overview,
    ScientificContributionItem,
    TableIRelatedWorksMatrix,
)
from app.services.monograph_service import monograph_service


# =============================================================================
# 1. Metadata and Title Invariants
# =============================================================================

def test_day91_manuscript_title_and_metadata():
    """Verify IEEE manuscript title, author attribution, and milestone codes."""
    packet = monograph_service.get_ieee_manuscript_day91()
    assert "NIRMAYA: A High-Throughput, Cryptographically-Federated Digital Health" in packet.title
    assert "Indian LGD Territorial Governance" in packet.title
    assert packet.author == "Suryansh Swarn"
    assert "Core Architecture Lead" in packet.affiliation
    assert packet.milestone == "19-01 (Day 91)"
    assert packet.release_version == "1.2.0"
    assert packet.status == "OFFICIALLY_COMPOSED"


# =============================================================================
# 2. Abstract Word Count & Content Invariants
# =============================================================================

def test_day91_abstract_word_count_and_scope():
    """Verify abstract word count is within IEEE Transactions standards (200-300 words)."""
    packet = monograph_service.get_ieee_manuscript_day91()
    word_count = len(packet.abstract_text.split())
    assert 200 <= word_count <= 300
    assert packet.abstract_word_count == word_count

    # Check key concepts
    assert "1.4 billion" in packet.abstract_text
    assert "Local Government Directory" in packet.abstract_text
    assert "ltree" in packet.abstract_text
    assert "Curve25519" in packet.abstract_text
    assert "DPDP" in packet.abstract_text
    assert "50,000 req/s" in packet.abstract_text
    assert "P99 = 18.5 ms" in packet.abstract_text


# =============================================================================
# 3. 10 IEEE Index Terms Verification
# =============================================================================

def test_day91_index_terms_count_and_content():
    """Verify exact 10 IEEE Index Terms are present."""
    packet = monograph_service.get_ieee_manuscript_day91()
    assert len(packet.index_terms) == 10

    expected_terms = [
        "Digital Public Infrastructure (DPI)",
        "Health Level Seven (HL7) FHIR Release 4",
        "Ayushman Bharat Digital Mission (ABDM)",
        "Curve25519 Elliptic Curve Cryptography",
        "Authenticated Encryption with Associated Data (AEAD)",
        "PostgreSQL ltree Hierarchical Indexing",
        "Local Government Directory (LGD)",
        "Scoped Territorial Role-Based Access Control (Scoped TRBAC)",
        "Digital Personal Data Protection Act 2023 (DPDP Act Sec 9)",
        "Zero-Knowledge Emergency Vault (Argon2id)",
    ]
    for term in expected_terms:
        assert term in packet.index_terms


# =============================================================================
# 4. 6 Core Scientific Contributions
# =============================================================================

def test_day91_scientific_contributions_count_and_slas():
    """Verify that all 6 core scientific contributions are articulated with quantitative SLAs."""
    packet = monograph_service.get_ieee_manuscript_day91()
    assert len(packet.scientific_contributions) == 6

    for idx, contrib in enumerate(packet.scientific_contributions, start=1):
        assert contrib.number == idx
        assert len(contrib.title) > 0
        assert len(contrib.description) > 0
        assert len(contrib.metric_sla) > 0
        assert contrib.verified is True

    # Check specific SLAs
    titles = [c.title for c in packet.scientific_contributions]
    assert any("LGD Administrative Hierarchy" in t for t in titles)
    assert any("ABDM M1–M3 Asynchronous Cryptographic Bridge" in t for t in titles)
    assert any("Family Health Proxy Engine" in t for t in titles)
    assert any("National Gateway Token-Bucket Rate Shield" in t for t in titles)
    assert any("Express 45-Second Outpatient Consultation" in t for t in titles)
    assert any("SQL/MED Legacy HIS Federation" in t for t in titles)


# =============================================================================
# 5. Table I Related Works & Research Gaps Matrix
# =============================================================================

def test_day91_table_1_matrix_dimensions_and_platforms():
    """Verify Table I comparative matrix evaluates all 6 platforms across 9 dimensions."""
    table_1 = monograph_service.get_table_1_matrix()
    assert table_1.table_id == "TABLE-I-RELATED-WORKS"
    assert table_1.dimensions_count == 9
    assert len(table_1.rows) == 9

    assert "OpenMRS" in table_1.evaluated_platforms
    assert "Bahmni" in table_1.evaluated_platforms
    assert "Epic Systems" in table_1.evaluated_platforms
    assert "Medplum" in table_1.evaluated_platforms
    assert "ABDM Reference" in table_1.evaluated_platforms
    assert "NIRMAYA (Proposed)" in table_1.evaluated_platforms


def test_day91_table_1_nirmaya_advantages_verified():
    """Verify NIRMAYA's specific architectural advantages across Table I rows."""
    table_1 = monograph_service.get_table_1_matrix()
    row_map = {r.dimension: r for r in table_1.rows}

    assert "Sovereign Dual-Plane" in row_map["1. System Topology"].nirmaya
    assert "689-line NRCeS profile validator" in row_map["2. HL7 FHIR R4 Native"].nirmaya
    assert "Full Production-Grade In-Engine" in row_map["3. ABDM M1–M3 Support"].nirmaya
    assert "ltree" in row_map["4. LGD Hierarchy Traversal"].nirmaya
    assert "50,000 req/s" in row_map["6. Gateway Ingress Capacity"].nirmaya
    assert "18.5 ms" in row_map["7. Outpatient Velocity SLA"].nirmaya
    assert "SQL/MED" in row_map["8. Legacy HIS Federation"].nirmaya
    assert "< 512MB" in row_map["9. Edge RAM Footprint"].nirmaya


# =============================================================================
# 6. Publication File Existence & Syntax Verification
# =============================================================================

def test_day91_latex_manuscript_source_exists_and_valid():
    """Verify that docs/academic/latex/nirmaya_ieee_manuscript.tex exists and is valid IEEEtran."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "academic", "latex", "nirmaya_ieee_manuscript.tex")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert r"\documentclass[journal,twocolumn]{IEEEtran}" in content
    assert r"\title{NIRMAYA:" in content
    assert r"\begin{abstract}" in content
    assert r"\begin{IEEEkeywords}" in content
    assert r"\begin{table*}[t]" in content
    assert r"\caption{Summary of Related Approaches and Identified Research Gaps}" in content
    assert r"\bibliography{references}" in content


def test_day91_bibtex_reference_database_exists_and_valid():
    """Verify that docs/academic/latex/references.bib exists and contains primary citations."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "academic", "latex", "references.bib")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "nha_abdm_2023" in content
    assert "hl7_fhir_r4" in content
    assert "dpdp_act_2023" in content
    assert "bernstein_curve25519" in content
    assert "seebregts_openmrs" in content
    assert "bartunov_ltree" in content
    assert "verhoeff_checksum" in content


def test_day91_canonical_markdown_paper_exists_and_valid():
    """Verify that docs/academic/nirmaya-ieee-research-paper.md exists and is complete."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "academic", "nirmaya-ieee-research-paper.md")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# NIRMAYA: A High-Throughput, Cryptographically-Federated" in content
    assert "## Abstract" in content
    assert "## Section I: Introduction" in content
    assert "### 1.1 The Digital Public Health Trilemma" in content
    assert "### 1.2 Core Scientific Contributions" in content
    assert "## Section II: Related Work and Identified Research Gaps" in content
    assert "#### Table I: Summary of Related Approaches and Identified Research Gaps" in content
    assert "## References" in content
    assert len(content) > 5000


def test_day91_journey_documentation_exists():
    """Verify that docs/journey/month-5/day-91.md and overview.md exist."""
    day91_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "journey", "month-5", "day-91.md")
    overview_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "journey", "month-5", "overview.md")
    assert os.path.exists(day91_path)
    assert os.path.exists(overview_path)

