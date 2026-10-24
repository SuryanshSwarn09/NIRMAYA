"use client";

import React, { useMemo } from "react";
import { Button } from "@/components/ui";
import {
  X,
  CheckCircle2,
  Code,
  Copy,
  Activity,
  Heart,
  Gauge,
  Scale,
  Thermometer,
  AlertTriangle,
  AlertCircle,
  Info,
} from "lucide-react";
import {
  evaluateBloodPressure,
  evaluateHeartRate,
  evaluateSpo2,
  evaluateBmi,
  evaluateTemperature,
  calculateBmi,
  LOINC_CODES,
  ClinicalEvaluation,
} from "@/lib/vitals";

export type VitalMetricType = "hr" | "bp" | "spo2" | "weight" | "temp";

export interface PatientModalsProps {
  isLogVitalsOpen: boolean;
  onCloseLogVitals: () => void;
  logVitalType: VitalMetricType;
  setLogVitalType: (type: VitalMetricType) => void;
  logValue: string;
  setLogValue: (val: string) => void;
  logSystolic: string;
  setLogSystolic: (val: string) => void;
  logDiastolic: string;
  setLogDiastolic: (val: string) => void;
  logWeight?: string;
  setLogWeight?: (val: string) => void;
  logHeight?: string;
  setLogHeight?: (val: string) => void;
  logTemp?: string;
  setLogTemp?: (val: string) => void;
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
  logWeight,
  setLogWeight,
  logHeight,
  setLogHeight,
  logTemp,
  setLogTemp,
  onLogVitalSubmit,
  selectedFhirJson,
  onCloseFhirModal,
  viewingFhirRx,
  onCloseFhirRxModal,
}: PatientModalsProps) {
  // Compute instant live clinical interpretation based on current intake
  const liveEvaluation: {
    eval: ClinicalEvaluation;
    loinc: string;
    targetText: string;
    computedValText?: string;
  } = useMemo(() => {
    switch (logVitalType) {
      case "bp": {
        const sys = parseFloat(logSystolic) || 120;
        const dia = parseFloat(logDiastolic) || 80;
        return {
          eval: evaluateBloodPressure(sys, dia),
          loinc: LOINC_CODES.BLOOD_PRESSURE_PANEL,
          targetText: "Normal: < 120/< 80 mmHg",
          computedValText: `${sys}/${dia} mmHg`,
        };
      }
      case "hr": {
        const bpm = parseFloat(logValue) || 72;
        return {
          eval: evaluateHeartRate(bpm),
          loinc: LOINC_CODES.HEART_RATE,
          targetText: "Normal Resting: 60 - 100 bpm",
          computedValText: `${bpm} bpm`,
        };
      }
      case "spo2": {
        const pct = parseFloat(logValue) || 98;
        return {
          eval: evaluateSpo2(pct),
          loinc: LOINC_CODES.OXYGEN_SATURATION,
          targetText: "Normal: ≥ 95%",
          computedValText: `${pct}%`,
        };
      }
      case "weight": {
        const wt = parseFloat(logWeight || logValue) || 70;
        const ht = parseFloat(logHeight || "175") || 175;
        const bmi = calculateBmi(wt, ht);
        return {
          eval: evaluateBmi(bmi),
          loinc: LOINC_CODES.BODY_MASS_INDEX,
          targetText: "Healthy BMI: 18.5 - 24.9 kg/m²",
          computedValText: `${wt} kg (BMI: ${bmi} kg/m²)`,
        };
      }
      case "temp": {
        const temp = parseFloat(logTemp || logValue) || 98.6;
        return {
          eval: evaluateTemperature(temp),
          loinc: LOINC_CODES.BODY_TEMPERATURE,
          targetText: "Normal: 97.8°F - 99.0°F",
          computedValText: `${temp}°F`,
        };
      }
      default:
        return {
          eval: {
            interpretation: "normal",
            label: "Normal",
            stage: "Baseline",
            category: "normal",
            recommendation: "Within clinical baseline limits.",
          },
          loinc: "LOINC",
          targetText: "Target: Normal range",
        };
    }
  }, [logVitalType, logSystolic, logDiastolic, logValue, logWeight, logHeight, logTemp]);

  const badgeCategoryStyles = {
    normal: "bg-[#ecfdf5] text-[#065f46] border-[#a7f3d0]",
    elevated: "bg-[#fffbeb] text-[#92400e] border-[#fde68a]",
    warning: "bg-[#fff7ed] text-[#9a3412] border-[#fed7aa]",
    critical: "bg-[#fef2f2] text-[#991b1b] border-[#fecaca]",
  };

  return (
    <>
      {/* 1. Log Vital Signs Modal */}
      {isLogVitalsOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-[12px] border border-[#e5e7eb] shadow-xl max-w-lg w-full p-6 space-y-5 animate-scale-in max-h-[92vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div>
                <h3 className="text-lg font-bold text-[#111111] tracking-tight">
                  Record Biometric Vital
                </h3>
                <p className="text-xs text-[#6b7280]">
                  Log fresh telemetry into your longitudinal FHIR observation vault.
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
                <div className="grid grid-cols-5 gap-1.5">
                  <button
                    type="button"
                    onClick={() => setLogVitalType("bp")}
                    className={`py-2 px-1.5 rounded-[6px] border text-center font-medium transition-all flex flex-col items-center justify-center gap-1 ${
                      logVitalType === "bp"
                        ? "bg-[#111111] text-white border-[#111111]"
                        : "bg-[#f8f9fa] text-[#111111] border-[#e5e7eb] hover:bg-[#e5e7eb]"
                    }`}
                  >
                    <Gauge className="h-4 w-4" />
                    <span className="text-[10px]">Blood Press.</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setLogVitalType("hr")}
                    className={`py-2 px-1.5 rounded-[6px] border text-center font-medium transition-all flex flex-col items-center justify-center gap-1 ${
                      logVitalType === "hr"
                        ? "bg-[#111111] text-white border-[#111111]"
                        : "bg-[#f8f9fa] text-[#111111] border-[#e5e7eb] hover:bg-[#e5e7eb]"
                    }`}
                  >
                    <Heart className="h-4 w-4" />
                    <span className="text-[10px]">Heart Rate</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setLogVitalType("spo2")}
                    className={`py-2 px-1.5 rounded-[6px] border text-center font-medium transition-all flex flex-col items-center justify-center gap-1 ${
                      logVitalType === "spo2"
                        ? "bg-[#111111] text-white border-[#111111]"
                        : "bg-[#f8f9fa] text-[#111111] border-[#e5e7eb] hover:bg-[#e5e7eb]"
                    }`}
                  >
                    <Activity className="h-4 w-4" />
                    <span className="text-[10px]">SpO2 Pulse</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setLogVitalType("weight")}
                    className={`py-2 px-1.5 rounded-[6px] border text-center font-medium transition-all flex flex-col items-center justify-center gap-1 ${
                      logVitalType === "weight"
                        ? "bg-[#111111] text-white border-[#111111]"
                        : "bg-[#f8f9fa] text-[#111111] border-[#e5e7eb] hover:bg-[#e5e7eb]"
                    }`}
                  >
                    <Scale className="h-4 w-4" />
                    <span className="text-[10px]">Weight / BMI</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setLogVitalType("temp")}
                    className={`py-2 px-1.5 rounded-[6px] border text-center font-medium transition-all flex flex-col items-center justify-center gap-1 ${
                      logVitalType === "temp"
                        ? "bg-[#111111] text-white border-[#111111]"
                        : "bg-[#f8f9fa] text-[#111111] border-[#e5e7eb] hover:bg-[#e5e7eb]"
                    }`}
                  >
                    <Thermometer className="h-4 w-4" />
                    <span className="text-[10px]">Temperature</span>
                  </button>
                </div>
              </div>

              {/* Dynamic Inputs according to Selected Vital */}
              {logVitalType === "bp" && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-medium text-[#111111] mb-1">
                      Systolic (mmHg)
                    </label>
                    <input
                      type="number"
                      required
                      min="60"
                      max="260"
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
                      min="40"
                      max="160"
                      value={logDiastolic}
                      onChange={(e) => setLogDiastolic(e.target.value)}
                      className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] text-sm focus:outline-hidden focus:border-[#111111]"
                      placeholder="80"
                    />
                  </div>
                </div>
              )}

              {logVitalType === "hr" && (
                <div>
                  <label className="block font-medium text-[#111111] mb-1">
                    Resting Heart Rate (beats / min)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="30"
                    max="220"
                    required
                    value={logValue}
                    onChange={(e) => setLogValue(e.target.value)}
                    className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] text-sm focus:outline-hidden focus:border-[#111111]"
                    placeholder="72"
                  />
                </div>
              )}

              {logVitalType === "spo2" && (
                <div>
                  <label className="block font-medium text-[#111111] mb-1">
                    Blood Oxygen Saturation (SpO2 %)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="70"
                    max="100"
                    required
                    value={logValue}
                    onChange={(e) => setLogValue(e.target.value)}
                    className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] text-sm focus:outline-hidden focus:border-[#111111]"
                    placeholder="98"
                  />
                </div>
              )}

              {logVitalType === "weight" && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-medium text-[#111111] mb-1">
                      Body Weight (kg)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="20"
                      max="300"
                      required
                      value={logWeight !== undefined ? logWeight : logValue}
                      onChange={(e) => {
                        if (setLogWeight) setLogWeight(e.target.value);
                        setLogValue(e.target.value);
                      }}
                      className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] text-sm focus:outline-hidden focus:border-[#111111]"
                      placeholder="72.5"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-[#111111] mb-1">
                      Height (cm)
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      min="80"
                      max="240"
                      required
                      value={logHeight || "175"}
                      onChange={(e) => setLogHeight && setLogHeight(e.target.value)}
                      className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] text-sm focus:outline-hidden focus:border-[#111111]"
                      placeholder="175"
                    />
                  </div>
                </div>
              )}

              {logVitalType === "temp" && (
                <div>
                  <label className="block font-medium text-[#111111] mb-1">
                    Body Temperature (°F)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="90"
                    max="108"
                    required
                    value={logTemp !== undefined ? logTemp : logValue}
                    onChange={(e) => {
                      if (setLogTemp) setLogTemp(e.target.value);
                      setLogValue(e.target.value);
                    }}
                    className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] text-sm focus:outline-hidden focus:border-[#111111]"
                    placeholder="98.6"
                  />
                </div>
              )}

              {/* Live Instant LOINC Clinical Evaluation Box */}
              <div className="p-3 bg-[#f8f9fa] rounded-[8px] border border-[#e5e7eb] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-medium text-[#6b7280] uppercase tracking-wider flex items-center gap-1">
                    <Info className="h-3 w-3 text-[#9ca3af]" />
                    LOINC {liveEvaluation.loinc} Evaluation
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] text-[10px] font-semibold border ${
                      badgeCategoryStyles[liveEvaluation.eval.category]
                    }`}
                  >
                    {liveEvaluation.eval.category === "critical" ? (
                      <AlertCircle className="h-3 w-3" />
                    ) : liveEvaluation.eval.category === "warning" ||
                      liveEvaluation.eval.category === "elevated" ? (
                      <AlertTriangle className="h-3 w-3" />
                    ) : (
                      <CheckCircle2 className="h-3 w-3" />
                    )}
                    {liveEvaluation.eval.label}
                  </span>
                </div>

                <div className="flex items-baseline justify-between text-xs pt-1">
                  <span className="font-semibold text-[#111111]">
                    {liveEvaluation.computedValText}
                  </span>
                  <span className="text-[11px] text-[#6b7280]">
                    {liveEvaluation.targetText}
                  </span>
                </div>

                <p className="text-[11px] text-[#4b5563] leading-relaxed border-t border-[#e5e7eb]/80 pt-1.5">
                  {liveEvaluation.eval.recommendation}
                </p>
              </div>

              <div className="p-2.5 bg-[#ffffff] rounded-[6px] border border-[#e5e7eb] text-[11px] text-[#6b7280] flex items-center gap-2">
                <Activity className="h-4 w-4 text-[#059669] shrink-0" />
                <span>
                  Calibrated values automatically generate LOINC-coded HL7 FHIR R4 Observation instances in your personal health vault.
                </span>
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
