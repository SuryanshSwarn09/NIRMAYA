"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Badge, Button, Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter, NavPillGroup } from "@/components/ui";
import { 
  ShieldCheck, 
  Activity, 
  Stethoscope, 
  FlaskConical, 
  Lock, 
  CheckCircle2, 
  ArrowRight,
  Database,
  Calendar,
  Clock,
  UserCheck,
  FileText,
  FileCheck2,
  ExternalLink,
  Code2
} from "lucide-react";

export default function Home() {
  const [selectedPillar, setSelectedPillar] = useState("patient");
  const [selectedSlot, setSelectedSlot] = useState("10:15 AM");
  const [selectedDate, setSelectedDate] = useState("Wed 24");

  return (
    <div className="space-y-24 pb-20">
      {/* 1. HERO BAND (7/5 Desktop Grid, 96px Rhythm, White Canvas) */}
      <section className="pt-12 pb-16 lg:pt-20 lg:pb-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            
            {/* Left 7 Columns: Editorial Headline & Primary CTAs */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#f8f9fa] border border-[#e5e7eb] text-xs font-medium text-[#111111]">
                <span className="h-2 w-2 rounded-full bg-[#10b981]" />
                <span>ABDM & HL7 FHIR R4 Interoperability Network</span>
              </div>

              <h1 className="display-xl text-[#111111]">
                The interoperable health network,{" "}
                <span className="text-[#6b7280]">finally simplified.</span>
              </h1>

              <p className="text-base sm:text-lg text-[#374151] leading-relaxed max-w-2xl font-normal">
                NIRMAYA unifies longitudinal patient vaults, clinical provider EMRs, and diagnostic laboratories 
                into an interoperable, consent-driven network anchored on HL7 FHIR R4.
              </p>

              {/* Primary Monochrome CTAs */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <Link href="/patient">
                  <Button variant="primary" size="lg">
                    <span>Access Patient Vault</span>
                    <ArrowRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
                <Link href="/doctor">
                  <Button variant="secondary" size="lg">
                    <Stethoscope className="h-4 w-4 mr-1" />
                    <span>Provider EMR</span>
                  </Button>
                </Link>
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline" size="lg">
                    <Database className="h-4 w-4 mr-1 text-[#6b7280]" />
                    <span>FastAPI Swagger</span>
                    <ExternalLink className="h-3.5 w-3.5 ml-1 opacity-50" />
                  </Button>
                </a>
              </div>

              {/* Enterprise Guarantees Checklist */}
              <div className="pt-8 border-t border-[#e5e7eb] grid grid-cols-2 sm:grid-cols-3 gap-3.5 text-xs text-[#374151] font-medium">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#111111]" />
                  <span>Zero Data Silos</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#111111]" />
                  <span>Longitudinal Vault</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#111111]" />
                  <span>ABHA ID Linked</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#111111]" />
                  <span>HL7 FHIR R4 Bundles</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#111111]" />
                  <span>Consent-Driven HIP/HIU</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#111111]" />
                  <span>Sub-ms Telemetry</span>
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
                      30 Min FHIR Tele-consult
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
                      Book & Generate Consent Artifact
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
              Switch views to inspect real clinical chrome across each healthcare touchpoint.
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
              <Card variant="mockup" className="space-y-4">
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
                      Metformin 500mg
                    </div>
                    <div className="text-[11px] text-[#6b7280]">
                      Issued by Dr. Sharma
                    </div>
                  </div>
                  <div className="p-3.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-1">
                    <div className="text-[#6b7280]">Recent Diagnostic</div>
                    <div className="font-semibold text-sm text-[#111111]">
                      Lipid Profile (Normal)
                    </div>
                    <div className="text-[11px] text-[#6b7280]">
                      Apollo Diagnostics
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 text-xs text-[#6b7280]">
                  <span>Consent Delegation: Revocable any time by patient.</span>
                  <Link href="/patient">
                    <Button variant="secondary" size="sm">
                      Open Patient Portal
                    </Button>
                  </Link>
                </div>
              </Card>
            )}

            {selectedPillar === "doctor" && (
              <Card variant="mockup" className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                  <div className="flex items-center gap-2">
                    <Stethoscope className="h-5 w-5 text-[#111111]" />
                    <span className="font-semibold text-sm text-[#111111]">
                      Clinical EMR • SOAP Encounter & E-Prescription
                    </span>
                  </div>
                  <Badge variant="fhir">FHIR MedicationRequest</Badge>
                </div>

                <div className="space-y-2 text-xs font-mono bg-[#f8f9fa] p-4 rounded-[8px] border border-[#e5e7eb] text-[#374151]">
                  <div>// HL7 FHIR R4 Bundle Fragment Generated On Sign</div>
                  <div>&#123;</div>
                  <div className="pl-4">&quot;resourceType&quot;: &quot;MedicationRequest&quot;,</div>
                  <div className="pl-4">&quot;status&quot;: &quot;active&quot;,</div>
                  <div className="pl-4">&quot;intent&quot;: &quot;order&quot;,</div>
                  <div className="pl-4">&quot;medicationCodeableConcept&quot;: &#123; &quot;text&quot;: &quot;Atorvastatin 20mg&quot; &#125;,</div>
                  <div className="pl-4">&quot;requester&quot;: &#123; &quot;reference&quot;: &quot;Practitioner/hpr-9102&quot; &#125;</div>
                  <div>&#125;</div>
                </div>

                <div className="flex items-center justify-between pt-2 text-xs text-[#6b7280]">
                  <span>Instant history review & structured e-prescriptions.</span>
                  <Link href="/doctor">
                    <Button variant="secondary" size="sm">
                      Open EMR Console
                    </Button>
                  </Link>
                </div>
              </Card>
            )}

            {selectedPillar === "lab" && (
              <Card variant="mockup" className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
                  <div className="flex items-center gap-2">
                    <FlaskConical className="h-5 w-5 text-[#111111]" />
                    <span className="font-semibold text-sm text-[#111111]">
                      Diagnostic Gateway • Dual Cryptographic & FHIR Ingest
                    </span>
                  </div>
                  <Badge variant="emerald">LOINC Mapped</Badge>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-1">
                    <div className="flex items-center gap-1.5 font-semibold text-[#111111]">
                      <FileCheck2 className="h-4 w-4 text-[#10b981]" />
                      Cryptographic PDF Ingestion
                    </div>
                    <p className="text-[#6b7280]">
                      SHA-256 integrity hash verified and stored in encrypted S3/MinIO bucket.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-1">
                    <div className="flex items-center gap-1.5 font-semibold text-[#111111]">
                      <Code2 className="h-4 w-4 text-[#111111]" />
                      Structured FHIR Observation
                    </div>
                    <p className="text-[#6b7280]">
                      Quantitative values mapped to LOINC codes for automated trending analysis.
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 text-xs text-[#6b7280]">
                  <span>Direct ingest for accredited clinical labs.</span>
                  <Link href="/lab">
                    <Button variant="secondary" size="sm">
                      Access Diagnostic Portal
                    </Button>
                  </Link>
                </div>
              </Card>
            )}
          </div>

        </div>
      </section>

      {/* 3. FEATURE CARDS GRID (3-up Desktop, #f5f5f5 Light Gray Surfaces, 32px Padding) */}
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
          <Card variant="feature" className="flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-full bg-white border border-[#e5e7eb] flex items-center justify-center text-[#111111] mb-5 shadow-xs">
                <Lock className="h-5 w-5" />
              </div>
              <CardTitle>Self-Sovereign Consent</CardTitle>
              <CardDescription className="mt-2">
                Patients maintain cryptographic ownership over their health records with granular, time-bound delegation.
              </CardDescription>
            </div>

            {/* Embedded Mini Chrome */}
            <div className="mt-6 pt-4 border-t border-[#e5e7eb] space-y-2 text-xs text-[#374151]">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-[#6b7280]">Consent Token:</span>
                <span className="font-semibold">HIU-CONSENT-9418</span>
              </div>
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-[#6b7280]">TTL Remaining:</span>
                <span className="text-[#059669] font-semibold">23h 48m</span>
              </div>
            </div>
          </Card>

          {/* Card 2: FHIR R4 Bundle Compliance */}
          <Card variant="feature" className="flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-full bg-white border border-[#e5e7eb] flex items-center justify-center text-[#111111] mb-5 shadow-xs">
                <FileText className="h-5 w-5" />
              </div>
              <CardTitle>HL7 FHIR R4 Compliant</CardTitle>
              <CardDescription className="mt-2">
                Full schema compatibility with Patient, Practitioner, Encounter, Observation, and DiagnosticReport.
              </CardDescription>
            </div>

            {/* Embedded Mini Chrome */}
            <div className="mt-6 pt-4 border-t border-[#e5e7eb] space-y-2 text-xs text-[#374151]">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-[#6b7280]">Validation:</span>
                <span className="text-[#059669] font-semibold">100% Passed</span>
              </div>
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-[#6b7280]">Pydantic v2:</span>
                <span className="font-semibold">Sub-millisecond</span>
              </div>
            </div>
          </Card>

          {/* Card 3: Real-Time Telemetry */}
          <Card variant="feature" className="flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-full bg-white border border-[#e5e7eb] flex items-center justify-center text-[#111111] mb-5 shadow-xs">
                <Activity className="h-5 w-5" />
              </div>
              <CardTitle>Real-Time Interoperability</CardTitle>
              <CardDescription className="mt-2">
                High-throughput async FastAPI endpoints backed by Supabase PostgreSQL and Redis caching.
              </CardDescription>
            </div>

            {/* Embedded Mini Chrome */}
            <div className="mt-6 pt-4 border-t border-[#e5e7eb] space-y-2 text-xs text-[#374151]">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-[#6b7280]">API Telemetry:</span>
                <span className="text-[#059669] font-semibold">&lt; 25ms avg</span>
              </div>
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-[#6b7280]">ABDM Gateway:</span>
                <span className="font-semibold">Sandbox Active</span>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* 4. PRE-FOOTER LIGHT CTA BAND (#f5f5f5 Card, 48px Padding, Display-sm) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-[12px] bg-[#f5f5f5] p-10 sm:p-14 text-center space-y-6 border border-transparent">
          <div className="max-w-2xl mx-auto space-y-3">
            <h3 className="display-sm text-[#111111]">
              Smarter, simpler clinical scheduling and records.
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
