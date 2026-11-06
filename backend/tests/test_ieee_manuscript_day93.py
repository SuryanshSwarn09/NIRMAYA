"""Unit test suite for Day 93 (Milestone 19-03): IEEE Capstone Research Manuscript - Section III-F.

Validates:
1. Section III-F (Family Health Proxy Logic & Age-of-Majority State Machine) in LaTeX source
2. Algorithm 3 (Zero-Contamination Family Proxy Delegation) pseudocode, complexities, and targets
3. Table II (Illustrative Example Trace Table) spanning all 8 operational phases with P99 SLAs
4. Table III (Summary of Mathematical and Cryptographic Notation) covering 16 variables
5. Family proxy discrete state machine transitions (single guardian, dual guardian, custody dispute, 18y conversion)
6. Canonical publication Markdown parity with KaTeX display equations and Mermaid diagram
7. Backend schemas, service layer methods, and REST endpoints
8. Day 93 engineering journey log existence
"""

import os
import pytest

from app.schemas.monograph import (
    AlgorithmListingItem,
    IeeeManuscriptDay93Overview,
    NotationTableSummary,
    TraceTableSummary,
)
from app.services.monograph_service import monograph_service


# =============================================================================
# 1. LaTeX Source Invariants for Section III-F, Algorithm 3, Tables II & III
# =============================================================================

def test_day93_latex_section3f_and_elements_exist():
    """Verify Section III-F, Algorithm 3, Table II, and Table III in LaTeX source."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "academic", "latex", "nirmaya_ieee_manuscript.tex"
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Section III-F headers
    assert r"\subsection{Family Health Proxy Logic and Age-of-Majority State Machine}" in content
    assert r"\subsubsection{Cryptographic Separation of Guardian and Ward Vaults}" in content
    assert r"\subsubsection{Multi-Guardian Dual-Signature Custody Dispute Interceptor}" in content
    assert r"\subsubsection{Deterministic 18-Year Age-of-Majority Conversion State Machine}" in content

    # Mathematical formulas
    assert r"\text{Enc}_{K_G}(V_G) \cap \text{Enc}_{K_W}(V_W) = \emptyset" in content
    assert r"\Phi_{\text{consent}}(W)" in content
    assert r"\tau_{\text{proxy}}(G, W, t)" in content

    # Algorithm 3
    assert r"\caption{Zero-Contamination Family Proxy Delegation and Age-of-Majority State Transition}" in content
    assert r"\label{alg:family_proxy}" in content

    # Table II and Table III
    assert r"\caption{Illustrative Example Trace Table: End-to-End Cryptographic and Clinical Encounter Life-Cycle}" in content
    assert r"\label{tab:encounter_trace}" in content
    assert r"\caption{Summary of Mathematical and Cryptographic Notation}" in content
    assert r"\label{tab:notation}" in content


# =============================================================================
# 2. Algorithm 3 Specification Verification
# =============================================================================

def test_day93_algorithm_3_specifications():
    """Verify Algorithm 3 listing, complexities, inputs, and outputs."""
    algos = monograph_service.get_algorithm_listings()
    alg3 = next((a for a in algos if a.number == 3), None)
    assert alg3 is not None
    assert alg3.algorithm_id == "ALG-03-FAMILY-PROXY"
    assert "Family Proxy Delegation" in alg3.title
    assert alg3.complexity_time == "O(1)"
    assert alg3.complexity_space == "O(1)"
    assert len(alg3.inputs) == 7
    assert len(alg3.outputs) == 2
    assert "AGE_OF_MAJORITY_TRANSITION" in alg3.pseudocode
    assert "CUSTODY_DISPUTE_LOCKED" in alg3.pseudocode
    assert "MISSING_CO_GUARDIAN_SIGNATURE" in alg3.pseudocode
    assert "Assert" in alg3.pseudocode
    assert "SHA-256" in alg3.pseudocode
    assert alg3.target_module == "app.services.family_proxy_vault_service"


# =============================================================================
# 3. Table II (Trace Table) Verification
# =============================================================================

def test_day93_trace_table_steps_and_sla():
    """Verify Table II encounter trace table has 8 steps and meets SLA budgets."""
    trace = monograph_service.get_trace_table_steps()
    assert trace.table_id == "TABLE-II-ENCOUNTER-TRACE"
    assert trace.total_steps == 8
    assert len(trace.steps) == 8

    # Validate all 8 operational phases exist in sequential order
    expected_phases = [
        "Patient ABHA Registration",
        "Outpatient Slot Allocation",
        "ABDM Consent Verification",
        "Ephemeral Key Agreement",
        "Symmetric Key Derivation",
        "Health Record Encryption",
        "HIU Record Ingest & GHASH",
        "Forensic Ledger Sealing",
    ]
    for idx, expected_phase in enumerate(expected_phases, 1):
        step = trace.steps[idx - 1]
        assert step.step_number == idx
        assert step.operational_phase == expected_phase
        # Individual step latency must be sub-10ms
        assert step.measured_p99_sla_ms < 10.0
        assert step.complexity_time != ""
        assert step.security_invariant_enforced != ""

    # Total P99 latency must be under 50ms (OPD consultation SLA)
    assert trace.total_p99_latency_budget_ms < 50.0
    assert trace.total_p99_latency_budget_ms == 16.07


# =============================================================================
# 4. Table III (Notation Table) Verification
# =============================================================================

def test_day93_notation_table_catalog():
    """Verify Table III indexes all 16 formal mathematical and cryptographic variables."""
    notation = monograph_service.get_notation_table()
    assert notation.table_id == "TABLE-III-NOTATION"
    assert notation.symbols_count == 16
    assert len(notation.items) == 16

    symbols = [item.symbol for item in notation.items]
    expected_symbols = [
        "D_5",
        "F_(2^255-19)",
        "sk",
        "pk",
        "K_shared",
        "PRK",
        "K_enc",
        "IV",
        "AAD",
        "T",
        "H_i",
        "Q",
        "<@",
        "V_G",
        "V_W",
        "tau_proxy",
    ]
    for sym in expected_symbols:
        assert sym in symbols

    for item in notation.items:
        assert item.latex_symbol != ""
        assert item.algebraic_domain != ""
        assert item.formal_description != ""
        assert item.first_occurrence != ""


# =============================================================================
# 5. Family Proxy State Machine Transitions
# =============================================================================

def test_day93_family_proxy_state_transitions():
    """Verify Section III-F discrete state transitions."""
    transitions = monograph_service.get_family_proxy_state_transitions()
    assert len(transitions) == 4

    to_states = [t.to_state for t in transitions]
    assert "ACTIVE_PROXY_SINGLE_GUARDIAN" in to_states
    assert "ACTIVE_PROXY_DUAL_GUARDIAN" in to_states
    assert "CUSTODY_DISPUTE_FROZEN" in to_states
    assert "SOVEREIGN_ADULT" in to_states

    # Check age of majority transition
    adult_trans = next(t for t in transitions if t.to_state == "SOVEREIGN_ADULT")
    assert "18" in adult_trans.condition_predicate
    assert "zero-touch" in adult_trans.security_action.lower()


# =============================================================================
# 6. Canonical Markdown Document Parity
# =============================================================================

def test_day93_canonical_markdown_section3f_exists():
    """Verify docs/academic/nirmaya-ieee-research-paper.md contains Section 3.6 and tables."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "academic", "nirmaya-ieee-research-paper.md"
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "### 3.6 Family Health Proxy Logic & Age-of-Majority State Machine" in content
    assert "stateDiagram-v2" in content
    assert "Algorithm 3: Zero-Contamination Family Proxy Delegation" in content
    assert "Table II: Illustrative Example Trace Table" in content
    assert "Table III: Summary of Mathematical and Cryptographic Notation" in content
    assert r"\text{Enc}_{K_G}(V_G) \cap \text{Enc}_{K_W}(V_W) = \emptyset" in content
    assert r"\Phi_{\text{consent}}(W)" in content


# =============================================================================
# 7. Day 93 Deliverable Overview Packet
# =============================================================================

def test_day93_ieee_manuscript_overview_packet():
    """Verify Day 93 deliverable packet aggregation."""
    packet = monograph_service.get_ieee_manuscript_day93()
    assert packet.milestone == "19-03 (Day 93)"
    assert packet.release_version == "1.2.0"
    assert "Section III-F" in packet.section_3_f_title
    assert packet.algorithm_3.number == 3
    assert packet.table_2_trace.total_steps == 8
    assert packet.table_3_notation.symbols_count == 16
    assert len(packet.state_transitions) == 4
    assert packet.status == "OFFICIALLY_COMPOSED"


# =============================================================================
# 8. Journey Documentation Existence
# =============================================================================

def test_day93_journey_log_exists():
    """Verify docs/journey/month-5/day-93.md exists and contains required sections."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "journey", "month-5", "day-93.md"
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Day 93: Family Health Proxy Logic, Algorithm 3" in content
    assert "19-03" in content
    assert "stateDiagram-v2" in content
    assert len(content) > 2500
