"use client";

import React from "react";
import { 
  Card, 
  CardTitle, 
  CardDescription, 
  Badge, 
  Button 
} from "@/components/ui";
import { 
  QrCode, 
  Lock, 
  Clock, 
  Calendar, 
  Download, 
  Pill, 
  Activity, 
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Stethoscope
} from "lucide-react";
import { Appointment, MedicationRequest } from "@/lib/api";
import { DigitalAbhaCard } from "./DigitalAbhaCard";

export interface PatientOverviewTabProps {
  abhaId?: string;
  abhaAddress?: string;
  patientName?: string;
  gender?: string;
  dob?: string;
  mobile?: string;
  bloodGroup?: string;
  stateNode?: string;
  distName?: string;
  emergencyContact?: string;
  organDonor?: boolean;
  qrPayload?: string;
  onOpenExport?: () => void;
  onOpenVerify?: () => void;
  consentActive: boolean;
  onToggleConsent: (active: boolean) => void;
  scheduledAppointments: Appointment[];
  prescriptions: MedicationRequest[];
  vitalsList: any[];
  onSelectTab: (tab: "overview" | "prescriptions" | "problems" | "records" | "book") => void;
  onOpenLogVitals: () => void;
  onViewFhirPrescription?: (rx: MedicationRequest) => void;
}

export function PatientOverviewTab({
  abhaId = "91-8472-1092-4821",
  abhaAddress = "arun.patel@abdm",
  patientName = "Arun Patel",
  gender = "Male",
  dob = "1990-06-04",
  mobile = "+91 98*** **421",
  bloodGroup = "O Positive (O+)",
  stateNode = "NCT of Delhi",
  distName = "South Delhi",
  emergencyContact = "Pooja Patel (+91 98*** **991)",
  organDonor = true,
  qrPayload,
  onOpenExport,
  onOpenVerify,
  consentActive,
  onToggleConsent,
  scheduledAppointments,
  prescriptions,
  vitalsList,
  onSelectTab,
  onOpenLogVitals,
  onViewFhirPrescription,
}: PatientOverviewTabProps) {
  // Most recent 2 prescriptions
  const recentPrescriptions = prescriptions.slice(0, 2);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in">
      
      {/* ========================================================================
          LEFT 5 COLUMNS: ABHA Card, Consent Delegation & Care Identifiers
          ======================================================================== */}
      <div className="lg:col-span-5 space-y-6">
        
        {/* Authentic Digital ABHA ID Card Canvas with 3D Flip & Vector QR */}
        <DigitalAbhaCard
          abhaId={abhaId}
          abhaAddress={abhaAddress}
          patientName={patientName}
          gender={gender}
          dob={dob}
          mobile={mobile}
          bloodGroup={bloodGroup}
          stateNode={stateNode}
          distName={distName}
          emergencyContact={emergencyContact}
          organDonor={organDonor}
          qrPayload={qrPayload}
          onOpenExport={onOpenExport}
          onOpenVerify={onOpenVerify}
        />

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
                  onClick={() => onToggleConsent(false)}
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
                onClick={() => onToggleConsent(true)}
                className="font-semibold underline cursor-pointer"
              >
                Restore
              </button>
            </div>
          )}
        </Card>

        {/* Emergency & Self-Sovereignty Guarantees */}
        <div className="p-4 rounded-[12px] border border-[#e5e7eb] bg-[#f8f9fa] space-y-2 text-xs">
          <div className="flex items-center gap-2 font-semibold text-[#111111]">
            <ShieldCheck className="h-4 w-4 text-[#059669]" />
            <span>ABDM Privacy & Security Architecture</span>
          </div>
          <p className="text-[#6b7280] leading-relaxed">
            Records are federated directly from authorized Health Information Providers (HIPs). Data is encrypted in transit via ECDH key exchange with FIDELIUS compliance.
          </p>
        </div>

      </div>

      {/* ========================================================================
          RIGHT 7 COLUMNS: Scheduled Encounters, Prescriptions & Vitals Snapshots
          ======================================================================== */}
      <div className="lg:col-span-7 space-y-6">

        {/* Scheduled Encounters Section */}
        <Card variant="mockup" className="space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-[#111111]" />
              <CardTitle className="text-base">Upcoming Clinical Consultations</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="emerald" size="sm">
                {scheduledAppointments.length} Confirmed
              </Badge>
              <button
                onClick={() => onSelectTab("book")}
                className="text-xs text-[#111111] hover:underline font-medium flex items-center gap-1 cursor-pointer"
              >
                Book New <ArrowRight className="h-3 w-3" />
              </button>
            </div>
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
                  className="p-3.5 rounded-[8px] border border-[#e5e7eb] bg-white space-y-2 text-xs hover:border-[#111111] transition-colors"
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
                      FHIR R4 Encounter
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Recent e-Prescriptions Snapshot */}
        <Card variant="mockup" className="space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
            <div className="flex items-center gap-2">
              <Pill className="h-4 w-4 text-[#111111]" />
              <CardTitle className="text-base">Active e-Prescriptions & Medications</CardTitle>
            </div>
            <button
              onClick={() => onSelectTab("prescriptions")}
              className="text-xs text-[#111111] hover:underline font-medium flex items-center gap-1 cursor-pointer"
            >
              View All ({prescriptions.length}) <ArrowRight className="h-3 w-3" />
            </button>
          </div>

          {recentPrescriptions.length === 0 ? (
            <div className="p-4 text-center text-xs text-[#6b7280] bg-[#f8f9fa] rounded-[8px]">
              No active prescriptions found in this care cycle.
            </div>
          ) : (
            <div className="space-y-3">
              {recentPrescriptions.map((rx) => (
                <div
                  key={rx.id}
                  className="p-3.5 rounded-[8px] border border-[#e5e7eb] bg-white space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#111111] text-sm">
                        {rx.medication?.name || "Prescribed Medication"}
                      </span>
                      <Badge variant="emerald" size="sm">
                        {rx.status.toUpperCase()}
                      </Badge>
                    </div>
                    {onViewFhirPrescription && (
                      <button
                        onClick={() => onViewFhirPrescription(rx)}
                        className="text-[11px] font-mono text-[#2563eb] hover:underline cursor-pointer"
                      >
                        FHIR JSON
                      </button>
                    )}
                  </div>
                  <p className="text-xs text-[#374151]">
                    {rx.dosage_text}
                  </p>
                  <div className="flex items-center gap-3 text-[11px] text-[#6b7280] pt-1 border-t border-[#f3f4f6]">
                    <span>Qty: <strong className="text-[#111111]">{rx.dispense_quantity || "N/A"} {rx.dispense_unit || "units"}</strong></span>
                    <span>•</span>
                    <span>Repeats: <strong className="text-[#111111]">{rx.number_of_repeats_allowed ?? 0} refills</strong></span>
                    <span>•</span>
                    <span className="text-[#059669]">Digitally Signed</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Recent Observational Vitals Snapshot */}
        <Card variant="mockup" className="space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-[#111111]" />
              <CardTitle className="text-base">Recent Biometric Vitals (LOINC)</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onOpenLogVitals}
                className="text-xs font-semibold text-[#2563eb] hover:underline cursor-pointer"
              >
                + Log Vital
              </button>
              <button
                onClick={() => onSelectTab("records")}
                className="text-xs text-[#111111] hover:underline font-medium flex items-center gap-1 cursor-pointer"
              >
                Full Telemetry <ArrowRight className="h-3 w-3" />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {vitalsList.slice(0, 4).map((obs) => {
              const displayVal = obs.components && obs.components.length >= 2
                ? `${obs.components[0].value_quantity}/${obs.components[1].value_quantity}`
                : obs.value_quantity !== null && obs.value_quantity !== undefined
                ? obs.value_quantity
                : "--";
              const isHigh = obs.interpretation === "high" || obs.interpretation === "critically-high";
              const isLow = obs.interpretation === "low" || obs.interpretation === "critically-low";

              return (
                <div
                  key={obs.id}
                  className="p-3 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] hover:bg-white hover:border-[#d1d5db] transition-all space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-[#6b7280] font-medium truncate max-w-[90px]">
                      {obs.code_display}
                    </span>
                    <span
                      className={`text-[9px] font-semibold px-1.5 py-0.5 rounded ${
                        isHigh
                          ? "bg-[#fef2f2] text-[#991b1b]"
                          : isLow
                          ? "bg-[#fffbeb] text-[#92400e]"
                          : "bg-[#ecfdf5] text-[#065f46]"
                      }`}
                    >
                      {obs.interpretation?.toUpperCase() || "NORMAL"}
                    </span>
                  </div>
                  <div className="font-bold text-[#111111] text-base tracking-tight">
                    {displayVal}{" "}
                    <span className="text-[11px] font-normal text-[#6b7280]">{obs.value_unit}</span>
                  </div>
                  <div className="text-[10px] text-[#9ca3af] flex items-center justify-between pt-1 border-t border-[#f3f4f6]">
                    <span>{obs.effective_date_time}</span>
                    <span className="font-mono text-[9px]">LOINC {obs.code_value}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

      </div>

    </div>
  );
}
