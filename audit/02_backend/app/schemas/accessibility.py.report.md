# Audit Report: backend/app/schemas/accessibility.py

**Path:** `backend/app/schemas/accessibility.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 78 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for the Indian DPI Accessibility Suite and Bilingual Localization, covering bilingual English/Hindi dictionaries, phonetic Text-To-Speech (TTS) audio prompt generation, and persistent citizen/clinician accessibility preferences.
- **Risk Level:** **S3 (Low)**
- **Verdict:** **READY**
- **Single Most Important Finding:** Pydantic v2 deprecated `example` keyword argument is used across multiple `Field(...)` definitions, which produces deprecation warnings and is ignored in favor of `examples` or `json_schema_extra` during OpenAPI documentation generation.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
Digital Public Infrastructure (DPI) in India must be accessible to diverse citizens, including rural populations with varying literacy levels, non-English speakers, and users with visual or motor impairments. NIRMAYA provides bilingual English/Hindi interfaces, phonetic Devanagari text-to-speech for prescription readouts, font scaling (up to 125%), WCAG AAA 7:1 high-contrast styling, and 48px touch targets. This file structures the dictionary records, audio prompt requests, and user accessibility preference profiles.

### How it works, step by step
1. `TranslationEntry` models an individual bilingual string with English (`en`), Hindi Devanagari (`hi`), and optional phonetic pronunciation guides (`phonetic_hi`).
2. `BilingualDictionaryResponse` delivers the complete dictionary payload, organized by namespace categories, to frontend client applications.
3. `AudioPromptRequest` accepts English clinical text and context type to generate phonetic speech text for browser-based Web Speech API synthesis.
4. `AudioPromptResponse` returns optimized phonetic speech text and pronunciation guidelines.
5. `UserAccessibilityPreference` persists user-specific accessibility configurations, including `font_size` (`small`, `normal`, `large`, `xl`), `high_contrast` mode, language `locale`, `tts_enabled`, and `touch_target_optimized`.

### Concepts and patterns used
- *WCAG 2.1 AAA Accessibility Conformance:* Explicit toggles for contrast, touch target sizing, and font scaling.
- *Bilingual Transliteration / Phonetics:* Providing Devanagari phonetic hints to enable natural speech synthesis for medication names and dosages.
- *Strict Literal Types:* Using `Literal["en", "hi"]` and `Literal["small", "normal", "large", "xl"]` for tight domain constraint enforcement.

### Key lines to read first
- `accessibility.py:13-14`: Type aliases `LocaleCode` and `FontSizeLevel`.
- `accessibility.py:17-26`: `TranslationEntry` bilingual record.
- `accessibility.py:43-54`: `AudioPromptRequest` TTS model.
- `accessibility.py:66-78`: `UserAccessibilityPreference` user settings model.

### How to change it safely
When expanding language support to other Indian Eighth Schedule languages (e.g. Tamil, Telugu, Marathi, Bengali), update `LocaleCode` and ensure `TranslationEntry` accommodates the new language codes.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `timezone`, `typing` (Dict, List, Literal, Optional), `pydantic` (BaseModel, ConfigDict, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/accessibility_service.py`, `backend/app/api/v1/endpoints/accessibility.py`.
- **Public Surface:** Type aliases `LocaleCode`, `FontSizeLevel`; classes `TranslationEntry`, `BilingualDictionaryResponse`, `AudioPromptRequest`, `AudioPromptResponse`, `UserAccessibilityPreference`.

### 2. Security [SEC]
- **No PII or Secret Exposures:** Accessibility schemas handle general UI strings, translations, and generic preference flags. No credentials or patient identifiers are exposed.

### 3. Code quality [QUAL]
- **Deprecated `example` Argument (`BE-ACC-F02`):** `Field(..., example=...)` is deprecated in Pydantic v2 (lines 19, 20, 21, 45). Modern Pydantic v2 requires `examples=[...]` or `json_schema_extra={"example": ...}`.
- **Unconstrained Context Type (`BE-ACC-F01`):** `AudioPromptRequest.context_type` (line 48) uses `str` with a docstring note rather than a typed `Literal["citizen_tiles", "active_medicines", "opd_token", "clinical_warning"]`.

### 4. AI-generated-code smells [QUAL]
- None; the model cleanly addresses Indian DPI accessibility requirements.

### 5. Performance [PERF]
- Dictionary models use dictionary lookups (`Dict[str, TranslationEntry]`) enabling $O(1)$ key-based string resolution.

### 6. Error handling & edge cases
- Optional fields (`phonetic_hi`, `context`, `text_hi`) gracefully accommodate missing transliterations.

### 7. Doc accuracy [DOC]
- Perfectly matches Day 89 DPI Accessibility Suite design.

### 8. Tests
- Covered by `backend/tests/test_accessibility.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-ACC-F01 | S3 | [QUAL] | 48-51 | Unconstrained `context_type` string | `context_type: str = Field(...)` | Convert to `Literal` with allowed values |
| BE-ACC-F02 | S3 | [QUAL] | 19-21, 45 | Deprecated `example` argument in Pydantic v2 | `Field(..., example="...")` | Migrate to `examples=["..."]` or `json_schema_extra` |
| BE-ACC-F03 | S4 | [QUAL] | 13 | Locale limited to English and Hindi | `LocaleCode = Literal["en", "hi"]` | Expand to additional Indian regional languages |

---

## Suggested Patches (NOT Applied)

### Patch BE-ACC-F02 · Risk: Low · [UNTESTED]
Migrate deprecated `example` argument to Pydantic v2 `examples`:

```diff
--- a/backend/app/schemas/accessibility.py
+++ b/backend/app/schemas/accessibility.py
@@ -19,3 +19,3 @@ class TranslationEntry(BaseModel):
-    key: str = Field(description="Unique dot-notated translation key", example="citizen.tile1.title")
-    en: str = Field(description="English translation text", example="My Health ID")
-    hi: str = Field(description="Hindi (Devanagari) translation text", example="मेरा स्वास्थ्य पहचान पत्र")
+    key: str = Field(description="Unique dot-notated translation key", examples=["citizen.tile1.title"])
+    en: str = Field(description="English translation text", examples=["My Health ID"])
+    hi: str = Field(description="Hindi (Devanagari) translation text", examples=["मेरा स्वास्थ्य पहचान पत्र"])
