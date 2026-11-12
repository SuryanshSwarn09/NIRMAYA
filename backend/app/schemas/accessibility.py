"""Pydantic v2 schemas for Day 89: Indian DPI Accessibility Suite & Bilingual Localization.

Defines schemas for:
- Bilingual English/Hindi dictionary entries & namespace categorization
- Phonetic Text-To-Speech (TTS) audio prompt formatting for low-literacy citizens
- Persistent user visual accessibility preferences (font scaling, high contrast, audio)
"""

from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

LocaleCode = Literal["en", "hi"]
FontSizeLevel = Literal["small", "normal", "large", "xl"]


class TranslationEntry(BaseModel):
    """Bilingual translation record with phonetic Devanagari guidance."""
    key: str = Field(description="Unique dot-notated translation key", example="citizen.tile1.title")
    en: str = Field(description="English translation text", example="My Health ID")
    hi: str = Field(description="Hindi (Devanagari) translation text", example="मेरा स्वास्थ्य पहचान पत्र")
    phonetic_hi: Optional[str] = Field(default=None, description="Transliterated phonetic guide for TTS speech synthesis")
    context: Optional[str] = Field(default=None, description="Clinical or UI context description")

    model_config = ConfigDict(from_attributes=True)


class BilingualDictionaryResponse(BaseModel):
    """Full bilingual dictionary payload returned to frontend clients."""
    version: str = Field(default="1.1.0", description="Dictionary version tag")
    supported_locales: List[str] = Field(default_factory=lambda: ["en", "hi"])
    total_keys: int = Field(description="Total translation key count")
    categories: Dict[str, Dict[str, str]] = Field(
        description="Category namespace mapping for localized strings by selected locale",
    )
    translations: Dict[str, TranslationEntry] = Field(
        description="Complete key-indexed translation map",
    )

    model_config = ConfigDict(from_attributes=True)


class AudioPromptRequest(BaseModel):
    """Request to generate phonetic screen-reader text for audio readout."""
    text_en: str = Field(description="Source English text", example="Take 1 tablet Paracetamol in the morning with food.")
    text_hi: Optional[str] = Field(default=None, description="Optional Hindi text override")
    target_locale: LocaleCode = Field(default="hi", description="Desired readout language (en | hi)")
    context_type: str = Field(
        default="citizen_tiles",
        description="Context type: citizen_tiles | active_medicines | opd_token | clinical_warning",
    )

    model_config = ConfigDict(from_attributes=True)


class AudioPromptResponse(BaseModel):
    """Spoken phonetic text returned for Web Speech API audio synthesis."""
    phonetic_speech_text: str = Field(description="Phonetic speech text optimized for TTS engines")
    target_locale: LocaleCode = Field(description="Language code for speech synthesis voice selection")
    audio_hint: str = Field(description="Plain advice on pronunciation rate and pitch")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Generation timestamp")

    model_config = ConfigDict(from_attributes=True)


class UserAccessibilityPreference(BaseModel):
    """Citizen or clinician visual and audio accessibility settings profile."""
    user_id: str = Field(description="User or Session UUID")
    font_size: FontSizeLevel = Field(default="normal", description="Text size level: small (87.5%) | normal (100%) | large (112.5%) | xl (125%)")
    high_contrast: bool = Field(default=False, description="WCAG AAA 7:1 high-contrast mode flag")
    locale: LocaleCode = Field(default="en", description="Active UI language: en | hi")
    tts_enabled: bool = Field(default=False, description="Whether audio readout helper is active")
    jargon_helper: bool = Field(default=True, description="Whether plain language clinical explainer is active")
    touch_target_optimized: bool = Field(default=True, description="Whether 48px touch target sizing is enforced")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)

