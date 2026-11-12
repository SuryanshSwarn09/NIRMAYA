/**
 * Indian DPI Accessibility Suite & Bilingual Localization Dictionary (English & Hindi - हिन्दी).
 * 
 * Provides instantaneous offline-capable string translations and phonetic guides
 * conforming to GIGW 3.0 & Ayushman Bharat Digital Mission (ABDM) guidelines.
 */

export type LocaleCode = "en" | "hi";

export interface TranslationItem {
  en: string;
  hi: string;
  phonetic_hi?: string;
}

export const I18N_DICTIONARY: Record<string, TranslationItem> = {
  // Navigation & Global Visual Control Strip
  "nav.brand": {
    en: "NIRMAYA Digital Health",
    hi: "निर्मया डिजिटल स्वास्थ्य",
    phonetic_hi: "Nirmaya Digital Swasthya",
  },
  "nav.citizen_portal": {
    en: "Citizen Portal",
    hi: "नागरिक पोर्टल",
    phonetic_hi: "Nagrik Portal",
  },
  "nav.doctor_opd": {
    en: "Doctor OPD Console",
    hi: "चिकित्सक ओपीडी कंसोल",
    phonetic_hi: "Chikitsak OPD Console",
  },
  "nav.appointments": {
    en: "Appointments",
    hi: "अपॉइंटमेंट",
    phonetic_hi: "Appointment",
  },
  "nav.helpline": {
    en: "National Health Helpline: 104",
    hi: "राष्ट्रीय स्वास्थ्य हेल्पलाइन: 104",
    phonetic_hi: "Rashtriya Swasthya Helpline ek sau char",
  },
  "nav.skip_to_content": {
    en: "Skip to main content (Press Enter)",
    hi: "मुख्य सामग्री पर जाएं (Enter दबाएं)",
    phonetic_hi: "Mukhya samagri par jayein",
  },
  "nav.listen": {
    en: "Listen",
    hi: "सुनें",
    phonetic_hi: "Sunein",
  },
  "nav.stop_listening": {
    en: "Stop",
    hi: "रोकें",
    phonetic_hi: "Rokein",
  },
  "nav.high_contrast": {
    en: "High Contrast",
    hi: "उच्च कंट्रास्ट",
    phonetic_hi: "Uchch Contrast",
  },
  "nav.font_size": {
    en: "Text Size",
    hi: "अक्षर का आकार",
    phonetic_hi: "Akshar ka aakar",
  },
  "nav.access_as": {
    en: "Access as:",
    hi: "इस रूप में पहुंचें:",
    phonetic_hi: "Is roop mein pahuchein:",
  },
  "nav.patient_role": {
    en: "Patient & Family",
    hi: "मरीज और परिवार",
    phonetic_hi: "Mareez aur parivar",
  },
  "nav.doctor_role": {
    en: "Doctor / EMR",
    hi: "डॉक्टर / ईएमआर",
    phonetic_hi: "Doctor / EMR",
  },
  "nav.lab_role": {
    en: "Diagnostic Lab",
    hi: "जांच प्रयोगशाला",
    phonetic_hi: "Jaanch prayogshala",
  },

  // Citizen Portal 3-Tile Interface
  "citizen.portal.badge": {
    en: "ABDM Verified Citizen Health",
    hi: "एबीडीएम सत्यापित नागरिक स्वास्थ्य",
    phonetic_hi: "ABDM Satyapit Nagrik Swasthya",
  },
  "citizen.portal.title": {
    en: "My Health Services",
    hi: "मेरी स्वास्थ्य सेवाएं",
    phonetic_hi: "Meri Swasthya Sevayein",
  },
  "citizen.portal.subtitle": {
    en: "Access your digital health card, active medicines, and verified consultation records.",
    hi: "अपना डिजिटल स्वास्थ्य कार्ड, सक्रिय दवाएं और सत्यापित परामर्श रिकॉर्ड देखें।",
    phonetic_hi: "Apna digital swasthya card, sakriya davayein aur satyapit paramarsh record dekhein.",
  },
  "citizen.tile1.title": {
    en: "My Health ID (ABHA)",
    hi: "मेरा स्वास्थ्य पहचान पत्र (आभा)",
    phonetic_hi: "Mera Swasthya Pehchan Patra (ABHA)",
  },
  "citizen.tile1.desc": {
    en: "Digital ABHA card with instant QR code for hospital walk-in OPD registration.",
    hi: "अस्पताल ओपीडी पंजीकरण के लिए तत्काल क्यूआर कोड के साथ डिजिटल आभा कार्ड।",
    phonetic_hi: "Aspatal OPD panjikaran ke liye tatkal QR code ke saath digital ABHA card.",
  },
  "citizen.tile1.action": {
    en: "Show Hospital OPD QR Code",
    hi: "अस्पताल ओपीडी क्यूआर कोड दिखाएं",
    phonetic_hi: "Aspatal OPD QR code dikhayein",
  },
  "citizen.tile2.title": {
    en: "Today's Medicines",
    hi: "आज की दवाएं",
    phonetic_hi: "Aaj ki davayein",
  },
  "citizen.tile2.desc": {
    en: "Plain schedules for morning, afternoon, and night without clinical jargon.",
    hi: "चिकित्सीय जटिलता के बिना सुबह, दोपहर और रात की दवाओं का सरल विवरण।",
    phonetic_hi: "Chikitsiya jatilta ke bina subah, dopahar aur raat ki davayon ka saral vivran.",
  },
  "citizen.tile2.morning": {
    en: "Morning (After Breakfast)",
    hi: "सुबह (नाश्ते के बाद)",
    phonetic_hi: "Subah naashte ke baad",
  },
  "citizen.tile2.afternoon": {
    en: "Afternoon (After Lunch)",
    hi: "दोपहर (दोपहर के भोजन के बाद)",
    phonetic_hi: "Dopahar ke bhojan ke baad",
  },
  "citizen.tile2.night": {
    en: "Night (Before Sleep)",
    hi: "रात (सोने से पहले)",
    phonetic_hi: "Raat sone se pehle",
  },
  "citizen.tile3.title": {
    en: "Past Consultations",
    hi: "पिछले परामर्श और पर्चे",
    phonetic_hi: "Pichhle paramarsh aur parchey",
  },
  "citizen.tile3.desc": {
    en: "Doctor visits and 1-click verifiable signed prescription PDFs.",
    hi: "डॉक्टर से परामर्श और 1-क्लिक में डाउनलोड करने योग्य हस्ताक्षरित पर्चा।",
    phonetic_hi: "Doctor se paramarsh aur ek-click mein download karne yogya hastaksharit parcha.",
  },
  "citizen.tile3.download_rx": {
    en: "Download Signed Prescription (PDF)",
    hi: "हस्ताक्षरित पर्चा डाउनलोड करें (पीडीएफ)",
    phonetic_hi: "Hastaksharit parcha download karein (PDF)",
  },

  // Express Doctor OPD Console
  "doctor.express.title": {
    en: "Express OPD Consultation",
    hi: "एक्सप्रेस ओपीडी परामर्श",
    phonetic_hi: "Express OPD Paramarsh",
  },
  "doctor.express.switch_label": {
    en: "Express Mode (45-sec)",
    hi: "एक्सप्रेस मोड (45 सेकंड)",
    phonetic_hi: "Express Mode (paitalis second)",
  },
  "doctor.allergy.critical_alert": {
    en: "CRITICAL ALLERGY ALERT",
    hi: "गंभीर एलर्जी चेतावनी",
    phonetic_hi: "Gambhir Allergy Chetwani",
  },
  "doctor.complaints.title": {
    en: "Quick Chief Complaints",
    hi: "त्वरित मुख्य लक्षण",
    phonetic_hi: "Twarit Mukhya Lakshan",
  },
  "doctor.rx_bundles.title": {
    en: "1-Click Prescription Bundles",
    hi: "1-क्लिक दवा बंडल",
    phonetic_hi: "Ek-click dava bundle",
  },
  "doctor.actions.sign_complete": {
    en: "Sign & Complete Encounter",
    hi: "हस्ताक्षर करें और परामर्श पूर्ण करें",
    phonetic_hi: "Hastakshar karein aur paramarsh poorn karein",
  },
  "doctor.queue.advance_next": {
    en: "Advance to Next Patient",
    hi: "अगले मरीज को बुलाएं",
    phonetic_hi: "Agle mareez ko bulayein",
  },

  // Authentication & National Gateway
  "auth.aadhaar_otp": {
    en: "Aadhaar OTP Login",
    hi: "आधार ओटीपी लॉगिन",
    phonetic_hi: "Aadhaar OTP Login",
  },
  "auth.abha_mobile": {
    en: "ABHA Mobile Login",
    hi: "आभा मोबाइल लॉगिन",
    phonetic_hi: "ABHA Mobile Login",
  },
  "auth.digilocker": {
    en: "DigiLocker KYC",
    hi: "डिजिलॉकर केवाईसी",
    phonetic_hi: "DigiLocker KYC",
  },
  "auth.verify_proceed": {
    en: "Verify OTP & Proceed",
    hi: "ओटीपी सत्यापित करें और आगे बढ़ें",
    phonetic_hi: "OTP satyapit karein aur aage badhein",
  },
  "auth.resend_otp": {
    en: "Resend OTP",
    hi: "ओटीपी पुनः भेजें",
    phonetic_hi: "OTP punah bhejein",
  },

  // Emergency Helplines
  "emergency.helpline_104": {
    en: "National Health Helpline: 104 (24x7 Toll-Free)",
    hi: "राष्ट्रीय स्वास्थ्य हेल्पलाइन: 104 (24 घंटे निःशुल्क)",
    phonetic_hi: "Rashtriya Swasthya Helpline ek sau char",
  },
  "emergency.tele_manas": {
    en: "Tele-MANAS Mental Health: 14416",
    hi: "टेली-मानस मानसिक स्वास्थ्य: 14416",
    phonetic_hi: "Tele-MANAS Mansik Swasthya: chaudah char sau solah",
  },
  "emergency.ambulance_108": {
    en: "Emergency Ambulance: 108",
    hi: "आपातकालीन एम्बुलेंस: 108",
    phonetic_hi: "Apatkaleen Ambulance: ek sau aath",
  },
};

/**
 * Translate a dot-notated key to the requested locale.
 * Falls back to defaultText or English if translation key is missing.
 */
export function translate(key: string, locale: LocaleCode = "en", defaultText?: string): string {
  const item = I18N_DICTIONARY[key];
  if (!item) return defaultText || key;
  return locale === "hi" ? item.hi || item.en : item.en;
}

