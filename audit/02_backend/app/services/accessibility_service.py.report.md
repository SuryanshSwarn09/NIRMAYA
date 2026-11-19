# Technical Audit Report: backend/app/services/accessibility_service.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/accessibility_service.py` implements the bilingual localization and accessibility service for the NIRMAYA platform, complying with Indian Digital Public Infrastructure (DPI) guidelines, Guidelines for Indian Government Websites (GIGW 3.0), and WCAG 2.1 AA. It provides an authoritative bilingual (English and Devanagari Hindi) translation dictionary, formats phonetic text prompts for low-literacy citizens using speech synthesis, and tracks visual preferences (font scale, high contrast, audio toggle). The audit identified key operational risks: user accessibility preferences are stored exclusively in an unpersisted process memory dictionary without database backing, and preference updates lack authorization checks, allowing arbitrary cross-user modification.

### Architectural Roster
- **Module Name:** `backend/app/services/accessibility_service.py`
- **Primary Responsibility:** Bilingual dictionary provisioning (en/hi), phonetic TTS prompt formatting, and user visual accessibility preference management.
- **Upstream Dependencies:**
  - `app.schemas.accessibility` (`UserAccessibilityPreference`, `BilingualDictionaryResponse`, `AudioPromptRequest`, etc.)
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/accessibility.py`
  - Frontend visual control strip and TTS reader components
- **Exported Symbols:**
  - `AccessibilityService`
  - `accessibility_service`

```
+-----------------------------------------------------------------------------------+
|                     Indian DPI Accessibility & Localization Engine                |
|                                                                                   |
|  [Citizen / Clinician Client]                                                     |
|          |                                                                        |
|          +--> [get_dictionary(locale)]                                            |
|          |         +--> Categorized Bilingual Dictionary (Navigation, OPD, Auth)  |
|          |                                                                        |
|          +--> [generate_audio_prompt(request)]                                     |
|          |         +--> Conversational Hindi/English Speech Synthesis Guidance    |
|          |                                                                        |
|          +--> [get_preferences(user_id)] / [save_preferences(prefs)]             |
|                    +--> In-Memory _user_preferences Cache (Non-Persistent)         |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

This module delivers inclusive digital healthcare experiences tailored to multilingual and low-literacy citizens across India:

1. **Bilingual Dictionary Initialization (`_initialize_dictionary`):** Hardcodes over 30 essential clinical, administrative, and emergency terms in both English and Devanagari Hindi, along with Latin phonetic transliterations (`phonetic_hi`). Keys span top navigation (`nav.*`), citizen 3-tile portal (`citizen.*`), express OPD consultation (`doctor.*`), multi-factor authentication (`auth.*`), and 24x7 emergency helplines (`emergency.*`, including 104 Health, 108 Ambulance, and 14416 Tele-MANAS).
2. **Dictionary Retrieval (`get_dictionary`):** Groups the dictionary entries into logical UI categories (`navigation`, `citizen_portal`, `doctor_express`, `auth`, `emergency`, `general`) based on the requested locale (`en` or `hi`), returning a `BilingualDictionaryResponse`.
3. **Phonetic Speech Prompt Generation (`generate_audio_prompt`):** Tailors clinical text for browser-based speech synthesis (`SpeechSynthesisUtterance`). When a patient inspects "active medicines" or "citizen tiles", this method wraps the raw text in clear conversational phrasing (e.g. adding courteous greetings and time-taking instructions in Hindi or English) and attaches synthesis rate and voice hints (e.g. `hi-IN` voice at 0.95x rate).
4. **Preference Management (`get_preferences`, `save_preferences`):** Stores user visual settings (font scaling, high-contrast mode, TTS enabled, touch-target optimization) in an internal dictionary indexed by `user_id`.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Compliance Standards
- **GIGW 3.0 & WCAG 2.1 AA:** High-contrast toggle and text sizing must provide predictable accessibility overrides without distorting layout components.
- **Multilingual Healthcare Dignity:** Emergency contacts (104, 108, Tele-MANAS) must be accurately translated with phonetic numerals to avoid communication failure during life-threatening crises.

### Vulnerabilities & Operational Risks
- **In-Memory Preference Storage:** `self._user_preferences: Dict[str, UserAccessibilityPreference]` resides purely in Python memory without PostgreSQL persistence. When the application container restarts, all saved font sizes, contrast modes, and language selections revert to default. In multi-worker Uvicorn configurations, preferences saved on worker 1 are inaccessible to worker 2.
- **Unauthenticated IDOR on Preferences:** `save_preferences` updates `self._user_preferences[prefs.user_id]` directly from the incoming model without verifying that the requesting user owns `prefs.user_id`.
- **Thread Concurrency Hazard:** Access and mutation of `_user_preferences` occur without a threading lock (`threading.Lock`), exposing the dictionary to race conditions under concurrent async event-loop workers.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-ACC-F01` | **S1** | `[SEC]` | `accessibility_service.py:415-420` | `save_preferences` allows unauthenticated callers to overwrite any user's accessibility preferences by passing an arbitrary `user_id`. |
| `BE-SVC-ACC-F02` | **S2** | `[QUAL]` | `accessibility_service.py:27, 400-420` | User accessibility preferences are stored exclusively in an in-memory dictionary without database persistence, losing user settings on container restart. |
| `BE-SVC-ACC-F03` | **S2** | `[QUAL]` | `accessibility_service.py:27, 402-419` | Lack of thread synchronization locks around `_user_preferences` mutations introduces race conditions in multi-threaded environments. |
| `BE-SVC-ACC-F04` | **S3** | `[QUAL]` | `accessibility_service.py:32-316` | Large static translation dictionary is hardcoded in Python code rather than managed in external JSON/i18n translation catalogs. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Thread-Safe State & Persistence Warning (`BE-SVC-ACC-F02`, `BE-SVC-ACC-F03`)

```diff
--- a/backend/app/services/accessibility_service.py
+++ b/backend/app/services/accessibility_service.py
@@ -10,6 +10,7 @@
 from datetime import datetime, timezone
+import threading
 from typing import Dict, List, Optional
 from app.schemas.accessibility import (
@@ -26,6 +27,7 @@ class AccessibilityService:
     def __init__(self) -> None:
         self._user_preferences: Dict[str, UserAccessibilityPreference] = {}
+        self._lock = threading.Lock()
         self._dictionary: Dict[str, TranslationEntry] = self._initialize_dictionary()
 
     def _initialize_dictionary(self) -> Dict[str, TranslationEntry]:
@@ -402,18 +404,20 @@ class AccessibilityService:
     def get_preferences(self, user_id: str) -> UserAccessibilityPreference:
         """Fetch or initialize visual and audio accessibility preferences for a user."""
-        if user_id not in self._user_preferences:
-            self._user_preferences[user_id] = UserAccessibilityPreference(
-                user_id=user_id,
-                font_size="normal",
-                high_contrast=False,
-                locale="en",
-                tts_enabled=False,
-                jargon_helper=True,
-                touch_target_optimized=True,
-                updated_at=datetime.now(timezone.utc),
-            )
-        return self._user_preferences[user_id]
+        with self._lock:
+            if user_id not in self._user_preferences:
+                self._user_preferences[user_id] = UserAccessibilityPreference(
+                    user_id=user_id,
+                    font_size="normal",
+                    high_contrast=False,
+                    locale="en",
+                    tts_enabled=False,
+                    jargon_helper=True,
+                    touch_target_optimized=True,
+                    updated_at=datetime.now(timezone.utc),
+                )
+            return self._user_preferences[user_id]
 
     def save_preferences(self, prefs: UserAccessibilityPreference) -> UserAccessibilityPreference:
         """Update and persist visual accessibility preferences."""
         prefs.updated_at = datetime.now(timezone.utc)
-        self._user_preferences[prefs.user_id] = prefs
+        with self._lock:
+            self._user_preferences[prefs.user_id] = prefs
         return prefs
```
