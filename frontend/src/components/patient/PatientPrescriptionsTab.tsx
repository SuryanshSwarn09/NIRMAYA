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
  Pill, 
  Code, 
  ShieldCheck, 
  RefreshCw, 
  CheckCircle2, 
  FileText 
} from "lucide-react";
import { MedicationRequest } from "@/lib/api";

export interface PatientPrescriptionsTabProps {
  prescriptions: MedicationRequest[];
  loading?: boolean;
  onRefresh?: () => void;
  onViewFhir: (rxId: string) => void;
  fetchingFhirId?: string | null;
}

export function PatientPrescriptionsTab({
  prescriptions,
  loading = false,
  onRefresh,
  onViewFhir,
  fetchingFhirId,
}: PatientPrescriptionsTabProps) {
  return (
    <div className="animate-fade-in max-w-5xl mx-auto space-y-6">
      <Card variant="mockup" className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#e5e7eb] gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Pill className="h-5 w-5 text-[#111111]" />
              <CardTitle className="text-xl">Active Digital Prescriptions & Pharmacy Orders</CardTitle>
              <Badge variant="verified" size="sm">FHIR R4</Badge>
            </div>
            <CardDescription className="mt-1">
              Verifiable electronic prescriptions signed by licensed practitioners under ABDM HPR.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="emerald" size="sm">
              {prescriptions.length} Records
            </Badge>
            {onRefresh && (
              <Button
                variant="secondary"
                size="sm"
                disabled={loading}
                onClick={onRefresh}
                className="text-xs"
              >
                <RefreshCw className={`h-3.5 w-3.5 mr-1 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-[#6b7280]">
            Loading verified prescriptions from ABHA Health Vault...
          </div>
        ) : prescriptions.length === 0 ? (
          <div className="py-12 text-center space-y-3">
            <div className="h-12 w-12 rounded-full bg-[#f3f4f6] flex items-center justify-center mx-auto text-[#6b7280]">
              <Pill className="h-6 w-6" />
            </div>
            <h4 className="text-sm font-semibold text-[#111111]">No active prescriptions found</h4>
            <p className="text-xs text-[#6b7280] max-w-sm mx-auto">
              When your attending physician issues a signed digital prescription during consultation, it will appear here instantly with full FHIR R4 provenance.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {prescriptions.map((rx) => {
              const isSigned = rx.is_signed;
              const isActive = rx.status === "active";
              return (
                <div
                  key={rx.id}
                  className="p-5 rounded-[10px] border border-[#e5e7eb] bg-white hover:border-[#d1d5db] transition-all space-y-4 shadow-xs"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#f3f4f6]">
                    <div className="flex items-start gap-3">
                      <div className="p-2.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] text-[#111111]">
                        <Pill className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-base font-bold text-[#111111]">
                            {rx.medication?.name || "Prescribed Medication"}
                          </h4>
                          <Badge
                            variant={isActive ? "emerald" : isSigned ? "default" : "warning"}
                            size="sm"
                          >
                            {rx.status.toUpperCase()}
                          </Badge>
                          {rx.allow_generic_substitution && (
                            <Badge variant="outline" size="sm">
                              Generic Allowed
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-[#6b7280] mt-0.5">
                          {rx.medication?.generic_name && `${rx.medication.generic_name} • `}
                          Form: {rx.medication?.form || "oral"} • Route: {rx.medication?.route || "oral"}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-start sm:self-auto">
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={fetchingFhirId === rx.id}
                        onClick={() => onViewFhir(rx.id)}
                        className="text-xs"
                      >
                        <Code className="h-3.5 w-3.5 mr-1" />
                        {fetchingFhirId === rx.id ? "Loading..." : "FHIR R4"}
                      </Button>
                    </div>
                  </div>

                  {/* Dosage Instructions */}
                  <div className="p-3.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-1.5 text-xs">
                    <div className="font-semibold text-[#111111] flex items-center gap-1.5">
                      <span>Directions for Use:</span>
                    </div>
                    <p className="text-sm font-medium text-[#111111]">
                      {rx.dosage_text}
                    </p>
                    <div className="flex flex-wrap gap-4 pt-1 text-[11px] text-[#6b7280]">
                      {rx.dose_quantity && (
                        <span>Dose: <strong className="text-[#111111]">{rx.dose_quantity} {rx.dose_unit || "mg"}</strong></span>
                      )}
                      {rx.frequency && (
                        <span>Frequency: <strong className="text-[#111111]">{rx.frequency}x per {rx.period || 1} {rx.period_unit || "day"}</strong></span>
                      )}
                      {rx.route && (
                        <span>Route: <strong className="text-[#111111]">{rx.route}</strong></span>
                      )}
                      {rx.as_needed && (
                        <span className="text-[#d97706] font-semibold">PRN (As Needed)</span>
                      )}
                    </div>
                  </div>

                  {/* Dispense & Refill Constraints */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-2.5 rounded-[6px] border border-[#f3f4f6] bg-[#fafafa]">
                      <span className="text-[11px] text-[#6b7280] block">Quantity Dispensed</span>
                      <span className="font-semibold text-[#111111]">{rx.dispense_quantity || "N/A"} {rx.dispense_unit || "units"}</span>
                    </div>
                    <div className="p-2.5 rounded-[6px] border border-[#f3f4f6] bg-[#fafafa]">
                      <span className="text-[11px] text-[#6b7280] block">Days Supply</span>
                      <span className="font-semibold text-[#111111]">{rx.expected_supply_duration_days ? `${rx.expected_supply_duration_days} Days` : "Course duration"}</span>
                    </div>
                    <div className="p-2.5 rounded-[6px] border border-[#f3f4f6] bg-[#fafafa]">
                      <span className="text-[11px] text-[#6b7280] block">Authorized Refills</span>
                      <span className="font-semibold text-[#111111]">{rx.number_of_repeats_allowed ?? 0} Refills Remaining</span>
                    </div>
                    <div className="p-2.5 rounded-[6px] border border-[#f3f4f6] bg-[#fafafa]">
                      <span className="text-[11px] text-[#6b7280] block">Authored On</span>
                      <span className="font-semibold text-[#111111]">{new Date(rx.authored_on).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* Cryptographic Digital Signature & Clinician Provenance */}
                  {isSigned && (
                    <div className="p-3 rounded-[8px] border border-[#a7f3d0] bg-[#ecfdf5] flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2">
                      <div className="flex items-center gap-2 text-[#065f46]">
                        <ShieldCheck className="h-4 w-4 text-[#059669] shrink-0" />
                        <span className="font-semibold">
                          Digitally Signed by Attending Clinician
                        </span>
                      </div>
                      {rx.signature_hash && (
                        <span className="font-mono text-[10px] text-[#047857] truncate max-w-xs bg-white/70 px-2 py-0.5 rounded border border-[#a7f3d0]">
                          SHA-256: {rx.signature_hash}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}
