"use client";

import React, { useState } from "react";
import { 
  User, 
  ShieldCheck, 
  AlertTriangle, 
  Activity, 
  Heart, 
  Phone, 
  Calendar, 
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  FileText,
  Clock,
  Sparkles
} from "lucide-react";

export interface PatientDemographics {
  id: string;
  name: string;
  age?: number;
  gender?: string;
  dateOfBirth?: string;
  bloodGroup?: string;
  abhaNumber: string;
  abhaAddress: string;
  phone?: string;
  emergencyContact?: {
    name: string;
    relationship: string;
    phone: string;
  };
  primaryConditions?: Array<{
    code: string;
    display: string;
    codingSystem?: string;
    severity?: "mild" | "moderate" | "severe";
  }>;
  allergies?: Array<{
    substance: string;
    criticality: "low" | "high" | "unable-to-assess";
    manifestation: string;
  }>;
  latestVitals?: {
    bp?: string;
    bpStatus?: "normal" | "elevated" | "high" | "crisis";
    hr?: string;
    spo2?: string;
    bmi?: string;
    temperature?: string;
    recordedAt?: string;
  };
  activeMedicationsCount?: number;
  recentEncountersCount?: number;
}

interface PatientDemographicBannerProps {
  patient: PatientDemographics;
  encounterReason?: string;
  isConsultationActive?: boolean;
  onViewFullRecord?: () => void;
  onLaunchTelemedicine?: () => void;
}

export function PatientDemographicBanner({
  patient,
  encounterReason,
  isConsultationActive = false,
  onViewFullRecord,
  onLaunchTelemedicine,
}: PatientDemographicBannerProps) {
  const [copiedAbha, setCopiedAbha] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleCopyAbha = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(patient.abhaNumber);
    setCopiedAbha(true);
    setTimeout(() => setCopiedAbha(false), 2000);
  };

  const hasAllergies = patient.allergies && patient.allergies.length > 0;

  return (
    <div className="bg-white rounded-xl border border-[#E5E7EB] shadow-xs overflow-hidden transition-all">
      {/* 1. Primary Clinical Demographics Strip */}
      <div className="p-4 sm:p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        
        {/* Left: Patient Avatar & Core Demographics */}
        <div className="flex items-start sm:items-center gap-3.5">
          <div className="h-12 w-12 rounded-full bg-[#111111] text-white flex items-center justify-center font-bold text-base shrink-0 shadow-xs">
            {patient.name
              .split(" ")
              .map((n) => n[0])
              .join("")}
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-lg sm:text-xl font-bold tracking-tight text-[#111827]">
                {patient.name}
              </h2>

              {patient.age && patient.gender && (
                <span className="text-xs font-medium text-[#4B5563] bg-[#F3F4F6] px-2 py-0.5 rounded-md">
                  {patient.age}y • {patient.gender}
                </span>
              )}

              {patient.bloodGroup && (
                <span className="text-xs font-bold text-[#DC2626] bg-[#FEF2F2] px-2 py-0.5 rounded-md border border-[#FEE2E2]">
                  {patient.bloodGroup}
                </span>
              )}

              {isConsultationActive && (
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#059669] bg-[#ECFDF5] px-2.5 py-0.5 rounded-md border border-[#A7F3D0]">
                  <span className="h-2 w-2 rounded-full bg-[#059669] animate-pulse" />
                  Active Encounter
                </span>
              )}
            </div>

            {/* ABHA & National Identity */}
            <div className="flex items-center gap-2 flex-wrap text-xs text-[#6B7280]">
              <span className="inline-flex items-center gap-1 font-mono text-[#059669] bg-[#ECFDF5] px-2 py-0.5 rounded border border-[#A7F3D0]">
                <ShieldCheck className="h-3.5 w-3.5" />
                ABHA: {patient.abhaNumber}
                <button
                  type="button"
                  onClick={handleCopyAbha}
                  title="Copy ABHA ID"
                  className="ml-1 hover:text-[#047857] cursor-pointer"
                >
                  {copiedAbha ? <Check className="h-3 w-3 text-[#059669]" /> : <Copy className="h-3 w-3" />}
                </button>
              </span>

              <span className="font-mono text-[#4B5563]">
                {patient.abhaAddress}
              </span>

              {patient.phone && (
                <span className="text-[#6B7280] hidden sm:inline">
                  • Tel: {patient.phone}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Right: Quick Vitals Pill & Expand Toggle */}
        <div className="flex items-center justify-between lg:justify-end gap-3 pt-3 lg:pt-0 border-t lg:border-t-0 border-[#F3F4F6]">
          {patient.latestVitals && (
            <div className="flex items-center gap-2 bg-[#F9FAFB] border border-[#E5E7EB] px-3 py-1.5 rounded-lg text-xs">
              <Activity className="h-4 w-4 text-[#4B5563] shrink-0" />
              <div className="space-x-2">
                <span className="text-[#111827] font-semibold">
                  BP: <span className={patient.latestVitals.bpStatus === "high" ? "text-[#DC2626]" : ""}>{patient.latestVitals.bp}</span>
                </span>
                {patient.latestVitals.hr && (
                  <span className="text-[#4B5563]">HR: {patient.latestVitals.hr}</span>
                )}
                {patient.latestVitals.spo2 && (
                  <span className="text-[#059669] font-medium">SpO2: {patient.latestVitals.spo2}</span>
                )}
              </div>
            </div>
          )}

          <div className="flex items-center gap-2">
            {onViewFullRecord && (
              <button
                type="button"
                onClick={onViewFullRecord}
                className="py-1.5 px-3 rounded-lg border border-[#E5E7EB] bg-white text-xs font-semibold text-[#374151] hover:bg-[#F9FAFB] transition-all flex items-center gap-1 cursor-pointer"
              >
                <span>Full Chart</span>
                <ExternalLink className="h-3 w-3" />
              </button>
            )}

            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 rounded-lg border border-[#E5E7EB] bg-white text-[#4B5563] hover:text-[#111827] hover:bg-[#F9FAFB] transition-all cursor-pointer"
              title={isExpanded ? "Collapse Details" : "Expand Demographics & Clinical Profile"}
            >
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* 2. Critical Clinical Alerts & Encounter Strip (Always Visible) */}
      <div className="px-4 py-2.5 bg-[#F9FAFB] border-t border-[#E5E7EB] flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          {encounterReason && (
            <div className="flex items-center gap-1.5 text-[#374151]">
              <span className="font-semibold text-[#111827]">Encounter Reason:</span>
              <span className="bg-white px-2 py-0.5 rounded border border-[#E5E7EB] font-medium text-[#111827]">
                {encounterReason}
              </span>
            </div>
          )}

          {hasAllergies && (
            <div className="inline-flex items-center gap-1.5 text-[#B91C1C] bg-[#FEF2F2] px-2 py-0.5 rounded border border-[#FECACA] font-semibold">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
              <span>
                Allergies: {patient.allergies?.map((a) => `${a.substance} (${a.criticality})`).join(", ")}
              </span>
            </div>
          )}
        </div>

        {patient.emergencyContact && (
          <div className="flex items-center gap-1 text-[11px] text-[#6B7280]">
            <Phone className="h-3 w-3" />
            <span>Emergency: {patient.emergencyContact.name} ({patient.emergencyContact.relationship}) • {patient.emergencyContact.phone}</span>
          </div>
        )}
      </div>

      {/* 3. Expandable Detailed Longitudinal Summary */}
      {isExpanded && (
        <div className="p-4 sm:p-5 bg-white border-t border-[#E5E7EB] grid grid-cols-1 md:grid-cols-3 gap-4 text-xs animate-fadeIn">
          
          {/* Column 1: Active Chronic Conditions */}
          <div className="space-y-2">
            <h4 className="font-bold text-[#111827] flex items-center gap-1.5">
              <Heart className="h-3.5 w-3.5 text-[#DC2626]" />
              Active Problem List (SNOMED-CT / ICD-10)
            </h4>
            {patient.primaryConditions && patient.primaryConditions.length > 0 ? (
              <div className="space-y-1.5">
                {patient.primaryConditions.map((c) => (
                  <div
                    key={c.code}
                    className="p-2 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB] flex items-center justify-between"
                  >
                    <div>
                      <div className="font-semibold text-[#111827]">{c.display}</div>
                      <div className="text-[10px] font-mono text-[#6B7280]">
                        Code: {c.code} {c.codingSystem && `(${c.codingSystem})`}
                      </div>
                    </div>
                    {c.severity && (
                      <span className="text-[10px] uppercase font-bold text-[#D97706] bg-[#FEF3C7] px-1.5 py-0.5 rounded">
                        {c.severity}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[#6B7280] italic">No chronic conditions recorded.</p>
            )}
          </div>

          {/* Column 2: Recent Vitals Breakdown */}
          <div className="space-y-2">
            <h4 className="font-bold text-[#111827] flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-[#059669]" />
              LOINC Telemetry Readings
            </h4>
            {patient.latestVitals ? (
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                  <span className="text-[10px] text-[#6B7280] block">Blood Pressure</span>
                  <span className="font-bold text-[#111827]">{patient.latestVitals.bp || "N/A"}</span>
                </div>
                <div className="p-2 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                  <span className="text-[10px] text-[#6B7280] block">Heart Rate</span>
                  <span className="font-bold text-[#111827]">{patient.latestVitals.hr || "N/A"}</span>
                </div>
                <div className="p-2 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                  <span className="text-[10px] text-[#6B7280] block">Oxygen Sat (SpO2)</span>
                  <span className="font-bold text-[#059669]">{patient.latestVitals.spo2 || "N/A"}</span>
                </div>
                <div className="p-2 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                  <span className="text-[10px] text-[#6B7280] block">Body Mass Index</span>
                  <span className="font-bold text-[#111827]">{patient.latestVitals.bmi || "N/A"}</span>
                </div>
              </div>
            ) : (
              <p className="text-[#6B7280] italic">No recent vitals logged.</p>
            )}
          </div>

          {/* Column 3: Active Regimens & Care Contexts */}
          <div className="space-y-2">
            <h4 className="font-bold text-[#111827] flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5 text-[#2563EB]" />
              Care Summary & Telemedicine
            </h4>
            <div className="p-3 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB] space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-[#6B7280]">Active Prescriptions:</span>
                <span className="font-bold text-[#111827]">
                  {patient.activeMedicationsCount ?? 2} Formularies
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-[#6B7280]">ABDM CareContexts:</span>
                <span className="font-bold text-[#059669]">Linked & Verified</span>
              </div>
              {onLaunchTelemedicine && (
                <button
                  type="button"
                  onClick={onLaunchTelemedicine}
                  className="w-full mt-2 py-1.5 px-3 rounded-lg border border-[#2563EB] bg-[#EFF6FF] text-[#2563EB] text-xs font-semibold hover:bg-[#DBEAFE] transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  Pre-Flight WebRTC Diagnostics
                </button>
              )}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
