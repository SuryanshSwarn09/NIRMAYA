"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { 
  PatientHeader, 
  PatientMetricsBar, 
  PatientNavTabs, 
  PatientOverviewTab, 
  PatientPrescriptionsTab, 
  PatientRecordsTab, 
  PatientModals,
  AbhaCardExportModal,
  AbhaQrVerificationModal,
  PatientTabId 
} from "@/components/patient";
import { 
  ClinicalSlotPicker, 
  AppointmentBookingModal 
} from "@/components/appointments";
import { ProblemListPanel } from "@/components/clinical";
import { Badge } from "@/components/ui";
import { 
  apiClient, 
  DoctorSlot, 
  SlotHoldResponse, 
  Appointment, 
  MedicationRequest 
} from "@/lib/api";

const CLINICIANS = [
  {
    id: "doc-ananya-sharma",
    name: "Dr. Ananya Sharma",
    specialty: "Chief Cardiologist",
    affiliation: "AIIMS New Delhi",
    fee: 1500,
    hpr: "ananya.sharma@hpr.abdm",
  },
  {
    id: "doc-rajesh-varma",
    name: "Dr. Rajesh Varma",
    specialty: "Consultant Physician",
    affiliation: "Fortis Escorts Heart Institute",
    fee: 1200,
    hpr: "rajesh.varma@hpr.abdm",
  },
  {
    id: "doc-kv-raman",
    name: "Dr. K. V. Raman",
    specialty: "Senior Dermatologist",
    affiliation: "Apollo Hospital Delhi",
    fee: 1000,
    hpr: "kv.raman@hpr.abdm",
  },
];

export default function PatientVaultPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<PatientTabId>("overview");
  const [consentActive, setConsentActive] = useState(true);

  // ABHA ID Card & QR Verification States (Day 32)
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);
  const [abhaCardData, setAbhaCardData] = useState<{
    abhaId: string;
    abhaAddress: string;
    patientName: string;
    gender: string;
    dob: string;
    mobile: string;
    bloodGroup: string;
    stateNode: string;
    distName: string;
    emergencyContact: string;
    organDonor: boolean;
    qrPayload: string;
  }>({
    abhaId: user?.abhaId || "91-8472-1092-4821",
    abhaAddress: "arun.patel@abdm",
    patientName: user?.fullName || "Arun Patel",
    gender: "Male",
    dob: "1990-06-04",
    mobile: "+91 98*** **421",
    bloodGroup: "O Positive (O+)",
    stateNode: "NCT of Delhi",
    distName: "South Delhi",
    emergencyContact: "Pooja Patel (+91 98*** **991)",
    organDonor: true,
    qrPayload: "",
  });

  // Attempt to load official ABHA card from backend if patient profile exists
  useEffect(() => {
    async function loadAbhaCard() {
      try {
        const patientId = user?.id || "pat-arun-patel";
        const res = await apiClient.getPatientAbhaCard(patientId);
        if (res && res.card_data) {
          setAbhaCardData({
            abhaId: res.card_data.abha_number || "91-8472-1092-4821",
            abhaAddress: res.card_data.abha_address || "arun.patel@abdm",
            patientName: res.card_data.name || user?.fullName || "Arun Patel",
            gender: res.card_data.gender === "M" ? "Male" : res.card_data.gender === "F" ? "Female" : "Other",
            dob: res.card_data.date_of_birth || "1990-06-04",
            mobile: res.card_data.mobile || "+91 98*** **421",
            bloodGroup: res.card_data.blood_group || "O Positive (O+)",
            stateNode: res.card_data.state || "NCT of Delhi",
            distName: res.card_data.district || "South Delhi",
            emergencyContact: res.card_data.emergency_contact_name 
              ? `${res.card_data.emergency_contact_name} (${res.card_data.emergency_contact_phone || ""})`
              : "Pooja Patel (+91 98*** **991)",
            organDonor: true,
            qrPayload: res.qr_payload || "",
          });
        }
      } catch (err) {
        // Fallback gracefully to default seeded identity
        console.info("Using local ABDM card identity", err);
      }
    }
    loadAbhaCard();
  }, [user?.id, user?.fullName, user?.abhaId]);

  // E-Prescriptions & Medication Tracker State (Day 27 & Day 29)
  const [prescriptions, setPrescriptions] = useState<MedicationRequest[]>([]);
  const [loadingPrescriptions, setLoadingPrescriptions] = useState(false);
  const [viewingFhirRx, setViewingFhirRx] = useState<Record<string, any> | null>(null);
  const [fetchingFhirId, setFetchingFhirId] = useState<string | null>(null);

  const loadPrescriptions = async () => {
    try {
      setLoadingPrescriptions(true);
      const res = await apiClient.getPatientPrescriptions(user?.id || "pat-arun-patel");
      if (res.items) {
        setPrescriptions(res.items);
      }
    } catch (err) {
      console.warn("Could not load real patient prescriptions, using fallback records", err);
    } finally {
      setLoadingPrescriptions(false);
    }
  };

  useEffect(() => {
    loadPrescriptions();
  }, [user?.id]);

  // Selected Clinician for Booking (Day 19)
  const [selectedDoctor, setSelectedDoctor] = useState(CLINICIANS[0]);
  const [selectedSlot, setSelectedSlot] = useState<DoctorSlot | null>(null);
  const [activeHold, setActiveHold] = useState<SlotHoldResponse | null>(null);
  const [isHolding, setIsHolding] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Scheduled Appointments List
  const [scheduledAppointments, setScheduledAppointments] = useState<Appointment[]>([
    {
      id: "686523ba-744c-4bb7-925b-4f88eefcd269",
      patient_id: "pat-arun-patel",
      doctor_id: "doc-ananya-sharma",
      doctor_name: "Dr. Ananya Sharma",
      doctor_specialty: "Chief Cardiologist",
      appointment_type: "routine_checkup",
      status: "confirmed",
      scheduled_start: new Date(Date.now() + 86400000 * 2).toISOString(),
      scheduled_end: new Date(Date.now() + 86400000 * 2 + 1800000).toISOString(),
      reason: "Quarterly cardiovascular review and blood pressure evaluation",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ]);

  // Vitals & Observational Telemetry State (Day 22)
  const [vitalsList, setVitalsList] = useState<any[]>([
    {
      id: "obs-bp-01",
      code_value: "85354-9",
      code_display: "Blood Pressure Panel",
      value_quantity: null,
      value_unit: "mmHg",
      interpretation: "high",
      components: [
        { code_value: "8480-6", code_display: "Systolic", value_quantity: 134, value_unit: "mmHg", interpretation: "high" },
        { code_value: "8462-4", code_display: "Diastolic", value_quantity: 86, value_unit: "mmHg", interpretation: "high" },
      ],
      effective_date_time: "Today, 10:15 AM",
      method: "Automated oscillometric",
    },
    {
      id: "obs-hr-01",
      code_value: "8867-4",
      code_display: "Heart Rate",
      value_quantity: 72,
      value_unit: "/min",
      interpretation: "normal",
      reference_range_text: "60 - 100 /min",
      effective_date_time: "Today, 10:15 AM",
    },
    {
      id: "obs-spo2-01",
      code_value: "2708-6",
      code_display: "Oxygen Saturation (SpO2)",
      value_quantity: 98,
      value_unit: "%",
      interpretation: "normal",
      reference_range_text: "95 - 100 %",
      effective_date_time: "Today, 10:15 AM",
    },
    {
      id: "obs-bmi-01",
      code_value: "39156-5",
      code_display: "Body Mass Index (BMI)",
      value_quantity: 24.2,
      value_unit: "kg/m²",
      interpretation: "normal",
      reference_range_text: "18.5 - 24.9 kg/m²",
      effective_date_time: "Sep 28, 2026",
    },
  ]);

  // Vitals Logging & FHIR Modals State
  const [isLogVitalsOpen, setIsLogVitalsOpen] = useState(false);
  const [logVitalType, setLogVitalType] = useState<"hr" | "bp" | "spo2">("hr");
  const [logValue, setLogValue] = useState("75");
  const [logSystolic, setLogSystolic] = useState("120");
  const [logDiastolic, setLogDiastolic] = useState("80");
  const [selectedFhirJson, setSelectedFhirJson] = useState<any | null>(null);

  // Diagnostic Lab Reports & Orders (Day 24)
  const [patientLabReports] = useState([
    {
      id: "dr-apollo-0925-01",
      order_id: "ord-req-901",
      title: "Comprehensive Lipid & Glycemic Diagnostic Panel",
      performer: "Apollo Diagnostics Central (HFR-DEL-91024)",
      code_value: "57021-8",
      code_display: "CBC and Comprehensive Metabolic Panel",
      issued_date_time: "Today, 11:15 AM",
      status: "final",
      is_abnormal: true,
      conclusion: "Borderline hypercholesterolemia with optimal fasting glucose. Dietary lipid modulation recommended.",
      coded_diagnosis_icd10: "E78.5 - Hyperlipidemia, unspecified",
      observations: [
        {
          code_value: "2093-3",
          code_display: "Total Serum Cholesterol",
          value_quantity: 215,
          value_unit: "mg/dL",
          reference_range_text: "< 200 mg/dL",
          interpretation: "high",
        },
        {
          code_value: "13457-7",
          code_display: "LDL Cholesterol (Calculated)",
          value_quantity: 142,
          value_unit: "mg/dL",
          reference_range_text: "< 100 mg/dL",
          interpretation: "high",
        },
        {
          code_value: "2085-9",
          code_display: "HDL Cholesterol",
          value_quantity: 44,
          value_unit: "mg/dL",
          reference_range_text: "> 40 mg/dL",
          interpretation: "normal",
        },
        {
          code_value: "2571-8",
          code_display: "Serum Triglycerides",
          value_quantity: 145,
          value_unit: "mg/dL",
          reference_range_text: "< 150 mg/dL",
          interpretation: "normal",
        },
        {
          code_value: "1558-6",
          code_display: "Fasting Blood Glucose",
          value_quantity: 94,
          value_unit: "mg/dL",
          reference_range_text: "70 - 99 mg/dL",
          interpretation: "normal",
        },
        {
          code_value: "4548-4",
          code_display: "Hemoglobin A1c (HbA1c)",
          value_quantity: 5.4,
          value_unit: "%",
          reference_range_text: "< 5.7 %",
          interpretation: "normal",
        },
      ],
    },
  ]);

  const [patientLabOrders] = useState([
    {
      id: "ord-req-901",
      code_value: "24331-1",
      code_display: "Lipid 1996 panel - Serum or Plasma",
      doctor_name: "Dr. Ananya Sharma (Chief Cardiologist, AIIMS)",
      priority: "routine",
      specimen_type: "serum",
      fasting_required: true,
      reason_display: "Cardiovascular risk stratification & baseline dyslipidemia surveillance",
      status: "completed",
      authored_on: "Today, 10:20 AM",
    },
  ]);

  // Slot Booking Handlers
  const handleHoldSlot = async (slot: DoctorSlot) => {
    setIsHolding(true);
    try {
      const hold = await apiClient.holdDoctorSlot(selectedDoctor.id, slot.id, 10);
      setActiveHold(hold);
      setIsModalOpen(true);
    } catch {
      const simulatedHold: SlotHoldResponse = {
        slot_id: slot.id,
        doctor_id: selectedDoctor.id,
        status: "held",
        held_until: new Date(Date.now() + 600000).toISOString(),
        held_by_patient_id: "pat-arun-patel",
        hold_duration_seconds: 600,
      };
      setActiveHold(simulatedHold);
      setIsModalOpen(true);
    } finally {
      setIsHolding(false);
    }
  };

  const handleReleaseHold = async () => {
    if (!activeHold) return;
    try {
      await apiClient.releaseDoctorSlot(selectedDoctor.id, activeHold.slot_id);
    } catch {
      // Ignore in demo
    } finally {
      setActiveHold(null);
      setSelectedSlot(null);
      setIsModalOpen(false);
    }
  };

  const handleBookingSuccess = (newAppt: Appointment) => {
    setScheduledAppointments((prev) => [
      {
        ...newAppt,
        doctor_name: selectedDoctor.name,
        doctor_specialty: selectedDoctor.specialty,
      },
      ...prev,
    ]);
    setActiveHold(null);
    setSelectedSlot(null);
  };

  // Vitals Logging Submission
  const handleLogVitalSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (logVitalType === "hr") {
      const val = parseFloat(logValue) || 72;
      const interp = val > 100 ? "high" : val < 60 ? "low" : "normal";
      const newObs = {
        id: `obs-hr-${Date.now()}`,
        code_value: "8867-4",
        code_display: "Heart Rate",
        value_quantity: val,
        value_unit: "/min",
        interpretation: interp,
        reference_range_text: "60 - 100 /min",
        effective_date_time: "Just now (Self-reported)",
      };
      setVitalsList((prev) => [newObs, ...prev.filter((v) => v.code_value !== "8867-4")]);
    } else if (logVitalType === "bp") {
      const sys = parseFloat(logSystolic) || 120;
      const dia = parseFloat(logDiastolic) || 80;
      const interp = sys > 130 || dia > 85 ? "high" : sys < 90 || dia < 60 ? "low" : "normal";
      const newObs = {
        id: `obs-bp-${Date.now()}`,
        code_value: "85354-9",
        code_display: "Blood Pressure Panel",
        value_quantity: null,
        value_unit: "mmHg",
        interpretation: interp,
        components: [
          { code_value: "8480-6", code_display: "Systolic", value_quantity: sys, value_unit: "mmHg", interpretation: interp },
          { code_value: "8462-4", code_display: "Diastolic", value_quantity: dia, value_unit: "mmHg", interpretation: interp },
        ],
        effective_date_time: "Just now (Self-reported)",
        method: "Home monitor",
      };
      setVitalsList((prev) => [newObs, ...prev.filter((v) => v.code_value !== "85354-9")]);
    } else if (logVitalType === "spo2") {
      const val = parseFloat(logValue) || 98;
      const interp = val < 95 ? "low" : "normal";
      const newObs = {
        id: `obs-spo2-${Date.now()}`,
        code_value: "2708-6",
        code_display: "Oxygen Saturation (SpO2)",
        value_quantity: val,
        value_unit: "%",
        interpretation: interp,
        reference_range_text: "95 - 100 %",
        effective_date_time: "Just now (Self-reported)",
      };
      setVitalsList((prev) => [newObs, ...prev.filter((v) => v.code_value !== "2708-6")]);
    }
    setIsLogVitalsOpen(false);
  };

  const handleViewFhirRx = async (rxId: string) => {
    try {
      setFetchingFhirId(rxId);
      const fhirRes = await apiClient.getPrescriptionFhir(rxId);
      setViewingFhirRx(fhirRes);
    } catch (err) {
      console.error("Failed to load FHIR MedicationRequest", err);
    } finally {
      setFetchingFhirId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 bg-white min-h-screen">
      
      {/* 1. Cal.com Patient Header Shell */}
      <PatientHeader
        patientName={user?.fullName || "Arun Patel"}
        abhaId={user?.abhaId || "91-8472-1092-4821"}
        abhaAddress="arun.patel@abdm"
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onExportFhir={() => alert("Downloading encrypted HL7 FHIR Bundle...")}
      />

      {/* 2. Cal.com Metrics Overview Bar */}
      <PatientMetricsBar
        activePrescriptionsCount={prescriptions.length}
        upcomingAppointmentsCount={scheduledAppointments.length}
        conditionsCount={2}
        latestBpText="134/86 mmHg"
        latestSpo2Text="98%"
        latestVitalsStatus="abnormal"
        onSelectTab={setActiveTab}
        onOpenLogVitals={() => setIsLogVitalsOpen(true)}
      />

      {/* 3. Cal.com Segmented Nav-Pill-Group */}
      <PatientNavTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        prescriptionsBadgeCount={prescriptions.length}
        conditionsBadgeCount={2}
      />

      {/* 4. Active Tab Views */}
      {activeTab === "overview" && (
        <PatientOverviewTab
          abhaId={abhaCardData.abhaId}
          abhaAddress={abhaCardData.abhaAddress}
          patientName={abhaCardData.patientName}
          gender={abhaCardData.gender}
          dob={abhaCardData.dob}
          mobile={abhaCardData.mobile}
          bloodGroup={abhaCardData.bloodGroup}
          stateNode={abhaCardData.stateNode}
          distName={abhaCardData.distName}
          emergencyContact={abhaCardData.emergencyContact}
          organDonor={abhaCardData.organDonor}
          qrPayload={abhaCardData.qrPayload}
          onOpenExport={() => setIsExportModalOpen(true)}
          onOpenVerify={() => setIsVerifyModalOpen(true)}
          consentActive={consentActive}
          onToggleConsent={setConsentActive}
          scheduledAppointments={scheduledAppointments}
          prescriptions={prescriptions}
          vitalsList={vitalsList}
          onSelectTab={setActiveTab}
          onOpenLogVitals={() => setIsLogVitalsOpen(true)}
          onViewFhirPrescription={(rx) => handleViewFhirRx(rx.id)}
        />
      )}

      {activeTab === "prescriptions" && (
        <PatientPrescriptionsTab
          prescriptions={prescriptions}
          loading={loadingPrescriptions}
          onRefresh={loadPrescriptions}
          onViewFhir={handleViewFhirRx}
          fetchingFhirId={fetchingFhirId}
        />
      )}

      {activeTab === "problems" && (
        <div className="animate-fade-in max-w-5xl mx-auto space-y-6">
          <ProblemListPanel
            patientId={user?.id || "pat-arun-patel"}
            patientName={user?.fullName || "Arun Patel"}
            isDoctorView={false}
          />
        </div>
      )}

      {activeTab === "records" && (
        <PatientRecordsTab
          vitalsList={vitalsList}
          patientLabReports={patientLabReports}
          patientLabOrders={patientLabOrders}
          onOpenLogVitals={() => setIsLogVitalsOpen(true)}
          onInspectFhir={(fhir) => setSelectedFhirJson(fhir)}
        />
      )}

      {activeTab === "book" && (
        <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
          {/* Clinician Directory Selector */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-[#111111] tracking-tight">
                  Choose Clinical Specialist
                </h2>
                <p className="text-xs text-[#6b7280]">
                  Select an accredited practitioner to view real-time consultation availability.
                </p>
              </div>
              <Badge variant="default" size="sm">
                {CLINICIANS.length} Available
              </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {CLINICIANS.map((doc) => {
                const isSelected = selectedDoctor.id === doc.id;
                return (
                  <button
                    key={doc.id}
                    type="button"
                    onClick={() => {
                      setSelectedDoctor(doc);
                      setSelectedSlot(null);
                      setActiveHold(null);
                    }}
                    className={`p-4 rounded-[12px] border text-left transition-all cursor-pointer ${
                      isSelected
                        ? "bg-[#f8f9fa] border-[#111111] shadow-xs"
                        : "bg-white border-[#e5e7eb] hover:bg-[#f8f9fa] hover:border-[#d1d5db]"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`h-10 w-10 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
                        isSelected ? "bg-[#111111] text-white" : "bg-[#f5f5f5] text-[#111111]"
                      }`}>
                        {doc.name.replace("Dr. ", "").split(" ").map((n) => n[0]).join("")}
                      </div>
                      <div>
                        <div className="font-bold text-sm text-[#111111]">
                          {doc.name}
                        </div>
                        <div className="text-xs text-[#059669] font-medium">
                          {doc.specialty}
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 pt-3 border-t border-[#e5e7eb] flex items-center justify-between text-xs">
                      <span className="text-[#6b7280]">{doc.affiliation}</span>
                      <span className="font-bold text-[#111111]">₹{doc.fee}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Embedded Interactive Slot Picker */}
          <ClinicalSlotPicker
            doctorId={selectedDoctor.id}
            doctorName={selectedDoctor.name}
            specialty={selectedDoctor.specialty}
            consultationFee={selectedDoctor.fee}
            selectedSlot={selectedSlot}
            onSelectSlot={(slot) => setSelectedSlot(slot)}
            onHoldSlot={handleHoldSlot}
            activeHold={activeHold}
            onReleaseHold={handleReleaseHold}
            isHolding={isHolding}
          />
        </div>
      )}

      {/* Appointment Intake Modal */}
      <AppointmentBookingModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        slot={selectedSlot}
        doctorId={selectedDoctor.id}
        doctorName={selectedDoctor.name}
        specialty={selectedDoctor.specialty}
        consultationFee={selectedDoctor.fee}
        activeHold={activeHold}
        onHoldRelease={handleReleaseHold}
        onSuccess={handleBookingSuccess}
      />

      {/* Reusable Modals (Log Vitals, FHIR Observation/Composition, FHIR MedicationRequest) */}
      <PatientModals
        isLogVitalsOpen={isLogVitalsOpen}
        onCloseLogVitals={() => setIsLogVitalsOpen(false)}
        logVitalType={logVitalType}
        setLogVitalType={setLogVitalType}
        logValue={logValue}
        setLogValue={setLogValue}
        logSystolic={logSystolic}
        setLogSystolic={setLogSystolic}
        logDiastolic={logDiastolic}
        setLogDiastolic={setLogDiastolic}
        onLogVitalSubmit={handleLogVitalSubmit}
        selectedFhirJson={selectedFhirJson}
        onCloseFhirModal={() => setSelectedFhirJson(null)}
        viewingFhirRx={viewingFhirRx}
        onCloseFhirRxModal={() => setViewingFhirRx(null)}
      />

      {/* ABHA ID Card High-Res Export & Print Modal */}
      <AbhaCardExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        cardData={abhaCardData}
      />

      {/* ABDM Cryptographic QR Code Verification & Inspector Modal */}
      <AbhaQrVerificationModal
        isOpen={isVerifyModalOpen}
        onClose={() => setIsVerifyModalOpen(false)}
        defaultQrPayload={abhaCardData.qrPayload}
        patientName={abhaCardData.patientName}
        abhaId={abhaCardData.abhaId}
      />

    </div>
  );
}
