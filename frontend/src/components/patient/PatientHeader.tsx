"use client";

import React from "react";
import { Button, Badge } from "@/components/ui";
import { Download, Calendar, ArrowLeft, ShieldCheck, CheckCircle2 } from "lucide-react";

export interface PatientHeaderProps {
  patientName: string;
  abhaId?: string;
  abhaAddress?: string;
  activeTab: "overview" | "prescriptions" | "problems" | "records" | "book";
  onTabChange: (tab: "overview" | "prescriptions" | "problems" | "records" | "book") => void;
  onExportFhir: () => void;
}

export function PatientHeader({
  patientName,
  abhaId = "91-8472-1092-4821",
  abhaAddress = "arun.patel@abdm",
  activeTab,
  onTabChange,
  onExportFhir,
}: PatientHeaderProps) {
  // Initials for avatar
  const initials = patientName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#e5e7eb] bg-white">
      {/* Patient Identity & ABHA Verification */}
      <div className="flex items-center gap-3.5">
        <div className="h-12 w-12 rounded-full bg-[#f3f4f6] border border-[#e5e7eb] flex items-center justify-center text-[#111111] font-bold text-sm tracking-tight shrink-0 shadow-xs">
          {initials}
        </div>
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111111]">
              {patientName}
            </h1>
            <Badge variant="verified">Self-Sovereign</Badge>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#ecfdf5] text-[#065f46] border border-[#a7f3d0]">
              <CheckCircle2 className="h-3 w-3 text-[#059669]" />
              ABHA Active
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-[#6b7280]">
            <span className="font-mono text-[#111111] font-semibold">{abhaAddress}</span>
            <span>•</span>
            <span>ABHA ID: <strong className="text-[#374151] font-mono">{abhaId}</strong></span>
            <span>•</span>
            <span className="flex items-center gap-1 text-[#059669]">
              <ShieldCheck className="h-3.5 w-3.5" />
              End-to-End Encrypted
            </span>
          </div>
        </div>
      </div>

      {/* Quick Action Cluster */}
      <div className="flex items-center gap-2.5 self-start sm:self-auto shrink-0">
        <Button
          variant="secondary"
          size="sm"
          onClick={onExportFhir}
          className="border-[#e5e7eb] hover:bg-[#f8f9fa] text-xs"
        >
          <Download className="h-3.5 w-3.5 mr-1.5 text-[#6b7280]" />
          Export FHIR Bundle
        </Button>

        {activeTab === "book" ? (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onTabChange("overview")}
            className="text-xs"
          >
            <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
            Back to Dashboard
          </Button>
        ) : (
          <Button
            variant="primary"
            size="sm"
            onClick={() => onTabChange("book")}
            className="text-xs"
          >
            <Calendar className="h-3.5 w-3.5 mr-1.5" />
            Book Consultation
          </Button>
        )}
      </div>
    </div>
  );
}
