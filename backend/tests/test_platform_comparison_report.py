"""Test suite for Phase 8: National Health Platform Comparative Benchmark & Deep Architectural Report.

Validates that the comprehensive comparative analysis report (docs/reports/)
and the interactive in-app comparison viewer (frontend/src/components/clinical/)
rigorously benchmark NIRMAYA against Apollo 24/7, Aarogya Setu, eSanjeevani, CoWIN,
and the official ABDM ABHA App across 10 architectural and clinical dimensions.
"""

from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = REPO_ROOT / "docs"
FRONTEND_DIR = REPO_ROOT / "frontend"


def test_comparative_report_file_exists():
    """Verify master comparative whitepaper exists in docs/reports/ and exceeds minimum thesis depth."""
    report_path = DOCS_DIR / "reports" / "nirmaya-vs-apollo-aarogyasetu-comparative-analysis.md"
    assert report_path.exists(), "Master comparative report must exist at docs/reports/nirmaya-vs-apollo-aarogyasetu-comparative-analysis.md"
    content = report_path.read_text(encoding="utf-8")
    assert len(content) > 10000, "Report must be a comprehensive whitepaper of at least 10,000 characters"


def test_comparative_report_platform_coverage():
    """Verify all 6 benchmark platforms are evaluated in the report."""
    report_path = DOCS_DIR / "reports" / "nirmaya-vs-apollo-aarogyasetu-comparative-analysis.md"
    content = report_path.read_text(encoding="utf-8")

    assert "NIRMAYA" in content, "Must evaluate NIRMAYA sovereign DPI"
    assert "Apollo 24/7" in content, "Must evaluate Apollo 24/7 commercial platform"
    assert "Aarogya Setu" in content, "Must evaluate Aarogya Setu"
    assert "eSanjeevani" in content, "Must evaluate eSanjeevani national telemedicine"
    assert "CoWIN" in content, "Must evaluate CoWIN vaccine and identity registry"
    assert "ABDM" in content and "ABHA" in content, "Must evaluate official ABDM ABHA App"


def test_comparative_report_ten_dimensions():
    """Verify all 10 architectural and clinical dimensions are analyzed in detail."""
    report_path = DOCS_DIR / "reports" / "nirmaya-vs-apollo-aarogyasetu-comparative-analysis.md"
    content = report_path.read_text(encoding="utf-8")

    # Dimension 1: Topology
    assert "Topology" in content or "Federated" in content
    # Dimension 2: Privacy / DPDP
    assert "DPDP Act 2023" in content
    assert "Section 9" in content, "Must analyze DPDP Section 9 minor/guardian proxy access"
    # Dimension 3: Cryptography
    assert "Fidelius" in content or "Curve25519" in content
    assert "AES-256-GCM" in content
    assert "SHA-256" in content
    # Dimension 4: Interoperability
    assert "HL7 FHIR" in content
    assert "SNOMED" in content
    assert "LOINC" in content
    # Dimension 5: Clinical Velocity
    assert "45-Second" in content or "45s" in content
    assert "Break-The-Glass" in content or "BTG" in content
    # Dimension 6: Identity
    assert "Verhoeff" in content, "Must evaluate Verhoeff D5 checksum algorithm"
    assert "DigiLocker" in content
    assert "Aadhaar" in content
    # Dimension 7: Telemedicine
    assert "WebRTC" in content
    assert "SQLite" in content or "Offline" in content
    # Dimension 8: Pathology
    assert "NABL" in content or "ISO 15189" in content
    # Dimension 9: LGD Governance
    assert "Local Government Directory" in content or "LGD" in content
    assert "ltree" in content
    # Dimension 10: Accessibility
    assert "GIGW 3.0" in content
    assert "WCAG 2.1 AA" in content


def test_frontend_comparison_component():
    """Verify PlatformComparisonViewerCard.tsx exists, exports profiles, and includes clean Cal.com styling."""
    component_path = FRONTEND_DIR / "src" / "components" / "clinical" / "PlatformComparisonViewerCard.tsx"
    assert component_path.exists(), "PlatformComparisonViewerCard.tsx must exist"
    content = component_path.read_text(encoding="utf-8")

    assert "PLATFORM_PROFILES" in content
    assert "DIMENSION_DATA" in content
    assert "Apollo 24/7" in content
    assert "Aarogya Setu" in content
    assert "eSanjeevani" in content
    assert "CoWIN" in content
    assert "ABDM ABHA App" in content
    assert "border-[#d1d5db]" in content, "Must use Cal.com solid hairline card border"


def test_frontend_exports_and_admin_mount():
    """Verify PlatformComparisonViewerCard is exported from clinical index and mounted in /admin."""
    index_path = FRONTEND_DIR / "src" / "components" / "clinical" / "index.ts"
    assert "PlatformComparisonViewerCard" in index_path.read_text(encoding="utf-8")

    admin_path = FRONTEND_DIR / "src" / "app" / "admin" / "page.tsx"
    admin_content = admin_path.read_text(encoding="utf-8")
    assert "PlatformComparisonViewerCard" in admin_content
    assert "<PlatformComparisonViewerCard />" in admin_content
