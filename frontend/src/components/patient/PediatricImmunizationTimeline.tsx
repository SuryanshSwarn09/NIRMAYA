"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  Baby,
  Calendar,
  CheckCircle2,
  Clock,
  FileCheck,
  Plus,
  ShieldCheck,
  Syringe,
} from "lucide-react";

export interface ImmunizationDose {
  code: string;
  name: string;
  targetAge: string;
  status: "ADMINISTERED" | "SCHEDULED" | "OVERDUE";
  date?: string;
  facility?: string;
  batch?: string;
}

const UIP_VACCINES: ImmunizationDose[] = [
  {
    code: "BCG",
    name: "Bacillus Calmette-Guerin (Tuberculosis)",
    targetAge: "At Birth",
    status: "ADMINISTERED",
    date: "15 Jun 2018",
    facility: "AIIMS Pediatric Ward, New Delhi",
    batch: "SII-BCG-9021-B",
  },
  {
    code: "OPV-0",
    name: "Oral Polio Vaccine (Birth Zero Dose)",
    targetAge: "At Birth",
    status: "ADMINISTERED",
    date: "15 Jun 2018",
    facility: "AIIMS Pediatric Ward, New Delhi",
    batch: "BIBCOL-OPV-4812",
  },
  {
    code: "HepB-0",
    name: "Hepatitis B (Birth Dose)",
    targetAge: "At Birth",
    status: "ADMINISTERED",
    date: "15 Jun 2018",
    facility: "AIIMS Pediatric Ward, New Delhi",
    batch: "BB-HEPB-1049",
  },
  {
    code: "PENTA-1",
    name: "Pentavalent (DPT + HepB + Hib - Dose 1)",
    targetAge: "6 Weeks",
    status: "ADMINISTERED",
    date: "30 Jul 2018",
    facility: "Max Pediatric Care, Saket",
    batch: "SII-PENTA-3301",
  },
  {
    code: "ROTA-1",
    name: "Rotavirus Vaccine (Dose 1)",
    targetAge: "6 Weeks",
    status: "ADMINISTERED",
    date: "30 Jul 2018",
    facility: "Max Pediatric Care, Saket",
    batch: "BB-ROTA-9102",
  },
  {
    code: "PENTA-2",
    name: "Pentavalent (DPT + HepB + Hib - Dose 2)",
    targetAge: "10 Weeks",
    status: "ADMINISTERED",
    date: "02 Sep 2018",
    facility: "Max Pediatric Care, Saket",
    batch: "SII-PENTA-3419",
  },
  {
    code: "PENTA-3",
    name: "Pentavalent (DPT + HepB + Hib - Dose 3)",
    targetAge: "14 Weeks",
    status: "ADMINISTERED",
    date: "05 Oct 2018",
    facility: "Max Pediatric Care, Saket",
    batch: "SII-PENTA-3590",
  },
  {
    code: "MR-1",
    name: "Measles & Rubella (Dose 1)",
    targetAge: "9 Months",
    status: "ADMINISTERED",
    date: "20 Mar 2019",
    facility: "Apollo Children Hospital, Delhi",
    batch: "SII-MR-8812",
  },
  {
    code: "MR-2",
    name: "Measles & Rubella (Dose 2 Booster)",
    targetAge: "16-24 Months",
    status: "ADMINISTERED",
    date: "14 Jan 2020",
    facility: "Apollo Children Hospital, Delhi",
    batch: "SII-MR-9921",
  },
  {
    code: "DPT-B1",
    name: "DPT Booster 1",
    targetAge: "16-24 Months",
    status: "ADMINISTERED",
    date: "14 Jan 2020",
    facility: "Apollo Children Hospital, Delhi",
    batch: "SII-DPT-4412",
  },
  {
    code: "DPT-B2",
    name: "DPT Booster 2 (Diphtheria, Pertussis, Tetanus)",
    targetAge: "5-6 Years",
    status: "SCHEDULED",
    date: "Due Q4 2026",
    facility: "Apollo Children Hospital, Delhi",
    batch: "To be allocated",
  },
];

export function PediatricImmunizationTimeline() {
  const [filter, setFilter] = useState<"ALL" | "ADMINISTERED" | "SCHEDULED">("ALL");

  const filteredVaccines = UIP_VACCINES.filter((v) => {
    if (filter === "ALL") return true;
    return v.status === filter;
  });

  return (
    <Card className="p-6 bg-white border border-[#e5e7eb] rounded-xl shadow-none font-sans space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#e5e7eb]">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] flex items-center justify-center shrink-0">
            <Syringe className="w-5 h-5 text-[#111111]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-[#111111] tracking-tight">
                National Universal Immunization Programme (UIP) Timeline
              </h3>
              <Badge variant="abdm">INDIA UIP</Badge>
              <Badge variant="verified">WHO ALIGNED</Badge>
            </div>
            <p className="text-xs text-[#6b7280] mt-1">
              National immunization schedule tracking standard pediatric vaccines, manufacturer batch numbers, and administering medical centres under NRCeS standards.
            </p>
          </div>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center gap-1 bg-[#f9fafb] p-1 border border-[#e5e7eb] rounded-lg text-xs font-medium">
          <button
            onClick={() => setFilter("ALL")}
            className={`px-3 py-1 rounded-md transition-colors ${
              filter === "ALL"
                ? "bg-white text-[#111111] shadow-xs border border-[#e5e7eb]"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            All Doses ({UIP_VACCINES.length})
          </button>
          <button
            onClick={() => setFilter("ADMINISTERED")}
            className={`px-3 py-1 rounded-md transition-colors ${
              filter === "ADMINISTERED"
                ? "bg-white text-[#111111] shadow-xs border border-[#e5e7eb]"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            Administered (10)
          </button>
          <button
            onClick={() => setFilter("SCHEDULED")}
            className={`px-3 py-1 rounded-md transition-colors ${
              filter === "SCHEDULED"
                ? "bg-white text-[#111111] shadow-xs border border-[#e5e7eb]"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            Upcoming (1)
          </button>
        </div>
      </div>

      {/* WHO Growth Percentile Telemetry Banner */}
      <div className="p-4 rounded-xl border border-[#e5e7eb] bg-[#f9fafb] space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Baby className="w-4 h-4 text-[#111111]" />
            <span className="text-xs font-semibold text-[#111111]">
              WHO Child Growth Standards Telemetry (Age 48m)
            </span>
            <Badge variant="emerald">OPTIMAL GROWTH</Badge>
          </div>
          <span className="text-[11px] text-[#6b7280]">Last Evaluated: 15 Jun 2022</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-2.5 rounded-lg bg-white border border-[#e5e7eb]">
            <span className="text-[11px] text-[#6b7280] block">Weight</span>
            <span className="font-semibold text-[#111111]">16.3 kg</span>
            <span className="text-[10px] text-[#059669] block font-mono">55th Percentile</span>
          </div>
          <div className="p-2.5 rounded-lg bg-white border border-[#e5e7eb]">
            <span className="text-[11px] text-[#6b7280] block">Height</span>
            <span className="font-semibold text-[#111111]">103.0 cm</span>
            <span className="text-[10px] text-[#059669] block font-mono">56th Percentile</span>
          </div>
          <div className="p-2.5 rounded-lg bg-white border border-[#e5e7eb]">
            <span className="text-[11px] text-[#6b7280] block">Head Circumference</span>
            <span className="font-semibold text-[#111111]">50.1 cm</span>
            <span className="text-[10px] text-[#059669] block font-mono">Normal Z-Score</span>
          </div>
          <div className="p-2.5 rounded-lg bg-white border border-[#e5e7eb]">
            <span className="text-[11px] text-[#6b7280] block">Nutritional Status</span>
            <span className="font-semibold text-[#111111]">Normal</span>
            <span className="text-[10px] text-[#6b7280] block">Zero Wasting/Stunting</span>
          </div>
        </div>
      </div>

      {/* Timeline List */}
      <div className="space-y-3">
        {filteredVaccines.map((v) => (
          <div
            key={v.code}
            className="p-3.5 rounded-lg border border-[#e5e7eb] bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-3"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-semibold text-[#111111]">
                  {v.code}
                </span>
                <span className="text-xs text-[#374151] font-medium">{v.name}</span>
                <Badge variant="neutral" size="sm">
                  {v.targetAge}
                </Badge>
              </div>
              <div className="text-[11px] text-[#6b7280] flex flex-wrap items-center gap-2">
                <span>Facility: {v.facility || "Unassigned"}</span>
                <span>•</span>
                <span className="font-mono">Batch: {v.batch || "N/A"}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {v.status === "ADMINISTERED" ? (
                <div className="flex items-center gap-1.5 text-xs text-[#059669] bg-[#ecfdf5] border border-[#a7f3d0] px-2.5 py-1 rounded-md font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Administered ({v.date})</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 text-xs text-[#6b7280] bg-[#f9fafb] border border-[#e5e7eb] px-2.5 py-1 rounded-md font-medium">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Scheduled ({v.date})</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
