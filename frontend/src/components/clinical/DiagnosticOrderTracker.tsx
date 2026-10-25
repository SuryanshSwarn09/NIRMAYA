"use client";

import React, { useState } from "react";
import { Badge, Button, Card } from "@/components/ui";
import { 
  DiagnosticOrder, 
  DiagnosticReport, 
  ServiceRequestPriority, 
  ServiceRequestStatus, 
  SpecimenType 
} from "@/lib/api";
import { 
  FlaskConical, 
  FileCheck, 
  Clock, 
  AlertCircle, 
  Plus, 
  CheckCircle2, 
  FileCode, 
  X, 
  Building2,
  Calendar,
  Download,
  Eye,
  Scan,
  Activity,
  Image as ImageIcon
} from "lucide-react";
import { PacsViewerModal } from "./PacsViewerModal";

interface DiagnosticOrderTrackerProps {
  patientId: string;
  patientName?: string;
  doctorId?: string;
  isDoctorView?: boolean;
  isLabView?: boolean;
  initialOrders?: DiagnosticOrder[];
  initialReports?: DiagnosticReport[];
  onOrderCreated?: (order: Partial<DiagnosticOrder>) => void;
  onReportIssued?: (report: Partial<DiagnosticReport>) => void;
}

export interface DiagnosticPreset {
  category: "laboratory" | "diagnostic_imaging";
  code_value: string;
  code_display: string;
  priority: ServiceRequestPriority;
  specimen_type: SpecimenType;
  fasting_required: boolean;
  reason: string;
  modalityCode?: "CR" | "ECG" | "CT" | "US";
}

export const DIAGNOSTIC_PRESETS: DiagnosticPreset[] = [
  {
    category: "laboratory",
    code_value: "24331-1",
    code_display: "Lipid panel with direct LDL - Serum or Plasma",
    priority: "routine",
    specimen_type: "serum",
    fasting_required: true,
    reason: "Hypertension baseline cardiovascular risk stratification",
  },
  {
    category: "laboratory",
    code_value: "4548-4",
    code_display: "Hemoglobin A1c/Hemoglobin.total in Blood",
    priority: "routine",
    specimen_type: "blood",
    fasting_required: false,
    reason: "Glycemic surveillance and prediabetes exclusion",
  },
  {
    category: "laboratory",
    code_value: "58410-2",
    code_display: "Complete Blood Count (CBC) with Automated Differential",
    priority: "routine",
    specimen_type: "blood",
    fasting_required: false,
    reason: "Fatigue workup and hematology baseline screening",
  },
  {
    category: "laboratory",
    code_value: "38483-4",
    code_display: "Creatinine with GFR in Serum or Plasma",
    priority: "routine",
    specimen_type: "serum",
    fasting_required: false,
    reason: "Renal functional surveillance prior to antihypertensive therapy",
  },
  {
    category: "laboratory",
    code_value: "2093-3",
    code_display: "Total Cholesterol in Serum or Plasma",
    priority: "routine",
    specimen_type: "serum",
    fasting_required: true,
    reason: "Atherosclerotic cardiovascular disease assessment",
  },
  {
    category: "laboratory",
    code_value: "1975-2",
    code_display: "Total Bilirubin in Serum or Plasma",
    priority: "routine",
    specimen_type: "serum",
    fasting_required: false,
    reason: "Hepatic function and metabolic profile panel",
  },
  {
    category: "laboratory",
    code_value: "3016-3",
    code_display: "Thyrotropin (TSH) in Serum or Plasma",
    priority: "routine",
    specimen_type: "serum",
    fasting_required: false,
    reason: "Thyroid gland functional screening",
  },
  {
    category: "diagnostic_imaging",
    code_value: "24648-8",
    code_display: "Chest X-Ray 2 Views PA and Lateral (CR/DX)",
    priority: "routine",
    specimen_type: "serum",
    fasting_required: false,
    reason: "Cardiomegaly exclusion and baseline cardiopulmonary imaging",
    modalityCode: "CR",
  },
  {
    category: "diagnostic_imaging",
    code_value: "11524-6",
    code_display: "12-Lead Electrocardiogram Diagnostic Strip (ECG)",
    priority: "routine",
    specimen_type: "serum",
    fasting_required: false,
    reason: "Electrophysiological screening for arrhythmia and ischemia",
    modalityCode: "ECG",
  },
  {
    category: "diagnostic_imaging",
    code_value: "36642-7",
    code_display: "Computed Tomography (CT) Head without IV Contrast",
    priority: "urgent",
    specimen_type: "serum",
    fasting_required: false,
    reason: "Neuroimaging evaluation and acute hemorrhage exclusion",
    modalityCode: "CT",
  },
  {
    category: "diagnostic_imaging",
    code_value: "77484-4",
    code_display: "Transthoracic 2D Doppler Echocardiogram (US)",
    priority: "routine",
    specimen_type: "serum",
    fasting_required: false,
    reason: "Left ventricular ejection fraction and valvular assessment",
    modalityCode: "US",
  },
];

export const DiagnosticOrderTracker: React.FC<DiagnosticOrderTrackerProps> = ({
  patientId,
  patientName = "Patient",
  doctorId = "doc-ananya-sharma",
  isDoctorView = false,
  isLabView = false,
  initialOrders,
  initialReports,
  onOrderCreated,
  onReportIssued,
}) => {
  const [orders, setOrders] = useState<DiagnosticOrder[]>(
    initialOrders || [
      {
        id: "ord-req-901",
        patient_id: patientId,
        status: "completed",
        intent: "order",
        priority: "routine",
        code_system: "http://loinc.org",
        code_value: "24331-1",
        code_display: "Lipid panel with direct LDL - Serum or Plasma",
        category: "laboratory",
        reason_code: "I10",
        reason_display: "Essential hypertension follow-up lipid screening",
        clinical_notes: "12-hour overnight fasting required.",
        specimen_type: "serum",
        fasting_required: true,
        authored_on: "2026-10-24T09:30:00Z",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: "ord-req-902",
        patient_id: patientId,
        status: "active",
        intent: "order",
        priority: "routine",
        code_system: "http://loinc.org",
        code_value: "4548-4",
        code_display: "Hemoglobin A1c in Whole Blood",
        category: "laboratory",
        reason_display: "Routine 3-month glycemic evaluation",
        specimen_type: "blood",
        fasting_required: false,
        authored_on: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: "ord-req-903",
        patient_id: patientId,
        status: "completed",
        intent: "order",
        priority: "routine",
        code_system: "http://loinc.org",
        code_value: "24648-8",
        code_display: "Chest X-Ray 2 Views PA and Lateral (CR)",
        category: "diagnostic_imaging",
        reason_display: "Cardiopulmonary baseline evaluation",
        specimen_type: "serum",
        fasting_required: false,
        authored_on: "2026-10-24T09:15:00Z",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: "ord-req-904",
        patient_id: patientId,
        status: "completed",
        intent: "order",
        priority: "routine",
        code_system: "http://loinc.org",
        code_value: "11524-6",
        code_display: "12-Lead Electrocardiogram Diagnostic Strip (ECG)",
        category: "diagnostic_imaging",
        reason_display: "Hypertension baseline rhythm assessment",
        specimen_type: "serum",
        fasting_required: false,
        authored_on: "2026-10-24T09:20:00Z",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]
  );

  const [reports, setReports] = useState<DiagnosticReport[]>(
    initialReports || [
      {
        id: "rep-901",
        patient_id: patientId,
        order_id: "ord-req-901",
        status: "final",
        category: "LAB",
        code_system: "http://loinc.org",
        code_value: "24331-1",
        code_display: "Comprehensive Lipid Profile Analysis",
        effective_date_time: "2026-10-24T14:00:00Z",
        issued_date_time: "2026-10-24T16:30:00Z",
        conclusion: "Mild dyslipidemia with borderline elevated direct LDL (138 mg/dL) and triglycerides (182 mg/dL). HDL measured at 44 mg/dL.",
        is_abnormal: true,
        observations: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: "rep-903",
        patient_id: patientId,
        order_id: "ord-req-903",
        status: "final",
        category: "RAD",
        code_system: "http://loinc.org",
        code_value: "24648-8",
        code_display: "Chest Radiograph 2 Views (PA and Lateral)",
        effective_date_time: "2026-10-24T09:40:00Z",
        issued_date_time: "2026-10-24T10:15:00Z",
        conclusion: "Normal cardiopulmonary silhouette. Cardiothoracic ratio is 0.44. Clear bilateral lung parenchymal fields. Costophrenic sulci sharp.",
        is_abnormal: false,
        observations: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: "rep-904",
        patient_id: patientId,
        order_id: "ord-req-904",
        status: "final",
        category: "ECG",
        code_system: "http://loinc.org",
        code_value: "11524-6",
        code_display: "Standard 12-Lead Electrocardiogram Report",
        effective_date_time: "2026-10-24T09:50:00Z",
        issued_date_time: "2026-10-24T10:30:00Z",
        conclusion: "Normal sinus rhythm at 72 bpm. PR 156 ms, QRS 84 ms, QTc 412 ms. Normal axis with no ischemic ST-T abnormalities or chamber enlargement.",
        is_abnormal: false,
        observations: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]
  );

  const [isRequisitionModalOpen, setIsRequisitionModalOpen] = useState(false);
  const [selectedPresetIndex, setSelectedPresetIndex] = useState(0);
  const [selectedPriority, setSelectedPriority] = useState<ServiceRequestPriority>("routine");
  const [selectedSpecimen, setSelectedSpecimen] = useState<SpecimenType>("serum");
  const [fastingRequired, setFastingRequired] = useState(true);
  const [clinicalReason, setClinicalReason] = useState(DIAGNOSTIC_PRESETS[0].reason);
  const [notes, setNotes] = useState("12-hour fasting prior to sample draw.");

  const [fulfillingOrder, setFulfillingOrder] = useState<DiagnosticOrder | null>(null);
  const [reportConclusion, setReportConclusion] = useState("");
  const [isAbnormalReport, setIsAbnormalReport] = useState(false);

  // PACS DICOM Viewer State
  const [pacsStudyKey, setPacsStudyKey] = useState<string | null>(null);

  const [viewingFhirItem, setViewingFhirItem] = useState<{
    type: "ServiceRequest" | "DiagnosticReport";
    data: unknown;
  } | null>(null);

  const handleSelectPreset = (idx: number) => {
    setSelectedPresetIndex(idx);
    const p = DIAGNOSTIC_PRESETS[idx];
    setSelectedPriority(p.priority);
    setSelectedSpecimen(p.specimen_type);
    setFastingRequired(p.fasting_required);
    setClinicalReason(p.reason);
    if (p.category === "diagnostic_imaging") {
      setNotes("Direct digital modality capture with WADO-RS PACS link.");
    } else if (p.fasting_required) {
      setNotes("12-hour fasting prior to sample draw.");
    } else {
      setNotes("Standard non-fasting routine collection.");
    }
  };

  const handleCreateOrder = (e: React.FormEvent) => {
    e.preventDefault();
    const preset = DIAGNOSTIC_PRESETS[selectedPresetIndex];
    const newOrder: DiagnosticOrder = {
      id: `ord-req-${Date.now().toString().slice(-4)}`,
      patient_id: patientId,
      doctor_id: doctorId,
      status: "active",
      intent: "order",
      priority: selectedPriority,
      code_system: "http://loinc.org",
      code_value: preset.code_value,
      code_display: preset.code_display,
      category: preset.category,
      reason_display: clinicalReason,
      clinical_notes: notes,
      specimen_type: selectedSpecimen,
      fasting_required: fastingRequired,
      authored_on: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setOrders((prev) => [newOrder, ...prev]);
    if (onOrderCreated) {
      onOrderCreated(newOrder);
    }
    setIsRequisitionModalOpen(false);
  };

  const handleFulfillOrder = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fulfillingOrder) return;

    const reportCat =
      fulfillingOrder.category === "diagnostic_imaging"
        ? fulfillingOrder.code_value === "11524-6"
          ? "ECG"
          : "RAD"
        : "LAB";

    const newReport: DiagnosticReport = {
      id: `rep-${Date.now().toString().slice(-4)}`,
      patient_id: fulfillingOrder.patient_id,
      order_id: fulfillingOrder.id,
      status: "final",
      category: reportCat,
      code_system: fulfillingOrder.code_system,
      code_value: fulfillingOrder.code_value,
      code_display: fulfillingOrder.code_display,
      effective_date_time: new Date().toISOString(),
      issued_date_time: new Date().toISOString(),
      conclusion: reportConclusion,
      is_abnormal: isAbnormalReport,
      observations: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setReports((prev) => [newReport, ...prev]);
    setOrders((prev) =>
      prev.map((o) => (o.id === fulfillingOrder.id ? { ...o, status: "completed" } : o))
    );

    if (onReportIssued) {
      onReportIssued(newReport);
    }

    setFulfillingOrder(null);
    setReportConclusion("");
  };

  const getPacsKeyForCode = (code: string): string => {
    if (code === "11524-6") return "ecg-rhythm";
    if (code === "36642-7") return "head-ct";
    return "chest-xray";
  };

  const isImagingItem = (category: string, code: string): boolean => {
    return (
      category === "diagnostic_imaging" ||
      category === "RAD" ||
      category === "ECG" ||
      code === "24648-8" ||
      code === "11524-6" ||
      code === "36642-7" ||
      code === "77484-4"
    );
  };

  return (
    <div className="space-y-6">
      {/* Tracker Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#f8f9fa] p-4 rounded-[8px] border border-[#e5e7eb]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-[#111111]">
              Diagnostic Requisitions & PACS Reports
            </h3>
            <Badge variant="neutral" size="sm">
              {orders.filter((o) => o.status === "active").length} In Progress
            </Badge>
          </div>
          <p className="text-xs text-[#6b7280]">
            HL7 FHIR R4 ServiceRequest, DiagnosticReport, LOINC Terminology, and DICOM 3.0 WADO-RS
          </p>
        </div>

        {isDoctorView && (
          <Button
            size="sm"
            onClick={() => setIsRequisitionModalOpen(true)}
            className="flex items-center gap-1.5 self-start sm:self-auto rounded-[8px]"
          >
            <Plus className="h-4 w-4" />
            Requisition Diagnostic Test
          </Button>
        )}
      </div>

      {/* Active Orders List */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-[#6b7280]">
          Active Diagnostic Requisitions (ServiceRequest)
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {orders.map((order) => {
            const isCompleted = order.status === "completed";
            const isImaging = isImagingItem(order.category, order.code_value);

            return (
              <Card
                key={order.id}
                className={`p-4 border transition-all rounded-[8px] ${
                  isCompleted
                    ? "border-[#e5e7eb] bg-[#fafafa] opacity-85"
                    : "border-[#e5e7eb] bg-white hover:border-[#111111]"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-bold px-1.5 py-0.5 rounded-[6px] bg-[#f3f4f6] text-[#111111] border border-[#e5e7eb]">
                        {order.code_value}
                      </span>
                      <Badge
                        variant={order.priority === "stat" ? "critical" : order.priority === "urgent" ? "warning" : "default"}
                        size="sm"
                      >
                        {order.priority.toUpperCase()}
                      </Badge>
                      <Badge
                        variant={isCompleted ? "emerald" : "pending"}
                        size="sm"
                      >
                        {order.status}
                      </Badge>
                      {isImaging && (
                        <Badge variant="outline" size="sm" className="font-mono text-[10px] text-[#374151]">
                          Imaging
                        </Badge>
                      )}
                    </div>

                    <h5 className="text-sm font-semibold text-[#111111] leading-tight">
                      {order.code_display}
                    </h5>
                  </div>

                  <button
                    onClick={() =>
                      setViewingFhirItem({
                        type: "ServiceRequest",
                        data: {
                          resourceType: "ServiceRequest",
                          id: order.id,
                          status: order.status,
                          intent: order.intent,
                          priority: order.priority,
                          category: [{ coding: [{ code: order.category, display: order.category }] }],
                          code: {
                            coding: [{ system: order.code_system, code: order.code_value, display: order.code_display }],
                          },
                          subject: { reference: `Patient/${patientId}`, display: patientName },
                          authoredOn: order.authored_on,
                        },
                      })
                    }
                    className="p-1 text-[#6b7280] hover:text-[#111111] rounded-[6px]"
                    title="View FHIR ServiceRequest"
                  >
                    <FileCode className="h-4 w-4" />
                  </button>
                </div>

                <div className="mt-2.5 pt-2 text-xs text-[#4b5563] border-t border-[#f3f4f6] space-y-1">
                  <p className="line-clamp-1">
                    <span className="font-medium text-[#111111]">Indication:</span> {order.reason_display || "Routine clinical evaluation"}
                  </p>
                  <div className="flex items-center gap-3 text-[11px] text-[#6b7280]">
                    <span>Category: <strong className="text-[#111111] capitalize">{order.category.replace("_", " ")}</strong></span>
                    {!isImaging && (
                      <span>Specimen: <strong className="text-[#111111] capitalize">{order.specimen_type}</strong></span>
                    )}
                    {order.fasting_required && (
                      <span className="text-[#d97706] font-medium">12-hr Fasting</span>
                    )}
                  </div>
                </div>

                {/* Actions Row */}
                <div className="mt-3 pt-2 border-t border-[#e5e7eb] flex items-center justify-between gap-2">
                  {isImaging && isCompleted && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setPacsStudyKey(getPacsKeyForCode(order.code_value))}
                      className="flex items-center gap-1.5 text-xs h-7 rounded-[8px]"
                    >
                      <Eye className="h-3.5 w-3.5 text-emerald-600" />
                      <span>Launch PACS Viewer</span>
                    </Button>
                  )}

                  {isLabView && !isCompleted && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setFulfillingOrder(order)}
                      className="ml-auto rounded-[8px]"
                    >
                      Fulfill & Issue Report
                    </Button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Verified Reports List */}
      <div className="space-y-3 pt-2">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-[#6b7280]">
          Completed Diagnostic & PACS Reports (DiagnosticReport)
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {reports.map((rep) => {
            const isImaging = isImagingItem(rep.category, rep.code_value);

            return (
              <Card
                key={rep.id}
                className="p-4 border border-[#e5e7eb] bg-white hover:border-[#111111] transition-all space-y-2.5 rounded-[8px]"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant="verified" size="sm">
                        {isImaging ? "AERB / DICOM Verified" : "NABL Certified"}
                      </Badge>
                      {rep.is_abnormal ? (
                        <Badge variant="warning" size="sm">
                          Findings Abnormal
                        </Badge>
                      ) : (
                        <Badge variant="emerald" size="sm">
                          Normal Findings
                        </Badge>
                      )}
                      <span className="font-mono text-xs font-bold px-1.5 py-0.5 rounded-[6px] bg-[#f3f4f6] text-[#111111] border border-[#e5e7eb]">
                        {rep.code_value}
                      </span>
                    </div>
                    <h5 className="text-sm font-semibold text-[#111111] leading-tight">
                      {rep.code_display}
                    </h5>
                  </div>

                  <button
                    onClick={() =>
                      setViewingFhirItem({
                        type: "DiagnosticReport",
                        data: {
                          resourceType: "DiagnosticReport",
                          id: rep.id,
                          status: rep.status,
                          category: [{ coding: [{ code: rep.category, display: rep.category }] }],
                          code: {
                            coding: [{ system: rep.code_system, code: rep.code_value, display: rep.code_display }],
                          },
                          subject: { reference: `Patient/${patientId}`, display: patientName },
                          conclusion: rep.conclusion,
                        },
                      })
                    }
                    className="p-1 text-[#6b7280] hover:text-[#111111] rounded-[6px]"
                    title="View FHIR DiagnosticReport"
                  >
                    <FileCode className="h-4 w-4" />
                  </button>
                </div>

                {rep.conclusion && (
                  <div className="p-2.5 rounded-[8px] bg-[#f9fafb] border border-[#f3f4f6] text-xs text-[#374151]">
                    <p className="font-medium text-[#111111] mb-0.5">Clinical Conclusion & Impression:</p>
                    <p className="leading-relaxed">{rep.conclusion}</p>
                  </div>
                )}

                <div className="flex items-center justify-between text-[11px] text-[#6b7280] pt-1 border-t border-[#f3f4f6]">
                  <span>Issued: {new Date(rep.issued_date_time).toLocaleDateString()}</span>
                  <span className="font-mono text-[#059669]">Order Ref: {rep.order_id}</span>
                </div>

                {/* Direct Launch PACS Viewer for Imaging Studies */}
                {isImaging && (
                  <div className="pt-2 flex items-center justify-between border-t border-[#f3f4f6]">
                    <span className="text-[11px] text-[#6b7280]">
                      Modality: <strong className="text-[#111111]">{rep.category === "ECG" ? "ECG Diagnostic Strip" : "Radiology (DICOM 3.0)"}</strong>
                    </span>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setPacsStudyKey(getPacsKeyForCode(rep.code_value))}
                      className="flex items-center gap-1.5 text-xs h-7 rounded-[8px]"
                    >
                      <Eye className="h-3.5 w-3.5 text-emerald-600" />
                      <span>Launch PACS Viewer</span>
                    </Button>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </div>

      {/* Modal: Requisition Diagnostic Test */}
      {isRequisitionModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="bg-white rounded-[8px] max-w-lg w-full p-6 shadow-2xl border border-[#e5e7eb] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-[8px] bg-[#111111] text-white flex items-center justify-center">
                  <FlaskConical className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="font-semibold text-base text-[#111111]">
                    Requisition Diagnostic Test
                  </h3>
                  <p className="text-xs text-[#6b7280]">
                    Create HL7 FHIR R4 ServiceRequest for {patientName}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsRequisitionModalOpen(false)}
                className="text-[#6b7280] hover:text-[#111111] rounded-[6px]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateOrder} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[#374151] mb-1">
                  Select LOINC Diagnostic Panel or Imaging Modality
                </label>
                <select
                  value={selectedPresetIndex}
                  onChange={(e) => handleSelectPreset(Number(e.target.value))}
                  className="w-full text-xs px-3 py-2 border border-[#e5e7eb] rounded-[8px] bg-white text-[#111111] focus:ring-1 focus:ring-[#111111]"
                >
                  <optgroup label="Laboratory & Pathology (Biochemistry / Hematology)">
                    {DIAGNOSTIC_PRESETS.filter((p) => p.category === "laboratory").map((preset, idx) => (
                      <option key={preset.code_value} value={DIAGNOSTIC_PRESETS.indexOf(preset)}>
                        {preset.code_value} • {preset.code_display}
                      </option>
                    ))}
                  </optgroup>
                  <optgroup label="Diagnostic Imaging & Electrophysiology (PACS / DICOM)">
                    {DIAGNOSTIC_PRESETS.filter((p) => p.category === "diagnostic_imaging").map((preset, idx) => (
                      <option key={preset.code_value} value={DIAGNOSTIC_PRESETS.indexOf(preset)}>
                        {preset.code_value} • {preset.code_display}
                      </option>
                    ))}
                  </optgroup>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Priority Tier
                  </label>
                  <select
                    value={selectedPriority}
                    onChange={(e) => setSelectedPriority(e.target.value as ServiceRequestPriority)}
                    className="w-full text-xs px-3 py-2 border border-[#e5e7eb] rounded-[8px] bg-white text-[#111111]"
                  >
                    <option value="routine">Routine</option>
                    <option value="urgent">Urgent</option>
                    <option value="stat">STAT (Emergency)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Specimen / Capture Source
                  </label>
                  <select
                    value={selectedSpecimen}
                    onChange={(e) => setSelectedSpecimen(e.target.value as SpecimenType)}
                    className="w-full text-xs px-3 py-2 border border-[#e5e7eb] rounded-[8px] bg-white text-[#111111]"
                  >
                    <option value="serum">Serum</option>
                    <option value="blood">Whole Blood</option>
                    <option value="plasma">Plasma</option>
                    <option value="urine">Urine</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#374151] mb-1">
                  Clinical Indication / Reason for Order
                </label>
                <input
                  type="text"
                  required
                  value={clinicalReason}
                  onChange={(e) => setClinicalReason(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-[#e5e7eb] rounded-[8px] focus:ring-1 focus:ring-[#111111]"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[#374151] mb-1">
                  Preparation Instructions & Clinical Notes
                </label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-[#e5e7eb] rounded-[8px] focus:ring-1 focus:ring-[#111111]"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="fastingCheck"
                  checked={fastingRequired}
                  onChange={(e) => setFastingRequired(e.target.checked)}
                  className="h-4 w-4 rounded-[4px] border-[#e5e7eb]"
                />
                <label htmlFor="fastingCheck" className="text-xs text-[#374151] cursor-pointer">
                  Require 12-hour overnight fasting prior to specimen draw
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#e5e7eb]">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsRequisitionModalOpen(false)}
                  className="rounded-[8px]"
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" className="rounded-[8px]">
                  Dispatch Requisition
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Fulfill Order & Issue Report (Lab Mode) */}
      {fulfillingOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="bg-white rounded-[8px] max-w-lg w-full p-6 shadow-2xl border border-[#e5e7eb] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <FileCheck className="h-5 w-5 text-[#111111]" />
                <h3 className="font-semibold text-base text-[#111111]">
                  Issue Diagnostic Report
                </h3>
              </div>
              <button
                onClick={() => setFulfillingOrder(null)}
                className="text-[#6b7280] hover:text-[#111111] rounded-[6px]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleFulfillOrder} className="space-y-4">
              <div className="p-3 bg-[#f9fafb] rounded-[8px] text-xs space-y-1">
                <p className="font-semibold text-[#111111]">{fulfillingOrder.code_display}</p>
                <p className="text-[#6b7280]">Requisition: {fulfillingOrder.id} • Specimen: {fulfillingOrder.specimen_type}</p>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#374151] mb-1">
                  Clinical Conclusion & Findings Narrative
                </label>
                <textarea
                  rows={3}
                  required
                  value={reportConclusion}
                  onChange={(e) => setReportConclusion(e.target.value)}
                  placeholder="e.g. Total cholesterol 218 mg/dL, LDL 138 mg/dL (borderline elevated). HDL 44 mg/dL."
                  className="w-full text-xs p-3 border border-[#e5e7eb] rounded-[8px] focus:outline-none focus:ring-1 focus:ring-[#111111]"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="abnormalCheck"
                  checked={isAbnormalReport}
                  onChange={(e) => setIsAbnormalReport(e.target.checked)}
                  className="h-4 w-4 rounded-[4px] border-[#e5e7eb]"
                />
                <label htmlFor="abnormalCheck" className="text-xs text-[#374151] cursor-pointer">
                  Mark as containing clinically abnormal findings
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#e5e7eb]">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setFulfillingOrder(null)}
                  className="rounded-[8px]"
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" className="rounded-[8px]">
                  Sign & Publish Report
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: FHIR Inspector */}
      {viewingFhirItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="bg-white rounded-[8px] max-w-xl w-full p-6 shadow-2xl border border-[#e5e7eb] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <FileCode className="h-5 w-5 text-[#111111]" />
                <h3 className="font-semibold text-sm text-[#111111]">
                  HL7 FHIR Release 4 • {viewingFhirItem.type}
                </h3>
              </div>
              <button
                onClick={() => setViewingFhirItem(null)}
                className="text-[#6b7280] hover:text-[#111111] rounded-[6px]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <pre className="p-4 bg-[#101010] text-[#a1a1aa] rounded-[8px] text-xs font-mono overflow-x-auto max-h-96">
              {JSON.stringify(viewingFhirItem.data, null, 2)}
            </pre>

            <div className="flex justify-end pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setViewingFhirItem(null)}
                className="rounded-[8px]"
              >
                Close Inspector
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Embedded PACS Viewer Modal */}
      <PacsViewerModal
        isOpen={!!pacsStudyKey}
        onClose={() => setPacsStudyKey(null)}
        studyKey={pacsStudyKey || "chest-xray"}
      />
    </div>
  );
};
