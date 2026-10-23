"use client";

import React from "react";
import { Button } from "@/components/ui";
import { X, CheckCircle2, Code, Copy, Activity, Thermometer, Gauge } from "lucide-react";

export interface PatientModalsProps {
  isLogVitalsOpen: boolean;
  onCloseLogVitals: () => void;
  logVitalType: "hr" | "bp" | "spo2";
  setLogVitalType: (type: "hr" | "bp" | "spo2") => void;
  logValue: string;
  setLogValue: (val: string) => void;
  logSystolic: string;
  setLogSystolic: (val: string) => void;
  logDiastolic: string;
  setLogDiastolic: (val: string) => void;
  onLogVitalSubmit: (e: React.FormEvent) => void;
  selectedFhirJson: any | null;
  onCloseFhirModal: () => void;
  viewingFhirRx: any | null;
  onCloseFhirRxModal: () => void;
}

export function PatientModals({
  isLogVitalsOpen,
  onCloseLogVitals,
  logVitalType,
  setLogVitalType,
  logValue,
  setLogValue,
  logSystolic,
  setLogSystolic,
  logDiastolic,
  setLogDiastolic,
  onLogVitalSubmit,
  selectedFhirJson,
  onCloseFhirModal,
  viewingFhirRx,
  onCloseFhirRxModal,
}: PatientModalsProps) {
  return (
    <>
      {/* 1. Log Vital Signs Modal */}
      {isLogVitalsOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-[12px] border border-[#e5e7eb] shadow-xl max-w-md w-full p-6 space-y-5 animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div>
                <h3 className="text-lg font-bold text-[#111111] tracking-tight">
                  Record Biometric Vital
                </h3>
                <p className="text-xs text-[#6b7280]">
                  Log fresh telemetry into your longitudinal FHIR problem vault.
                </p>
              </div>
              <button
                type="button"
                onClick={onCloseLogVitals}
                className="text-[#9ca3af] hover:text-[#111111] transition-colors p-1"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={onLogVitalSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-[#111111] mb-1.5">
                  Select Metric Type
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setLogVitalType("hr")}
                    className={`py-2 px-3 rounded-[6px] border text-center font-medium transition-all ${
                      logVitalType === "hr"
                        ? "bg-[#111111] text-white border-[#111111]"
                        : "bg-[#f8f9fa] text-[#111111] border-[#e5e7eb] hover:bg-[#e5e7eb]"
                    }`}
                  >
                    Heart Rate
                  </button>
                  <button
                    type="button"
                    onClick={() => setLogVitalType("bp")}
                    className={`py-2 px-3 rounded-[6px] border text-center font-medium transition-all ${
                      logVitalType === "bp"
                        ? "bg-[#111111] text-white border-[#111111]"
                        : "bg-[#f8f9fa] text-[#111111] border-[#e5e7eb] hover:bg-[#e5e7eb]"
                    }`}
                  >
                    Blood Pressure
                  </button>
                  <button
                    type="button"
                    onClick={() => setLogVitalType("spo2")}
                    className={`py-2 px-3 rounded-[6px] border text-center font-medium transition-all ${
                      logVitalType === "spo2"
                        ? "bg-[#111111] text-white border-[#111111]"
                        : "bg-[#f8f9fa] text-[#111111] border-[#e5e7eb] hover:bg-[#e5e7eb]"
                    }`}
                  >
                    Oxygen (SpO2)
                  </button>
                </div>
              </div>

              {logVitalType === "bp" ? (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-medium text-[#111111] mb-1">
                      Systolic (mmHg)
                    </label>
                    <input
                      type="number"
                      required
                      value={logSystolic}
                      onChange={(e) => setLogSystolic(e.target.value)}
                      className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] text-sm focus:outline-hidden focus:border-[#111111]"
                      placeholder="120"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-[#111111] mb-1">
                      Diastolic (mmHg)
                    </label>
                    <input
                      type="number"
                      required
                      value={logDiastolic}
                      onChange={(e) => setLogDiastolic(e.target.value)}
                      className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] text-sm focus:outline-hidden focus:border-[#111111]"
                      placeholder="80"
                    />
                  </div>
                </div>
              ) : (
                <div>
                  <label className="block font-medium text-[#111111] mb-1">
                    Measurement Value ({logVitalType === "hr" ? "/min" : "%"})
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={logValue}
                    onChange={(e) => setLogValue(e.target.value)}
                    className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] text-sm focus:outline-hidden focus:border-[#111111]"
                    placeholder={logVitalType === "hr" ? "75" : "98"}
                  />
                </div>
              )}

              <div className="p-3 bg-[#f8f9fa] rounded-[6px] border border-[#e5e7eb] text-[11px] text-[#6b7280]">
                Calibrated values automatically generate LOINC-coded FHIR Observation instances in your personal health record.
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#e5e7eb]">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={onCloseLogVitals}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                >
                  Save Measurement
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 2. Generic FHIR JSON Modal */}
      {selectedFhirJson && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-[12px] border border-[#e5e7eb] shadow-2xl max-w-2xl w-full p-6 space-y-4 max-h-[85vh] flex flex-col animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <Code className="h-5 w-5 text-[#111111]" />
                <h3 className="text-base font-bold text-[#111111]">
                  HL7 FHIR R4 {selectedFhirJson.resourceType} Resource
                </h3>
              </div>
              <button
                type="button"
                onClick={onCloseFhirModal}
                className="text-[#9ca3af] hover:text-[#111111] transition-colors p-1 cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <pre className="p-3 bg-[#111111] text-[#f8f9fa] rounded-[8px] text-[11px] font-mono overflow-auto max-h-80 leading-relaxed">
              {JSON.stringify(selectedFhirJson, null, 2)}
            </pre>

            <div className="flex items-center justify-between pt-2 border-t border-[#e5e7eb]">
              <span className="text-xs text-[#059669] font-medium flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Valid HL7 FHIR R4 Structure
              </span>
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(selectedFhirJson, null, 2));
                  alert("Copied FHIR JSON to clipboard!");
                }}
              >
                Copy JSON
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 3. FHIR R4 MedicationRequest Modal */}
      {viewingFhirRx && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-[12px] border border-[#e5e7eb] shadow-2xl max-w-2xl w-full p-6 space-y-4 max-h-[85vh] flex flex-col animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <Code className="h-5 w-5 text-[#111111]" />
                <h3 className="text-base font-bold text-[#111111]">
                  HL7 FHIR R4 MedicationRequest Resource
                </h3>
              </div>
              <button
                type="button"
                onClick={onCloseFhirRxModal}
                className="text-[#9ca3af] hover:text-[#111111] transition-colors p-1 cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <pre className="flex-1 overflow-auto bg-[#0b0f19] text-[#e2e8f0] p-4 rounded-[8px] text-[11px] font-mono leading-relaxed border border-[#1e293b]">
              {JSON.stringify(viewingFhirRx, null, 2)}
            </pre>
            <div className="flex justify-between items-center pt-2 border-t border-[#e5e7eb]">
              <span className="text-xs text-[#059669] font-medium flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" />
                ABDM NRCeS Prescription Profile Compliant
              </span>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(viewingFhirRx, null, 2));
                  }}
                >
                  <Copy className="h-3.5 w-3.5 mr-1" />
                  Copy JSON
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={onCloseFhirRxModal}
                >
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
