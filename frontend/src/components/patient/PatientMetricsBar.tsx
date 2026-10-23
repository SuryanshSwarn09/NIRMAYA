"use client";

import React from "react";
import { Pill, Calendar, Stethoscope, Activity, ArrowUpRight } from "lucide-react";
import { Badge } from "@/components/ui";

export interface PatientMetricsBarProps {
  activePrescriptionsCount: number;
  upcomingAppointmentsCount: number;
  conditionsCount: number;
  latestBpText?: string;
  latestSpo2Text?: string;
  latestVitalsStatus?: "normal" | "abnormal";
  onSelectTab: (tab: "overview" | "prescriptions" | "problems" | "records" | "book") => void;
  onOpenLogVitals?: () => void;
}

export function PatientMetricsBar({
  activePrescriptionsCount,
  upcomingAppointmentsCount,
  conditionsCount,
  latestBpText = "134/86 mmHg",
  latestSpo2Text = "98%",
  latestVitalsStatus = "abnormal",
  onSelectTab,
  onOpenLogVitals,
}: PatientMetricsBarProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
      {/* 1. Active Prescriptions */}
      <div
        onClick={() => onSelectTab("prescriptions")}
        className="group p-4 rounded-[12px] border border-[#e5e7eb] bg-[#f8f9fa] hover:bg-white hover:border-[#111111] hover:shadow-sm transition-all duration-150 cursor-pointer flex flex-col justify-between"
      >
        <div className="flex items-center justify-between">
          <div className="h-8 w-8 rounded-[8px] bg-white border border-[#e5e7eb] flex items-center justify-center text-[#111111] group-hover:scale-105 transition-transform">
            <Pill className="h-4 w-4" />
          </div>
          <ArrowUpRight className="h-4 w-4 text-[#9ca3af] group-hover:text-[#111111] transition-colors" />
        </div>
        <div className="mt-3">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-[#111111]">
              {activePrescriptionsCount}
            </span>
            <Badge variant="emerald" size="sm">Active</Badge>
          </div>
          <p className="text-xs font-semibold text-[#111111] mt-0.5">e-Prescriptions</p>
          <p className="text-[11px] text-[#6b7280]">Pharmacy dispense tracking</p>
        </div>
      </div>

      {/* 2. Upcoming Visits */}
      <div
        onClick={() => onSelectTab("book")}
        className="group p-4 rounded-[12px] border border-[#e5e7eb] bg-[#f8f9fa] hover:bg-white hover:border-[#111111] hover:shadow-sm transition-all duration-150 cursor-pointer flex flex-col justify-between"
      >
        <div className="flex items-center justify-between">
          <div className="h-8 w-8 rounded-[8px] bg-white border border-[#e5e7eb] flex items-center justify-center text-[#111111] group-hover:scale-105 transition-transform">
            <Calendar className="h-4 w-4" />
          </div>
          <ArrowUpRight className="h-4 w-4 text-[#9ca3af] group-hover:text-[#111111] transition-colors" />
        </div>
        <div className="mt-3">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-[#111111]">
              {upcomingAppointmentsCount}
            </span>
            <Badge variant="verified" size="sm">Confirmed</Badge>
          </div>
          <p className="text-xs font-semibold text-[#111111] mt-0.5">Scheduled Visits</p>
          <p className="text-[11px] text-[#6b7280]">Clinical consultations</p>
        </div>
      </div>

      {/* 3. Problem List & Conditions */}
      <div
        onClick={() => onSelectTab("problems")}
        className="group p-4 rounded-[12px] border border-[#e5e7eb] bg-[#f8f9fa] hover:bg-white hover:border-[#111111] hover:shadow-sm transition-all duration-150 cursor-pointer flex flex-col justify-between"
      >
        <div className="flex items-center justify-between">
          <div className="h-8 w-8 rounded-[8px] bg-white border border-[#e5e7eb] flex items-center justify-center text-[#111111] group-hover:scale-105 transition-transform">
            <Stethoscope className="h-4 w-4" />
          </div>
          <ArrowUpRight className="h-4 w-4 text-[#9ca3af] group-hover:text-[#111111] transition-colors" />
        </div>
        <div className="mt-3">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-[#111111]">
              {conditionsCount}
            </span>
            <Badge variant="outline" size="sm">SNOMED-CT</Badge>
          </div>
          <p className="text-xs font-semibold text-[#111111] mt-0.5">Active Conditions</p>
          <p className="text-[11px] text-[#6b7280]">Longitudinal health record</p>
        </div>
      </div>

      {/* 4. Latest Vitals Telemetry */}
      <div
        onClick={() => {
          if (onOpenLogVitals) onOpenLogVitals();
          else onSelectTab("records");
        }}
        className="group p-4 rounded-[12px] border border-[#e5e7eb] bg-[#f8f9fa] hover:bg-white hover:border-[#111111] hover:shadow-sm transition-all duration-150 cursor-pointer flex flex-col justify-between"
      >
        <div className="flex items-center justify-between">
          <div className="h-8 w-8 rounded-[8px] bg-white border border-[#e5e7eb] flex items-center justify-center text-[#111111] group-hover:scale-105 transition-transform">
            <Activity className="h-4 w-4" />
          </div>
          <span className="text-[11px] font-medium text-[#2563eb] hover:underline">
            + Log Vital
          </span>
        </div>
        <div className="mt-3">
          <div className="flex items-baseline gap-2">
            <span className="text-base font-bold tracking-tight text-[#111111]">
              {latestBpText}
            </span>
            <Badge
              variant={latestVitalsStatus === "normal" ? "emerald" : "warning"}
              size="sm"
            >
              {latestVitalsStatus === "normal" ? "Normal" : "Review"}
            </Badge>
          </div>
          <p className="text-xs font-semibold text-[#111111] mt-0.5">Latest Vitals</p>
          <p className="text-[11px] text-[#6b7280]">{latestSpo2Text} SpO2 • Self-monitored</p>
        </div>
      </div>
    </div>
  );
}
