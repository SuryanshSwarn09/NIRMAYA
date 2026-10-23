"use client";

import React, { useState, useEffect } from "react";
import { Button, Badge } from "@/components/ui";
import { ClinicalCondition, ConditionSeverity } from "@/lib/api";
import { findConditionTerminology } from "@/lib/conditions";
import { 
  X, 
  HeartPulse, 
  Activity, 
  AlertCircle, 
  CheckCircle2, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Sparkles,
  ShieldCheck
} from "lucide-react";

export interface PatientConditionUpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  condition: ClinicalCondition | null;
  onSubmitUpdate: (
    conditionId: string, 
    updateData: {
      severity: ConditionSeverity;
      trend: "improved" | "stable" | "worsened";
      patientNote: string;
      flagForReview: boolean;
    }
  ) => Promise<void> | void;
}

export function PatientConditionUpdateModal({
  isOpen,
  onClose,
  condition,
  onSubmitUpdate,
}: PatientConditionUpdateModalProps) {
  const [severity, setSeverity] = useState<ConditionSeverity>("moderate");
  const [trend, setTrend] = useState<"improved" | "stable" | "worsened">("stable");
  const [patientNote, setPatientNote] = useState("");
  const [flagForReview, setFlagForReview] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (condition) {
      setSeverity(condition.severity || "moderate");
      setTrend("stable");
      setPatientNote("");
      setFlagForReview(false);
      setErrorMsg(null);
    }
  }, [condition]);

  if (!isOpen || !condition) return null;

  const mapping = findConditionTerminology(condition.code_value) || findConditionTerminology(condition.code_display);
  const conditionTitle = mapping?.commonName || condition.code_display;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientNote.trim()) {
      setErrorMsg("Please provide a brief note describing your current symptoms or observations.");
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    try {
      await onSubmitUpdate(condition.id, {
        severity,
        trend,
        patientNote: patientNote.trim(),
        flagForReview,
      });
      onClose();
    } catch (err: any) {
      console.error("Failed to submit condition update", err);
      setErrorMsg(err.message || "Failed to record symptom update. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in overflow-y-auto">
      <div className="bg-white rounded-[16px] border border-[#e5e7eb] shadow-2xl max-w-lg w-full p-6 space-y-5 animate-scale-in my-8">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-full bg-[#f8f9fa] border border-[#e5e7eb] flex items-center justify-center">
              <HeartPulse className="h-4 w-4 text-[#10b981]" />
            </div>
            <div>
              <h3 className="text-base sm:text-lg font-bold text-[#111111] tracking-tight">
                Log Symptom Progress
              </h3>
              <p className="text-xs text-[#6b7280]">
                Record self-reported observations for your longitudinal health record.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[#9ca3af] hover:text-[#111111] transition-colors p-1"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Condition Summary Context Badge */}
        <div className="p-3 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold tracking-wider text-[#6b7280] block">
              Active Health Condition
            </span>
            <span className="text-sm font-bold text-[#111111]">
              {conditionTitle}
            </span>
          </div>
          <Badge variant="emerald" size="sm">
            {condition.code_value}
          </Badge>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          {/* 1. Perceived Severity */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#111111] block">
              Current Severity Assessment
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(["mild", "moderate", "severe"] as ConditionSeverity[]).map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => setSeverity(lvl)}
                  className={`py-2 px-3 rounded-[8px] border text-xs font-semibold capitalize transition-all ${
                    severity === lvl
                      ? lvl === "severe"
                        ? "bg-[#fef2f2] border-[#ef4444] text-[#991b1b]"
                        : lvl === "moderate"
                        ? "bg-[#fff7ed] border-[#f59e0b] text-[#9a3412]"
                        : "bg-[#ecfdf5] border-[#10b981] text-[#065f46]"
                      : "bg-white border-[#e5e7eb] text-[#4b5563] hover:bg-[#f8f9fa]"
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>
          </div>

          {/* 2. Symptom Trend */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#111111] block">
              Symptom Trend (Past 7–14 Days)
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: "improved", label: "Improved", icon: TrendingDown, color: "text-[#10b981]" },
                { id: "stable", label: "Stable / Same", icon: Minus, color: "text-[#3b82f6]" },
                { id: "worsened", label: "Worsening", icon: TrendingUp, color: "text-[#ef4444]" },
              ].map((t) => {
                const Icon = t.icon;
                const isSelected = trend === t.id;
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setTrend(t.id as any)}
                    className={`py-2 px-3 rounded-[8px] border text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                      isSelected
                        ? "bg-[#111111] text-white border-[#111111]"
                        : "bg-white border-[#e5e7eb] text-[#4b5563] hover:bg-[#f8f9fa]"
                    }`}
                  >
                    <Icon className={`h-3.5 w-3.5 ${isSelected ? "text-white" : t.color}`} />
                    <span>{t.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 3. Patient Observation Note */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#111111] block">
              Symptom Details & Biometric Telemetry
            </label>
            <textarea
              rows={4}
              value={patientNote}
              onChange={(e) => setPatientNote(e.target.value)}
              placeholder="e.g. Morning blood pressure readings have averaged 136/88 mmHg. Taking prescribed medication with food. Occasional mild exertion fatigue."
              className="w-full p-3 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] text-xs text-[#111111] focus:outline-hidden focus:ring-2 focus:ring-[#111111]"
            />
          </div>

          {/* 4. Clinician Flag */}
          <div className="flex items-center gap-2.5 pt-1">
            <input
              type="checkbox"
              id="flagForReview"
              checked={flagForReview}
              onChange={(e) => setFlagForReview(e.target.checked)}
              className="h-4 w-4 rounded-[4px] border-[#d1d5db] text-[#111111] focus:ring-[#111111]"
            />
            <label htmlFor="flagForReview" className="text-xs text-[#374151] cursor-pointer">
              Flag this symptom log for physician review during next scheduled encounter
            </label>
          </div>

          {/* Error Message */}
          {errorMsg && (
            <div className="p-3 rounded-[8px] bg-[#fef2f2] border border-[#fecaca] text-xs text-[#991b1b] flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-[#ef4444] shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-3 border-t border-[#e5e7eb]">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={submitting}
              className="flex items-center gap-1.5"
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>{submitting ? "Saving Log..." : "Save Symptom Log"}</span>
            </Button>
          </div>

        </form>

      </div>
    </div>
  );
}
