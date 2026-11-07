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
    <div className="ux4g-card p-2 flex flex-wrap items-center justify-between gap-2 border border-[var(--ux4g-border)] bg-white rounded-xl shadow-xs">
      
      {/* Action pill group (UX4G Standard) */}
      <div className="flex items-center gap-1.5 flex-wrap overflow-x-auto py-0.5">
        {actions.map((act) => {
          const isActive = activeTab === act.id;
          return (
            <button
              key={act.id}
              type="button"
              onClick={() => onChangeTab(act.id)}
              className={`ux4g-btn ux4g-btn-s ${
                isActive
                  ? "ux4g-btn-primary"
                  : "ux4g-btn-secondary"
              } flex items-center gap-1.5 cursor-pointer whitespace-nowrap`}
              title={`Switch to ${act.label} (Alt+${act.shortcut})`}
            >
              {act.icon}
              <span>{act.label}</span>
              {act.shortcut && (
                <kbd
                  className={`hidden md:inline-block font-mono text-[9px] px-1 py-0.5 rounded border select-none ${
                    isActive
                      ? "border-white/30 text-white/80 bg-white/10"
                      : "border-[var(--ux4g-border)] text-[var(--ux4g-text-secondary)] bg-[var(--ux4g-surface-ground)]"
                  }`}
                >
                  {act.shortcut}
                </kbd>
              )}
              {act.badge && (
                <span
                  className={`ux4g-badge ${
                    isActive ? "ux4g-badge-neutral bg-white/20 text-white" : "ux4g-badge-success"
                  } text-[9px] px-1 py-0.2 rounded font-bold`}
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
          className="ux4g-btn ux4g-btn-primary ux4g-btn-s flex items-center gap-1.5 cursor-pointer whitespace-nowrap self-stretch sm:self-auto justify-center"
        >
          <Video className="h-4 w-4" />
          <span>Launch Teleconsult Video</span>
        </button>
      )}
    </div>
  );
}
