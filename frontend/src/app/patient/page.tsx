"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button, Badge, Card, CardTitle, CardDescription } from "@/components/ui";
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
  AlertCircle
} from "lucide-react";

export default function PatientVaultPage() {
  const { user } = useAuth();
  const [consentActive, setConsentActive] = useState(true);

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
          <Link href="/doctor">
            <Button variant="primary" size="sm">
              Book Consultation
            </Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
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
                  onClick={() => setConsentActive(true)}
                  className="font-semibold underline cursor-pointer"
                >
                  Restore
                </button>
              </div>
            )}
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

    </div>
  );
}
