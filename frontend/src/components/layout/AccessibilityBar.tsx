"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAccessibility } from "@/context/AccessibilityContext";
import { NationalEmblem } from "@/components/common/NationalEmblem";
import { 
  Eye, 
  User, 
  Stethoscope, 
  FlaskConical, 
  ShieldCheck,
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
          ? "निर्मया नागरिक पोर्टल में आपका स्वागत है। यहां आपका डिजिटल आभा स्वास्थ्य कार्ड, आज की दवाएं, और डॉक्टर के परामर्श उपलब्ध हैं।"
          : "Welcome to the NIRMAYA Citizen Portal. Here you can view your digital ABHA health card, daily medications, and doctor consultation prescriptions.";
      } else if (pathname.startsWith("/doctor")) {
        pageDescription = locale === "hi"
          ? "डॉक्टर ओपीडी कंसोल। यहां तीव्र परामर्श, मरीज की एलर्जी चेतावनी, और दवा पर्चे उपलब्ध हैं।"
          : "Doctor OPD Console. Express consultation mode, critical allergy alerts, and prescription bundles are active.";
      } else if (pathname.startsWith("/admin")) {
        pageDescription = locale === "hi"
          ? "राष्ट्रीय प्रशासनिक एवं स्वास्थ्य कमांड केंद्र। यहां 6-स्तरीय प्रशासनिक पदानुक्रम और महामारी नियंत्रण उपलब्ध है।"
          : "National Administrative and Public Health Command Center. Territorial governance and outbreak surveillance active.";
      } else {
        pageDescription = locale === "hi"
          ? "निर्मया डिजिटल स्वास्थ्य मंच में आपका स्वागत है। राष्ट्रीय स्वास्थ्य हेल्पलाइन 104 पर 24 घंटे कॉल करें।"
          : "Welcome to NIRMAYA Digital Health Network. Call national health helpline 104 toll free anytime.";
      }
      speakText(pageDescription);
    }
  };

  return (
    <>
      {/* Keyboard Accessibility Skip Link (WCAG 2.1 AA / GIGW 3.0) */}
      <a href="#main-content" className="skip-to-content focus:not-sr-only">
        {t("nav.skip_to_content", "Skip to main content (Press Enter)")}
      </a>

      {/* 1. Official National Tricolor Top Stripe (Tiranga) */}
      <div className="h-1 w-full bg-gradient-to-r from-[#ff671f] via-white to-[#046a38]" aria-hidden="true" />

      {/* 2. Official Government of India (GOI) Masthead Strip */}
      <header className="bg-white border-b border-[#e5e7eb] py-2 px-4 sm:px-6 transition-colors">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
          {/* Left: Ashok Stambh Emblem & Ministry Branding */}
          <div className="flex items-center gap-3 self-start md:self-center">
            <NationalEmblem size="md" className="text-[#0b4d8c] flex-shrink-0" />
            <div className="border-l border-[#d1d5db] pl-3 py-0.5 leading-tight">
              <div className="text-[11px] font-bold tracking-tight text-[#111111]">
                भारत सरकार | <span className="text-[#0b4d8c]">Government of India</span>
              </div>
              <div className="text-[10px] text-[#4b5563] font-medium hidden sm:block">
                स्वास्थ्य एवं परिवार कल्याण मंत्रालय | Ministry of Health & Family Welfare
              </div>
              <div className="text-[10px] text-[#0b4d8c] font-semibold">
                राष्ट्रीय स्वास्थ्य प्राधिकरण (NHA) | Ayushman Bharat Digital Mission (ABDM)
              </div>
            </div>
          </div>

          {/* Right: GIGW 3.0 Standard Accessibility Toolbar */}
          <div className="flex items-center gap-2 flex-wrap self-end md:self-center" role="toolbar" aria-label="Accessibility and Language Toolbar">
            
            {/* Bilingual Hindi / English Switcher */}
            <div className="flex items-center bg-[#f8f9fa] rounded-md border border-[#e5e7eb] p-0.5" role="group" aria-label="Language selection">
              <Languages className="h-3 w-3 text-[#6b7280] ml-1 mr-0.5 hidden sm:inline" />
              <button
                type="button"
                onClick={() => setLocale("en")}
                aria-pressed={locale === "en"}
                className={cn(
                  "px-2 py-0.5 rounded text-[11px] font-semibold transition-all cursor-pointer",
                  locale === "en"
                    ? "bg-[#0b4d8c] text-white shadow-xs"
                    : "text-[#4b5563] hover:text-[#0b4d8c]"
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
                    ? "bg-[#0b4d8c] text-white shadow-xs"
                    : "text-[#4b5563] hover:text-[#0b4d8c]"
                )}
                title="हिन्दी में बदलें (Switch to Hindi)"
              >
                हिन्दी
              </button>
            </div>

            {/* Font Size Scaling (A- / A / A+ / A++) */}
            <div className="flex items-center bg-[#f8f9fa] rounded-md border border-[#e5e7eb] p-0.5" role="group" aria-label="Text size scaling controls">
              <span className="text-[10px] text-[#6b7280] font-semibold px-1 hidden md:inline">
                {t("nav.font_size", "Text")}:
              </span>
              <button
                type="button"
                onClick={() => setFontSize("small")}
                aria-pressed={fontSize === "small"}
                className={cn(
                  "px-1.5 py-0.5 rounded text-[10px] font-bold transition-all cursor-pointer",
                  fontSize === "small"
                    ? "bg-[#0b4d8c] text-white"
                    : "text-[#4b5563] hover:text-[#0b4d8c]"
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
                    ? "bg-[#0b4d8c] text-white"
                    : "text-[#4b5563] hover:text-[#0b4d8c]"
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
                    ? "bg-[#0b4d8c] text-white"
                    : "text-[#4b5563] hover:text-[#0b4d8c]"
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
                    ? "bg-[#0b4d8c] text-white"
                    : "text-[#4b5563] hover:text-[#0b4d8c]"
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
                  ? "bg-[#000000] text-[#ffd700] border-[#000000]"
                  : "bg-[#f8f9fa] text-[#4b5563] border-[#e5e7eb] hover:bg-[#e8f1f9] hover:text-[#0b4d8c]"
              )}
              title="Toggle high-contrast theme (GIGW 3.0 / WCAG AAA)"
            >
              <Eye className="h-3 w-3 text-[#f47920]" />
              <span>{highContrast ? "High Contrast" : t("nav.high_contrast", "Contrast")}</span>
            </button>

            {/* Low-Literacy Audio Screen Readout */}
            <button
              type="button"
              onClick={handleToggleSpeech}
              aria-pressed={isSpeaking}
              className={cn(
                "px-2 py-1 rounded-md text-[11px] font-semibold border flex items-center gap-1 transition-all cursor-pointer",
                isSpeaking
                  ? "bg-[#fef3c7] text-[#92400e] border-[#fde68a] animate-pulse"
                  : "bg-[#f8f9fa] text-[#4b5563] border-[#e5e7eb] hover:bg-[#e8f1f9] hover:text-[#0b4d8c]"
              )}
              title={isSpeaking ? "Stop audio speech" : "Listen to audio readout for this page (Text-to-Speech)"}
            >
              {isSpeaking ? (
                <>
                  <VolumeX className="h-3 w-3 text-[#d97706]" />
                  <span>{t("nav.stop_listening", "Stop")}</span>
                </>
              ) : (
                <>
                  <Volume2 className="h-3 w-3 text-[#046a38]" />
                  <span className="hidden sm:inline">{t("nav.listen", "Listen")}</span>
                </>
              )}
            </button>

            {/* National Health Toll-Free Helpline 104 */}
            <a
              href="tel:104"
              className="px-2.5 py-1 rounded-md bg-[#e8f1f9] text-[#0b4d8c] border border-[#b9d5ee] text-[11px] font-bold flex items-center gap-1 hover:bg-[#d0e4f5] transition-colors"
              title="National Health Helpline (Toll Free: 104 / 1075)"
            >
              <PhoneCall className="h-3 w-3 text-[#f47920]" />
              <span>104</span>
            </a>
          </div>
        </div>
      </header>

      {/* 3. Role-Based Navigation Strip */}
      <aside aria-label="Portal Navigation" className="bg-[#f0f4f8] border-b border-[#d1d5db] text-xs text-[#374151] py-1.5 px-3 sm:px-6">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
          
          <nav aria-label="Choose your role" className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] font-semibold text-[#0b4d8c] mr-1 hidden sm:inline">
              {t("nav.access_as", "Official Portals:")}
            </span>
            <Link
              href="/patient"
              className={cn(
                "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 cursor-pointer touch-target-48 sm:touch-target",
                pathname.startsWith("/patient")
                  ? "bg-[#0b4d8c] text-white shadow-xs font-semibold"
                  : "bg-white text-[#374151] border border-[#d1d5db] hover:bg-[#e8f1f9] hover:text-[#0b4d8c]"
              )}
            >
              <User className="h-3 w-3 text-[#046a38]" />
              <span>{t("nav.patient_role", "Citizen Health Vault")}</span>
            </Link>

            <Link
              href="/doctor"
              className={cn(
                "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 cursor-pointer touch-target-48 sm:touch-target",
                pathname.startsWith("/doctor")
                  ? "bg-[#0b4d8c] text-white shadow-xs font-semibold"
                  : "bg-white text-[#374151] border border-[#d1d5db] hover:bg-[#e8f1f9] hover:text-[#0b4d8c]"
              )}
            >
              <Stethoscope className="h-3 w-3 text-[#0b4d8c]" />
              <span>{t("nav.doctor_role", "Doctor Clinical EMR")}</span>
            </Link>

            <Link
              href="/lab"
              className={cn(
                "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 cursor-pointer touch-target-48 sm:touch-target",
                pathname.startsWith("/lab")
                  ? "bg-[#0b4d8c] text-white shadow-xs font-semibold"
                  : "bg-white text-[#374151] border border-[#d1d5db] hover:bg-[#e8f1f9] hover:text-[#0b4d8c]"
              )}
            >
              <FlaskConical className="h-3 w-3 text-[#7c3aed]" />
              <span>{t("nav.lab_role", "Diagnostic Lab")}</span>
            </Link>

            <Link
              href="/admin"
              className={cn(
                "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 cursor-pointer touch-target-48 sm:touch-target",
                pathname.startsWith("/admin")
                  ? "bg-[#0b4d8c] text-white shadow-xs font-semibold"
                  : "bg-white text-[#374151] border border-[#d1d5db] hover:bg-[#e8f1f9] hover:text-[#0b4d8c]"
              )}
            >
              <ShieldCheck className="h-3 w-3 text-[#f47920]" />
              <span>{t("nav.admin_role", "Command Center")}</span>
            </Link>
          </nav>

          {/* Plain-Language Clinical Explainer Toggle */}
          <button
            type="button"
            onClick={toggleJargonHelper}
            aria-pressed={jargonHelper}
            className={cn(
              "px-2 py-0.5 rounded text-[11px] font-semibold border flex items-center gap-1 transition-all cursor-pointer ml-auto",
              jargonHelper
                ? "bg-[#ecfdf5] text-[#065f46] border-[#a7f3d0]"
                : "bg-white text-[#4b5563] border-[#d1d5db] hover:bg-[#f3f4f6]"
            )}
            title="Plain language explanations for clinical terms"
          >
            <Sparkles className="h-3 w-3 text-[#046a38]" />
            <span>Simple Terms: {jargonHelper ? "On" : "Off"}</span>
          </button>
        </div>
      </aside>
    </>
  );
}
