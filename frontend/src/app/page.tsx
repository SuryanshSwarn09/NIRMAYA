"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Badge, Button, Card, CardTitle, CardDescription, NavPillGroup } from "@/components/ui";
import { 
  ShieldCheck, 
  Activity, 
  Stethoscope, 
  FlaskConical, 
  Lock, 
  ArrowRight,
  Calendar,
  Clock,
  UserCheck,
  FileText,
  FileCheck2,
  Code2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

export default function Home() {
  const [selectedPillar, setSelectedPillar] = useState("patient");
  const [selectedSlot, setSelectedSlot] = useState("10:15 AM");
  const [selectedDate, setSelectedDate] = useState("Wed 24");
  const [showDoctorFhir, setShowDoctorFhir] = useState(false);
  const [showLabFhir, setShowLabFhir] = useState(false);

  return (
    <div className="space-y-24 pb-20 bg-white">
      {/* 1. HERO BAND (7/5 Desktop Grid, White Canvas, Cal.com Rhythm) */}
      <section className="pt-12 pb-16 lg:pt-20 lg:pb-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            
            {/* Left 7 Columns: Editorial Headline & 2 Primary CTAs */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#f8f9fa] border border-[#e5e7eb] text-xs font-medium text-[#111111]">
                <span className="h-2 w-2 rounded-full bg-[#10b981]" />
                <span>ABDM & HL7 FHIR R4 Interoperable</span>
              </div>

              <h1 className="display-xl text-[#111111]">
                The interoperable health network,{" "}
                <span className="text-[#6b7280]">finally simplified.</span>
              </h1>

              <p className="text-base sm:text-lg text-[#374151] leading-relaxed max-w-2xl font-normal">
                NIRMAYA unifies longitudinal patient vaults, clinical provider EMRs, and diagnostic laboratories 
                into an interoperable, consent-driven network anchored on HL7 FHIR R4.
              </p>

              {/* 2 Focused Primary CTAs (No clutter) */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <Link href="/patient">
                  <Button variant="primary" size="lg">
                    <span>Access Patient Vault</span>
                    <ArrowRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
                <Link href="/doctor">
                  <Button variant="secondary" size="lg">
                    <Stethoscope className="h-4 w-4 mr-1.5" />
                    <span>Provider EMR</span>
                  </Button>
                </Link>
              </div>

              {/* 3 Sleek Trust Pillars (Replaces 6-item checklist wall) */}
              <div className="pt-6 border-t border-[#e5e7eb] flex flex-wrap items-center gap-6 text-xs text-[#4b5563] font-medium">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-[#10b981]" />
                  <span>Patient-Sovereign Consent</span>
                </div>
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-[#111111]" />
                  <span>Zero Clinic & Lab Silos</span>
                </div>
                <div className="flex items-center gap-2">
                  <Lock className="h-4 w-4 text-[#111111]" />
                  <span>HL7 FHIR R4 & ABHA Ready</span>
                </div>
              </div>
            </div>

            {/* Right 5 Columns: Hero App Mockup Card with Real Booking Chrome */}
            <div className="lg:col-span-5">
              <Card variant="hero-mockup" className="relative">
                {/* Doctor Chrome Header */}
                <div className="flex items-center justify-between pb-4 border-b border-[#e5e7eb]">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-[#f5f5f5] border border-[#e5e7eb] flex items-center justify-center font-bold text-sm text-[#111111]">
                      AS
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-semibold text-[#111111]">
                          Dr. Ananya Sharma
                        </span>
                        <UserCheck className="h-3.5 w-3.5 text-[#10b981]" />
                      </div>
                      <p className="text-xs text-[#6b7280]">
                        Chief Cardiologist • AIIMS New Delhi
                      </p>
                    </div>
                  </div>
                  <Badge variant="verified" size="sm">
                    Verified HPR
                  </Badge>
                </div>

                {/* Consultation Details */}
                <div className="py-4 space-y-3">
                  <div className="flex items-center justify-between text-xs text-[#374151]">
                    <span className="flex items-center gap-1.5 font-medium">
                      <Clock className="h-3.5 w-3.5 text-[#6b7280]" />
                      30 Min Clinical Consultation
                    </span>
                    <span className="font-semibold text-[#111111]">
                      ABHA ID: 91-8472-1092-4821
                    </span>
                  </div>

                  {/* Day Picker Segmented Row */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-[#111111] flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-[#6b7280]" />
                      Select Consultation Date
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {["Wed 24", "Thu 25", "Fri 26"].map((date) => (
                        <button
                          key={date}
                          onClick={() => setSelectedDate(date)}
                          className={`py-2 text-xs font-medium rounded-[8px] border transition-all text-center cursor-pointer ${
                            selectedDate === date
                              ? "bg-[#111111] text-white border-[#111111] shadow-xs"
                              : "bg-[#f8f9fa] text-[#374151] border-[#e5e7eb] hover:bg-[#f5f5f5]"
                          }`}
                        >
                          {date}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Slot Picker Grid */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-[#111111]">
                      Available Clinical Slots
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {["09:30 AM", "10:15 AM", "02:00 PM", "04:30 PM"].map(
                        (slot) => (
                          <button
                            key={slot}
                            onClick={() => setSelectedSlot(slot)}
                            className={`py-2 px-3 text-xs font-medium rounded-[8px] border transition-all text-left flex items-center justify-between cursor-pointer ${
                              selectedSlot === slot
                                ? "bg-[#111111] text-white border-[#111111]"
                                : "bg-white text-[#374151] border-[#e5e7eb] hover:bg-[#f5f5f5]"
                            }`}
                          >
                            <span>{slot}</span>
                            {selectedSlot === slot && (
                              <span className="h-1.5 w-1.5 rounded-full bg-white" />
                            )}
                          </button>
                        )
                      )}
                    </div>
                  </div>
                </div>

                {/* Confirm Action Button */}
                <div className="pt-3 border-t border-[#e5e7eb]">
                  <Link href="/patient" className="block w-full">
                    <Button variant="primary" size="md" className="w-full">
                      Book Clinical Consultation
                    </Button>
                  </Link>
                </div>
              </Card>
            </div>

          </div>
        </div>
      </section>

      {/* 2. SIGNATURE NAV-PILL-GROUP CLINICAL PRODUCT SWITCHER */}
      <section className="py-12 border-y border-[#e5e7eb] bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          
          <div className="text-center max-w-2xl mx-auto space-y-4">
            <h2 className="display-md text-[#111111]">
              Explore the Three Network Pillars
            </h2>
            <p className="text-sm sm:text-base text-[#6b7280]">
              Switch views to inspect clean clinical workflows across each healthcare touchpoint.
            </p>

            {/* Signature Pill Switcher */}
            <div className="pt-2 flex justify-center">
              <NavPillGroup
                items={[
                  {
                    id: "patient",
                    label: "Patient Vault",
                    icon: <ShieldCheck className="h-4 w-4" />,
                  },
                  {
                    id: "doctor",
                    label: "Provider EMR",
                    icon: <Stethoscope className="h-4 w-4" />,
                  },
                  {
                    id: "lab",
                    label: "Diagnostic Gateway",
                    icon: <FlaskConical className="h-4 w-4" />,
                  },
                ]}
                activeId={selectedPillar}
                onChange={setSelectedPillar}
              />
            </div>
          </div>

          {/* Interactive Pillar Mockup Zone */}
          <div className="max-w-4xl mx-auto">
            {selectedPillar === "patient" && (
              <Card variant="mockup" className="space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5 text-[#111111]" />
                    <span className="font-semibold text-sm text-[#111111]">
                      Longitudinal Health Record Locker
                    </span>
                  </div>
                  <Badge variant="verified">Consent Active (24h)</Badge>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-3.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-1">
                    <div className="text-[#6b7280]">Ayushman Bharat ID</div>
                    <div className="font-semibold text-sm text-[#111111]">
                      91-8472-1092-4821
                    </div>
                    <div className="text-[11px] text-[#059669]">
                      Verified by NHA Sandbox
                    </div>
                  </div>
                  <div className="p-3.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-1">
                    <div className="text-[#6b7280]">Active Prescriptions</div>
                    <div className="font-semibold text-sm text-[#111111]">
                      Atorvastatin 20mg
                    </div>
                    <div className="text-[11px] text-[#6b7280]">
                      Dr. Ananya Sharma • Cardiology
                    </div>
                  </div>
                  <div className="p-3.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-1">
                    <div className="text-[#6b7280]">Recent Diagnostic</div>
                    <div className="font-semibold text-sm text-[#111111]">
                      Lipid Profile (Normal)
                    </div>
                    <div className="text-[11px] text-[#059669]">
                      Apollo Diagnostics • Sealed
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 text-xs text-[#6b7280]">
                  <span>Consent Delegation: Revocable any time by patient.</span>
                  <Link href="/patient">
                    <Button variant="secondary" size="sm">
                      Open Patient Vault
                    </Button>
                  </Link>
                </div>
              </Card>
            )}

            {selectedPillar === "doctor" && (
              <Card variant="mockup" className="space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                  <div className="flex items-center gap-2">
                    <Stethoscope className="h-5 w-5 text-[#111111]" />
                    <span className="font-semibold text-sm text-[#111111]">
                      Provider EMR • Digital Consultation & E-Prescription
                    </span>
                  </div>
                  <Badge variant="verified">HPR Digitally Signed</Badge>
                </div>

                {/* Clean Clinical Prescription Card */}
                <div className="p-4 bg-[#f8f9fa] rounded-lg border border-[#e5e7eb] space-y-3 text-xs">
                  <div className="flex items-center justify-between border-b border-[#e5e7eb] pb-2">
                    <div>
                      <span className="font-semibold text-[#111111] text-sm">Patient: Arun Patel</span>
                      <span className="text-[#6b7280] ml-2">42y, Male • ABHA: 91-8472-1092-4821</span>
                    </div>
                    <span className="font-mono text-[11px] text-[#059669] bg-[#ecfdf5] px-2 py-0.5 rounded border border-[#a7f3d0]">
                      Diagnosis: Essential Hypertension (ICD-10 I10)
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    <div className="p-2.5 bg-white rounded border border-[#e5e7eb]">
                      <div className="font-semibold text-[#111111]">1. Atorvastatin 20mg Tablet</div>
                      <div className="text-[#6b7280] mt-0.5">1 tab once daily at bedtime • Duration: 30 Days</div>
                    </div>
                    <div className="p-2.5 bg-white rounded border border-[#e5e7eb]">
                      <div className="font-semibold text-[#111111]">2. Amlodipine 5mg Tablet</div>
                      <div className="text-[#6b7280] mt-0.5">1 tab once daily in morning • Duration: 30 Days</div>
                    </div>
                  </div>
                </div>

                {/* Collapsible FHIR R4 Bundle Toggle */}
                <div>
                  <button
                    onClick={() => setShowDoctorFhir(!showDoctorFhir)}
                    className="text-xs text-[#6b7280] hover:text-[#111111] flex items-center gap-1 font-medium transition-colors cursor-pointer"
                  >
                    <Code2 className="h-3.5 w-3.5" />
                    <span>{showDoctorFhir ? "Hide FHIR R4 Schema" : "Inspect Under-the-Hood FHIR R4 Bundle (JSON)"}</span>
                    {showDoctorFhir ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  </button>

                  {showDoctorFhir && (
                    <div className="mt-2.5 p-3.5 bg-[#111111] text-[#f3f4f6] rounded-lg font-mono text-[11px] overflow-x-auto max-h-48 border border-[#262626]">
                      <pre>{JSON.stringify({
                        resourceType: "MedicationRequest",
                        id: "medrx-cardio-9102",
                        status: "active",
                        intent: "order",
                        medicationCodeableConcept: { text: "Atorvastatin 20mg" },
                        subject: { reference: "Patient/ABHA-91-8472-1092-4821", display: "Arun Patel" },
                        requester: { reference: "Practitioner/hpr-ananya-sharma", display: "Dr. Ananya Sharma" },
                        authoredOn: new Date().toISOString()
                      }, null, 2)}</pre>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-1 text-xs text-[#6b7280]">
                  <span>Instant history review & structured e-prescriptions.</span>
                  <Link href="/doctor">
                    <Button variant="secondary" size="sm">
                      Open Doctor EMR
                    </Button>
                  </Link>
                </div>
              </Card>
            )}

            {selectedPillar === "lab" && (
              <Card variant="mockup" className="space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                  <div className="flex items-center gap-2">
                    <FlaskConical className="h-5 w-5 text-[#111111]" />
                    <span className="font-semibold text-sm text-[#111111]">
                      Diagnostic Gateway • Pathology & LOINC Ingestion
                    </span>
                  </div>
                  <Badge variant="emerald">NABL ISO 15189:2022</Badge>
                </div>

                {/* Clean Clinical Diagnostic Report Card */}
                <div className="p-4 bg-[#f8f9fa] rounded-lg border border-[#e5e7eb] space-y-3 text-xs">
                  <div className="flex items-center justify-between border-b border-[#e5e7eb] pb-2">
                    <div>
                      <span className="font-semibold text-[#111111] text-sm">Apollo Diagnostics Central</span>
                      <span className="text-[#6b7280] ml-2">Facility HFR: HFR-DEL-91024</span>
                    </div>
                    <span className="text-[11px] text-[#059669] font-medium flex items-center gap-1">
                      <FileCheck2 className="h-3.5 w-3.5 text-[#10b981]" />
                      SHA-256 Tamper-Sealed
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    <div className="p-2.5 bg-white rounded border border-[#e5e7eb]">
                      <div className="text-[11px] text-[#6b7280]">Fasting Blood Glucose (LOINC 1558-6)</div>
                      <div className="text-sm font-semibold text-[#111111] mt-0.5">94 mg/dL <span className="text-xs font-normal text-[#059669]">(Normal)</span></div>
                    </div>
                    <div className="p-2.5 bg-white rounded border border-[#e5e7eb]">
                      <div className="text-[11px] text-[#6b7280]">Total Serum Cholesterol (LOINC 2093-3)</div>
                      <div className="text-sm font-semibold text-[#111111] mt-0.5">185 mg/dL <span className="text-xs font-normal text-[#059669]">(Desirable)</span></div>
                    </div>
                  </div>
                </div>

                {/* Collapsible FHIR DiagnosticReport JSON */}
                <div>
                  <button
                    onClick={() => setShowLabFhir(!showLabFhir)}
                    className="text-xs text-[#6b7280] hover:text-[#111111] flex items-center gap-1 font-medium transition-colors cursor-pointer"
                  >
                    <Code2 className="h-3.5 w-3.5" />
                    <span>{showLabFhir ? "Hide FHIR Schema" : "Inspect Under-the-Hood DiagnosticReport (JSON)"}</span>
                    {showLabFhir ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  </button>

                  {showLabFhir && (
                    <div className="mt-2.5 p-3.5 bg-[#111111] text-[#f3f4f6] rounded-lg font-mono text-[11px] overflow-x-auto max-h-48 border border-[#262626]">
                      <pre>{JSON.stringify({
                        resourceType: "DiagnosticReport",
                        id: "dr-apollo-0925",
                        status: "final",
                        code: { coding: [{ system: "http://loinc.org", code: "57021-8", display: "Lipid Panel" }] },
                        subject: { reference: "Patient/ABHA-91-8472-1092-4821" },
                        performer: [{ reference: "Organization/HFR-DEL-91024", display: "Apollo Diagnostics Central" }],
                        presentedForm: [{ contentType: "application/pdf", hash: "d5a8b79e13c84f494f69747a28e9323f4b46c6a49dbd29486c434f09a5ebc109" }]
                      }, null, 2)}</pre>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-1 text-xs text-[#6b7280]">
                  <span>Accredited diagnostic ingestion directly into patient vault.</span>
                  <Link href="/lab">
                    <Button variant="secondary" size="sm">
                      Open Diagnostic Gateway
                    </Button>
                  </Link>
                </div>
              </Card>
            )}
          </div>

        </div>
      </section>

      {/* 3. FEATURE CARDS GRID (Clean Cal.com Surfaces, 0 Benchmarking Noise) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-3">
          <Badge variant="default">Enterprise Guarantees</Badge>
          <h2 className="display-md text-[#111111]">
            Engineered for Uncompromising Interoperability
          </h2>
          <p className="text-sm sm:text-base text-[#6b7280]">
            Every layer follows standardized protocols to eliminate data fragmentation across Indian healthcare.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Self-Sovereign Consent */}
          <Card variant="feature" className="p-6 flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-full bg-white border border-[#e5e7eb] flex items-center justify-center text-[#111111] mb-5 shadow-xs">
                <Lock className="h-5 w-5" />
              </div>
              <CardTitle>Self-Sovereign Consent</CardTitle>
              <CardDescription className="mt-2 text-sm leading-relaxed text-[#6b7280]">
                Patients maintain cryptographic ownership over their health data. Grant, inspect, or revoke clinical access with one tap.
              </CardDescription>
            </div>
          </Card>

          {/* Card 2: FHIR R4 Bundle Compliance */}
          <Card variant="feature" className="p-6 flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-full bg-white border border-[#e5e7eb] flex items-center justify-center text-[#111111] mb-5 shadow-xs">
                <FileText className="h-5 w-5" />
              </div>
              <CardTitle>HL7 FHIR R4 Standards</CardTitle>
              <CardDescription className="mt-2 text-sm leading-relaxed text-[#6b7280]">
                Universal schema compatibility for Patients, Practitioners, Encounters, Observations, and DiagnosticReports eliminates vendor lock-in.
              </CardDescription>
            </div>
          </Card>

          {/* Card 3: Tamper-Evident Security */}
          <Card variant="feature" className="p-6 flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-full bg-white border border-[#e5e7eb] flex items-center justify-center text-[#111111] mb-5 shadow-xs">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <CardTitle>Tamper-Evident Records</CardTitle>
              <CardDescription className="mt-2 text-sm leading-relaxed text-[#6b7280]">
                Every diagnostic PDF and prescription is stamped with SHA-256 integrity digests, preventing record tampering across disparate facilities.
              </CardDescription>
            </div>
          </Card>
        </div>
      </section>

      {/* 4. PRE-FOOTER LIGHT CTA BAND (#f5f5f5 Card, 48px Padding, Display-sm) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-[12px] bg-[#f5f5f5] p-10 sm:p-14 text-center space-y-6 border border-transparent">
          <div className="max-w-2xl mx-auto space-y-3">
            <h3 className="display-sm text-[#111111]">
              Smarter, simpler clinical records and scheduling.
            </h3>
            <p className="text-sm sm:text-base text-[#6b7280] leading-relaxed">
              Join the unified healthcare network. Connect with your ABHA identifier in under 60 seconds.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link href="/register">
              <Button variant="primary" size="lg">
                <span>Create ABHA Profile</span>
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
            <Link href="/doctor">
              <Button variant="secondary" size="lg">
                Provider Onboarding
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
