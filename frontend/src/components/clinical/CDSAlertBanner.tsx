"use client";

import React, { useState } from "react";
import { Badge, Button } from "@/components/ui";
import type { SafetyAlert, CDSSeverity } from "@/lib/api";
import {
  ShieldAlert,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Lock,
  ArrowRight,
  Stethoscope,
  X,
} from "lucide-react";

export interface CDSAlertBannerProps {
  alerts: SafetyAlert[];
  hasCriticalAlerts: boolean;
  requiresOverride: boolean;
  onOverride?: (reason: string) => void;
  onDismiss?: () => void;
  isOverridden?: boolean;
  overrideReason?: string;
  className?: string;
}

const COMMON_OVERRIDE_REASONS = [
  "Therapeutic clinical benefit outweighs potential interaction risk",
  "Patient under continuous intensive hemodynamic/laboratory monitoring",
  "Dosage and timing separated to prevent pharmacokinetic interaction",
  "Alternative non-interacting therapeutic options exhausted",
  "Specialist multidisciplinary consultation completed and documented",
];

export const CDSAlertBanner: React.FC<CDSAlertBannerProps> = ({
  alerts,
  hasCriticalAlerts,
  requiresOverride,
  onOverride,
  onDismiss,
  isOverridden = false,
  overrideReason = "",
  className = "",
}) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);
  const [overrideInput, setOverrideInput] = useState<string>("");
  const [selectedPresetReason, setSelectedPresetReason] = useState<string>("");
  const [showOverrideForm, setShowOverrideForm] = useState<boolean>(false);

  if (!alerts || alerts.length === 0) {
    return null;
  }

  const toggleExpand = (index: number) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  const handleConfirmOverride = () => {
    const finalReason =
      overrideInput.trim() || selectedPresetReason || "Clinician override verified";
    if (onOverride) {
      onOverride(finalReason);
    }
    setShowOverrideForm(false);
  };

  // Severity styling tokens aligned with Cal.com clean design
  const bannerTone = hasCriticalAlerts
    ? {
        border: "border-red-200",
        bg: "bg-red-50/50",
        headerBg: "bg-red-100/60",
        text: "text-red-950",
        icon: <ShieldAlert className="w-5 h-5 text-red-600 flex-shrink-0" />,
        badgeVariant: "critical" as const,
        title: "Critical Safety Warning: Severe Contraindication Intercepted",
      }
    : requiresOverride
    ? {
        border: "border-amber-200",
        bg: "bg-amber-50/50",
        headerBg: "bg-amber-100/60",
        text: "text-amber-950",
        icon: <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />,
        badgeVariant: "warning" as const,
        title: "Clinical Safety Precaution: Potential Interaction Detected",
      }
    : {
        border: "border-blue-200",
        bg: "bg-blue-50/50",
        headerBg: "bg-blue-100/60",
        text: "text-blue-950",
        icon: <Info className="w-5 h-5 text-blue-600 flex-shrink-0" />,
        badgeVariant: "neutral" as const,
        title: "Clinical Decision Support Advisory",
      };

  return (
    <div
      className={`rounded-xl border ${bannerTone.border} ${bannerTone.bg} overflow-hidden shadow-xs transition-all duration-200 ${className}`}
    >
      {/* Banner Header */}
      <div
        className={`px-4 py-3 border-b ${bannerTone.border} flex items-center justify-between gap-3`}
      >
        <div className="flex items-center gap-2.5">
          {bannerTone.icon}
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-sm font-semibold tracking-tight ${bannerTone.text}`}>
                {bannerTone.title}
              </span>
              <Badge variant={bannerTone.badgeVariant} className="text-[10px] px-1.5 py-0 uppercase">
                {hasCriticalAlerts ? "Critical" : requiresOverride ? "Major Risk" : "Advisory"}
              </Badge>
            </div>
            <p className="text-xs text-neutral-600 mt-0.5">
              {alerts.length} safety {alerts.length === 1 ? "rule" : "rules"} triggered by current
              prescription formulation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isOverridden && (
            <Badge variant="outline" className="bg-emerald-50 text-emerald-800 border-emerald-200 text-xs gap-1 py-0.5">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              Override Certified
            </Badge>
          )}

          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-neutral-400 hover:text-neutral-700 p-1 rounded-md transition-colors"
              title="Dismiss warning"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Alert Items List */}
      <div className="divide-y divide-neutral-200/60 bg-white/70">
        {alerts.map((alert, idx) => {
          const isExpanded = expandedIndex === idx;
          const severityBadgeColor =
            alert.severity === "critical"
              ? "bg-red-100 text-red-800 border-red-200"
              : alert.severity === "major"
              ? "bg-amber-100 text-amber-800 border-amber-200"
              : "bg-blue-100 text-blue-800 border-blue-200";

          const typeDisplay =
            alert.alert_type === "drug-drug"
              ? "Drug-Drug Interaction"
              : alert.alert_type === "drug-allergy"
              ? "Allergy Cross-Reactivity"
              : "Condition Contraindication";

          return (
            <div key={`${alert.rule_id}-${idx}`} className="p-3.5">
              <div
                className="flex items-start justify-between gap-3 cursor-pointer select-none"
                onClick={() => toggleExpand(idx)}
              >
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-1.5 mb-1">
                    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border uppercase font-medium ${severityBadgeColor}`}>
                      {alert.severity}
                    </span>
                    <span className="text-[10px] bg-neutral-100 text-neutral-700 px-1.5 py-0.5 rounded font-mono">
                      {alert.rule_id}
                    </span>
                    <span className="text-xs text-neutral-500">• {typeDisplay}</span>
                  </div>

                  <h4 className="text-xs font-semibold text-neutral-900 leading-snug">
                    {alert.title}
                  </h4>

                  <div className="text-xs text-neutral-600 mt-0.5 flex items-center gap-1">
                    <span className="font-medium text-neutral-700">Offending Entity:</span>
                    <span className="font-mono text-neutral-900 bg-neutral-100 px-1 rounded text-[11px]">
                      {alert.offending_entity}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  className="text-neutral-400 hover:text-neutral-700 p-1"
                  aria-label="Toggle details"
                >
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </button>
              </div>

              {/* Collapsible Clinical Rationale & Recommendations */}
              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-neutral-100 space-y-2 text-xs">
                  <div>
                    <span className="font-medium text-neutral-700 block mb-0.5">
                      Pharmacological Mechanism:
                    </span>
                    <p className="text-neutral-600 leading-relaxed bg-neutral-50 p-2.5 rounded-lg border border-neutral-200/60 font-sans">
                      {alert.mechanism}
                    </p>
                  </div>

                  <div>
                    <span className="font-medium text-emerald-800 flex items-center gap-1 mb-0.5">
                      <Stethoscope className="w-3.5 h-3.5" />
                      Actionable Clinical Guidance:
                    </span>
                    <p className="text-emerald-950 bg-emerald-50/70 p-2.5 rounded-lg border border-emerald-200/70 leading-relaxed">
                      {alert.recommendation}
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Override Governance Section */}
      {requiresOverride && (
        <div className="p-3 bg-neutral-50 border-t border-neutral-200/70">
          {isOverridden ? (
            <div className="flex items-start gap-2 bg-emerald-50/80 border border-emerald-200 rounded-lg p-2.5 text-xs text-emerald-900">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold block">Clinician Override Recorded & Signed:</span>
                <p className="text-neutral-700 italic mt-0.5">"{overrideReason}"</p>
              </div>
            </div>
          ) : showOverrideForm ? (
            <div className="bg-white border border-neutral-200 rounded-lg p-3 space-y-2.5 text-xs shadow-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-neutral-900 flex items-center gap-1">
                  <Lock className="w-3.5 h-3.5 text-amber-600" />
                  Document Clinical Override Justification
                </span>
                <button
                  type="button"
                  onClick={() => setShowOverrideForm(false)}
                  className="text-neutral-400 hover:text-neutral-700 text-xs"
                >
                  Cancel
                </button>
              </div>

              <div>
                <label className="text-neutral-600 block mb-1">Standard clinical rationale preset:</label>
                <select
                  className="w-full text-xs p-2 rounded-md border border-neutral-300 bg-white focus:outline-none focus:ring-1 focus:ring-neutral-900"
                  value={selectedPresetReason}
                  onChange={(e) => {
                    setSelectedPresetReason(e.target.value);
                    if (e.target.value) setOverrideInput(e.target.value);
                  }}
                >
                  <option value="">Select standard rationale...</option>
                  {COMMON_OVERRIDE_REASONS.map((r, i) => (
                    <option key={i} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-neutral-600 block mb-1">Prescriber clinical commentary:</label>
                <textarea
                  rows={2}
                  className="w-full text-xs p-2 rounded-md border border-neutral-300 focus:outline-none focus:ring-1 focus:ring-neutral-900 placeholder:text-neutral-400"
                  placeholder="Specify monitoring protocol, renal dosage adjustments, or multidisciplinary rationale..."
                  value={overrideInput}
                  onChange={(e) => setOverrideInput(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-2 pt-1">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowOverrideForm(false)}
                  className="h-7 text-xs"
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={handleConfirmOverride}
                  className="h-7 text-xs bg-neutral-900 text-white hover:bg-neutral-800"
                  disabled={!overrideInput.trim() && !selectedPresetReason}
                >
                  Certify Override & Proceed
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-3">
              <div className="text-xs text-neutral-600">
                <span className="font-semibold text-neutral-800">
                  {hasCriticalAlerts ? "Prescription Blocked:" : "Caution Advised:"}
                </span>{" "}
                Requires explicit clinical justification before signing or dispensing.
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowOverrideForm(true)}
                className="h-7 text-xs text-neutral-800 border-neutral-300 hover:bg-white"
              >
                Override Alert <ArrowRight className="w-3 h-3 ml-1" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
