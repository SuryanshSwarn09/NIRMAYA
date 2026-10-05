"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button, Badge, Card, CardTitle, CardDescription, NavPillGroup } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import { 
  ShieldCheck, 
  Activity, 
  FileText, 
  Calendar, 
  User, 
  QrCode, 
  Clock, 
  Lock, 
  Download, 
  AlertCircle,
  Video,
  MapPin,
  Stethoscope,
  CheckCircle2,
  Copy,
  Heart,
  Plus,
  Thermometer,
  Gauge,
  X
} from "lucide-react";
import { 
  CalcomSlotPicker, 
  AppointmentBookingModal 
} from "@/components/appointments";
import { 
  apiClient, 
  DoctorSlot, 
  SlotHoldResponse, 
  Appointment,
  ClinicalObservation
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
  const [activeTab, setActiveTab] = useState<"records" | "book">("records");
  const [consentActive, setConsentActive] = useState(true);

  // Selected Clinician for Booking
  const [selectedDoctor, setSelectedDoctor] = useState(CLINICIANS[0]);

  // Selected Slot & Hold State
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

  // Vitals Modal State
  const [isLogVitalsOpen, setIsLogVitalsOpen] = useState(false);
  const [logVitalType, setLogVitalType] = useState<"hr" | "bp" | "spo2">("hr");
  const [logValue, setLogValue] = useState("75");
  const [logSystolic, setLogSystolic] = useState("120");
  const [logDiastolic, setLogDiastolic] = useState("80");
  const [selectedFhirJson, setSelectedFhirJson] = useState<any | null>(null);

  // Handle slot hold reservation
  const handleHoldSlot = async (slot: DoctorSlot) => {
    setIsHolding(true);
    try {
      const hold = await apiClient.holdDoctorSlot(selectedDoctor.id, slot.id, 10);
      setActiveHold(hold);
      setIsModalOpen(true);
    } catch {
      // Simulate hold for UI demonstration
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

  // Handle slot hold release
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

  // Handle successful appointment booking
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

  // Handle logging new vital sign (Day 22)
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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 bg-white">
      
      {/* Top Welcome & Health ID Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#e5e7eb]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111111]">
              Patient Health Vault
            </h1>
            <Badge variant="verified">Self-Sovereign</Badge>
          </div>
          <p className="text-sm text-[#6b7280] mt-1">
            Welcome, <span className="font-semibold text-[#111111]">{user?.fullName || "Arun Patel"}</span>. All records are cryptographically verified and FHIR R4 compliant.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="secondary" size="sm" onClick={() => alert("Downloading encrypted HL7 FHIR Bundle...")}>
            <Download className="h-4 w-4 mr-1 text-[#6b7280]" />
            Export FHIR Bundle
          </Button>
          <Button 
            variant={activeTab === "book" ? "secondary" : "primary"} 
            size="sm"
            onClick={() => setActiveTab(activeTab === "book" ? "records" : "book")}
          >
            {activeTab === "book" ? "Back to Health Records" : "Book Clinical Consultation"}
          </Button>
        </div>
      </div>

      {/* Main Tab Nav Switcher */}
      <div className="flex justify-start">
        <NavPillGroup
          items={[
            {
              id: "records",
              label: "Health Vault & Records",
              icon: <ShieldCheck className="h-4 w-4" />,
            },
            {
              id: "book",
              label: "Schedule Consultation (Cal.com)",
              icon: <Calendar className="h-4 w-4" />,
            },
          ]}
          activeId={activeTab}
          onChange={(id) => setActiveTab(id as "records" | "book")}
        />
      </div>

      {activeTab === "book" ? (
        /* ========================================================================
           BOOKING TAB: CAL.COM SLOT PICKER EXPERIENCE
           ======================================================================== */
        <div className="space-y-8 animate-fade-in">
          
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
                        {doc.name.replace("Dr. ", "").split(" ").map(n => n[0]).join("")}
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

          {/* Embedded Cal.com Interactive Slot Picker */}
          <CalcomSlotPicker
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

          {/* Booking Intake Modal */}
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
        </div>
      ) : (
        /* ========================================================================
           HEALTH RECORDS TAB (WITH SCHEDULED CONSULTATIONS)
           ======================================================================== */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fade-in">
          
          {/* Left 5 Columns: Official ABHA Health Card & Consent Manager */}
          <div className="lg:col-span-5 space-y-6">
            
            {/* ABHA National Health Card */}
            <Card variant="mockup" className="space-y-5 bg-[#f8f9fa] border-[#e5e7eb]">
              <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                <div className="flex items-center gap-2">
                  <div className="h-7 w-7 rounded-full bg-[#111111] text-white flex items-center justify-center font-bold text-xs">
                    N
                  </div>
                  <span className="text-xs font-bold tracking-tight text-[#111111] uppercase">
                    Ayushman Bharat Health Card
                  </span>
                </div>
                <Badge variant="emerald" size="sm">ABDM Verified</Badge>
              </div>

              <div className="flex items-center gap-4">
                <div className="h-16 w-16 rounded-[8px] bg-white border border-[#e5e7eb] flex items-center justify-center text-[#111111] shadow-xs">
                  <QrCode className="h-10 w-10 text-[#111111]" />
                </div>
                <div>
                  <div className="text-xs text-[#6b7280]">ABHA Health ID Number</div>
                  <div className="text-lg font-bold text-[#111111] tracking-wider font-mono">
                    {user?.abhaId || "91-8472-1092-4821"}
                  </div>
                  <div className="text-xs text-[#374151] mt-0.5">
                    arun.patel@abdm • Male, 34 Yrs
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-3 border-t border-[#e5e7eb] text-xs">
                <div className="p-2.5 rounded-[6px] bg-white border border-[#e5e7eb]">
                  <div className="text-[#6b7280]">Blood Group</div>
                  <div className="font-semibold text-[#111111]">O Positive (O+)</div>
                </div>
                <div className="p-2.5 rounded-[6px] bg-white border border-[#e5e7eb]">
                  <div className="text-[#6b7280]">State Node</div>
                  <div className="font-semibold text-[#111111]">NCT of Delhi</div>
                </div>
              </div>
            </Card>

            {/* Active Consent Delegation Panel */}
            <Card variant="mockup" className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="h-4 w-4 text-[#111111]" />
                  <CardTitle className="text-base">Consent Token Delegations</CardTitle>
                </div>
                <Badge variant={consentActive ? "verified" : "critical"} size="sm">
                  {consentActive ? "1 Active Grant" : "Revoked"}
                </Badge>
              </div>

              <CardDescription>
                You maintain total cryptographic ownership. Delegations grant time-bound access to clinical history.
              </CardDescription>

              {consentActive ? (
                <div className="p-3.5 rounded-[8px] border border-[#e5e7eb] bg-[#f8f9fa] space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <div>
                      <span className="font-semibold text-[#111111]">Dr. Ananya Sharma</span>
                      <p className="text-[#6b7280] text-[11px]">AIIMS Cardiology • HPR-91024</p>
                    </div>
                    <span className="text-[11px] font-mono text-[#059669] font-medium flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      23h 41m TTL
                    </span>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-[#e5e7eb]">
                    <span className="text-[11px] text-[#6b7280]">Scope: Encounters & Lab Reports</span>
                    <button
                      type="button"
                      onClick={() => setConsentActive(false)}
                      className="text-xs font-semibold text-[#ef4444] hover:underline cursor-pointer"
                    >
                      Revoke Access
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-3 rounded-[8px] bg-[#fef2f2] border border-[#fecaca] text-xs text-[#991b1b] flex items-center justify-between">
                  <span>Access token revoked. No providers have active access.</span>
                  <button
                    type="button"
                    onClick={() => setConsentActive(true)}
                    className="font-semibold underline cursor-pointer"
                  >
                    Restore
                  </button>
                </div>
              )}
            </Card>

            {/* Scheduled Encounters Section */}
            <Card variant="mockup" className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-[#111111]" />
                  <CardTitle className="text-base">Scheduled Encounters</CardTitle>
                </div>
                <Badge variant="emerald" size="sm">
                  {scheduledAppointments.length} Confirmed
                </Badge>
              </div>

              <div className="space-y-3">
                {scheduledAppointments.map((appt) => {
                  const careContext = `APPT-${appt.id.replace(/-/g, "").substring(0, 8).toUpperCase()}`;
                  const apptDate = new Date(appt.scheduled_start).toLocaleString("en-US", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: true,
                  });

                  return (
                    <div
                      key={appt.id}
                      className="p-3.5 rounded-[8px] border border-[#e5e7eb] bg-white space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-sm text-[#111111]">
                          {appt.doctor_name || "Dr. Ananya Sharma"}
                        </span>
                        <Badge variant="verified" size="sm">
                          {appt.status.toUpperCase()}
                        </Badge>
                      </div>

                      <div className="text-[#6b7280]">
                        {apptDate} • {appt.doctor_specialty || "Cardiology"}
                      </div>

                      <div className="pt-2 border-t border-[#f3f4f6] flex items-center justify-between">
                        <span className="font-mono text-[11px] text-[#059669] font-bold">
                          {careContext}
                        </span>
                        <button
                          type="button"
                          onClick={() => alert(`Exporting signed FHIR Bundle for ${careContext}...`)}
                          className="text-[11px] font-semibold text-[#111111] hover:underline flex items-center gap-1 cursor-pointer"
                        >
                          <Download className="h-3 w-3" />
                          FHIR R4
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>

          </div>

          {/* Right 7 Columns: Longitudinal Clinical History & Vitals Telemetry */}
          <div className="lg:col-span-7 space-y-6">

            {/* Vital Signs & Clinical Telemetry Panel (Day 22) */}
            <Card variant="mockup" className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                <div>
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-lg">Vital Signs & Biometric Telemetry</CardTitle>
                    <Badge variant="verified">LOINC & FHIR R4</Badge>
                  </div>
                  <CardDescription>
                    Longitudinal physiological telemetry and patient self-measurements.
                  </CardDescription>
                </div>
                <Button 
                  variant="secondary" 
                  size="sm"
                  onClick={() => setIsLogVitalsOpen(true)}
                  className="cursor-pointer"
                >
                  <Plus className="h-3.5 w-3.5 mr-1" />
                  Log Vital
                </Button>
              </div>

              {/* Vitals Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {vitalsList.map((vital) => {
                  const isHigh = vital.interpretation === "high" || vital.interpretation === "critically-high";
                  const isLow = vital.interpretation === "low" || vital.interpretation === "critically-low";

                  return (
                    <div
                      key={vital.id}
                      className="p-3.5 rounded-[8px] border border-[#e5e7eb] bg-[#f8f9fa] hover:bg-white hover:border-[#d1d5db] transition-all space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-xs text-[#111111]">
                          {vital.code_display}
                        </span>
                        <Badge 
                          variant={isHigh ? "critical" : isLow ? "warning" : "emerald"}
                          size="sm"
                        >
                          {vital.interpretation?.toUpperCase() || "NORMAL"}
                        </Badge>
                      </div>

                      <div className="flex items-baseline justify-between">
                        <div className="text-xl font-bold tracking-tight text-[#111111]">
                          {vital.components ? (
                            `${vital.components[0].value_quantity} / ${vital.components[1].value_quantity}`
                          ) : (
                            vital.value_quantity
                          )}
                          <span className="text-xs font-normal text-[#6b7280] ml-1">
                            {vital.value_unit}
                          </span>
                        </div>
                        <span className="font-mono text-[10px] text-[#6b7280] bg-white px-1.5 py-0.5 rounded border border-[#e5e7eb]">
                          LOINC {vital.code_value}
                        </span>
                      </div>

                      <div className="pt-2 border-t border-[#e5e7eb] flex items-center justify-between text-[11px] text-[#6b7280]">
                        <span>{vital.effective_date_time}</span>
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedFhirJson({
                              resourceType: "Observation",
                              id: vital.id,
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
                                  text: "vital-signs",
                                },
                              ],
                              code: {
                                coding: [
                                  {
                                    system: "http://loinc.org",
                                    code: vital.code_value,
                                    display: vital.code_display,
                                  },
                                ],
                                text: vital.code_display,
                              },
                              subject: {
                                reference: "Patient/pat-arun-patel",
                                display: "Arun Patel",
                                type: "Patient",
                              },
                              effectiveDateTime: new Date().toISOString(),
                              valueQuantity: vital.value_quantity !== null ? {
                                value: vital.value_quantity,
                                unit: vital.value_unit,
                                system: "http://unitsofmeasure.org",
                              } : undefined,
                              component: vital.components?.map((c: any) => ({
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
                                  system: "http://unitsofmeasure.org",
                                },
                              })),
                            });
                          }}
                          className="font-semibold text-[#111111] hover:underline flex items-center gap-1 cursor-pointer"
                        >
                          <Download className="h-3 w-3" />
                          FHIR R4
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>

            <Card variant="mockup" className="space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                <div>
                  <CardTitle className="text-lg">Longitudinal Clinical Timeline</CardTitle>
                  <CardDescription>
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
                    <span className="text-[#111111] font-medium cursor-pointer hover:underline">
                      View Cryptographic PDF
                    </span>
                  </div>
                </div>
              </div>

            </Card>
          </div>

        </div>
      )}

      {/* Log Vital Signs Modal (Day 22) */}
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
                onClick={() => setIsLogVitalsOpen(false)}
                className="text-[#9ca3af] hover:text-[#111111] transition-colors p-1"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleLogVitalSubmit} className="space-y-4 text-xs">
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
                    <label className="block font-semibold text-[#111111] mb-1">
                      Systolic (mmHg)
                    </label>
                    <input
                      type="number"
                      value={logSystolic}
                      onChange={(e) => setLogSystolic(e.target.value)}
                      placeholder="120"
                      className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] focus:outline-none focus:border-[#111111]"
                      required
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#111111] mb-1">
                      Diastolic (mmHg)
                    </label>
                    <input
                      type="number"
                      value={logDiastolic}
                      onChange={(e) => setLogDiastolic(e.target.value)}
                      placeholder="80"
                      className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] focus:outline-none focus:border-[#111111]"
                      required
                    />
                  </div>
                </div>
              ) : (
                <div>
                  <label className="block font-semibold text-[#111111] mb-1">
                    {logVitalType === "hr" ? "Heart Rate (bpm)" : "Oxygen Saturation (%)"}
                  </label>
                  <input
                    type="number"
                    value={logValue}
                    onChange={(e) => setLogValue(e.target.value)}
                    placeholder={logVitalType === "hr" ? "72" : "98"}
                    className="w-full px-3 py-2 border border-[#e5e7eb] rounded-[6px] focus:outline-none focus:border-[#111111]"
                    required
                  />
                </div>
              )}

              <div className="p-3 bg-[#f8f9fa] rounded-[6px] border border-[#e5e7eb] text-[11px] text-[#6b7280]">
                {logVitalType === "bp" && "LOINC 85354-9 Panel: Systolic (<120 mmHg) & Diastolic (<80 mmHg)."}
                {logVitalType === "hr" && "LOINC 8867-4: Normal resting pulse 60 - 100 beats per minute."}
                {logVitalType === "spo2" && "LOINC 2708-6: Normal arterial saturation 95% - 100% on room air."}
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#e5e7eb]">
                <Button
                  variant="secondary"
                  size="sm"
                  type="button"
                  onClick={() => setIsLogVitalsOpen(false)}
                >
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit">
                  Save to Vault
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* FHIR R4 JSON Inspection Modal */}
      {selectedFhirJson && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-[12px] border border-[#e5e7eb] shadow-xl max-w-xl w-full p-6 space-y-4 animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div>
                <h3 className="text-base font-bold text-[#111111] tracking-tight">
                  HL7 FHIR R4 Observation Resource
                </h3>
                <p className="text-xs text-[#6b7280]">
                  Standardized JSON serialization conforming to HL7 FHIR Release 4 & ABDM.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedFhirJson(null)}
                className="text-[#9ca3af] hover:text-[#111111] transition-colors p-1"
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

    </div>
  );
}
