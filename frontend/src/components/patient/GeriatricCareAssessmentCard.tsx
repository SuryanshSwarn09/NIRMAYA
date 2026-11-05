"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  FileText,
  HeartHandshake,
  Pill,
  ShieldAlert,
  ShieldCheck,
  Zap,
} from "lucide-react";

export function GeriatricCareAssessmentCard() {
  return (
    <Card className="p-6 bg-white border border-[#e5e7eb] rounded-xl shadow-none font-sans space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#e5e7eb]">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] flex items-center justify-center shrink-0">
            <HeartHandshake className="w-5 h-5 text-[#111111]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-[#111111] tracking-tight">
                Comprehensive Geriatric Assessment (CGA) & Polypharmacy Audit
              </h3>
              <Badge variant="warning">GERIATRIC CGA</Badge>
              <Badge variant="verified">BEERS CRITERIA</Badge>
            </div>
            <p className="text-xs text-[#6b7280] mt-1">
              Multidimensional evaluation for senior dependents covering frailty staging, Beers Criteria drug interaction warnings, and Timed Up and Go (TUG) fall risk grading.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-[#6b7280]">Last Evaluated:</span>
          <span className="text-xs font-semibold text-[#111111]">18 Oct 2026</span>
        </div>
      </div>

      {/* CGA Primary Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {/* Frailty Index */}
        <div className="p-4 rounded-xl border border-[#e5e7eb] bg-[#f9fafb] space-y-1">
          <span className="text-[11px] text-[#6b7280] block font-medium">
            Fried Frailty Score
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-[#111111]">2 / 5</span>
            <Badge variant="warning" size="sm">
              PRE-FRAIL
            </Badge>
          </div>
          <span className="text-[11px] text-[#6b7280] block">
            Mild fatigue; preserved muscle mass.
          </span>
        </div>

        {/* Fall Risk (TUG) */}
        <div className="p-4 rounded-xl border border-[#e5e7eb] bg-[#f9fafb] space-y-1">
          <span className="text-[11px] text-[#6b7280] block font-medium">
            Timed Up & Go (TUG)
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-[#111111]">13.8 s</span>
            <Badge variant="warning" size="sm">
              MODERATE RISK
            </Badge>
          </div>
          <span className="text-[11px] text-[#6b7280] block">
            Mild hesitation on uneven thresholds.
          </span>
        </div>

        {/* Katz ADL Score */}
        <div className="p-4 rounded-xl border border-[#e5e7eb] bg-[#f9fafb] space-y-1">
          <span className="text-[11px] text-[#6b7280] block font-medium">
            Katz ADL Independence
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-[#111111]">5 / 6</span>
            <Badge variant="emerald" size="sm">
              FUNCTIONAL
            </Badge>
          </div>
          <span className="text-[11px] text-[#6b7280] block">
            Independent in bathing, dressing, meals.
          </span>
        </div>

        {/* Polypharmacy Count */}
        <div className="p-4 rounded-xl border border-[#e5e7eb] bg-[#f9fafb] space-y-1">
          <span className="text-[11px] text-[#6b7280] block font-medium">
            Polypharmacy Load
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-[#111111]">5 Rx Drugs</span>
            <Badge variant="neutral" size="sm">
              ACTIVE
            </Badge>
          </div>
          <span className="text-[11px] text-[#6b7280] block">
            2 safety advisories flagged.
          </span>
        </div>
      </div>

      {/* Beers Criteria Polypharmacy Safety Audit Card */}
      <div className="p-4 rounded-xl border border-[#fef3c7] bg-[#fffbeb] space-y-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-[#d97706]" />
          <h4 className="text-xs font-semibold text-[#92400e]">
            Beers Criteria Medication Safety Warnings
          </h4>
        </div>

        <div className="space-y-2 text-xs">
          <div className="p-3 rounded-lg bg-white border border-[#fde68a] space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-[#111111]">
                Amlodipine 5mg + Atorvastatin 20mg
              </span>
              <Badge variant="warning" size="sm">
                MONITOR EDEMA
              </Badge>
            </div>
            <p className="text-[11px] text-[#6b7280]">
              Co-prescription in senior patients may increase lower extremity fluid retention and requires bilateral ankle circumference checks every 6 months.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-white border border-[#fde68a] space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-[#111111]">Pantoprazole 40mg (Daily)</span>
              <Badge variant="critical" size="sm">
                LONG-TERM CAUTION
              </Badge>
            </div>
            <p className="text-[11px] text-[#6b7280]">
              Beers Criteria Alert: Chronic proton-pump inhibitor (PPI) therapy exceeding 8 weeks increases risks of osteopenia and C. difficile enteric infection. Re-evaluate clinical indication.
            </p>
          </div>
        </div>
      </div>

      {/* Cognitive & Caregiver Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="p-4 rounded-xl border border-[#e5e7eb] bg-[#f9fafb] space-y-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#111111]" />
            <span className="font-semibold text-[#111111]">Cognitive Function (Mini-Cog)</span>
          </div>
          <p className="text-[#374151]">
            <span className="font-semibold text-[#111111]">Score: 4 / 5 (Intact).</span> Patient demonstrated 100% 3-word delayed recall after 5 minutes and accurate 12-hour analog clock face drawing with correct hand placement.
          </p>
        </div>

        <div className="p-4 rounded-xl border border-[#e5e7eb] bg-[#f9fafb] space-y-2">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-[#111111]" />
            <span className="font-semibold text-[#111111]">Caregiver & Fall Prevention Notes</span>
          </div>
          <p className="text-[#374151]">
            Patient walks independently indoors with non-skid footwear. Home safety inspection completed: grab bars installed in primary shower; throw rugs removed from living hallway.
          </p>
        </div>
      </div>
    </Card>
  );
}
