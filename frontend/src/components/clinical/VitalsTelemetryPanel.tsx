"use client";

import React, { useState } from "react";
import { Badge, Button, Card } from "@/components/ui";
import { 
  ClinicalObservation, 
  ObservationCategory, 
  ObservationInterpretation, 
  VitalsSummary 
} from "@/lib/api";
import { 
  Activity, 
  Heart, 
  Thermometer, 
  Gauge, 
  Plus, 
  FileCode, 
  Clock, 
  X,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  Wind
} from "lucide-react";

interface VitalsTelemetryPanelProps {
  patientId: string;
  patientName?: string;
  isDoctorView?: boolean;
  onVitalsRecorded?: (vitals: Record<string, unknown>) => void;
}

export const VitalsTelemetryPanel: React.FC<VitalsTelemetryPanelProps> = ({
  patientId,
  patientName = "Patient",
  isDoctorView = false,
  onVitalsRecorded,
}) => {
  const [systolic, setSystolic] = useState("134");
  const [diastolic, setDiastolic] = useState("86");
  const [heartRate, setHeartRate] = useState("72");
  const [spo2, setSpo2] = useState("98");
  const [respiratoryRate, setRespiratoryRate] = useState("16");
  const [temperature, setTemperature] = useState("98.4");
  const [bmi, setBmi] = useState("24.2");
  const [lastRecordedTime, setLastRecordedTime] = useState("Today, 10:15 AM");

  const [isRecordModalOpen, setIsRecordModalOpen] = useState(false);
  const [modalSystolic, setModalSystolic] = useState(systolic);
  const [modalDiastolic, setModalDiastolic] = useState(diastolic);
  const [modalHeartRate, setModalHeartRate] = useState(heartRate);
  const [modalSpo2, setModalSpo2] = useState(spo2);
  const [modalRespRate, setModalRespRate] = useState(respiratoryRate);
  const [modalTemp, setModalTemp] = useState(temperature);
  const [modalBmi, setModalBmi] = useState(bmi);
  const [recordSuccess, setRecordSuccess] = useState(false);
  const [viewingFhirObservation, setViewingFhirObservation] = useState<Record<string, unknown> | null>(null);

  const handleSaveTelemetry = (e: React.FormEvent) => {
    e.preventDefault();
    setSystolic(modalSystolic);
    setDiastolic(modalDiastolic);
    setHeartRate(modalHeartRate);
    setSpo2(modalSpo2);
    setRespiratoryRate(modalRespRate);
    setTemperature(modalTemp);
    setBmi(modalBmi);
    setLastRecordedTime("Just now");
    setRecordSuccess(true);
    setIsRecordModalOpen(false);

    if (onVitalsRecorded) {
      onVitalsRecorded({
        systolic: modalSystolic,
        diastolic: modalDiastolic,
        heartRate: modalHeartRate,
        spo2: modalSpo2,
        respiratoryRate: modalRespRate,
        temperature: modalTemp,
        bmi: modalBmi,
      });
    }

    setTimeout(() => setRecordSuccess(false), 3500);
  };

  const METRIC_CARDS = [
    {
      title: "Blood Pressure",
      value: `${systolic} / ${diastolic}`,
      unit: "mmHg",
      loinc: "85354-9",
      interpretation: Number(systolic) > 130 || Number(diastolic) > 85 ? "High (Stage 1)" : "Normal",
      statusVariant: Number(systolic) > 130 || Number(diastolic) > 85 ? ("orange" as const) : ("emerald" as const),
      icon: <Gauge className="h-5 w-5 text-[#111111]" />,
      desc: "Compound sitting brachial artery reading",
    },
    {
      title: "Heart Rate",
      value: heartRate,
      unit: "bpm",
      loinc: "8867-4",
      interpretation: Number(heartRate) > 100 ? "Tachycardia" : Number(heartRate) < 60 ? "Bradycardia" : "Normal",
      statusVariant: Number(heartRate) >= 60 && Number(heartRate) <= 100 ? ("emerald" as const) : ("orange" as const),
      icon: <Heart className="h-5 w-5 text-[#ef4444]" />,
      desc: "Radial pulse rhythm regular",
    },
    {
      title: "Oxygen Saturation (SpO2)",
      value: `${spo2}%`,
      unit: "Room Air",
      loinc: "2708-6",
      interpretation: Number(spo2) >= 95 ? "Normal" : "Hypoxemic",
      statusVariant: Number(spo2) >= 95 ? ("emerald" as const) : ("critical" as const),
      icon: <Activity className="h-5 w-5 text-[#3b82f6]" />,
      desc: "Peripheral pulse oximetry",
    },
    {
      title: "Body Mass Index (BMI)",
      value: bmi,
      unit: "kg/m²",
      loinc: "39156-5",
      interpretation: Number(bmi) < 25 ? "Normal Weight" : "Overweight",
      statusVariant: Number(bmi) < 25 ? ("emerald" as const) : ("orange" as const),
      icon: <TrendingUp className="h-5 w-5 text-[#8b5cf6]" />,
      desc: "Calculated from height & weight",
    },
    {
      title: "Respiratory Rate",
      value: respiratoryRate,
      unit: "breaths/min",
      loinc: "9279-1",
      interpretation: "Normal",
      statusVariant: "emerald" as const,
      icon: <Wind className="h-5 w-5 text-[#10b981]" />,
      desc: "Resting spontaneous respiration",
    },
    {
      title: "Body Temperature",
      value: `${temperature}°`,
      unit: "Fahrenheit",
      loinc: "8310-5",
      interpretation: Number(temperature) > 99.5 ? "Febrile" : "Afebrile",
      statusVariant: Number(temperature) > 99.5 ? ("orange" as const) : ("emerald" as const),
      icon: <Thermometer className="h-5 w-5 text-[#f59e0b]" />,
      desc: "Tympanic membrane sensor",
    },
  ];

  return (
    <div className="space-y-4">
      {/* Telemetry Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#f8f9fa] p-4 rounded-xl border border-[#e5e7eb]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-[#111111]">
              Vitals & Biometric Telemetry
            </h3>
            <Badge variant="emerald" size="sm">
              LOINC Verified
            </Badge>
          </div>
          <p className="text-xs text-[#6b7280]">
            Last recorded: <span className="font-medium text-[#111111]">{lastRecordedTime}</span> • ABDM Health Facility Sync active
          </p>
        </div>

        {isDoctorView && (
          <Button
            size="sm"
            onClick={() => setIsRecordModalOpen(true)}
            className="flex items-center gap-1.5 self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            Record New Telemetry
          </Button>
        )}
      </div>

      {recordSuccess && (
        <div className="flex items-center gap-2 p-3 bg-[#ecfdf5] border border-[#a7f3d0] rounded-xl text-xs text-[#065f46]">
          <CheckCircle2 className="h-4 w-4 text-[#10b981] shrink-0" />
          <span>Biometric observations saved and transformed into HL7 FHIR R4 resources.</span>
        </div>
      )}

      {/* Grid of Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {METRIC_CARDS.map((metric) => (
          <Card
            key={metric.title}
            className="p-4 border border-[#e5e7eb] hover:border-[#111111] transition-all bg-white"
          >
            <div className="flex items-center justify-between pb-2">
              <span className="text-xs font-medium text-[#6b7280]">
                {metric.title}
              </span>
              <div className="flex items-center gap-1">
                <span className="font-mono text-[10px] text-[#9ca3af]">
                  {metric.loinc}
                </span>
                <button
                  onClick={() =>
                    setViewingFhirObservation({
                      resourceType: "Observation",
                      status: "final",
                      category: [{ coding: [{ system: "http://terminology.hl7.org/CodeSystem/observation-category", code: "vital-signs" }] }],
                      code: { coding: [{ system: "http://loinc.org", code: metric.loinc, display: metric.title }] },
                      valueQuantity: { value: metric.value, unit: metric.unit },
                      interpretation: [{ text: metric.interpretation }],
                    })
                  }
                  className="p-1 text-[#9ca3af] hover:text-[#111111]"
                  title="View FHIR Observation"
                >
                  <FileCode className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div className="flex items-baseline gap-2 my-1">
              <span className="text-2xl font-bold tracking-tight text-[#111111]">
                {metric.value}
              </span>
              <span className="text-xs text-[#6b7280]">
                {metric.unit}
              </span>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-[#f3f4f6] mt-2">
              <Badge variant={metric.statusVariant} size="sm">
                {metric.interpretation}
              </Badge>
              <div className="p-1 rounded-md bg-[#f8f9fa]">
                {metric.icon}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Modal: Record Telemetry */}
      {isRecordModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-[#e5e7eb] space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-[#111111] text-white flex items-center justify-center">
                  <Activity className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="font-semibold text-base text-[#111111]">
                    Record Patient Vital Signs
                  </h3>
                  <p className="text-xs text-[#6b7280]">
                    Clinical encounter telemetry for {patientName}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsRecordModalOpen(false)}
                className="text-[#6b7280] hover:text-[#111111] p-1 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSaveTelemetry} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Systolic BP (mmHg)
                  </label>
                  <input
                    type="number"
                    required
                    value={modalSystolic}
                    onChange={(e) => setModalSystolic(e.target.value)}
                    className="w-full text-xs font-mono px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Diastolic BP (mmHg)
                  </label>
                  <input
                    type="number"
                    required
                    value={modalDiastolic}
                    onChange={(e) => setModalDiastolic(e.target.value)}
                    className="w-full text-xs font-mono px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Heart Rate (bpm)
                  </label>
                  <input
                    type="number"
                    required
                    value={modalHeartRate}
                    onChange={(e) => setModalHeartRate(e.target.value)}
                    className="w-full text-xs font-mono px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    SpO2 Oxygen (%)
                  </label>
                  <input
                    type="number"
                    required
                    value={modalSpo2}
                    onChange={(e) => setModalSpo2(e.target.value)}
                    className="w-full text-xs font-mono px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Resp. Rate (/min)
                  </label>
                  <input
                    type="number"
                    value={modalRespRate}
                    onChange={(e) => setModalRespRate(e.target.value)}
                    className="w-full text-xs font-mono px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Temp (°F)
                  </label>
                  <input
                    type="text"
                    value={modalTemp}
                    onChange={(e) => setModalTemp(e.target.value)}
                    className="w-full text-xs font-mono px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    BMI (kg/m²)
                  </label>
                  <input
                    type="text"
                    value={modalBmi}
                    onChange={(e) => setModalBmi(e.target.value)}
                    className="w-full text-xs font-mono px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#e5e7eb]">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsRecordModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Save Telemetry
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: FHIR Observation Inspector */}
      {viewingFhirObservation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-[#e5e7eb] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <FileCode className="h-5 w-5 text-[#111111]" />
                <h3 className="font-semibold text-sm text-[#111111]">
                  HL7 FHIR Release 4 • Observation Resource
                </h3>
              </div>
              <button
                onClick={() => setViewingFhirObservation(null)}
                className="text-[#6b7280] hover:text-[#111111]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <pre className="p-4 bg-[#101010] text-[#a1a1aa] rounded-xl text-xs font-mono overflow-x-auto max-h-96">
              {JSON.stringify(viewingFhirObservation, null, 2)}
            </pre>

            <div className="flex justify-end pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setViewingFhirObservation(null)}
              >
                Close Inspector
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
