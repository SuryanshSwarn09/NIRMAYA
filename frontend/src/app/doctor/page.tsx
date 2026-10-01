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
  MapPin
} from "lucide-react";
import { DoctorSlotManager } from "@/components/appointments";

export default function DoctorEMRPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"queue" | "slots">("queue");
  const [selectedPatient, setSelectedPatient] = useState("Arun Patel");
  const [medication, setMedication] = useState("Atorvastatin 20mg");
  const [dosage, setDosage] = useState("Once daily at bedtime");
  const [issuedPrescription, setIssuedPrescription] = useState(false);

  const doctorId = "doc-ananya-sharma";

  const handleSignPrescription = (e: React.FormEvent) => {
    e.preventDefault();
    setIssuedPrescription(true);
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
              id: "slots",
              label: "Availability & Slot Engine",
              icon: <Calendar className="h-4 w-4" />,
            },
          ]}
          activeId={activeTab}
          onChange={(id) => setActiveTab(id as "queue" | "slots")}
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
                  <span className="font-bold text-sm text-[#111111]">134 / 86 mmHg</span>
                </div>
                <div className="p-2.5 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb]">
                  <span className="text-[#6b7280] block text-[11px]">Heart Rate</span>
                  <span className="font-bold text-sm text-[#111111]">72 bpm</span>
                </div>
                <div className="p-2.5 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb]">
                  <span className="text-[#6b7280] block text-[11px]">SpO2</span>
                  <span className="font-bold text-sm text-[#059669]">98% Room Air</span>
                </div>
                <div className="p-2.5 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb]">
                  <span className="text-[#6b7280] block text-[11px]">BMI</span>
                  <span className="font-bold text-sm text-[#111111]">24.2 kg/m²</span>
                </div>
              </div>
            </Card>
          </div>

          {/* Right 8 Columns: Clinical Consultation Note & Digital Prescription Pad */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Consultation Note Pad */}
            <Card variant="mockup" className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                <div>
                  <CardTitle className="text-base sm:text-lg">
                    Clinical Encounter Examination: {selectedPatient}
                  </CardTitle>
                  <CardDescription>
                    Serializes to HL7 FHIR R4 Encounter & Observation bundles upon signature.
                  </CardDescription>
                </div>
                <Badge variant="abdm" size="sm">CareContext Linkable</Badge>
              </div>

              <div className="space-y-3 text-xs sm:text-sm">
                <div>
                  <label className="block text-xs font-semibold text-[#111111] mb-1">
                    Subjective Clinical Impression & Symptoms
                  </label>
                  <textarea
                    rows={3}
                    defaultValue="Patient reports well-managed blood pressure with mild morning fatigue. Denies chest pain or shortness of breath on routine exertion."
                    className="w-full p-3 rounded-[8px] border border-[#e5e7eb] text-xs sm:text-sm text-[#111111] focus:outline-none focus:ring-1 focus:ring-[#111111]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-[#111111] mb-1">
                      ICD-10 Clinical Coding
                    </label>
                    <input
                      type="text"
                      defaultValue="I10 (Essential Primary Hypertension)"
                      className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] font-mono text-xs focus:outline-none focus:ring-1 focus:ring-[#111111]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#111111] mb-1">
                      Encounter Class
                    </label>
                    <input
                      type="text"
                      disabled
                      defaultValue="Ambulatory Clinic (AMB - ActCode)"
                      className="w-full p-2.5 rounded-[8px] border border-[#e5e7eb] bg-[#f8f9fa] font-mono text-xs text-[#6b7280]"
                    />
                  </div>
                </div>
              </div>
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

          </div>

        </div>
      )}

    </div>
  );
}
