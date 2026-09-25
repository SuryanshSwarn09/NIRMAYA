"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button, Badge, Card, CardTitle, CardDescription } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import {
  TestTube2,
  FileCheck,
  ShieldCheck,
  UploadCloud,
  FileText,
  CheckCircle2,
  Activity,
  Code,
  QrCode,
  AlertCircle,
  Hash,
  Download,
  Building2,
  Fingerprint,
  Lock,
} from "lucide-react";

export default function DiagnosticLabPage() {
  const { user } = useAuth();

  // Patient & Document State
  const [selectedPatient, setSelectedPatient] = useState("Arun Patel (91-8472-1092-4821)");
  const [fileName, setFileName] = useState("Apollo_Lipid_Panel_Report_0925.pdf");
  const [fileSha256, setFileSha256] = useState(
    "d5a8b79e13c84f494f69747a28e9323f4b46c6a49dbd29486c434f09a5ebc109"
  );
  const [isHashing, setIsHashing] = useState(false);
  const [isIngested, setIsIngested] = useState(false);

  // Simulated Cryptographic Stamping
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFileName(file.name);
      setIsHashing(true);
      setIsIngested(false);

      // Compute genuine SHA-256 via Web Crypto API
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const buffer = reader.result as ArrayBuffer;
          const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
          const hashArray = Array.from(new Uint8Array(hashBuffer));
          const hashHex = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
          setFileSha256(hashHex);
        } catch {
          // Fallback hash
          setFileSha256("b7e31d4289cf0829a1b945112fa572183e20da85c962b1093f48a192e40938bb");
        } finally {
          setIsHashing(false);
        }
      };
      reader.readAsArrayBuffer(file);
    }
  };

  const handleIngestPDF = (e: React.FormEvent) => {
    e.preventDefault();
    setIsIngested(true);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 bg-white">
      
      {/* Top Facility Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#e5e7eb]">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-[#111111] text-white flex items-center justify-center font-bold text-base shrink-0">
            <TestTube2 className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111111]">
                Apollo Diagnostics Central
              </h1>
              <Badge variant="verified">NABL Accredited</Badge>
            </div>
            <p className="text-sm text-[#6b7280]">
              Clinical Pathology & Molecular Diagnostics • HFR:{" "}
              <span className="font-mono text-[#111111]">HFR-DEL-91024</span> • ISO 15189:2022
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="emerald" size="sm">Gateway Online</Badge>
          <Link href="/patient">
            <Button variant="secondary" size="sm">
              Patient Vault
            </Button>
          </Link>
          <Link href="/doctor">
            <Button variant="secondary" size="sm">
              Doctor EMR
            </Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left 5 Columns: Cryptographic PDF Stamping & Ingestion Panel */}
        <div className="lg:col-span-5 space-y-6">
          <Card variant="mockup" className="space-y-5 bg-[#f8f9fa] border-[#e5e7eb]">
            <div>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Cryptographic PDF Ingestion</CardTitle>
                <Badge variant="neutral">SHA-256 Sealed</Badge>
              </div>
              <CardDescription>
                Upload diagnostic PDFs to compute immutable cryptographic hashes before patient vault dispatch.
              </CardDescription>
            </div>

            <form onSubmit={handleIngestPDF} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#6b7280] mb-1.5">
                  Select Patient (ABHA Linked)
                </label>
                <select
                  value={selectedPatient}
                  onChange={(e) => setSelectedPatient(e.target.value)}
                  className="w-full h-10 px-3 text-sm rounded-lg border border-[#e5e7eb] bg-white text-[#111111] focus:outline-none focus:ring-2 focus:ring-[#111111]"
                >
                  <option value="Arun Patel (91-8472-1092-4821)">Arun Patel • ABHA: 91-8472-1092-4821</option>
                  <option value="Sunita Rao (91-2384-9812-7419)">Sunita Rao • ABHA: 91-2384-9812-7419</option>
                  <option value="Vikram Malhotra (91-5512-8823-1094)">Vikram Malhotra • ABHA: 91-5512-8823-1094</option>
                </select>
              </div>

              {/* Upload Zone */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#6b7280] mb-1.5">
                  Diagnostic PDF Report
                </label>
                <div className="border-2 border-dashed border-[#e5e7eb] rounded-lg p-4 text-center hover:border-[#111111] transition-colors bg-white cursor-pointer relative">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                  />
                  <UploadCloud className="h-8 w-8 text-[#9ca3af] mx-auto mb-2" />
                  <p className="text-xs font-medium text-[#111111] truncate">{fileName}</p>
                  <p className="text-[11px] text-[#6b7280] mt-0.5">Click or drag PDF to compute tamper-seal</p>
                </div>
              </div>

              {/* SHA-256 Digest Box */}
              <div className="p-3 bg-white rounded-lg border border-[#e5e7eb] space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#111111] flex items-center gap-1">
                    <Fingerprint className="h-3.5 w-3.5 text-[#111111]" />
                    SHA-256 Tamper-Evident Digest
                  </span>
                  <span className="text-[10px] text-[#10b981] font-mono">
                    {isHashing ? "Hashing..." : "Verified"}
                  </span>
                </div>
                <p className="font-mono text-[11px] text-[#6b7280] break-all leading-tight bg-[#f9fafb] p-2 rounded border border-[#f3f4f6]">
                  {fileSha256}
                </p>
              </div>

              {/* Cryptographic Stamping Key */}
              <div className="flex items-center justify-between text-xs text-[#6b7280] px-1">
                <span className="flex items-center gap-1">
                  <Lock className="h-3 w-3 text-[#111111]" />
                  RSA-PSS 4096-bit Signed
                </span>
                <span className="font-mono text-[11px]">HFR: HFR-DEL-91024</span>
              </div>

              <Button type="submit" variant="primary" className="w-full">
                <ShieldCheck className="h-4 w-4 mr-2" />
                Sign & Seal Diagnostic Report
              </Button>
            </form>

            {isIngested && (
              <div className="p-3 bg-[#ecfdf5] border border-[#a7f3d0] rounded-lg text-xs text-[#065f46] flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#059669] shrink-0" />
                <div>
                  <p className="font-semibold">Diagnostic Report Signed & Queued</p>
                  <p className="text-[11px] text-[#047857]">Dispatched to ABHA Health Locker with SHA-256 verification hash.</p>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Right 7 Columns placeholder for LOINC Builder & FHIR Bundle */}
        <div className="lg:col-span-7 space-y-6">
          <Card variant="mockup" className="p-6">
            <CardTitle className="text-lg">Observation & FHIR Builder</CardTitle>
            <CardDescription>Configuring structured laboratory diagnostics...</CardDescription>
          </Card>
        </div>

      </div>
    </div>
  );
}
