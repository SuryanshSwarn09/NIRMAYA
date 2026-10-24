"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAccessibility, FontSizeOption } from "@/context/AccessibilityContext";
import { 
  Eye, 
  HelpCircle, 
  User, 
  Stethoscope, 
  FlaskConical, 
  PhoneCall, 
  Sparkles,
  Check
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
  } = useAccessibility();

  return (
    <>
      {/* Keyboard Accessibility Skip Link */}
      <a href="#main-content" className="skip-to-content focus:not-sr-only">
        Skip to main content (Press Enter)
      </a>

      {/* Approachable Accessibility & Persona Banner */}
      <aside aria-label="Accessibility and fast navigation" className="bg-[#f8f9fa] border-b border-[#e5e7eb] text-xs text-[#4b5563] py-1.5 px-3 sm:px-6">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2.5">
          
          {/* Left: Persona / Role Quick Switcher for Easy Approachability */}
          <nav aria-label="Choose your role" className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] font-semibold text-[#6b7280] mr-1 hidden sm:inline">
              Access as:
            </span>
            <Link
              href="/patient"
              className={cn(
                "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 cursor-pointer",
                pathname.startsWith("/patient")
                  ? "bg-[#111111] text-white shadow-xs"
                  : "bg-white text-[#374151] border border-[#e5e7eb] hover:bg-[#f3f4f6]"
              )}
            >
              <User className="h-3 w-3 text-[#059669]" />
              <span>Patient & Family</span>
            </Link>

            <Link
              href="/doctor"
              className={cn(
                "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 cursor-pointer",
                pathname.startsWith("/doctor")
                  ? "bg-[#111111] text-white shadow-xs"
                  : "bg-white text-[#374151] border border-[#e5e7eb] hover:bg-[#f3f4f6]"
              )}
            >
              <Stethoscope className="h-3 w-3 text-[#2563eb]" />
              <span>Doctor / EMR</span>
            </Link>

            <Link
              href="/lab"
              className={cn(
                "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 cursor-pointer",
                pathname.startsWith("/lab")
                  ? "bg-[#111111] text-white shadow-xs"
                  : "bg-white text-[#374151] border border-[#e5e7eb] hover:bg-[#f3f4f6]"
              )}
            >
              <FlaskConical className="h-3 w-3 text-[#7c3aed]" />
              <span>Diagnostic Lab</span>
            </Link>
          </nav>

          {/* Right: Accessibility Controls (Font Sizer, High Contrast, Plain Terms) */}
          <div className="flex items-center gap-2 flex-wrap ml-auto">
            
            {/* Font Size Scaling (A / A+ / A++) */}
            <div className="flex items-center bg-white rounded-md border border-[#e5e7eb] p-0.5" role="group" aria-label="Text size controls">
              <span className="text-[10px] text-[#6b7280] font-semibold px-1.5 hidden md:inline">
                Text Size:
              </span>
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
                title="Large text size (Elderly & low-vision friendly, 112.5%)"
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
              <span>{highContrast ? "High Contrast On" : "Contrast"}</span>
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
              <span>Simple Terms: {jargonHelper ? "On" : "Off"}</span>
            </button>

            {/* Emergency Helpline Pill */}
            <a
              href="tel:1075"
              className="px-2 py-1 rounded-md bg-[#fef2f2] text-[#991b1b] border border-[#fecaca] text-[11px] font-bold flex items-center gap-1 hover:bg-[#fee2e2] transition-colors"
              title="National Health Helpline (Toll Free: 1075 / 112)"
            >
              <PhoneCall className="h-2.5 w-2.5" />
              <span>1075 (Helpline)</span>
            </a>
          </div>

        </div>
      </aside>
    </>
  );
}
