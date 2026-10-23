"use client";

import React from "react";
import { Badge, Button } from "@/components/ui";
import { ClinicalCondition } from "@/lib/api";
import { 
  findConditionTerminology, 
  getSeverityBadgeConfig, 
  getClinicalStatusBadgeConfig, 
  formatConditionDate, 
  getCategoryLabel 
} from "@/lib/conditions";
import { 
  FileCode, 
  ShieldCheck, 
  Activity, 
  Calendar, 
  Sparkles, 
  ChevronRight, 
  Stethoscope, 
  Info,
  CheckCircle2,
  Clock,
  HeartPulse
} from "lucide-react";

export interface PatientConditionCardProps {
  condition: ClinicalCondition;
  onViewFhir?: (condition: ClinicalCondition) => void;
  onOpenUpdateModal?: (condition: ClinicalCondition) => void;
  className?: string;
}

export function PatientConditionCard({
  condition,
  onViewFhir,
  onOpenUpdateModal,
  className = "",
}: PatientConditionCardProps) {
  // Resolve mapping from SNOMED-CT or ICD-10 dictionary
  const mapping = findConditionTerminology(condition.code_value) || findConditionTerminology(condition.code_display);

  const statusConfig = getClinicalStatusBadgeConfig(condition.clinical_status);
  const severityConfig = getSeverityBadgeConfig(condition.severity || mapping?.typicalSeverity);
  const isSnomed = condition.code_coding_system.includes("snomed");
  const isIcd10 = condition.code_coding_system.includes("icd-10") || condition.code_coding_system.includes("icd");

  const primaryName = mapping?.commonName || condition.code_display;
  const snomedCode = mapping?.snomedCode || (isSnomed ? condition.code_value : undefined);
  const icd10Code = mapping?.icd10Code || (isIcd10 ? condition.code_value : undefined);

  return (
    <div className={`p-5 rounded-[14px] bg-white border border-[#e5e7eb] shadow-xs hover:border-[#d1d5db] transition-all space-y-4 ${className}`}>
      
      {/* 1. Header: Concept Title & Terminology Chips */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs uppercase font-bold tracking-wider text-[#6b7280]">
              {getCategoryLabel(condition.category)}
            </span>
            <span className="text-[#d1d5db]">•</span>
            <span className="text-xs font-mono text-[#4b5563] flex items-center gap-1">
              <Calendar className="h-3 w-3 text-[#6b7280]" />
              Onset: {formatConditionDate(condition.onset_date_time)}
            </span>
          </div>

          <h3 className="text-base sm:text-lg font-bold text-[#111111] tracking-tight">
            {primaryName}
          </h3>

          {/* Clinical Diagnostic Display Name if different from common title */}
          {condition.code_display !== primaryName && (
            <p className="text-xs text-[#6b7280] italic">
              Formal Concept: {condition.code_display}
            </p>
          )}

          {/* Dual Terminology Pill Badges */}
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            {snomedCode && (
              <span className="px-2 py-0.5 rounded-[6px] bg-[#eff6ff] text-[#1d4ed8] border border-[#bfdbfe] text-[10px] font-mono font-semibold flex items-center gap-1">
                <span className="font-bold">SNOMED:</span> {snomedCode}
              </span>
            )}

            {icd10Code && (
              <span className="px-2 py-0.5 rounded-[6px] bg-[#f3f4f6] text-[#374151] border border-[#e5e7eb] text-[10px] font-mono font-semibold flex items-center gap-1">
                <span className="font-bold">ICD-10:</span> {icd10Code}
              </span>
            )}

            {condition.verification_status && (
              <span className="px-2 py-0.5 rounded-[6px] bg-[#f8f9fa] text-[#4b5563] border border-[#e5e7eb] text-[10px] font-medium flex items-center gap-1 capitalize">
                <ShieldCheck className="h-3 w-3 text-[#10b981]" />
                {condition.verification_status}
              </span>
            )}
          </div>
        </div>

        {/* Status & Severity Pill Clusters */}
        <div className="flex sm:flex-col items-end gap-1.5 shrink-0">
          <Badge variant={statusConfig.variant} size="sm" dot>
            {statusConfig.label}
          </Badge>
          <Badge variant={severityConfig.variant} size="sm">
            {severityConfig.label}
          </Badge>
        </div>
      </div>

      {/* 2. Patient Guidance & Self-Care Context */}
      <div className="p-3.5 rounded-[10px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-2 text-xs">
        <div className="text-[#374151] leading-relaxed">
          {mapping?.patientSummary || (
            condition.note ? condition.note : "Active diagnosed condition being monitored by the clinical team."
          )}
        </div>

        {/* Lifestyle Guidance Bullets if mapped */}
        {mapping?.lifestyleAdvice && mapping.lifestyleAdvice.length > 0 && (
          <div className="pt-2 border-t border-[#e5e7eb] space-y-1">
            <span className="text-[10px] uppercase font-bold tracking-wider text-[#6b7280] flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-[#d97706]" />
              Lifestyle & Self-Care Guidance:
            </span>
            <ul className="space-y-0.5 text-[#4b5563] pl-1">
              {mapping.lifestyleAdvice.map((advice, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#10b981] shrink-0 mt-0.5" />
                  <span>{advice}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Target Monitoring Goal */}
        {mapping?.monitoringGoal && (
          <div className="pt-1.5 flex items-center justify-between text-[11px] text-[#4b5563] bg-white p-2 rounded-[6px] border border-[#e5e7eb]">
            <span className="text-[#6b7280]">Clinical Monitoring Target:</span>
            <span className="font-semibold text-[#111111]">{mapping.monitoringGoal}</span>
          </div>
        )}
      </div>

      {/* 3. Clinician Clinical Notes & Attribution */}
      {condition.note && condition.note !== mapping?.patientSummary && (
        <div className="text-xs text-[#4b5563] bg-[#fafafa] p-2.5 rounded-[8px] border border-[#f3f4f6] flex items-start gap-2">
          <Info className="h-4 w-4 text-[#3b82f6] shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-[#111111]">Clinical Documentation Note: </span>
            <span>{condition.note}</span>
          </div>
        </div>
      )}

      {/* 4. Action Controls Footer */}
      <div className="pt-1 flex flex-wrap items-center justify-between gap-2 border-t border-[#f3f4f6]">
        <div className="text-[11px] text-[#6b7280] flex items-center gap-1.5">
          <Stethoscope className="h-3.5 w-3.5 text-[#6b7280]" />
          <span>
            Specialty: <strong>{mapping?.recommendedSpecialist || "Internal Medicine"}</strong>
          </span>
        </div>

        <div className="flex items-center gap-2">
          {onViewFhir && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onViewFhir(condition)}
              className="text-xs font-medium flex items-center gap-1.5 text-[#374151]"
            >
              <FileCode className="h-3.5 w-3.5 text-[#6b7280]" />
              <span>FHIR Condition</span>
            </Button>
          )}

          {onOpenUpdateModal && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onOpenUpdateModal(condition)}
              className="text-xs font-medium flex items-center gap-1.5 text-[#111111] hover:bg-[#f3f4f6]"
            >
              <HeartPulse className="h-3.5 w-3.5 text-[#10b981]" />
              <span>Log Symptom Update</span>
            </Button>
          )}
        </div>
      </div>

    </div>
  );
}
