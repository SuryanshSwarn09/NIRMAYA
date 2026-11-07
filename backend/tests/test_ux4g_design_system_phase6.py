"""Test suite for Phase 6 Wave 1: UX4G Government of India Design System Migration.

Validates that frontend tokens, layout roots, GIGW 3.0 accessibility tools,
and UI primitives strictly adhere to the UX4G Design System contract (Design.md).
"""

from pathlib import Path
import re
import pytest

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


def test_ux4g_package_installation_in_package_json():
    """Verify ux4g-web-components package is declared in package.json."""
    pkg_json_path = FRONTEND_DIR / "package.json"
    assert pkg_json_path.exists(), "frontend/package.json must exist"
    content = pkg_json_path.read_text(encoding="utf-8")
    assert "ux4g-web-components" in content, "ux4g-web-components must be declared in dependencies"


def test_ux4g_tokens_in_globals_css():
    """Verify approved Sovereign Government of India theme tokens exist in globals.css."""
    css_path = FRONTEND_DIR / "src" / "app" / "globals.css"
    assert css_path.exists(), "globals.css must exist"
    content = css_path.read_text(encoding="utf-8")

    # 1. Official CSS package import
    assert 'ux4g-web-components/styles.css' in content, "Must import ux4g-web-components/styles.css"

    # 2. Approved Primary (Ashoka Navy / India Blue) token override
    assert "--ux4g-color-primary-600: #0b4d8c !important" in content

    # 3. Approved Secondary (Tiranga Saffron) token override
    assert "--ux4g-color-secondary-600: #f47920 !important" in content

    # 4. Approved Tertiary / Success (India Green) token override
    assert "--ux4g-color-green-600: #046a38 !important" in content

    # 5. Semantic brand tokens
    assert "--ux4g-text-brand-primary-default: #0b4d8c !important" in content
    assert "--ux4g-bg-primary-strong: #0b4d8c !important" in content
    assert "--ux4g-border-color-primary-strong: #0b4d8c !important" in content


def test_ux4g_layout_theme_and_typography():
    """Verify data-theme="light" attribute and Noto font families in layout.tsx."""
    layout_path = FRONTEND_DIR / "src" / "app" / "layout.tsx"
    assert layout_path.exists(), "layout.tsx must exist"
    content = layout_path.read_text(encoding="utf-8")

    # Must set data-theme="light" on <html>
    assert 'data-theme="light"' in content, 'data-theme="light" is required on <html> by UX4G contract'


def test_gigw3_accessibility_bar_elements():
    """Verify GIGW 3.0 accessibility toolbar controls and Ashok Stambh emblem in AccessibilityBar.tsx."""
    bar_path = FRONTEND_DIR / "src" / "components" / "layout" / "AccessibilityBar.tsx"
    assert bar_path.exists(), "AccessibilityBar.tsx must exist"
    content = bar_path.read_text(encoding="utf-8")

    # 1. National Emblem component import
    assert "NationalEmblem" in content, "AccessibilityBar must embed NationalEmblem (Ashok Stambh)"

    # 2. Government of India and NHA credentials
    assert "Government of India" in content
    assert "Ayushman Bharat Digital Mission" in content

    # 3. GIGW 3.0 Accessibility controls (Skip link, Font Scaling, High Contrast, Bilingual)
    assert "skip-to-content" in content, "Must provide skip-to-content landmark"
    assert 'setFontSize("small")' in content
    assert 'setFontSize("normal")' in content
    assert 'setFontSize("large")' in content
    assert 'setFontSize("xl")' in content
    assert "toggleHighContrast" in content
    assert 'setLocale("en")' in content
    assert 'setLocale("hi")' in content
    assert "tel:104" in content, "Must provide 104 National Health Helpline"


def test_ux4g_button_class_compositions():
    """Verify Button.tsx implements full UX4G class compositions (Base + Variant + Size)."""
    btn_path = FRONTEND_DIR / "src" / "components" / "ui" / "Button.tsx"
    assert btn_path.exists(), "Button.tsx must exist"
    content = btn_path.read_text(encoding="utf-8")

    assert "ux4g-btn" in content, "Must include base ux4g-btn class"
    assert "ux4g-btn-primary" in content
    assert "ux4g-btn-tonal-primary" in content
    assert "ux4g-btn-outline-primary" in content
    assert "ux4g-btn-danger" in content
    assert "ux4g-btn-s" in content
    assert "ux4g-btn-m" in content
    assert "ux4g-btn-l" in content
    assert "ux4g-icon-btn" in content


def test_ux4g_card_and_primitives():
    """Verify Card, Badge, Input, and Alert components implement UX4G classes."""
    card_path = FRONTEND_DIR / "src" / "components" / "ui" / "Card.tsx"
    assert "ux4g-card" in card_path.read_text(encoding="utf-8")
    assert "ux4g-card-elevated" in card_path.read_text(encoding="utf-8")

    badge_path = FRONTEND_DIR / "src" / "components" / "ui" / "Badge.tsx"
    assert "ux4g-badge" in badge_path.read_text(encoding="utf-8")

    input_path = FRONTEND_DIR / "src" / "components" / "ui" / "Input.tsx"
    assert "ux4g-input" in input_path.read_text(encoding="utf-8")
    assert "ux4g-input-m" in input_path.read_text(encoding="utf-8")

    alert_path = FRONTEND_DIR / "src" / "components" / "ui" / "Alert.tsx"
    assert "ux4g-alert" in alert_path.read_text(encoding="utf-8")
    assert "ux4g-alert-info" in alert_path.read_text(encoding="utf-8")
    assert "ux4g-alert-warning" in alert_path.read_text(encoding="utf-8")
    assert "ux4g-alert-danger" in alert_path.read_text(encoding="utf-8")
