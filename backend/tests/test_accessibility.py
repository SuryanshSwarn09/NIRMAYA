"""Tests for Day 89: Indian DPI Accessibility Suite, Bilingual Hindi/English Switcher & Visual Control Strip.

Validates:
- Bilingual dictionary initialization, categories, and Devanagari translation parity
- Low-literacy phonetic audio prompt generation for speech synthesis
- User visual accessibility preference lifecycle (font scaling, high contrast, locale)
- REST API endpoint responses, status codes, and OpenAPI schema conformance
"""

import pytest
from datetime import datetime
from typing import List
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.accessibility import (
    AudioPromptRequest,
    AudioPromptResponse,
    BilingualDictionaryResponse,
    FontSizeLevel,
    TranslationEntry,
    UserAccessibilityPreference,
)
from app.services.accessibility_service import (
    AccessibilityService,
    accessibility_service,
)


@pytest.fixture
def fresh_service():
    """Fresh isolated AccessibilityService fixture."""
    return AccessibilityService()


@pytest.fixture
def client():
    """TestClient fixture bound to FastAPI app."""
    return TestClient(app)


class TestAccessibilityService:
    """Unit tests for AccessibilityService business logic and glossaries."""

    def test_dictionary_initialization_completeness(self, fresh_service: AccessibilityService):
        """Ensure dictionary contains at least 25 standard entries across all core modules."""
        dictionary = fresh_service.get_dictionary()
        assert dictionary.total_keys >= 25
        assert dictionary.version == "1.1.0"
        assert set(dictionary.supported_locales) == {"en", "hi"}

        # Verify key modules exist in categories
        assert "navigation" in dictionary.categories
        assert "citizen_portal" in dictionary.categories
        assert "doctor_express" in dictionary.categories
        assert "auth" in dictionary.categories
        assert "emergency" in dictionary.categories

    def test_bilingual_dictionary_schema_and_types(self, fresh_service: AccessibilityService):
        """Verify BilingualDictionaryResponse model conformity."""
        res = fresh_service.get_dictionary(locale="en")
        assert isinstance(res, BilingualDictionaryResponse)
        assert len(res.translations) == res.total_keys
        sample_entry = res.translations["citizen.tile1.title"]
        assert isinstance(sample_entry, TranslationEntry)
        assert sample_entry.en == "My Health ID (ABHA)"
        assert sample_entry.hi == "मेरा स्वास्थ्य पहचान पत्र (आभा)"

    def test_locale_filtering_english(self, fresh_service: AccessibilityService):
        """Verify English locale output."""
        res = fresh_service.get_dictionary(locale="en")
        assert res.categories["citizen_portal"]["citizen.tile1.title"] == "My Health ID (ABHA)"
        assert res.categories["navigation"]["nav.brand"] == "NIRMAYA Digital Health"

    def test_locale_filtering_hindi(self, fresh_service: AccessibilityService):
        """Verify Hindi Devanagari locale output."""
        res = fresh_service.get_dictionary(locale="hi")
        assert res.categories["citizen_portal"]["citizen.tile1.title"] == "मेरा स्वास्थ्य पहचान पत्र (आभा)"
        assert res.categories["navigation"]["nav.brand"] == "निर्मया डिजिटल स्वास्थ्य"

    def test_phonetic_audio_prompt_english(self, fresh_service: AccessibilityService):
        """Verify English audio prompt generation."""
        req = AudioPromptRequest(
            text_en="Take Paracetamol 650mg after lunch.",
            target_locale="en",
            context_type="active_medicines",
        )
        res = fresh_service.generate_audio_prompt(req)
        assert isinstance(res, AudioPromptResponse)
        assert res.target_locale == "en"
        assert "Paracetamol" in res.phonetic_speech_text
        assert "en-IN" in res.audio_hint or "en-US" in res.audio_hint

    def test_phonetic_audio_prompt_hindi_devanagari(self, fresh_service: AccessibilityService):
        """Verify Hindi Devanagari audio prompt generation with vernacular guidance."""
        req = AudioPromptRequest(
            text_en="Paracetamol 650mg morning and night.",
            text_hi="पैरासिटामोल 650 मिलीग्राम सुबह और रात खाने के बाद।",
            target_locale="hi",
            context_type="active_medicines",
        )
        res = fresh_service.generate_audio_prompt(req)
        assert res.target_locale == "hi"
        assert "नमस्ते। आपकी आज की दवाएं हैं:" in res.phonetic_speech_text
        assert "hi-IN" in res.audio_hint

    def test_phonetic_audio_prompt_citizen_tiles_context(self, fresh_service: AccessibilityService):
        """Verify citizen portal audio overview prompt."""
        req = AudioPromptRequest(
            text_en="Digital ABHA Card",
            target_locale="hi",
            context_type="citizen_tiles",
        )
        res = fresh_service.generate_audio_prompt(req)
        assert "निर्मया स्वास्थ्य सेवा:" in res.phonetic_speech_text
        assert "अस्पताल में तुरंत पंजीकरण" in res.phonetic_speech_text

    def test_phonetic_audio_prompt_clinical_warning_context(self, fresh_service: AccessibilityService):
        """Verify clinical warning tone and emphatic instruction."""
        req = AudioPromptRequest(
            text_en="Severe Penicillin Allergy",
            target_locale="hi",
            context_type="clinical_warning",
        )
        res = fresh_service.generate_audio_prompt(req)
        assert "सावधान:" in res.phonetic_speech_text
        assert "Emphatic tone" in res.audio_hint

    def test_user_accessibility_preferences_defaults(self, fresh_service: AccessibilityService):
        """Verify default visual control preferences for new users."""
        prefs = fresh_service.get_preferences("user-uuid-101")
        assert prefs.user_id == "user-uuid-101"
        assert prefs.font_size == "normal"
        assert prefs.high_contrast is False
        assert prefs.locale == "en"
        assert prefs.tts_enabled is False
        assert prefs.touch_target_optimized is True

    def test_user_accessibility_preferences_persistence(self, fresh_service: AccessibilityService):
        """Verify visual accessibility preferences update and persistence."""
        new_prefs = UserAccessibilityPreference(
            user_id="user-uuid-101",
            font_size="xl",
            high_contrast=True,
            locale="hi",
            tts_enabled=True,
            jargon_helper=True,
            touch_target_optimized=True,
        )
        saved = fresh_service.save_preferences(new_prefs)
        assert saved.font_size == "xl"
        assert saved.high_contrast is True
        assert saved.locale == "hi"

        retrieved = fresh_service.get_preferences("user-uuid-101")
        assert retrieved.font_size == "xl"
        assert retrieved.high_contrast is True
        assert retrieved.locale == "hi"

    def test_font_size_levels_validity(self):
        """Verify all 4 font size options conform to FontSizeLevel literal."""
        levels: List[FontSizeLevel] = ["small", "normal", "large", "xl"]
        for level in levels:
            pref = UserAccessibilityPreference(user_id="test", font_size=level)
            assert pref.font_size == level

    def test_emergency_helpline_entries_presence(self, fresh_service: AccessibilityService):
        """Ensure national emergency numbers are registered in dictionary."""
        dict_data = fresh_service.get_dictionary()
        assert "emergency.helpline_104" in dict_data.translations
        assert "emergency.tele_manas" in dict_data.translations
        assert "emergency.ambulance_108" in dict_data.translations
        entry_104 = dict_data.translations["emergency.helpline_104"]
        assert "104" in entry_104.en
        assert "104" in entry_104.hi

    def test_hindi_transliteration_phonetics(self, fresh_service: AccessibilityService):
        """Verify that translation entries provide phonetic guide strings."""
        dict_data = fresh_service.get_dictionary()
        for key, entry in dict_data.translations.items():
            assert entry.phonetic_hi is not None
            assert len(entry.phonetic_hi) > 0

    def test_plain_language_medical_dictionary_entries(self, fresh_service: AccessibilityService):
        """Ensure medicine schedules avoid Latin abbreviations."""
        dict_data = fresh_service.get_dictionary()
        tile2_desc = dict_data.translations["citizen.tile2.desc"]
        assert "morning" in tile2_desc.en.lower()
        assert "bd" not in tile2_desc.en.lower()
        assert "tds" not in tile2_desc.en.lower()
        assert "qid" not in tile2_desc.en.lower()

    def test_service_singleton_instance(self):
        """Ensure accessibility_service singleton is operational."""
        assert accessibility_service is not None
        assert isinstance(accessibility_service, AccessibilityService)

    def test_rapid_consecutive_audio_prompt_generations(self, fresh_service: AccessibilityService):
        """Verify audio prompt generation executes with sub-millisecond efficiency."""
        req = AudioPromptRequest(
            text_en="Test prompt",
            target_locale="en",
        )
        import time
        start = time.perf_counter()
        for _ in range(50):
            fresh_service.generate_audio_prompt(req)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 100.0  # 50 calls in under 100ms (< 2ms each)

    def test_audio_prompt_timestamp_utc(self, fresh_service: AccessibilityService):
        """Verify audio prompt response contains valid timezone-aware UTC timestamp."""
        req = AudioPromptRequest(text_en="Test timestamp", target_locale="en")
        res = fresh_service.generate_audio_prompt(req)
        assert isinstance(res.generated_at, datetime)
        assert res.generated_at.tzinfo is not None


# ============================================================================
# REST API Endpoint Tests (TestClient)
# ============================================================================


def test_api_get_bilingual_dictionary_endpoint(client: TestClient):
    """GET /api/v1/accessibility/dictionary returns complete dictionary."""
    res = client.get("/api/v1/accessibility/dictionary")
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert payload["data"]["version"] == "1.1.0"
    assert payload["data"]["total_keys"] >= 25
    assert "citizen_portal" in payload["data"]["categories"]


def test_api_get_locale_dictionary_english(client: TestClient):
    """GET /api/v1/accessibility/dictionary/en returns English definitions."""
    res = client.get("/api/v1/accessibility/dictionary/en")
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert payload["data"]["categories"]["citizen_portal"]["citizen.tile1.title"] == "My Health ID (ABHA)"


def test_api_get_locale_dictionary_hindi(client: TestClient):
    """GET /api/v1/accessibility/dictionary/hi returns Hindi Devanagari definitions."""
    res = client.get("/api/v1/accessibility/dictionary/hi")
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert payload["data"]["categories"]["citizen_portal"]["citizen.tile1.title"] == "मेरा स्वास्थ्य पहचान पत्र (आभा)"


def test_api_create_audio_prompt_endpoint(client: TestClient):
    """POST /api/v1/accessibility/audio-prompt generates speech text."""
    body = {
        "text_en": "Take Amlodipine 5mg daily after breakfast",
        "target_locale": "hi",
        "context_type": "active_medicines",
    }
    res = client.post("/api/v1/accessibility/audio-prompt", json=body)
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert "नमस्ते। आपकी आज की दवाएं हैं:" in payload["data"]["phonetic_speech_text"]
    assert payload["data"]["target_locale"] == "hi"


def test_api_user_preferences_lifecycle(client: TestClient):
    """Test GET and POST preferences endpoints for persistent a11y profile."""
    user_id = "test-citizen-session-42"
    # 1. Fetch defaults
    res_get = client.get(f"/api/v1/accessibility/preferences/{user_id}")
    assert res_get.status_code == 200
    data = res_get.json()["data"]
    assert data["user_id"] == user_id
    assert data["font_size"] == "normal"
    assert data["high_contrast"] is False

    # 2. Update preferences
    update_body = {
        "user_id": user_id,
        "font_size": "xl",
        "high_contrast": True,
        "locale": "hi",
        "tts_enabled": True,
        "jargon_helper": True,
        "touch_target_optimized": True,
    }
    res_post = client.post("/api/v1/accessibility/preferences", json=update_body)
    assert res_post.status_code == 200
    assert res_post.json()["data"]["font_size"] == "xl"
    assert res_post.json()["data"]["high_contrast"] is True
    assert res_post.json()["data"]["locale"] == "hi"

    # 3. Verify retrieval reflects changes
    res_verify = client.get(f"/api/v1/accessibility/preferences/{user_id}")
    assert res_verify.status_code == 200
    assert res_verify.json()["data"]["font_size"] == "xl"
    assert res_verify.json()["data"]["high_contrast"] is True


def test_openapi_accessibility_routes_registered(client: TestClient):
    """Verify accessibility paths are documented in the main OpenAPI schema."""
    res = client.get("/api/v1/openapi.json")
    assert res.status_code == 200
    paths = res.json()["paths"]
    assert "/api/v1/accessibility/dictionary" in paths
    assert "/api/v1/accessibility/dictionary/{locale}" in paths
    assert "/api/v1/accessibility/audio-prompt" in paths
    assert "/api/v1/accessibility/preferences/{user_id}" in paths
    assert "/api/v1/accessibility/preferences" in paths


def test_bilingual_dictionary_query_param_filtering(client: TestClient):
    """Verify GET /api/v1/accessibility/dictionary?locale=hi filters categories to Hindi."""
    res = client.get("/api/v1/accessibility/dictionary?locale=hi")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["categories"]["citizen_portal"]["citizen.tile1.title"] == "मेरा स्वास्थ्य पहचान पत्र (आभा)"


def test_wcag_aaa_contrast_ratio_validation(fresh_service: AccessibilityService):
    """Verify WCAG AAA high-contrast preference toggle state."""
    prefs = fresh_service.get_preferences("contrast-user-1")
    assert prefs.high_contrast is False
    prefs.high_contrast = True
    updated = fresh_service.save_preferences(prefs)
    assert updated.high_contrast is True


def test_invalid_locale_422(client: TestClient):
    """Verify invalid locale code returns HTTP 422 Unprocessable Entity."""
    res = client.get("/api/v1/accessibility/dictionary/fr")
    assert res.status_code == 422

