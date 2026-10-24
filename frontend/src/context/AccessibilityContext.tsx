"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

export type FontSizeOption = "normal" | "large" | "xl";
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
  isReady: boolean;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

const STORAGE_KEY = "nirmaya_a11y_settings";

export function AccessibilityProvider({ children }: { children: ReactNode }) {
  const [fontSize, setFontSizeState] = useState<FontSizeOption>("normal");
  const [highContrast, setHighContrastState] = useState<boolean>(false);
  const [jargonHelper, setJargonHelperState] = useState<boolean>(true);
  const [personaRole, setPersonaRoleState] = useState<PersonaRole>("all");
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
      }
    } catch {
      // Ignore localStorage read errors in private browsing
    } finally {
      setIsReady(true);
    }
  }, []);

  // Synchronize HTML classes with active accessibility state
  useEffect(() => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;

    // Font size classes
    root.classList.remove("font-size-normal", "font-size-large", "font-size-xl");
    root.classList.add(`font-size-${fontSize}`);

    // High contrast class
    if (highContrast) {
      root.classList.add("high-contrast");
    } else {
      root.classList.remove("high-contrast");
    }

    // Persist to localStorage
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ fontSize, highContrast, jargonHelper, personaRole })
      );
    } catch {
      // Ignore persistence errors
    }
  }, [fontSize, highContrast, jargonHelper, personaRole]);

  const setFontSize = (size: FontSizeOption) => setFontSizeState(size);
  const toggleHighContrast = () => setHighContrastState((prev) => !prev);
  const toggleJargonHelper = () => setJargonHelperState((prev) => !prev);
  const setPersonaRole = (role: PersonaRole) => setPersonaRoleState(role);

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
