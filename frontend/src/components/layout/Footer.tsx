import React from "react";
import Link from "next/link";
import Image from "next/image";
import { FOOTER_SECTIONS } from "@/config/navigation";
import { NationalEmblem } from "@/components/common/NationalEmblem";
import { ExternalLink, ShieldCheck, CheckCircle2 } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-[#051c33] text-[#d1d5db] border-t border-[#0b4d8c] transition-colors" role="contentinfo">
      {/* Top Tiranga Accent Strip */}
      <div className="h-1 w-full bg-gradient-to-r from-[#ff671f] via-white to-[#046a38]" aria-hidden="true" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8 lg:gap-10">
          
          {/* Brand Identity & Sovereign DPI Mission */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <NationalEmblem size="sm" className="text-white flex-shrink-0" />
              <div className="border-l border-white/20 pl-2.5">
                <span className="font-bold text-white text-base tracking-tight block">
                  NIRMAYA
                </span>
                <span className="text-[10px] text-white/80 font-medium">
                  राष्ट्रीय डिजिटल स्वास्थ्य नेटवर्क | National Health Network
                </span>
              </div>
            </div>

            <p className="text-xs leading-relaxed text-[#9ca3af] max-w-sm">
              NIRMAYA (Networked Interoperable Records Medical Assets & Your Archives) 
              is a sovereign health information platform uniting citizen vaults, 
              clinical provider EMRs, and diagnostic laboratories under the Ayushman Bharat Digital Mission (ABDM).
            </p>

            {/* Official Compliance Pills */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-[11px] px-2.5 py-0.5 rounded-[4px] bg-[#0b4d8c] text-white font-medium border border-[#3b82c4] flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3 text-[#38bdf8]" />
                HL7 FHIR R4
              </span>
              <span className="text-[11px] px-2.5 py-0.5 rounded-[4px] bg-[#0b4d8c] text-white font-medium border border-[#3b82c4] flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3 text-[#38bdf8]" />
                ABDM Certified (M1, M2, M3)
              </span>
              <span className="text-[11px] px-2.5 py-0.5 rounded-[4px] bg-[#046a38] text-white font-medium border border-[#10b981] flex items-center gap-1">
                <ShieldCheck className="h-3 w-3 text-[#86efac]" />
                GIGW 3.0 / WCAG 2.1 AA
              </span>
            </div>
          </div>

          {/* Navigation Section Columns */}
          {FOOTER_SECTIONS.map((section) => (
            <div key={section.title} className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-white border-b border-white/10 pb-1">
                {section.title}
              </h4>
              <ul className="space-y-2 text-xs">
                {section.links.map((link) => {
                  const isExternal = link.href.startsWith("http");
                  return (
                    <li key={link.label}>
                      {isExternal ? (
                        <a
                          href={link.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-[#9ca3af] hover:text-white transition-colors"
                        >
                          <span>{link.label}</span>
                          <ExternalLink className="h-3 w-3 opacity-60" />
                        </a>
                      ) : (
                        <Link
                          href={link.href}
                          className="text-[#9ca3af] hover:text-white transition-colors"
                        >
                          {link.label}
                        </Link>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Sovereign Notice & GIGW 3.0 Attestation Bar */}
        <div className="mt-12 pt-6 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-[#9ca3af]">
          <div className="flex items-center gap-2 text-center md:text-left">
            <span>
              &copy; {new Date().getFullYear()} Government of India. Designed in accordance with UX4G & Guidelines for Indian Government Websites (GIGW 3.0).
            </span>
          </div>

          <div className="flex items-center gap-3.5 flex-wrap justify-center">
            <Link href="/privacy" className="hover:text-white transition-colors">
              Privacy Policy
            </Link>
            <span>•</span>
            <Link href="/terms" className="hover:text-white transition-colors">
              Terms of Service
            </Link>
            <span>•</span>
            <span className="text-[#f47920] font-semibold">DPDP Act 2023 Compliant</span>
            <span>•</span>
            <span>Toll Free Helpline: 104 / 1075</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
