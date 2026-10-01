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
  Copy
} from "lucide-react";
import { 
  CalcomSlotPicker, 
  AppointmentBookingModal 
} from "@/components/appointments";
import { 
  apiClient, 
  DoctorSlot, 
  SlotHoldResponse, 
  Appointment 
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

          {/* Right 7 Columns: Longitudinal Clinical History Timeline */}
          <div className="lg:col-span-7 space-y-6">
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

    </div>
  );
}
