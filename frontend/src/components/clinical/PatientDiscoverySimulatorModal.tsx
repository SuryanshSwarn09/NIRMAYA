"use client";

import React, { useState } from "react";
import { X, Search, ShieldCheck, CheckCircle2, AlertTriangle, FileText, ChevronRight, RefreshCw } from "lucide-react";

export interface CareContextItem {
  referenceNumber: string;
  display: string;
  careContextType?: string;
  serviceDate?: string;
}

export interface MatchScoreBreakdown {
  identifier_score: number;
  mobile_score: number;
  name_score: number;
  yob_score: number;
  gender_score: number;
  combined_score: number;
}

export interface SimulationResult {
  matched: boolean;
  score: number;
  match_tier: string;
  score_breakdown: MatchScoreBreakdown;
  patient_reference?: string;
  patient_display?: string;
  care_contexts: CareContextItem[];
  error?: {
    code: number;
    message: string;
  };
}

interface PatientDiscoverySimulatorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PatientDiscoverySimulatorModal({ isOpen, onClose }: PatientDiscoverySimulatorModalProps) {
  const [abhaAddress, setAbhaAddress] = useState("ananya.sharma@abdm");
  const [name, setName] = useState("Ananya Sharma");
  const [yearOfBirth, setYearOfBirth] = useState("1994");
  const [gender, setGender] = useState("F");
  const [phoneNumber, setPhoneNumber] = useState("9876543210");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    setResult(null);

    try {
      const payload: Record<string, unknown> = {
        name: name.trim() || undefined,
        gender: gender || undefined,
        yearOfBirth: yearOfBirth ? parseInt(yearOfBirth, 10) : undefined,
      };

      const verifiedIdentifiers: Array<{ type: string; value: string }> = [];
      if (phoneNumber.trim()) {
        verifiedIdentifiers.push({ type: "MOBILE", value: phoneNumber.trim() });
      }

      const unverifiedIdentifiers: Array<{ type: string; value: string }> = [];
      if (abhaAddress.trim()) {
        unverifiedIdentifiers.push({ type: "ABHA_ADDRESS", value: abhaAddress.trim() });
      }

      if (verifiedIdentifiers.length > 0) {
        payload.verifiedIdentifiers = verifiedIdentifiers;
      }
      if (unverifiedIdentifiers.length > 0) {
        payload.unverifiedIdentifiers = unverifiedIdentifiers;
      }

      const response = await fetch("/api/v1/abdm/m2/bridge/discovery/simulate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Simulation failed with HTTP status ${response.status}`);
      }

      const data: SimulationResult = await response.json();
      setResult(data);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "An unexpected error occurred during simulation.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#111827]/40 p-4 backdrop-blur-[2px]">
      <div className="relative flex max-h-[90vh] w-full max-w-2xl flex-col rounded-[8px] border border-[#e5e7eb] bg-[#ffffff] shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#e5e7eb] px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-[6px] border border-[#e5e7eb] bg-[#f9fafb] text-[#111827]">
              <Search className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-[#111827]">ABDM M2 Patient Discovery Simulator</h2>
              <p className="text-xs text-[#6b7280]">Evaluate demographic fuzzy match scores and care context discovery</p>
            </div>
          </div>
          <button
            onClick={onClose}
            type="button"
            className="flex h-7 w-7 items-center justify-center rounded-[6px] text-[#6b7280] transition-colors hover:bg-[#f3f4f6] hover:text-[#111827]"
            aria-label="Close dialog"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          <form onSubmit={handleSimulate} className="space-y-4">
            <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-[#374151]">
                  ABHA Address / Identifier
                </label>
                <input
                  type="text"
                  value={abhaAddress}
                  onChange={(e) => setAbhaAddress(e.target.value)}
                  placeholder="e.g. ananya.sharma@abdm"
                  className="w-full rounded-[8px] border border-[#d1d5db] bg-[#ffffff] px-3 py-1.5 text-xs text-[#111827] placeholder-[#9ca3af] transition-colors focus:border-[#111827] focus:outline-none focus:ring-1 focus:ring-[#111827]"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-[#374151]">
                  Patient Full Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Ananya Sharma"
                  className="w-full rounded-[8px] border border-[#d1d5db] bg-[#ffffff] px-3 py-1.5 text-xs text-[#111827] placeholder-[#9ca3af] transition-colors focus:border-[#111827] focus:outline-none focus:ring-1 focus:ring-[#111827]"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-[#374151]">
                  Verified Mobile Number
                </label>
                <input
                  type="text"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="e.g. 9876543210"
                  className="w-full rounded-[8px] border border-[#d1d5db] bg-[#ffffff] px-3 py-1.5 text-xs text-[#111827] placeholder-[#9ca3af] transition-colors focus:border-[#111827] focus:outline-none focus:ring-1 focus:ring-[#111827]"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="mb-1 block text-xs font-medium text-[#374151]">
                    Year of Birth
                  </label>
                  <input
                    type="number"
                    value={yearOfBirth}
                    onChange={(e) => setYearOfBirth(e.target.value)}
                    placeholder="1994"
                    className="w-full rounded-[8px] border border-[#d1d5db] bg-[#ffffff] px-3 py-1.5 text-xs text-[#111827] placeholder-[#9ca3af] transition-colors focus:border-[#111827] focus:outline-none focus:ring-1 focus:ring-[#111827]"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[#374151]">
                    Gender
                  </label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-full rounded-[8px] border border-[#d1d5db] bg-[#ffffff] px-3 py-1.5 text-xs text-[#111827] transition-colors focus:border-[#111827] focus:outline-none focus:ring-1 focus:ring-[#111827]"
                  >
                    <option value="F">Female (F)</option>
                    <option value="M">Male (M)</option>
                    <option value="O">Other (O)</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={() => {
                  setName("Ananya Sharma");
                  setAbhaAddress("ananya.sharma@abdm");
                  setPhoneNumber("9876543210");
                  setYearOfBirth("1994");
                  setGender("F");
                  setResult(null);
                }}
                className="rounded-[8px] border border-[#e5e7eb] bg-[#ffffff] px-3 py-1.5 text-xs font-medium text-[#374151] transition-colors hover:bg-[#f9fafb]"
              >
                Reset Defaults
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="inline-flex items-center gap-1.5 rounded-[8px] bg-[#111827] px-4 py-1.5 text-xs font-medium text-[#ffffff] transition-colors hover:bg-[#1f2937] disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    Evaluating...
                  </>
                ) : (
                  <>
                    <Search className="h-3.5 w-3.5" />
                    Simulate Discovery
                  </>
                )}
              </button>
            </div>
          </form>

          {errorMsg && (
            <div className="mt-4 flex items-start gap-2.5 rounded-[8px] border border-[#fecaca] bg-[#fef2f2] p-3 text-xs text-[#991b1b]">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p className="font-medium">Discovery Simulation Failed</p>
                <p className="mt-0.5 text-[#b91c1c]">{errorMsg}</p>
              </div>
            </div>
          )}

          {result && (
            <div className="mt-5 space-y-4 border-t border-[#e5e7eb] pt-4">
              {/* Match Header Card */}
              <div
                className={`flex items-center justify-between rounded-[8px] border p-3.5 ${
                  result.matched
                    ? "border-[#bbf7d0] bg-[#f0fdf4]"
                    : result.error?.code === 1441
                    ? "border-[#fde68a] bg-[#fffbeb]"
                    : "border-[#e5e7eb] bg-[#f9fafb]"
                }`}
              >
                <div className="flex items-center gap-3">
                  {result.matched ? (
                    <div className="flex h-9 w-9 items-center justify-center rounded-[6px] border border-[#86efac] bg-[#ffffff] text-[#166534]">
                      <CheckCircle2 className="h-5 w-5" />
                    </div>
                  ) : (
                    <div className="flex h-9 w-9 items-center justify-center rounded-[6px] border border-[#d1d5db] bg-[#ffffff] text-[#4b5563]">
                      <AlertTriangle className="h-5 w-5" />
                    </div>
                  )}
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-[#111827]">
                        {result.matched
                          ? "Deterministic Patient Match"
                          : result.error?.code === 1441
                          ? "Ambiguous Match Aborted"
                          : "No Match Found"}
                      </span>
                      <span
                        className={`rounded-[6px] px-2 py-0.5 text-[10px] font-medium ${
                          result.matched
                            ? "bg-[#dcfce7] text-[#166534]"
                            : "bg-[#f3f4f6] text-[#4b5563]"
                        }`}
                      >
                        {result.match_tier}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-[#6b7280]">
                      {result.matched
                        ? `Patient: ${result.patient_display} (${result.patient_reference})`
                        : result.error?.message || "Demographics did not satisfy confidence threshold (0.85)"}
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-base font-bold text-[#111827]">
                    {(result.score * 100).toFixed(0)}%
                  </div>
                  <div className="text-[10px] uppercase tracking-wide text-[#6b7280]">
                    Match Score
                  </div>
                </div>
              </div>

              {/* Score Breakdown Radar */}
              <div className="rounded-[8px] border border-[#e5e7eb] bg-[#ffffff] p-3.5">
                <div className="mb-2.5 flex items-center justify-between">
                  <span className="text-xs font-medium text-[#111827]">Match Dimension Breakdown</span>
                  <span className="text-[10px] text-[#6b7280]">Multi-Tier Evaluation Rules</span>
                </div>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
                  <div className="rounded-[6px] border border-[#e5e7eb] bg-[#f9fafb] p-2 text-center">
                    <div className="text-[10px] text-[#6b7280]">Identifier</div>
                    <div className="mt-0.5 text-xs font-semibold text-[#111827]">
                      {(result.score_breakdown.identifier_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-[#e5e7eb] bg-[#f9fafb] p-2 text-center">
                    <div className="text-[10px] text-[#6b7280]">Mobile Phone</div>
                    <div className="mt-0.5 text-xs font-semibold text-[#111827]">
                      {(result.score_breakdown.mobile_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-[#e5e7eb] bg-[#f9fafb] p-2 text-center">
                    <div className="text-[10px] text-[#6b7280]">Full Name</div>
                    <div className="mt-0.5 text-xs font-semibold text-[#111827]">
                      {(result.score_breakdown.name_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-[#e5e7eb] bg-[#f9fafb] p-2 text-center">
                    <div className="text-[10px] text-[#6b7280]">Birth Year</div>
                    <div className="mt-0.5 text-xs font-semibold text-[#111827]">
                      {(result.score_breakdown.yob_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-[#e5e7eb] bg-[#f9fafb] p-2 text-center">
                    <div className="text-[10px] text-[#6b7280]">Gender</div>
                    <div className="mt-0.5 text-xs font-semibold text-[#111827]">
                      {(result.score_breakdown.gender_score * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Discovered Care Contexts */}
              <div className="rounded-[8px] border border-[#e5e7eb] bg-[#ffffff] p-3.5">
                <div className="mb-2.5 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-[#4b5563]" />
                    <span className="text-xs font-medium text-[#111827]">
                      Linked Care Contexts ({result.care_contexts?.length || 0})
                    </span>
                  </div>
                  <span className="text-[10px] text-[#6b7280]">Ready for ABDM Linkage</span>
                </div>

                {result.care_contexts && result.care_contexts.length > 0 ? (
                  <div className="space-y-1.5">
                    {result.care_contexts.map((ctx) => (
                      <div
                        key={ctx.referenceNumber}
                        className="flex items-center justify-between rounded-[6px] border border-[#e5e7eb] bg-[#f9fafb] px-3 py-2 text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[11px] text-[#374151]">
                            {ctx.referenceNumber}
                          </span>
                          <span className="text-[#6b7280]">|</span>
                          <span className="font-medium text-[#111827]">{ctx.display}</span>
                        </div>
                        <span className="rounded-[6px] border border-[#e5e7eb] bg-[#ffffff] px-2 py-0.5 text-[10px] font-medium text-[#4b5563]">
                          {ctx.careContextType || "CARE_CONTEXT"}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-4 text-center text-xs text-[#9ca3af]">
                    No care contexts discovered for this patient record.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-[#e5e7eb] bg-[#f9fafb] px-6 py-3">
          <div className="flex items-center gap-1.5 text-[11px] text-[#6b7280]">
            <ShieldCheck className="h-3.5 w-3.5 text-[#166534]" />
            <span>Compliant with ABDM M2 Discovery & Ambiguity Specifications</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-[8px] border border-[#e5e7eb] bg-[#ffffff] px-3 py-1.5 text-xs font-medium text-[#374151] transition-colors hover:bg-[#f3f4f6]"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
