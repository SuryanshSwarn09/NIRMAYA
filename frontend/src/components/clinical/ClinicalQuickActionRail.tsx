"use client";

import React from "react";
import { 
  FileText, 
  Pill, 
  FlaskConical, 
  Heart, 
  Activity, 
  Video, 
  Stethoscope, 
  Calendar,
  Sparkles
} from "lucide-react";

export type ClinicalTabType = 
  | "queue" 
  | "soap" 
  | "prescriptions" 
  | "diagnostics" 
  | "problems" 
  | "vitals" 
  | "medications" 
  | "slots";

interface ClinicalQuickActionRailProps {
  activeTab: ClinicalTabType;
  onChangeTab: (tab: ClinicalTabType) => void;
  onLaunchTelemedicine?: () => void;
  isTelemedicineEncounter?: boolean;
}

export function ClinicalQuickActionRail({
  activeTab,
  onChangeTab,
  onLaunchTelemedicine,
  isTelemedicineEncounter = false,
}: ClinicalQuickActionRailProps) {
  const actions: Array<{
    id: ClinicalTabType;
    label: string;
    icon: React.ReactNode;
    badge?: string;
    shortcut?: string;
  }> = [
    {
      id: "queue",
      label: "Consultation Queue",
      icon: <Calendar className="h-4 w-4" />,
      shortcut: "1",
    },
    {
      id: "soap",
      label: "SOAP Note",
      icon: <FileText className="h-4 w-4" />,
      shortcut: "2",
    },
    {
      id: "prescriptions",
      label: "e-Prescriptions",
      icon: <Pill className="h-4 w-4" />,
      badge: "DDI Guard",
      shortcut: "3",
    },
    {
      id: "diagnostics",
      label: "Lab Orders",
      icon: <FlaskConical className="h-4 w-4" />,
      shortcut: "4",
    },
    {
      id: "problems",
      label: "Problem List",
      icon: <Heart className="h-4 w-4" />,
      shortcut: "5",
    },
    {
      id: "vitals",
      label: "Vitals Telemetry",
      icon: <Activity className="h-4 w-4" />,
      shortcut: "6",
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-[#E5E7EB] p-2 flex flex-wrap items-center justify-between gap-2 shadow-xs">
      
      {/* Action pill group */}
      <div className="flex items-center gap-1.5 flex-wrap overflow-x-auto py-0.5">
        {actions.map((act) => {
          const isActive = activeTab === act.id;
          return (
            <button
              key={act.id}
              type="button"
              onClick={() => onChangeTab(act.id)}
              className={`py-2 px-3 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                isActive
                  ? "bg-[#111111] text-white shadow-xs"
                  : "bg-white text-[#4B5563] hover:text-[#111827] hover:bg-[#F9FAFB]"
              }`}
              title={`Switch to ${act.label} (Alt+${act.shortcut})`}
            >
              {act.icon}
              <span>{act.label}</span>
              {act.shortcut && (
                <kbd
                  className={`hidden md:inline-block font-mono text-[9px] px-1 py-0.5 rounded border select-none ${
                    isActive
                      ? "border-white/30 text-white/80 bg-white/10"
                      : "border-[#E5E7EB] text-[#9CA3AF] bg-[#F9FAFB]"
                  }`}
                >
                  {act.shortcut}
                </kbd>
              )}
              {act.badge && (
                <span
                  className={`text-[9px] uppercase px-1 py-0.2 rounded font-bold ${
                    isActive ? "bg-white/20 text-white" : "bg-[#ECFDF5] text-[#059669]"
                  }`}
                >
                  {act.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Right: Telemedicine Launch Trigger */}
      {isTelemedicineEncounter && onLaunchTelemedicine && (
        <button
          type="button"
          onClick={onLaunchTelemedicine}
          className="py-2 px-3.5 rounded-lg border border-[#2563EB] bg-[#2563EB] text-white text-xs font-semibold hover:bg-[#1D4ED8] transition-all flex items-center gap-1.5 cursor-pointer shadow-xs whitespace-nowrap self-stretch sm:self-auto justify-center"
        >
          <Video className="h-4 w-4" />
          <span>Launch Teleconsult Video</span>
        </button>
      )}
    </div>
  );
}
