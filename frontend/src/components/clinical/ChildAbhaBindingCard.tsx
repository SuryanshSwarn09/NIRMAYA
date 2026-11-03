"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  AlertCircle,
  ArrowRight,
  Baby,
  CheckCircle2,
  FileCheck,
  FileCode,
  Lock,
  QrCode,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

export interface ChildAbhaIssuedState {
  childName: string;
  childGender: "MALE" | "FEMALE" | "OTHER";
  childDob: string;
  childAge: number;
  abhaNumber: string;
  abhaAddress: string;
  patientId: string;
  relationshipId: string;
  verificationTier: string;
  documentHash: string;
  qrPayload: string;
}

export function ChildAbhaBindingCard() {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [guardianAadhaar, setGuardianAadhaar] = useState<string>("548190284821");
  const [guardianConsent, setGuardianConsent] = useState<boolean>(true);
  const [otpCode, setOtpCode] = useState<string>("123456");
  const [txnId, setTxnId] = useState<string>("txn-child-abha-mock-9102");

  // Child details
  const [childName, setChildName] = useState<string>("Diya Sharma");
  const [childGender, setChildGender] = useState<"MALE" | "FEMALE" | "OTHER">("FEMALE");
  const [childDob, setChildDob] = useState<string>("2021-04-18");
  const [preferredHandle, setPreferredHandle] = useState<string>("diya.sharma");
  const [birthCertId, setBirthCertId] = useState<string>("NDMC-BIRTH-2021-981240");
  const [digilockerVerified, setDigilockerVerified] = useState<boolean>(false);
  const [digilockerHash, setDigilockerHash] = useState<string>("");

  // Result state
  const [issuedResult, setIssuedResult] = useState<ChildAbhaIssuedState | null>(null);
  const [showFhirJson, setShowFhirJson] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleSendOtp = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setTxnId(`txn-child-abha-${Date.now().toString().slice(-6)}`);
      setStep(2);
    }, 600);
  };

  const handleVerifyDigiLocker = () => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setDigilockerVerified(true);
      setDigilockerHash("4f910a284c81029481b049182b0412984109481b049182b0412984109481b049");
    }, 500);
  };

  const handleMintChildAbha = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    setTimeout(() => {
      setIsLoading(false);
      const mintedAbha = `14-${Math.floor(1000 + Math.random() * 9000)}-${Math.floor(1000 + Math.random() * 9000)}-${Math.floor(1000 + Math.random() * 9000)}`;
      const result: ChildAbhaIssuedState = {
        childName,
        childGender,
        childDob,
        childAge: 5,
        abhaNumber: mintedAbha,
        abhaAddress: `${preferredHandle.toLowerCase()}@abdm`,
        patientId: `pat-child-${Date.now().toString().slice(-6)}`,
        relationshipId: `rel-proxy-child-${Date.now().toString().slice(-4)}`,
        verificationTier: digilockerVerified
          ? "DIGILOCKER_BIRTH_CERTIFICATE"
          : "AADHAAR_DEMOGRAPHIC_EKYC",
        documentHash:
          digilockerHash ||
          "8f12a048c081294801928409182409182b0412984109481b049182b041298410",
        qrPayload: `ABDM:CHILD:${mintedAbha}:${preferredHandle.toLowerCase()}@abdm`,
      };
      setIssuedResult(result);
      setStep(4);
    }, 800);
  };

  const handleReset = () => {
    setStep(1);
    setDigilockerVerified(false);
    setDigilockerHash("");
    setIssuedResult(null);
    setShowFhirJson(false);
  };

  const fhirRelatedPersonSample = issuedResult
    ? {
        resourceType: "RelatedPerson",
        id: `related-person-${issuedResult.relationshipId}`,
        patient: {
          reference: `Patient/${issuedResult.patientId}`,
          display: issuedResult.childName,
        },
        relationship: [
          {
            coding: [
              {
                system: "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                code: "PRN",
                display: "parent",
              },
            ],
            text: "Mother (Guardian)",
          },
        ],
        name: [
          {
            use: "official",
            text: "Dr. Priya Sharma",
          },
        ],
        telecom: [
          {
            system: "phone",
            value: "+91-9876543210",
            use: "mobile",
          },
        ],
        period: {
          start: new Date().toISOString(),
        },
      }
    : null;

  return (
    <Card className="border border-[#e5e7eb] bg-[#ffffff] shadow-sm rounded-lg overflow-hidden">
      {/* Header */}
      <div className="border-b border-[#e5e7eb] p-6 bg-[#ffffff]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold tracking-wider text-[#6b7280] uppercase">
                ABDM M1 & DPDP Act Sec 9 Integration
              </span>
              <Badge variant="abdm">ABDM M1 Certified</Badge>
              <Badge variant="verified">Parent-Linked Child ABHA</Badge>
            </div>
            <h2 className="text-xl font-semibold text-[#111111] tracking-tight">
              Child-ABHA Issuance & Demographic Binding
            </h2>
            <p className="text-sm text-[#4b5563] mt-0.5">
              Parent-authorized digital health identity issuance for minor children under 18 years. Cryptographic birth certificate provenance via DigiLocker.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="neutral">
              Step {step} of 4:{" "}
              {step === 1 && "Parent Aadhaar OTP"}
              {step === 2 && "Child Demographics"}
              {step === 3 && "DigiLocker Verification"}
              {step === 4 && "Issued Child-ABHA Card"}
            </Badge>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Step 1: Parent Aadhaar OTP Challenge */}
        {step === 1 && (
          <div className="max-w-xl mx-auto space-y-5">
            <div className="p-4 rounded-lg border border-[#e5e7eb] bg-[#f9fafb]">
              <div className="flex items-start gap-3">
                <Lock className="w-5 h-5 text-[#111111] flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-semibold text-[#111111]">
                    Parent/Guardian Aadhaar Authentication
                  </h3>
                  <p className="text-xs text-[#4b5563] mt-0.5">
                    Under ABDM M1 guidelines, children under 18 cannot undergo independent Aadhaar biometric e-KYC. Identity minting is authorized by a registered parent.
                  </p>
                </div>
              </div>
            </div>

            <form onSubmit={handleSendOtp} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[#374151] mb-1">
                  Guardian Aadhaar Number (12 Digits)
                </label>
                <input
                  type="text"
                  required
                  maxLength={12}
                  value={guardianAadhaar}
                  onChange={(e) => setGuardianAadhaar(e.target.value)}
                  placeholder="e.g. 548190284821"
                  className="w-full text-xs font-mono px-3 py-2 border border-[#d1d5db] rounded bg-[#ffffff] text-[#111111] focus:outline-none focus:border-[#111111]"
                />
                <span className="text-[11px] text-[#6b7280] mt-1 block">
                  Simulated sandbox Aadhaar for Dr. Priya Sharma (pat-priya-sharma-01).
                </span>
              </div>

              <div className="flex items-start gap-2 pt-1">
                <input
                  type="checkbox"
                  id="guardianConsentCheck"
                  required
                  checked={guardianConsent}
                  onChange={(e) => setGuardianConsent(e.target.checked)}
                  className="mt-0.5 rounded border-[#d1d5db] text-[#111111] focus:ring-[#111111]"
                />
                <label htmlFor="guardianConsentCheck" className="text-xs text-[#4b5563]">
                  I hereby attest under DPDP Act 2023 Section 9 that I am the legal parent/guardian of the minor child, and consent to issuing an ABDM Child ABHA linked to my Aadhaar identity.
                </label>
              </div>

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full bg-[#111111] text-[#ffffff] hover:bg-[#262626] text-xs font-medium py-2"
              >
                {isLoading ? (
                  <RefreshCw className="w-3.5 h-3.5 mr-1 animate-spin" />
                ) : (
                  <ArrowRight className="w-3.5 h-3.5 mr-1" />
                )}
                Request Aadhaar OTP
              </Button>
            </form>
          </div>
        )}

        {/* Step 2: Child Demographic Ingestion */}
        {step === 2 && (
          <div className="max-w-2xl mx-auto space-y-5">
            <div className="p-3 bg-[#ecfdf5] border border-[#a7f3d0] rounded text-xs text-[#065f46] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>Aadhaar OTP dispatched to guardian mobile (XXXXXX4821).</span>
              </div>
              <span className="font-mono text-[10px] text-[#059669]">Txn: {txnId}</span>
            </div>

            <form onSubmit={handleMintChildAbha} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    6-Digit Aadhaar OTP Code
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    placeholder="123456"
                    className="w-full text-xs font-mono px-3 py-2 border border-[#d1d5db] rounded bg-[#ffffff] text-[#111111] focus:outline-none focus:border-[#111111]"
                  />
                  <span className="text-[10px] text-[#6b7280] mt-0.5 block">Default sandbox OTP: 123456</span>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Child Legal Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={childName}
                    onChange={(e) => setChildName(e.target.value)}
                    placeholder="e.g. Diya Sharma"
                    className="w-full text-xs px-3 py-2 border border-[#d1d5db] rounded bg-[#ffffff] text-[#111111] focus:outline-none focus:border-[#111111]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Administrative Gender
                  </label>
                  <select
                    value={childGender}
                    onChange={(e) => setChildGender(e.target.value as any)}
                    className="w-full text-xs px-3 py-2 border border-[#d1d5db] rounded bg-[#ffffff] text-[#111111] focus:outline-none focus:border-[#111111]"
                  >
                    <option value="FEMALE">Female</option>
                    <option value="MALE">Male</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Date of Birth (Age &lt; 18)
                  </label>
                  <input
                    type="date"
                    required
                    value={childDob}
                    onChange={(e) => setChildDob(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-[#d1d5db] rounded bg-[#ffffff] text-[#111111] focus:outline-none focus:border-[#111111]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Preferred ABHA Address Handle
                  </label>
                  <div className="flex items-center">
                    <input
                      type="text"
                      required
                      value={preferredHandle}
                      onChange={(e) => setPreferredHandle(e.target.value)}
                      placeholder="diya.sharma"
                      className="w-full text-xs px-3 py-2 border border-r-0 border-[#d1d5db] rounded-l bg-[#ffffff] text-[#111111] focus:outline-none focus:border-[#111111]"
                    />
                    <span className="px-3 py-2 text-xs bg-[#f3f4f6] text-[#6b7280] border border-l-0 border-[#d1d5db] rounded-r font-mono">
                      @abdm
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Birth Certificate Number
                  </label>
                  <input
                    type="text"
                    value={birthCertId}
                    onChange={(e) => setBirthCertId(e.target.value)}
                    placeholder="e.g. NDMC-BIRTH-2021-981240"
                    className="w-full text-xs px-3 py-2 border border-[#d1d5db] rounded bg-[#ffffff] text-[#111111] focus:outline-none focus:border-[#111111]"
                  />
                </div>
              </div>

              {/* DigiLocker Ingestion Box */}
              <div className="p-4 rounded-lg border border-[#e5e7eb] bg-[#f9fafb] space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileCheck className="w-4 h-4 text-[#059669]" />
                    <span className="text-xs font-semibold text-[#111111]">
                      DigiLocker Birth Certificate Verification
                    </span>
                  </div>
                  {digilockerVerified ? (
                    <Badge variant="verified">Verified (SHA-256)</Badge>
                  ) : (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={handleVerifyDigiLocker}
                      className="text-xs text-[#111111] border-[#d1d5db] hover:bg-[#ffffff]"
                    >
                      Verify via DigiLocker
                    </Button>
                  )}
                </div>
                {digilockerVerified && (
                  <div className="text-[11px] font-mono text-[#065f46] bg-[#ecfdf5] p-2 rounded truncate">
                    Hash: {digilockerHash}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2 pt-2">
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="bg-[#111111] text-[#ffffff] hover:bg-[#262626] text-xs font-medium py-2"
                >
                  {isLoading ? (
                    <RefreshCw className="w-3.5 h-3.5 mr-1 animate-spin" />
                  ) : (
                    <Sparkles className="w-3.5 h-3.5 mr-1" />
                  )}
                  Verify & Mint Sovereign Child-ABHA
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep(1)}
                  className="text-xs text-[#6b7280] border-[#e5e7eb]"
                >
                  Back
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* Step 4: Issued Child-ABHA Credential Presentation */}
        {step === 4 && issuedResult && (
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="p-3 bg-[#ecfdf5] border border-[#a7f3d0] rounded text-xs text-[#065f46] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span className="font-semibold">
                  Child ABHA successfully issued and verified under DPDP Act Section 9.
                </span>
              </div>
              <Badge variant="verified">Sovereign Vault Active</Badge>
            </div>

            {/* ABHA Digital Credential Card */}
            <div className="border border-[#111111] rounded-xl p-6 bg-[#ffffff] shadow-sm relative overflow-hidden">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-4">
                  <div>
                    <span className="text-[10px] font-semibold tracking-wider text-[#6b7280] uppercase">
                      National Health Authority | ABDM Child Identity
                    </span>
                    <h3 className="text-xl font-bold text-[#111111] mt-0.5">
                      {issuedResult.childName}
                    </h3>
                    <span className="text-xs text-[#4b5563]">
                      DOB: {issuedResult.childDob} ({issuedResult.childAge} years) | Gender: {issuedResult.childGender}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 pt-1">
                    <div>
                      <span className="text-[10px] font-medium text-[#6b7280] uppercase block">
                        Child ABHA Number
                      </span>
                      <div className="font-mono text-base font-bold text-[#111111] tracking-wide mt-0.5">
                        {issuedResult.abhaNumber}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] font-medium text-[#6b7280] uppercase block">
                        ABHA Address Handle
                      </span>
                      <div className="font-mono text-sm font-semibold text-[#111111] mt-0.5">
                        {issuedResult.abhaAddress}
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 flex flex-wrap items-center gap-2">
                    <Badge variant="verified">DigiLocker Verified</Badge>
                    <Badge variant="emerald">Zero Contamination Isolated</Badge>
                    <span className="text-[11px] font-mono text-[#6b7280]">
                      ID: {issuedResult.patientId}
                    </span>
                  </div>
                </div>

                {/* QR Code Block */}
                <div className="flex flex-col items-center justify-center p-4 bg-[#f9fafb] border border-[#e5e7eb] rounded-lg">
                  <QrCode className="w-24 h-24 text-[#111111]" />
                  <span className="text-[10px] font-mono text-[#6b7280] mt-1 text-center">
                    Offline ABHA QR
                  </span>
                </div>
              </div>
            </div>

            {/* Action Buttons & FHIR Inspector */}
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-2">
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowFhirJson(!showFhirJson)}
                  className="text-xs font-medium text-[#111111] border-[#d1d5db] hover:bg-[#f9fafb]"
                >
                  <FileCode className="w-3.5 h-3.5 mr-1" />
                  {showFhirJson ? "Hide HL7 FHIR RelatedPerson" : "Inspect HL7 FHIR RelatedPerson"}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleReset}
                  className="text-xs text-[#6b7280] border-[#e5e7eb]"
                >
                  Issue Another Child ABHA
                </Button>
              </div>

              <span className="text-xs text-[#4b5563]">
                Delegation ID: <code className="text-xs font-mono">{issuedResult.relationshipId}</code>
              </span>
            </div>

            {/* HL7 FHIR R4 JSON Viewer */}
            {showFhirJson && fhirRelatedPersonSample && (
              <div className="p-4 rounded-lg border border-[#e5e7eb] bg-[#111111] text-[#ffffff] font-mono text-xs overflow-x-auto">
                <div className="flex items-center justify-between pb-2 border-b border-[#262626] mb-3">
                  <span className="text-[11px] text-[#9ca3af]">
                    NRCeS Standard: HL7 FHIR R4 RelatedPerson Resource
                  </span>
                  <Badge variant="neutral" className="bg-[#262626] text-[#ffffff] border-[#374151]">
                    JSON
                  </Badge>
                </div>
                <pre>{JSON.stringify(fhirRelatedPersonSample, null, 2)}</pre>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
