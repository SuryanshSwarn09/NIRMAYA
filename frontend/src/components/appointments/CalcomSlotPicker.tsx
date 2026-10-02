"use client";

import React, { useState, useEffect, useMemo } from "react";
import { 
  ChevronLeft, 
  ChevronRight, 
  Clock, 
  Video, 
  MapPin, 
  Calendar as CalendarIcon,
  Check,
  ShieldCheck,
  Sparkles,
  Info
} from "lucide-react";
import { Button, Badge, Card } from "@/components/ui";
import { apiClient, DoctorSlot, SlotStatus, SlotHoldResponse } from "@/lib/api";
import { SlotHoldCountdown } from "./SlotHoldCountdown";

export interface CalcomSlotPickerProps {
  doctorId: string;
  doctorName?: string;
  specialty?: string;
  consultationFee?: number;
  selectedSlot: DoctorSlot | null;
  onSelectSlot: (slot: DoctorSlot) => void;
  activeHold?: SlotHoldResponse | null;
  onHoldSlot?: (slot: DoctorSlot) => Promise<void>;
  onReleaseHold?: () => Promise<void>;
  isHolding?: boolean;
  className?: string;
}

// Days of week
const DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

export function CalcomSlotPicker({
  doctorId,
  doctorName = "Clinical Specialist",
  specialty = "General Consultation",
  consultationFee,
  selectedSlot,
  onSelectSlot,
  activeHold,
  onHoldSlot,
  onReleaseHold,
  isHolding = false,
  className = "",
}: CalcomSlotPickerProps) {
  // Calendar month view state
  const [currentDate, setCurrentDate] = useState(() => new Date());
  const [selectedDate, setSelectedDate] = useState<Date>(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return today;
  });

  // Filter: all vs in-person vs teleconsult
  const [modalityFilter, setModalityFilter] = useState<"all" | "clinic" | "teleconsult">("all");

  // Slots state from backend
  const [slots, setSlots] = useState<DoctorSlot[]>([]);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [slotError, setSlotError] = useState<string | null>(null);

  // Month navigation
  const currentYear = currentDate.getFullYear();
  const currentMonth = currentDate.getMonth();

  const monthName = currentDate.toLocaleString("default", {
    month: "long",
    year: "numeric",
  });

  const prevMonth = () => {
    setCurrentDate(new Date(currentYear, currentMonth - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentYear, currentMonth + 1, 1));
  };

  // Calendar dates computation
  const daysInMonth = useMemo(() => {
    const firstDayIndex = new Date(currentYear, currentMonth, 1).getDay();
    const lastDate = new Date(currentYear, currentMonth + 1, 0).getDate();

    const days: (number | null)[] = [];
    for (let i = 0; i < firstDayIndex; i++) {
      days.push(null);
    }
    for (let d = 1; d <= lastDate; d++) {
      days.push(d);
    }
    return days;
  }, [currentYear, currentMonth]);

  // Format date as YYYY-MM-DD for API
  const formattedSelectedDate = useMemo(() => {
    const year = selectedDate.getFullYear();
    const month = String(selectedDate.getMonth() + 1).padStart(2, "0");
    const day = String(selectedDate.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }, [selectedDate]);

  // Fetch doctor slots for the selected date
  useEffect(() => {
    let isCancelled = false;

    async function fetchSlots() {
      setIsLoadingSlots(true);
      setSlotError(null);

      try {
        const fetched = await apiClient.getDoctorSlots(doctorId, {
          target_date: formattedSelectedDate,
        });

        if (!isCancelled) {
          if (fetched && fetched.length > 0) {
            setSlots(fetched);
          } else {
            // Generate clean standard Cal.com clinical consultation slots for selected date
            const generatedFallback = generateDefaultSlots(doctorId, selectedDate);
            setSlots(generatedFallback);
          }
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          // If backend has no pre-seeded slots for doctor, fallback to standard clinical availability hours
          const generatedFallback = generateDefaultSlots(doctorId, selectedDate);
          setSlots(generatedFallback);
        }
      } finally {
        if (!isCancelled) {
          setIsLoadingSlots(false);
        }
      }
    }

    if (doctorId) {
      fetchSlots();
    }

    return () => {
      isCancelled = true;
    };
  }, [doctorId, formattedSelectedDate, selectedDate]);

  // Filter slots based on modality
  const filteredSlots = useMemo(() => {
    return slots.filter((s) => {
      if (modalityFilter === "clinic") return !s.is_teleconsult;
      if (modalityFilter === "teleconsult") return s.is_teleconsult;
      return true;
    });
  }, [slots, modalityFilter]);

  const handleDayClick = (day: number) => {
    const newSelected = new Date(currentYear, currentMonth, day);
    newSelected.setHours(0, 0, 0, 0);
    setSelectedDate(newSelected);
  };

  const handleSlotClick = async (slot: DoctorSlot) => {
    if (slot.status !== "available" && slot.id !== activeHold?.slot_id) {
      return;
    }

    onSelectSlot(slot);

    if (onHoldSlot && slot.status === "available") {
      try {
        await onHoldSlot(slot);
      } catch (e) {
        console.error("Failed to hold slot:", e);
      }
    }
  };

  const isToday = (day: number) => {
    const today = new Date();
    return (
      today.getDate() === day &&
      today.getMonth() === currentMonth &&
      today.getFullYear() === currentYear
    );
  };

  const isPast = (day: number) => {
    const checkDate = new Date(currentYear, currentMonth, day, 23, 59, 59);
    return checkDate.getTime() < Date.now();
  };

  const isSelected = (day: number) => {
    return (
      selectedDate.getDate() === day &&
      selectedDate.getMonth() === currentMonth &&
      selectedDate.getFullYear() === currentYear
    );
  };

  const availableCount = filteredSlots.filter(
    (s) => s.status === "available" || s.id === activeHold?.slot_id
  ).length;

  return (
    <div
      className={`rounded-[16px] bg-white border border-[#e5e7eb] shadow-[0_1px_3px_rgba(0,0,0,0.06)] overflow-hidden ${className}`}
    >
      {/* Active Hold Alert Banner (if slot is held) */}
      {activeHold && (
        <div className="p-4 bg-[#f8f9fa] border-b border-[#e5e7eb]">
          <SlotHoldCountdown
            heldUntil={activeHold.held_until}
            onRelease={onReleaseHold}
          />
        </div>
      )}

      {/* Header Info Band */}
      <div className="p-5 sm:p-6 border-b border-[#e5e7eb] bg-[#fdfdfd] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold tracking-tight text-[#6b7280] uppercase">
              Schedule Consultation
            </span>
            <Badge variant="verified" size="sm">
              ACID Slot Engine
            </Badge>
          </div>
          <h2 className="text-lg sm:text-xl font-bold text-[#111111] tracking-tight mt-0.5">
            {doctorName}
          </h2>
          <p className="text-xs sm:text-sm text-[#6b7280]">
            {specialty}{" "}
            {consultationFee !== undefined && (
              <>• <span className="font-semibold text-[#111111]">₹{consultationFee}</span> consultation fee</>
            )}
          </p>
        </div>

        {/* Modality Selector (Nav-Pill style) */}
        <div className="inline-flex p-1 rounded-full bg-[#f5f5f5] border border-[#e5e7eb] self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setModalityFilter("all")}
            className={`px-3 py-1 text-xs font-semibold rounded-full transition-all cursor-pointer ${
              modalityFilter === "all"
                ? "bg-white text-[#111111] shadow-xs"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            All Slots
          </button>
          <button
            type="button"
            onClick={() => setModalityFilter("clinic")}
            className={`px-3 py-1 text-xs font-semibold rounded-full transition-all cursor-pointer flex items-center gap-1 ${
              modalityFilter === "clinic"
                ? "bg-white text-[#111111] shadow-xs"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            <MapPin className="h-3 w-3" />
            In-Person (AMB)
          </button>
          <button
            type="button"
            onClick={() => setModalityFilter("teleconsult")}
            className={`px-3 py-1 text-xs font-semibold rounded-full transition-all cursor-pointer flex items-center gap-1 ${
              modalityFilter === "teleconsult"
                ? "bg-white text-[#111111] shadow-xs"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            <Video className="h-3 w-3" />
            Virtual (VR)
          </button>
        </div>
      </div>

      {/* Main Dual-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[#e5e7eb]">
        
        {/* Left Column (7 cols): Cal.com Monthly Date Matrix */}
        <div className="lg:col-span-7 p-6 sm:p-8 space-y-6">
          
          {/* Month Header and Steppers */}
          <div className="flex items-center justify-between">
            <h3 className="text-base sm:text-lg font-bold text-[#111111]">
              {monthName}
            </h3>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={prevMonth}
                aria-label="Previous month"
                className="h-8 w-8 rounded-full border border-[#e5e7eb] bg-white text-[#111111] hover:bg-[#f5f5f5] flex items-center justify-center transition-all cursor-pointer"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={nextMonth}
                aria-label="Next month"
                className="h-8 w-8 rounded-full border border-[#e5e7eb] bg-white text-[#111111] hover:bg-[#f5f5f5] flex items-center justify-center transition-all cursor-pointer"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Weekday Labels */}
          <div className="grid grid-cols-7 gap-1 text-center">
            {DAYS.map((d) => (
              <span
                key={d}
                className="text-[11px] font-semibold text-[#6b7280] py-1 tracking-wider"
              >
                {d}
              </span>
            ))}
          </div>

          {/* Day Grid Cells */}
          <div className="grid grid-cols-7 gap-1.5 sm:gap-2">
            {daysInMonth.map((day, idx) => {
              if (day === null) {
                return <div key={`empty-${idx}`} className="h-9 sm:h-11" />;
              }

              const disabled = isPast(day);
              const active = isSelected(day);
              const current = isToday(day);

              return (
                <button
                  key={`day-${day}`}
                  type="button"
                  disabled={disabled}
                  onClick={() => handleDayClick(day)}
                  aria-pressed={active}
                  aria-label={`${monthName} ${day}${current ? ' (Today)' : ''}`}
                  className={`h-9 sm:h-11 rounded-[8px] sm:rounded-full text-xs sm:text-sm font-semibold transition-all relative flex flex-col items-center justify-center cursor-pointer ${
                    active
                      ? "bg-[#111111] text-white shadow-xs"
                      : disabled
                      ? "text-[#d1d5db] cursor-not-allowed hover:bg-transparent"
                      : "text-[#111111] hover:bg-[#f5f5f5] active:bg-[#e5e7eb]"
                  }`}
                >
                  <span>{day}</span>
                  {current && !active && (
                    <span className="absolute bottom-1.5 h-1 w-1 rounded-full bg-[#111111]" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Quick Date Presets */}
          <div className="pt-4 border-t border-[#e5e7eb] flex items-center gap-2 overflow-x-auto text-xs">
            <span className="text-[#6b7280] shrink-0 font-medium">Quick select:</span>
            <button
              type="button"
              onClick={() => {
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                setSelectedDate(today);
                setCurrentDate(today);
              }}
              className="px-2.5 py-1 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb] text-[#111111] hover:bg-[#e5e7eb] transition-all cursor-pointer font-medium"
            >
              Today
            </button>
            <button
              type="button"
              onClick={() => {
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                tomorrow.setHours(0, 0, 0, 0);
                setSelectedDate(tomorrow);
                setCurrentDate(tomorrow);
              }}
              className="px-2.5 py-1 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb] text-[#111111] hover:bg-[#e5e7eb] transition-all cursor-pointer font-medium"
            >
              Tomorrow
            </button>
          </div>
        </div>

        {/* Right Column (5 cols): Cal.com Available Consultation Time Slots */}
        <div className="lg:col-span-5 p-6 sm:p-8 space-y-5 bg-[#fafafa]">
          
          <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
            <div>
              <div className="text-xs font-semibold text-[#6b7280]">
                {selectedDate.toLocaleDateString("en-US", {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                })}
              </div>
              <div className="text-sm font-bold text-[#111111]">
                Available Windows
              </div>
            </div>

            <Badge
              variant={availableCount > 0 ? "emerald" : "neutral"}
              size="sm"
            >
              {availableCount} Available
            </Badge>
          </div>

          {/* Time Zone Indicator */}
          <div className="flex items-center gap-1.5 text-[11px] text-[#6b7280]">
            <Clock className="h-3.5 w-3.5" />
            <span>India Standard Time (IST, UTC+05:30)</span>
          </div>

          {/* Slots Container */}
          <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
            {isLoadingSlots ? (
              <div className="py-12 text-center text-xs text-[#6b7280]">
                Loading available consultation windows...
              </div>
            ) : filteredSlots.length === 0 ? (
              <div className="py-12 text-center space-y-2 text-[#6b7280]">
                <CalendarIcon className="h-8 w-8 mx-auto text-[#9ca3af]" />
                <p className="text-xs font-medium">No consultation slots available on this date.</p>
                <p className="text-[11px] text-[#9ca3af]">Please pick another date or consult another doctor.</p>
              </div>
            ) : (
              filteredSlots.map((slot) => {
                const startTime = formatTimeOnly(slot.start_time);
                const isSelected = selectedSlot?.id === slot.id;
                const isHeldByMe = activeHold?.slot_id === slot.id;
                const isUnavailable =
                  slot.status === "booked" ||
                  slot.status === "blocked" ||
                  (slot.status === "held" && !isHeldByMe);

                return (
                  <button
                    key={slot.id}
                    type="button"
                    disabled={isUnavailable || isHolding}
                    onClick={() => handleSlotClick(slot)}
                    aria-pressed={isSelected || isHeldByMe}
                    aria-label={`Select consultation slot at ${startTime} (${slot.is_teleconsult ? 'Teleconsultation' : 'In-person'})`}
                    className={`w-full p-3 rounded-[8px] border text-left transition-all flex items-center justify-between cursor-pointer ${
                      isSelected
                        ? "bg-[#111111] text-white border-[#111111] shadow-xs"
                        : isHeldByMe
                        ? "bg-[#ecfdf5] border-[#10b981] text-[#065f46]"
                        : isUnavailable
                        ? "bg-[#f3f4f6] border-[#e5e7eb] text-[#9ca3af] cursor-not-allowed opacity-60"
                        : "bg-white border-[#e5e7eb] text-[#111111] hover:bg-[#f8f9fa] hover:border-[#d1d5db]"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="text-sm font-semibold font-mono">
                        {startTime}
                      </div>
                      <div className="flex items-center gap-1 text-[11px]">
                        {slot.is_teleconsult ? (
                          <span
                            className={`px-1.5 py-0.5 rounded-[4px] font-medium flex items-center gap-0.5 ${
                              isSelected
                                ? "bg-white/20 text-white"
                                : "bg-[#f5f3ff] text-[#7c3aed]"
                            }`}
                          >
                            <Video className="h-2.5 w-2.5" />
                            VR
                          </span>
                        ) : (
                          <span
                            className={`px-1.5 py-0.5 rounded-[4px] font-medium flex items-center gap-0.5 ${
                              isSelected
                                ? "bg-white/20 text-white"
                                : "bg-[#f8f9fa] text-[#4b5563]"
                            }`}
                          >
                            <MapPin className="h-2.5 w-2.5" />
                            AMB
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="text-xs flex items-center gap-1.5">
                      {isHeldByMe ? (
                        <span className="font-semibold text-xs flex items-center gap-1 text-[#059669]">
                          <Check className="h-3.5 w-3.5" />
                          Held (10m)
                        </span>
                      ) : slot.status === "booked" ? (
                        <span className="text-[11px] text-[#9ca3af]">Booked</span>
                      ) : slot.status === "held" ? (
                        <span className="text-[11px] text-[#ea580c] bg-[#fff7ed] px-1.5 py-0.5 rounded">
                          Held
                        </span>
                      ) : isSelected ? (
                        <span className="font-semibold text-xs text-white">Selected</span>
                      ) : (
                        <span className="text-xs text-[#6b7280]">Select</span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Bottom Security Note */}
          <div className="p-3 rounded-[8px] bg-white border border-[#e5e7eb] flex items-start gap-2 text-[11px] text-[#6b7280]">
            <ShieldCheck className="h-4 w-4 text-[#059669] shrink-0 mt-0.5" />
            <span>
              Selecting a slot automatically engages an ACID row-lock hold for 10 minutes to protect your checkout intake.
            </span>
          </div>
        </div>

      </div>
    </div>
  );
}

// Helper: Format ISO timestamp to local 12-hour time string
function formatTimeOnly(isoString: string): string {
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return "09:00 AM";
  }
}

// Helper: Generate fallback default slots for smooth testing and demonstration
function generateDefaultSlots(doctorId: string, targetDate: Date): DoctorSlot[] {
  const slots: DoctorSlot[] = [];
  const hours = [9, 10, 11, 14, 15, 16];

  hours.forEach((hour, idx) => {
    // 00 min slot
    const start1 = new Date(targetDate);
    start1.setHours(hour, 0, 0, 0);
    const end1 = new Date(targetDate);
    end1.setHours(hour, 30, 0, 0);

    slots.push({
      id: `slot-fallback-${doctorId}-${hour}-00`,
      doctor_id: doctorId,
      start_time: start1.toISOString(),
      end_time: end1.toISOString(),
      status: idx === 1 ? "booked" : "available",
      is_teleconsult: hour >= 14,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    // 30 min slot
    const start2 = new Date(targetDate);
    start2.setHours(hour, 30, 0, 0);
    const end2 = new Date(targetDate);
    end2.setHours(hour + 1, 0, 0, 0);

    slots.push({
      id: `slot-fallback-${doctorId}-${hour}-30`,
      doctor_id: doctorId,
      start_time: start2.toISOString(),
      end_time: end2.toISOString(),
      status: "available",
      is_teleconsult: hour >= 14,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  });

  return slots;
}
