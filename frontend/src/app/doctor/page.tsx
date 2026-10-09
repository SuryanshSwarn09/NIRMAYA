"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button, Badge, Card, CardTitle, CardDescription, NavPillGroup } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import { 
  Stethoscope, 
  UserCheck, 
  Calendar, 
  Clock, 
  FileText, 
  Plus, 
  CheckCircle2, 
  Send,
  User,
  Activity,
  Code,
  Sparkles,
  Video,
  MapPin,
  TestTube2,
  FlaskConical
} from "lucide-react";
import { DoctorSlotManager } from "@/components/appointments";
import { ProblemListPanel, VitalsTelemetryPanel } from "@/components/clinical";

export default function DoctorEMRPage() {
  const { user } = useAuth();
  const doctorId = user?.id || "doc-ananya-sharma";
  const [activeTab, setActiveTab] = useState<"queue" | "problems" | "vitals" | "slots">("queue");
  const [selectedPatient, setSelectedPatient] = useState("Arun Patel");
  const [medication, setMedication] = useState("Atorvastatin 20mg");
  const [dosage, setDosage] = useState("Once daily at bedtime");
  const [issuedPrescription, setIssuedPrescription] = useState(false);

  // Patient Clinical Vitals Telemetry (Day 22)
  const [patientVitals, setPatientVitals] = useState({
    bp: "134 / 86 mmHg",
    hr: "72 bpm",
    spo2: "98% Room Air",
    bmi: "24.2 kg/m²",
  });
  const [isRecordingVitals, setIsRecordingVitals] = useState(false);
  const [newSystolic, setNewSystolic] = useState("134");
  const [newDiastolic, setNewDiastolic] = useState("86");
  const [newHr, setNewHr] = useState("72");
  const [newSpo2, setNewSpo2] = useState("98");
  const [vitalsSaved, setVitalsSaved] = useState(false);

  // Structured SOAP Clinical Documentation (Day 23)
  const [chiefComplaint, setChiefComplaint] = useState(
    "Exertional dyspnea and morning fatigue during cardiac rehabilitation"
  );
  const [subjectiveNotes, setSubjectiveNotes] = useState(
    "Patient reports mild exertional shortness of breath when climbing 2 flights of stairs. Denies orthopnea, paroxysmal nocturnal dyspnea, or chest pain. Compliant with prescribed antihypertensives."
  );
  const [objectiveNotes, setObjectiveNotes] = useState(
    "BP 134/86 mmHg, HR 72 bpm regular rhythm, SpO2 98% room air. Dual heart sounds S1 S2 present, no murmurs. JVP normal. Bilateral vesicular breath sounds without crackles or wheezing."
  );
  const [assessmentNotes, setAssessmentNotes] = useState(
    "1. Essential (primary) hypertension, well-compensated.\n2. Exertional Dyspnea NYHA Class I-II, stable.\n3. Lipid Profile surveillance pending."
  );
  const [planNotes, setPlanNotes] = useState(
    "1. Continue current medical regimen: Atorvastatin 20mg nocte and Amlodipine.\n2. Requisition 12-lead resting ECG and Fasting Lipid Panel.\n3. Return for clinical review in 4 weeks."
  );
  const [soapPrimaryDx, setSoapPrimaryDx] = useState("I10 - Essential (primary) hypertension");
  const [isSoapSigned, setIsSoapSigned] = useState(false);
  const [soapSignatureHash, setSoapSignatureHash] = useState("");
  const [isViewingSoapFhir, setIsViewingSoapFhir] = useState(false);
  const [soapTab, setSoapTab] = useState<"s" | "o" | "a" | "p">("s");

  const handleSignPrescription = (e: React.FormEvent) => {
    e.preventDefault();
    setIssuedPrescription(true);
  };

  const handleSaveVitals = (e: React.FormEvent) => {
    e.preventDefault();
    setPatientVitals({
      bp: `${newSystolic} / ${newDiastolic} mmHg`,
      hr: `${newHr} bpm`,
      spo2: `${newSpo2}% Room Air`,
      bmi: patientVitals.bmi,
    });
    setVitalsSaved(true);
    setIsRecordingVitals(false);
    setTimeout(() => setVitalsSaved(false), 3000);
  };

  const handleSignSoapNote = (e: React.FormEvent) => {
    e.preventDefault();
    const mockHash = "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069";
    setIsSoapSigned(true);
    setSoapSignatureHash(mockHash);
  };

  // Diagnostic Lab Orders & Requisitions (Day 24)
  const LAB_TEST_PRESETS = [
    {
      code: "24331-1",
      display: "Lipid 1996 panel - Serum or Plasma",
      specimen: "serum" as const,
      fasting: true,
    },
    {
      code: "4548-4",
      display: "Hemoglobin A1c/Hemoglobin.total in Blood",
      specimen: "blood" as const,
      fasting: false,
    },
    {
      code: "58410-2",
      display: "Complete Blood Count (CBC) with Automated Differential",
      specimen: "blood" as const,
      fasting: false,
    },
    {
      code: "38483-4",
      display: "Creatinine with GFR [Mass/volume] in Serum or Plasma",
      specimen: "serum" as const,
      fasting: false,
    },
    {
      code: "1558-6",
      display: "Fasting Blood Glucose in Serum or Plasma",
      specimen: "serum" as const,
      fasting: true,
    },
  ];

  const [selectedLabTestCode, setSelectedLabTestCode] = useState("24331-1");
  const [labPriority, setLabPriority] = useState<"routine" | "urgent" | "stat">("routine");
  const [labSpecimen, setLabSpecimen] = useState<"serum" | "blood" | "plasma" | "urine">("serum");
  const [labFasting, setLabFasting] = useState(true);
  const [labClinicalReason, setLabClinicalReason] = useState(
    "Essential hypertension follow-up & cardiovascular risk evaluation"
  );
  const [labNotes, setLabNotes] = useState(
    "12-hour overnight fast requested prior to venipuncture."
  );
  const [issuedOrders, setIssuedOrders] = useState([
    {
      id: "ord-req-901",
      code: "24331-1",
      display: "Lipid 1996 panel - Serum or Plasma",
      priority: "routine",
      specimen: "serum",
      fasting: true,
      reason: "Essential hypertension follow-up lipid screening",
      status: "active",
      authored_on: "Today, 10:20 AM",
    },
  ]);
  const [isViewingOrderFhir, setIsViewingOrderFhir] = useState(false);
  const [selectedOrderForFhir, setSelectedOrderForFhir] = useState<any>(null);
  const [orderIssuedSuccess, setOrderIssuedSuccess] = useState(false);

  const handleTestPresetChange = (code: string) => {
    setSelectedLabTestCode(code);
    const preset = LAB_TEST_PRESETS.find((p) => p.code === code);
    if (preset) {
      setLabSpecimen(preset.specimen);
      setLabFasting(preset.fasting);
    }
  };

  const handleIssueLabOrder = (e: React.FormEvent) => {
    e.preventDefault();
    const preset = LAB_TEST_PRESETS.find((p) => p.code === selectedLabTestCode) || {
      code: selectedLabTestCode,
      display: "Diagnostic Test Requisition",
      specimen: labSpecimen,
      fasting: labFasting,
    };

    const newOrder = {
      id: `ord-req-${Date.now().toString().slice(-4)}`,
      code: preset.code,
      display: preset.display,
      priority: labPriority,
      specimen: labSpecimen,
      fasting: labFasting,
      reason: labClinicalReason,
      status: "active",
      authored_on: "Just now",
    };

    setIssuedOrders((prev) => [newOrder, ...prev]);
    setOrderIssuedSuccess(true);
    setTimeout(() => setOrderIssuedSuccess(false), 4000);
  };


  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 bg-white">
      
      {/* Top Clinician Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#e5e7eb]">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-[#111111] text-white flex items-center justify-center font-bold text-base shrink-0">
            AS
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111111]">
                {user?.fullName || "Dr. Ananya Sharma"}
              </h1>
              <Badge variant="verified">HPR Verified</Badge>
            </div>
            <p className="text-sm text-[#6b7280]">
              Chief Cardiologist • AIIMS New Delhi • HPR:{" "}
              <span className="font-mono text-[#111111]">ananya.sharma@hpr.abdm</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="emerald" size="sm">Clinical Session Active</Badge>
          <Link href="/patient">
            <Button variant="secondary" size="sm">
              Switch to Patient View
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Tab Nav Switcher */}
      <div className="flex justify-start">
        <NavPillGroup
          items={[
            {
              id: "queue",
              label: "Consultation Queue & EMR",
              icon: <Stethoscope className="h-4 w-4" />,
            },
            {
              id: "problems",
              label: "Longitudinal Problems",
              icon: <FileText className="h-4 w-4" />,
            },
            {
              id: "vitals",
              label: "Vitals & Telemetry",
              icon: <Activity className="h-4 w-4" />,
            },
            {
              id: "slots",
              label: "Availability & Slot Engine",
              icon: <Calendar className="h-4 w-4" />,
            },
          ]}
          activeId={activeTab}
          onChange={(id) => setActiveTab(id as "queue" | "problems" | "vitals" | "slots")}
        />
      </div>

      {activeTab === "slots" ? (
        /* ========================================================================
           SLOT AVAILABILITY ENGINE & SCHEDULE GENERATOR
           ======================================================================== */
        <div className="animate-fade-in">
          <DoctorSlotManager
            doctorId={doctorId}
            doctorName={user?.fullName || "Dr. Ananya Sharma"}
          />
        </div>
      ) : activeTab === "problems" ? (
        <div className="animate-fade-in max-w-5xl mx-auto">
          <ProblemListPanel
            patientId="pat-arun-patel"
            patientName={selectedPatient}
            isDoctorView={true}
          />
        </div>
      ) : activeTab === "vitals" ? (
        <div className="animate-fade-in max-w-5xl mx-auto">
          <VitalsTelemetryPanel
            patientId="pat-arun-patel"
            patientName={selectedPatient}
            isDoctorView={true}
          />
        </div>
      ) : (
        /* ========================================================================
           CLINICAL ENCOUNTER QUEUE & EMR INTERFACE
           ======================================================================== */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fade-in">
          
          {/* Left 4 Columns: Today's Clinical Appointment Queue */}
          <div className="lg:col-span-4 space-y-5">
            <Card variant="mockup" className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-[#111111]" />
                  <CardTitle className="text-base">Consultation Queue</CardTitle>
                </div>
                <Badge variant="default" size="sm">2 Scheduled</Badge>
              </div>

              <div className="space-y-2.5">
                {/* Patient 1 */}
                <button
                  type="button"
                  onClick={() => {
                    setSelectedPatient("Arun Patel");
                    setIssuedPrescription(false);
                  }}
                  className={`w-full p-3.5 rounded-[8px] border text-left transition-all cursor-pointer ${
                    selectedPatient === "Arun Patel"
                      ? "bg-[#f8f9fa] border-[#111111] shadow-xs"
                      : "bg-white border-[#e5e7eb] hover:bg-[#f8f9fa]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-[#111111]">Arun Patel</span>
                    <span className="text-[11px] font-mono text-[#059669] bg-[#ecfdf5] px-2 py-0.5 rounded-full">
                      10:15 AM
                    </span>
                  </div>
                  <div className="text-xs text-[#6b7280] mt-1">
                    ABHA: 91-8472-1092-4821
                  </div>
                  <div className="text-[11px] text-[#374151] font-medium mt-1">
                    Reason: Hypertension Follow-up
                  </div>
                </button>

                {/* Patient 2 */}
                <button
                  type="button"
                  onClick={() => {
                    setSelectedPatient("Priya Nair");
                    setIssuedPrescription(false);
                  }}
                  className={`w-full p-3.5 rounded-[8px] border text-left transition-all cursor-pointer ${
                    selectedPatient === "Priya Nair"
                      ? "bg-[#f8f9fa] border-[#111111] shadow-xs"
                      : "bg-white border-[#e5e7eb] hover:bg-[#f8f9fa]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-[#111111]">Priya Nair</span>
                    <span className="text-[11px] font-mono text-[#059669] bg-[#ecfdf5] px-2 py-0.5 rounded-full">
                      11:30 AM
                    </span>
                  </div>
                  <div className="text-xs text-[#6b7280] mt-1">
                    ABHA: 91-9988-7766-5544
                  </div>
                  <div className="text-[11px] text-[#374151] font-medium mt-1">
                    Reason: Arrhythmia Assessment
                  </div>
                </button>
              </div>

              {/* Quick Action to manage slots */}
              <div className="pt-2 border-t border-[#e5e7eb]">
                <button
                  type="button"
                  onClick={() => setActiveTab("slots")}
                  className="w-full py-2 px-3 rounded-[6px] border border-[#e5e7eb] bg-[#f8f9fa] text-xs font-semibold text-[#111111] hover:bg-[#e5e7eb] transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  Manage Daily Practice Availability
                </button>
              </div>
            </Card>

            {/* Quick Vital Signs Snapshot */}
            <Card variant="mockup" className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#6b7280] uppercase tracking-wider">
                  Patient Vitals ({selectedPatient})
                </span>
                <Badge variant="verified" size="sm">FHIR Verified</Badge>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb]">
                  <span className="text-[#6b7280] block text-[11px]">Blood Pressure</span>
                  <span className="font-bold text-sm text-[#111111]">{patientVitals.bp}</span>
                </div>
                <div className="p-2.5 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb]">
                  <span className="text-[#6b7280] block text-[11px]">Heart Rate</span>
                  <span className="font-bold text-sm text-[#111111]">{patientVitals.hr}</span>
                </div>
                <div className="p-2.5 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb]">
                  <span className="text-[#6b7280] block text-[11px]">SpO2</span>
                  <span className="font-bold text-sm text-[#059669]">{patientVitals.spo2}</span>
                </div>
                <div className="p-2.5 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb]">
                  <span className="text-[#6b7280] block text-[11px]">BMI</span>
                  <span className="font-bold text-sm text-[#111111]">{patientVitals.bmi}</span>
                </div>
              </div>

              {vitalsSaved && (
                <div className="p-2 rounded-[6px] bg-[#ecfdf5] border border-[#a7f3d0] text-xs text-[#065f46] flex items-center gap-1.5 animate-fadeIn">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#059669] shrink-0" />
                  <span>Clinical telemetry saved & signed to FHIR observation store!</span>
                </div>
              )}

              <button
                type="button"
                onClick={() => setIsRecordingVitals(true)}
                className="w-full py-2 px-3 rounded-[6px] border border-[#111111] bg-[#111111] text-xs font-semibold text-white hover:bg-black transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
              >
                <Activity className="h-3.5 w-3.5" />
                Record Clinical Vitals
              </button>
            </Card>
          </div>

          {/* Right 8 Columns: Clinical Consultation Note & Digital Prescription Pad */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Structured SOAP Clinical Documentation Pad (Day 23) */}
            <Card variant="mockup" className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#e5e7eb] gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-base sm:text-lg">
                      Structured SOAP Encounter Note: {selectedPatient}
                    </CardTitle>
                    {isSoapSigned ? (
                      <Badge variant="verified" size="sm">Final & Signed</Badge>
                    ) : (
                      <Badge variant="pending" size="sm">Preliminary Draft</Badge>
                    )}
                  </div>
                  <CardDescription>
                    HL7 FHIR R4 Composition • LOINC 11506-3 Narrative Sections
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsViewingSoapFhir(true)}
                    className="py-1 px-2.5 rounded-[6px] border border-[#e5e7eb] bg-[#f8f9fa] text-xs font-semibold text-[#111111] hover:bg-[#e5e7eb] transition-all flex items-center gap-1.5 cursor-pointer"
                  >
                    <Code className="h-3.5 w-3.5" />
                    FHIR Composition
                  </button>
                  <Badge variant="abdm" size="sm">CareContext Linkable</Badge>
                </div>
              </div>

              {isSoapSigned && (
                <div className="p-3.5 rounded-[8px] border border-[#a7f3d0] bg-[#ecfdf5] space-y-2 text-xs animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-[#065f46]">
                      <CheckCircle2 className="h-4 w-4" />
                      <span>Encounter Finalized & Electronically Signed (SHA-256)</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setIsSoapSigned(false)}
                      className="text-[11px] underline font-semibold text-[#065f46] cursor-pointer"
                    >
                      Amend Note
                    </button>
                  </div>
                  <div className="font-mono text-[11px] text-[#047857] truncate bg-white/60 p-1.5 rounded border border-[#a7f3d0]">
                    Digest: {soapSignatureHash}
                  </div>
                </div>
              )}

              {/* Chief Complaint & Primary Diagnosis Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs sm:text-sm">
                <div>
                  <label className="block text-xs font-semibold text-[#111111] mb-1">
                    Chief Complaint (LOINC 10154-3)
                  </label>
                  <input
                    type="text"
                    disabled={isSoapSigned}
                    value={chiefComplaint}
                    onChange={(e) => setChiefComplaint(e.target.value)}
                    className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-xs focus:outline-none focus:ring-1 focus:ring-[#111111] disabled:bg-[#f8f9fa]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#111111] mb-1">
                    Primary Diagnosis Coding (ICD-10 / SNOMED)
                  </label>
                  <input
                    type="text"
                    disabled={isSoapSigned}
                    value={soapPrimaryDx}
                    onChange={(e) => setSoapPrimaryDx(e.target.value)}
                    className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-xs font-mono focus:outline-none focus:ring-1 focus:ring-[#111111] disabled:bg-[#f8f9fa]"
                  />
                </div>
              </div>

              {/* SOAP Section Selector Tabs */}
              <div className="flex border-b border-[#e5e7eb] gap-1 pt-1">
                <button
                  type="button"
                  onClick={() => setSoapTab("s")}
                  className={`py-1.5 px-3 text-xs font-semibold rounded-t-[6px] border-b-2 cursor-pointer transition-all ${
                    soapTab === "s"
                      ? "border-[#111111] text-[#111111] bg-[#f8f9fa]"
                      : "border-transparent text-[#6b7280] hover:text-[#111111]"
                  }`}
                >
                  [S] Subjective (LOINC 61150-9)
                </button>
                <button
                  type="button"
                  onClick={() => setSoapTab("o")}
                  className={`py-1.5 px-3 text-xs font-semibold rounded-t-[6px] border-b-2 cursor-pointer transition-all ${
                    soapTab === "o"
                      ? "border-[#111111] text-[#111111] bg-[#f8f9fa]"
                      : "border-transparent text-[#6b7280] hover:text-[#111111]"
                  }`}
                >
                  [O] Objective (LOINC 61149-1)
                </button>
                <button
                  type="button"
                  onClick={() => setSoapTab("a")}
                  className={`py-1.5 px-3 text-xs font-semibold rounded-t-[6px] border-b-2 cursor-pointer transition-all ${
                    soapTab === "a"
                      ? "border-[#111111] text-[#111111] bg-[#f8f9fa]"
                      : "border-transparent text-[#6b7280] hover:text-[#111111]"
                  }`}
                >
                  [A] Assessment (LOINC 51848-0)
                </button>
                <button
                  type="button"
                  onClick={() => setSoapTab("p")}
                  className={`py-1.5 px-3 text-xs font-semibold rounded-t-[6px] border-b-2 cursor-pointer transition-all ${
                    soapTab === "p"
                      ? "border-[#111111] text-[#111111] bg-[#f8f9fa]"
                      : "border-transparent text-[#6b7280] hover:text-[#111111]"
                  }`}
                >
                  [P] Plan (LOINC 18776-5)
                </button>
              </div>

              {/* Active Tab Textarea */}
              <div className="space-y-3">
                {soapTab === "s" && (
                  <div>
                    <span className="block text-[11px] text-[#6b7280] mb-1">
                      Patient-reported history of present illness, symptom chronology, onset, lifestyle & risk factors:
                    </span>
                    <textarea
                      rows={4}
                      disabled={isSoapSigned}
                      value={subjectiveNotes}
                      onChange={(e) => setSubjectiveNotes(e.target.value)}
                      className="w-full p-3 rounded-[8px] border border-[#e5e7eb] text-xs sm:text-sm text-[#111111] focus:outline-none focus:ring-1 focus:ring-[#111111] disabled:bg-[#f8f9fa]"
                    />
                  </div>
                )}
                {soapTab === "o" && (
                  <div>
                    <span className="block text-[11px] text-[#6b7280] mb-1">
                      Physical examination findings, general condition, cardiovascular examination & vitals review:
                    </span>
                    <textarea
                      rows={4}
                      disabled={isSoapSigned}
                      value={objectiveNotes}
                      onChange={(e) => setObjectiveNotes(e.target.value)}
                      className="w-full p-3 rounded-[8px] border border-[#e5e7eb] text-xs sm:text-sm text-[#111111] focus:outline-none focus:ring-1 focus:ring-[#111111] disabled:bg-[#f8f9fa]"
                    />
                  </div>
                )}
                {soapTab === "a" && (
                  <div>
                    <span className="block text-[11px] text-[#6b7280] mb-1">
                      Clinical impression, diagnosis evaluation, disease staging, and differential diagnoses:
                    </span>
                    <textarea
                      rows={4}
                      disabled={isSoapSigned}
                      value={assessmentNotes}
                      onChange={(e) => setAssessmentNotes(e.target.value)}
                      className="w-full p-3 rounded-[8px] border border-[#e5e7eb] text-xs sm:text-sm text-[#111111] focus:outline-none focus:ring-1 focus:ring-[#111111] disabled:bg-[#f8f9fa]"
                    />
                  </div>
                )}
                {soapTab === "p" && (
                  <div>
                    <span className="block text-[11px] text-[#6b7280] mb-1">
                      Care management plan, medication regimens, diagnostic lab requisitions, and patient instructions:
                    </span>
                    <textarea
                      rows={4}
                      disabled={isSoapSigned}
                      value={planNotes}
                      onChange={(e) => setPlanNotes(e.target.value)}
                      className="w-full p-3 rounded-[8px] border border-[#e5e7eb] text-xs sm:text-sm text-[#111111] focus:outline-none focus:ring-1 focus:ring-[#111111] disabled:bg-[#f8f9fa]"
                    />
                  </div>
                )}
              </div>

              {!isSoapSigned && (
                <div className="pt-2 flex items-center justify-end gap-3 border-t border-[#e5e7eb]">
                  <Button
                    type="button"
                    variant="primary"
                    size="md"
                    onClick={handleSignSoapNote}
                    className="cursor-pointer"
                  >
                    <CheckCircle2 className="h-4 w-4 mr-1.5" />
                    Sign & Finalize SOAP Note (SHA-256)
                  </Button>
                </div>
              )}
            </Card>

            {/* E-Prescription Generator */}
            <Card variant="mockup" className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-[#111111]" />
                  <CardTitle className="text-base">Digital Prescription (MedicationRequest)</CardTitle>
                </div>
                <Badge variant="emerald" size="sm">FHIR Encoded</Badge>
              </div>

              {issuedPrescription ? (
                <div className="p-4 rounded-[8px] border border-[#a7f3d0] bg-[#ecfdf5] space-y-3 text-xs sm:text-sm animate-fade-in">
                  <div className="flex items-center gap-2 text-[#065f46] font-bold">
                    <CheckCircle2 className="h-5 w-5" />
                    <span>Prescription Signed & Synced to ABHA Health Locker</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[#065f46]/70">Medication</span>
                      <p className="font-semibold text-[#065f46]">{medication}</p>
                    </div>
                    <div>
                      <span className="text-[#065f46]/70">Dosage</span>
                      <p className="font-semibold text-[#065f46]">{dosage}</p>
                    </div>
                  </div>
                  <div className="pt-2 border-t border-[#a7f3d0] flex items-center justify-between text-[11px] text-[#065f46]">
                    <span>Digital Signature: SHA-256 Verified (HPR-91024)</span>
                    <button
                      type="button"
                      onClick={() => setIssuedPrescription(false)}
                      className="underline font-semibold cursor-pointer"
                    >
                      Issue Another
                    </button>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSignPrescription} className="space-y-3.5 text-xs sm:text-sm">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-[#111111] mb-1">
                        Prescribed Medication & Strength
                      </label>
                      <input
                        type="text"
                        required
                        value={medication}
                        onChange={(e) => setMedication(e.target.value)}
                        className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-xs sm:text-sm focus:outline-none focus:ring-1 focus:ring-[#111111]"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-[#111111] mb-1">
                        Dosage & Frequency Instructions
                      </label>
                      <input
                        type="text"
                        required
                        value={dosage}
                        onChange={(e) => setDosage(e.target.value)}
                        className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-xs sm:text-sm focus:outline-none focus:ring-1 focus:ring-[#111111]"
                      />
                    </div>
                  </div>

                  <div className="pt-2 flex items-center justify-end gap-3 border-t border-[#e5e7eb]">
                    <Button
                      type="submit"
                      variant="primary"
                      size="md"
                    >
                      <Send className="h-3.5 w-3.5 mr-1.5" />
                      Sign & Transmit to Patient ABHA
                    </Button>
                  </div>
                </form>
              )}
            </Card>

            {/* Diagnostic Lab Test Requisition Pad (Day 24 - ServiceRequest) */}
            <Card variant="mockup" className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#e5e7eb] gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <FlaskConical className="h-4 w-4 text-[#111111]" />
                    <CardTitle className="text-base sm:text-lg">
                      Diagnostic Lab Requisition (ServiceRequest)
                    </CardTitle>
                    <Badge variant="verified" size="sm">FHIR R4</Badge>
                  </div>
                  <CardDescription>
                    Clinician lab test orders • LOINC standard coding • Direct dispatch to pathology
                  </CardDescription>
                </div>
                <Badge variant="emerald" size="sm">{issuedOrders.length} Requisitions</Badge>
              </div>

              {orderIssuedSuccess && (
                <div className="p-3 rounded-[8px] border border-[#a7f3d0] bg-[#ecfdf5] text-xs text-[#065f46] flex items-center justify-between animate-fadeIn">
                  <div className="flex items-center gap-2 font-medium">
                    <CheckCircle2 className="h-4 w-4 text-[#059669] shrink-0" />
                    <span>Lab order authorized & queued for Apollo Diagnostics Central!</span>
                  </div>
                  <span className="font-mono text-[11px] text-[#047857]">FHIR ServiceRequest Active</span>
                </div>
              )}

              {/* Active Requisitions for Current Encounter */}
              {issuedOrders.length > 0 && (
                <div className="space-y-2">
                  <span className="text-[11px] font-bold text-[#6b7280] uppercase tracking-wider block">
                    Active Orders for {selectedPatient}
                  </span>
                  <div className="space-y-2">
                    {issuedOrders.map((ord) => (
                      <div
                        key={ord.id}
                        className="p-3 rounded-[8px] border border-[#e5e7eb] bg-[#f8f9fa] flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-[#111111]">{ord.display}</span>
                            <Badge variant={ord.priority === "stat" ? "critical" : ord.priority === "urgent" ? "warning" : "default"} size="sm">
                              {ord.priority.toUpperCase()}
                            </Badge>
                            {ord.fasting && (
                              <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-medium">
                                Fasting Required
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-[#6b7280]">
                            LOINC <span className="font-mono text-[#111111]">{ord.code}</span> • Specimen: <span className="capitalize">{ord.specimen}</span> • Reason: {ord.reason}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedOrderForFhir(ord);
                              setIsViewingOrderFhir(true);
                            }}
                            className="py-1 px-2.5 rounded-[6px] border border-[#e5e7eb] bg-white text-[11px] font-semibold text-[#111111] hover:bg-[#f3f4f6] transition-all flex items-center gap-1 cursor-pointer"
                          >
                            <Code className="h-3 w-3" />
                            FHIR JSON
                          </button>
                          <Badge variant="emerald" size="sm">DISPATCHED</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Order Requisition Form */}
              <form onSubmit={handleIssueLabOrder} className="space-y-3.5 pt-2 border-t border-[#e5e7eb] text-xs sm:text-sm">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-[#111111] mb-1">
                      Standard Diagnostic Test (LOINC)
                    </label>
                    <select
                      value={selectedLabTestCode}
                      onChange={(e) => handleTestPresetChange(e.target.value)}
                      className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-xs focus:outline-none focus:ring-1 focus:ring-[#111111] bg-white"
                    >
                      {LAB_TEST_PRESETS.map((t) => (
                        <option key={t.code} value={t.code}>
                          [{t.code}] {t.display}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-semibold text-[#111111] mb-1">
                        Order Priority
                      </label>
                      <select
                        value={labPriority}
                        onChange={(e) => setLabPriority(e.target.value as any)}
                        className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-xs focus:outline-none focus:ring-1 focus:ring-[#111111] bg-white"
                      >
                        <option value="routine">Routine</option>
                        <option value="urgent">Urgent</option>
                        <option value="stat">STAT (Emergency)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-[#111111] mb-1">
                        Specimen Type
                      </label>
                      <select
                        value={labSpecimen}
                        onChange={(e) => setLabSpecimen(e.target.value as any)}
                        className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-xs focus:outline-none focus:ring-1 focus:ring-[#111111] bg-white capitalize"
                      >
                        <option value="serum">Serum</option>
                        <option value="blood">Whole Blood</option>
                        <option value="plasma">Plasma</option>
                        <option value="urine">Urine</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-[#111111] mb-1">
                      Clinical Reason / Diagnostic Indication
                    </label>
                    <input
                      type="text"
                      required
                      value={labClinicalReason}
                      onChange={(e) => setLabClinicalReason(e.target.value)}
                      className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-xs focus:outline-none focus:ring-1 focus:ring-[#111111]"
                      placeholder="e.g. Assessment of hyperlipidemia"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#111111] mb-1">
                      Pathology & Specimen Instructions
                    </label>
                    <input
                      type="text"
                      value={labNotes}
                      onChange={(e) => setLabNotes(e.target.value)}
                      className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-xs focus:outline-none focus:ring-1 focus:ring-[#111111]"
                      placeholder="e.g. Fasting 10-12 hours required"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="labFastingCheckbox"
                    checked={labFasting}
                    onChange={(e) => setLabFasting(e.target.checked)}
                    className="h-4 w-4 rounded border-[#e5e7eb] text-[#111111] focus:ring-[#111111]"
                  />
                  <label htmlFor="labFastingCheckbox" className="text-xs text-[#374151] select-none cursor-pointer">
                    Require 10-12 hour overnight fasting prior to specimen collection
                  </label>
                </div>

                <div className="pt-2 flex items-center justify-end gap-3 border-t border-[#e5e7eb]">
                  <Button
                    type="submit"
                    variant="primary"
                    size="md"
                    className="cursor-pointer"
                  >
                    <FlaskConical className="h-3.5 w-3.5 mr-1.5" />
                    Authorize & Dispatch Lab Order (ServiceRequest)
                  </Button>
                </div>
              </form>
            </Card>

          </div>

        </div>
      )}

      {/* Record Clinical Vitals Modal Dialog */}
      {isRecordingVitals && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-[12px] border border-[#e5e7eb] shadow-xl max-w-md w-full p-6 space-y-5 animate-scaleUp">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div>
                <h3 className="text-base font-bold text-[#111111] flex items-center gap-2">
                  <Activity className="h-4 w-4 text-[#111111]" />
                  Record Clinical Vitals
                </h3>
                <p className="text-xs text-[#6b7280]">
                  Patient: <span className="font-semibold text-[#111111]">{selectedPatient}</span> (Encounter Examination)
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsRecordingVitals(false)}
                className="text-[#9ca3af] hover:text-[#111111] text-lg font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveVitals} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#111111] mb-1">
                    Systolic BP (mmHg)
                  </label>
                  <input
                    type="number"
                    min="60"
                    max="260"
                    required
                    value={newSystolic}
                    onChange={(e) => setNewSystolic(e.target.value)}
                    className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-sm focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                  <span className="text-[10px] text-[#6b7280]">LOINC 8480-6</span>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#111111] mb-1">
                    Diastolic BP (mmHg)
                  </label>
                  <input
                    type="number"
                    min="40"
                    max="150"
                    required
                    value={newDiastolic}
                    onChange={(e) => setNewDiastolic(e.target.value)}
                    className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-sm focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                  <span className="text-[10px] text-[#6b7280]">LOINC 8462-4</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#111111] mb-1">
                    Heart Rate (bpm)
                  </label>
                  <input
                    type="number"
                    min="30"
                    max="220"
                    required
                    value={newHr}
                    onChange={(e) => setNewHr(e.target.value)}
                    className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-sm focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                  <span className="text-[10px] text-[#6b7280]">LOINC 8867-4</span>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#111111] mb-1">
                    SpO2 Pulse Ox (%)
                  </label>
                  <input
                    type="number"
                    min="50"
                    max="100"
                    required
                    value={newSpo2}
                    onChange={(e) => setNewSpo2(e.target.value)}
                    className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] text-sm focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                  <span className="text-[10px] text-[#6b7280]">LOINC 2708-6</span>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-[#e5e7eb]">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsRecordingVitals(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                >
                  Save & Validate Reading
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Inspect HL7 FHIR R4 Composition Modal (Day 23) */}
      {isViewingSoapFhir && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-[12px] border border-[#e5e7eb] shadow-xl max-w-2xl w-full p-6 space-y-4 animate-scaleUp">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div>
                <h3 className="text-base font-bold text-[#111111] flex items-center gap-2">
                  <Code className="h-4 w-4 text-[#111111]" />
                  HL7 FHIR R4 Composition Resource
                </h3>
                <p className="text-xs text-[#6b7280]">
                  Document Type: LOINC 11506-3 Progress note • Patient: {selectedPatient}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsViewingSoapFhir(false)}
                className="text-[#9ca3af] hover:text-[#111111] text-lg font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <pre className="p-3.5 rounded-[8px] bg-[#111111] text-[#f8f9fa] text-xs font-mono overflow-auto max-h-[380px]">
              {JSON.stringify(
                {
                  resourceType: "Composition",
                  id: "soap-encounter-01",
                  status: isSoapSigned ? "final" : "preliminary",
                  type: {
                    coding: [
                      {
                        system: "http://loinc.org",
                        code: "11506-3",
                        display: "Provider-unspecified Progress note",
                      },
                    ],
                    text: "Cardiology Follow-up SOAP Note",
                  },
                  subject: {
                    reference: `Patient/${selectedPatient.toLowerCase().replace(" ", "-")}`,
                    display: selectedPatient,
                  },
                  author: [
                    {
                      reference: "Practitioner/doc-ananya-sharma",
                      display: "Dr. Ananya Sharma (DMC-2026-9901)",
                    },
                  ],
                  section: [
                    {
                      title: "Chief Complaint",
                      code: {
                        coding: [
                          { system: "http://loinc.org", code: "10154-3", display: "Chief complaint narrative" },
                        ],
                      },
                      text: { status: "generated", div: `<div>${chiefComplaint}</div>` },
                    },
                    {
                      title: "Subjective",
                      code: {
                        coding: [
                          { system: "http://loinc.org", code: "61150-9", display: "Subjective narrative" },
                        ],
                      },
                      text: { status: "generated", div: `<div>${subjectiveNotes}</div>` },
                    },
                    {
                      title: "Objective",
                      code: {
                        coding: [
                          { system: "http://loinc.org", code: "61149-1", display: "Objective narrative" },
                        ],
                      },
                      text: { status: "generated", div: `<div>${objectiveNotes}</div>` },
                    },
                    {
                      title: "Assessment",
                      code: {
                        coding: [
                          { system: "http://loinc.org", code: "51848-0", display: "Evaluation note" },
                        ],
                      },
                      text: { status: "generated", div: `<div>${assessmentNotes}</div>` },
                    },
                    {
                      title: "Plan",
                      code: {
                        coding: [
                          { system: "http://loinc.org", code: "18776-5", display: "Plan of care note" },
                        ],
                      },
                      text: { status: "generated", div: `<div>${planNotes}</div>` },
                    },
                  ],
                },
                null,
                2
              )}
            </pre>

            <div className="pt-2 flex items-center justify-end border-t border-[#e5e7eb]">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsViewingSoapFhir(false)}
              >
                Close Preview
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Inspect HL7 FHIR R4 ServiceRequest Modal (Day 24) */}
      {isViewingOrderFhir && selectedOrderForFhir && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-[12px] border border-[#e5e7eb] shadow-xl max-w-2xl w-full p-6 space-y-4 animate-scaleUp">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div>
                <h3 className="text-base font-bold text-[#111111] flex items-center gap-2">
                  <Code className="h-4 w-4 text-[#111111]" />
                  HL7 FHIR R4 ServiceRequest Resource
                </h3>
                <p className="text-xs text-[#6b7280]">
                  Requisition ID: {selectedOrderForFhir.id} • LOINC {selectedOrderForFhir.code}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsViewingOrderFhir(false)}
                className="text-[#9ca3af] hover:text-[#111111] text-lg font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <pre className="p-3.5 rounded-[8px] bg-[#111111] text-[#f8f9fa] text-xs font-mono overflow-auto max-h-[380px]">
              {JSON.stringify(
                {
                  resourceType: "ServiceRequest",
                  id: selectedOrderForFhir.id,
                  meta: {
                    profile: ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/ServiceRequest"],
                  },
                  status: selectedOrderForFhir.status,
                  intent: "order",
                  priority: selectedOrderForFhir.priority,
                  category: [
                    {
                      coding: [
                        {
                          system: "http://snomed.info/sct",
                          code: "108252007",
                          display: "Laboratory procedure",
                        },
                      ],
                      text: "Laboratory",
                    },
                  ],
                  code: {
                    coding: [
                      {
                        system: "http://loinc.org",
                        code: selectedOrderForFhir.code,
                        display: selectedOrderForFhir.display,
                      },
                    ],
                    text: selectedOrderForFhir.display,
                  },
                  subject: {
                    reference: `Patient/${selectedPatient.toLowerCase().replace(" ", "-")}`,
                    display: selectedPatient,
                  },
                  requester: {
                    reference: "Practitioner/doc-ananya-sharma",
                    display: "Dr. Ananya Sharma",
                  },
                  authoredOn: new Date().toISOString(),
                  reasonCode: [
                    {
                      text: selectedOrderForFhir.reason,
                    },
                  ],
                  specimen: [
                    {
                      display: `${selectedOrderForFhir.specimen.toUpperCase()} specimen (${selectedOrderForFhir.fasting ? "12hr fasting" : "routine"})`,
                    },
                  ],
                  note: [
                    {
                      text: labNotes,
                    },
                  ],
                },
                null,
                2
              )}
            </pre>

            <div className="pt-2 flex items-center justify-end border-t border-[#e5e7eb]">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsViewingOrderFhir(false)}
              >
                Close Preview
              </Button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
