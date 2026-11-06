"""Unit test suite for Day 92 (Milestone 19-02): IEEE Capstone Research Manuscript - Section III.

Validates:
1. Section III (System Architecture & Mathematical Formulations) in LaTeX source
2. Algorithm 1 and Algorithm 2 pseudocode, complexities, and targets
3. 5 core mathematical models (Verhoeff D5, Curve25519, HKDF, AES-256-GCM, Merkle)
4. Threat model definitions (A_net, A_broker, A_edge) and DPDP Act Sec 9
5. Canonical publication Markdown parity with KaTeX display equations
6. Backend schemas, service methods, and REST endpoints
7. Day 92 engineering journey log existence
"""

import os
import pytest

from app.schemas.monograph import (
    AlgorithmListingItem,
    IeeeManuscriptDay92Overview,
    MathematicalFormulationItem,
    ThreatModelItem,
)
from app.services.monograph_service import monograph_service


# =============================================================================
# 1. LaTeX Source Invariants for Section III
# =============================================================================

def test_day92_latex_section3_and_algorithms_exist():
    """Verify Section III and algorithms exist in LaTeX source."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "academic", "latex", "nirmaya_ieee_manuscript.tex"
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert r"\section{System Architecture and Mathematical Formulations}" in content
    assert r"\subsection{Threat Model and Formal Security Guarantees}" in content
    assert r"\subsection{Dual-Plane Air-Gap Topology}" in content
    assert r"\subsection{Inbound Consent Notification and Ephemeral Key Pipeline}" in content
    assert r"\subsection{Mathematical Formulations}" in content
    assert r"\subsection{Typeset Core Algorithms}" in content

    # Check algorithms
    assert r"\begin{algorithm}[t]" in content
    assert r"\caption{Asynchronous Curve25519-HKDF-AES256 Encrypted Health Information Transfer Protocol}" in content
    assert r"\caption{Sub-2ms 6-Tier Indian LGD Territorial Scope Traversal with PostgreSQL \texttt{ltree}}" in content

    # Check equations
    assert r"y^2 = x^3 + 486662x^2 + x" in content
    assert r"K_{\text{shared}} = \text{X25519}" in content
    assert r"\sum_{i=0}^{n-1} F(i+1, c_i) = 0" in content
    assert r"HMAC-SHA256" in content


# =============================================================================
# 2. Algorithm 1 and 2 Listings Verification
# =============================================================================

def test_day92_algorithm_listings_specifications():
    """Verify Algorithm 1 and 2 listings, complexities, and inputs/outputs."""
    algos = monograph_service.get_algorithm_listings()
    assert len(algos) >= 2

    algo1 = algos[0]
    assert algo1.number == 1
    assert "Curve25519-HKDF-AES256" in algo1.title
    assert algo1.complexity_time == "O(|P|)"
    assert algo1.complexity_space == "O(|P|)"
    assert len(algo1.inputs) == 4
    assert len(algo1.outputs) == 5
    assert "X25519" in algo1.pseudocode
    assert "AES-256-GCM-Encrypt" in algo1.pseudocode
    assert "SecureWipe" in algo1.pseudocode

    algo2 = algos[1]
    assert algo2.number == 2
    assert "PostgreSQL ltree" in algo2.title
    assert algo2.complexity_time == "O(log N + k)"
    assert algo2.complexity_space == "O(k)"
    assert len(algo2.inputs) == 3
    assert len(algo2.outputs) == 2
    assert "GiST Index Traversal" in algo2.pseudocode
    assert "EvaluateTRBAC" in algo2.pseudocode


# =============================================================================
# 3. 5 Mathematical Formulations Verification
# =============================================================================

def test_day92_mathematical_formulations_count_and_domains():
    """Verify all 5 formal mathematical equations, domains, and invariants."""
    math_items = monograph_service.get_mathematical_formulations()
    assert len(math_items) == 5

    id_map = {m.formulation_id: m for m in math_items}

    # 1. Verhoeff D5
    assert "MATH-01-VERHOEFF-D5" in id_map
    v = id_map["MATH-01-VERHOEFF-D5"]
    assert "Dihedral Group D5" in v.algebraic_domain
    assert "D_5" in v.latex_formula

    # 2. Curve25519
    assert "MATH-02-CURVE25519-ECDH" in id_map
    c = id_map["MATH-02-CURVE25519-ECDH"]
    assert "486662" in c.latex_formula
    assert "X25519" in c.latex_formula

    # 3. HKDF
    assert "MATH-03-HKDF-SHA256" in id_map
    h = id_map["MATH-03-HKDF-SHA256"]
    assert "PRK" in h.latex_formula
    assert "HMAC-SHA256" in h.latex_formula

    # 4. AES-GCM
    assert "MATH-04-AES-256-GCM-AEAD" in id_map
    a = id_map["MATH-04-AES-256-GCM-AEAD"]
    assert "GHASH" in a.latex_formula
    assert "AES-CTR" in a.latex_formula

    # 5. Merkle Chain
    assert "MATH-05-MERKLE-AUDIT-CHAIN" in id_map
    m = id_map["MATH-05-MERKLE-AUDIT-CHAIN"]
    assert "SHA-256" in m.latex_formula
    assert "H_{i-1}" in m.latex_formula


# =============================================================================
# 4. Threat Model & Adversary Classification
# =============================================================================

def test_day92_threat_model_summary():
    """Verify Section III-A threat model adversary classes and security targets."""
    threats = monograph_service.get_threat_model_summary()
    assert len(threats) == 3

    code_map = {t.adversary_code: t for t in threats}
    assert "A_net" in code_map
    assert "Dolev-Yao" in code_map["A_net"].formal_model
    assert "A_broker" in code_map
    assert "Honest-but-Curious" in code_map["A_broker"].title
    assert "A_edge" in code_map
    assert "Physical" in code_map["A_edge"].title


# =============================================================================
# 5. Canonical Markdown Document Parity
# =============================================================================

def test_day92_canonical_markdown_section3_exists():
    """Verify that docs/academic/nirmaya-ieee-research-paper.md contains complete Section III."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "academic", "nirmaya-ieee-research-paper.md"
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "## Section III: System Architecture and Mathematical Formulations" in content
    assert "### 3.1 Threat Model & Security Goals" in content
    assert "### 3.2 Dual-Plane Air-Gap Topology" in content
    assert "### 3.3 Inbound Consent Notification and Ephemeral Key Pipeline" in content
    assert "### 3.4 Mathematical Formulations" in content
    assert "#### 1. Dihedral Group $D_5$ Verhoeff Checksum" in content
    assert "#### 2. Curve25519 ECDH Key Agreement" in content
    assert "#### Algorithm 1: Asynchronous Curve25519-HKDF-AES256 Encrypted Transfer Protocol" in content
    assert "#### Algorithm 2: Sub-2ms 6-Tier Indian LGD Territorial Scope Traversal with PostgreSQL ltree" in content


# =============================================================================
# 6. Service & Day 92 Deliverable Schema
# =============================================================================

def test_day92_ieee_manuscript_overview_packet():
    """Verify Day 92 deliverable packet aggregation."""
    packet = monograph_service.get_ieee_manuscript_day92()
    assert packet.milestone == "19-02 (Day 92)"
    assert packet.release_version == "1.2.0"
    assert len(packet.threat_model) == 3
    assert len(packet.mathematical_formulations) == 5
    assert len(packet.algorithms) == 2
    assert len(packet.consent_pipeline_phases) == 4
    assert packet.status == "OFFICIALLY_COMPOSED"


def test_day92_journey_log_exists():
    """Verify that docs/journey/month-5/day-92.md exists and is complete."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "journey", "month-5", "day-92.md"
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Day 92: Threat Model, Dual-Plane Air-Gap Topology" in content
    assert "19-02" in content
    assert len(content) > 3000

