"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Button, Badge, Card, CardTitle, CardDescription } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import { 
  Stethoscope, 
  Calendar, 
  Clock, 
  FileText, 
  CheckCircle2, 
  User, 
  Activity, 
  Video, 
  FlaskConical, 
  ShieldCheck, 
  Pill,
  Heart,
  AlertTriangle,
  Play,
  ArrowRight,
  Sparkles,
  ExternalLink
} from "lucide-react";
import { DoctorSlotManager } from "@/components/appointments";
import { 
  ProblemListPanel, 
  VitalsTelemetryPanel, 
  SoapNoteEditor, 
  DiagnosticOrderTracker,
  MedicationCatalogBrowser,
  PrescriptionAuthoringPad,
  ClinicianConsultationQueue,
  QueueAppointment,
  PatientDemographicBanner,
  PatientDemographics,
  ClinicalQuickActionRail,
  ClinicalTabType,
  INITIAL_MOCK_QUEUE
} from "@/components/clinical";
import { TelemedicineReadinessModal } from "@/components/patient";
import { SoapNote } from "@/lib/api";

const PATIENT_PROFILES: Record<string, PatientDemographics> = {
  "Arun Patel": {
    id: "pat-arun-patel-01",
    name: "Arun Patel",
    age: 36,
    gender: "Male",
    dateOfBirth: "1990-06-04",
    bloodGroup: "O+",
    abhaNumber: "91-8472-1092-4821",
    abhaAddress: "arun.patel@abdm",
    phone: "+91 98765 43210",
    emergencyContact: {
      name: "Pooja Patel",
      relationship: "Spouse",
      phone: "+91 98765 09991",
    },
    primaryConditions: [
      {
        code: "38341003",
        display: "Essential hypertension",
        codingSystem: "SNOMED-CT",
        severity: "moderate",
      },
      {
        code: "44054006",
        display: "Type 2 diabetes mellitus",
        codingSystem: "SNOMED-CT",
        severity: "mild",
      },
    ],
    allergies: [
      {
        substance: "Penicillin V",
        criticality: "high",
        manifestation: "Severe Anaphylaxis",
      },
    ],
    latestVitals: {
      bp: "138/88 mmHg",
      bpStatus: "high",
      hr: "74 bpm",
      spo2: "98%",
      bmi: "24.2 kg/m²",
      temperature: "36.8°C",
      recordedAt: "Today, 10:05 AM",
    },
    activeMedicationsCount: 2,
    recentEncountersCount: 3,
  },
  "Priya Nair": {
    id: "pat-priya-nair-02",
    name: "Priya Nair",
    age: 42,
    gender: "Female",
    dateOfBirth: "1984-09-12",
    bloodGroup: "B+",
    abhaNumber: "91-9988-7766-5544",
    abhaAddress: "priya.nair@abdm",
    phone: "+91 98123 45678",
    emergencyContact: {
      name: "Rajesh Nair",
      relationship: "Brother",
      phone: "+91 98111 22334",
    },
    primaryConditions: [
      {
        code: "426749004",
        display: "Chronic paroxysmal tachycardia",
        codingSystem: "SNOMED-CT",
        severity: "moderate",
      },
    ],
    allergies: [
      {
        substance: "Ibuprofen / NSAIDs",
        criticality: "high",
        manifestation: "Severe Bronchospasm",
      },
    ],
    latestVitals: {
      bp: "126/82 mmHg",
      bpStatus: "normal",
      hr: "88 bpm",
      spo2: "99%",
      bmi: "22.8 kg/m²",
      temperature: "37.0°C",
    },
    activeMedicationsCount: 1,
    recentEncountersCount: 1,
  },
  "Vikram Malhotra": {
    id: "pat-vikram-malhotra-01",
    name: "Vikram Malhotra",
    age: 38,
    gender: "Male",
    dateOfBirth: "1988-11-20",
    bloodGroup: "B+",
    abhaNumber: "91-3322-1144-5566",
    abhaAddress: "vikram.malhotra@abdm",
    phone: "+91 98222 33445",
    primaryConditions: [
      {
        code: "370992007",
        display: "Dyslipidemia",
        codingSystem: "SNOMED-CT",
        severity: "mild",
      },
    ],
    latestVitals: {
      bp: "122/78 mmHg",
      bpStatus: "normal",
      hr: "68 bpm",
      spo2: "99%",
      bmi: "23.5 kg/m²",
    },
    activeMedicationsCount: 1,
    recentEncountersCount: 2,
  },
  "Anita Deshmukh": {
    id: "pat-anita-deshmukh-04",
    name: "Anita Deshmukh",
    age: 51,
    gender: "Female",
    dateOfBirth: "1975-03-14",
    bloodGroup: "A+",
    abhaNumber: "91-6677-8899-0011",
    abhaAddress: "anita.deshmukh@abdm",
    phone: "+91 98333 44556",
    primaryConditions: [
      {
        code: "414024009",
        display: "Coronary artery disease post-PCI",
        codingSystem: "SNOMED-CT",
        severity: "mild",
      },
    ],
    latestVitals: {
      bp: "118/76 mmHg",
      bpStatus: "normal",
      hr: "70 bpm",
      spo2: "99%",
      bmi: "25.1 kg/m²",
    },
    activeMedicationsCount: 3,
    recentEncountersCount: 4,
  },
};

export default function DoctorEMRPage() {
  const { user } = useAuth();
  const doctorId = user?.id || "doc-ananya-sharma";
  const doctorName = user?.fullName || "Dr. Ananya Sharma";

  const [activeTab, setActiveTab] = useState<ClinicalTabType>("queue");
  const [selectedAppointment, setSelectedAppointment] = useState<QueueAppointment>(INITIAL_MOCK_QUEUE[0]);
  const [selectedPatientName, setSelectedPatientName] = useState<string>("Arun Patel");
  const [isTelemedicineModalOpen, setIsTelemedicineModalOpen] = useState(false);
  const [signedNotes, setSignedNotes] = useState<Record<string, SoapNote>>({});
  const [noteAttestationSuccess, setNoteAttestationSuccess] = useState<string | null>(null);
  const [prescriptionSuccess, setPrescriptionSuccess] = useState<string | null>(null);

  // Clinician Keyboard Ergonomics: Alt+1..Alt+6 (and fast number keys outside form inputs)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const isInput = target && (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable ||
        target.tagName === "SELECT"
      );

      const tabMap: Record<string, ClinicalTabType> = {
        "1": "queue",
        "2": "soap",
        "3": "prescriptions",
        "4": "diagnostics",
        "5": "problems",
        "6": "vitals",
      };

      if (e.altKey && tabMap[e.key]) {
        e.preventDefault();
        setActiveTab(tabMap[e.key]);
      } else if (!e.altKey && !e.ctrlKey && !e.metaKey && !isInput && tabMap[e.key]) {
        // Fast tab switch for active clinician when browsing panels
        setActiveTab(tabMap[e.key]);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Active patient profile derived from selected appointment or selected name
  const activePatient: PatientDemographics = 
    PATIENT_PROFILES[selectedPatientName] || 
    PATIENT_PROFILES["Arun Patel"];

  const isTelemed = selectedAppointment?.appointmentType === "teleconsultation";

  const handleSelectAppointment = (appt: QueueAppointment) => {
    setSelectedAppointment(appt);
    setSelectedPatientName(appt.patientName);
  };

  const handleStartConsultation = (appt: QueueAppointment) => {
    setSelectedAppointment(appt);
    setSelectedPatientName(appt.patientName);
  };

  const handleLaunchTelemedicine = (appt?: QueueAppointment) => {
    if (appt) {
      setSelectedAppointment(appt);
      setSelectedPatientName(appt.patientName);
    }
    setIsTelemedicineModalOpen(true);
  };

  const handleNoteSigned = (note: SoapNote) => {
    setSignedNotes((prev) => ({
      ...prev,
      [activePatient.id]: note,
    }));
    setNoteAttestationSuccess(
      `Encounter SOAP documentation for ${activePatient.name} has been cryptographically signed and sealed under IMC standards.`
    );
    setTimeout(() => setNoteAttestationSuccess(null), 6000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 bg-white min-h-screen">
      
      {/* 1. Top Clinician Practice Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-3.5">
          <div className="h-12 w-12 rounded-full bg-[#111111] text-white flex items-center justify-center font-bold text-base shrink-0 shadow-xs">
            AS
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#111827]">
                {doctorName}
              </h1>
              <Badge variant="verified">HPR Verified</Badge>
            </div>
            <p className="text-xs text-[#6B7280]">
              Chief Cardiologist • AIIMS New Delhi • HPR:{" "}
              <span className="font-mono text-[#111827]">ananya.sharma@hpr.abdm</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Badge variant="emerald" size="sm">Clinical Session Active</Badge>
          <Link href="/patient">
            <Button variant="secondary" size="sm">
              Switch to Patient View
            </Button>
          </Link>
        </div>
      </div>

      {/* 2. Active Patient Demographic & Clinical Banner */}
      <PatientDemographicBanner
        patient={activePatient}
        encounterReason={selectedAppointment?.reason}
        isConsultationActive={selectedAppointment?.status === "in_progress"}
        onViewFullRecord={() => setActiveTab("problems")}
        onLaunchTelemedicine={isTelemed ? () => handleLaunchTelemedicine() : undefined}
      />

      {/* 3. Clinical Quick Action Rail (Cal.com Tabs) */}
      <ClinicalQuickActionRail
        activeTab={activeTab}
        onChangeTab={(tab) => setActiveTab(tab)}
        onLaunchTelemedicine={() => handleLaunchTelemedicine()}
        isTelemedicineEncounter={isTelemed}
      />

      {/* 4. Main Tab Content Views */}
      {activeTab === "slots" ? (
        <div className="animate-fade-in">
          <DoctorSlotManager
            doctorId={doctorId}
            doctorName={doctorName}
          />
        </div>
      ) : activeTab === "soap" ? (
        <div className="animate-fade-in max-w-5xl mx-auto space-y-4">
          {noteAttestationSuccess && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center justify-between animate-in fade-in">
              <div className="flex items-center gap-2 font-medium">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                <span>{noteAttestationSuccess}</span>
              </div>
              <button
                type="button"
                onClick={() => setActiveTab("prescriptions")}
                className="underline font-semibold hover:text-emerald-950 flex items-center gap-1 cursor-pointer"
              >
                <span>Proceed to e-Prescriptions</span>
                <ArrowRight className="h-3 w-3" />
              </button>
            </div>
          )}
          <SoapNoteEditor
            key={activePatient.id}
            patientId={activePatient.id}
            patientName={activePatient.name}
            doctorId={doctorId}
            doctorName={doctorName}
            doctorSpecialty="Consultant Physician / Cardiology"
            doctorRegNumber="MCI-2015-84920"
            encounterId={selectedAppointment?.id}
            initialNote={signedNotes[activePatient.id]}
            prefilledVitals={activePatient.latestVitals}
            prefilledConditions={activePatient.primaryConditions}
            onNoteSigned={handleNoteSigned}
          />
        </div>
      ) : activeTab === "diagnostics" ? (
        <div className="animate-fade-in max-w-5xl mx-auto">
          <DiagnosticOrderTracker
            key={activePatient.id}
            patientId={activePatient.id}
            patientName={activePatient.name}
            doctorId={doctorId}
            isDoctorView={true}
          />
        </div>
      ) : activeTab === "problems" ? (
        <div className="animate-fade-in max-w-5xl mx-auto">
          <ProblemListPanel
            patientId={activePatient.id}
            patientName={activePatient.name}
            isDoctorView={true}
          />
        </div>
      ) : activeTab === "vitals" ? (
        <div className="animate-fade-in max-w-5xl mx-auto">
          <VitalsTelemetryPanel
            patientId={activePatient.id}
            patientName={activePatient.name}
            isDoctorView={true}
          />
        </div>
      ) : activeTab === "medications" ? (
        <div className="animate-fade-in max-w-5xl mx-auto">
          <MedicationCatalogBrowser />
        </div>
      ) : activeTab === "prescriptions" ? (
        <div className="animate-fade-in max-w-5xl mx-auto space-y-4">
          {prescriptionSuccess && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center justify-between animate-in fade-in shadow-xs">
              <div className="flex items-center gap-2 font-medium">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                <span>{prescriptionSuccess}</span>
              </div>
              <button
                type="button"
                onClick={() => setActiveTab("diagnostics")}
                className="underline font-semibold hover:text-emerald-950 flex items-center gap-1 cursor-pointer shrink-0"
              >
                <span>Order Lab Panels</span>
                <ArrowRight className="h-3 w-3" />
              </button>
            </div>
          )}
          <PrescriptionAuthoringPad
            key={activePatient.id}
            patientId={activePatient.id}
            patientName={activePatient.name}
            doctorId={doctorId}
            doctorName={doctorName}
            doctorSpecialty="Consultant Physician / Cardiology"
            doctorRegNumber="MCI-2015-84920"
            encounterId={selectedAppointment?.id}
            onPrescriptionSigned={() => {
              setPrescriptionSuccess(
                `Prescription successfully signed and sealed with SHA-256 for ${activePatient.name}. Transmitted to patient vault.`
              );
              setTimeout(() => setPrescriptionSuccess(null), 6000);
            }}
          />
        </div>
      ) : (
        /* ========================================================================
           ACTIVE CONSULTATION QUEUE & EMR INTERFACE (Day 36 Milestone 08-01)
           ======================================================================== */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in">
          
          {/* Left Column (5 Cols): Real-time Clinician Consultation Queue */}
          <div className="lg:col-span-5 space-y-4">
            <Card variant="mockup" className="p-4 sm:p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-[#111827]" />
                  <CardTitle className="text-base">Consultation Queue</CardTitle>
                </div>
                <Badge variant="default" size="sm">
                  {INITIAL_MOCK_QUEUE.length} Encounters
                </Badge>
              </div>

              <ClinicianConsultationQueue
                doctorId={doctorId}
                selectedAppointmentId={selectedAppointment?.id}
                onSelectAppointment={handleSelectAppointment}
                onStartConsultation={handleStartConsultation}
                onLaunchTelemedicine={handleLaunchTelemedicine}
                onCompleteConsultation={(id) => {
                  if (selectedAppointment?.id === id) {
                    setSelectedAppointment((prev) => ({ ...prev, status: "completed" }));
                  }
                }}
              />

              {/* Bottom Quick Action to Manage Slots */}
              <div className="pt-3 border-t border-[#E5E7EB]">
                <button
                  type="button"
                  onClick={() => setActiveTab("slots")}
                  className="w-full py-2 px-3 rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] text-xs font-semibold text-[#111827] hover:bg-[#E5E7EB] transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <Sparkles className="h-3.5 w-3.5 text-[#059669]" />
                  Manage Daily Practice Availability Slots
                </button>
              </div>
            </Card>
          </div>

          {/* Right Column (7 Cols): Active Encounter Cockpit & Quick Documentation Actions */}
          <div className="lg:col-span-7 space-y-5">
            
            {/* 1. Active Encounter Header Card */}
            <Card variant="mockup" className="p-5 space-y-4">
              <div className="flex items-start justify-between pb-3 border-b border-[#E5E7EB] gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-lg">
                      Encounter: {selectedAppointment?.patientName || activePatient.name}
                    </CardTitle>
                    {selectedAppointment?.status === "in_progress" ? (
                      <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#059669] bg-[#ECFDF5] px-2.5 py-0.5 rounded-md border border-[#A7F3D0]">
                        <span className="h-2 w-2 rounded-full bg-[#059669] animate-pulse" />
                        In Progress
                      </span>
                    ) : selectedAppointment?.status === "completed" ? (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#6B7280] bg-[#F3F4F6] px-2 py-0.5 rounded-md">
                        <CheckCircle2 className="h-3 w-3 text-[#059669]" />
                        Completed
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#D97706] bg-[#FEF3C7] px-2 py-0.5 rounded-md">
                        Waiting in Queue
                      </span>
                    )}
                  </div>
                  <CardDescription className="mt-0.5">
                    {selectedAppointment?.scheduledDate || "Today"} • {selectedAppointment?.scheduledTime || "10:15 AM"} • {isTelemed ? "Teleconsultation (WebRTC Video)" : "In-Clinic Visit"}
                  </CardDescription>
                </div>

                {isTelemed && (
                  <button
                    type="button"
                    onClick={() => handleLaunchTelemedicine()}
                    className="py-1.5 px-3 rounded-lg border border-[#2563EB] bg-[#2563EB] text-white text-xs font-semibold hover:bg-[#1D4ED8] transition-all flex items-center gap-1.5 cursor-pointer shadow-xs shrink-0"
                  >
                    <Video className="h-3.5 w-3.5" />
                    <span>Join Video</span>
                  </button>
                )}
              </div>

              {/* Chief Reason Box */}
              <div className="p-3.5 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB] text-xs space-y-1">
                <span className="font-semibold text-[#111827] block">
                  Chief Complaint / Encounter Reason:
                </span>
                <p className="text-[#4B5563]">
                  {selectedAppointment?.reason || "Quarterly cardiovascular review and blood pressure evaluation."}
                </p>
              </div>

              {/* One-Click Clinical Workflow Launchers */}
              <div className="space-y-2 pt-1">
                <h4 className="text-xs font-bold text-[#111827] uppercase tracking-wider">
                  Clinical Encounter Actions
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  <button
                    type="button"
                    onClick={() => setActiveTab("soap")}
                    className="p-3 rounded-lg border border-[#E5E7EB] bg-white hover:border-[#111827] hover:bg-[#F9FAFB] transition-all text-left flex items-start gap-3 cursor-pointer group"
                  >
                    <div className="p-2 rounded-md bg-[#F3F4F6] text-[#111827] group-hover:bg-[#111111] group-hover:text-white transition-all">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#111827] flex items-center gap-1">
                        SOAP Encounter Pad
                        <ArrowRight className="h-3 w-3 text-[#9CA3AF] group-hover:translate-x-0.5 transition-all" />
                      </div>
                      <div className="text-[11px] text-[#6B7280]">
                        Record S-O-A-P narrative & sign FHIR Composition
                      </div>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab("prescriptions")}
                    className="p-3 rounded-lg border border-[#E5E7EB] bg-white hover:border-[#111827] hover:bg-[#F9FAFB] transition-all text-left flex items-start gap-3 cursor-pointer group"
                  >
                    <div className="p-2 rounded-md bg-[#ECFDF5] text-[#059669] group-hover:bg-[#059669] group-hover:text-white transition-all">
                      <Pill className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#111827] flex items-center gap-1">
                        Author e-Prescription
                        <ArrowRight className="h-3 w-3 text-[#9CA3AF] group-hover:translate-x-0.5 transition-all" />
                      </div>
                      <div className="text-[11px] text-[#6B7280]">
                        RxNorm formulary search with instant DDI checks
                      </div>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab("diagnostics")}
                    className="p-3 rounded-lg border border-[#E5E7EB] bg-white hover:border-[#111827] hover:bg-[#F9FAFB] transition-all text-left flex items-start gap-3 cursor-pointer group"
                  >
                    <div className="p-2 rounded-md bg-[#EFF6FF] text-[#2563EB] group-hover:bg-[#2563EB] group-hover:text-white transition-all">
                      <FlaskConical className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#111827] flex items-center gap-1">
                        Order Lab Panels
                        <ArrowRight className="h-3 w-3 text-[#9CA3AF] group-hover:translate-x-0.5 transition-all" />
                      </div>
                      <div className="text-[11px] text-[#6B7280]">
                        LOINC requisitions for Lipid, CBC, Glucose
                      </div>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab("problems")}
                    className="p-3 rounded-lg border border-[#E5E7EB] bg-white hover:border-[#111827] hover:bg-[#F9FAFB] transition-all text-left flex items-start gap-3 cursor-pointer group"
                  >
                    <div className="p-2 rounded-md bg-[#FEF3C7] text-[#D97706] group-hover:bg-[#D97706] group-hover:text-white transition-all">
                      <Heart className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#111827] flex items-center gap-1">
                        Longitudinal Problem List
                        <ArrowRight className="h-3 w-3 text-[#9CA3AF] group-hover:translate-x-0.5 transition-all" />
                      </div>
                      <div className="text-[11px] text-[#6B7280]">
                        Manage SNOMED-CT / ICD-10 conditions
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Vitals & Telemetry Overview */}
              <div className="pt-2 border-t border-[#E5E7EB]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-[#111827] uppercase tracking-wider">
                    Recent Vitals & Telemetry
                  </span>
                  <button
                    type="button"
                    onClick={() => setActiveTab("vitals")}
                    className="text-xs text-[#2563EB] font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <span>Full Observational Graph</span>
                    <ArrowRight className="h-3 w-3" />
                  </button>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                    <span className="text-[10px] text-[#6B7280] block">Blood Pressure</span>
                    <span className="font-bold text-[#111827]">
                      {activePatient.latestVitals?.bp || "138/88 mmHg"}
                    </span>
                    <span className="text-[9px] uppercase font-bold text-[#DC2626] block">
                      AHA Stage 1
                    </span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                    <span className="text-[10px] text-[#6B7280] block">Heart Rate</span>
                    <span className="font-bold text-[#111827]">
                      {activePatient.latestVitals?.hr || "74 bpm"}
                    </span>
                    <span className="text-[9px] uppercase font-bold text-[#059669] block">
                      Normal Sinus
                    </span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                    <span className="text-[10px] text-[#6B7280] block">Oxygen (SpO2)</span>
                    <span className="font-bold text-[#059669]">
                      {activePatient.latestVitals?.spo2 || "98%"}
                    </span>
                    <span className="text-[9px] uppercase font-bold text-[#059669] block">
                      Optimal
                    </span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                    <span className="text-[10px] text-[#6B7280] block">Body Mass Index</span>
                    <span className="font-bold text-[#111827]">
                      {activePatient.latestVitals?.bmi || "24.2 kg/m²"}
                    </span>
                    <span className="text-[9px] uppercase font-bold text-[#059669] block">
                      Normal BMI
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            {/* 2. ABDM Interoperability & Security Assurance */}
            <div className="p-4 rounded-xl border border-[#A7F3D0] bg-[#ECFDF5] text-xs flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="h-5 w-5 text-[#059669] shrink-0" />
                <div>
                  <div className="font-bold text-[#065F46]">
                    ABDM Health Information Provider (HIP) Session Active
                  </div>
                  <div className="text-[11px] text-[#047857]">
                    All encounters, SOAP narratives, and diagnostic orders are cryptographically signed and linkable to patient ABHA CareContexts.
                  </div>
                </div>
              </div>
              <Badge variant="abdm" size="sm">NRCeS Compliant</Badge>
            </div>

          </div>

        </div>
      )}

      {/* 5. Telemedicine Consultation Readiness & WebRTC Diagnostics Modal */}
      <TelemedicineReadinessModal
        isOpen={isTelemedicineModalOpen}
        onClose={() => setIsTelemedicineModalOpen(false)}
        doctorName={doctorName}
        doctorSpecialty="Chief Cardiologist, AIIMS"
        appointmentTime={`${selectedAppointment?.scheduledDate || "Today"}, ${selectedAppointment?.scheduledTime || "10:15 AM"}`}
        roomToken={`nirmaya-webrtc-${selectedAppointment?.id || "telemed-01"}`}
        onJoinRoom={() => {
          setIsTelemedicineModalOpen(false);
          setActiveTab("soap");
        }}
      />

    </div>
  );
}
