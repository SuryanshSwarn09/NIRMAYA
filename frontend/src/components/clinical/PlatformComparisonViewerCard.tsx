"use client";

import React, { useState } from "react";
import { 
  ShieldCheck, 
  Layers, 
  Lock, 
  Cpu, 
  Activity, 
  FileText, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Download, 
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Award,
  Globe2,
  Stethoscope,
  Building2,
  FileCode2
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export type PlatformId = "nirmaya" | "apollo" | "aarogya" | "esanjeevani" | "cowin" | "abdm_app";

export interface PlatformProfile {
  id: PlatformId;
  name: string;
  tagline: string;
  operator: string;
  archetype: string;
  overallScore: number;
  badgeVariant: "verified" | "neutral" | "warning" | "critical" | "default";
  badgeText: string;
  highlights: string[];
  drawbacks: string[];
}

export const PLATFORM_PROFILES: Record<PlatformId, PlatformProfile> = {
  nirmaya: {
    id: "nirmaya",
    name: "NIRMAYA",
    tagline: "Sovereign Health Interoperability & Digital Public Infrastructure",
    operator: "Sovereign DPI / Open-Source (MeitY/NHA Aligned)",
    archetype: "Federated P2P Sovereign Mesh + PostgreSQL ltree + WebRTC",
    overallScore: 9.87,
    badgeVariant: "verified",
    badgeText: "Sovereign DPI",
    highlights: [
      "100% NRCeS HL7 FHIR R4 native validation with SNOMED CT and LOINC",
      "Express 45-Second Doctor OPD consultation mode with sub-50ms HPR digital signing",
      "Fidelius Curve25519-AES-GCM zero-knowledge end-to-end encryption",
      "DPDP Act 2023 Section 9 parental proxy consent with conflict resolution",
      "6-Tier sovereign LGD administrative hierarchy (india.state.dist.subdist.block.facility)",
    ],
    drawbacks: [
      "Requires institutional ABDM bridge adoption across state hospital networks",
    ],
  },
  apollo: {
    id: "apollo",
    name: "Apollo 24/7",
    tagline: "Commercial Private Healthcare Super-App & Hospital Monolith",
    operator: "Apollo Hospitals Enterprise Ltd. (Commercial)",
    archetype: "Centralized Cloud Monolith / AWS Relational & NoSQL Silos",
    overallScore: 4.93,
    badgeVariant: "critical",
    badgeText: "Commercial Monolith",
    highlights: [
      "Fast consumer pharmacy ordering and home diagnostic collection",
      "Large dedicated network of private Apollo specialists",
      "High commercial customer convenience and payment gateway integration",
    ],
    drawbacks: [
      "Severe proprietary vendor lock-in; health records cannot export to external EMRs",
      "Commercial data monetization and behavioral ad tracking (CleverTap/AppsFlyer)",
      "Zero compliance with DPDP Act Sec 9 multi-guardian verification",
      "Clunky 4–8 minute doctor EHR forms causing severe clinic delays",
    ],
  },
  aarogya: {
    id: "aarogya",
    name: "Aarogya Setu",
    tagline: "National Contact Tracing evolved to Citizen Health Status & ABHA PHR",
    operator: "National Informatics Centre (NIC) / MoHFW / MeitY",
    archetype: "Hybrid Mobile Client + Centralized Government Cloud (MeghRaj)",
    overallScore: 7.42,
    badgeVariant: "neutral",
    badgeText: "Government PHR",
    highlights: [
      "Massive citizen reach (over 200M installations across India)",
      "Native CoWIN vaccination status and 14-digit ABHA creation",
      "Zero commercial advertising or predatory marketing",
    ],
    drawbacks: [
      "Read-only citizen interface; lacks clinical EMR, doctor OPD, and lab workflows",
      "Centralized cloud dependency; no offline edge capability in rural clinics",
      "Passive PDF viewer rather than computable machine-readable FHIR engine",
    ],
  },
  esanjeevani: {
    id: "esanjeevani",
    name: "eSanjeevani",
    tagline: "National Telemedicine Service of India (Ayushman Bharat)",
    operator: "CDAC Mohali / Ministry of Health and Family Welfare (MoHFW)",
    archetype: "Hub-and-Spoke Telemedicine Web Monolith",
    overallScore: 6.86,
    badgeVariant: "warning",
    badgeText: "National Telehealth",
    highlights: [
      "Over 100M teleconsultations delivered across rural Health & Wellness Centres",
      "Structured Hub-and-Spoke referral routing (Medical Colleges to HWCs)",
      "Completely free public healthcare consultation for rural citizens",
    ],
    drawbacks: [
      "Monolithic server architecture causes frequent morning OPD connection dropouts",
      "Generates static HTML-to-PDF prescriptions rather than computable FHIR bundles",
      "Slow multi-minute consultation forms with zero 1-tap regimen bundling",
    ],
  },
  cowin: {
    id: "cowin",
    name: "CoWIN",
    tagline: "Covid-19 Vaccine Intelligence Network & High-Throughput Registry",
    operator: "Ministry of Health and Family Welfare / UNDP",
    archetype: "High-Throughput Centralized Cloud Cache + Scaled Registry",
    overallScore: 8.36,
    badgeVariant: "default",
    badgeText: "Identity Grid",
    highlights: [
      "World-record scalability: over 2.5 billion vaccine doses registered",
      "Cryptographically signed, QR-verifiable W3C compliant certificates",
      "Radically simple citizen UX with sub-15s slot verification",
    ],
    drawbacks: [
      "Single-domain scope: limited to vaccine scheduling and certificate issuance",
      "Unsuited for longitudinal multi-specialty clinical EHR or diagnostic orders",
    ],
  },
  abdm_app: {
    id: "abdm_app",
    name: "ABDM ABHA App",
    tagline: "Official National Personal Health Record (PHR) Reference Client",
    operator: "National Health Authority (NHA)",
    archetype: "Mobile PHR Client + Centralized ABDM Gateway Intermediary",
    overallScore: 8.58,
    badgeVariant: "default",
    badgeText: "NHA Reference",
    highlights: [
      "Official reference implementation of ABDM Milestone M1, M2, and M3 protocols",
      "Patient-sovereign consent management and CareContext linking",
      "Ad-free, sovereign government client with bilingual support",
    ],
    drawbacks: [
      "Pure consumer client; does not include hospital clinician consoles or lab portals",
      "Relies strictly on external HIP nodes for record rendering",
    ],
  },
};

export interface DimensionComparison {
  dimension: string;
  category: "architecture" | "privacy" | "crypto" | "clinical" | "interop" | "identity" | "telemedicine";
  nirmayaSpec: string;
  nirmayaAdvantage: string;
  competitorSpec: Record<PlatformId, string>;
  winner: string;
}

export const DIMENSION_DATA: DimensionComparison[] = [
  {
    dimension: "System Topology & Scalability",
    category: "architecture",
    nirmayaSpec: "Federated P2P Sovereign Mesh. Local PostgreSQL 16 ltree partitioning with asynchronous delta replication. Zero cloud zone lock-in.",
    nirmayaAdvantage: "No single point of failure; sub-2ms hierarchical queries across 100,000 sub-facilities.",
    competitorSpec: {
      nirmaya: "Federated P2P Mesh (PostgreSQL 16 ltree)",
      apollo: "Proprietary Centralized AWS Monolith (Relational + NoSQL Silo)",
      aarogya: "Centralized Government Cloud (NIC MeghRaj)",
      esanjeevani: "Centralized Hub-and-Spoke Web Portal (CDAC Mohali)",
      cowin: "Centralized Cloud Cache + Scaled Registry (Redis + DocumentDB)",
      abdm_app: "Client-Side App + ABDM Gateway Proxy",
    },
    winner: "NIRMAYA / CoWIN",
  },
  {
    dimension: "Data Sovereignty & DPDP Act 2023",
    category: "privacy",
    nirmayaSpec: "Full Section 9 Compliance: Parental/Guardian Proxy Verification via DigiLocker with Multi-Guardian Conflict Resolution. Zero commercial ad tracking.",
    nirmayaAdvantage: "Cryptographically verifiable minor/senior proxy access; zero data monetization.",
    competitorSpec: {
      nirmaya: "Full DPDP Sec 9 Guardian Proxy & Zero Monetization",
      apollo: "Commercial Terms of Service; Targeted Ads (CleverTap/AppsFlyer); Pharmacy Cross-Sell",
      aarogya: "Strict Government Privacy Policy; Limited Proxy Structure",
      esanjeevani: "Government Data Policy; No Formal Sec 9 Minor Adjudication",
      cowin: "Vaccination Status Public Good; Max 4 Members per Mobile",
      abdm_app: "ABDM Consent Framework Compliant; Basic Profile Linking",
    },
    winner: "NIRMAYA",
  },
  {
    dimension: "End-to-End Cryptography",
    category: "crypto",
    nirmayaSpec: "Client-Side Fidelius Curve25519 (X25519) ECDH + Ephemeral AES-256-GCM. SHA-256 Merkle Ledger for all clinical actions.",
    nirmayaAdvantage: "Central gateway acts as a Zero-Knowledge Ciphertext Pipe; tamper-evident audit trail.",
    competitorSpec: {
      nirmaya: "Curve25519 ECDH + AES-256-GCM + SHA-256 Ledger",
      apollo: "Standard TLS 1.3 Terminated at Load Balancer; Plaintext DB Storage",
      aarogya: "TLS 1.3 in Transit; Server-Side Relay",
      esanjeevani: "TLS 1.3 in Transit; Plaintext Server Processing",
      cowin: "W3C Verifiable Credentials with RSA-2048/ECDSA Signatures",
      abdm_app: "Fidelius Curve25519 Protocol for Record Transfer",
    },
    winner: "NIRMAYA",
  },
  {
    dimension: "HL7 FHIR & Clinical Ontologies",
    category: "interop",
    nirmayaSpec: "100% Native NRCeS HL7 FHIR Release 4 Schemas. Bijective SNOMED CT (350k concepts) and LOINC pathology bindings.",
    nirmayaAdvantage: "Computable, machine-readable health records that seamlessly interchange across any international EHR.",
    competitorSpec: {
      nirmaya: "Native NRCeS FHIR R4 + SNOMED CT + LOINC Builder",
      apollo: "Proprietary Database Schemas; Proprietary Pharmacy SKU Codes",
      aarogya: "FHIR Document Manifest Viewer (Read-Only)",
      esanjeevani: "Internal CDAC EHR Schema; Generates Rendered PDF Output",
      cowin: "Custom JSON Payload + Signed QR Code",
      abdm_app: "ABDM FHIR Bundle Viewer & File Downloader",
    },
    winner: "NIRMAYA",
  },
  {
    dimension: "Clinical Ergonomics & OPD Velocity",
    category: "clinical",
    nirmayaSpec: "Express 45-Second OPD Console: 1-Tap Pre-Coded Chief Complaint Chips, 1-0-1 Standard Regimen Bundles, Sub-50ms HPR Signature.",
    nirmayaAdvantage: "Enables clinicians to consult 60–100 patients/morning without administrative burnout.",
    competitorSpec: {
      nirmaya: "45-Second High-Velocity OPD + Sub-50ms HPR Sign",
      apollo: "4–8 Minutes per Patient (Multi-Screen Search Forms)",
      aarogya: "N/A (Citizen Self-Service Only)",
      esanjeevani: "5–10 Minutes per Patient (Slow Web Video + Text Form)",
      cowin: "15-Second Slot Verification (Vaccination Only)",
      abdm_app: "N/A (Citizen PHR Only)",
    },
    winner: "NIRMAYA",
  },
  {
    dimension: "Identity & Checksum Rigor",
    category: "identity",
    nirmayaSpec: "Hardware-grade Verhoeff D5 dihedral group algorithm for instantaneous typo detection. UIDAI Aadhaar OTP + DigiLocker 1-Click PKCE S256.",
    nirmayaAdvantage: "Zero-latency mathematical verification before network dispatch; passwordless session security.",
    competitorSpec: {
      nirmaya: "Verhoeff D5 Checksum + Aadhaar OTP + DigiLocker PKCE",
      apollo: "Standard 10-Digit Mobile Number + SMS OTP + Password",
      aarogya: "Mobile Number + Aadhaar Demographic Check",
      esanjeevani: "Mobile OTP + Doctor License ID",
      cowin: "Aadhaar / Passport / Photo ID Number Validation",
      abdm_app: "Aadhaar OTP + Mobile OTP ABHA Minting",
    },
    winner: "NIRMAYA / CoWIN",
  },
  {
    dimension: "Telemedicine & Network Resilience",
    category: "telemedicine",
    nirmayaSpec: "Peer-to-Peer WebRTC Mesh with Pre-Flight Device Diagnostics, dynamic bitrate scaling down to 24 kbps, and offline SQLite sync.",
    nirmayaAdvantage: "Uninterrupted clinical care in rural 2G/3G zones with intermittent grid power.",
    competitorSpec: {
      nirmaya: "P2P WebRTC Mesh + Offline Local Queue Sync",
      apollo: "Proprietary SDK (Twilio/Agora); Inoperable Offline",
      aarogya: "N/A (No Video Telemedicine)",
      esanjeevani: "Centralized Video Server; Severe Packet Loss on 2G",
      cowin: "N/A (No Telemedicine)",
      abdm_app: "N/A (No Telemedicine)",
    },
    winner: "NIRMAYA",
  },
];

export function PlatformComparisonViewerCard() {
  const [selectedPlatform, setSelectedPlatform] = useState<PlatformId>("apollo");
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"matrix" | "radar" | "summary">("matrix");

  const filteredDimensions = DIMENSION_DATA.filter((dim) => {
    if (activeCategory === "all") return true;
    return dim.category === activeCategory;
  });

  const activeProfile = PLATFORM_PROFILES[selectedPlatform];

  const handleExportJson = () => {
    const payload = {
      timestamp: new Date().toISOString(),
      benchmark: "National Health Interoperability & Architecture Benchmark v1.0",
      nirmaya: PLATFORM_PROFILES.nirmaya,
      benchmarkedPlatforms: PLATFORM_PROFILES,
      dimensions: DIMENSION_DATA,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `nirmaya-vs-${selectedPlatform}-benchmark.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="rounded-[10px] border border-[#d1d5db] bg-white shadow-xs p-6 space-y-6">
      {/* 1. Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[#e5e7eb] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-[#0b4d8c] animate-pulse" />
            <h2 className="text-lg font-bold text-[#111827]">
              National Platform Benchmark & Architectural Matrix
            </h2>
            <Badge variant="verified" size="sm">
              Sovereign DPI Analysis
            </Badge>
          </div>
          <p className="text-xs text-[#6b7280] mt-1">
            Empirical comparative analysis of NIRMAYA vs. Apollo 24/7, Aarogya Setu, eSanjeevani, CoWIN, and ABDM ABHA App across 10 architectural dimensions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Mode Switcher */}
          <div className="flex items-center rounded-lg border border-[#d1d5db] bg-[#f9fafb] p-0.5 text-xs">
            <button
              type="button"
              onClick={() => setViewMode("matrix")}
              className={`rounded-md px-3 py-1.5 font-semibold transition cursor-pointer ${
                viewMode === "matrix" ? "bg-[#0b4d8c] text-white shadow-xs" : "text-[#4b5563] hover:text-[#111827]"
              }`}
            >
              Side-by-Side Matrix
            </button>
            <button
              type="button"
              onClick={() => setViewMode("radar")}
              className={`rounded-md px-3 py-1.5 font-semibold transition cursor-pointer ${
                viewMode === "radar" ? "bg-[#0b4d8c] text-white shadow-xs" : "text-[#4b5563] hover:text-[#111827]"
              }`}
            >
              Radar Scorecard
            </button>
            <button
              type="button"
              onClick={() => setViewMode("summary")}
              className={`rounded-md px-3 py-1.5 font-semibold transition cursor-pointer ${
                viewMode === "summary" ? "bg-[#0b4d8c] text-white shadow-xs" : "text-[#4b5563] hover:text-[#111827]"
              }`}
            >
              Policy Monograph
            </button>
          </div>

          <Button variant="outline" size="sm" onClick={handleExportJson} className="text-xs">
            <Download className="h-3.5 w-3.5 mr-1" />
            Export Spec
          </Button>
        </div>
      </div>

      {viewMode === "matrix" && (
        <>
          {/* 2. Platform Selection Bar */}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-[#374151] uppercase tracking-wider">
              Select Benchmark System to Compare Against NIRMAYA:
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
              {(["apollo", "aarogya", "esanjeevani", "cowin", "abdm_app"] as PlatformId[]).map((pid) => {
                const p = PLATFORM_PROFILES[pid];
                const isSelected = selectedPlatform === pid;
                return (
                  <button
                    key={pid}
                    type="button"
                    onClick={() => setSelectedPlatform(pid)}
                    className={`p-3 rounded-lg border text-left transition-all cursor-pointer ${
                      isSelected
                        ? "border-[#0b4d8c] bg-[#e8f1f9]/40 ring-1 ring-[#0b4d8c]"
                        : "border-[#e5e7eb] bg-white hover:border-[#d1d5db] hover:bg-[#fafafa]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-[#111827]">{p.name}</span>
                      <span className="text-xs font-bold text-[#0b4d8c]">{p.overallScore}</span>
                    </div>
                    <p className="text-[11px] text-[#6b7280] truncate mt-0.5">{p.operator}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 3. Category Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            {[
              { id: "all", label: "All Dimensions" },
              { id: "architecture", label: "Topology & Scalability" },
              { id: "privacy", label: "Privacy & DPDP Act" },
              { id: "crypto", label: "Cryptography & Trust" },
              { id: "interop", label: "HL7 FHIR & Ontologies" },
              { id: "clinical", label: "Clinical Speed (OPD)" },
              { id: "identity", label: "Identity & Auth" },
              { id: "telemedicine", label: "Telemedicine & Offline" },
            ].map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() => setActiveCategory(cat.id)}
                className={`px-3 py-1 rounded-full font-medium transition cursor-pointer whitespace-nowrap ${
                  activeCategory === cat.id
                    ? "bg-[#0b4d8c] text-white"
                    : "bg-[#f3f4f6] text-[#4b5563] hover:bg-[#e5e7eb]"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* 4. Side-by-Side Comparison Profile Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left: NIRMAYA Card */}
            <div className="rounded-[8px] border-2 border-[#0b4d8c]/30 bg-[#f8fafc] p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-[#0b4d8c]">NIRMAYA</span>
                    <Badge variant="verified" size="sm">DPI Gold Standard</Badge>
                  </div>
                  <p className="text-xs text-[#4b5563] mt-0.5">{PLATFORM_PROFILES.nirmaya.tagline}</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-black text-[#0b4d8c]">{PLATFORM_PROFILES.nirmaya.overallScore}</div>
                  <div className="text-[10px] uppercase font-bold text-[#6b7280]">Composite Score</div>
                </div>
              </div>

              <div className="text-xs space-y-1.5 pt-2 border-t border-[#e2e8f0]">
                <div className="font-semibold text-[#1e293b]">Key Architectural Pillars:</div>
                {PLATFORM_PROFILES.nirmaya.highlights.map((h, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-[#334155]">
                    <CheckCircle2 className="h-3.5 w-3.5 text-[#046a38] shrink-0 mt-0.5" />
                    <span>{h}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Selected Competitor Card */}
            <div className="rounded-[8px] border border-[#d1d5db] bg-white p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-[#111827]">{activeProfile.name}</span>
                    <Badge variant={activeProfile.badgeVariant} size="sm">{activeProfile.badgeText}</Badge>
                  </div>
                  <p className="text-xs text-[#6b7280] mt-0.5">{activeProfile.tagline}</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-black text-[#111827]">{activeProfile.overallScore}</div>
                  <div className="text-[10px] uppercase font-bold text-[#6b7280]">Composite Score</div>
                </div>
              </div>

              <div className="text-xs space-y-1.5 pt-2 border-t border-[#e5e7eb]">
                <div className="font-semibold text-[#374151]">Observed Strengths & Limitations:</div>
                {activeProfile.highlights.slice(0, 2).map((h, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-[#4b5563]">
                    <CheckCircle2 className="h-3.5 w-3.5 text-[#059669] shrink-0 mt-0.5" />
                    <span>{h}</span>
                  </div>
                ))}
                {activeProfile.drawbacks.map((d, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-[#991b1b]">
                    <XCircle className="h-3.5 w-3.5 text-[#dc2626] shrink-0 mt-0.5" />
                    <span>{d}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 5. Detailed Dimension Comparison Table */}
          <div className="border border-[#e5e7eb] rounded-[8px] overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#f9fafb] border-b border-[#e5e7eb] text-[#374151] font-semibold">
                <tr>
                  <th className="p-3 w-1/4">Evaluation Dimension</th>
                  <th className="p-3 w-3/8 text-[#0b4d8c]">NIRMAYA Sovereign Specification</th>
                  <th className="p-3 w-3/8 text-[#111827]">{activeProfile.name} Specification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e5e7eb]">
                {filteredDimensions.map((dim, idx) => (
                  <tr key={idx} className="hover:bg-[#f8fafc]/50">
                    <td className="p-3 font-medium text-[#111827] align-top">
                      <div className="font-bold">{dim.dimension}</div>
                      <Badge variant="neutral" size="sm" className="mt-1 text-[10px]">
                        Advantage: {dim.winner}
                      </Badge>
                    </td>
                    <td className="p-3 bg-[#e8f1f9]/20 text-[#1e3a8a] align-top leading-relaxed">
                      <div className="font-medium">{dim.nirmayaSpec}</div>
                      <div className="text-[11px] text-[#046a38] font-semibold mt-1 flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3 inline" />
                        {dim.nirmayaAdvantage}
                      </div>
                    </td>
                    <td className="p-3 text-[#374151] align-top leading-relaxed">
                      {dim.competitorSpec[selectedPlatform]}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {viewMode === "radar" && (
        <div className="space-y-4">
          <div className="text-xs text-[#4b5563]">
            Quantitative multi-index scorecard rating platforms across seven objective engineering criteria (Scale 1–10).
          </div>
          <div className="border border-[#e5e7eb] rounded-[8px] overflow-x-auto">
            <table className="w-full text-left text-xs min-w-[700px]">
              <thead className="bg-[#f9fafb] border-b border-[#e5e7eb] text-[#374151] font-semibold">
                <tr>
                  <th className="p-3">Platform</th>
                  <th className="p-3 text-center">Architecture</th>
                  <th className="p-3 text-center">Privacy & DPDP</th>
                  <th className="p-3 text-center">Cryptography</th>
                  <th className="p-3 text-center">FHIR Interop</th>
                  <th className="p-3 text-center">Clinical Speed</th>
                  <th className="p-3 text-center">Identity Rigor</th>
                  <th className="p-3 text-center">Public Value</th>
                  <th className="p-3 text-right">Composite</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e5e7eb]">
                {[
                  { name: "NIRMAYA", scores: [9.8, 9.9, 9.9, 10.0, 9.7, 9.8, 10.0], comp: "9.87", highlight: true },
                  { name: "Apollo 24/7", scores: [7.5, 3.5, 6.0, 4.0, 5.0, 6.5, 2.0], comp: "4.93", highlight: false },
                  { name: "Aarogya Setu", scores: [7.0, 7.0, 7.5, 7.0, 0.0, 8.5, 7.5], comp: "7.42", highlight: false },
                  { name: "eSanjeevani", scores: [6.5, 8.0, 6.5, 5.5, 5.0, 8.0, 8.5], comp: "6.86", highlight: false },
                  { name: "CoWIN", scores: [9.5, 7.5, 8.5, 6.0, 8.5, 9.5, 9.0], comp: "8.36", highlight: false },
                  { name: "ABDM ABHA App", scores: [7.5, 8.5, 9.0, 8.5, 0.0, 9.0, 9.0], comp: "8.58", highlight: false },
                ].map((row, idx) => (
                  <tr key={idx} className={row.highlight ? "bg-[#e8f1f9]/40 font-bold" : "hover:bg-[#fafafa]"}>
                    <td className="p-3 text-[#111827]">
                      {row.name}
                      {row.highlight && (
                        <span className="ml-1.5 text-[10px] bg-[#0b4d8c] text-white px-1.5 py-0.2 rounded font-semibold">
                          DPI Sovereign
                        </span>
                      )}
                    </td>
                    {row.scores.map((s, si) => (
                      <td key={si} className="p-3 text-center text-[#4b5563]">
                        {s === 0 ? "—" : s.toFixed(1)}
                      </td>
                    ))}
                    <td className="p-3 text-right font-black text-[#0b4d8c]">{row.comp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {viewMode === "summary" && (
        <div className="space-y-4 text-xs text-[#374151] leading-relaxed">
          <div className="p-4 rounded-[8px] bg-[#f8fafc] border border-[#e2e8f0] space-y-2">
            <div className="font-bold text-sm text-[#0b4d8c]">
              Strategic Conclusions & Policy Recommendations for India&apos;s Digital Health Grid
            </div>
            <p>
              While <strong>Apollo 24/7</strong> pioneered commercial consumer healthcare and <strong>CoWIN</strong> proved unprecedented national scale in identity verification, NIRMAYA bridges the critical missing link in India&apos;s digital healthcare architecture: <strong>a high-velocity, privacy-preserving clinical EMR operating over a federated sovereign mesh</strong>.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3 rounded-lg border border-[#e5e7eb] bg-white space-y-1">
              <div className="font-bold text-[#111827]">1. Universal FHIR Serialization</div>
              <p className="text-[11px] text-[#6b7280]">
                Mandate NRCeS HL7 FHIR Release 4 translation across all hospitals. Transition beyond static PDF attachments to computable SNOMED CT and LOINC observations.
              </p>
            </div>
            <div className="p-3 rounded-lg border border-[#e5e7eb] bg-white space-y-1">
              <div className="font-bold text-[#111827]">2. Zero-Knowledge Cryptography</div>
              <p className="text-[11px] text-[#6b7280]">
                Enforce ephemeral Curve25519 Diffie-Hellman encryption across all ABDM gateway intermediaries to guarantee zero server-side plaintext exposure.
              </p>
            </div>
            <div className="p-3 rounded-lg border border-[#e5e7eb] bg-white space-y-1">
              <div className="font-bold text-[#111827]">3. Clinician Ergonomic Standards</div>
              <p className="text-[11px] text-[#6b7280]">
                Institutionalize 45-second Express OPD regimens across civil hospital software to remove cognitive friction and eliminate doctor resistance.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 6. Footer Meta */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-[11px] text-[#6b7280] pt-4 border-t border-[#e5e7eb] gap-2">
        <div className="flex items-center gap-1.5">
          <Award className="h-4 w-4 text-[#0b4d8c]" />
          <span>Full formal monograph published in <code className="bg-[#f3f4f6] px-1.5 py-0.5 rounded text-[#111827]">docs/reports/nirmaya-vs-apollo-aarogyasetu-comparative-analysis.md</code></span>
        </div>
        <div className="flex items-center gap-3 font-mono">
          <span>BENCHMARK-REV-2026-11</span>
          <span>COMPLIANCE: GIGW 3.0 / DPDP 2023</span>
        </div>
      </div>
    </Card>
  );
}
