"use client";

import React, { useState, useEffect, useRef } from "react";
import { Button, Badge } from "@/components/ui";
import { 
  X, 
  Printer, 
  Download, 
  Copy, 
  Check, 
  FileCode, 
  CreditCard, 
  FileImage, 
  Sparkles,
  ShieldCheck,
  User as UserIcon,
  Heart,
  MapPin,
  Phone
} from "lucide-react";
import { generateQrSvgString, encodeAbdmQrPayload } from "@/lib/qr";

export interface AbhaCardExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  cardData: {
    abhaId: string;
    abhaAddress: string;
    patientName: string;
    gender: string;
    dob: string;
    mobile: string;
    bloodGroup: string;
    stateNode: string;
    distName?: string;
    emergencyContact?: string;
    organDonor?: boolean;
    qrPayload?: string;
    rawResponse?: any;
  };
}

export function AbhaCardExportModal({
  isOpen,
  onClose,
  cardData,
}: AbhaCardExportModalProps) {
  const [activeTab, setActiveTab] = useState<"wallet" | "svg" | "json">("wallet");
  const [copiedJson, setCopiedJson] = useState(false);
  const [qrSvg, setQrSvg] = useState<string>("");
  const printRef = useRef<HTMLDivElement>(null);

  const {
    abhaId,
    abhaAddress,
    patientName,
    gender,
    dob,
    mobile,
    bloodGroup,
    stateNode,
    distName = "South Delhi",
    emergencyContact = "Pooja Patel (+91 98*** **991)",
    organDonor = true,
    qrPayload,
    rawResponse,
  } = cardData;

  // Resolve QR payload string
  const activeQrPayload = React.useMemo(() => {
    if (qrPayload) return qrPayload;
    return encodeAbdmQrPayload({
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
    });
  }, [qrPayload, abhaId, abhaAddress, patientName, gender, dob, stateNode, distName, mobile, bloodGroup]);

  useEffect(() => {
    generateQrSvgString(activeQrPayload, {
      width: 140,
      margin: 0,
      color: { dark: "#111111", light: "#ffffff" },
    }).then(setQrSvg).catch(console.error);
  }, [activeQrPayload]);

  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadSvg = () => {
    const blob = new Blob([qrSvg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `ABHA_QR_${abhaId.replace(/[^0-9]/g, "")}.svg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const jsonContent = JSON.stringify(
    rawResponse || {
      schema: "https://abdm.gov.in/schemas/abha-card/v1",
      abha_id: abhaId,
      abha_address: abhaAddress,
      cardholder: {
        name: patientName,
        gender,
        dob,
        mobile_masked: mobile,
        blood_group: bloodGroup,
      },
      jurisdiction: {
        state: stateNode,
        district: distName,
      },
      emergency: {
        contact: emergencyContact,
        organ_donor: organDonor,
      },
      cryptographic_qr: {
        payload: activeQrPayload,
        algorithm: "HMAC-SHA256",
        issued_at: new Date().toISOString(),
      },
    },
    null,
    2
  );

  const handleCopyJson = () => {
    navigator.clipboard?.writeText(jsonContent);
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const handleDownloadJson = () => {
    const blob = new Blob([jsonContent], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `ABHA_Claims_${abhaId.replace(/[^0-9]/g, "")}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in overflow-y-auto">
      {/* Hidden Print-Specific Stylesheet */}
      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          body * {
            visibility: hidden;
          }
          #nirmaya-printable-abha-card, #nirmaya-printable-abha-card * {
            visibility: visible;
          }
          #nirmaya-printable-abha-card {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            margin: 0;
            padding: 20px;
            background: white !important;
          }
          .no-print {
            display: none !important;
          }
        }
      `}} />

      <div className="bg-white rounded-[16px] border border-[#e5e7eb] shadow-2xl max-w-2xl w-full p-6 space-y-5 animate-scale-in my-8">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
          <div>
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-[#111111]" />
              <h3 className="text-lg font-bold text-[#111111] tracking-tight">
                Export & Print ABHA ID Card
              </h3>
            </div>
            <p className="text-xs text-[#6b7280] mt-0.5">
              Official Ayushman Bharat Digital Mission (ABDM) CR80 wallet card & cryptographic certificate.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[#9ca3af] hover:text-[#111111] transition-colors p-1"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Export Mode Pill Switcher */}
        <div className="flex rounded-[8px] bg-[#f3f4f6] p-1 border border-[#e5e7eb]">
          <button
            type="button"
            onClick={() => setActiveTab("wallet")}
            className={`flex-1 py-1.5 px-3 rounded-[6px] text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              activeTab === "wallet"
                ? "bg-white text-[#111111] shadow-xs"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            <Printer className="h-3.5 w-3.5" />
            <span>ID-1 Wallet Sheet (Print)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("svg")}
            className={`flex-1 py-1.5 px-3 rounded-[6px] text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              activeTab === "svg"
                ? "bg-white text-[#111111] shadow-xs"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            <FileImage className="h-3.5 w-3.5" />
            <span>Vector SVG Asset</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("json")}
            className={`flex-1 py-1.5 px-3 rounded-[6px] text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              activeTab === "json"
                ? "bg-white text-[#111111] shadow-xs"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            <FileCode className="h-3.5 w-3.5" />
            <span>ABDM JSON Certificate</span>
          </button>
        </div>

        {/* ====================================================================
            TAB 1: ID-1 Wallet Print Sheet (85.6mm × 54mm)
            ==================================================================== */}
        {activeTab === "wallet" && (
          <div className="space-y-4">
            <div className="p-3 bg-[#f8f9fa] rounded-[8px] border border-[#e5e7eb] flex items-center justify-between text-xs text-[#4b5563]">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-[#10b981]" />
                <span>Standard CR80 dimensions (85.60 × 53.98 mm) with fold line for wallet lamination.</span>
              </div>
              <Badge variant="emerald" size="sm">Print Ready</Badge>
            </div>

            {/* Printable Container with Front & Back side-by-side */}
            <div 
              ref={printRef}
              id="nirmaya-printable-abha-card"
              className="p-4 bg-[#f3f4f6] rounded-[12px] border border-dashed border-[#d1d5db] space-y-4"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* FRONT FACE */}
                <div className="bg-white rounded-[12px] border border-[#e5e7eb] shadow-xs overflow-hidden flex flex-col justify-between">
                  <div className="h-1.5 w-full flex">
                    <div className="h-full w-1/3 bg-[#FF9933]" />
                    <div className="h-full w-1/3 bg-white" />
                    <div className="h-full w-1/3 bg-[#138808]" />
                  </div>
                  <div className="p-3 border-b border-[#f3f4f6] flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <div className="h-5 w-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[9px] font-bold">🏛️</div>
                      <span className="text-[10px] font-bold text-[#111111] tracking-tight">ABHA ID Card • Govt of India</span>
                    </div>
                    <span className="text-[9px] text-[#059669] font-bold">ABDM</span>
                  </div>
                  <div className="p-3 grid grid-cols-12 gap-2 items-center">
                    <div className="col-span-3 flex flex-col items-center">
                      <div className="h-14 w-14 rounded-[8px] bg-gray-100 border border-gray-200 flex items-center justify-center">
                        <UserIcon className="h-7 w-7 text-gray-400" />
                      </div>
                    </div>
                    <div className="col-span-5 text-[11px] leading-tight space-y-1">
                      <div className="font-bold text-[#111111] text-xs">{patientName}</div>
                      <div className="text-[10px] text-[#3b82f6] font-mono truncate">{abhaAddress}</div>
                      <div className="text-[10px] text-[#6b7280]">{gender} • {dob}</div>
                    </div>
                    <div className="col-span-4 flex justify-center">
                      <div 
                        className="h-14 w-14 [&>svg]:w-full [&>svg]:h-full"
                        dangerouslySetInnerHTML={{ __html: qrSvg }}
                      />
                    </div>
                  </div>
                  <div className="px-3 py-1.5 bg-[#f8f9fa] border-t border-[#e5e7eb] flex items-center justify-between text-[11px]">
                    <span className="text-[9px] uppercase font-semibold text-[#6b7280]">ABHA Number</span>
                    <span className="font-mono font-bold text-[#111111]">{abhaId}</span>
                  </div>
                </div>

                {/* BACK FACE */}
                <div className="bg-white rounded-[12px] border border-[#e5e7eb] shadow-xs overflow-hidden flex flex-col justify-between">
                  <div className="h-1.5 w-full flex">
                    <div className="h-full w-1/3 bg-[#FF9933]" />
                    <div className="h-full w-1/3 bg-white" />
                    <div className="h-full w-1/3 bg-[#138808]" />
                  </div>
                  <div className="p-3 border-b border-[#f3f4f6] flex items-center justify-between">
                    <span className="text-[10px] font-bold text-[#111111] uppercase tracking-wide">Emergency & Node Profile</span>
                    <span className="text-[9px] font-mono text-[#6b7280]">ID: {abhaId.slice(-4)}</span>
                  </div>
                  <div className="p-3 grid grid-cols-2 gap-2 text-[10px]">
                    <div className="p-1.5 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb]">
                      <span className="text-[#6b7280] block text-[9px]">Blood Group</span>
                      <strong className="text-[#b91c1c]">{bloodGroup}</strong>
                    </div>
                    <div className="p-1.5 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb]">
                      <span className="text-[#6b7280] block text-[9px]">Organ Donor</span>
                      <strong className="text-[#059669]">{organDonor ? "Registered" : "None"}</strong>
                    </div>
                    <div className="col-span-2 p-1.5 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb]">
                      <span className="text-[#6b7280] block text-[9px]">Emergency Contact</span>
                      <strong className="text-[#111111] truncate block">{emergencyContact}</strong>
                    </div>
                  </div>
                  <div className="px-3 py-1.5 bg-[#f8f9fa] border-t border-[#e5e7eb] flex items-center justify-between text-[9px] text-[#6b7280]">
                    <span>Toll Free: 14477</span>
                    <span>abdm.gov.in</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onClose}
              >
                Close
              </Button>
              <Button
                type="button"
                variant="primary"
                size="sm"
                onClick={handlePrint}
                className="flex items-center gap-1.5"
              >
                <Printer className="h-3.5 w-3.5" />
                <span>Print Wallet Card</span>
              </Button>
            </div>
          </div>
        )}

        {/* ====================================================================
            TAB 2: Vector SVG Asset
            ==================================================================== */}
        {activeTab === "svg" && (
          <div className="space-y-4">
            <div className="p-4 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] flex flex-col items-center justify-center space-y-3">
              <div 
                className="h-36 w-36 bg-white p-3 rounded-[12px] border border-[#e5e7eb] shadow-sm flex items-center justify-center [&>svg]:w-full [&>svg]:h-full"
                dangerouslySetInnerHTML={{ __html: qrSvg }}
              />
              <div className="text-center">
                <span className="text-xs font-bold text-[#111111]">Scalable Vector Graphics (SVG)</span>
                <p className="text-[11px] text-[#6b7280]">
                  Lossless vector XML encoding with embedded HMAC-SHA256 signature payload.
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onClose}
              >
                Close
              </Button>
              <Button
                type="button"
                variant="primary"
                size="sm"
                onClick={handleDownloadSvg}
                className="flex items-center gap-1.5"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download Vector SVG</span>
              </Button>
            </div>
          </div>
        )}

        {/* ====================================================================
            TAB 3: ABDM Claims Certificate (JSON)
            ==================================================================== */}
        {activeTab === "json" && (
          <div className="space-y-4">
            <div className="relative">
              <pre className="p-4 rounded-[10px] bg-[#111111] text-[#e5e7eb] text-xs font-mono max-h-64 overflow-y-auto leading-relaxed">
                {jsonContent}
              </pre>
              <button
                type="button"
                onClick={handleCopyJson}
                className="absolute top-3 right-3 px-2 py-1 rounded-[6px] bg-[#242424] text-white text-[11px] font-medium hover:bg-[#333333] transition-colors flex items-center gap-1 border border-white/10"
              >
                {copiedJson ? (
                  <>
                    <Check className="h-3 w-3 text-[#10b981]" />
                    <span className="text-[#10b981]">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3 text-gray-300" />
                    <span>Copy JSON</span>
                  </>
                )}
              </button>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onClose}
              >
                Close
              </Button>
              <Button
                type="button"
                variant="primary"
                size="sm"
                onClick={handleDownloadJson}
                className="flex items-center gap-1.5"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download Certificate JSON</span>
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
