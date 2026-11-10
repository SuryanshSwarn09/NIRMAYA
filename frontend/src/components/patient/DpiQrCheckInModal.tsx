"use client";

import React, { useState, useEffect } from "react";
import { X, QrCode, CheckCircle2, ShieldCheck, Clock, Building2, Copy, Check } from "lucide-react";
import { Button, Badge } from "@/components/ui";

interface DpiQrCheckInModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientName: string;
  abhaNumber: string;
  abhaAddress: string;
  patientId: string;
}

export function DpiQrCheckInModal({
  isOpen,
  onClose,
  patientName,
  abhaNumber,
  abhaAddress,
  patientId,
}: DpiQrCheckInModalProps) {
  const [copied, setCopied] = useState(false);
  const [secondsRemaining, setSecondsRemaining] = useState(3600); // 60 min TTL

  useEffect(() => {
    if (!isOpen) return;
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [isOpen]);

  if (!isOpen) return null;

  const handleCopyAbha = () => {
    navigator.clipboard.writeText(abhaNumber);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const minutes = Math.floor(secondsRemaining / 60);
  const seconds = secondsRemaining % 60;
  const timeFormatted = `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs">
      <div className="relative w-full max-w-sm rounded-[14px] bg-white border border-[#e5e7eb] shadow-xl overflow-hidden p-6 space-y-5 animate-in fade-in zoom-in-95 duration-150">
        
        {/* Tricolor Strip */}
        <div className="h-1 w-full absolute top-0 left-0 flex">
          <div className="h-full w-1/3 bg-[#ff9933]" />
          <div className="h-full w-1/3 bg-white" />
          <div className="h-full w-1/3 bg-[#138808]" />
        </div>

        {/* Modal Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-full hover:bg-[#f3f4f6] text-[#6b7280] hover:text-[#111827] transition-colors cursor-pointer"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="text-center space-y-1 pt-2">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-xs font-semibold text-[#065f46]">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>ABDM OPD Fast-Track Check-In</span>
          </div>
          <h3 className="text-lg font-bold text-[#111827]">Scan at Hospital Counter</h3>
          <p className="text-xs text-[#6b7280]">
            Point this high-contrast screen directly at the hospital counter camera or barcode scanner.
          </p>
        </div>

        {/* High-Contrast Maximum-Legibility QR Container */}
        <div className="bg-white p-5 rounded-[12px] border-2 border-[#111827] shadow-inner text-center space-y-3">
          <div className="relative mx-auto w-48 h-48 bg-[#111827] rounded-[8px] flex items-center justify-center text-white">
            {/* High-Contrast Stylized QR Representation */}
            <div className="w-40 h-40 bg-white p-2.5 rounded-[6px] grid grid-cols-6 grid-rows-6 gap-1">
              {/* Corner Position Tags */}
              <div className="col-span-2 row-span-2 bg-[#111827] rounded-xs" />
              <div className="col-span-2 bg-[#111827] rounded-xs" />
              <div className="col-span-2 row-span-2 bg-[#111827] rounded-xs" />
              <div className="col-span-2 bg-[#111827] rounded-xs" />
              <div className="bg-[#111827] rounded-xs" />
              <div className="bg-[#111827] rounded-xs" />
              <div className="col-span-2 row-span-2 bg-[#111827] rounded-xs" />
              <div className="col-span-2 bg-[#111827] rounded-xs" />
              <div className="col-span-2 bg-[#111827] rounded-xs" />
              <div className="bg-[#111827] rounded-xs" />
              <div className="col-span-2 bg-[#111827] rounded-xs" />
              <div className="bg-[#111827] rounded-xs" />
            </div>
            {/* Center ABDM Crest Pill */}
            <div className="absolute inset-0 m-auto w-10 h-10 rounded-full bg-white border-2 border-[#111827] flex items-center justify-center text-[10px] font-bold text-[#111827]">
              ABDM
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm font-bold text-[#111827]">{patientName}</div>
            <div className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-[#111827] bg-[#f9fafb] px-2.5 py-1 rounded border border-[#e5e7eb]">
              <span>{abhaNumber}</span>
              <button
                type="button"
                onClick={handleCopyAbha}
                className="hover:text-black cursor-pointer text-[#6b7280]"
              >
                {copied ? <Check className="h-3 w-3 text-[#10b981]" /> : <Copy className="h-3 w-3" />}
              </button>
            </div>
            <div className="text-[11px] text-[#6b7280]">{abhaAddress}</div>
          </div>
        </div>

        {/* Security & Timer Footer */}
        <div className="flex items-center justify-between text-xs text-[#6b7280] pt-2 border-t border-[#f3f4f6]">
          <span className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5 text-[#111827]" />
            <span>Expires in: <strong className="font-mono text-[#111827]">{timeFormatted}</strong></span>
          </span>
          <Badge variant="verified" size="sm">Single-Encounter</Badge>
        </div>

        {/* Dismiss Button */}
        <Button
          type="button"
          variant="primary"
          className="w-full justify-center"
          onClick={onClose}
        >
          <span>Done / Back to Vault</span>
        </Button>
      </div>
    </div>
  );
}
