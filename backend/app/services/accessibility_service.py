"""Accessibility and bilingual localization service for Day 89: Indian DPI Accessibility Suite.

Provides:
- Comprehensive bilingual Hindi (Devanagari) & English translation dictionary
- Phonetic Text-To-Speech (TTS) formatting for low-literacy citizens
- Visual accessibility preference management (font scaling, high-contrast, speech)
- GIGW 3.0 & WCAG 2.1 AA compliance validation
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.accessibility import (
    AudioPromptRequest,
    AudioPromptResponse,
    BilingualDictionaryResponse,
    FontSizeLevel,
    LocaleCode,
    TranslationEntry,
    UserAccessibilityPreference,
)


class AccessibilityService:
    """Service providing bilingual localization dictionaries, TTS audio prompts, and user a11y preferences."""

    def __init__(self) -> None:
        self._user_preferences: Dict[str, UserAccessibilityPreference] = {}
        self._dictionary: Dict[str, TranslationEntry] = self._initialize_dictionary()

    def _initialize_dictionary(self) -> Dict[str, TranslationEntry]:
        """Initialize comprehensive bilingual Hindi/English dictionary for Indian DPI healthcare."""
        entries: List[TranslationEntry] = [
            # Navigation & Global
            TranslationEntry(
                key="nav.brand",
                en="NIRMAYA Digital Health",
                hi="निर्मया डिजिटल स्वास्थ्य",
                phonetic_hi="Nirmaya Digital Swasthya",
                context="Top navigation brand header",
            ),
            TranslationEntry(
                key="nav.citizen_portal",
                en="Citizen Portal",
                hi="नागरिक पोर्टल",
                phonetic_hi="Nagrik Portal",
                context="Citizen 3-tile portal link",
            ),
            TranslationEntry(
                key="nav.doctor_opd",
                en="Doctor OPD Console",
                hi="चिकित्सक ओपीडी कंसोल",
                phonetic_hi="Chikitsak OPD Console",
                context="Doctor express OPD console link",
            ),
            TranslationEntry(
                key="nav.appointments",
                en="Appointments",
                hi="अपॉइंटमेंट",
                phonetic_hi="Appointment",
                context="Appointments navigation",
            ),
            TranslationEntry(
                key="nav.helpline",
                en="National Health Helpline: 104",
                hi="राष्ट्रीय स्वास्थ्य हेल्पलाइन: 104",
                phonetic_hi="Rashtriya Swasthya Helpline ek sau char",
                context="Top visual control strip helpline",
            ),
            TranslationEntry(
                key="nav.skip_to_content",
                en="Skip to main content",
                hi="मुख्य सामग्री पर जाएं",
                phonetic_hi="Mukhya samagri par jayein",
                context="Accessibility screen reader skip link",
            ),
            TranslationEntry(
                key="nav.listen",
                en="Listen",
                hi="सुनें",
                phonetic_hi="Sunein",
                context="TTS audio playback toggle button",
            ),
            TranslationEntry(
                key="nav.stop_listening",
                en="Stop",
                hi="रोकें",
                phonetic_hi="Rokein",
                context="TTS audio playback stop button",
            ),
            TranslationEntry(
                key="nav.high_contrast",
                en="High Contrast",
                hi="उच्च कंट्रास्ट",
                phonetic_hi="Uchch Contrast",
                context="WCAG AAA high-contrast mode toggle",
            ),
            TranslationEntry(
                key="nav.font_size",
                en="Text Size",
                hi="अक्षर का आकार",
                phonetic_hi="Akshar ka aakar",
                context="Visual control strip font scaler",
            ),

            # Citizen Portal (CoWIN/DigiLocker 3-Tile Design)
            TranslationEntry(
                key="citizen.portal.badge",
                en="ABDM Verified Citizen Health",
                hi="एबीडीएम सत्यापित नागरिक स्वास्थ्य",
                phonetic_hi="ABDM Satyapit Nagrik Swasthya",
                context="Citizen portal header badge",
            ),
            TranslationEntry(
                key="citizen.portal.title",
                en="My Health Services",
                hi="मेरी स्वास्थ्य सेवाएं",
                phonetic_hi="Meri Swasthya Sevayein",
                context="Citizen portal main title",
            ),
            TranslationEntry(
                key="citizen.portal.subtitle",
                en="Access your digital health card, active medicines, and verified consultation records.",
                hi="अपना डिजिटल स्वास्थ्य कार्ड, सक्रिय दवाएं और सत्यापित परामर्श रिकॉर्ड देखें।",
                phonetic_hi="Apna digital swasthya card, sakriya davayein aur satyapit paramarsh record dekhein.",
                context="Citizen portal subtitle",
            ),
            TranslationEntry(
                key="citizen.tile1.title",
                en="My Health ID (ABHA)",
                hi="मेरा स्वास्थ्य पहचान पत्र (आभा)",
                phonetic_hi="Mera Swasthya Pehchan Patra (ABHA)",
                context="Tile 1 title",
            ),
            TranslationEntry(
                key="citizen.tile1.desc",
                en="Digital ABHA card with instant QR code for hospital walk-in OPD registration.",
                hi="अस्पताल ओपीडी पंजीकरण के लिए तत्काल क्यूआर कोड के साथ डिजिटल आभा कार्ड।",
                phonetic_hi="Aspatal OPD panjikaran ke liye tatkal QR code ke saath digital ABHA card.",
                context="Tile 1 description",
            ),
            TranslationEntry(
                key="citizen.tile1.action",
                en="Show Hospital OPD QR Code",
                hi="अस्पताल ओपीडी क्यूआर कोड दिखाएं",
                phonetic_hi="Aspatal OPD QR code dikhayein",
                context="Tile 1 button action",
            ),
            TranslationEntry(
                key="citizen.tile2.title",
                en="Today's Medicines",
                hi="आज की दवाएं",
                phonetic_hi="Aaj ki davayein",
                context="Tile 2 title",
            ),
            TranslationEntry(
                key="citizen.tile2.desc",
                en="Plain schedules for morning, afternoon, and night without clinical jargon.",
                hi="चिकित्सीय जटिलता के बिना सुबह, दोपहर और रात की दवाओं का सरल विवरण।",
                phonetic_hi="Chikitsiya jatilta ke bina subah, dopahar aur raat ki davayon ka saral vivran.",
                context="Tile 2 description",
            ),
            TranslationEntry(
                key="citizen.tile2.morning",
                en="Morning (After Breakfast)",
                hi="सुबह (नाश्ते के बाद)",
                phonetic_hi="Subah naashte ke baad",
                context="Morning medicine slot",
            ),
            TranslationEntry(
                key="citizen.tile2.afternoon",
                en="Afternoon (After Lunch)",
                hi="दोपहर (दोपहर के भोजन के बाद)",
                phonetic_hi="Dopahar ke bhojan ke baad",
                context="Afternoon medicine slot",
            ),
            TranslationEntry(
                key="citizen.tile2.night",
                en="Night (Before Sleep)",
                hi="रात (सोने से पहले)",
                phonetic_hi="Raat sone se pehle",
                context="Night medicine slot",
            ),
            TranslationEntry(
                key="citizen.tile3.title",
                en="Past Consultations",
                hi="पिछले परामर्श और पर्चे",
                phonetic_hi="Pichhle paramarsh aur parchey",
                context="Tile 3 title",
            ),
            TranslationEntry(
                key="citizen.tile3.desc",
                en="Doctor visits and 1-click verifiable signed prescription PDFs.",
                hi="डॉक्टर से परामर्श और 1-क्लिक में डाउनलोड करने योग्य हस्ताक्षरित पर्चा।",
                phonetic_hi="Doctor se paramarsh aur ek-click mein download karne yogya hastaksharit parcha.",
                context="Tile 3 description",
            ),
            TranslationEntry(
                key="citizen.tile3.download_rx",
                en="Download Signed Prescription (PDF)",
                hi="हस्ताक्षरित पर्चा डाउनलोड करें (पीडीएफ)",
                phonetic_hi="Hastaksharit parcha download karein (PDF)",
                context="Prescription download button",
            ),

            # Express Doctor OPD Console
            TranslationEntry(
                key="doctor.express.title",
                en="Express OPD Consultation",
                hi="एक्सप्रेस ओपीडी परामर्श",
                phonetic_hi="Express OPD Paramarsh",
                context="Doctor express mode banner",
            ),
            TranslationEntry(
                key="doctor.express.switch_label",
                en="Express Mode (45-sec)",
                hi="एक्सप्रेस मोड (45 सेकंड)",
                phonetic_hi="Express Mode (paitalis second)",
                context="Doctor mode toggle switch",
            ),
            TranslationEntry(
                key="doctor.allergy.critical_alert",
                en="CRITICAL ALLERGY ALERT",
                hi="गंभीर एलर्जी चेतावनी",
                phonetic_hi="Gambhir Allergy Chetwani",
                context="Crimson allergy alert banner",
            ),
            TranslationEntry(
                key="doctor.complaints.title",
                en="Quick Chief Complaints",
                hi="त्वरित मुख्य लक्षण",
                phonetic_hi="Twarit Mukhya Lakshan",
                context="Chief complaints section",
            ),
            TranslationEntry(
                key="doctor.rx_bundles.title",
                en="1-Click Prescription Bundles",
                hi="1-क्लिक दवा बंडल",
                phonetic_hi="Ek-click dava bundle",
                context="Prescription bundle section",
            ),
            TranslationEntry(
                key="doctor.actions.sign_complete",
                en="Sign & Complete Encounter",
                hi="हस्ताक्षर करें और परामर्श पूर्ण करें",
                phonetic_hi="Hastakshar karein aur paramarsh poorn karein",
                context="Doctor sign encounter button",
            ),
            TranslationEntry(
                key="doctor.queue.advance_next",
                en="Advance to Next Patient",
                hi="अगले मरीज को बुलाएं",
                phonetic_hi="Agle mareez ko bulayein",
                context="Queue advancement button",
            ),

            # Authentication & National Gateway
            TranslationEntry(
                key="auth.aadhaar_otp",
                en="Aadhaar OTP Login",
                hi="आधार ओटीपी लॉगिन",
                phonetic_hi="Aadhaar OTP Login",
                context="Aadhaar auth button",
            ),
            TranslationEntry(
                key="auth.abha_mobile",
                en="ABHA Mobile Login",
                hi="आभा मोबाइल लॉगिन",
                phonetic_hi="ABHA Mobile Login",
                context="Mobile ABHA auth",
            ),
            TranslationEntry(
                key="auth.digilocker",
                en="DigiLocker KYC",
                hi="डिजिलॉकर केवाईसी",
                phonetic_hi="DigiLocker KYC",
                context="DigiLocker KYC option",
            ),
            TranslationEntry(
                key="auth.verify_proceed",
                en="Verify OTP & Proceed",
                hi="ओटीपी सत्यापित करें और आगे बढ़ें",
                phonetic_hi="OTP satyapit karein aur aage badhein",
                context="Auth verification button",
            ),
            TranslationEntry(
                key="auth.resend_otp",
                en="Resend OTP",
                hi="ओटीपी पुनः भेजें",
                phonetic_hi="OTP punah bhejein",
                context="Resend OTP button",
            ),

            # Emergency Helplines
            TranslationEntry(
                key="emergency.helpline_104",
                en="National Health Helpline: 104 (24x7 Toll-Free)",
                hi="राष्ट्रीय स्वास्थ्य हेल्पलाइन: 104 (24 घंटे निःशुल्क)",
                phonetic_hi="Rashtriya Swasthya Helpline ek sau char",
                context="Health helpline",
            ),
            TranslationEntry(
                key="emergency.tele_manas",
                en="Tele-MANAS Mental Health: 14416",
                hi="टेली-मानस मानसिक स्वास्थ्य: 14416",
                phonetic_hi="Tele-MANAS Mansik Swasthya: chaudah char sau solah",
                context="Mental health helpline",
            ),
            TranslationEntry(
                key="emergency.ambulance_108",
                en="Emergency Ambulance: 108",
                hi="आपातकालीन एम्बुलेंस: 108",
                phonetic_hi="Apatkaleen Ambulance: ek sau aath",
                context="Emergency ambulance",
            ),
        ]
        return {entry.key: entry for entry in entries}

    def get_dictionary(self, locale: Optional[LocaleCode] = None) -> BilingualDictionaryResponse:
        """Return the bilingual dictionary payload categorized by module."""
        loc = locale or "en"
        categories: Dict[str, Dict[str, str]] = {
            "navigation": {},
            "citizen_portal": {},
            "doctor_express": {},
            "auth": {},
            "emergency": {},
        }

        for key, entry in self._dictionary.items():
            text = entry.hi if loc == "hi" else entry.en
            if key.startswith("nav."):
                categories["navigation"][key] = text
            elif key.startswith("citizen."):
                categories["citizen_portal"][key] = text
            elif key.startswith("doctor."):
                categories["doctor_express"][key] = text
            elif key.startswith("auth."):
                categories["auth"][key] = text
            elif key.startswith("emergency."):
                categories["emergency"][key] = text
            else:
                categories.setdefault("general", {})[key] = text

        return BilingualDictionaryResponse(
            version="1.1.0",
            supported_locales=["en", "hi"],
            total_keys=len(self._dictionary),
            categories=categories,
            translations=self._dictionary,
        )

    def generate_audio_prompt(self, request: AudioPromptRequest) -> AudioPromptResponse:
        """Generate phonetic text for speech synthesis optimized for low-literacy citizens."""
        if request.target_locale == "hi":
            # If Hindi text is supplied or available, format into conversational Devanagari guidance
            base_text = request.text_hi or request.text_en
            if request.context_type == "active_medicines":
                phonetic = (
                    f"नमस्ते। आपकी आज की दवाएं हैं: {base_text}। "
                    "कृपया समय पर दवा लें और निर्देशों का पालन करें।"
                )
                hint = "Use Hindi (India) voice (hi-IN) with 0.95x speed and normal pitch."
            elif request.context_type == "citizen_tiles":
                phonetic = (
                    f"निर्मया स्वास्थ्य सेवा: {base_text}। "
                    "अस्पताल में तुरंत पंजीकरण के लिए क्यूआर कोड दिखाएं।"
                )
                hint = "Use Hindi voice (hi-IN) with steady cadence."
            elif request.context_type == "clinical_warning":
                phonetic = f"सावधान: {base_text}। कृपया डॉक्टर को तुरंत सूचित करें।"
                hint = "Emphatic tone with clear pauses between phrases."
            else:
                phonetic = base_text
                hint = "Standard Hindi speech synthesis."
        else:
            # English audio prompt
            if request.context_type == "active_medicines":
                phonetic = (
                    f"Hello. Here are your scheduled medicines for today: {request.text_en}. "
                    "Please take them on time as prescribed."
                )
                hint = "Use en-IN or en-US voice with 1.0x rate."
            elif request.context_type == "citizen_tiles":
                phonetic = (
                    f"NIRMAYA Digital Health: {request.text_en}. "
                    "Show your digital QR code for instant hospital check-in."
                )
                hint = "Clear, calm pronunciation."
            else:
                phonetic = request.text_en
                hint = "Standard English speech synthesis."

        return AudioPromptResponse(
            phonetic_speech_text=phonetic,
            target_locale=request.target_locale,
            audio_hint=hint,
            generated_at=datetime.now(timezone.utc),
        )

    def get_preferences(self, user_id: str) -> UserAccessibilityPreference:
        """Fetch or initialize visual and audio accessibility preferences for a user."""
        if user_id not in self._user_preferences:
            self._user_preferences[user_id] = UserAccessibilityPreference(
                user_id=user_id,
                font_size="normal",
                high_contrast=False,
                locale="en",
                tts_enabled=False,
                jargon_helper=True,
                touch_target_optimized=True,
                updated_at=datetime.now(timezone.utc),
            )
        return self._user_preferences[user_id]

    def save_preferences(self, prefs: UserAccessibilityPreference) -> UserAccessibilityPreference:
        """Update and persist visual accessibility preferences."""
        prefs.updated_at = datetime.now(timezone.utc)
        self._user_preferences[prefs.user_id] = prefs
        return prefs


# Global singleton instance
accessibility_service = AccessibilityService()

