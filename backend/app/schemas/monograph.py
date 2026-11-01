from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProofCategoryEnum(str, Enum):
    """Categorization for formal mathematical and architectural proofs."""
    CRYPTOGRAPHIC_INVARIANT = "CRYPTOGRAPHIC_INVARIANT"
    SECURITY_GUARANTEE = "SECURITY_GUARANTEE"
    SOVEREIGN_HIERARCHY = "SOVEREIGN_HIERARCHY"
    STORE_AND_FORWARD_SYNC = "STORE_AND_FORWARD_SYNC"
    SQL_MED_ISOLATION = "SQL_MED_ISOLATION"
    CONCURRENCY_MODEL = "CONCURRENCY_MODEL"


class BenchmarkCategoryEnum(str, Enum):
    """Categorization for empirical system benchmarks."""
    THROUGHPUT_CONCURRENCY = "THROUGHPUT_CONCURRENCY"
    LATENCY_PERCENTILES = "LATENCY_PERCENTILES"
    MEMORY_FOOTPRINT = "MEMORY_FOOTPRINT"
    CONTAINER_SIZE = "CONTAINER_SIZE"
    STANDARDS_COMPLIANCE = "STANDARDS_COMPLIANCE"
    TEST_COVERAGE = "TEST_COVERAGE"


class BenchmarkStatusEnum(str, Enum):
    """Fulfillment state of an engineering performance benchmark."""
    EXCEEDED = "EXCEEDED"
    MET = "MET"
    OPTIMIZED = "OPTIMIZED"


class ChapterSection(BaseModel):
    """Sub-section within an academic monograph chapter."""
    section_id: str = Field(..., description="Unique section slug (e.g., sec-2-1)")
    title: str = Field(..., description="Section title")
    word_count: int = Field(default=0, description="Approximate word count of section")
    abstract: str = Field(..., description="Condensed overview of section concepts")


class MonographChapter(BaseModel):
    """Complete chapter metadata in the academic monograph thesis."""
    chapter_num: int = Field(..., ge=1, le=10, description="Sequential chapter index")
    slug: str = Field(..., description="URL-friendly chapter identifier")
    title: str = Field(..., description="Primary chapter title")
    subtitle: str = Field(..., description="Descriptive subtitle")
    word_count: int = Field(default=0, description="Chapter word count")
    sections: List[ChapterSection] = Field(default_factory=list)
    diagrams_count: int = Field(default=0, description="Number of architectural diagrams")
    proofs_count: int = Field(default=0, description="Number of formal proofs included")


class ArchitecturalProof(BaseModel):
    """Formal mathematical or algorithmic proof verifying a core system invariant."""
    proof_id: str = Field(..., description="Unique proof identifier (e.g., PRF-01-VERHOEFF)")
    title: str = Field(..., description="Title of architectural or cryptographic proof")
    category: ProofCategoryEnum
    formal_statement: str = Field(..., description="Mathematical or theoretical theorem statement")
    mathematical_expression: Optional[str] = Field(None, description="LaTeX or mathematical formula")
    implementation_file: str = Field(..., description="Source code file enforcing invariant")
    verification_suite: str = Field(..., description="Automated test suite verifying proof")
    verified: bool = Field(default=True, description="Whether proof is empirically verified")


class BenchmarkSummary(BaseModel):
    """Empirical performance or resource footprint benchmark scorecard."""
    benchmark_id: str = Field(..., description="Unique benchmark key (e.g., BM-01-WS-LATENCY)")
    metric_name: str = Field(..., description="Human-readable benchmark name")
    category: BenchmarkCategoryEnum
    target_threshold: str = Field(..., description="Engineering design specification target")
    achieved_value: str = Field(..., description="Actual empirical value achieved in tests")
    latency_ms: Optional[float] = Field(None, description="Measured response latency in ms")
    concurrency_units: Optional[int] = Field(None, description="Simultaneous concurrent connections")
    status: BenchmarkStatusEnum = Field(default=BenchmarkStatusEnum.EXCEEDED)


class CitationItem(BaseModel):
    """Academic reference citation formatted in IEEE, APA, and BibTeX."""
    citation_key: str = Field(..., description="BibTeX citation key (e.g., nirmaya2026sovereign)")
    title: str = Field(..., description="Publication title")
    authors: str = Field(..., description="Author attribution string")
    year: int = Field(default=2026)
    venue: str = Field(..., description="Conference, journal, or institutional publisher")
    doi_or_url: str = Field(..., description="Canonical DOI or URL")
    bibtex: str = Field(..., description="Full BibTeX format citation entry")
    ieee_format: str = Field(..., description="IEEE bibliographic string format")


class MonographMetadataResponse(BaseModel):
    """Global overview and aggregated statistics of the NIRMAYA Academic Monograph."""
    title: str = Field(default="NIRMAYA: A Sovereign, Interoperable, and Zero-Trust National Health Information Network")
    subtitle: str = Field(default="Architecture, Cryptographic Verification, and Empirical Field Evaluation (Days 1–80)")
    version: str = Field(default="1.0.0-rc1")
    release_target: str = Field(default="Production Master Release v1.0.0")
    total_chapters: int = Field(default=10)
    total_word_count: int = Field(default=0)
    total_diagrams: int = Field(default=0)
    total_formal_proofs: int = Field(default=0)
    cumulative_test_count: int = Field(default=630)
    cumulative_test_modules: int = Field(default=39)
    chapters: List[MonographChapter] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
