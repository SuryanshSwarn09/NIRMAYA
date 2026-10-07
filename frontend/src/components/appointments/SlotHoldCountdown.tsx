"use client";

import React, { useEffect, useState } from "react";
import { Clock, AlertCircle, X } from "lucide-react";
import { Button } from "@/components/ui";

export interface SlotHoldCountdownProps {
  heldUntil: string | Date;
  onExpire?: () => void;
  onRelease?: () => void;
  isReleasing?: boolean;
  className?: string;
}

/**
 * Temporary slot hold countdown banner.
 * Reassures patient during intake that their chosen slot is safely locked against concurrent checkout.
 */
export function SlotHoldCountdown({
  heldUntil,
  onExpire,
  onRelease,
  isReleasing = false,
  className = "",
}: SlotHoldCountdownProps) {
  const [secondsRemaining, setSecondsRemaining] = useState<number>(() => {
    const target = new Date(heldUntil).getTime();
    const now = Date.now();
    return Math.max(0, Math.floor((target - now) / 1000));
  });

  useEffect(() => {
    const target = new Date(heldUntil).getTime();

    const interval = setInterval(() => {
      const now = Date.now();
      const remaining = Math.max(0, Math.floor((target - now) / 1000));
      setSecondsRemaining(remaining);

      if (remaining <= 0) {
        clearInterval(interval);
        if (onExpire) {
          onExpire();
        }
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [heldUntil, onExpire]);

  const minutes = Math.floor(secondsRemaining / 60);
  const seconds = secondsRemaining % 60;
  const formattedTime = `${String(minutes).padStart(2, "0")}:${String(
    seconds
  ).padStart(2, "0")}`;

  const isUrgent = secondsRemaining < 120; // Under 2 minutes

  if (secondsRemaining <= 0) {
    return (
      <div
        className={`p-3.5 rounded-[8px] border border-[#fecaca] bg-[#fef2f2] text-[#991b1b] flex items-center justify-between text-xs sm:text-sm animate-fade-in ${className}`}
      >
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-[#ef4444]" />
          <span>
            Slot reservation has expired. Please select a fresh slot to proceed.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={`Slot hold reservation: ${formattedTime} remaining`}
      className={`p-3.5 rounded-[8px] border transition-all duration-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs sm:text-sm ${
        isUrgent
          ? "border-[#fed7aa] bg-[#fff7ed] text-[#9a3412]"
          : "border-[#e5e7eb] bg-[#f8f9fa] text-[#111111]"
      } ${className}`}
    >
      <div className="flex items-center gap-2.5">
        <div
          className={`h-7 w-7 rounded-full flex items-center justify-center shrink-0 ${
            isUrgent ? "bg-[#fed7aa] text-[#ea580c]" : "bg-white text-[#111111] shadow-xs"
          }`}
        >
          <Clock className="h-4 w-4" />
        </div>
        <div>
          <span className="font-semibold text-xs sm:text-sm">
            Slot Held:{" "}
            <span className="font-mono font-bold tracking-tight">
              {formattedTime}
            </span>
          </span>
          <p className="text-[11px] sm:text-xs text-[#6b7280] mt-0.5">
            Reserved exclusively for you to prevent concurrent checkout conflicts.
          </p>
        </div>
      </div>

      {onRelease && (
        <div className="flex items-center justify-end shrink-0">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onRelease}
            isLoading={isReleasing}
            aria-label="Release held consultation slot"
            className="text-xs text-[#6b7280] hover:text-[#111111] hover:bg-black/[0.04]"
          >
            <X className="h-3.5 w-3.5 mr-1" />
            Release Hold
          </Button>
        </div>
      )}
    </div>
  );
}
