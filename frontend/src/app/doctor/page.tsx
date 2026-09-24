"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button, Badge, Card, CardTitle, CardDescription } from "@/components/ui";
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
  Code
} from "lucide-react";

export default function DoctorEMRPage() {
  const { user } = useAuth();
  const [selectedPatient, setSelectedPatient] = useState("Arun Patel");
  const [medication, setMedication] = useState("Atorvastatin 20mg");
  const [dosage, setDosage] = useState("Once daily at bedtime");
  const [issuedPrescription, setIssuedPrescription] = useState(false);

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

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
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
                  <span className="text-[11px] font-mono text-[#6b7280] bg-[#f5f5f5] px-2 py-0.5 rounded-full">
                    11:00 AM
                  </span>
                </div>
                <div className="text-xs text-[#6b7280] mt-1">
                  ABHA: 91-4432-8819-2041
                </div>
                <div className="text-[11px] text-[#374151] font-medium mt-1">
                  Reason: Lipid Profiling Review
                </div>
              </button>
            </div>
          </Card>
        </div>

        {/* Right 8 Columns: Clinical Encounter Workspace & E-Prescription Form */}
        <div className="lg:col-span-8 space-y-6">
          <Card variant="mockup" className="space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div>
                <CardTitle className="text-lg">
                  Clinical Encounter Workspace: {selectedPatient}
                </CardTitle>
                <CardDescription>
                  Generate standardized HL7 FHIR R4 MedicationRequest and encounter notes.
                </CardDescription>
              </div>
              <Badge variant="verified">Consent Verified (24h)</Badge>
            </div>

            <form onSubmit={handleSignPrescription} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#111111]">
                    Clinical Diagnosis (ICD-10 / SNOMED CT)
                  </label>
                  <input
                    type="text"
                    defaultValue="I10 - Essential (Primary) Hypertension"
                    className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111111] focus:border-[#111111] outline-none"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#111111]">
                    Encounter Type
                  </label>
                  <select className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111111] focus:border-[#111111] outline-none">
                    <option>Teleconsultation (ABDM Sandbox)</option>
                    <option>Ambulatory In-Person</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#111111]">
                    Prescribed Medication
                  </label>
                  <input
                    type="text"
                    required
                    value={medication}
                    onChange={(e) => setMedication(e.target.value)}
                    placeholder="e.g. Atorvastatin 20mg"
                    className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111111] focus:border-[#111111] outline-none"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#111111]">
                    Dosage & Regimen
                  </label>
                  <input
                    type="text"
                    required
                    value={dosage}
                    onChange={(e) => setDosage(e.target.value)}
                    placeholder="e.g. 1 Tablet Daily with Dinner"
                    className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111111] focus:border-[#111111] outline-none"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <span className="text-xs text-[#6b7280]">
                  Signing will generate an immutable FHIR Bundle and notify patient vault.
                </span>
                <Button type="submit" variant="primary" size="md">
                  <Send className="h-4 w-4 mr-1.5" />
                  Sign & Issue Prescription
                </Button>
              </div>
            </form>

            {/* Real-time FHIR MedicationRequest JSON Preview */}
            {issuedPrescription && (
              <div className="mt-6 pt-5 border-t border-[#e5e7eb] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#10b981]" />
                    <span className="text-sm font-semibold text-[#111111]">
                      Prescription Successfully Signed & Linked to ABHA
                    </span>
                  </div>
                  <Badge variant="fhir" size="sm">FHIR R4 Valid</Badge>
                </div>

                <div className="bg-[#f8f9fa] p-4 rounded-[8px] border border-[#e5e7eb] font-mono text-xs text-[#374151] overflow-x-auto space-y-1">
                  <div className="text-[#6b7280]">// Generated HL7 FHIR R4 Resource Envelope</div>
                  <div>&#123;</div>
                  <div className="pl-4">&quot;resourceType&quot;: &quot;MedicationRequest&quot;,</div>
                  <div className="pl-4">&quot;id&quot;: &quot;rx-{Date.now()}&quot;,</div>
                  <div className="pl-4">&quot;status&quot;: &quot;active&quot;,</div>
                  <div className="pl-4">&quot;intent&quot;: &quot;order&quot;,</div>
                  <div className="pl-4">&quot;subject&quot;: &#123; &quot;reference&quot;: &quot;Patient/pat-918472&quot;, &quot;display&quot;: &quot;{selectedPatient}&quot; &#125;,</div>
                  <div className="pl-4">&quot;requester&quot;: &#123; &quot;reference&quot;: &quot;Practitioner/hpr-ananya-sharma&quot; &#125;,</div>
                  <div className="pl-4">&quot;medicationCodeableConcept&quot;: &#123; &quot;text&quot;: &quot;{medication}&quot; &#125;,</div>
                  <div className="pl-4">&quot;dosageInstruction&quot;: [ &#123; &quot;text&quot;: &quot;{dosage}&quot; &#125; ]</div>
                  <div>&#125;</div>
                </div>
              </div>
            )}
          </Card>
        </div>

      </div>

    </div>
  );
}
