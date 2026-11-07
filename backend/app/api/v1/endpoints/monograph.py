"""FastAPI REST router for NIRMAYA Academic Project Monograph & Engineering Thesis.

Serves table of contents, formal mathematical proofs, empirical benchmarks, and citations.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Response, status

from app.core.container_security import get_container_security_headers
from app.schemas.monograph import (
    ArchitecturalProof,
    BenchmarkSummary,
    CitationItem,
    MonographChapter,
    MonographMetadataResponse,
    IeeeManuscriptDay91Overview,
    IeeeManuscriptDay92Overview,
    IeeeManuscriptDay93Overview,
    IeeeManuscriptDay94Overview,
    AlgorithmListingItem,
    MathematicalFormulationItem,
    NotationTableSummary,
    TableIRelatedWorksMatrix,
    TraceTableSummary,
    TableIVTestbedSummary,
    TableVGatewayIngressSummary,
    TableVICryptoPipelineSummary,
    TableVIILgdTraversalSummary,
    TableVIIIStatisticalSignificanceSummary,
)
from app.services.monograph_service import monograph_service

router = APIRouter()


@router.get(
    "/overview",
    response_model=MonographMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Academic Monograph overview and metadata",
    description="Returns monograph title, 80-day milestone summary, chapter table of contents, and total word counts.",
)
async def get_monograph_overview(response: Response) -> MonographMetadataResponse:
    """Retrieve full monograph metadata and table of contents."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_overview()


@router.get(
    "/chapters",
    response_model=List[MonographChapter],
    status_code=status.HTTP_200_OK,
    summary="List all 10 Academic Monograph chapters",
    description="Returns detailed chapter outlines including section abstracts, word counts, and diagram counts.",
)
async def list_monograph_chapters(response: Response) -> List[MonographChapter]:
    """List all monograph chapters."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.list_chapters()


@router.get(
    "/chapters/{slug}",
    response_model=MonographChapter,
    status_code=status.HTTP_200_OK,
    summary="Retrieve single monograph chapter details",
    description="Returns section breakdown, word count, and proofs for a specific chapter slug.",
)
async def get_monograph_chapter(slug: str, response: Response) -> MonographChapter:
    """Retrieve single chapter by slug or number."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    chapter = monograph_service.get_chapter(slug)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter '{slug}' not found in monograph catalog",
        )
    return chapter


@router.get(
    "/proofs",
    response_model=List[ArchitecturalProof],
    status_code=status.HTTP_200_OK,
    summary="List formal mathematical and architectural proofs",
    description="Returns formal theorem statements and verification suites for Verhoeff check digits, Merkle tree ledgers, and Scoped TRBAC.",
)
async def list_architectural_proofs(response: Response) -> List[ArchitecturalProof]:
    """List all formal architectural and cryptographic proofs."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.list_proofs()


@router.get(
    "/proofs/{proof_id}",
    response_model=ArchitecturalProof,
    status_code=status.HTTP_200_OK,
    summary="Retrieve single architectural proof by ID",
    description="Returns formal theorem statement, mathematical formula, implementation file, and test suite.",
)
async def get_architectural_proof(proof_id: str, response: Response) -> ArchitecturalProof:
    """Retrieve single architectural proof."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    proof = monograph_service.get_proof(proof_id)
    if not proof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proof '{proof_id}' not found in proofs catalog",
        )
    return proof


@router.get(
    "/benchmarks",
    response_model=List[BenchmarkSummary],
    status_code=status.HTTP_200_OK,
    summary="Retrieve empirical performance benchmark scorecard",
    description="Returns achieved throughput, latency percentiles, memory budgets, and test coverage metrics.",
)
async def list_monograph_benchmarks(response: Response) -> List[BenchmarkSummary]:
    """Retrieve empirical benchmark scorecard."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.list_benchmarks()


@router.get(
    "/citations",
    response_model=List[CitationItem],
    status_code=status.HTTP_200_OK,
    summary="Retrieve academic citations in IEEE, APA, and BibTeX",
    description="Provides publication-ready citation records for the NIRMAYA national architecture monograph and referenced standards.",
)
async def list_academic_citations(response: Response) -> List[CitationItem]:
    """List formatted academic citations."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.list_citations()


# =============================================================================
# IEEE Capstone Research Manuscript Endpoints (Phase 6: Days 91–95)
# =============================================================================

@router.get(
    "/manuscript/day91",
    response_model=IeeeManuscriptDay91Overview,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Day 91 IEEE Capstone Research Manuscript Overview",
    description="Returns Title, 250-word Abstract, 10 Index Terms, 6 Core Scientific Contributions, and Table I Comparative Matrix.",
)
async def get_ieee_manuscript_day91_endpoint(response: Response) -> IeeeManuscriptDay91Overview:
    """Retrieve full Day 91 IEEE manuscript deliverable packet."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_ieee_manuscript_day91()


@router.get(
    "/manuscript/table-1",
    response_model=TableIRelatedWorksMatrix,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Table I: Summary of Related Approaches & Research Gaps",
    description="Returns multi-parameter comparative matrix evaluating NIRMAYA against OpenMRS, Bahmni, Epic, Medplum, and ABDM Reference.",
)
async def get_table_1_matrix_endpoint(response: Response) -> TableIRelatedWorksMatrix:
    """Retrieve Table I comparative evaluation matrix."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_table_1_matrix()


@router.get(
    "/manuscript/day92",
    response_model=IeeeManuscriptDay92Overview,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Day 92 IEEE Capstone Research Manuscript Overview",
    description="Returns Section III overview: Threat Model, Dual-Plane Topology, 5 Mathematical Formulations, and Algorithms 1 & 2.",
)
async def get_ieee_manuscript_day92_endpoint(response: Response) -> IeeeManuscriptDay92Overview:
    """Retrieve full Day 92 IEEE manuscript deliverable packet."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_ieee_manuscript_day92()


@router.get(
    "/manuscript/algorithms",
    response_model=List[AlgorithmListingItem],
    status_code=status.HTTP_200_OK,
    summary="List typeset algorithms in IEEE Capstone Manuscript",
    description="Returns formal pseudocode, asymptotic complexities, and source modules for Algorithms 1, 2, and 3.",
)
async def list_algorithms_endpoint(response: Response) -> List[AlgorithmListingItem]:
    """Retrieve typeset algorithms."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_algorithm_listings()


@router.get(
    "/manuscript/math-formulations",
    response_model=List[MathematicalFormulationItem],
    status_code=status.HTTP_200_OK,
    summary="List formal mathematical formulations in Section III-D",
    description="Returns LaTeX formulas, algebraic groups, and security invariants for Verhoeff, Curve25519, HKDF, AES-GCM, and Merkle chains.",
)
async def list_math_formulations_endpoint(response: Response) -> List[MathematicalFormulationItem]:
    """Retrieve mathematical formulations."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_mathematical_formulations()


@router.get(
    "/manuscript/day93",
    response_model=IeeeManuscriptDay93Overview,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Day 93 IEEE Capstone Research Manuscript Overview",
    description="Returns Section III-F overview: Family Health Proxy Logic, Age-of-Majority State Machine, Algorithm 3, Trace Table II, and Notation Table III.",
)
async def get_ieee_manuscript_day93_endpoint(response: Response) -> IeeeManuscriptDay93Overview:
    """Retrieve full Day 93 IEEE manuscript deliverable packet."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_ieee_manuscript_day93()


@router.get(
    "/manuscript/trace-table",
    response_model=TraceTableSummary,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Table II: Illustrative Example Trace Table",
    description="Returns multi-phase trace table spanning all 8 operational phases with measured P99 latency SLAs and security invariants.",
)
async def get_trace_table_endpoint(response: Response) -> TraceTableSummary:
    """Retrieve Table II encounter trace table."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_trace_table_steps()


@router.get(
    "/manuscript/notation-table",
    response_model=NotationTableSummary,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Table III: Summary of Mathematical and Cryptographic Notation",
    description="Returns full notation table indexing 16 algebraic and cryptographic variables across the manuscript.",
)
async def get_notation_table_endpoint(response: Response) -> NotationTableSummary:
    """Retrieve Table III notation table."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_notation_table()


# =============================================================================
# Day 94 (Milestone 19-04) Empirical Evaluation & Benchmark Endpoints
# =============================================================================

@router.get(
    "/manuscript/day94",
    response_model=IeeeManuscriptDay94Overview,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Day 94 IEEE Capstone Research Manuscript Overview",
    description="Returns Section IV overview: Testbed Specs (Table IV), Gateway Benchmarks (Table V), Crypto Pipeline (Table VI), LGD Traversal (Table VII), and Statistical Tests (Table VIII).",
)
async def get_ieee_manuscript_day94_endpoint(response: Response) -> IeeeManuscriptDay94Overview:
    """Retrieve full Day 94 IEEE manuscript deliverable packet."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_ieee_manuscript_day94()


@router.get(
    "/manuscript/table-4",
    response_model=TableIVTestbedSummary,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Table IV: Experimental Testbed Specifications",
    description="Returns testbed node clusters, edge mini-PC hardware, PostgreSQL ltree engine, and load injector specs.",
)
async def get_table_4_endpoint(response: Response) -> TableIVTestbedSummary:
    """Retrieve Table IV testbed environment specifications."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_table_4_testbed()


@router.get(
    "/manuscript/table-5",
    response_model=TableVGatewayIngressSummary,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Table V: High-Throughput Gateway Ingress Benchmarks",
    description="Returns saturation metrics from 1,000 to 50,000 req/s, P50-P99 latencies, CPU utilization, and error rates.",
)
async def get_table_5_endpoint(response: Response) -> TableVGatewayIngressSummary:
    """Retrieve Table V gateway ingress benchmarks."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_table_5_gateway_ingress()


@router.get(
    "/manuscript/table-6",
    response_model=TableVICryptoPipelineSummary,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Table VI: End-to-End Cryptographic Transfer Pipeline Breakdown",
    description="Returns phase-by-phase comparison of Curve25519, HKDF, AES-256-GCM, and NRCeS validation against OpenMRS and Bahmni.",
)
async def get_table_6_endpoint(response: Response) -> TableVICryptoPipelineSummary:
    """Retrieve Table VI cryptographic pipeline comparison."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_table_6_crypto_pipeline()


@router.get(
    "/manuscript/table-7",
    response_model=TableVIILgdTraversalSummary,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Table VII: Indian LGD 6-Tier Hierarchical Traversal Latency",
    description="Returns indexing benchmarks: PostgreSQL ltree with GiST vs Recursive CTE vs Nested Set Model across 788 districts and 28k facilities.",
)
async def get_table_7_endpoint(response: Response) -> TableVIILgdTraversalSummary:
    """Retrieve Table VII LGD traversal benchmarks."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_table_7_lgd_traversal()


@router.get(
    "/manuscript/table-8",
    response_model=TableVIIIStatisticalSignificanceSummary,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Table VIII: Statistical Hypothesis Testing & Effect Size Summary",
    description="Returns two-tailed paired t-test and Wilcoxon signed-rank test results (p < 0.001, Cohen's d > 1.8) over 10,000 executions.",
)
async def get_table_8_endpoint(response: Response) -> TableVIIIStatisticalSignificanceSummary:
    """Retrieve Table VIII statistical significance summary."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return monograph_service.get_table_8_statistical_significance()
