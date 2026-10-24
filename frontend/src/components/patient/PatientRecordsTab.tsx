"use client";

import React, { useState } from "react";
import { 
  Card, 
  CardTitle, 
  CardDescription, 
  Badge, 
  Button 
} from "@/components/ui";
import { 
  Activity, 
  Plus, 
  Download, 
  CheckCircle2, 
  FlaskConical, 
  Calendar, 
  FileText, 
  Clock 
} from "lucide-react";
import { VitalsTimeSeriesPoint } from "@/lib/vitals";
import { PatientVitalsTelemetry } from "./PatientVitalsTelemetry";

export interface PatientRecordsTabProps {
  vitalsList: any[];
  timeSeriesData?: VitalsTimeSeriesPoint[];
  patientLabReports: any[];
  patientLabOrders: any[];
  onOpenLogVitals: () => void;
  onInspectFhir: (fhirResource: any) => void;
}

export function PatientRecordsTab({
  vitalsList,
  timeSeriesData = [],
  patientLabReports,
  patientLabOrders,
  onOpenLogVitals,
  onInspectFhir,
}: PatientRecordsTabProps) {
  const [labSectionTab, setLabSectionTab] = useState<"reports" | "orders">("reports");

  return (
    <div className="animate-fade-in max-w-5xl mx-auto space-y-6">

      {/* 1. Vital Signs & Clinical Telemetry Dashboard */}
      <PatientVitalsTelemetry
        timeSeriesData={timeSeriesData}
        recordsList={vitalsList}
        onOpenLogModal={onOpenLogVitals}
        onInspectFhir={onInspectFhir}
      />

      {/* 2. Clinical Encounter Documentation & SOAP Notes */}
      <Card variant="mockup" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#e5e7eb] gap-2">
          <div>
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-[#111111]" />
              <CardTitle className="text-lg">Clinical Consultation Notes (SOAP)</CardTitle>
              <Badge variant="verified">FHIR Composition</Badge>
            </div>
            <CardDescription className="mt-1">
              Structured clinical encounter notes authored and signed by attending physicians.
            </CardDescription>
          </div>
          <Badge variant="abdm" size="sm">CareContext Linkable</Badge>
        </div>

        <div className="p-4 rounded-[8px] border border-[#e5e7eb] bg-[#f8f9fa] space-y-3 text-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#e5e7eb] pb-2.5">
            <div>
              <span className="font-bold text-sm text-[#111111]">
                Cardiology Outpatient Consultation
              </span>
              <span className="text-xs text-[#6b7280] block sm:inline sm:ml-2">
                by <span className="font-semibold text-[#111111]">Dr. Ananya Sharma</span> (Chief Cardiologist, AIIMS)
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="verified" size="sm">Signed & Final</Badge>
              <span className="font-mono text-[11px] text-[#6b7280]">Today, 10:30 AM</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-[6px] bg-white border border-[#e5e7eb]">
              <span className="text-[#6b7280] block text-[10px] font-semibold uppercase tracking-wider">
                Chief Complaint (LOINC 10154-3)
              </span>
              <p className="text-[#111111] font-medium mt-0.5">
                Exertional dyspnea and morning fatigue during cardiac rehabilitation
              </p>
            </div>
            <div className="p-2.5 rounded-[6px] bg-white border border-[#e5e7eb]">
              <span className="text-[#6b7280] block text-[10px] font-semibold uppercase tracking-wider">
                Primary Diagnosis (ICD-10)
              </span>
              <p className="text-[#111111] font-mono font-medium mt-0.5">
                I10 - Essential (primary) hypertension
              </p>
            </div>
          </div>

          {/* 4 SOAP Blocks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-[6px] bg-white border border-[#e5e7eb] space-y-1">
              <span className="font-semibold text-[#111111] flex items-center gap-1">
                <span className="text-[#059669] font-bold">[S]</span> Subjective (LOINC 61150-9)
              </span>
              <p className="text-[#6b7280]">
                Patient reports mild exertional shortness of breath when climbing 2 flights of stairs. Compliant with antihypertensives.
              </p>
            </div>
            <div className="p-2.5 rounded-[6px] bg-white border border-[#e5e7eb] space-y-1">
              <span className="font-semibold text-[#111111] flex items-center gap-1">
                <span className="text-[#0284c7] font-bold">[O]</span> Objective (LOINC 61149-1)
              </span>
              <p className="text-[#6b7280]">
                BP 134/86 mmHg, HR 72 bpm regular rhythm, SpO2 98% room air. Dual heart sounds S1 S2 present, no murmurs.
              </p>
            </div>
            <div className="p-2.5 rounded-[6px] bg-white border border-[#e5e7eb] space-y-1">
              <span className="font-semibold text-[#111111] flex items-center gap-1">
                <span className="text-[#d97706] font-bold">[A]</span> Assessment (LOINC 51848-0)
              </span>
              <p className="text-[#6b7280]">
                Essential hypertension, well-compensated. Exertional Dyspnea NYHA Class I-II, stable.
              </p>
            </div>
            <div className="p-2.5 rounded-[6px] bg-white border border-[#e5e7eb] space-y-1">
              <span className="font-semibold text-[#111111] flex items-center gap-1">
                <span className="text-[#7c3aed] font-bold">[P]</span> Plan (LOINC 18776-5)
              </span>
              <p className="text-[#6b7280]">
                Continue Atorvastatin 20mg nocte and Amlodipine. Requisition 12-lead ECG and Lipid Panel. Follow-up in 4 weeks.
              </p>
            </div>
          </div>

          <div className="pt-2 border-t border-[#e5e7eb] flex items-center justify-between text-[11px]">
            <span className="font-mono text-[#059669] flex items-center gap-1">
              <CheckCircle2 className="h-3.5 w-3.5" />
              SHA-256 Attestation: 7f83b165...9069
            </span>
            <button
              type="button"
              onClick={() => {
                onInspectFhir({
                  resourceType: "Composition",
                  id: "comp-cardio-01",
                  status: "final",
                  type: {
                    coding: [
                      {
                        system: "http://loinc.org",
                        code: "11506-3",
                        display: "Provider-unspecified Progress note",
                      },
                    ],
                    text: "Cardiology Outpatient Consultation",
                  },
                  subject: { reference: "Patient/pat-arun-patel", display: "Arun Patel" },
                  author: [{ reference: "Practitioner/doc-ananya-sharma", display: "Dr. Ananya Sharma" }],
                  section: [
                    {
                      title: "Chief Complaint",
                      code: { coding: [{ system: "http://loinc.org", code: "10154-3" }] },
                      text: { status: "generated", div: "<div>Exertional dyspnea and morning fatigue</div>" },
                    },
                    {
                      title: "Subjective",
                      code: { coding: [{ system: "http://loinc.org", code: "61150-9" }] },
                      text: { status: "generated", div: "<div>Patient reports mild exertional shortness of breath.</div>" },
                    },
                    {
                      title: "Objective",
                      code: { coding: [{ system: "http://loinc.org", code: "61149-1" }] },
                      text: { status: "generated", div: "<div>BP 134/86 mmHg, HR 72 bpm, SpO2 98%.</div>" },
                    },
                    {
                      title: "Assessment",
                      code: { coding: [{ system: "http://loinc.org", code: "51848-0" }] },
                      text: { status: "generated", div: "<div>Essential hypertension, well-compensated.</div>" },
                    },
                    {
                      title: "Plan",
                      code: { coding: [{ system: "http://loinc.org", code: "18776-5" }] },
                      text: { status: "generated", div: "<div>Continue Atorvastatin 20mg nocte and Amlodipine.</div>" },
                    },
                  ],
                });
              }}
              className="font-semibold text-[#111111] hover:underline flex items-center gap-1 cursor-pointer"
            >
              <Download className="h-3 w-3" />
              Inspect FHIR Composition
            </button>
          </div>
        </div>
      </Card>

      {/* 3. Diagnostic Lab Reports & Service Requests */}
      <Card variant="mockup" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#e5e7eb] gap-2">
          <div>
            <div className="flex items-center gap-2">
              <FlaskConical className="h-5 w-5 text-[#111111]" />
              <CardTitle className="text-lg">Diagnostic Lab Reports & Requisitions</CardTitle>
              <Badge variant="verified">LOINC & FHIR R4</Badge>
            </div>
            <CardDescription className="mt-1">
              Quantitative laboratory findings, automated abnormal flags, and clinician test orders.
            </CardDescription>
          </div>
          <div className="flex items-center gap-1 bg-[#f3f4f6] p-1 rounded-lg">
            <button
              type="button"
              onClick={() => setLabSectionTab("reports")}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                labSectionTab === "reports"
                  ? "bg-white text-[#111111] shadow-xs"
                  : "text-[#6b7280] hover:text-[#111111]"
              }`}
            >
              Reports ({patientLabReports.length})
            </button>
            <button
              type="button"
              onClick={() => setLabSectionTab("orders")}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                labSectionTab === "orders"
                  ? "bg-white text-[#111111] shadow-xs"
                  : "text-[#6b7280] hover:text-[#111111]"
              }`}
            >
              Orders ({patientLabOrders.length})
            </button>
          </div>
        </div>

        {/* VIEW 1: Lab Reports */}
        {labSectionTab === "reports" && (
          <div className="space-y-4">
            {patientLabReports.map((report) => (
              <div
                key={report.id}
                className="p-4 rounded-[8px] border border-[#e5e7eb] bg-[#f8f9fa] space-y-3 text-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#e5e7eb] pb-2.5">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-[#111111]">{report.title}</span>
                      <Badge variant={report.is_abnormal ? "critical" : "emerald"} size="sm">
                        {report.is_abnormal ? "ABNORMAL / ELEVATED" : "NORMAL"}
                      </Badge>
                    </div>
                    <span className="text-xs text-[#6b7280] mt-0.5 block">
                      Performed by <span className="font-semibold text-[#111111]">{report.performer}</span>
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="verified" size="sm">{report.status.toUpperCase()}</Badge>
                    <span className="font-mono text-[11px] text-[#6b7280]">{report.issued_date_time}</span>
                  </div>
                </div>

                {/* Diagnostic Interpretation Banner */}
                <div className="p-2.5 rounded-[6px] bg-white border border-[#e5e7eb] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold text-[#6b7280] tracking-wider">
                      Pathologist Conclusion & Coding
                    </span>
                    <span className="font-mono text-[11px] text-[#b91c1c] font-semibold bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                      ICD-10: {report.coded_diagnosis_icd10}
                    </span>
                  </div>
                  <p className="text-xs text-[#111111] font-medium">
                    {report.conclusion}
                  </p>
                </div>

                {/* Observations Grid */}
                <div className="space-y-1.5">
                  <span className="text-[10px] uppercase font-bold text-[#6b7280] tracking-wider block">
                    Calibrated Quantitative Observations ({report.observations.length})
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                    {report.observations.map((obs: any) => {
                      const isHigh = obs.interpretation === "high";
                      return (
                        <div
                          key={obs.code_value}
                          className={`p-2.5 rounded-[6px] border text-xs space-y-1 ${
                            isHigh
                              ? "bg-rose-50/60 border-rose-200 text-[#881337]"
                              : "bg-white border-[#e5e7eb] text-[#111111]"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-mono text-[#6b7280]">
                              LOINC {obs.code_value}
                            </span>
                            <Badge variant={isHigh ? "critical" : "emerald"} size="sm">
                              {obs.interpretation.toUpperCase()}
                            </Badge>
                          </div>
                          <div className="font-semibold text-xs truncate" title={obs.code_display}>
                            {obs.code_display}
                          </div>
                          <div className="flex items-baseline justify-between pt-0.5">
                            <span className="font-bold text-sm">
                              {obs.value_quantity}{" "}
                              <span className="text-[11px] font-normal opacity-75">{obs.value_unit}</span>
                            </span>
                            <span className="text-[10px] text-[#6b7280] font-mono">
                              {obs.reference_range_text}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Footer & FHIR inspection */}
                <div className="pt-2 border-t border-[#e5e7eb] flex items-center justify-between text-[11px]">
                  <span className="font-mono text-[#059669] flex items-center gap-1">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Order Linked: {report.order_id}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      onInspectFhir({
                        resourceType: "DiagnosticReport",
                        id: report.id,
                        meta: {
                          profile: ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/DiagnosticReportLab"],
                        },
                        status: report.status,
                        category: [
                          {
                            coding: [
                              { system: "http://terminology.hl7.org/CodeSystem/v2-0074", code: "LAB", display: "Laboratory" },
                            ],
                          },
                        ],
                        code: {
                          coding: [
                            { system: "http://loinc.org", code: report.code_value, display: report.code_display },
                          ],
                          text: report.title,
                        },
                        subject: { reference: "Patient/pat-arun-patel", display: "Arun Patel" },
                        effectiveDateTime: new Date().toISOString(),
                        issued: new Date().toISOString(),
                        performer: [{ reference: "Organization/HFR-DEL-91024", display: report.performer }],
                        basedOn: [{ reference: `ServiceRequest/${report.order_id}` }],
                        result: report.observations.map((o: any) => ({
                          reference: `Observation/loinc-${o.code_value}`,
                          display: `${o.code_display}: ${o.value_quantity} ${o.value_unit}`,
                        })),
                        conclusion: report.conclusion,
                        conclusionCode: [
                          {
                            coding: [
                              { system: "http://hl7.org/fhir/sid/icd-10", code: "E78.5", display: "Hyperlipidemia, unspecified" },
                            ],
                          },
                        ],
                      });
                    }}
                    className="font-semibold text-[#111111] hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <Download className="h-3 w-3" />
                    Inspect FHIR DiagnosticReport
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* VIEW 2: Doctor Requisitions */}
        {labSectionTab === "orders" && (
          <div className="space-y-3">
            {patientLabOrders.map((ord) => (
              <div
                key={ord.id}
                className="p-4 rounded-[8px] border border-[#e5e7eb] bg-[#f8f9fa] space-y-2 text-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 border-b border-[#e5e7eb] pb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#111111]">{ord.code_display}</span>
                    <Badge variant="emerald" size="sm">{ord.status.toUpperCase()}</Badge>
                    {ord.fasting_required && (
                      <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-medium">
                        Fasting Required
                      </span>
                    )}
                  </div>
                  <span className="font-mono text-[11px] text-[#6b7280]">{ord.authored_on}</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-[#6b7280]">Ordering Clinician:</span>{" "}
                    <span className="font-semibold text-[#111111]">{ord.doctor_name}</span>
                  </div>
                  <div>
                    <span className="text-[#6b7280]">Specimen Protocol:</span>{" "}
                    <span className="capitalize font-medium text-[#111111]">{ord.specimen_type}</span>
                  </div>
                  <div className="sm:col-span-2">
                    <span className="text-[#6b7280]">Indication:</span> {ord.reason_display}
                  </div>
                </div>

                <div className="pt-2 border-t border-[#e5e7eb] flex items-center justify-between text-[11px]">
                  <span className="font-mono text-[#059669]">Requisition ID: {ord.id}</span>
                  <button
                    type="button"
                    onClick={() => {
                      onInspectFhir({
                        resourceType: "ServiceRequest",
                        id: ord.id,
                        status: ord.status,
                        intent: "order",
                        priority: ord.priority,
                        code: {
                          coding: [
                            { system: "http://loinc.org", code: ord.code_value, display: ord.code_display },
                          ],
                        },
                        subject: { reference: "Patient/pat-arun-patel", display: "Arun Patel" },
                        requester: { reference: "Practitioner/doc-ananya-sharma", display: ord.doctor_name },
                        authoredOn: new Date().toISOString(),
                        reasonCode: [{ text: ord.reason_display }],
                      });
                    }}
                    className="font-semibold text-[#111111] hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <Download className="h-3 w-3" />
                    Inspect FHIR ServiceRequest
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* 4. Longitudinal Clinical Timeline */}
      <Card variant="mockup" className="space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
          <div>
            <CardTitle className="text-lg">Longitudinal Clinical Timeline</CardTitle>
            <CardDescription className="mt-1">
              Chronological FHIR R4 records linked to your ABHA profile.
            </CardDescription>
          </div>
          <Badge variant="default">3 Linked Records</Badge>
        </div>

        {/* Timeline Item 1: Encounter */}
        <div className="relative pl-6 pb-6 border-l-2 border-[#e5e7eb] last:border-l-0 space-y-2">
          <span className="absolute -left-[9px] top-0 h-4 w-4 rounded-full bg-[#111111] border-2 border-white ring-2 ring-[#e5e7eb]" />
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[#111111] text-sm">
              Clinical Encounter • AIIMS Cardiology
            </span>
            <span className="text-[#6b7280] font-mono">Today, 10:15 AM</span>
          </div>
          <p className="text-xs text-[#374151]">
            Attending: <span className="font-medium text-[#111111]">Dr. Ananya Sharma (Chief Cardiologist)</span>
          </p>
          <div className="p-3 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] text-xs space-y-1">
            <div className="font-semibold text-[#111111]">Encounter Note:</div>
            <p className="text-[#6b7280]">
              Routine hypertension follow-up. Blood pressure reading 134/86 mmHg. Advised continuation of lifestyle modifications and daily pharmacotherapy.
            </p>
          </div>
        </div>

        {/* Timeline Item 2: MedicationRequest */}
        <div className="relative pl-6 pb-6 border-l-2 border-[#e5e7eb] last:border-l-0 space-y-2">
          <span className="absolute -left-[9px] top-0 h-4 w-4 rounded-full bg-[#10b981] border-2 border-white ring-2 ring-[#e5e7eb]" />
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[#111111] text-sm">
              Active E-Prescription • FHIR MedicationRequest
            </span>
            <span className="text-[#6b7280] font-mono">Issued 2 Days Ago</span>
          </div>
          <div className="p-3 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] text-xs grid grid-cols-2 gap-2">
            <div>
              <div className="text-[#6b7280]">Medication</div>
              <div className="font-semibold text-[#111111]">Metformin HCl 500mg</div>
            </div>
            <div>
              <div className="text-[#6b7280]">Dosage Instructions</div>
              <div className="font-semibold text-[#111111]">1 Tablet with Dinner</div>
            </div>
          </div>
        </div>

        {/* Timeline Item 3: Lab Observation */}
        <div className="relative pl-6 space-y-2">
          <span className="absolute -left-[9px] top-0 h-4 w-4 rounded-full bg-[#3b82f6] border-2 border-white ring-2 ring-[#e5e7eb]" />
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[#111111] text-sm">
              Diagnostic Report • Apollo Diagnostics Central
            </span>
            <span className="text-[#6b7280] font-mono">Sep 18, 2026</span>
          </div>
          <div className="p-3 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] text-xs space-y-2">
            <div className="flex items-center justify-between font-semibold text-[#111111]">
              <span>Fasting Blood Glucose (LOINC 1558-6)</span>
              <span className="text-[#059669]">96 mg/dL (Normal)</span>
            </div>
            <div className="flex items-center justify-between text-[#6b7280] text-[11px] pt-1 border-t border-[#e5e7eb]">
              <span>Report ID: ARX-91024</span>
              <span className="text-[#111111] font-medium">
                Cryptographic PDF
              </span>
            </div>
          </div>
        </div>
      </Card>

    </div>
  );
}
