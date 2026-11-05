"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  Baby,
  Check,
  ChevronDown,
  HeartHandshake,
  Lock,
  ShieldCheck,
  User,
  Users,
} from "lucide-react";

export type ContextType = "SELF" | "PEDIATRIC_MINOR" | "GERIATRIC_SENIOR";

export interface DependentContext {
  id: string;
  name: string;
  abha: string;
  type: ContextType;
  age: number;
  gender: string;
  relationship: string;
  scope: string;
}

export const SEEDED_CONTEXTS: DependentContext[] = [
  {
    id: "pat-priya-sharma-01",
    name: "Dr. Priya Sharma (Self)",
    abha: "91-8472-1092-4821",
    type: "SELF",
    age: 38,
    gender: "Female",
    relationship: "Self (Primary Account)",
    scope: "FULL_MANAGEMENT",
  },
  {
    id: "pat-aarav-sharma-02",
    name: "Aarav Sharma",
    abha: "14-8291-0391-4821",
    type: "PEDIATRIC_MINOR",
    age: 8,
    gender: "Male",
    relationship: "Son (Child Minor)",
    scope: "FULL_MANAGEMENT",
  },
  {
    id: "pat-kavita-sharma-03",
    name: "Kavita Sharma",
    abha: "14-9102-4819-2041",
    type: "GERIATRIC_SENIOR",
    age: 68,
    gender: "Female",
    relationship: "Mother (Senior Dependent)",
    scope: "FULL_MANAGEMENT",
  },
];

interface CalcomDependentSwitcherProps {
  activeContextId: string;
  onContextChange: (context: DependentContext) => void;
}

export function CalcomDependentSwitcher({
  activeContextId,
  onContextChange,
}: CalcomDependentSwitcherProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const activeContext =
    SEEDED_CONTEXTS.find((c) => c.id === activeContextId) || SEEDED_CONTEXTS[0];

  const handleSelect = (ctx: DependentContext) => {
    onContextChange(ctx);
    setDropdownOpen(false);
  };

  const getPersonaBadge = (type: ContextType) => {
    switch (type) {
      case "PEDIATRIC_MINOR":
        return <Badge variant="neutral">PEDIATRIC</Badge>;
      case "GERIATRIC_SENIOR":
        return <Badge variant="warning">GERIATRIC</Badge>;
      default:
        return <Badge variant="verified">PERSONAL</Badge>;
    }
  };

  const getPersonaIcon = (type: ContextType) => {
    switch (type) {
      case "PEDIATRIC_MINOR":
        return <Baby className="w-4 h-4 text-[#111111]" />;
      case "GERIATRIC_SENIOR":
        return <HeartHandshake className="w-4 h-4 text-[#111111]" />;
      default:
        return <User className="w-4 h-4 text-[#111111]" />;
    }
  };

  return (
    <div className="relative font-sans">
      <div className="p-4 bg-white border border-[#e5e7eb] rounded-xl shadow-none flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Active Context Information */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] flex items-center justify-center shrink-0">
            {getPersonaIcon(activeContext.type)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#6b7280]">Active Clinical Persona:</span>
              <span className="text-sm font-semibold text-[#111111]">
                {activeContext.name}
              </span>
              {getPersonaBadge(activeContext.type)}
              <Badge variant="verified">DPDP SEC 9</Badge>
            </div>
            <div className="flex items-center gap-2 mt-0.5 text-xs text-[#6b7280]">
              <span className="font-mono">{activeContext.abha}</span>
              <span>•</span>
              <span>
                {activeContext.age} years ({activeContext.gender})
              </span>
              <span>•</span>
              <span>{activeContext.relationship}</span>
            </div>
          </div>
        </div>

        {/* Switcher Dropdown Action */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="text-xs border-[#e5e7eb] bg-[#f9fafb] text-[#111111] hover:bg-white flex items-center gap-2"
            >
              <Users className="w-3.5 h-3.5 text-[#111111]" />
              <span>Switch Dependent</span>
              <ChevronDown className="w-3.5 h-3.5 text-[#6b7280]" />
            </Button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-72 bg-white border border-[#e5e7eb] rounded-xl shadow-lg z-50 p-1.5 space-y-1">
                <div className="px-2.5 py-1.5 text-[11px] font-semibold text-[#6b7280] uppercase tracking-wider">
                  Select Family Account
                </div>
                {SEEDED_CONTEXTS.map((ctx) => (
                  <button
                    key={ctx.id}
                    onClick={() => handleSelect(ctx)}
                    className={`w-full text-left p-2.5 rounded-lg flex items-center justify-between text-xs transition-colors ${
                      ctx.id === activeContext.id
                        ? "bg-[#f9fafb] text-[#111111] font-medium border border-[#e5e7eb]"
                        : "text-[#374151] hover:bg-[#f9fafb] border border-transparent"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-md bg-white border border-[#e5e7eb] flex items-center justify-center shrink-0">
                        {getPersonaIcon(ctx.type)}
                      </div>
                      <div>
                        <div className="font-semibold text-[#111111] leading-tight">
                          {ctx.name}
                        </div>
                        <div className="text-[11px] text-[#6b7280] mt-0.5">
                          {ctx.relationship}
                        </div>
                      </div>
                    </div>
                    {ctx.id === activeContext.id && (
                      <Check className="w-4 h-4 text-[#111111]" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Zero Contamination Assurance Callout */}
      {activeContext.type !== "SELF" && (
        <div className="mt-2 px-3 py-1.5 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] flex items-center justify-between text-[11px] text-[#6b7280]">
          <div className="flex items-center gap-1.5">
            <Lock className="w-3 h-3 text-[#111111]" />
            <span>
              Zero-Contamination Boundary Active: Viewing sovereign records for{" "}
              <strong className="text-[#111111]">{activeContext.name}</strong>. No clinical notes or vitals will bleed into your adult profile.
            </span>
          </div>
          <Badge variant="abdm" size="sm">
            NRCeS Isolated
          </Badge>
        </div>
      )}
    </div>
  );
}
