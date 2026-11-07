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


def test_wave2_landing_page_ux4g_classes():
    """Verify Landing Page (page.tsx) integrates NationalEmblem and UX4G button/card classes."""
    page_path = FRONTEND_DIR / "src" / "app" / "page.tsx"
    assert page_path.exists()
    content = page_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in content
    assert "ux4g-btn ux4g-btn-primary ux4g-btn-l" in content
    assert "ux4g-btn ux4g-btn-outline-primary" in content
    assert "ux4g-card ux4g-card-elevated" in content


def test_wave2_login_and_gateway_ux4g_classes():
    """Verify LoginPage and UniversalNationalGatewayCard implement UX4G inputs, buttons, and alerts."""
    login_path = FRONTEND_DIR / "src" / "app" / "login" / "page.tsx"
    assert login_path.exists()
    login_content = login_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in login_content

    gateway_path = FRONTEND_DIR / "src" / "components" / "gateway" / "UniversalNationalGatewayCard.tsx"
    assert gateway_path.exists()
    gw_content = gateway_path.read_text(encoding="utf-8")
    assert "ux4g-input ux4g-input-m" in gw_content
    assert "ux4g-btn ux4g-btn-primary ux4g-btn-m" in gw_content
    assert "ux4g-card ux4g-card-elevated" in gw_content
    assert "ux4g-alert" in gw_content


def test_wave2_register_and_passwordless_classes():
    """Verify Registration page and PatientPasswordlessAuthCard use UX4G inputs and buttons."""
    reg_path = FRONTEND_DIR / "src" / "app" / "register" / "page.tsx"
    assert reg_path.exists()
    reg_content = reg_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in reg_content
    assert "ux4g-input ux4g-input-m" in reg_content
    assert "ux4g-card ux4g-card-elevated" in reg_content

    card_path = FRONTEND_DIR / "src" / "components" / "patient" / "PatientPasswordlessAuthCard.tsx"
    assert card_path.exists()
    card_content = card_path.read_text(encoding="utf-8")
    assert "ux4g-input ux4g-input-m" in card_content
    assert "ux4g-btn ux4g-btn-primary ux4g-btn-m" in card_content
    assert "ux4g-alert" in card_content


def test_wave2_official_abha_card_nha_specs():
    """Verify DigitalAbhaCard and DpiHealthIdTile embed NationalEmblem, tricolor, and 14-digit ABHA."""
    card_path = FRONTEND_DIR / "src" / "components" / "patient" / "DigitalAbhaCard.tsx"
    assert card_path.exists()
    content = card_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in content
    assert "#f47920" in content
    assert "#046a38" in content
    assert "ABHA Number (14 Digits)" in content
    assert "ux4g-card ux4g-card-elevated" in content

    tile_path = FRONTEND_DIR / "src" / "components" / "patient" / "DpiHealthIdTile.tsx"
    assert tile_path.exists()
    tile_content = tile_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in tile_content
    assert "ux4g-card ux4g-card-elevated" in tile_content
    assert "ux4g-btn ux4g-btn-primary ux4g-btn-l" in tile_content


def test_wave2_patient_vault_and_demographic_banner():
    """Verify Patient Vault mode switcher and PatientDemographicBanner adhere to UX4G styles."""
    vault_path = FRONTEND_DIR / "src" / "app" / "patient" / "page.tsx"
    assert vault_path.exists()
    vault_content = vault_path.read_text(encoding="utf-8")
    assert "ux4g-btn ux4g-btn-s" in vault_content

    banner_path = FRONTEND_DIR / "src" / "components" / "clinical" / "PatientDemographicBanner.tsx"
    assert banner_path.exists()
    banner_content = banner_path.read_text(encoding="utf-8")
    assert "ux4g-card ux4g-card-elevated" in banner_content
    assert "ux4g-btn ux4g-btn-s" in banner_content
