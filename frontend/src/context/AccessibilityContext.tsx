"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { LocaleCode, translate } from "@/lib/i18n/dictionary";

export type FontSizeOption = "small" | "normal" | "large" | "xl";
export type PersonaRole = "all" | "patient" | "doctor" | "lab";

interface AccessibilityContextType {
  fontSize: FontSizeOption;
  setFontSize: (size: FontSizeOption) => void;
  highContrast: boolean;
  toggleHighContrast: () => void;
  jargonHelper: boolean;
  toggleJargonHelper: () => void;
  personaRole: PersonaRole;
  setPersonaRole: (role: PersonaRole) => void;
  locale: LocaleCode;
  setLocale: (locale: LocaleCode) => void;
  t: (key: string, defaultText?: string) => string;
  speakText: (text: string, langOverride?: LocaleCode) => void;
  stopSpeaking: () => void;
  isSpeaking: boolean;
  isReady: boolean;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

const STORAGE_KEY = "nirmaya_a11y_settings";

export function AccessibilityProvider({ children }: { children: ReactNode }) {
  const [fontSize, setFontSizeState] = useState<FontSizeOption>("normal");
  const [highContrast, setHighContrastState] = useState<boolean>(false);
  const [jargonHelper, setJargonHelperState] = useState<boolean>(true);
  const [personaRole, setPersonaRoleState] = useState<PersonaRole>("all");
  const [locale, setLocaleState] = useState<LocaleCode>("en");
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isReady, setIsReady] = useState(false);

  // Initialize from localStorage safely on client
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.fontSize) setFontSizeState(parsed.fontSize);
        if (typeof parsed.highContrast === "boolean") setHighContrastState(parsed.highContrast);
        if (typeof parsed.jargonHelper === "boolean") setJargonHelperState(parsed.jargonHelper);
        if (parsed.personaRole) setPersonaRoleState(parsed.personaRole);
        if (parsed.locale && (parsed.locale === "en" || parsed.locale === "hi")) {
          setLocaleState(parsed.locale);
        }
      }
    } catch {
      // Ignore localStorage read errors in private browsing
    } finally {
      setIsReady(true);
    }
  }, []);

  // Synchronize HTML classes and language with active accessibility state
  useEffect(() => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;

    // Font size classes
    root.classList.remove("font-size-small", "font-size-normal", "font-size-large", "font-size-xl");
    root.classList.add(`font-size-${fontSize}`);

    // High contrast class
    if (highContrast) {
      root.classList.add("high-contrast");
    } else {
      root.classList.remove("high-contrast");
    }

    // Set document lang attribute for screen readers
    root.setAttribute("lang", locale === "hi" ? "hi" : "en");

    // Persist to localStorage
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ fontSize, highContrast, jargonHelper, personaRole, locale })
      );
    } catch {
      // Ignore persistence errors
    }
  }, [fontSize, highContrast, jargonHelper, personaRole, locale]);

  const setFontSize = (size: FontSizeOption) => setFontSizeState(size);
  const toggleHighContrast = () => setHighContrastState((prev) => !prev);
  const toggleJargonHelper = () => setJargonHelperState((prev) => !prev);
  const setPersonaRole = (role: PersonaRole) => setPersonaRoleState(role);
  const setLocale = (newLocale: LocaleCode) => setLocaleState(newLocale);

  // Translation function wrapper
  const t = useCallback(
    (key: string, defaultText?: string) => {
      return translate(key, locale, defaultText);
    },
    [locale]
  );

  // Audio Speech Synthesizer for low-literacy citizens
  const stopSpeaking = useCallback(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, []);

  const speakText = useCallback(
    (text: string, langOverride?: LocaleCode) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) {
        return;
      }

      window.speechSynthesis.cancel();

      const targetLang = langOverride || locale;
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = targetLang === "hi" ? "hi-IN" : "en-IN";
      utterance.rate = targetLang === "hi" ? 0.95 : 1.0;
      utterance.pitch = 1.0;

      // Try selecting a matching native voice if available
      const voices = window.speechSynthesis.getVoices();
      const matchedVoice = voices.find(
        (v) => v.lang.toLowerCase() === utterance.lang.toLowerCase() || (targetLang === "hi" && v.lang.startsWith("hi"))
      );
      if (matchedVoice) {
        utterance.voice = matchedVoice;
      }

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    },
    [locale]
  );

  return (
    <AccessibilityContext.Provider
      value={{
        fontSize,
        setFontSize,
        highContrast,
        toggleHighContrast,
        jargonHelper,
        toggleJargonHelper,
        personaRole,
        setPersonaRole,
        locale,
        setLocale,
        t,
        speakText,
        stopSpeaking,
        isSpeaking,
        isReady,
      }}
    >
      {children}
    </AccessibilityContext.Provider>
  );
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error("useAccessibility must be used within an AccessibilityProvider");
  }
  return context;
}
