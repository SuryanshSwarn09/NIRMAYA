"use client";

import React, { useState } from "react";
import { Badge, Button, Card } from "@/components/ui";
import { 
  VitalsTimeSeriesPoint, 
  VitalSignRecord, 
  evaluateBloodPressure, 
  getVitalBadgeConfig 
} from "@/lib/vitals";
import { BloodPressureChart } from "./BloodPressureChart";
import { VitalsMetricChart, MetricType } from "./VitalsMetricChart";
import { 
  Activity, 
  Heart, 
  Wind, 
  Scale, 
  Thermometer, 
  Plus, 
  FileCode, 
  Calendar, 
  CheckCircle2, 
  ShieldCheck,
  TrendingUp,
  Download
} from "lucide-react";

export interface PatientVitalsTelemetryProps {
  timeSeriesData: VitalsTimeSeriesPoint[];
  recordsList?: VitalSignRecord[] | any[];
  onOpenLogModal: () => void;
  onInspectFhir: (fhirResource: any) => void;
  className?: string;
}

export function PatientVitalsTelemetry({
  timeSeriesData,
  recordsList = [],
  onOpenLogModal,
  onInspectFhir,
  className = "",
}: PatientVitalsTelemetryProps) {
  const [activeChartTab, setActiveChartTab] = useState<"bp" | "other">("bp");
  const [selectedSubMetric, setSelectedSubMetric] = useState<MetricType>("heartRate");

  // Get latest values
  const latestPoint = timeSeriesData.length > 0 ? timeSeriesData[timeSeriesData.length - 1] : null;
  const bpEval = latestPoint && latestPoint.systolic && latestPoint.diastolic
    ? evaluateBloodPressure(latestPoint.systolic, latestPoint.diastolic)
    : null;

  return (
    <div className={`space-y-6 ${className}`}>
      
      {/* 1. Quick Telemetry Metrics Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* Blood Pressure Card */}
        <div 
          onClick={() => setActiveChartTab("bp")}
          className={`p-4 rounded-[12px] border cursor-pointer transition-all space-y-1 ${
            activeChartTab === "bp"
              ? "bg-white border-[#111111] shadow-xs"
              : "bg-[#f8f9fa] border-[#e5e7eb] hover:bg-white"
          }`}
        >
          <div className="flex items-center justify-between text-[#6b7280]">
            <span className="text-[11px] uppercase font-bold tracking-wider">Blood Pressure</span>
            <Activity className="h-4 w-4 text-[#111111]" />
          </div>
          <div className="text-xl sm:text-2xl font-bold text-[#111111] tracking-tight">
            {latestPoint?.systolic ? `${latestPoint.systolic} / ${latestPoint.diastolic}` : "134/86"}
            <span className="text-xs font-normal text-[#6b7280] ml-1">mmHg</span>
          </div>
          {bpEval && (
            <Badge 
              variant={bpEval.category === "critical" ? "critical" : bpEval.category === "warning" ? "warning" : "emerald"}
              size="sm"
            >
              {bpEval.label}
            </Badge>
          )}
        </div>

        {/* Heart Rate Card */}
        <div 
          onClick={() => {
            setActiveChartTab("other");
            setSelectedSubMetric("heartRate");
          }}
          className={`p-4 rounded-[12px] border cursor-pointer transition-all space-y-1 ${
            activeChartTab === "other" && selectedSubMetric === "heartRate"
              ? "bg-white border-[#e11d48] shadow-xs"
              : "bg-[#f8f9fa] border-[#e5e7eb] hover:bg-white"
          }`}
        >
          <div className="flex items-center justify-between text-[#6b7280]">
            <span className="text-[11px] uppercase font-bold tracking-wider">Resting Pulse</span>
            <Heart className="h-4 w-4 text-[#e11d48]" />
          </div>
          <div className="text-xl sm:text-2xl font-bold text-[#111111] tracking-tight">
            {latestPoint?.heartRate || 74}
            <span className="text-xs font-normal text-[#6b7280] ml-1">BPM</span>
          </div>
          <Badge variant="emerald" size="sm">Normal Resting</Badge>
        </div>

        {/* Oxygen Saturation Card */}
        <div 
          onClick={() => {
            setActiveChartTab("other");
            setSelectedSubMetric("spo2");
          }}
          className={`p-4 rounded-[12px] border cursor-pointer transition-all space-y-1 ${
            activeChartTab === "other" && selectedSubMetric === "spo2"
              ? "bg-white border-[#0284c7] shadow-xs"
              : "bg-[#f8f9fa] border-[#e5e7eb] hover:bg-white"
          }`}
        >
          <div className="flex items-center justify-between text-[#6b7280]">
            <span className="text-[11px] uppercase font-bold tracking-wider">Blood Oxygen</span>
            <Wind className="h-4 w-4 text-[#0284c7]" />
          </div>
          <div className="text-xl sm:text-2xl font-bold text-[#111111] tracking-tight">
            {latestPoint?.spo2 || 98}
            <span className="text-xs font-normal text-[#6b7280] ml-1">%</span>
          </div>
          <Badge variant="emerald" size="sm">SpO2 Optimal</Badge>
        </div>

        {/* Body Weight / BMI Card */}
        <div 
          onClick={() => {
            setActiveChartTab("other");
            setSelectedSubMetric("weight");
          }}
          className={`p-4 rounded-[12px] border cursor-pointer transition-all space-y-1 ${
            activeChartTab === "other" && selectedSubMetric === "weight"
              ? "bg-white border-[#059669] shadow-xs"
              : "bg-[#f8f9fa] border-[#e5e7eb] hover:bg-white"
          }`}
        >
          <div className="flex items-center justify-between text-[#6b7280]">
            <span className="text-[11px] uppercase font-bold tracking-wider">Weight & BMI</span>
            <Scale className="h-4 w-4 text-[#059669]" />
          </div>
          <div className="text-xl sm:text-2xl font-bold text-[#111111] tracking-tight">
            {latestPoint?.weight || 74.2}
            <span className="text-xs font-normal text-[#6b7280] ml-1">kg</span>
          </div>
          <Badge variant="emerald" size="sm">BMI: {latestPoint?.bmi || 24.2}</Badge>
        </div>
      </div>

      {/* 2. Chart Section with Tab Switcher */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex rounded-[8px] bg-[#f3f4f6] p-1 border border-[#e5e7eb] self-start">
            <button
              type="button"
              onClick={() => setActiveChartTab("bp")}
              className={`py-1.5 px-3.5 rounded-[6px] text-xs font-semibold flex items-center gap-1.5 transition-all ${
                activeChartTab === "bp"
                  ? "bg-white text-[#111111] shadow-xs"
                  : "text-[#6b7280] hover:text-[#111111]"
              }`}
            >
              <Activity className="h-3.5 w-3.5" />
              <span>Blood Pressure Chart (AHA)</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveChartTab("other")}
              className={`py-1.5 px-3.5 rounded-[6px] text-xs font-semibold flex items-center gap-1.5 transition-all ${
                activeChartTab === "other"
                  ? "bg-white text-[#111111] shadow-xs"
                  : "text-[#6b7280] hover:text-[#111111]"
              }`}
            >
              <Heart className="h-3.5 w-3.5" />
              <span>Pulse, SpO2 & Weight Trends</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={onOpenLogModal}
              className="flex items-center gap-1.5 text-xs"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Log Biometric Reading</span>
            </Button>
          </div>
        </div>

        {/* Render Active Chart Component */}
        {activeChartTab === "bp" ? (
          <BloodPressureChart 
            data={timeSeriesData} 
            onOpenLogModal={onOpenLogModal}
          />
        ) : (
          <VitalsMetricChart 
            data={timeSeriesData} 
            initialMetric={selectedSubMetric}
            onOpenLogModal={onOpenLogModal}
          />
        )}
      </div>

      {/* 3. Historical Observational Telemetry Table */}
      <div className="p-5 rounded-[16px] bg-white border border-[#e5e7eb] shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#f3f4f6]">
          <div>
            <h4 className="text-sm font-bold text-[#111111] tracking-tight">
              Observational Telemetry Log
            </h4>
            <p className="text-[11px] text-[#6b7280]">
              Raw clinical observation records formatted with LOINC taxonomy and HL7 FHIR attributes.
            </p>
          </div>
          <Badge variant="fhir" size="sm">HL7 FHIR Observation</Badge>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#e5e7eb] text-[#6b7280] uppercase text-[10px] font-bold tracking-wider">
                <th className="pb-2.5 font-bold">Observation Concept</th>
                <th className="pb-2.5 font-bold">LOINC Code</th>
                <th className="pb-2.5 font-bold">Value / Component</th>
                <th className="pb-2.5 font-bold">Interpretation</th>
                <th className="pb-2.5 font-bold">Date & Time</th>
                <th className="pb-2.5 text-right font-bold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f3f4f6]">
              {recordsList.map((rec) => {
                const badgeCfg = getVitalBadgeConfig(rec.interpretation);
                return (
                  <tr key={rec.id} className="hover:bg-[#f8f9fa] transition-colors">
                    <td className="py-2.5 font-semibold text-[#111111]">
                      {rec.code_display}
                    </td>
                    <td className="py-2.5 font-mono text-[11px] text-[#6b7280]">
                      {rec.code_value}
                    </td>
                    <td className="py-2.5 font-bold text-[#111111] font-mono">
                      {rec.components ? (
                        `${rec.components[0].value_quantity} / ${rec.components[1].value_quantity} ${rec.value_unit || "mmHg"}`
                      ) : (
                        `${rec.value_quantity} ${rec.value_unit}`
                      )}
                    </td>
                    <td className="py-2.5">
                      <Badge variant={badgeCfg.variant} size="sm">
                        {badgeCfg.label}
                      </Badge>
                    </td>
                    <td className="py-2.5 text-[#6b7280] text-[11px]">
                      {rec.effective_date_time}
                    </td>
                    <td className="py-2.5 text-right">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          onInspectFhir({
                            resourceType: "Observation",
                            id: rec.id,
                            status: "final",
                            category: [
                              {
                                coding: [
                                  {
                                    system: "http://terminology.hl7.org/CodeSystem/observation-category",
                                    code: "vital-signs",
                                    display: "Vital Signs",
                                  },
                                ],
                              },
                            ],
                            code: {
                              coding: [
                                {
                                  system: "http://loinc.org",
                                  code: rec.code_value,
                                  display: rec.code_display,
                                },
                              ],
                              text: rec.code_display,
                            },
                            subject: {
                              reference: `Patient/${rec.patient_id || "pat-arun-patel"}`,
                              display: "Arun Patel",
                            },
                            effectiveDateTime: rec.effective_date_time,
                            component: rec.components?.map((c: any) => ({
                              code: {
                                coding: [
                                  {
                                    system: "http://loinc.org",
                                    code: c.code_value,
                                    display: c.code_display,
                                  },
                                ],
                              },
                              valueQuantity: {
                                value: c.value_quantity,
                                unit: c.value_unit,
                              },
                            })),
                            valueQuantity: rec.value_quantity !== undefined ? {
                              value: rec.value_quantity,
                              unit: rec.value_unit,
                            } : undefined,
                            interpretation: [
                              {
                                coding: [
                                  {
                                    system: "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                                    code: rec.interpretation || "N",
                                    display: badgeCfg.label,
                                  },
                                ],
                              },
                            ],
                          });
                        }}
                        className="text-[11px] py-1 px-2.5 h-auto flex items-center gap-1 text-[#374151]"
                      >
                        <FileCode className="h-3 w-3 text-[#6b7280]" />
                        <span>FHIR</span>
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
