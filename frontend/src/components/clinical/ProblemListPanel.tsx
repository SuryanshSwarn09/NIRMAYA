"use client";

import React, { useState } from "react";
import { Badge, Button, Card, CardTitle, CardDescription } from "@/components/ui";
import { 
  ClinicalCondition, 
  ClinicalStatus, 
  VerificationStatus, 
  ConditionSeverity, 
  ConditionCategory 
} from "@/lib/api";
import { 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  FileCode, 
  Plus, 
  ShieldCheck, 
  Stethoscope, 
  X,
  Activity,
  Calendar,
  Sparkles
} from "lucide-react";

interface ProblemListPanelProps {
  patientId: string;
  patientName?: string;
  isDoctorView?: boolean;
  initialConditions?: ClinicalCondition[];
  onConditionAdded?: (condition: Partial<ClinicalCondition>) => void;
}

const COMMON_CONDITION_PRESETS = [
  {
    code: "I10",
    display: "Essential (primary) hypertension",
    system: "http://hl7.org/fhir/sid/icd-10",
    category: "problem-list-item" as ConditionCategory,
    severity: "moderate" as ConditionSeverity,
  },
  {
    code: "E11.9",
    display: "Type 2 diabetes mellitus without complications",
    system: "http://hl7.org/fhir/sid/icd-10",
    category: "chronic-condition" as ConditionCategory,
    severity: "moderate" as ConditionSeverity,
  },
  {
    code: "E78.5",
    display: "Hyperlipidemia, unspecified",
    system: "http://hl7.org/fhir/sid/icd-10",
    category: "problem-list-item" as ConditionCategory,
    severity: "mild" as ConditionSeverity,
  },
  {
    code: "I25.10",
    display: "Atherosclerotic heart disease of native coronary artery",
    system: "http://hl7.org/fhir/sid/icd-10",
    category: "chronic-condition" as ConditionCategory,
    severity: "severe" as ConditionSeverity,
  },
  {
    code: "J45.909",
    display: "Unspecified asthma, uncomplicated",
    system: "http://hl7.org/fhir/sid/icd-10",
    category: "problem-list-item" as ConditionCategory,
    severity: "mild" as ConditionSeverity,
  },
];

export const ProblemListPanel: React.FC<ProblemListPanelProps> = ({
  patientId,
  patientName = "Patient",
  isDoctorView = false,
  initialConditions,
  onConditionAdded,
}) => {
  const [conditions, setConditions] = useState<ClinicalCondition[]>(
    initialConditions || [
      {
        id: "cond-101",
        patient_id: patientId,
        clinical_status: "active",
        verification_status: "confirmed",
        category: "problem-list-item",
        severity: "moderate",
        code_coding_system: "http://hl7.org/fhir/sid/icd-10",
        code_value: "I10",
        code_display: "Essential (primary) hypertension",
        onset_date_time: "2024-03-15T09:00:00Z",
        note: "Baseline BP consistently 138-142 / 88-92 mmHg. Lifestyle and dietary intervention ongoing.",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: "cond-102",
        patient_id: patientId,
        clinical_status: "active",
        verification_status: "confirmed",
        category: "problem-list-item",
        severity: "mild",
        code_coding_system: "http://hl7.org/fhir/sid/icd-10",
        code_value: "E78.5",
        code_display: "Hyperlipidemia, unspecified",
        onset_date_time: "2024-06-10T11:30:00Z",
        note: "Elevated fasting triglycerides and direct LDL. On low-dose statin therapy.",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]
  );

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedPresetIndex, setSelectedPresetIndex] = useState(0);
  const [customCode, setCustomCode] = useState(COMMON_CONDITION_PRESETS[0].code);
  const [customDisplay, setCustomDisplay] = useState(COMMON_CONDITION_PRESETS[0].display);
  const [severity, setSeverity] = useState<ConditionSeverity>("moderate");
  const [clinicalStatus, setClinicalStatus] = useState<ClinicalStatus>("active");
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus>("confirmed");
  const [note, setNote] = useState("");
  const [viewingFhirCondition, setViewingFhirCondition] = useState<ClinicalCondition | null>(null);

  const handleSelectPreset = (index: number) => {
    setSelectedPresetIndex(index);
    const p = COMMON_CONDITION_PRESETS[index];
    setCustomCode(p.code);
    setCustomDisplay(p.display);
    setSeverity(p.severity);
  };

  const handleAddCondition = (e: React.FormEvent) => {
    e.preventDefault();
    const newCond: ClinicalCondition = {
      id: `cond-${Date.now().toString().slice(-4)}`,
      patient_id: patientId,
      clinical_status: clinicalStatus,
      verification_status: verificationStatus,
      category: "problem-list-item",
      severity,
      code_coding_system: "http://hl7.org/fhir/sid/icd-10",
      code_value: customCode,
      code_display: customDisplay,
      onset_date_time: new Date().toISOString(),
      note: note || undefined,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setConditions((prev) => [newCond, ...prev]);
    if (onConditionAdded) {
      onConditionAdded(newCond);
    }
    setIsAddModalOpen(false);
    setNote("");
  };

  const handleResolveCondition = (condId: string) => {
    setConditions((prev) =>
      prev.map((c) => (c.id === condId ? { ...c, clinical_status: "resolved" } : c))
    );
  };

  return (
    <div className="space-y-4">
      {/* Panel Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#f8f9fa] p-4 rounded-xl border border-[#e5e7eb]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-[#111111]">
              Longitudinal Problem List
            </h3>
            <Badge variant="neutral" size="sm">
              {conditions.filter((c) => c.clinical_status === "active").length} Active
            </Badge>
          </div>
          <p className="text-xs text-[#6b7280]">
            HL7 FHIR R4 Condition profile & ICD-10 diagnostic classifications
          </p>
        </div>

        {isDoctorView && (
          <Button
            size="sm"
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-1.5 self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            Add Diagnosed Condition
          </Button>
        )}
      </div>

      {/* Condition Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {conditions.map((cond) => {
          const isActive = cond.clinical_status === "active";
          return (
            <Card
              key={cond.id}
              className={`p-4 transition-all duration-200 border ${
                isActive ? "border-[#e5e7eb] hover:border-[#111111]" : "border-[#e5e7eb] opacity-75 bg-[#fcfcfc]"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-[#111111] text-white">
                      {cond.code_value}
                    </span>
                    <Badge
                      variant={
                        cond.severity === "severe"
                          ? "critical"
                          : cond.severity === "moderate"
                          ? "orange"
                          : "default"
                      }
                      size="sm"
                    >
                      {cond.severity || "mild"}
                    </Badge>
                    <Badge
                      variant={isActive ? "emerald" : "neutral"}
                      size="sm"
                    >
                      {cond.clinical_status}
                    </Badge>
                  </div>
                  <h4 className="text-sm font-semibold text-[#111111] leading-tight">
                    {cond.code_display}
                  </h4>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setViewingFhirCondition(cond)}
                  title="View HL7 FHIR R4 JSON"
                  className="p-1 h-8 w-8 text-[#6b7280] hover:text-[#111111]"
                >
                  <FileCode className="h-4 w-4" />
                </Button>
              </div>

              {cond.note && (
                <p className="text-xs text-[#4b5563] mt-2.5 pt-2.5 border-t border-[#f3f4f6] line-clamp-2">
                  {cond.note}
                </p>
              )}

              <div className="flex items-center justify-between mt-3 pt-2 text-[11px] text-[#6b7280] border-t border-[#f3f4f6]">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Onset: {cond.onset_date_time ? new Date(cond.onset_date_time).toLocaleDateString() : "Undated"}
                </span>
                
                {isDoctorView && isActive && (
                  <button
                    onClick={() => handleResolveCondition(cond.id)}
                    className="text-[11px] font-medium text-[#6b7280] hover:text-[#111111] underline underline-offset-2"
                  >
                    Mark Resolved
                  </button>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Modal: Add Condition */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-[#e5e7eb] space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-[#111111] text-white flex items-center justify-center">
                  <Stethoscope className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="font-semibold text-base text-[#111111]">
                    Record Clinical Condition
                  </h3>
                  <p className="text-xs text-[#6b7280]">
                    Appending to patient {patientName}&apos;s longitudinal problem list
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-[#6b7280] hover:text-[#111111] p-1 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAddCondition} className="space-y-4">
              {/* Presets Selector */}
              <div>
                <label className="block text-xs font-medium text-[#374151] mb-1.5">
                  Standard ICD-10 Diagnostic Presets
                </label>
                <div className="grid grid-cols-1 gap-1.5 max-h-36 overflow-y-auto p-1 bg-[#f9fafb] rounded-lg border border-[#e5e7eb]">
                  {COMMON_CONDITION_PRESETS.map((p, idx) => (
                    <button
                      key={p.code}
                      type="button"
                      onClick={() => handleSelectPreset(idx)}
                      className={`text-left p-2 rounded text-xs transition-all flex items-center justify-between ${
                        selectedPresetIndex === idx
                          ? "bg-[#111111] text-white font-medium"
                          : "hover:bg-[#f3f4f6] text-[#374151]"
                      }`}
                    >
                      <span>{p.display}</span>
                      <span className="font-mono text-[10px] opacity-80">{p.code}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Diagnostic Details */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    ICD-10 Code
                  </label>
                  <input
                    type="text"
                    required
                    value={customCode}
                    onChange={(e) => setCustomCode(e.target.value)}
                    className="w-full text-xs font-mono px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Severity Assessment
                  </label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value as ConditionSeverity)}
                    className="w-full text-xs px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111] bg-white"
                  >
                    <option value="mild">Mild</option>
                    <option value="moderate">Moderate</option>
                    <option value="severe">Severe</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#374151] mb-1">
                  Diagnosis Display Name
                </label>
                <input
                  type="text"
                  required
                  value={customDisplay}
                  onChange={(e) => setCustomDisplay(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111]"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[#374151] mb-1">
                  Clinical Commentary / Diagnostic Rationale
                </label>
                <textarea
                  rows={2}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="e.g. Diagnosed following ambulatory BP monitoring. Initiating ACE inhibitor therapy."
                  className="w-full text-xs px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#e5e7eb]">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsAddModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Record Diagnosis
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: FHIR Export Inspector */}
      {viewingFhirCondition && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-[#e5e7eb] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <FileCode className="h-5 w-5 text-[#111111]" />
                <h3 className="font-semibold text-sm text-[#111111]">
                  HL7 FHIR Release 4 • Condition Resource
                </h3>
              </div>
              <button
                onClick={() => setViewingFhirCondition(null)}
                className="text-[#6b7280] hover:text-[#111111]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <pre className="p-4 bg-[#101010] text-[#a1a1aa] rounded-xl text-xs font-mono overflow-x-auto max-h-96">
              {JSON.stringify(
                {
                  resourceType: "Condition",
                  id: viewingFhirCondition.id,
                  clinicalStatus: {
                    coding: [
                      {
                        system: "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        code: viewingFhirCondition.clinical_status,
                      },
                    ],
                  },
                  verificationStatus: {
                    coding: [
                      {
                        system: "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        code: viewingFhirCondition.verification_status,
                      },
                    ],
                  },
                  code: {
                    coding: [
                      {
                        system: viewingFhirCondition.code_coding_system,
                        code: viewingFhirCondition.code_value,
                        display: viewingFhirCondition.code_display,
                      },
                    ],
                    text: viewingFhirCondition.code_display,
                  },
                  subject: {
                    reference: `Patient/${viewingFhirCondition.patient_id}`,
                    type: "Patient",
                  },
                  onsetDateTime: viewingFhirCondition.onset_date_time,
                  note: viewingFhirCondition.note
                    ? [{ text: viewingFhirCondition.note }]
                    : undefined,
                },
                null,
                2
              )}
            </pre>

            <div className="flex justify-end pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setViewingFhirCondition(null)}
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
