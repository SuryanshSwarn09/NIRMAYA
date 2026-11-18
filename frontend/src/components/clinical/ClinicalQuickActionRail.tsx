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
      label: "Diagnostics & PACS",
      icon: <FlaskConical className="h-4 w-4" />,
      badge: "PACS",
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
    <div className="p-2 flex flex-wrap items-center justify-between gap-2 border border-[#d1d5db] bg-white rounded-xl shadow-xs">
      
      {/* Action pill group (Cal.com & Sovereign Standard) */}
      <div className="flex items-center gap-1.5 flex-wrap overflow-x-auto py-0.5">
        {actions.map((act) => {
          const isActive = activeTab === act.id;
          return (
            <button
              key={act.id}
              type="button"
              onClick={() => onChangeTab(act.id)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                isActive
                  ? "bg-[#0b4d8c] text-white shadow-xs"
                  : "bg-[#f8fafc] text-[#4b5563] hover:text-[#0b4d8c] hover:bg-[#f0f6ff] border border-[#e5e7eb]"
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
                      : "border-gray-200 text-gray-500 bg-gray-50"
                  }`}
                >
                  {act.shortcut}
                </kbd>
              )}
              {act.badge && (
                <span
                  className={`text-[9px] px-1.5 py-0.2 rounded font-bold ${
                    isActive ? "bg-white/20 text-white" : "bg-emerald-100 text-emerald-800 border border-emerald-200"
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
          className="px-3 py-1.5 rounded-md bg-[#0b4d8c] text-white hover:bg-[#083c6f] text-xs font-semibold shadow-xs flex items-center gap-1.5 cursor-pointer whitespace-nowrap self-stretch sm:self-auto justify-center"
        >
          <Video className="h-4 w-4" />
          <span>Launch Teleconsult Video</span>
        </button>
      )}
    </div>
  );
}
