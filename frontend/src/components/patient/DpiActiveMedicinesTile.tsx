"use client";

import React from "react";
import { Pill, Clock, AlertCircle, CheckCircle2, Calendar, Stethoscope, ChevronRight } from "lucide-react";
import { Card, Badge, Button } from "@/components/ui";

export interface PlainSchedule {
  morning: boolean;
  afternoon: boolean;
  night: boolean;
  time_description: string;
}

export interface ActiveMedicine {
  medicine_id: string;
  name: string;
  dosage_form: string;
  strength: string;
  schedule: PlainSchedule;
  plain_instruction: string;
  remaining_days: number;
  total_days: number;
  refill_due_date?: string | null;
  is_refill_urgent?: boolean;
  prescribed_by: string;
  prescribed_at: string;
}

export interface DpiActiveMedicinesTileProps {
  medicines: (ActiveMedicine | any)[];
  patientName?: string;
}

export function DpiActiveMedicinesTile({ medicines, patientName }: DpiActiveMedicinesTileProps) {
  // Normalize items whether they conform to ActiveMedicine or CitizenActiveMedicineItem
  const normalizedMedicines: ActiveMedicine[] = medicines.map((item, idx) => {
    if ("medicine_id" in item && "schedule" in item) {
      return item as ActiveMedicine;
    }
    // Convert CitizenActiveMedicineItem
    const schedItems: any[] = item.plain_schedule || [];
    const morning = schedItems.some((s) => s.slot === "morning");
    const afternoon = schedItems.some((s) => s.slot === "afternoon");
    const night = schedItems.some((s) => s.slot === "night");

    return {
      medicine_id: item.id || `med-${idx}`,
      name: item.brand_name || item.name || "Medication",
      dosage_form: item.dosage_form || "Tablet",
      strength: item.dosage_display || item.strength || item.generic_name || "",
      schedule: {
        morning,
        afternoon,
        night,
        time_description: item.instructions || "",
      },
      plain_instruction: item.instructions || "Take as directed with water.",
      remaining_days: item.days_remaining ?? item.remaining_days ?? 7,
      total_days: item.course_duration_days ?? item.total_days ?? 14,
      refill_due_date: item.end_date || null,
      is_refill_urgent: item.refill_urgency === "urgent" || item.refill_needed || false,
      prescribed_by: item.prescribing_doctor || item.prescribed_by || "Attending Physician",
      prescribed_at: item.prescribed_on || item.prescribed_at || "Recent",
    };
  });

  return (
    <Card variant="mockup" className="p-0 overflow-hidden border border-[#e5e7eb] bg-white shadow-xs">
      {/* Tile Title Strip */}
      <div className="px-5 py-3 bg-[#f9fafb] border-b border-[#e5e7eb] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[#3b82f6]" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#111827]">
            Tile 2: Today&apos;s Active Medicines (Daily Schedule)
          </h3>
        </div>
        <Badge variant="neutral" size="sm">
          {normalizedMedicines.length} Prescriptions Active
        </Badge>
      </div>

      <div className="p-5 sm:p-6 space-y-4">
        {normalizedMedicines.length === 0 ? (
          <div className="p-6 rounded-[10px] bg-[#f9fafb] border border-[#e5e7eb] text-center space-y-2">
            <CheckCircle2 className="h-8 w-8 text-[#10b981] mx-auto" />
            <h4 className="text-sm font-semibold text-[#111827]">No Active Prescription Courses</h4>
            <p className="text-xs text-[#6b7280]">
              You have no active medications scheduled for today. Consult your practitioner if you feel unwell.
            </p>
          </div>
        ) : (
          <div className="space-y-3.5">
            {normalizedMedicines.map((med) => {

              const progressPct = Math.min(
                100,
                Math.round(((med.total_days - med.remaining_days) / med.total_days) * 100)
              );

              return (
                <div
                  key={med.medicine_id}
                  className="rounded-[10px] border border-[#e5e7eb] bg-white p-4 space-y-3 hover:border-[#111827] transition-all shadow-2xs"
                >
                  {/* Top Bar: Name, Dosage Form & Refill Urgency */}
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-base font-bold text-[#111827]">{med.name}</span>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded-[4px] bg-[#f3f4f6] text-[#374151] font-mono">
                          {med.strength}
                        </span>
                      </div>
                      <span className="text-xs text-[#6b7280] capitalize">{med.dosage_form}</span>
                    </div>

                    {med.is_refill_urgent ? (
                      <Badge variant="critical" size="sm">
                        Refill Due Soon ({med.remaining_days}d left)
                      </Badge>
                    ) : (
                      <Badge variant="verified" size="sm">
                        Course Active
                      </Badge>
                    )}
                  </div>

                  {/* Plain Language Time-of-Day Intake Indicators (No Latin abbreviations) */}
                  <div className="space-y-1.5">
                    <div className="text-[11px] font-semibold text-[#6b7280]">When to take today:</div>
                    <div className="grid grid-cols-3 gap-2">
                      {/* Morning Indicator */}
                      <div
                        className={`p-2 rounded-[6px] text-center border text-xs font-semibold flex items-center justify-center gap-1.5 ${
                          med.schedule.morning
                            ? "bg-[#ecfdf5] border-[#a7f3d0] text-[#065f46]"
                            : "bg-[#f9fafb] border-[#e5e7eb] text-[#9ca3af] opacity-60"
                        }`}
                      >
                        <span>Morning</span>
                        {med.schedule.morning ? (
                          <span className="h-1.5 w-1.5 rounded-full bg-[#10b981]" />
                        ) : (
                          <span className="text-[10px]">&times;</span>
                        )}
                      </div>

                      {/* Afternoon Indicator */}
                      <div
                        className={`p-2 rounded-[6px] text-center border text-xs font-semibold flex items-center justify-center gap-1.5 ${
                          med.schedule.afternoon
                            ? "bg-[#ecfdf5] border-[#a7f3d0] text-[#065f46]"
                            : "bg-[#f9fafb] border-[#e5e7eb] text-[#9ca3af] opacity-60"
                        }`}
                      >
                        <span>Afternoon</span>
                        {med.schedule.afternoon ? (
                          <span className="h-1.5 w-1.5 rounded-full bg-[#10b981]" />
                        ) : (
                          <span className="text-[10px]">&times;</span>
                        )}
                      </div>

                      {/* Night Indicator */}
                      <div
                        className={`p-2 rounded-[6px] text-center border text-xs font-semibold flex items-center justify-center gap-1.5 ${
                          med.schedule.night
                            ? "bg-[#ecfdf5] border-[#a7f3d0] text-[#065f46]"
                            : "bg-[#f9fafb] border-[#e5e7eb] text-[#9ca3af] opacity-60"
                        }`}
                      >
                        <span>Night</span>
                        {med.schedule.night ? (
                          <span className="h-1.5 w-1.5 rounded-full bg-[#10b981]" />
                        ) : (
                          <span className="text-[10px]">&times;</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Plain Language Instructions Banner */}
                  <div className="p-2.5 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb] text-xs text-[#111827]">
                    <span className="font-semibold">Instruction: </span>
                    <span>{med.plain_instruction}</span>
                  </div>

                  {/* Course Duration Progress & Refill Countdown */}
                  <div className="space-y-1 pt-1">
                    <div className="flex items-center justify-between text-[11px] text-[#6b7280]">
                      <span>
                        Course Progress: <strong className="text-[#111827]">{med.total_days - med.remaining_days} of {med.total_days} days completed</strong>
                      </span>
                      <span>{med.remaining_days} days remaining</span>
                    </div>
                    <div className="w-full h-1.5 bg-[#e5e7eb] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#111827] rounded-full transition-all"
                        style={{ width: `${progressPct}%` }}
                      />
                    </div>
                  </div>

                  {/* Doctor Attestation Footer */}
                  <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-[#6b7280] pt-2 border-t border-[#f3f4f6]">
                    <span className="flex items-center gap-1">
                      <Stethoscope className="h-3 w-3 text-[#111827]" />
                      <span>Prescribed by {med.prescribed_by}</span>
                    </span>
                    <span>Issued: {med.prescribed_at}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
}
