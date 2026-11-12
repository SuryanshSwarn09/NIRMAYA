"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAccessibility, FontSizeOption } from "@/context/AccessibilityContext";
import { 
  Eye, 
  User, 
  Stethoscope, 
  FlaskConical, 
  PhoneCall, 
  Sparkles,
  Volume2,
  VolumeX,
  Languages,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function AccessibilityBar() {
  const pathname = usePathname();
  const {
    fontSize,
    setFontSize,
    highContrast,
    toggleHighContrast,
    jargonHelper,
    toggleJargonHelper,
    locale,
    setLocale,
    t,
    speakText,
    stopSpeaking,
    isSpeaking,
  } = useAccessibility();

  // Low-literacy spoken readout handler
  const handleToggleSpeech = () => {
    if (isSpeaking) {
      stopSpeaking();
    } else {
      let pageDescription = "";
      if (pathname.startsWith("/patient")) {
        pageDescription = locale === "hi"
          ? "निर्मया नागरिक पोर्टल में आपका स्वागत है। यहां आपका डिजिटल आभा स्वास्थ्य कार्ड, आज की सुबह, दोपहर और रात की दवाएं, और डॉक्टर के पिछले परामर्श पर्चे उपलब्ध हैं।"
          : "Welcome to the NIRMAYA Citizen Portal. Here you can view your digital ABHA health card, today's morning, afternoon, and night medicines, and doctor consultation prescriptions.";
      } else if (pathname.startsWith("/doctor")) {
        pageDescription = locale === "hi"
          ? "डॉक्टर ओपीडी कंसोल। यहां तीव्र परामर्श, मरीज की एलर्जी चेतावनी, और 1-क्लिक दवा बंडल उपलब्ध हैं।"
          : "Doctor OPD Console. Express consultation mode, critical allergy alerts, and 1-click prescription bundles are active.";
      } else {
        pageDescription = locale === "hi"
          ? "निर्मया डिजिटल स्वास्थ्य मंच में आपका स्वागत है। राष्ट्रीय स्वास्थ्य हेल्पलाइन 104 पर 24 घंटे कॉल करें।"
          : "Welcome to NIRMAYA Digital Health. Call national health helpline 104 toll free anytime.";
      }
      speakText(pageDescription);
    }
  };

  return (
    <>
      {/* Keyboard Accessibility Skip Link (WCAG 2.1 AA) */}
      <a href="#main-content" className="skip-to-content focus:not-sr-only">
        {t("nav.skip_to_content", "Skip to main content (Press Enter)")}
      </a>

      {/* Indian DPI Universal Visual Control Strip */}
      <aside aria-label="Accessibility and visual control strip" className="bg-[#f8f9fa] border-b border-[#e5e7eb] text-xs text-[#4b5563] py-1.5 px-3 sm:px-6">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2.5">
          
          {/* Left: Persona / Role Quick Switcher */}
          <nav aria-label="Choose your role" className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] font-semibold text-[#6b7280] mr-1 hidden sm:inline">
              {t("nav.access_as", "Access as:")}
            </span>
            <Link
              href="/patient"
              className={cn(
                "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 cursor-pointer touch-target-48 sm:touch-target",
                pathname.startsWith("/patient")
                  ? "bg-[#111111] text-white shadow-xs"
                  : "bg-white text-[#374151] border border-[#e5e7eb] hover:bg-[#f3f4f6]"
              )}
            >
              <User className="h-3 w-3 text-[#059669]" />
              <span>{t("nav.patient_role", "Patient & Family")}</span>
            </Link>

            <Link
              href="/doctor"
              className={cn(
                "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 cursor-pointer touch-target-48 sm:touch-target",
                pathname.startsWith("/doctor")
                  ? "bg-[#111111] text-white shadow-xs"
                  : "bg-white text-[#374151] border border-[#e5e7eb] hover:bg-[#f3f4f6]"
              )}
            >
              <Stethoscope className="h-3 w-3 text-[#2563eb]" />
              <span>{t("nav.doctor_role", "Doctor / EMR")}</span>
            </Link>

            <Link
              href="/lab"
              className={cn(
                "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 cursor-pointer touch-target-48 sm:touch-target",
                pathname.startsWith("/lab")
                  ? "bg-[#111111] text-white shadow-xs"
                  : "bg-white text-[#374151] border border-[#e5e7eb] hover:bg-[#f3f4f6]"
              )}
            >
              <FlaskConical className="h-3 w-3 text-[#7c3aed]" />
              <span>{t("nav.lab_role", "Diagnostic Lab")}</span>
            </Link>
          </nav>

          {/* Right: Accessibility Controls (Bilingual Switcher, Audio Readout, Font Scaler, Contrast) */}
          <div className="flex items-center gap-2 flex-wrap ml-auto">
            
            {/* Bilingual Hindi / English Switcher */}
            <div className="flex items-center bg-white rounded-md border border-[#e5e7eb] p-0.5" role="group" aria-label="Language selection">
              <Languages className="h-3 w-3 text-[#6b7280] ml-1 mr-0.5 hidden sm:inline" />
              <button
                type="button"
                onClick={() => setLocale("en")}
                aria-pressed={locale === "en"}
                className={cn(
                  "px-2 py-0.5 rounded text-[11px] font-semibold transition-all cursor-pointer",
                  locale === "en"
                    ? "bg-[#111111] text-white"
                    : "text-[#4b5563] hover:text-[#111111]"
                )}
                title="Switch to English"
              >
                English
              </button>
              <button
                type="button"
                onClick={() => setLocale("hi")}
                aria-pressed={locale === "hi"}
                className={cn(
                  "px-2 py-0.5 rounded text-[11px] font-semibold transition-all cursor-pointer",
                  locale === "hi"
                    ? "bg-[#111111] text-white"
                    : "text-[#4b5563] hover:text-[#111111]"
                )}
                title="हिन्दी में बदलें (Switch to Hindi)"
              >
                हिन्दी
              </button>
            </div>

            {/* Low-Literacy Audio Screen Readout (Web Speech API) */}
            <button
              type="button"
              onClick={handleToggleSpeech}
              aria-pressed={isSpeaking}
              className={cn(
                "px-2 py-1 rounded-md text-[11px] font-semibold border flex items-center gap-1 transition-all cursor-pointer",
                isSpeaking
                  ? "bg-[#fef3c7] text-[#92400e] border-[#fde68a] animate-pulse"
                  : "bg-white text-[#4b5563] border-[#e5e7eb] hover:bg-[#f3f4f6] hover:text-[#111111]"
              )}
              title={isSpeaking ? "Stop audio speech" : "Listen to audio readout for this page (Low-literacy TTS)"}
            >
              {isSpeaking ? (
                <>
                  <VolumeX className="h-3 w-3 text-[#d97706]" />
                  <span>{t("nav.stop_listening", "Stop")}</span>
                </>
              ) : (
                <>
                  <Volume2 className="h-3 w-3 text-[#059669]" />
                  <span>{t("nav.listen", "Listen")}</span>
                </>
              )}
            </button>

            {/* Font Size Scaling (A- / A / A+ / A++) */}
            <div className="flex items-center bg-white rounded-md border border-[#e5e7eb] p-0.5" role="group" aria-label="Text size controls">
              <span className="text-[10px] text-[#6b7280] font-semibold px-1 hidden md:inline">
                {t("nav.font_size", "Text Size")}:
              </span>
              <button
                type="button"
                onClick={() => setFontSize("small")}
                aria-pressed={fontSize === "small"}
                className={cn(
                  "px-1.5 py-0.5 rounded text-[10px] font-bold transition-all cursor-pointer",
                  fontSize === "small"
                    ? "bg-[#111111] text-white"
                    : "text-[#4b5563] hover:text-[#111111]"
                )}
                title="Small text size (87.5%)"
              >
                A-
              </button>
              <button
                type="button"
                onClick={() => setFontSize("normal")}
                aria-pressed={fontSize === "normal"}
                className={cn(
                  "px-1.5 py-0.5 rounded text-[11px] font-bold transition-all cursor-pointer",
                  fontSize === "normal"
                    ? "bg-[#111111] text-white"
                    : "text-[#4b5563] hover:text-[#111111]"
                )}
                title="Normal text size (100%)"
              >
                A
              </button>
              <button
                type="button"
                onClick={() => setFontSize("large")}
                aria-pressed={fontSize === "large"}
                className={cn(
                  "px-1.5 py-0.5 rounded text-xs font-bold transition-all cursor-pointer",
                  fontSize === "large"
                    ? "bg-[#111111] text-white"
                    : "text-[#4b5563] hover:text-[#111111]"
                )}
                title="Large text size (112.5%)"
              >
                A+
              </button>
              <button
                type="button"
                onClick={() => setFontSize("xl")}
                aria-pressed={fontSize === "xl"}
                className={cn(
                  "px-1.5 py-0.5 rounded text-sm font-bold transition-all cursor-pointer",
                  fontSize === "xl"
                    ? "bg-[#111111] text-white"
                    : "text-[#4b5563] hover:text-[#111111]"
                )}
                title="Extra large text size (125%)"
              >
                A++
              </button>
            </div>

            {/* High Contrast Mode Toggle */}
            <button
              type="button"
              onClick={toggleHighContrast}
              aria-pressed={highContrast}
              className={cn(
                "px-2 py-1 rounded-md text-[11px] font-semibold border flex items-center gap-1 transition-all cursor-pointer",
                highContrast
                  ? "bg-[#000000] text-white border-[#000000]"
                  : "bg-white text-[#4b5563] border-[#e5e7eb] hover:bg-[#f3f4f6] hover:text-[#111111]"
              )}
              title="Toggle high-contrast mode for enhanced visual readability"
            >
              <Eye className="h-3 w-3" />
              <span>{highContrast ? "High Contrast On" : t("nav.high_contrast", "Contrast")}</span>
            </button>

            {/* Plain-Language Medical Explainer Toggle */}
            <button
              type="button"
              onClick={toggleJargonHelper}
              aria-pressed={jargonHelper}
              className={cn(
                "px-2 py-1 rounded-md text-[11px] font-semibold border flex items-center gap-1 transition-all cursor-pointer",
                jargonHelper
                  ? "bg-[#ecfdf5] text-[#065f46] border-[#a7f3d0]"
                  : "bg-white text-[#6b7280] border-[#e5e7eb] hover:bg-[#f3f4f6]"
              )}
              title="Plain language explanations for clinical terms"
            >
              <Sparkles className="h-3 w-3 text-[#059669]" />
              <span className="hidden sm:inline">Simple Terms: {jargonHelper ? "On" : "Off"}</span>
            </button>

            {/* Emergency Helpline Pill */}
            <a
              href="tel:104"
              className="px-2 py-1 rounded-md bg-[#fef2f2] text-[#991b1b] border border-[#fecaca] text-[11px] font-bold flex items-center gap-1 hover:bg-[#fee2e2] transition-colors"
              title="National Health Helpline (Toll Free: 104 / 112)"
            >
              <PhoneCall className="h-2.5 w-2.5" />
              <span>104</span>
            </a>
          </div>

        </div>
      </aside>
    </>
  );
}
