"use client";

import React, { useState, useEffect } from "react";
import { Badge, Button } from "@/components/ui";
import { 
  QrCode, 
  RotateCcw, 
  Download, 
  Copy, 
  Check, 
  ShieldCheck, 
  Printer, 
  Heart, 
  Phone, 
  MapPin, 
  User as UserIcon,
  Sparkles,
  ExternalLink,
  Landmark
} from "lucide-react";
import { generateQrSvgString, encodeAbdmQrPayload, AbdmQrClaims } from "@/lib/qr";

export interface DigitalAbhaCardProps {
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
  className?: string;
}

export function DigitalAbhaCard({
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
  className = "",
}: DigitalAbhaCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);
  const [copiedId, setCopiedId] = useState(false);
  const [qrSvg, setQrSvg] = useState<string>("");
  const [qrLoading, setQrLoading] = useState(true);

  // Compute or format QR payload string
  const activePayloadString = React.useMemo(() => {
    if (qrPayload) return qrPayload;
    const claims: AbdmQrClaims = {
      hidn: abhaId.replace(/[^0-9]/g, ""),
      hid: abhaAddress,
      name: patientName,
      gender: gender.toUpperCase().startsWith("M") ? "M" : gender.toUpperCase().startsWith("F") ? "F" : "O",
      dob: dob,
      state_name: stateNode,
      dist_name: distName,
      mobile: mobile,
      blood_group: bloodGroup,
      issue_date: "2026-10-23T00:00:00Z",
    };
    return encodeAbdmQrPayload(claims);
  }, [qrPayload, abhaId, abhaAddress, patientName, gender, dob, stateNode, distName, mobile, bloodGroup]);

  // Generate pure vector QR SVG
  useEffect(() => {
    let cancelled = false;
    setQrLoading(true);

    generateQrSvgString(activePayloadString, {
      width: 130,
      margin: 0,
      color: {
        dark: "#111111",
        light: "#ffffff",
      },
      errorCorrectionLevel: "M",
    })
      .then((svg) => {
        if (!cancelled) {
          setQrSvg(svg);
          setQrLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          console.error("Failed to render QR SVG", err);
          setQrLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activePayloadString]);

  const handleCopyAbhaId = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard?.writeText(abhaId);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Perspective Container for 3D Flip */}
      <div 
        className="w-full max-w-[480px] mx-auto select-none"
        style={{ perspective: "1200px" }}
      >
        <div
          onClick={() => setIsFlipped(!isFlipped)}
          className="relative w-full cursor-pointer transition-transform duration-700 ease-out"
          style={{
            transformStyle: "preserve-3d",
            transform: isFlipped ? "rotateY(180deg)" : "rotateY(0deg)",
            minHeight: "270px",
          }}
          title="Click to flip card"
        >
          {/* ====================================================================
              FRONT FACE (Ayushman Bharat Health Account ID)
              ==================================================================== */}
          <div
            className="w-full rounded-[16px] bg-white border border-[#e5e7eb] shadow-md overflow-hidden flex flex-col justify-between"
            style={{
              backfaceVisibility: "hidden",
              WebkitBackfaceVisibility: "hidden",
            }}
          >
            {/* National Tricolor Top Banner */}
            <div className="h-2 w-full flex">
              <div className="h-full w-1/3 bg-[#FF9933]" />
              <div className="h-full w-1/3 bg-white" />
              <div className="h-full w-1/3 bg-[#138808]" />
            </div>

            {/* Header: NHA Emblem & Title */}
            <div className="px-5 pt-3.5 pb-2.5 flex items-center justify-between border-b border-[#f3f4f6] bg-[#fafafa]">
              <div className="flex items-center gap-2.5">
                {/* Government Emblem Symbol */}
                <div className="h-8 w-8 rounded-[8px] bg-[#111111] text-white flex items-center justify-center font-bold text-xs shadow-xs shrink-0 border border-[#262626]">
                  <Landmark className="h-4 w-4 text-white" />
                </div>
                <div>
                  <div className="text-[10px] uppercase font-bold tracking-wider text-[#6b7280]">
                    National Health Authority • Govt. of India
                  </div>
                  <div className="text-xs font-bold text-[#111111] tracking-tight">
                    Ayushman Bharat Health Account (ABHA)
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1.5">
                <Badge variant="emerald" size="sm" className="text-[10px] px-2 py-0.5 font-semibold">
                  ABDM Verified
                </Badge>
              </div>
            </div>

            {/* Main Body: Photo/Avatar, Details & QR */}
            <div className="p-4 sm:p-5 grid grid-cols-12 gap-3.5 items-center">
              {/* Photo & Hologram */}
              <div className="col-span-3 flex flex-col items-center justify-center">
                <div className="relative h-20 w-20 rounded-[8px] bg-[#f3f4f6] border border-[#e5e7eb] overflow-hidden flex items-center justify-center shadow-inner">
                  <div className="h-full w-full flex flex-col items-center justify-center bg-[#f3f4f6] text-[#4b5563]">
                    <UserIcon className="h-10 w-10 text-[#9ca3af]" />
                  </div>
                  {/* Security Authenticity Seal */}
                  <div className="absolute bottom-1 right-1 h-5 w-5 rounded-[4px] bg-[#111111] border border-[#374151] flex items-center justify-center shadow-xs">
                    <ShieldCheck className="h-3 w-3 text-[#10b981]" />
                  </div>
                </div>
                <span className="text-[9px] font-semibold text-[#6b7280] mt-1 uppercase tracking-wider">
                  Photo ID
                </span>
              </div>

              {/* Patient Core Identity */}
              <div className="col-span-5 space-y-1">
                <div>
                  <span className="text-[10px] uppercase font-semibold text-[#898989] tracking-wider block">
                    Cardholder Name
                  </span>
                  <div className="text-sm sm:text-base font-bold text-[#111111] tracking-tight leading-tight">
                    {patientName}
                  </div>
                </div>

                <div>
                  <span className="text-[10px] uppercase font-semibold text-[#898989] tracking-wider block">
                    ABHA Address
                  </span>
                  <div className="text-xs font-semibold text-[#3b82f6] font-mono truncate">
                    {abhaAddress}
                  </div>
                </div>

                <div className="pt-1 flex flex-wrap gap-x-2 gap-y-0.5 text-[11px] text-[#4b5563]">
                  <span><strong>Gender:</strong> {gender}</span>
                  <span><strong>DOB:</strong> {dob}</span>
                </div>
              </div>

              {/* Vector QR Code */}
              <div className="col-span-4 flex flex-col items-center justify-center">
                <div className="relative p-1.5 rounded-[10px] bg-white border border-[#e5e7eb] shadow-xs flex items-center justify-center">
                  {qrLoading ? (
                    <div className="h-20 w-20 flex items-center justify-center text-[#9ca3af] animate-pulse">
                      <QrCode className="h-8 w-8" />
                    </div>
                  ) : (
                    <div 
                      className="h-20 w-20 flex items-center justify-center [&>svg]:w-full [&>svg]:h-full"
                      dangerouslySetInnerHTML={{ __html: qrSvg }}
                    />
                  )}
                </div>
                <span className="text-[9px] font-mono text-[#6b7280] mt-1 text-center">
                  Scan to Verify
                </span>
              </div>
            </div>

            {/* Bottom Number Bar: 14-Digit ABHA ID */}
            <div className="px-5 py-2.5 bg-[#f8f9fa] border-t border-[#e5e7eb] flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-semibold text-[#6b7280] tracking-wider block">
                  ABHA Number (14 Digits)
                </span>
                <span className="text-sm sm:text-base font-mono font-bold tracking-wider text-[#111111]">
                  {abhaId}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCopyAbhaId}
                  className="px-2.5 py-1 rounded-[6px] bg-white border border-[#e5e7eb] text-[11px] font-semibold text-[#374151] hover:bg-[#f3f4f6] flex items-center gap-1 transition-colors"
                >
                  {copiedId ? (
                    <>
                      <Check className="h-3 w-3 text-[#10b981]" />
                      <span className="text-[#10b981]">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3 text-[#6b7280]" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* ====================================================================
              BACK FACE (Medical Emergency, Jurisdiction & ABDM Security)
              ==================================================================== */}
          <div
            className="absolute inset-0 w-full h-full rounded-[16px] bg-[#ffffff] border border-[#e5e7eb] shadow-md overflow-hidden flex flex-col justify-between"
            style={{
              backfaceVisibility: "hidden",
              WebkitBackfaceVisibility: "hidden",
              transform: "rotateY(180deg)",
            }}
          >
            {/* National Tricolor Top Banner */}
            <div className="h-2 w-full flex">
              <div className="h-full w-1/3 bg-[#FF9933]" />
              <div className="h-full w-1/3 bg-white" />
              <div className="h-full w-1/3 bg-[#138808]" />
            </div>

            {/* Header: Emergency & Verification Notice */}
            <div className="px-5 pt-3 pb-2 flex items-center justify-between border-b border-[#f3f4f6] bg-[#fafafa]">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-[#10b981]" />
                <span className="text-xs font-bold text-[#111111] uppercase tracking-wide">
                  Emergency Medical Profile & Health Node
                </span>
              </div>
              <span className="text-[10px] font-mono text-[#6b7280]">
                SEC-ID: {abhaId.slice(-4)}
              </span>
            </div>

            {/* Back Face Body: Key Health Data */}
            <div className="p-4 sm:p-5 grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-0.5">
                <span className="text-[10px] uppercase font-semibold text-[#6b7280] tracking-wider block">
                  Blood Group
                </span>
                <span className="text-xs font-bold text-[#b91c1c] flex items-center gap-1">
                  <Heart className="h-3.5 w-3.5 fill-[#b91c1c] text-[#b91c1c]" />
                  {bloodGroup}
                </span>
              </div>

              <div className="p-2.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-0.5">
                <span className="text-[10px] uppercase font-semibold text-[#6b7280] tracking-wider block">
                  Organ Donor Status
                </span>
                <span className="text-xs font-bold text-[#059669] flex items-center gap-1">
                  {organDonor ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-[#059669]" />
                      <span>Registered Donor (NHO)</span>
                    </>
                  ) : (
                    <span>Not Registered</span>
                  )}
                </span>
              </div>

              <div className="p-2.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-0.5">
                <span className="text-[10px] uppercase font-semibold text-[#6b7280] tracking-wider block">
                  Jurisdiction / State Node
                </span>
                <span className="text-xs font-semibold text-[#111111] flex items-center gap-1 truncate">
                  <MapPin className="h-3 w-3 text-[#6b7280] shrink-0" />
                  {distName}, {stateNode}
                </span>
              </div>

              <div className="p-2.5 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-0.5">
                <span className="text-[10px] uppercase font-semibold text-[#6b7280] tracking-wider block">
                  Emergency Contact
                </span>
                <span className="text-xs font-semibold text-[#111111] flex items-center gap-1 truncate">
                  <Phone className="h-3 w-3 text-[#6b7280] shrink-0" />
                  {emergencyContact}
                </span>
              </div>
            </div>

            {/* ABDM Disclaimer & Simulated Barcode Strip */}
            <div className="px-5 py-2.5 bg-[#f8f9fa] border-t border-[#e5e7eb] space-y-2">
              <div className="flex items-center justify-between text-[10px] text-[#6b7280]">
                <span>ABDM Helpline: <strong>14477</strong> (Toll Free)</span>
                <span>Portal: <strong>abdm.gov.in</strong></span>
              </div>

              {/* Simulated High-Density Code-128 Barcode */}
              <div className="h-5 w-full bg-white border border-[#e5e7eb] rounded-[4px] px-2 flex items-center justify-between overflow-hidden">
                <div className="h-3.5 w-full flex items-center justify-between gap-[2px] opacity-75">
                  {Array.from({ length: 48 }).map((_, i) => (
                    <div
                      key={i}
                      className="h-full bg-[#111111]"
                      style={{
                        width: `${(i % 3) + 1}px`,
                        opacity: i % 5 === 0 ? 0.3 : 1,
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Card Action Pill Controls */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setIsFlipped(!isFlipped)}
          className="text-xs font-medium flex items-center gap-1.5"
        >
          <RotateCcw className="h-3.5 w-3.5 text-[#6b7280]" />
          <span>{isFlipped ? "Show Front Face" : "Flip to Back Face"}</span>
        </Button>

        {onOpenExport && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onOpenExport}
            className="text-xs font-medium flex items-center gap-1.5"
          >
            <Download className="h-3.5 w-3.5 text-[#6b7280]" />
            <span>Download & Print</span>
          </Button>
        )}

        {onOpenVerify && (
          <Button
            type="button"
            variant="primary"
            size="sm"
            onClick={onOpenVerify}
            className="text-xs font-medium flex items-center gap-1.5"
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Verify QR Code</span>
          </Button>
        )}
      </div>
    </div>
  );
}
