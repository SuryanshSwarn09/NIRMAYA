"use client";

/**
 * Clinician Consultation Queue Component (Day 36 Milestone 08-01).
 * 
 * Provides real-time appointment queue management with status tabs (Today's Queue, Waiting,
 * In Consultation, Completed), encounter type filters (Teleconsultation vs In-Clinic),
 * search capabilities, and encounter lifecycle transitions.
 * Conforms to the Cal.com design system tokens (white canvas, subtle borders, high contrast).
 */
import React, { useState, useMemo } from "react";
import { 
  Calendar, 
  Clock, 
  Search, 
  Video, 
  User, 
  CheckCircle2, 
  AlertCircle, 
  Play, 
  Check, 
  Filter, 
  PhoneCall, 
  ShieldCheck, 
  Activity,
  ArrowRight,
  MoreVertical,
  Stethoscope,
  Sparkles
} from "lucide-react";

export interface QueueAppointment {
  id: string;
  patientId: string;
  patientName: string;
  patientAge?: number;
  patientGender?: string;
  patientAbha: string;
  patientPhone?: string;
  scheduledTime: string;
  scheduledDate: string;
  appointmentType: "teleconsultation" | "routine_checkup" | "follow_up" | "emergency";
  status: "scheduled" | "confirmed" | "in_progress" | "completed" | "cancelled";
  reason: string;
  priority?: "routine" | "urgent" | "high";
  vitalsSummary?: {
    bp?: string;
    hr?: string;
    spo2?: string;
  };
}

interface ClinicianConsultationQueueProps {
  doctorId?: string;
  selectedAppointmentId?: string;
  onSelectAppointment: (appointment: QueueAppointment) => void;
  onStartConsultation?: (appointment: QueueAppointment) => void;
  onLaunchTelemedicine?: (appointment: QueueAppointment) => void;
  onCompleteConsultation?: (appointmentId: string) => void;
}

export const INITIAL_MOCK_QUEUE: QueueAppointment[] = [
  {
    id: "appt-telemed-encounter-01",
    patientId: "pat-arun-patel-01",
    patientName: "Arun Patel",
    patientAge: 36,
    patientGender: "Male",
    patientAbha: "91-8472-1092-4821",
    patientPhone: "+91 98765 43210",
    scheduledTime: "10:15 AM",
    scheduledDate: "Today",
    appointmentType: "teleconsultation",
    status: "in_progress",
    priority: "routine",
    reason: "Quarterly cardiovascular review and blood pressure evaluation",
    vitalsSummary: {
      bp: "138/88 mmHg",
      hr: "74 bpm",
      spo2: "98%",
    },
  },
  {
    id: "appt-clinic-priya-02",
    patientId: "pat-priya-nair-02",
    patientName: "Priya Nair",
    patientAge: 42,
    patientGender: "Female",
    patientAbha: "91-9988-7766-5544",
    patientPhone: "+91 98123 45678",
    scheduledTime: "11:00 AM",
    scheduledDate: "Today",
    appointmentType: "teleconsultation",
    status: "confirmed",
    priority: "urgent",
    reason: "Episodes of exertional palpitations and morning dizziness",
    vitalsSummary: {
      bp: "126/82 mmHg",
      hr: "88 bpm",
      spo2: "99%",
    },
  },
  {
    id: "appt-clinic-vikram-03",
    patientId: "pat-vikram-malhotra-01",
    patientName: "Vikram Malhotra",
    patientAge: 38,
    patientGender: "Male",
    patientAbha: "91-3322-1144-5566",
    patientPhone: "+91 98222 33445",
    scheduledTime: "11:45 AM",
    scheduledDate: "Today",
    appointmentType: "routine_checkup",
    status: "confirmed",
    priority: "routine",
    reason: "Routine dyslipidemia screening and dietary adherence check",
    vitalsSummary: {
      bp: "122/78 mmHg",
      hr: "68 bpm",
      spo2: "99%",
    },
  },
  {
    id: "appt-clinic-anita-04",
    patientId: "pat-anita-deshmukh-04",
    patientName: "Anita Deshmukh",
    patientAge: 51,
    patientGender: "Female",
    patientAbha: "91-6677-8899-0011",
    patientPhone: "+91 98333 44556",
    scheduledTime: "09:30 AM",
    scheduledDate: "Today",
    appointmentType: "follow_up",
    status: "completed",
    priority: "routine",
    reason: "Post-angioplasty 3-month exercise tolerance evaluation",
    vitalsSummary: {
      bp: "118/76 mmHg",
      hr: "70 bpm",
      spo2: "99%",
    },
  },
];

export function ClinicianConsultationQueue({
  doctorId,
  selectedAppointmentId = "appt-telemed-encounter-01",
  onSelectAppointment,
  onStartConsultation,
  onLaunchTelemedicine,
  onCompleteConsultation,
}: ClinicianConsultationQueueProps) {
  const [appointments, setAppointments] = useState<QueueAppointment[]>(INITIAL_MOCK_QUEUE);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "waiting" | "in_progress" | "completed">("all");
  const [typeFilter, setTypeFilter] = useState<"all" | "teleconsultation" | "in_clinic">("all");

  // Summary Metrics
  const metrics = useMemo(() => {
    const total = appointments.length;
    const waiting = appointments.filter((a) => a.status === "confirmed" || a.status === "scheduled").length;
    const inProgress = appointments.filter((a) => a.status === "in_progress").length;
    const completed = appointments.filter((a) => a.status === "completed").length;
    return { total, waiting, inProgress, completed };
  }, [appointments]);

  // Filtered appointments
  const filteredAppointments = useMemo(() => {
    return appointments.filter((appt) => {
      // Search text filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesName = appt.patientName.toLowerCase().includes(query);
        const matchesAbha = appt.patientAbha.replace(/-/g, "").includes(query.replace(/-/g, ""));
        const matchesReason = appt.reason.toLowerCase().includes(query);
        if (!matchesName && !matchesAbha && !matchesReason) return false;
      }

      // Status filter
      if (statusFilter === "waiting") {
        if (appt.status !== "confirmed" && appt.status !== "scheduled") return false;
      } else if (statusFilter === "in_progress") {
        if (appt.status !== "in_progress") return false;
      } else if (statusFilter === "completed") {
        if (appt.status !== "completed") return false;
      }

      // Type filter
      if (typeFilter === "teleconsultation") {
        if (appt.appointmentType !== "teleconsultation") return false;
      } else if (typeFilter === "in_clinic") {
        if (appt.appointmentType === "teleconsultation") return false;
      }

      return true;
    });
  }, [appointments, searchQuery, statusFilter, typeFilter]);

  const handleStartConsult = (appt: QueueAppointment, e: React.MouseEvent) => {
    e.stopPropagation();
    setAppointments((prev) =>
      prev.map((a) => (a.id === appt.id ? { ...a, status: "in_progress" } : a))
    );
    if (onStartConsultation) {
      onStartConsultation({ ...appt, status: "in_progress" });
    }
    onSelectAppointment({ ...appt, status: "in_progress" });
  };

  const handleCompleteConsult = (apptId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setAppointments((prev) =>
      prev.map((a) => (a.id === apptId ? { ...a, status: "completed" } : a))
    );
    if (onCompleteConsultation) {
      onCompleteConsultation(apptId);
    }
  };

  return (
    <div className="space-y-4">
      {/* 1. Header & Metric Counter Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <button
          type="button"
          onClick={() => setStatusFilter("all")}
          className={`p-3 rounded-lg border text-left transition-all cursor-pointer ${
            statusFilter === "all"
              ? "bg-[#111111] text-white border-[#111111] shadow-xs"
              : "bg-white text-[#111827] border-[#E5E7EB] hover:bg-[#F9FAFB]"
          }`}
        >
          <div className="text-[11px] font-medium uppercase tracking-wider opacity-80">
            Today's Queue
          </div>
          <div className="text-xl font-bold mt-0.5">{metrics.total}</div>
        </button>

        <button
          type="button"
          onClick={() => setStatusFilter("waiting")}
          className={`p-3 rounded-lg border text-left transition-all cursor-pointer ${
            statusFilter === "waiting"
              ? "bg-[#111111] text-white border-[#111111] shadow-xs"
              : "bg-white text-[#111827] border-[#E5E7EB] hover:bg-[#F9FAFB]"
          }`}
        >
          <div className="text-[11px] font-medium uppercase tracking-wider text-[#D97706]">
            Waiting Room
          </div>
          <div className="text-xl font-bold text-[#D97706] mt-0.5">{metrics.waiting}</div>
        </button>

        <button
          type="button"
          onClick={() => setStatusFilter("in_progress")}
          className={`p-3 rounded-lg border text-left transition-all cursor-pointer ${
            statusFilter === "in_progress"
              ? "bg-[#111111] text-white border-[#111111] shadow-xs"
              : "bg-white text-[#111827] border-[#E5E7EB] hover:bg-[#F9FAFB]"
          }`}
        >
          <div className="text-[11px] font-medium uppercase tracking-wider text-[#059669]">
            In Consultation
          </div>
          <div className="text-xl font-bold text-[#059669] mt-0.5">{metrics.inProgress}</div>
        </button>

        <button
          type="button"
          onClick={() => setStatusFilter("completed")}
          className={`p-3 rounded-lg border text-left transition-all cursor-pointer ${
            statusFilter === "completed"
              ? "bg-[#111111] text-white border-[#111111] shadow-xs"
              : "bg-white text-[#111827] border-[#E5E7EB] hover:bg-[#F9FAFB]"
          }`}
        >
          <div className="text-[11px] font-medium uppercase tracking-wider text-[#6B7280]">
            Completed
          </div>
          <div className="text-xl font-bold text-[#6B7280] mt-0.5">{metrics.completed}</div>
        </button>
      </div>

      {/* 2. Search & Type Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#9CA3AF]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search patient name, ABHA ID (e.g. 91-8472...), reason..."
            className="w-full pl-9 pr-3 py-2 bg-white border border-[#E5E7EB] rounded-lg text-xs text-[#111827] placeholder-[#9CA3AF] focus:outline-none focus:ring-1 focus:ring-[#111111]"
          />
        </div>

        <div className="flex items-center gap-1.5 self-end sm:self-auto">
          <span className="text-[11px] text-[#6B7280] font-medium">Type:</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as typeof typeFilter)}
            className="bg-white border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#111827] focus:outline-none focus:ring-1 focus:ring-[#111111]"
          >
            <option value="all">All Encounters</option>
            <option value="teleconsultation">Teleconsultation (Video)</option>
            <option value="in_clinic">In-Clinic Visit</option>
          </select>
        </div>
      </div>

      {/* 3. Appointment Queue List */}
      <div className="space-y-2.5">
        {filteredAppointments.length === 0 ? (
          <div className="text-center py-10 bg-[#F9FAFB] rounded-xl border border-dashed border-[#E5E7EB]">
            <Calendar className="h-8 w-8 text-[#9CA3AF] mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-[#111827]">No Appointments Found</h4>
            <p className="text-xs text-[#6B7280] mt-0.5">
              No patients match the active queue filter criteria.
            </p>
          </div>
        ) : (
          filteredAppointments.map((appt) => {
            const isSelected = appt.id === selectedAppointmentId;
            const isTelemed = appt.appointmentType === "teleconsultation";

            return (
              <div
                key={appt.id}
                onClick={() => onSelectAppointment(appt)}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? "bg-[#FFFFFF] border-[#111111] ring-1 ring-[#111111] shadow-xs"
                    : "bg-white border-[#E5E7EB] hover:border-[#D1D5DB] hover:bg-[#FAFAFA]"
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  
                  {/* Left: Patient Demographic & Timing */}
                  <div className="flex items-start gap-3">
                    <div
                      className={`h-10 w-10 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
                        isSelected
                          ? "bg-[#111111] text-white"
                          : "bg-[#F3F4F6] text-[#4B5563]"
                      }`}
                    >
                      {appt.patientName
                        .split(" ")
                        .map((n) => n[0])
                        .join("")}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-sm text-[#111827]">
                          {appt.patientName}
                        </span>
                        {appt.patientAge && appt.patientGender && (
                          <span className="text-xs text-[#6B7280]">
                            • {appt.patientAge}y, {appt.patientGender}
                          </span>
                        )}
                        <span className="inline-flex items-center gap-1 font-mono text-[11px] text-[#059669] bg-[#ECFDF5] px-2 py-0.5 rounded-md border border-[#A7F3D0]">
                          <ShieldCheck className="h-3 w-3" />
                          {appt.patientAbha}
                        </span>

                        {appt.priority === "urgent" && (
                          <span className="text-[10px] uppercase font-bold text-[#DC2626] bg-[#FEF2F2] px-1.5 py-0.5 rounded border border-[#FECACA]">
                            Urgent
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-[#4B5563] line-clamp-1">
                        <span className="font-medium text-[#111827]">Reason:</span> {appt.reason}
                      </p>

                      {/* Vitals snapshot strip */}
                      {appt.vitalsSummary && (
                        <div className="flex items-center gap-2 pt-0.5 text-[11px] text-[#6B7280]">
                          <span className="font-medium text-[#111827]">Vitals:</span>
                          {appt.vitalsSummary.bp && <span>BP {appt.vitalsSummary.bp}</span>}
                          {appt.vitalsSummary.hr && <span>• HR {appt.vitalsSummary.hr}</span>}
                          {appt.vitalsSummary.spo2 && <span>• SpO2 {appt.vitalsSummary.spo2}</span>}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right: Timing & Action Triggers */}
                  <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-[#F3F4F6]">
                    <div className="text-left sm:text-right">
                      <div className="flex items-center sm:justify-end gap-1 text-xs font-semibold text-[#111827]">
                        <Clock className="h-3.5 w-3.5 text-[#6B7280]" />
                        {appt.scheduledTime}
                      </div>
                      <div className="flex items-center sm:justify-end gap-1 mt-0.5">
                        {isTelemed ? (
                          <span className="inline-flex items-center gap-1 text-[11px] text-[#2563EB] bg-[#EFF6FF] px-1.5 py-0.5 rounded">
                            <Video className="h-3 w-3" />
                            Teleconsult
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] text-[#4B5563] bg-[#F3F4F6] px-1.5 py-0.5 rounded">
                            <Stethoscope className="h-3 w-3" />
                            In-Clinic
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center gap-1.5">
                      {appt.status === "in_progress" ? (
                        <>
                          <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#059669] bg-[#ECFDF5] px-2.5 py-1.5 rounded-lg border border-[#A7F3D0]">
                            <span className="h-2 w-2 rounded-full bg-[#059669] animate-pulse" />
                            In Progress
                          </span>
                          {isTelemed && onLaunchTelemedicine && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                onLaunchTelemedicine(appt);
                              }}
                              className="px-2.5 py-1.5 rounded-lg border border-[#2563EB] bg-[#2563EB] text-white text-xs font-semibold hover:bg-[#1D4ED8] transition-all flex items-center gap-1 cursor-pointer"
                            >
                              <Video className="h-3.5 w-3.5" />
                              Join Video
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={(e) => handleCompleteConsult(appt.id, e)}
                            className="px-2.5 py-1.5 rounded-lg border border-[#E5E7EB] bg-white text-xs font-semibold text-[#374151] hover:bg-[#F3F4F6] transition-all cursor-pointer"
                          >
                            Finish
                          </button>
                        </>
                      ) : appt.status === "completed" ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#6B7280] bg-[#F3F4F6] px-2.5 py-1.5 rounded-lg border border-[#E5E7EB]">
                          <CheckCircle2 className="h-3.5 w-3.5 text-[#059669]" />
                          Completed
                        </span>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={(e) => handleStartConsult(appt, e)}
                            className="px-3 py-1.5 rounded-lg border border-[#111111] bg-[#111111] text-white text-xs font-semibold hover:bg-black transition-all flex items-center gap-1.5 cursor-pointer shadow-xs"
                          >
                            <Play className="h-3 w-3 fill-current" />
                            Call Patient
                          </button>
                          {isTelemed && onLaunchTelemedicine && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                onLaunchTelemedicine(appt);
                              }}
                              title="Preview WebRTC Device Diagnostics"
                              className="p-1.5 rounded-lg border border-[#E5E7EB] bg-white text-[#4B5563] hover:text-[#111111] hover:bg-[#F9FAFB] transition-all cursor-pointer"
                            >
                              <Video className="h-4 w-4" />
                            </button>
                          )}
                        </>
                      )}
                    </div>

                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
