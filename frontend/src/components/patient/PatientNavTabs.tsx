"use client";

import React from "react";
import { NavPillGroup, NavPillItem } from "@/components/ui";
import { LayoutDashboard, Pill, Stethoscope, ShieldCheck, Calendar } from "lucide-react";

export type PatientTabId = "overview" | "prescriptions" | "problems" | "records" | "book";

export interface PatientNavTabsProps {
  activeTab: PatientTabId;
  onTabChange: (tab: PatientTabId) => void;
  prescriptionsBadgeCount?: number;
  conditionsBadgeCount?: number;
}

export function PatientNavTabs({
  activeTab,
  onTabChange,
  prescriptionsBadgeCount,
  conditionsBadgeCount,
}: PatientNavTabsProps) {
  const items: NavPillItem[] = [
    {
      id: "overview",
      label: "Overview",
      icon: <LayoutDashboard className="h-4 w-4" />,
    },
    {
      id: "prescriptions",
      label: "Prescriptions & Rx",
      icon: <Pill className="h-4 w-4" />,
      badge: prescriptionsBadgeCount && prescriptionsBadgeCount > 0 ? String(prescriptionsBadgeCount) : undefined,
    },
    {
      id: "problems",
      label: "Problem List & Conditions",
      icon: <Stethoscope className="h-4 w-4" />,
      badge: conditionsBadgeCount && conditionsBadgeCount > 0 ? String(conditionsBadgeCount) : undefined,
    },
    {
      id: "records",
      label: "Health Records & Labs",
      icon: <ShieldCheck className="h-4 w-4" />,
    },
    {
      id: "book",
      label: "Schedule Consultation",
      icon: <Calendar className="h-4 w-4" />,
    },
  ];

  return (
    <div className="flex justify-start overflow-x-auto pb-1">
      <NavPillGroup
        items={items}
        activeId={activeTab}
        onChange={(id) => onTabChange(id as PatientTabId)}
      />
    </div>
  );
}
