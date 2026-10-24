import React from "react";
import Link from "next/link";
import Image from "next/image";
import { FOOTER_SECTIONS } from "@/config/navigation";

import { ExternalLink, Shield } from "lucide-react";

/**
 * Signature Modern SaaS Footer:
 * Deep near-black surface (#101010) with muted light text (#a1a1aa).
 * The footer is the dedicated dark surface on the page: visually grounding the application.
 */
export function Footer() {
  return (
    <footer className="bg-[#101010] text-[#a1a1aa] border-t border-[#1a1a1a] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8 lg:gap-10">
          {/* Brand Identity & Mission Statement */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-[8px] bg-white flex items-center justify-center overflow-hidden border border-[#262626]">
                <Image
                  src="/logo.png"
                  alt="NIRMAYA Logo"
                  width={32}
                  height={32}
                  className="object-contain"
                />
              </div>

              <span className="font-bold text-white text-lg tracking-tight">
                nirmaya
              </span>
              <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded-[4px] bg-[#1a1a1a] text-[#a1a1aa] border border-[#262626]">
                Network
              </span>
            </div>

            <p className="text-sm leading-relaxed text-[#a1a1aa] max-w-sm">
              NIRMAYA (Networked Interoperable Records Medical Assets & Your Archives) 
              is a standardized health informatics platform uniting patient vaults, 
              clinical provider EMRs, and diagnostic laboratories into an interoperable FHIR network.
            </p>

            <div className="flex flex-wrap items-center gap-2 pt-2">
              <span className="text-xs px-2.5 py-1 rounded-[4px] bg-[#1a1a1a] text-[#e4e4e7] border border-[#262626]">
                HL7 FHIR R4
              </span>
              <span className="text-xs px-2.5 py-1 rounded-[4px] bg-[#1a1a1a] text-[#e4e4e7] border border-[#262626]">
                ABHA Verified
              </span>
              <span className="text-xs px-2.5 py-1 rounded-[4px] bg-[#1a1a1a] text-[#e4e4e7] border border-[#262626]">
                Consent Driven
              </span>
            </div>
          </div>

          {/* 4 Navigation Section Columns */}
          {FOOTER_SECTIONS.map((section) => (
            <div key={section.title} className="space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-white">
                {section.title}
              </h4>
              <ul className="space-y-2.5 text-sm">
                {section.links.map((link) => {
                  const isExternal = link.href.startsWith("http");
                  return (
                    <li key={link.label}>
                      {isExternal ? (
                        <a
                          href={link.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-[#a1a1aa] hover:text-white transition-colors"
                        >
                          <span>{link.label}</span>
                          <ExternalLink className="h-3 w-3 opacity-60" />
                        </a>
                      ) : (
                        <Link
                          href={link.href}
                          className="text-[#a1a1aa] hover:text-white transition-colors"
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

        {/* Bottom Legal & Project Credit Bar */}
        <div className="mt-14 pt-8 border-t border-[#1a1a1a] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#71717a]">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-[#a1a1aa]" />
            <span>
              &copy; {new Date().getFullYear()} NIRMAYA Health Network. Open Health Informatics Architecture.
            </span>
          </div>

          <div className="flex items-center gap-4 text-[#71717a]">
            <Link href="/privacy" className="hover:text-white transition-colors">
              Privacy Policy
            </Link>
            <span>•</span>
            <Link href="/terms" className="hover:text-white transition-colors">
              Terms & Conditions
            </Link>
            <span>•</span>
            <span>DPDP Act 2023</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
