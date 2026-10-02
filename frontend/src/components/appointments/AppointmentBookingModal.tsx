"use client";

import React, { useState } from "react";
import { 
  X, 
  CheckCircle2, 
  Calendar, 
  Clock, 
  User, 
  ShieldCheck, 
  Download, 
  FileText,
  AlertCircle,
  Copy,
  ExternalLink
} from "lucide-react";
import { Button, Badge, Card } from "@/components/ui";
import { 
  apiClient, 
  DoctorSlot, 
  SlotHoldResponse, 
  Appointment, 
  AppointmentType, 
  AppointmentCreate 
} from "@/lib/api";
import { SlotHoldCountdown } from "./SlotHoldCountdown";
import { useAuth } from "@/context/AuthContext";

export interface AppointmentBookingModalProps {
  isOpen: boolean;
  onClose: () => void;
  slot: DoctorSlot | null;
  doctorId: string;
  doctorName?: string;
  specialty?: string;
  consultationFee?: number;
  activeHold?: SlotHoldResponse | null;
  onHoldRelease?: () => Promise<void>;
  onSuccess?: (appointment: Appointment) => void;
}

export function AppointmentBookingModal({
  isOpen,
  onClose,
  slot,
  doctorId,
  doctorName = "Dr. Specialist",
  specialty = "Cardiology",
  consultationFee = 1500,
  activeHold,
  onHoldRelease,
  onSuccess,
}: AppointmentBookingModalProps) {
  const { user } = useAuth();

  const [appointmentType, setAppointmentType] = useState<AppointmentType>(
    slot?.is_teleconsult ? "teleconsultation" : "routine_checkup"
  );
  const [reason, setReason] = useState("");
  const [clinicalNotes, setClinicalNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Success view state
  const [confirmedAppointment, setConfirmedAppointment] = useState<Appointment | null>(null);
  const [copiedAbdm, setCopiedAbdm] = useState(false);

  if (!isOpen || !slot) return null;

  const formattedStart = new Date(slot.start_time).toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) {
      setErrorMsg("Please provide a reason or chief clinical complaint for this consultation.");
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const payload: AppointmentCreate = {
        doctor_id: doctorId,
        slot_id: slot.id,
        scheduled_start: slot.start_time,
        scheduled_end: slot.end_time,
        appointment_type: appointmentType,
        reason: reason.trim(),
        clinical_notes: clinicalNotes.trim() || undefined,
        teleconsultation_url: slot.is_teleconsult ? "https://meet.nirmaya.health/room/" + slot.id : undefined,
      };

      const result = await apiClient.bookAppointment(payload);
      setConfirmedAppointment(result);
      if (onSuccess) {
        onSuccess(result);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to complete appointment booking. Please try again.";
      setErrorMsg(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const careContextRef = confirmedAppointment?.id
    ? `APPT-${confirmedAppointment.id.replace(/-/g, "").substring(0, 8).toUpperCase()}`
    : "APPT-06EC8B98";

  const handleCopyCareContext = () => {
    navigator.clipboard.writeText(careContextRef);
    setCopiedAbdm(true);
    setTimeout(() => setCopiedAbdm(false), 2000);
  };

  const handleModalClose = () => {
    setErrorMsg(null);
    setConfirmedAppointment(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in">
      <div 
        className="w-full max-w-lg bg-white rounded-[16px] border border-[#e5e7eb] shadow-2xl overflow-hidden transition-all"
        role="dialog"
        aria-modal="true"
        aria-labelledby="booking-modal-title"
      >
        {/* Header */}
        <div className="p-5 sm:p-6 border-b border-[#e5e7eb] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 id="booking-modal-title" className="text-base sm:text-lg font-bold text-[#111111]">
              {confirmedAppointment ? "Booking Confirmed" : "Confirm Clinical Consultation"}
            </h3>
            <Badge variant="verified" size="sm">
              HL7 FHIR R4
            </Badge>
          </div>
          <button
            type="button"
            onClick={handleModalClose}
            aria-label="Close booking modal"
            className="h-8 w-8 rounded-full border border-[#e5e7eb] text-[#6b7280] hover:text-[#111111] hover:bg-[#f5f5f5] flex items-center justify-center transition-all cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 sm:p-6 space-y-5 max-h-[80vh] overflow-y-auto">
          {confirmedAppointment ? (
            /* ========================================================================
               CONFIRMED APPOINTMENT SCREEN
               ======================================================================== */
            <div className="space-y-6 text-center animate-fade-in">
              <div className="h-14 w-14 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#059669] flex items-center justify-center mx-auto shadow-sm">
                <CheckCircle2 className="h-8 w-8" />
              </div>

              <div>
                <h4 className="text-xl font-bold text-[#111111]">
                  Consultation Successfully Scheduled!
                </h4>
                <p className="text-xs sm:text-sm text-[#6b7280] mt-1">
                  Your clinical encounter is secured and indexed into your ABDM Health Locker.
                </p>
              </div>

              {/* Consultation Details Card */}
              <div className="rounded-[12px] bg-[#f8f9fa] border border-[#e5e7eb] p-4 text-left space-y-3 text-xs sm:text-sm">
                <div className="flex items-center justify-between pb-2 border-b border-[#e5e7eb]">
                  <span className="text-[#6b7280]">Clinician</span>
                  <span className="font-semibold text-[#111111]">{doctorName} ({specialty})</span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-[#e5e7eb]">
                  <span className="text-[#6b7280]">Scheduled Time</span>
                  <span className="font-semibold text-[#111111]">{formattedStart}</span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-[#e5e7eb]">
                  <span className="text-[#6b7280]">Encounter Class</span>
                  <span className="font-semibold text-[#111111]">
                    {slot.is_teleconsult ? "Virtual Telehealth (VR)" : "Ambulatory Clinic (AMB)"}
                  </span>
                </div>
                <div className="flex items-center justify-between pt-1">
                  <span className="text-[#6b7280]">ABDM CareContext</span>
                  <button
                    type="button"
                    onClick={handleCopyCareContext}
                    className="font-mono font-bold text-[#059669] flex items-center gap-1 hover:underline cursor-pointer"
                  >
                    <span>{careContextRef}</span>
                    <Copy className="h-3 w-3" />
                    {copiedAbdm && <span className="text-[10px] text-[#059669]">Copied</span>}
                  </button>
                </div>
              </div>

              {/* Quick Action Links */}
              <div className="pt-2 flex flex-col sm:flex-row gap-2.5">
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleModalClose}
                  className="w-full"
                >
                  Done & Close
                </Button>
                <Button
                  variant="secondary"
                  size="md"
                  onClick={() => alert(`Exporting signed FHIR R4 Bundle for CareContext ${careContextRef}...`)}
                  className="w-full"
                >
                  <Download className="h-4 w-4 mr-1 text-[#6b7280]" />
                  Download FHIR Bundle
                </Button>
              </div>
            </div>
          ) : (
            /* ========================================================================
               INTAKE FORM SCREEN
               ======================================================================== */
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Active 10-Minute Hold Countdown Banner */}
              {activeHold && (
                <SlotHoldCountdown
                  heldUntil={activeHold.held_until}
                  onRelease={onHoldRelease}
                />
              )}

              {/* Selected Slot Summary Card */}
              <div className="p-3.5 rounded-[10px] bg-[#f8f9fa] border border-[#e5e7eb] flex items-center justify-between">
                <div>
                  <div className="text-xs font-semibold text-[#6b7280]">
                    {specialty} • {doctorName}
                  </div>
                  <div className="text-sm font-bold text-[#111111] mt-0.5">
                    {formattedStart}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-[#6b7280]">Fee</div>
                  <div className="text-sm font-bold text-[#111111]">₹{consultationFee}</div>
                </div>
              </div>

              {/* Patient ABHA Information */}
              <div className="p-3 rounded-[8px] border border-[#e5e7eb] bg-white flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-[#6b7280]" />
                  <div>
                    <span className="font-semibold text-[#111111]">
                      {user?.fullName || "Arun Patel"}
                    </span>
                    <span className="text-[#6b7280] block text-[11px]">
                      ABHA: {user?.abhaId || "91-8472-1092-4821"}
                    </span>
                  </div>
                </div>
                <Badge variant="abdm" size="sm">
                  ABDM Linked
                </Badge>
              </div>

              {/* Encounter Type Selector */}
              <div>
                <label className="block text-xs font-semibold text-[#111111] mb-1.5">
                  Consultation Type
                </label>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    { id: "routine_checkup", label: "Routine Checkup" },
                    { id: "follow_up", label: "Follow-Up Visit" },
                    { id: "teleconsultation", label: "Virtual Teleconsult" },
                    { id: "emergency", label: "Urgent Consultation" },
                  ].map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setAppointmentType(t.id as AppointmentType)}
                      className={`p-2.5 rounded-[8px] border text-left font-medium transition-all cursor-pointer ${
                        appointmentType === t.id
                          ? "bg-[#111111] text-white border-[#111111]"
                          : "bg-white text-[#374151] border-[#e5e7eb] hover:bg-[#f5f5f5]"
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Reason / Chief Clinical Complaint */}
              <div>
                <label className="block text-xs font-semibold text-[#111111] mb-1.5">
                  Chief Clinical Complaint <span className="text-[#ef4444]">*</span>
                </label>
                <textarea
                  required
                  rows={2}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. Recurrent chest tightness, shortness of breath on climbing stairs..."
                  className="w-full p-3 rounded-[8px] border border-[#e5e7eb] text-xs sm:text-sm text-[#111111] placeholder-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#111111] transition-all"
                />
              </div>

              {/* Optional Intake Notes */}
              <div>
                <label className="block text-xs font-semibold text-[#111111] mb-1.5">
                  Additional Notes or Ongoing Medications (Optional)
                </label>
                <textarea
                  rows={2}
                  value={clinicalNotes}
                  onChange={(e) => setClinicalNotes(e.target.value)}
                  placeholder="e.g. Taking Atorvastatin 20mg and Telmisartan 40mg..."
                  className="w-full p-3 rounded-[8px] border border-[#e5e7eb] text-xs sm:text-sm text-[#111111] placeholder-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#111111] transition-all"
                />
              </div>

              {/* Error Message Alert */}
              {errorMsg && (
                <div className="p-3 rounded-[8px] bg-[#fef2f2] border border-[#fecaca] text-[#991b1b] text-xs flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 text-[#ef4444]" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-2 flex items-center justify-end gap-3 border-t border-[#e5e7eb]">
                <Button
                  type="button"
                  variant="ghost"
                  size="md"
                  onClick={handleModalClose}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  isLoading={isSubmitting}
                >
                  Confirm & Book Appointment
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
