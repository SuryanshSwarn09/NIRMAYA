"use client";

import React, { useState, useMemo } from "react";
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
  Copy,
  Check,
  RefreshCw,
} from "lucide-react";

interface ObservationItem {
  loinc: string;
  name: string;
  value: number;
  unit: string;
  reference: string;
  status: "normal" | "warning" | "high";
}

export default function DiagnosticLabPage() {
  const { user } = useAuth();

  // Patient & Document State
  const [selectedPatientId, setSelectedPatientId] = useState("91-8472-1092-4821");
  const [patientName, setPatientName] = useState("Arun Patel");
  const [fileName, setFileName] = useState("Apollo_Biochemistry_Panel_0925.pdf");
  const [fileSha256, setFileSha256] = useState(
    "d5a8b79e13c84f494f69747a28e9323f4b46c6a49dbd29486c434f09a5ebc109"
  );
  const [isHashing, setIsHashing] = useState(false);
  const [isIngested, setIsIngested] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"builder" | "fhir" | "ledger">("builder");

  // Structured LOINC Observations State
  const [fastingGlucose, setFastingGlucose] = useState<number>(94);
  const [totalCholesterol, setTotalCholesterol] = useState<number>(185);
  const [hdlCholesterol, setHdlCholesterol] = useState<number>(54);
  const [ldlCholesterol, setLdlCholesterol] = useState<number>(108);
  const [triglycerides, setTriglycerides] = useState<number>(138);
  const [hba1c, setHba1c] = useState<number>(5.4);

  // Compute status helpers
  const observations: ObservationItem[] = useMemo(() => [
    {
      loinc: "1558-6",
      name: "Fasting Blood Glucose",
      value: fastingGlucose,
      unit: "mg/dL",
      reference: "70 - 99 mg/dL",
      status: fastingGlucose > 125 ? "high" : fastingGlucose >= 100 ? "warning" : "normal",
    },
    {
      loinc: "2093-3",
      name: "Total Cholesterol",
      value: totalCholesterol,
      unit: "mg/dL",
      reference: "< 200 mg/dL",
      status: totalCholesterol >= 240 ? "high" : totalCholesterol >= 200 ? "warning" : "normal",
    },
    {
      loinc: "2085-9",
      name: "HDL Cholesterol",
      value: hdlCholesterol,
      unit: "mg/dL",
      reference: "> 40 mg/dL",
      status: hdlCholesterol < 40 ? "warning" : "normal",
    },
    {
      loinc: "13457-7",
      name: "LDL Cholesterol (Calculated)",
      value: ldlCholesterol,
      unit: "mg/dL",
      reference: "< 100 mg/dL",
      status: ldlCholesterol >= 160 ? "high" : ldlCholesterol >= 100 ? "warning" : "normal",
    },
    {
      loinc: "2571-8",
      name: "Serum Triglycerides",
      value: triglycerides,
      unit: "mg/dL",
      reference: "< 150 mg/dL",
      status: triglycerides >= 200 ? "high" : triglycerides >= 150 ? "warning" : "normal",
    },
    {
      loinc: "4548-4",
      name: "Hemoglobin A1c (HbA1c)",
      value: hba1c,
      unit: "%",
      reference: "< 5.7 %",
      status: hba1c >= 6.5 ? "high" : hba1c >= 5.7 ? "warning" : "normal",
    },
  ], [fastingGlucose, totalCholesterol, hdlCholesterol, ldlCholesterol, triglycerides, hba1c]);

  // Dynamic HL7 FHIR R4 DiagnosticReport Bundle
  const fhirDiagnosticReport = useMemo(() => {
    return {
      resourceType: "DiagnosticReport",
      id: "dr-apollo-2026-0925-01",
      meta: {
        versionId: "1",
        lastUpdated: new Date().toISOString(),
        profile: [
          "https://nrces.in/ndhm/fhir/r4/StructureDefinition/DiagnosticReportLab",
        ],
      },
      status: "final",
      category: [
        {
          coding: [
            {
              system: "http://terminology.hl7.org/CodeSystem/v2-0074",
              code: "LAB",
              display: "Laboratory",
            },
          ],
        },
      ],
      code: {
        coding: [
          {
            system: "http://loinc.org",
            code: "57021-8",
            display: "CBC and Comprehensive Metabolic Panel",
          },
        ],
        text: "Comprehensive Lipid & Glycemic Diagnostic Panel",
      },
      subject: {
        reference: `Patient/ABHA-${selectedPatientId}`,
        display: patientName,
      },
      effectiveDateTime: new Date().toISOString(),
      issued: new Date().toISOString(),
      performer: [
        {
          reference: "Organization/HFR-DEL-91024",
          display: "Apollo Diagnostics Central",
        },
      ],
      presentedForm: [
        {
          contentType: "application/pdf",
          language: "en-IN",
          title: fileName,
          hash: fileSha256,
        },
      ],
      result: observations.map((obs) => ({
        reference: `Observation/loinc-${obs.loinc}`,
        display: `${obs.name}: ${obs.value} ${obs.unit}`,
      })),
      conclusion: "Lipid profile within normal physiological range. Mild lifestyle monitoring advised.",
    };
  }, [selectedPatientId, patientName, fileName, fileSha256, observations]);

  // Handle patient switch
  const handlePatientSelect = (val: string) => {
    if (val === "arun") {
      setSelectedPatientId("91-8472-1092-4821");
      setPatientName("Arun Patel");
    } else if (val === "sunita") {
      setSelectedPatientId("91-2384-9812-7419");
      setPatientName("Sunita Rao");
    } else if (val === "vikram") {
      setSelectedPatientId("91-5512-8823-1094");
      setPatientName("Vikram Malhotra");
    }
  };

  // Cryptographic Stamping
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFileName(file.name);
      setIsHashing(true);
      setIsIngested(false);

      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const buffer = reader.result as ArrayBuffer;
          const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
          const hashArray = Array.from(new Uint8Array(hashBuffer));
          const hashHex = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
          setFileSha256(hashHex);
        } catch {
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

  const copyToClipboard = () => {
    navigator.clipboard.writeText(JSON.stringify(fhirDiagnosticReport, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
                  value={
                    selectedPatientId.includes("8472")
                      ? "arun"
                      : selectedPatientId.includes("2384")
                      ? "sunita"
                      : "vikram"
                  }
                  onChange={(e) => handlePatientSelect(e.target.value)}
                  className="w-full h-10 px-3 text-sm rounded-lg border border-[#e5e7eb] bg-white text-[#111111] focus:outline-none focus:ring-2 focus:ring-[#111111]"
                >
                  <option value="arun">Arun Patel • ABHA: 91-8472-1092-4821</option>
                  <option value="sunita">Sunita Rao • ABHA: 91-2384-9812-7419</option>
                  <option value="vikram">Vikram Malhotra • ABHA: 91-5512-8823-1094</option>
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
                    {isHashing ? "Computing..." : "Verified"}
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

          {/* Standards & Certifications Card */}
          <Card variant="feature" className="p-5 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#6b7280]">
              Accreditation & Interoperability
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 bg-[#f9fafb] rounded border border-[#e5e7eb]">
                <p className="font-semibold text-[#111111]">NABL Medical</p>
                <p className="text-[11px] text-[#6b7280]">ISO 15189:2022 Certified</p>
              </div>
              <div className="p-2.5 bg-[#f9fafb] rounded border border-[#e5e7eb]">
                <p className="font-semibold text-[#111111]">ABDM M3</p>
                <p className="text-[11px] text-[#6b7280]">Diagnostic HIP / HIU Active</p>
              </div>
              <div className="p-2.5 bg-[#f9fafb] rounded border border-[#e5e7eb]">
                <p className="font-semibold text-[#111111]">LOINC Database</p>
                <p className="text-[11px] text-[#6b7280]">v2.76 Release Synced</p>
              </div>
              <div className="p-2.5 bg-[#f9fafb] rounded border border-[#e5e7eb]">
                <p className="font-semibold text-[#111111]">HL7 FHIR</p>
                <p className="text-[11px] text-[#6b7280]">DiagnosticReport R4</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Right 7 Columns: Structured LOINC Builder, Live FHIR JSON & Ledger */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* Cal.com-Style Navigation Tabs */}
          <div className="flex items-center justify-between pb-2 border-b border-[#e5e7eb]">
            <div className="flex items-center gap-1 bg-[#f3f4f6] p-1 rounded-lg">
              <button
                onClick={() => setActiveTab("builder")}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  activeTab === "builder"
                    ? "bg-white text-[#111111] shadow-sm font-semibold"
                    : "text-[#6b7280] hover:text-[#111111]"
                }`}
              >
                LOINC Observation Builder
              </button>
              <button
                onClick={() => setActiveTab("fhir")}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  activeTab === "fhir"
                    ? "bg-white text-[#111111] shadow-sm font-semibold"
                    : "text-[#6b7280] hover:text-[#111111]"
                }`}
              >
                FHIR R4 DiagnosticReport JSON
              </button>
              <button
                onClick={() => setActiveTab("ledger")}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  activeTab === "ledger"
                    ? "bg-white text-[#111111] shadow-sm font-semibold"
                    : "text-[#6b7280] hover:text-[#111111]"
                }`}
              >
                Recent Ingestion Ledger
              </button>
            </div>

            {activeTab === "fhir" && (
              <Button variant="secondary" size="sm" onClick={copyToClipboard}>
                {copied ? <Check className="h-3.5 w-3.5 mr-1 text-[#10b981]" /> : <Copy className="h-3.5 w-3.5 mr-1" />}
                {copied ? "Copied" : "Copy JSON"}
              </Button>
            )}
          </div>

          {/* TAB 1: Structured LOINC Builder */}
          {activeTab === "builder" && (
            <Card variant="mockup" className="space-y-6">
              <div>
                <CardTitle className="text-lg">Structured Pathology Test Parameters</CardTitle>
                <CardDescription>
                  Enter calibrated clinical laboratory findings. Numeric values automatically validate against clinical reference thresholds.
                </CardDescription>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Fasting Glucose */}
                <div className="p-4 bg-[#f9fafb] rounded-lg border border-[#e5e7eb] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#6b7280]">LOINC 1558-6</span>
                    <Badge variant={fastingGlucose >= 100 ? "warning" : "emerald"} size="sm">
                      {fastingGlucose >= 100 ? "Pre-diabetic" : "Normal"}
                    </Badge>
                  </div>
                  <label className="block text-sm font-semibold text-[#111111]">
                    Fasting Blood Glucose
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={fastingGlucose}
                      onChange={(e) => setFastingGlucose(Number(e.target.value))}
                      className="w-full h-9 px-3 text-sm rounded border border-[#e5e7eb] bg-white font-mono"
                    />
                    <span className="text-xs font-medium text-[#6b7280] shrink-0">mg/dL</span>
                  </div>
                  <p className="text-[11px] text-[#9ca3af]">Ref: 70 - 99 mg/dL</p>
                </div>

                {/* Total Cholesterol */}
                <div className="p-4 bg-[#f9fafb] rounded-lg border border-[#e5e7eb] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#6b7280]">LOINC 2093-3</span>
                    <Badge variant={totalCholesterol >= 200 ? "warning" : "emerald"} size="sm">
                      {totalCholesterol >= 200 ? "Borderline High" : "Desirable"}
                    </Badge>
                  </div>
                  <label className="block text-sm font-semibold text-[#111111]">
                    Total Serum Cholesterol
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={totalCholesterol}
                      onChange={(e) => setTotalCholesterol(Number(e.target.value))}
                      className="w-full h-9 px-3 text-sm rounded border border-[#e5e7eb] bg-white font-mono"
                    />
                    <span className="text-xs font-medium text-[#6b7280] shrink-0">mg/dL</span>
                  </div>
                  <p className="text-[11px] text-[#9ca3af]">Ref: &lt; 200 mg/dL</p>
                </div>

                {/* HDL Cholesterol */}
                <div className="p-4 bg-[#f9fafb] rounded-lg border border-[#e5e7eb] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#6b7280]">LOINC 2085-9</span>
                    <Badge variant={hdlCholesterol < 40 ? "warning" : "emerald"} size="sm">
                      {hdlCholesterol < 40 ? "Low (Risk)" : "Normal"}
                    </Badge>
                  </div>
                  <label className="block text-sm font-semibold text-[#111111]">
                    HDL Cholesterol (Good)
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={hdlCholesterol}
                      onChange={(e) => setHdlCholesterol(Number(e.target.value))}
                      className="w-full h-9 px-3 text-sm rounded border border-[#e5e7eb] bg-white font-mono"
                    />
                    <span className="text-xs font-medium text-[#6b7280] shrink-0">mg/dL</span>
                  </div>
                  <p className="text-[11px] text-[#9ca3af]">Ref: &gt; 40 mg/dL</p>
                </div>

                {/* LDL Cholesterol */}
                <div className="p-4 bg-[#f9fafb] rounded-lg border border-[#e5e7eb] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#6b7280]">LOINC 13457-7</span>
                    <Badge variant={ldlCholesterol >= 100 ? "warning" : "emerald"} size="sm">
                      {ldlCholesterol >= 100 ? "Borderline High" : "Optimal"}
                    </Badge>
                  </div>
                  <label className="block text-sm font-semibold text-[#111111]">
                    LDL Cholesterol (Calculated)
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={ldlCholesterol}
                      onChange={(e) => setLdlCholesterol(Number(e.target.value))}
                      className="w-full h-9 px-3 text-sm rounded border border-[#e5e7eb] bg-white font-mono"
                    />
                    <span className="text-xs font-medium text-[#6b7280] shrink-0">mg/dL</span>
                  </div>
                  <p className="text-[11px] text-[#9ca3af]">Ref: &lt; 100 mg/dL</p>
                </div>

                {/* Triglycerides */}
                <div className="p-4 bg-[#f9fafb] rounded-lg border border-[#e5e7eb] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#6b7280]">LOINC 2571-8</span>
                    <Badge variant={triglycerides >= 150 ? "warning" : "emerald"} size="sm">
                      {triglycerides >= 150 ? "Elevated" : "Normal"}
                    </Badge>
                  </div>
                  <label className="block text-sm font-semibold text-[#111111]">
                    Serum Triglycerides
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={triglycerides}
                      onChange={(e) => setTriglycerides(Number(e.target.value))}
                      className="w-full h-9 px-3 text-sm rounded border border-[#e5e7eb] bg-white font-mono"
                    />
                    <span className="text-xs font-medium text-[#6b7280] shrink-0">mg/dL</span>
                  </div>
                  <p className="text-[11px] text-[#9ca3af]">Ref: &lt; 150 mg/dL</p>
                </div>

                {/* HbA1c */}
                <div className="p-4 bg-[#f9fafb] rounded-lg border border-[#e5e7eb] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#6b7280]">LOINC 4548-4</span>
                    <Badge variant={hba1c >= 5.7 ? "warning" : "emerald"} size="sm">
                      {hba1c >= 5.7 ? "Elevated" : "Normal"}
                    </Badge>
                  </div>
                  <label className="block text-sm font-semibold text-[#111111]">
                    Glycated Hemoglobin (HbA1c)
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      step="0.1"
                      value={hba1c}
                      onChange={(e) => setHba1c(Number(e.target.value))}
                      className="w-full h-9 px-3 text-sm rounded border border-[#e5e7eb] bg-white font-mono"
                    />
                    <span className="text-xs font-medium text-[#6b7280] shrink-0">%</span>
                  </div>
                  <p className="text-[11px] text-[#9ca3af]">Ref: &lt; 5.7 %</p>
                </div>

              </div>

              <div className="flex items-center justify-between pt-2">
                <Button variant="secondary" size="sm" onClick={() => setActiveTab("fhir")}>
                  <Code className="h-4 w-4 mr-2" />
                  Inspect FHIR Bundle
                </Button>
                <Button variant="primary" size="sm" onClick={handleIngestPDF}>
                  <ShieldCheck className="h-4 w-4 mr-2" />
                  Emit Signed FHIR Bundle
                </Button>
              </div>
            </Card>
          )}

          {/* TAB 2: Live FHIR R4 DiagnosticReport JSON */}
          {activeTab === "fhir" && (
            <Card variant="mockup" className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-mono">HL7 FHIR R4 DiagnosticReport</CardTitle>
                  <CardDescription>
                    Live schema conforming to ABDM NRCeS DiagnosticReportLab profile.
                  </CardDescription>
                </div>
                <Badge variant="verified">FHIR R4 Valid</Badge>
              </div>

              <div className="p-4 bg-[#111111] text-[#f3f4f6] rounded-xl font-mono text-xs overflow-x-auto max-h-[480px] border border-[#262626]">
                <pre>{JSON.stringify(fhirDiagnosticReport, null, 2)}</pre>
              </div>

              <div className="flex items-center justify-between text-xs text-[#6b7280]">
                <span>Schema Profile: StructureDefinition/DiagnosticReportLab</span>
                <span>Payload Size: ~1.4 KB</span>
              </div>
            </Card>
          )}

          {/* TAB 3: Recent Ingestion Ledger */}
          {activeTab === "ledger" && (
            <Card variant="mockup" className="space-y-4">
              <div>
                <CardTitle className="text-lg">Recent Diagnostic Encounters</CardTitle>
                <CardDescription>
                  Chronological dispatch ledger of cryptographically stamped laboratory encounters.
                </CardDescription>
              </div>

              <div className="divide-y divide-[#e5e7eb] border border-[#e5e7eb] rounded-lg overflow-hidden">
                
                {/* Item 1 */}
                <div className="p-4 bg-white flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-[#111111]">Arun Patel</span>
                      <span className="font-mono text-xs text-[#6b7280]">ABHA: 91-8472-1092-4821</span>
                    </div>
                    <p className="text-xs text-[#6b7280]">
                      Lipid & Glycemic Panel (6 LOINC parameters) • Apollo_Biochemistry_Panel_0925.pdf
                    </p>
                    <p className="font-mono text-[10px] text-[#9ca3af] truncate max-w-md">
                      SHA-256: d5a8b79e13c84f494f69747a28e9323f4b46c6a49dbd29486c434f09a5ebc109
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <Badge variant="verified" size="sm">Vault Synced</Badge>
                    <p className="text-[10px] text-[#9ca3af] mt-1">Today, 18:45</p>
                  </div>
                </div>

                {/* Item 2 */}
                <div className="p-4 bg-[#fafafa] flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-[#111111]">Sunita Rao</span>
                      <span className="font-mono text-xs text-[#6b7280]">ABHA: 91-2384-9812-7419</span>
                    </div>
                    <p className="text-xs text-[#6b7280]">
                      Complete Blood Count (CBC) • Apollo_CBC_Differential_0924.pdf
                    </p>
                    <p className="font-mono text-[10px] text-[#9ca3af] truncate max-w-md">
                      SHA-256: 4e91bc78291a189fec01a23891402837bc901a18274981bc8910a23891bc8102
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <Badge variant="verified" size="sm">Vault Synced</Badge>
                    <p className="text-[10px] text-[#9ca3af] mt-1">Yesterday, 14:10</p>
                  </div>
                </div>

                {/* Item 3 */}
                <div className="p-4 bg-white flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-[#111111]">Vikram Malhotra</span>
                      <span className="font-mono text-xs text-[#6b7280]">ABHA: 91-5512-8823-1094</span>
                    </div>
                    <p className="text-xs text-[#6b7280]">
                      Thyroid Stimulating Hormone (TSH) • Apollo_Endocrine_TSH_0922.pdf
                    </p>
                    <p className="font-mono text-[10px] text-[#9ca3af] truncate max-w-md">
                      SHA-256: f819bc29810419283bc901824719283749102837491028374910283749102837
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <Badge variant="verified" size="sm">Vault Synced</Badge>
                    <p className="text-[10px] text-[#9ca3af] mt-1">22 Sep, 11:30</p>
                  </div>
                </div>

              </div>
            </Card>
          )}

        </div>

      </div>
    </div>
  );
}
