"use client";

import React, { useState } from "react";
import { 
  ShieldCheck, 
  QrCode, 
  Copy, 
  Check, 
  Download, 
  User, 
  Calendar, 
  Droplet, 
  Phone,
  Maximize2,
  Volume2
} from "lucide-react";
import { Card, Button, Badge } from "@/components/ui";
import { useAccessibility } from "@/context/AccessibilityContext";
import { DpiQrCheckInModal } from "./DpiQrCheckInModal";

export interface DpiHealthIdTileProps {
  patientId: string;
  patientName: string;
  abhaNumber: string;
  abhaAddress: string;
  gender: string;
  dateOfBirth: string;
  bloodGroup?: string;
  mobile?: string;
  isDependent?: boolean;
  relationship?: string | null;
}

export function DpiHealthIdTile({
  patientId,
  patientName,
  abhaNumber,
  abhaAddress,
  gender,
  dateOfBirth,
  bloodGroup = "O+",
  mobile = "+91 ******4821",
  isDependent = false,
  relationship,
}: DpiHealthIdTileProps) {
  const { t, locale, speakText } = useAccessibility();
  const [isQrModalOpen, setIsQrModalOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleSpeakCard = () => {
    const cardSummary = locale === "hi"
      ? `डिजिटल आभा स्वास्थ्य कार्ड। नाम: ${patientName}। आभा संख्या: ${abhaNumber.split("-").join(" ")}। पता: ${abhaAddress}। अस्पताल ओपीडी में दिखाने के लिए क्यूआर कोड बटन दबाएं।`
      : `Digital ABHA Health Card. Name: ${patientName}. ABHA Number: ${abhaNumber}. Address: ${abhaAddress}. Press QR code button to display at hospital counter.`;
    speakText(cardSummary);
  };

  const handleCopyAbha = () => {
    navigator.clipboard.writeText(abhaNumber);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      <Card variant="mockup" className="p-0 overflow-hidden border border-[#e5e7eb] bg-white shadow-xs">
        {/* Tricolor Micro-Strip Header */}
        <div className="h-1 w-full flex">
          <div className="h-full w-1/3 bg-[#ff9933]" />
          <div className="h-full w-1/3 bg-white" />
          <div className="h-full w-1/3 bg-[#138808]" />
        </div>

        {/* Tile Title Strip */}
        <div className="px-5 py-3 bg-[#f9fafb] border-b border-[#e5e7eb] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#10b981]" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#111827]">
              {t("citizen.tile1.title", "Tile 1: My Health ID (ABHA Card)")}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleSpeakCard}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-white border border-[#e5e7eb] hover:bg-[#f3f4f6] text-[#374151] cursor-pointer"
              title="Listen to ABHA Card information"
            >
              <Volume2 className="h-3 w-3 text-[#059669]" />
              <span>{t("nav.listen", "Listen")}</span>
            </button>
            {isDependent && relationship && (
              <Badge variant="warning" size="sm">
                {relationship}
              </Badge>
            )}
            <Badge variant="emerald" size="sm">
              ABDM Verified
            </Badge>
          </div>
        </div>

        {/* ABHA Card Surface */}
        <div className="p-5 sm:p-6 space-y-5">
          <div className="rounded-[12px] border border-[#e5e7eb] bg-[#fdfdfd] p-4 sm:p-5 relative overflow-hidden shadow-xs">
            {/* Soft decorative background seal */}
            <div className="absolute -right-6 -bottom-6 w-32 h-32 rounded-full bg-[#f3f4f6]/60 pointer-events-none" />

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              {/* Profile Details */}
              <div className="space-y-3">
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-[#6b7280]">
                    National Health Authority of India
                  </div>
                  <div className="text-lg sm:text-xl font-bold text-[#111827] mt-0.5">
                    {patientName}
                  </div>
                </div>

                {/* 14-Digit ABHA Number Display with Copy Action */}
                <div className="space-y-1">
                  <div className="text-[11px] text-[#6b7280]">14-Digit ABHA Number</div>
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-[6px] bg-white border border-[#e5e7eb] shadow-2xs font-mono text-sm sm:text-base font-bold text-[#111827]">
                    <span>{abhaNumber}</span>
                    <button
                      type="button"
                      onClick={handleCopyAbha}
                      className="p-1 rounded hover:bg-[#f3f4f6] text-[#6b7280] hover:text-[#111827] transition-colors cursor-pointer"
                      title="Copy ABHA Number"
                    >
                      {copied ? <Check className="h-3.5 w-3.5 text-[#10b981]" /> : <Copy className="h-3.5 w-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Demographic Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1 text-xs text-[#374151]">
                  <div>
                    <span className="text-[11px] text-[#6b7280] block">PHR Address:</span>
                    <span className="font-semibold text-[#111827]">{abhaAddress}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-[#6b7280] block">Gender:</span>
                    <span className="font-semibold capitalize text-[#111827]">{gender}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-[#6b7280] block">DOB:</span>
                    <span className="font-semibold text-[#111827]">{dateOfBirth}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-[#6b7280] block">Blood Group:</span>
                    <span className="font-semibold text-[#111827]">{bloodGroup}</span>
                  </div>
                </div>
              </div>

              {/* QR Code Action Box */}
              <div 
                onClick={() => setIsQrModalOpen(true)}
                className="w-full sm:w-auto p-3 rounded-[10px] bg-white border border-[#e5e7eb] hover:border-[#111827] hover:shadow-xs transition-all flex sm:flex-col items-center justify-between sm:justify-center gap-3 cursor-pointer group shrink-0"
              >
                <div className="w-20 h-20 bg-[#111827] rounded-[6px] flex items-center justify-center text-white relative group-hover:scale-102 transition-transform">
                  <QrCode className="h-14 w-14 text-white" />
                  <div className="absolute inset-0 bg-black/20 rounded-[6px] opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                    <Maximize2 className="h-5 w-5 text-white" />
                  </div>
                </div>
                <span className="text-[11px] font-semibold text-[#111827] text-center group-hover:underline">
                  Tap to Enlarge QR
                </span>
              </div>
            </div>
          </div>

          {/* Primary Big Touch Target Action */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
            <Button
              type="button"
              variant="primary"
              size="lg"
              className="flex-1 justify-center h-12 text-sm font-semibold shadow-xs"
              onClick={() => setIsQrModalOpen(true)}
            >
              <QrCode className="h-4 w-4 mr-2" />
              <span>{t("citizen.tile1.action", "Show at Hospital Counter / OPD Registration")}</span>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="lg"
              className="justify-center h-12 text-xs bg-white hover:bg-[#f9fafb]"
              onClick={() => alert(`ABHA Card for ${patientName} is digitally stamped under Ayushman Bharat Digital Mission.`)}
            >
              <Download className="h-4 w-4 mr-1.5" />
              <span>Download ABHA Card (PDF)</span>
            </Button>
          </div>
        </div>
      </Card>

      {/* OPD Fast-Track Check-In Modal */}
      <DpiQrCheckInModal
        isOpen={isQrModalOpen}
        onClose={() => setIsQrModalOpen(false)}
        patientName={patientName}
        abhaNumber={abhaNumber}
        abhaAddress={abhaAddress}
        patientId={patientId}
      />
    </>
  );
}
