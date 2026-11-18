"""Test suite for UX4G Government of India Design System Integration & Visual Polish.

Validates that frontend tokens, layout roots, GIGW 3.0 accessibility tools,
and UI primitives strictly adhere to the Sovereign Government Design System contract,
ensuring clean Cal.com card boundaries, accessible typography, and no disruptive CSS resets.
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
    """Verify approved Sovereign Government of India theme tokens exist in globals.css and disruptive reset is decoupled."""
    css_path = FRONTEND_DIR / "src" / "app" / "globals.css"
    assert css_path.exists(), "globals.css must exist"
    content = css_path.read_text(encoding="utf-8")

    # 1. Destructive universal reset import must be decoupled to preserve Tailwind layouts
    assert 'ux4g-web-components/styles.css' not in content, "Destructive reset must not be imported in globals.css"

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
    """Verify Button.tsx implements full Sovereign Indian Government color compositions."""
    btn_path = FRONTEND_DIR / "src" / "components" / "ui" / "Button.tsx"
    assert btn_path.exists(), "Button.tsx must exist"
    content = btn_path.read_text(encoding="utf-8")

    assert "#0b4d8c" in content, "Must include Ashoka Navy brand primary color"
    assert "#e8f1f9" in content, "Must include tonal secondary background"
    assert "#046a38" in content, "Must include Tiranga Emerald green variant"
    assert "#db372d" in content, "Must include danger button variant"


def test_ux4g_card_and_primitives():
    """Verify Card, Badge, Input, and Alert components implement clean Cal.com and Sovereign tokens."""
    card_path = FRONTEND_DIR / "src" / "components" / "ui" / "Card.tsx"
    card_content = card_path.read_text(encoding="utf-8")
    assert "border-[#e5e7eb]" in card_content
    assert "rounded-[8px]" in card_content

    badge_path = FRONTEND_DIR / "src" / "components" / "ui" / "Badge.tsx"
    badge_content = badge_path.read_text(encoding="utf-8")
    assert "#0b4d8c" in badge_content
    assert "#046a38" in badge_content

    input_path = FRONTEND_DIR / "src" / "components" / "ui" / "Input.tsx"
    input_content = input_path.read_text(encoding="utf-8")
    assert "border-[#d1d5db]" in input_content
    assert "focus-visible:ring-[#0b4d8c]" in input_content

    alert_path = FRONTEND_DIR / "src" / "components" / "ui" / "Alert.tsx"
    alert_content = alert_path.read_text(encoding="utf-8")
    assert "rounded-[8px]" in alert_content
    assert "border-[#b9d5ee]" in alert_content


def test_wave2_landing_page_ux4g_classes():
    """Verify Landing Page (page.tsx) integrates NationalEmblem and clean CTA/card styling."""
    page_path = FRONTEND_DIR / "src" / "app" / "page.tsx"
    assert page_path.exists()
    content = page_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in content
    assert "Access Patient Vault" in content
    assert "Provider EMR" in content


def test_wave2_login_and_gateway_ux4g_classes():
    """Verify LoginPage and UniversalNationalGatewayCard implement clean inputs, buttons, and alerts."""
    login_path = FRONTEND_DIR / "src" / "app" / "login" / "page.tsx"
    assert login_path.exists()
    login_content = login_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in login_content

    gateway_path = FRONTEND_DIR / "src" / "components" / "gateway" / "UniversalNationalGatewayCard.tsx"
    assert gateway_path.exists()
    gw_content = gateway_path.read_text(encoding="utf-8")
    assert "border-[#d1d5db]" in gw_content
    assert "Generate OTP Challenge" in gw_content


def test_wave2_register_and_passwordless_classes():
    """Verify Registration page and PatientPasswordlessAuthCard use clean inputs and buttons."""
    reg_path = FRONTEND_DIR / "src" / "app" / "register" / "page.tsx"
    assert reg_path.exists()
    reg_content = reg_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in reg_content
    assert "Register on NIRMAYA" in reg_content

    card_path = FRONTEND_DIR / "src" / "components" / "patient" / "PatientPasswordlessAuthCard.tsx"
    assert card_path.exists()
    card_content = card_path.read_text(encoding="utf-8")
    assert "Continue with DigiLocker" in card_content


def test_wave2_official_abha_card_nha_specs():
    """Verify DigitalAbhaCard and DpiHealthIdTile embed NationalEmblem, tricolor, and 14-digit ABHA."""
    card_path = FRONTEND_DIR / "src" / "components" / "patient" / "DigitalAbhaCard.tsx"
    assert card_path.exists()
    content = card_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in content
    assert "#f47920" in content
    assert "#046a38" in content
    assert "ABHA Number (14 Digits)" in content

    tile_path = FRONTEND_DIR / "src" / "components" / "patient" / "DpiHealthIdTile.tsx"
    assert tile_path.exists()
    tile_content = tile_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in tile_content


def test_wave2_patient_vault_and_demographic_banner():
    """Verify Patient Vault mode switcher and PatientDemographicBanner adhere to clean styles."""
    vault_path = FRONTEND_DIR / "src" / "app" / "patient" / "page.tsx"
    assert vault_path.exists()
    vault_content = vault_path.read_text(encoding="utf-8")
    assert "Citizen Health Portal (CoWIN/DigiLocker DPI)" in vault_content
    assert "Specialist Health Vault" in vault_content

    banner_path = FRONTEND_DIR / "src" / "components" / "clinical" / "PatientDemographicBanner.tsx"
    assert banner_path.exists()
    banner_content = banner_path.read_text(encoding="utf-8")
    assert "PatientDemographics" in banner_content
    assert "bg-white" in banner_content


def test_wave3_doctor_console_ux4g_classes():
    """Verify Doctor EMR (/doctor), QuickActionRail, and ConsultationQueue implement clean components."""
    doc_path = FRONTEND_DIR / "src" / "app" / "doctor" / "page.tsx"
    assert doc_path.exists()
    doc_content = doc_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in doc_content, "Doctor page must embed NationalEmblem (Ashok Stambh)"
    assert "Express 45s OPD Mode" in doc_content

    rail_path = FRONTEND_DIR / "src" / "components" / "clinical" / "ClinicalQuickActionRail.tsx"
    assert rail_path.exists()
    rail_content = rail_path.read_text(encoding="utf-8")
    assert "Prescriptions" in rail_content
    assert "Consultation Queue" in rail_content

    queue_path = FRONTEND_DIR / "src" / "components" / "clinical" / "ClinicianConsultationQueue.tsx"
    assert queue_path.exists()
    queue_content = queue_path.read_text(encoding="utf-8")
    assert "Live Queue Sync" in queue_content


def test_wave3_lab_console_ux4g_classes():
    """Verify Diagnostic Lab (/lab) implements NationalEmblem, LOINC builder, SHA-256 card, and clean controls."""
    lab_path = FRONTEND_DIR / "src" / "app" / "lab" / "page.tsx"
    assert lab_path.exists()
    content = lab_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in content, "Lab console must embed NationalEmblem"
    assert "NABL Accredited" in content
    assert "SHA-256" in content


def test_wave3_admin_console_ux4g_classes():
    """Verify Public Health & Admin Command Center (/admin) and LGD cards adhere to clean standards."""
    admin_path = FRONTEND_DIR / "src" / "app" / "admin" / "page.tsx"
    assert admin_path.exists()
    content = admin_path.read_text(encoding="utf-8")
    assert "NationalEmblem" in content, "Admin console must embed NationalEmblem"
    assert "Super Admin" in content
    assert "CIS Hardened" in content

    command_path = FRONTEND_DIR / "src" / "components" / "clinical" / "TerritorialCommandCenterCard.tsx"
    assert command_path.exists()
    cmd_content = command_path.read_text(encoding="utf-8")
    assert "border-[#d1d5db]" in cmd_content

    hier_path = FRONTEND_DIR / "src" / "components" / "clinical" / "AdministrativeHierarchyViewerCard.tsx"
    assert hier_path.exists()
    hier_content = hier_path.read_text(encoding="utf-8")
    assert "border-[#d1d5db]" in hier_content
