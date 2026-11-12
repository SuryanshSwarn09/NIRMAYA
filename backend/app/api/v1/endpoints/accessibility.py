"""FastAPI REST API Endpoints for Day 89: Indian DPI Accessibility Suite & Bilingual Localization.

Exposes:
- GET /api/v1/accessibility/dictionary (Complete English/Hindi translation glossaries)
- GET /api/v1/accessibility/dictionary/{locale} (Bilingual dictionary filtered for selected locale)
- POST /api/v1/accessibility/audio-prompt (Phonetic TTS speech synthesis prompt generator)
- GET /api/v1/accessibility/preferences/{user_id} (Citizen / doctor visual a11y preferences)
- POST /api/v1/accessibility/preferences (Persist visual a11y preferences)
"""

from typing import Optional
from fastapi import APIRouter, Path, Query, status

from app.schemas.accessibility import (
    AudioPromptRequest,
    AudioPromptResponse,
    BilingualDictionaryResponse,
    LocaleCode,
    UserAccessibilityPreference,
)
from app.schemas.common import APIResponse
from app.services.accessibility_service import accessibility_service

router = APIRouter(prefix="/accessibility", tags=["Indian DPI Accessibility Suite"])


@router.get(
    "/dictionary",
    response_model=APIResponse[BilingualDictionaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get bilingual dictionary for all supported languages",
    description="Returns the full Hindi Devanagari and English terminology glossary mapped by UI domain.",
)
async def get_bilingual_dictionary(
    locale: Optional[LocaleCode] = Query(default=None, description="Optional locale selector (en | hi)"),
) -> APIResponse[BilingualDictionaryResponse]:
    """Fetch complete bilingual translation dictionary."""
    dictionary_data = accessibility_service.get_dictionary(locale=locale)
    return APIResponse(
        success=True,
        data=dictionary_data,
        message=f"Bilingual dictionary loaded successfully with {dictionary_data.total_keys} terms.",
    )


@router.get(
    "/dictionary/{locale}",
    response_model=APIResponse[BilingualDictionaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get localized dictionary for a specific language code",
    description="Returns localized terminology definitions specifically optimized for either 'en' or 'hi'.",
)
async def get_locale_dictionary(
    locale: LocaleCode = Path(..., description="Target language code: en or hi"),
) -> APIResponse[BilingualDictionaryResponse]:
    """Fetch locale-specific dictionary."""
    dictionary_data = accessibility_service.get_dictionary(locale=locale)
    return APIResponse(
        success=True,
        data=dictionary_data,
        message=f"Bilingual dictionary for locale '{locale}' loaded successfully.",
    )


@router.post(
    "/audio-prompt",
    response_model=APIResponse[AudioPromptResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate phonetic TTS readout prompt for Web Speech synthesis",
    description="Generates simplified, phonetic speech strings designed for low-literacy citizens.",
)
async def create_audio_prompt(
    request: AudioPromptRequest,
) -> APIResponse[AudioPromptResponse]:
    """Generate spoken phonetic audio prompt."""
    prompt_res = accessibility_service.generate_audio_prompt(request)
    return APIResponse(
        success=True,
        data=prompt_res,
        message="Audio prompt generated successfully.",
    )


@router.get(
    "/preferences/{user_id}",
    response_model=APIResponse[UserAccessibilityPreference],
    status_code=status.HTTP_200_OK,
    summary="Retrieve user accessibility preferences",
    description="Gets persistent visual control preferences (font size, high contrast, locale, audio) for a user.",
)
async def get_user_preferences(
    user_id: str = Path(..., description="User ID or session identifier"),
) -> APIResponse[UserAccessibilityPreference]:
    """Retrieve user visual accessibility preferences."""
    prefs = accessibility_service.get_preferences(user_id=user_id)
    return APIResponse(
        success=True,
        data=prefs,
        message="User accessibility preferences retrieved successfully.",
    )


@router.post(
    "/preferences",
    response_model=APIResponse[UserAccessibilityPreference],
    status_code=status.HTTP_200_OK,
    summary="Save user accessibility preferences",
    description="Updates and saves visual control preferences including font scaling and high contrast.",
)
async def save_user_preferences(
    preferences: UserAccessibilityPreference,
) -> APIResponse[UserAccessibilityPreference]:
    """Save or update user visual accessibility preferences."""
    saved = accessibility_service.save_preferences(preferences)
    return APIResponse(
        success=True,
        data=saved,
        message="User accessibility preferences updated successfully.",
    )

