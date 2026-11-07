"""Unit test suite for Day 94 (Milestone 19-04): IEEE Capstone Research Manuscript - Section IV.

Validates:
1. Section IV (System Implementation and Empirical Evaluation) in LaTeX source
2. Table IV (Experimental Testbed Specifications)
3. Table V (High-Throughput Gateway Ingress Benchmarks)
4. Table VI (End-to-End Cryptographic Transfer Pipeline Breakdown)
5. Table VII (Indian LGD 6-Tier Hierarchical Traversal Latency Comparison)
6. Table VIII (Statistical Hypothesis Testing and Effect Size Summary with p < 0.001)
7. Low-resource edge appliance RAM budget (480 MB <= 512 MB ceiling)
8. Canonical publication Markdown parity with Tables IV-VIII and statistical formulas
9. Backend schemas, service layer methods, and REST endpoints
10. Day 94 engineering journey log existence
"""

import os
import pytest

from app.schemas.monograph import (
    IeeeManuscriptDay94Overview,
    TableIVTestbedSummary,
    TableVGatewayIngressSummary,
    TableVICryptoPipelineSummary,
    TableVIILgdTraversalSummary,
    TableVIIIStatisticalSignificanceSummary,
)
from app.services.monograph_service import monograph_service


# =============================================================================
# 1. LaTeX Source Invariants for Section IV and Tables IV-VIII
# =============================================================================

def test_day94_latex_section4_and_tables_exist():
    """Verify Section IV, subsections, and Tables IV-VIII in LaTeX source."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "academic", "latex", "nirmaya_ieee_manuscript.tex"
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Section IV and subsection headings
    assert r"\section{System Implementation and Empirical Evaluation}" in content
    assert r"\label{sec:empirical_eval}" in content
    assert r"\subsection{Experimental Testbed and Benchmark Setup}" in content
    assert r"\subsection{High-Throughput Gateway Ingress and Concurrency Saturation}" in content
    assert r"\subsection{End-to-End Cryptographic Transfer and Data Pipeline Profiling}" in content
    assert r"\subsection{Indian LGD Hierarchical Query Traversal: PostgreSQL \texttt{ltree} with GiST}" in content
    assert r"\subsection{Low-Resource Edge Appliance Footprint and Offline Synchronization}" in content
    assert r"\subsection{Statistical Significance Testing and Effect Size Analysis}" in content

    # Tables IV through VIII
    assert r"\caption{Experimental Testbed and Benchmark Specifications}" in content
    assert r"\label{tab:testbed_specs}" in content
    assert r"\caption{High-Throughput Gateway Ingress and Concurrency Saturation Benchmarks}" in content
    assert r"\label{tab:gateway_benchmarks}" in content
    assert r"\caption{End-to-End Cryptographic Transfer Pipeline Breakdown and Comparative Evaluation}" in content
    assert r"\label{tab:crypto_comparison}" in content
    assert r"\caption{Indian LGD 6-Tier Hierarchical Traversal Latency Comparison}" in content
    assert r"\label{tab:lgd_benchmarks}" in content
    assert r"\caption{Statistical Hypothesis Testing and Effect Size Summary ($n = 10,000$ Paired Executions)}" in content
    assert r"\label{tab:statistical_tests}" in content

    # Statistical formulas
    assert r"t = \frac{\bar{D} - \mu_0}{s_D / \sqrt{n}}" in content
    assert r"W = \sum_{i=1}^{n'}" in content
    assert r"z = \frac{W - \frac{n'(n'+1)}{4}}" in content


# =============================================================================
# 2. Table IV (Testbed Environment) Verification
# =============================================================================

def test_day94_table_4_testbed_specifications():
    """Verify Table IV testbed environment specifications."""
    testbed = monograph_service.get_table_4_testbed()
    assert testbed.table_id == "TABLE-IV-TESTBED-SPECS"
    assert testbed.items_count == 7
    assert len(testbed.items) == 7

    components = [item.component for item in testbed.items]
    assert "Cloud Node Cluster" in components
    assert "Edge Node Appliance" in components
    assert "Database Engine" in components
    assert "Caching & Rate Limiter" in components
    assert "Application Stack" in components
    assert "Load Generators" in components
    assert "Network Emulation" in components

    edge_spec = next(item for item in testbed.items if item.component == "Edge Node Appliance")
    assert "Celeron N5105" in edge_spec.specification
    assert "4GB" in edge_spec.specification


# =============================================================================
# 3. Table V (Gateway Ingress Benchmarks) Verification
# =============================================================================

def test_day94_table_5_gateway_ingress_benchmarks():
    """Verify Table V gateway ingress saturation benchmarks."""
    gw = monograph_service.get_table_5_gateway_ingress()
    assert gw.table_id == "TABLE-V-GATEWAY-INGRESS"
    assert gw.rows_count == 5
    assert len(gw.rows) == 5
    assert gw.max_sustained_rps == 49974

    loads = [row.nominal_load_rps for row in gw.rows]
    assert loads == [1000, 5000, 10000, 25000, 50000]

    # Under 10k req/s, P99 must be sub-10ms
    row_10k = next(r for r in gw.rows if r.nominal_load_rps == 10000)
    assert row_10k.latency_p99_ms < 10.0
    assert row_10k.error_rate_pct == 0.00

    # At 50k req/s, error rate must remain under 0.05%
    row_50k = next(r for r in gw.rows if r.nominal_load_rps == 50000)
    assert row_50k.error_rate_pct < 0.05
    assert row_50k.latency_p99_ms == 22.40
    assert row_50k.cpu_utilization_pct < 90.0


# =============================================================================
# 4. Table VI (Crypto Pipeline Breakdown) Verification
# =============================================================================

def test_day94_table_6_crypto_pipeline_comparison():
    """Verify Table VI cryptographic transfer pipeline breakdown."""
    crypto = monograph_service.get_table_6_crypto_pipeline()
    assert crypto.table_id == "TABLE-VI-CRYPTO-PIPELINE"
    assert crypto.total_pipeline_p99_ms == 7.14
    assert crypto.speedup_vs_bahmni == 14.8
    assert crypto.speedup_vs_openmrs == 22.3
    assert len(crypto.rows) == 6

    phases = [r.phase_operation for r in crypto.rows]
    assert "ABDM Consent Signature Verification" in phases
    assert "Curve25519 Ephemeral Key Agreement" in phases
    assert "HKDF-SHA256 Key Derivation" in phases
    assert "AES-256-GCM Payload Encryption" in phases
    assert "FHIR R4 NRCeS Schema Validation" in phases
    assert "Merkle Ledger Audit Sealing" in phases


# =============================================================================
# 5. Table VII (LGD Traversal Latency) Verification
# =============================================================================

def test_day94_table_7_lgd_traversal_benchmarks():
    """Verify Table VII LGD 6-tier traversal benchmarks."""
    lgd = monograph_service.get_table_7_lgd_traversal()
    assert lgd.table_id == "TABLE-VII-LGD-TRAVERSAL"
    assert lgd.speedup_vs_cte == 32.5
    assert len(lgd.rows) == 4

    archs = [r.indexing_architecture for r in lgd.rows]
    assert "Recursive CTE (Adjacency List)" in archs
    assert "Nested Set Model (Left/Right)" in archs
    assert "Flat String Path Pattern Match" in archs
    assert "PostgreSQL ltree + GiST" in archs

    gist_row = next(r for r in lgd.rows if "ltree" in r.indexing_architecture)
    assert gist_row.latency_p99_ms == 1.42
    assert gist_row.latency_p50_ms == 0.32
    assert "Negligible" in gist_row.write_penalty


# =============================================================================
# 6. Table VIII (Statistical Hypothesis Testing) Verification
# =============================================================================

def test_day94_table_8_statistical_significance_analysis():
    """Verify Table VIII statistical testing: p < 0.001 and Cohen's d > 1.8 across all dimensions."""
    stats = monograph_service.get_table_8_statistical_significance()
    assert stats.table_id == "TABLE-VIII-STATISTICAL-SIGNIFICANCE"
    assert stats.sample_size_n == 10000
    assert stats.all_dimensions_p_value_threshold == "p < 0.001"
    assert len(stats.rows) == 5

    for row in stats.rows:
        assert row.p_value == "p < 0.001"
        assert row.cohens_d >= 1.80
        assert row.t_statistic > 50.0
        assert row.wilcoxon_z > 50.0

    dimensions = [r.dimension for r in stats.rows]
    assert "Gateway Ingress Latency (10k req/s)" in dimensions
    assert "ABDM Crypto Transfer Latency" in dimensions
    assert "LGD 6-Tier Traversal Latency" in dimensions
    assert "Outpatient Prescription Signing" in dimensions
    assert "Edge Cold-Start Initialization" in dimensions


# =============================================================================
# 7. Canonical Markdown Document Parity
# =============================================================================

def test_day94_canonical_markdown_section4_parity():
    """Verify docs/academic/nirmaya-ieee-research-paper.md contains Section IV and Tables IV-VIII."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "academic", "nirmaya-ieee-research-paper.md"
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "## Section IV: System Implementation and Empirical Evaluation" in content
    assert "#### Table IV: Experimental Testbed Specifications" in content
    assert "#### Table V: High-Throughput Gateway Ingress and Concurrency Saturation Benchmarks" in content
    assert "#### Table VI: End-to-End Cryptographic Transfer Pipeline Breakdown and Comparative Evaluation" in content
    assert "#### Table VII: Indian LGD 6-Tier Hierarchical Traversal Latency Comparison" in content
    assert "#### Table VIII: Statistical Hypothesis Testing and Effect Size Summary" in content
    assert "## Section V: Conclusion and Future Directions" in content


# =============================================================================
# 8. Day 94 Deliverable Packet Verification
# =============================================================================

def test_day94_ieee_manuscript_overview_packet():
    """Verify Day 94 deliverable packet aggregation."""
    packet = monograph_service.get_ieee_manuscript_day94()
    assert packet.milestone == "19-04 (Day 94)"
    assert packet.release_version == "1.2.0"
    assert "Section IV" in packet.section_4_title
    assert packet.table_4_testbed.items_count == 7
    assert packet.table_5_gateway_ingress.rows_count == 5
    assert packet.table_6_crypto_pipeline.total_pipeline_p99_ms == 7.14
    assert packet.table_7_lgd_traversal.speedup_vs_cte == 32.5
    assert packet.table_8_statistical_tests.sample_size_n == 10000
    assert packet.edge_appliance_ram_budget_mb == 480
    assert packet.edge_appliance_target_mb == 512
    assert packet.edge_appliance_ram_budget_mb <= packet.edge_appliance_target_mb
    assert packet.status == "OFFICIALLY_COMPOSED"


# =============================================================================
# 9. Journey Documentation Existence
# =============================================================================

def test_day94_journey_log_exists():
    """Verify docs/journey/month-5/day-94.md exists and contains required sections."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "journey", "month-5", "day-94.md"
    )
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Day 94: Experimental Testbed, Empirical System Benchmarks" in content
    assert "19-04" in content
    assert "Table IV: Experimental Testbed Specifications" in content
    assert "Table VIII: Statistical Significance Summary" in content
    assert len(content) > 3000

