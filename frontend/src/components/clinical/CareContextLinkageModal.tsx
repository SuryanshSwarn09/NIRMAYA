"use client";

import React, { useState } from "react";
import {
  X,
  Link2,
  ShieldCheck,
  Smartphone,
  CheckCircle2,
  AlertCircle,
  Copy,
  Clock,
  ArrowRight,
  RefreshCw,
  FileText,
  User,
} from "lucide-react";

export interface CareContextItem {
  referenceNumber: string;
  display: string;
}

export interface CareContextLinkageModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialPatientId?: string;
  initialPatientName?: string;
}

export function CareContextLinkageModal({
  isOpen,
  onClose,
  initialPatientId = "arun.patel@abdm",
  initialPatientName = "Arun Patel",
}: CareContextLinkageModalProps) {
  // Wizard steps: 1 = Init, 2 = Verify OTP, 3 = Confirmed
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Step 1 Form state
  const [patientIdentifier, setPatientIdentifier] = useState(initialPatientId);
  const [selectedCareContexts, setSelectedCareContexts] = useState<string[]>([]);
  const [initLoading, setInitLoading] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);

  // Step 2 Challenge state
  const [linkRefNumber, setLinkRefNumber] = useState<string>("");
  const [transactionId, setTransactionId] = useState<string>("");
  const [communicationHint, setCommunicationHint] = useState<string>("+91 ******3210");
  const [sandboxOtp, setSandboxOtp] = useState<string>("123456");
  const [otpInput, setOtpInput] = useState<string>("");
  const [attemptsLeft, setAttemptsLeft] = useState<number>(3);
  const [verifyLoading, setVerifyLoading] = useState<boolean>(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  // Step 3 Result state
  const [linkedPatientName, setLinkedPatientName] = useState<string>(initialPatientName);
  const [confirmedContexts, setConfirmedContexts] = useState<CareContextItem[]>([]);
  const [callbackPayload, setCallbackPayload] = useState<Record<string, unknown> | null>(null);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  // Preset demo patients
  const demoPatients = [
    { id: "arun.patel@abdm", name: "Arun Patel", abha: "91-1029-3847-5610" },
    { id: "priya.sharma@abdm", name: "Priya Sharma", abha: "91-4521-8830-1092" },
    { id: "kavita.rao@abdm", name: "Kavita Rao", abha: "91-8840-2219-5561" },
  ];

  const handleInitLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setInitLoading(true);
    setInitError(null);

    try {
      const res = await fetch("/api/v1/abdm/m2/bridge/link/init/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_identifier: patientIdentifier,
          care_context_references: selectedCareContexts.length > 0 ? selectedCareContexts : null,
        }),
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const body = await res.json();
      const data = body.data;

      if (!data.success) {
        setInitError(data.error_message || "Failed to initiate link challenge");
        return;
      }

      setLinkRefNumber(data.link_ref_number);
      setTransactionId(data.transaction_id);
      setCommunicationHint(data.communication_hint);
      setSandboxOtp(data.otp_sandbox_hint || "123456");
      setAttemptsLeft(3);
      setStep(2);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setInitError(msg);
    } finally {
      setInitLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpInput || otpInput.trim().length !== 6) {
      setVerifyError("Please enter a valid 6-digit OTP code");
      return;
    }

    setVerifyLoading(true);
    setVerifyError(null);

    try {
      const res = await fetch("/api/v1/abdm/m2/bridge/link/confirm/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          link_ref_number: linkRefNumber,
          otp_token: otpInput.trim(),
        }),
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const body = await res.json();
      const data = body.data;

      if (!data.success || !data.linked) {
        setAttemptsLeft((prev) => Math.max(0, prev - 1));
        setVerifyError(data.error_message || "Invalid OTP code entered");
        return;
      }

      setLinkedPatientName(data.patient_name || patientIdentifier);
      setConfirmedContexts(data.linked_care_contexts || []);
      setCallbackPayload(data.callback_payload || null);
      setStep(3);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setVerifyError(msg);
    } finally {
      setVerifyLoading(false);
    }
  };

  const handleCopyPayload = () => {
    if (!callbackPayload) return;
    navigator.clipboard.writeText(JSON.stringify(callbackPayload, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    setStep(1);
    setOtpInput("");
    setInitError(null);
    setVerifyError(null);
    setCallbackPayload(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#111827]/40 backdrop-blur-xs font-sans">
      <div className="w-full max-w-2xl bg-[#ffffff] border border-[#e5e7eb] rounded-[10px] shadow-lg overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#e5e7eb] flex items-center justify-between bg-[#ffffff]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-[6px] bg-[#f9fafb] border border-[#e5e7eb] flex items-center justify-center text-[#111827]">
              <Link2 className="w-4 h-4 text-[#111827]" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#111827]">
                ABDM Care Context Linkage Simulator
              </h3>
              <p className="text-xs text-[#6b7280]">
                ABDM Milestone 2 (HIP Record Linkage & DIRECT OTP Verification)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-[6px] text-[#6b7280] hover:text-[#111827] hover:bg-[#f3f4f6] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Wizard Progress Indicator */}
        <div className="px-6 py-2.5 bg-[#f9fafb] border-b border-[#e5e7eb] flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-semibold ${
                step >= 1 ? "bg-[#111827] text-[#ffffff]" : "bg-[#e5e7eb] text-[#6b7280]"
              }`}
            >
              1
            </span>
            <span className={step === 1 ? "font-medium text-[#111827]" : "text-[#6b7280]"}>
              Link Initiation
            </span>
          </div>
          <div className="w-8 h-[1px] bg-[#e5e7eb]"></div>
          <div className="flex items-center gap-2">
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-semibold ${
                step >= 2 ? "bg-[#111827] text-[#ffffff]" : "bg-[#e5e7eb] text-[#6b7280]"
              }`}
            >
              2
            </span>
            <span className={step === 2 ? "font-medium text-[#111827]" : "text-[#6b7280]"}>
              OTP Challenge
            </span>
          </div>
          <div className="w-8 h-[1px] bg-[#e5e7eb]"></div>
          <div className="flex items-center gap-2">
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-semibold ${
                step === 3 ? "bg-[#059669] text-[#ffffff]" : "bg-[#e5e7eb] text-[#6b7280]"
              }`}
            >
              3
            </span>
            <span className={step === 3 ? "font-medium text-[#059669]" : "text-[#6b7280]"}>
              Records Linked
            </span>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-[#374151]">
          {/* STEP 1: Link Initiation Form */}
          {step === 1 && (
            <form onSubmit={handleInitLink} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[#111827] mb-1">
                  Target Patient Identifier (ABHA Address or 14-digit ABHA Number)
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={patientIdentifier}
                    onChange={(e) => setPatientIdentifier(e.target.value)}
                    placeholder="e.g. arun.patel@abdm or 91-1029-3847-5610"
                    required
                    className="w-full px-3 py-2 text-xs border border-[#e5e7eb] rounded-[6px] focus:outline-none focus:ring-1 focus:ring-[#111827] bg-[#ffffff] font-mono text-[#111827]"
                  />
                  <div className="absolute right-2.5 top-2.5 text-[#9ca3af]">
                    <User className="w-3.5 h-3.5" />
                  </div>
                </div>
              </div>

              {/* Demo quick selection */}
              <div>
                <span className="text-[11px] text-[#6b7280] block mb-1.5 font-medium">
                  Pre-configured Sandbox Profiles:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {demoPatients.map((dp) => (
                    <button
                      key={dp.id}
                      type="button"
                      onClick={() => setPatientIdentifier(dp.id)}
                      className={`px-2 py-1 rounded-[6px] border text-[11px] transition-colors ${
                        patientIdentifier === dp.id
                          ? "bg-[#111827] text-[#ffffff] border-[#111827]"
                          : "bg-[#ffffff] text-[#374151] border-[#e5e7eb] hover:bg-[#f9fafb]"
                      }`}
                    >
                      {dp.name} ({dp.id})
                    </button>
                  ))}
                </div>
              </div>

              {/* Information Callout */}
              <div className="p-3 bg-[#f9fafb] border border-[#e5e7eb] rounded-[6px] text-xs text-[#4b5563] space-y-1">
                <div className="flex items-center gap-1.5 text-[#111827] font-medium">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#059669]" />
                  ABDM Gateway Protocol Handshake
                </div>
                <p className="text-[11px] leading-relaxed text-[#6b7280]">
                  When initiating care context linkage, the HIP matches the patient vault record,
                  extracts verified OPD clinical consultations and diagnostic lab investigations, and
                  dispatches a simulated 6-digit SMS OTP challenge valid for 10 minutes.
                </p>
              </div>

              {initError && (
                <div className="p-2.5 rounded-[6px] bg-[#fef2f2] border border-[#fecaca] text-[#991b1b] flex items-center gap-2 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0 text-[#dc2626]" />
                  <span>{initError}</span>
                </div>
              )}

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 border border-[#e5e7eb] rounded-[6px] text-xs font-medium text-[#374151] hover:bg-[#f9fafb] transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={initLoading || !patientIdentifier.trim()}
                  className="px-4 py-2 bg-[#111827] text-[#ffffff] rounded-[6px] text-xs font-medium hover:bg-[#1f2937] transition-colors flex items-center gap-1.5 disabled:opacity-50"
                >
                  {initLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Initiating Link...
                    </>
                  ) : (
                    <>
                      Initiate Care Context Link
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* STEP 2: OTP Verification Challenge */}
          {step === 2 && (
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div className="p-3 bg-[#f9fafb] border border-[#e5e7eb] rounded-[6px] space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#6b7280]">Link Reference:</span>
                  <span className="font-mono font-semibold text-[#111827]">{linkRefNumber}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#6b7280]">Communication Target:</span>
                  <span className="font-medium text-[#111827] flex items-center gap-1">
                    <Smartphone className="w-3.5 h-3.5 text-[#4b5563]" />
                    {communicationHint}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs pt-1 border-t border-[#e5e7eb]">
                  <span className="text-[#6b7280]">Challenge Expiry:</span>
                  <span className="text-[#059669] flex items-center gap-1 font-medium">
                    <Clock className="w-3 h-3" />
                    10 Minutes Remaining
                  </span>
                </div>
              </div>

              {/* Sandbox auto-fill helper */}
              <div className="p-2.5 bg-[#ecfdf5] border border-[#a7f3d0] rounded-[6px] flex items-center justify-between text-xs">
                <div>
                  <span className="font-semibold text-[#065f46] block text-[11px]">
                    Sandbox Test OTP Hint
                  </span>
                  <span className="text-xs text-[#047857]">
                    Simulated verification code:{" "}
                    <span className="font-mono font-bold text-[#065f46]">{sandboxOtp}</span>
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setOtpInput(sandboxOtp)}
                  className="px-2.5 py-1 bg-[#065f46] text-[#ffffff] rounded-[4px] text-[11px] font-medium hover:bg-[#047857] transition-colors"
                >
                  Auto-Fill OTP
                </button>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#111827] mb-1">
                  Enter 6-Digit OTP Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  value={otpInput}
                  onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, ""))}
                  placeholder="123456"
                  required
                  autoFocus
                  className="w-full text-center tracking-widest text-lg font-mono px-3 py-2 border border-[#e5e7eb] rounded-[6px] focus:outline-none focus:ring-1 focus:ring-[#111827] bg-[#ffffff] text-[#111827]"
                />
                <div className="flex items-center justify-between text-[11px] text-[#6b7280] mt-1.5">
                  <span>Attempts remaining: {attemptsLeft} of 3</span>
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="text-[#111827] hover:underline"
                  >
                    Change patient
                  </button>
                </div>
              </div>

              {verifyError && (
                <div className="p-2.5 rounded-[6px] bg-[#fef2f2] border border-[#fecaca] text-[#991b1b] flex items-center gap-2 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0 text-[#dc2626]" />
                  <span>{verifyError}</span>
                </div>
              )}

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="px-4 py-2 border border-[#e5e7eb] rounded-[6px] text-xs font-medium text-[#374151] hover:bg-[#f9fafb] transition-colors"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={verifyLoading || otpInput.length !== 6 || attemptsLeft <= 0}
                  className="px-4 py-2 bg-[#111827] text-[#ffffff] rounded-[6px] text-xs font-medium hover:bg-[#1f2937] transition-colors flex items-center gap-1.5 disabled:opacity-50"
                >
                  {verifyLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Verify & Link Records
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* STEP 3: Confirmed & Linked Records */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="p-4 bg-[#ecfdf5] border border-[#a7f3d0] rounded-[8px] text-center space-y-1">
                <div className="w-10 h-10 rounded-full bg-[#10b981]/20 text-[#059669] flex items-center justify-center mx-auto mb-2">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-semibold text-[#065f46]">
                  Care Contexts Successfully Linked!
                </h4>
                <p className="text-xs text-[#047857]">
                  All selected health records for <span className="font-semibold">{linkedPatientName}</span> are now bound to their ABHA address.
                </p>
              </div>

              {/* List of Linked Care Contexts */}
              <div>
                <h5 className="text-xs font-semibold text-[#111827] mb-2 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-[#4b5563]" />
                  Active Care Context Episodes Linked ({confirmedContexts.length})
                </h5>
                <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                  {confirmedContexts.map((cc) => (
                    <div
                      key={cc.referenceNumber}
                      className="p-2.5 rounded-[6px] bg-[#f9fafb] border border-[#e5e7eb] flex items-center justify-between"
                    >
                      <div>
                        <span className="font-medium text-[#111827] block text-xs">{cc.display}</span>
                        <span className="text-[10px] text-[#6b7280] font-mono">{cc.referenceNumber}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded-[4px] text-[10px] font-semibold bg-[#ecfdf5] text-[#065f46] border border-[#a7f3d0]">
                        LINKED
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Collapsible Gateway On-Confirm JSON Payload */}
              {callbackPayload && (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-semibold text-[#6b7280] uppercase tracking-wider">
                      ABDM On-Confirm Callback Payload (/v0.5/links/link/on-confirm)
                    </span>
                    <button
                      type="button"
                      onClick={handleCopyPayload}
                      className="text-[11px] text-[#4b5563] hover:text-[#111827] flex items-center gap-1"
                    >
                      <Copy className="w-3 h-3" />
                      {copied ? "Copied" : "Copy JSON"}
                    </button>
                  </div>
                  <pre className="p-3 bg-[#111827] text-[#f9fafb] rounded-[6px] text-[11px] font-mono overflow-x-auto max-h-36">
                    {JSON.stringify(callbackPayload, null, 2)}
                  </pre>
                </div>
              )}

              <div className="pt-2 flex justify-between items-center">
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-3 py-1.5 border border-[#e5e7eb] rounded-[6px] text-xs font-medium text-[#374151] hover:bg-[#f9fafb] transition-colors"
                >
                  Link Another Patient
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 bg-[#111827] text-[#ffffff] rounded-[6px] text-xs font-medium hover:bg-[#1f2937] transition-colors"
                >
                  Done
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
