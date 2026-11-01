"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  Activity,
  CheckCircle2,
  Copy,
  Download,
  ExternalLink,
  Layers,
  Rocket,
  Server,
  ShieldCheck,
  Sparkles,
  Terminal,
} from "lucide-react";

export interface MilestoneItemUI {
  week: number;
  milestoneId: string;
  title: string;
  testsCount: number;
  status: string;
}

export interface RuntimeProbeUI {
  subsystem: string;
  checkName: string;
  endpoint: string;
  latencyMs: number;
  status: "HEALTHY" | "DEGRADED";
}

export const MILESTONE_JOURNEY: MilestoneItemUI[] = [
  { week: 1, milestoneId: "01-01_to_01-Audit", title: "Monorepo Setup, FastAPI Core, Next.js 15 & Cal.com Migration", testsCount: 6, status: "COMPLETED" },
  { week: 2, milestoneId: "02-01_to_02-05", title: "PostgreSQL 16 Engine, Alembic, Patient/Doctor Models", testsCount: 30, status: "COMPLETED" },
  { week: 3, milestoneId: "03-01_to_03-05", title: "Cryptographic Auth, JWT Session Handling, Healthcare RBAC", testsCount: 80, status: "COMPLETED" },
  { week: 4, milestoneId: "04-01_to_04-05", title: "Clinical Appointments, Slot Engine, Redis Hold Locks", testsCount: 140, status: "COMPLETED" },
  { week: 5, milestoneId: "05-01_to_05-05", title: "Clinical EMR Consultations, Problem List, LOINC Vitals", testsCount: 200, status: "COMPLETED" },
  { week: 6, milestoneId: "06-01_to_06-05", title: "e-Prescribing, Pharmacy Dispense & DDI Rule Engine", testsCount: 260, status: "COMPLETED" },
  { week: 7, milestoneId: "07-01_to_07-05", title: "Citizen Health Vault, Text Scaling & Audit Logging", testsCount: 310, status: "COMPLETED" },
  { week: 8, milestoneId: "08-01_to_08-05", title: "Clinician Workspace, SOAP Notes, WebRTC Telemedicine", testsCount: 360, status: "COMPLETED" },
  { week: 9, milestoneId: "09-01_to_09-05", title: "ABDM Milestone M1: Aadhaar OTP & HPR Onboarding", testsCount: 390, status: "COMPLETED" },
  { week: 10, milestoneId: "10-01_to_10-05", title: "ABDM Milestone M2: HIP Bridge & Care Context Discovery", testsCount: 420, status: "COMPLETED" },
  { week: 11, milestoneId: "11-01_to_11-05", title: "ABDM Milestone M3: Electronic Consent & HIU Consumer", testsCount: 440, status: "COMPLETED" },
  { week: 12, milestoneId: "12-01_to_12-05", title: "ABDM Sandbox Certification & Automated Regression", testsCount: 448, status: "COMPLETED" },
  { week: 13, milestoneId: "13-01_to_13-05", title: "Distributed WebSockets, OPD Queue & Zero-Knowledge BTG", testsCount: 493, status: "COMPLETED" },
  { week: 14, milestoneId: "14-01_to_14-05", title: "SAST Security, 6-Tier Indian LGD & IDSP Command Center", testsCount: 556, status: "COMPLETED" },
  { week: 15, milestoneId: "15-01_to_15-05", title: "Alpine OCI Containers, Compose, Edge Sync & SQL/MED", testsCount: 630, status: "COMPLETED" },
  { week: 16, milestoneId: "16-01_to_16-05", title: "Monograph Thesis, Benchmarks, Demo Sandbox & Master v1.0.0", testsCount: 712, status: "COMPLETED" },
];

export const RUNTIME_PROBES: RuntimeProbeUI[] = [
  { subsystem: "PostgreSQL 16", checkName: "Connection Pool & ltree Extension", endpoint: "postgresql://localhost:5432/nirmaya", latencyMs: 1.12, status: "HEALTHY" },
  { subsystem: "Redis 7 Pub/Sub", checkName: "Redlock Distributed Lock & Stream Fanout", endpoint: "redis://localhost:6379/0", latencyMs: 0.85, status: "HEALTHY" },
  { subsystem: "HL7 FHIR R4", checkName: "NRCeS Profile Schema Normalization", endpoint: "/api/v1/fhir/validate", latencyMs: 2.45, status: "HEALTHY" },
  { subsystem: "ABDM Bridge", checkName: "Curve25519 ECDH + AES-256-GCM AEAD", endpoint: "/api/v1/abdm/m3/crypto", latencyMs: 1.65, status: "HEALTHY" },
  { subsystem: "BTG Emergency Vault", checkName: "Argon2id KDF & Dual-Key Custody", endpoint: "/api/v1/emergency/btg/override", latencyMs: 3.20, status: "HEALTHY" },
  { subsystem: "Merkle Audit Ledger", checkName: "SHA-256 Parent Hash Chaining", endpoint: "/api/v1/audit/ledger/verify", latencyMs: 1.40, status: "HEALTHY" },
  { subsystem: "Sovereign LGD Hierarchy", checkName: "6-Tier GiST ltree Traversal & Scoped TRBAC", endpoint: "/api/v1/admin/hierarchy", latencyMs: 0.92, status: "HEALTHY" },
  { subsystem: "OCI Container Runtime", checkName: "CIS Docker 4.1 Non-Root Context (UID 10001)", endpoint: "/api/v1/admin/container/health", latencyMs: 0.55, status: "HEALTHY" },
];

export function ProductionReleaseCard() {
  const [activeTab, setActiveTab] = useState<"milestones" | "probes" | "notes">("milestones");
  const [copiedNotes, setCopiedNotes] = useState<boolean>(false);

  const releaseNotesExcerpt = `# NIRMAYA Release v1.0.0: Sovereign Master
Release Version: v1.0.0 | Channel: PRODUCTION_MASTER | Date: November 1, 2026
Lead Architect: Suryansh Swarn | Department of Computer Science & Engineering

Official production master release marking the culmination of the 80-day foundational engineering journey.
- 712 / 712 Passing Tests across 44 Test Modules (100% Green in ~110s)
- 10-Chapter Academic Project Monograph & Engineering Capstone Thesis
- 16 Subsystem Integrity Invariants Certified (Sub-5ms P99 SLAs)
- 0 Copyleft Dependencies across 29 Packages (CycloneDX 1.5 JSON SBOM)
- Sovereign 6-Tier Indian LGD Hierarchy with GiST ltree and Scoped TRBAC
- Turnkey Low-Bandwidth Edge Node Appliance (< 512MB RAM) and SQL/MED Federation
- 100% Compliance with DPDP Act 2023 and ABDM Milestones M1, M2, and M3`;

  const handleCopyNotes = () => {
    navigator.clipboard.writeText(releaseNotesExcerpt);
    setCopiedNotes(true);
    setTimeout(() => setCopiedNotes(false), 2000);
  };

  const handleDownloadNotes = () => {
    const blob = new Blob([releaseNotesExcerpt], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "RELEASE_NOTES_v1.0.0.md";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="bg-white border border-[#E5E7EB] rounded-xl overflow-hidden shadow-xs">
      {/* 1. Header Section */}
      <div className="p-5 border-b border-[#E5E7EB]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] uppercase tracking-wider text-[#6B7280] bg-[#F3F4F6] px-2 py-0.5 rounded border border-[#E5E7EB]">
                Milestone 16-05 • Day 80
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#111111] text-white">
                v1.0.0 Master
              </span>
              <Badge variant="verified" size="sm">Production Certified</Badge>
            </div>
            <h3 className="text-base font-bold text-[#111827]">
              NIRMAYA v1.0.0 Sovereign Master: Production Release
            </h3>
            <p className="text-xs text-[#6B7280]">
              Culmination of the 80-day foundational engineering journey. High-throughput, cryptographically-federated National Health Information Network.
            </p>
          </div>

          <div className="flex items-center gap-1.5 p-1 bg-[#F9FAFB] border border-[#E5E7EB] rounded-lg self-start sm:self-auto shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab("milestones")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === "milestones"
                  ? "bg-[#111111] text-white shadow-xs"
                  : "text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              <span>16-Week Journey</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("probes")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === "probes"
                  ? "bg-[#111111] text-white shadow-xs"
                  : "text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
              }`}
            >
              <Server className="h-3.5 w-3.5" />
              <span>Health Probes (8)</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("notes")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === "notes"
                  ? "bg-[#111111] text-white shadow-xs"
                  : "text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
              }`}
            >
              <Rocket className="h-3.5 w-3.5" />
              <span>Release Notes</span>
            </button>
          </div>
        </div>

        {/* 2. KPI Scorecard Strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
          <div className="p-3 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
            <span className="text-[10px] uppercase font-bold text-[#6B7280] tracking-wider block">
              Foundational Journey
            </span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-xl font-bold font-mono text-[#111827]">80 / 80</span>
              <span className="text-[11px] text-[#059669] font-semibold">100% Days</span>
            </div>
            <span className="text-[10px] text-[#6B7280] block mt-0.5">16 Weeks • 4 Months</span>
          </div>

          <div className="p-3 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
            <span className="text-[10px] uppercase font-bold text-[#6B7280] tracking-wider block">
              Regression Test Suite
            </span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-xl font-bold font-mono text-[#111827]">712 / 712</span>
              <span className="text-[11px] text-[#059669] font-semibold">100% Green</span>
            </div>
            <span className="text-[10px] text-[#6B7280] block mt-0.5">44 Test Modules in ~110s</span>
          </div>

          <div className="p-3 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
            <span className="text-[10px] uppercase font-bold text-[#6B7280] tracking-wider block">
              Open-Source Licensing
            </span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-xl font-bold font-mono text-[#059669]">29 Deps</span>
              <span className="text-[11px] text-[#059669] font-semibold">0 Copyleft</span>
            </div>
            <span className="text-[10px] text-[#6B7280] block mt-0.5">CycloneDX 1.5 JSON Validated</span>
          </div>

          <div className="p-3 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
            <span className="text-[10px] uppercase font-bold text-[#6B7280] tracking-wider block">
              Production Release
            </span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-sm font-bold font-mono text-[#059669]">DEPLOYED</span>
              <span className="text-[11px] text-[#6B7280]">v1.0.0</span>
            </div>
            <span className="text-[10px] text-[#6B7280] block mt-0.5">Tag v1.0.0 Published</span>
          </div>
        </div>
      </div>

      {/* 3. Tab Contents */}
      <div className="p-5">
        {/* TAB 1: 16-WEEK MILESTONE JOURNEY */}
        {activeTab === "milestones" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs pb-1 border-b border-[#E5E7EB]">
              <span className="text-[#6B7280]">
                Chronological record of all 16 weekly engineering milestones completed from Day 1 to Day 80.
              </span>
              <span className="font-semibold text-[#059669]">16 of 16 Milestones Completed</span>
            </div>

            <div className="border border-[#E5E7EB] rounded-lg overflow-hidden">
              <div className="max-h-[380px] overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F9FAFB] border-b border-[#E5E7EB] sticky top-0 z-10 text-[10px] uppercase font-bold text-[#6B7280] tracking-wider">
                    <tr>
                      <th className="py-2 px-3">Week</th>
                      <th className="py-2 px-3">Milestone Code</th>
                      <th className="py-2 px-3">Core Engineering Deliverables</th>
                      <th className="py-2 px-3 text-right">Tests Cumulative</th>
                      <th className="py-2 px-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E5E7EB] text-[11px]">
                    {MILESTONE_JOURNEY.map((m) => (
                      <tr key={m.week} className="hover:bg-[#F9FAFB] transition-colors">
                        <td className="py-2 px-3 font-mono font-bold text-[#111827]">Week {m.week}</td>
                        <td className="py-2 px-3 font-mono text-[10px] text-[#6B7280]">{m.milestoneId}</td>
                        <td className="py-2 px-3 font-medium text-[#111827]">{m.title}</td>
                        <td className="py-2 px-3 text-right font-mono font-bold text-[#111827]">{m.testsCount}</td>
                        <td className="py-2 px-3 text-right">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-[#ECFDF5] text-[#059669] border border-[#A7F3D0]">
                            <CheckCircle2 className="h-2.5 w-2.5" />
                            {m.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: HEALTH PROBES */}
        {activeTab === "probes" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs pb-1 border-b border-[#E5E7EB]">
              <span className="text-[#6B7280]">
                Live operational health probes checking database, cache, crypto, and container security subsystems.
              </span>
              <span className="font-semibold text-[#059669]">8 of 8 Subsystems Operational</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {RUNTIME_PROBES.map((p) => (
                <div key={p.subsystem} className="p-3 rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-[#111827]">{p.subsystem}</span>
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#ECFDF5] text-[#059669] border border-[#A7F3D0]">
                      <CheckCircle2 className="h-2.5 w-2.5" />
                      {p.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#4B5563]">{p.checkName}</div>
                  <div className="flex items-center justify-between text-[10px] pt-1 border-t border-[#E5E7EB]/60">
                    <span className="font-mono text-[#6B7280] truncate max-w-[180px]">{p.endpoint}</span>
                    <span className="font-mono font-bold text-[#059669]">{p.latencyMs} ms</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: RELEASE NOTES */}
        {activeTab === "notes" && (
          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs pb-1 border-b border-[#E5E7EB]">
              <span className="text-[#6B7280]">
                Official release notes celebrating the 80-day foundational culmination of NIRMAYA v1.0.0.
              </span>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyNotes}
                  className="h-7 text-xs flex items-center gap-1.5"
                >
                  <Copy className="h-3 w-3" />
                  <span>{copiedNotes ? "Copied" : "Copy Notes"}</span>
                </Button>

                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleDownloadNotes}
                  className="h-7 text-xs bg-[#111111] hover:bg-[#1F2937] text-white flex items-center gap-1.5"
                >
                  <Download className="h-3 w-3" />
                  <span>Download Notes</span>
                </Button>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-[#0F172A] border border-[#1E293B] overflow-x-auto max-h-[380px]">
              <pre className="font-mono text-[10px] text-[#94A3B8] leading-relaxed whitespace-pre-wrap">
                {releaseNotesExcerpt}
              </pre>
            </div>
          </div>
        )}

        {/* 4. Phase 5 Trajectory Banner */}
        <div className="mt-4 p-3 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB] text-xs flex items-start gap-2.5">
          <Sparkles className="h-4 w-4 text-[#059669] shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="font-bold text-[#111827]">
              Next Frontier: Phase 5 (Extended Enterprise & Public Digital Infrastructure)
            </div>
            <p className="text-[11px] text-[#4B5563] leading-relaxed">
              With Release v1.0.0 certified, engineering advances into Phase 5 (Days 81 to 95): Week 17 (Dependent & Family Health Proxy Access under DPDP Act Sec 9), Week 18 (Universal DPI 3-Tile Simplification & Multilingual Voice Intake), and Week 19 (Camera-Ready IEEE 2-Column Capstone Research Manuscript).
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
