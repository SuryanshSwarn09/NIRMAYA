"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  AlertCircle,
  ArrowRight,
  Ban,
  CheckCircle2,
  Clock,
  Eye,
  FileCheck,
  FileCode,
  Key,
  Lock,
  RefreshCw,
  ShieldCheck,
  UserCheck,
  X,
} from "lucide-react";

export interface PendingConsentRequest {
  requestId: string;
  requesterName: string;
  requesterHpid: string;
  requesterFacility: string;
  childName: string;
  childAbha: string;
  purpose: string;
  purposeDescription: string;
  hiTypes: string[];
  dateFrom: string;
  dateTo: string;
  requestedAt: string;
}

export interface ActiveConsentArtifact {
  artifactId: string;
  relationshipId: string;
  childName: string;
  childAbha: string;
  guardianName: string;
  guardianRole: string;
  requesterFacility: string;
  purpose: string;
  hiTypes: string[];
  status: "ACTIVE" | "EXPIRED" | "REVOKED";
  grantedAt: string;
  expiresAt: string;
  digitalSignature: string;
}

export interface EphemeralTokenState {
  token: string;
  tokenType: string;
  expiresInSeconds: number;
  jti: string;
  allowedHiTypes: string[];
  purpose: string;
  childAbha: string;
  issuedAt: string;
}

const INITIAL_REQUESTS: PendingConsentRequest[] = [
  {
    requestId: "req-abdm-ped-9021",
    requesterName: "Dr. Ananya Sen, MD (Pediatrics)",
    requesterHpid: "dr.ananya.sen@hpid",
    requesterFacility: "Fortis Memorial Pediatric Care",
    childName: "Diya Sharma (5 yrs)",
    childAbha: "14-8821-9031-4120",
    purpose: "CARETREE",
    purposeDescription: "Routine Clinical Care and Management",
    hiTypes: ["Prescription", "DiagnosticReport", "OPConsultation"],
    dateFrom: "2026-05-01",
    dateTo: "2026-11-04",
    requestedAt: "2026-11-04 09:15 IST",
  },
  {
    requestId: "req-abdm-ped-9022",
    requesterName: "Dr. Rajesh Kulkarni, MS (ENT)",
    requesterHpid: "dr.rkulkarni@hpid",
    requesterFacility: "Apollo Tele-Pediatrics Super-Specialty",
    childName: "Aarav Sharma (3 yrs)",
    childAbha: "14-7712-3490-8812",
    purpose: "BTG",
    purposeDescription: "Break-The-Glass Emergency Pediatric Triage",
    hiTypes: ["Prescription", "DischargeSummary", "DiagnosticReport"],
    dateFrom: "2026-10-01",
    dateTo: "2026-11-04",
    requestedAt: "2026-11-04 11:30 IST",
  },
];

const INITIAL_ARTIFACTS: ActiveConsentArtifact[] = [
  {
    artifactId: "ABDM-ART-20261104-91028",
    relationshipId: "rel-proxy-child-8812",
    childName: "Diya Sharma",
    childAbha: "14-8821-9031-4120",
    guardianName: "Sunita Sharma (Mother)",
    guardianRole: "PRN (Parent / Legal Guardian)",
    requesterFacility: "Max Healthcare Pediatric Center",
    purpose: "CARETREE",
    hiTypes: ["Prescription", "DiagnosticReport", "ImmunizationRecord"],
    status: "ACTIVE",
    grantedAt: "2026-11-02 14:00 IST",
    expiresAt: "2027-05-02 23:59 IST",
    digitalSignature: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  },
];

export function GuardianConsentDelegationCard() {
  const [activeTab, setActiveTab] = useState<"pending" | "active" | "token">("pending");
  const [pendingRequests, setPendingRequests] = useState<PendingConsentRequest[]>(INITIAL_REQUESTS);
  const [artifacts, setArtifacts] = useState<ActiveConsentArtifact[]>(INITIAL_ARTIFACTS);

  // Modal Grant Flow
  const [selectedRequest, setSelectedRequest] = useState<PendingConsentRequest | null>(null);
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [selectedHiTypes, setSelectedHiTypes] = useState<string[]>([]);
  const [dpdpConsentChecked, setDpdpConsentChecked] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Revocation State
  const [revokingArtifactId, setRevokingArtifactId] = useState<string | null>(null);
  const [revokeReason, setRevokeReason] = useState<string>("Parent requested delegation termination");
  const [revokeModalOpen, setRevokeModalOpen] = useState<boolean>(false);

  // Ephemeral Token Generation State
  const [tokenPurpose, setTokenPurpose] = useState<string>("CARETREE");
  const [tokenChildAbha, setTokenChildAbha] = useState<string>("14-8821-9031-4120");
  const [tokenHiTypes, setTokenHiTypes] = useState<string[]>([
    "Prescription",
    "DiagnosticReport",
  ]);
  const [tokenExpiryMinutes, setTokenExpiryMinutes] = useState<number>(15);
  const [generatedToken, setGeneratedToken] = useState<EphemeralTokenState | null>(null);
  const [isMintingToken, setIsMintingToken] = useState<boolean>(false);

  // JSON Preview Modal
  const [inspectedArtifact, setInspectedArtifact] = useState<ActiveConsentArtifact | null>(null);

  const ALL_HITYPES = [
    "Prescription",
    "DiagnosticReport",
    "OPConsultation",
    "DischargeSummary",
    "ImmunizationRecord",
    "HealthDocumentRecord",
  ];

  const handleOpenGrantModal = (req: PendingConsentRequest) => {
    setSelectedRequest(req);
    setSelectedHiTypes([...req.hiTypes]);
    setDpdpConsentChecked(false);
    setModalOpen(true);
  };

  const toggleHiType = (type: string) => {
    if (selectedHiTypes.includes(type)) {
      setSelectedHiTypes(selectedHiTypes.filter((t) => t !== type));
    } else {
      setSelectedHiTypes([...selectedHiTypes, type]);
    }
  };

  const toggleTokenHiType = (type: string) => {
    if (tokenHiTypes.includes(type)) {
      setTokenHiTypes(tokenHiTypes.filter((t) => t !== type));
    } else {
      setTokenHiTypes([...tokenHiTypes, type]);
    }
  };

  const handleGrantConsent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest || !dpdpConsentChecked) return;

    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);

      const newArtifact: ActiveConsentArtifact = {
        artifactId: `ABDM-ART-20261104-${Math.floor(10000 + Math.random() * 90000)}`,
        relationshipId: "rel-proxy-child-8812",
        childName: selectedRequest.childName,
        childAbha: selectedRequest.childAbha,
        guardianName: "Sunita Sharma (Mother)",
        guardianRole: "PRN (Parent / Legal Guardian)",
        requesterFacility: selectedRequest.requesterFacility,
        purpose: selectedRequest.purpose,
        hiTypes: selectedHiTypes,
        status: "ACTIVE",
        grantedAt: "2026-11-04 14:15 IST",
        expiresAt: "2027-05-04 23:59 IST",
        digitalSignature: "9a01824c81029481b049182b0412984109481b049182b0412984109481b04901",
      };

      setArtifacts([newArtifact, ...artifacts]);
      setPendingRequests(pendingRequests.filter((r) => r.requestId !== selectedRequest.requestId));
      setModalOpen(false);
      setSelectedRequest(null);
    }, 700);
  };

  const handleDenyRequest = (requestId: string) => {
    setPendingRequests(pendingRequests.filter((r) => r.requestId !== requestId));
  };

  const handleOpenRevoke = (artifactId: string) => {
    setRevokingArtifactId(artifactId);
    setRevokeModalOpen(true);
  };

  const handleConfirmRevoke = () => {
    if (!revokingArtifactId) return;
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setArtifacts(
        artifacts.map((a) =>
          a.artifactId === revokingArtifactId ? { ...a, status: "REVOKED" } : a
        )
      );
      setRevokeModalOpen(false);
      setRevokingArtifactId(null);
    }, 500);
  };

  const handleMintScopedToken = (e: React.FormEvent) => {
    e.preventDefault();
    setIsMintingToken(true);
    setTimeout(() => {
      setIsMintingToken(false);
      const jti = `jti-proxy-${Date.now().toString().slice(-8)}`;
      const token = `eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdW5pdGEuc2hhcm1hQGFiZG0iLCJjaGlsZF9hYmhhIjoi${tokenChildAbha.replace(/-/g, "")}IiwianRpIjoi${jti}IiwiaGlfdHlwZXMiOlsi${tokenHiTypes.join('","')}\"],"cHVycG9zZSI6IiR7dG9rZW5QdXJwb3NlfSIsImV4cCI6MTgwMTY4NDAwMCwiaWF0IjoxODAxNjgzMTAwfQ.signature_verification_hash_sha256`;

      setGeneratedToken({
        token,
        tokenType: "Bearer",
        expiresInSeconds: tokenExpiryMinutes * 60,
        jti,
        allowedHiTypes: tokenHiTypes,
        purpose: tokenPurpose,
        childAbha: tokenChildAbha,
        issuedAt: "2026-11-04 14:30 IST",
      });
    }, 600);
  };

  return (
    <Card className="p-6 bg-white border border-[#e5e7eb] rounded-xl shadow-none font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#e5e7eb]">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] flex items-center justify-center shrink-0">
            <ShieldCheck className="w-5 h-5 text-[#111111]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-[#111111] tracking-tight">
                Guardian Consent Delegation & Scoped Token Interceptor
              </h2>
              <Badge variant="abdm">ABDM M3</Badge>
              <Badge variant="verified">DPDP ACT SEC 9</Badge>
            </div>
            <p className="text-xs text-[#6b7280] mt-1">
              Legal proxy authorization gateway for minor patients. Grants granular ABDM consent artifacts, verifies parent biometric attestations, and mints zero-leakage scoped tokens.
            </p>
          </div>
        </div>

        {/* Tab switchers */}
        <div className="flex items-center gap-1 bg-[#f9fafb] p-1 border border-[#e5e7eb] rounded-lg text-xs font-medium">
          <button
            onClick={() => setActiveTab("pending")}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "pending"
                ? "bg-white text-[#111111] shadow-xs border border-[#e5e7eb]"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            Pending Requests ({pendingRequests.length})
          </button>
          <button
            onClick={() => setActiveTab("active")}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "active"
                ? "bg-white text-[#111111] shadow-xs border border-[#e5e7eb]"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            Active Artifacts ({artifacts.filter((a) => a.status === "ACTIVE").length})
          </button>
          <button
            onClick={() => setActiveTab("token")}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "token"
                ? "bg-white text-[#111111] shadow-xs border border-[#e5e7eb]"
                : "text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            Scoped Token Console
          </button>
        </div>
      </div>

      {/* TAB 1: PENDING INBOUND CONSENT REQUESTS */}
      {activeTab === "pending" && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#111111] uppercase tracking-wider">
              Inbound ABDM Consent Requests for Dependent Minors
            </span>
            <span className="text-xs text-[#6b7280]">
              Requires Guardian Biometric/Demographic Attestation
            </span>
          </div>

          {pendingRequests.length === 0 ? (
            <div className="p-8 text-center border border-dashed border-[#e5e7eb] rounded-lg">
              <CheckCircle2 className="w-8 h-8 text-[#111111] mx-auto mb-2 opacity-60" />
              <p className="text-xs font-medium text-[#111111]">
                No pending consent requests for your dependents
              </p>
              <p className="text-xs text-[#6b7280] mt-1">
                Any incoming ABDM data exchange requests will appear here for guardian review.
              </p>
            </div>
          ) : (
            pendingRequests.map((req) => (
              <div
                key={req.requestId}
                className="p-4 rounded-lg border border-[#e5e7eb] bg-[#f9fafb] flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-[#111111]">
                      {req.requesterFacility}
                    </span>
                    <Badge variant="neutral">{req.purpose}</Badge>
                    <span className="text-xs text-[#6b7280]">
                      Requested at {req.requestedAt}
                    </span>
                  </div>

                  <p className="text-xs text-[#374151]">
                    <span className="font-medium text-[#111111]">{req.requesterName}</span> (
                    {req.requesterHpid}) is requesting records for{" "}
                    <span className="font-semibold text-[#111111]">{req.childName}</span> (ABHA:{" "}
                    <code className="text-[#111111] font-mono text-[11px]">{req.childAbha}</code>).
                  </p>

                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    <span className="text-xs text-[#6b7280] mr-1">HiTypes:</span>
                    {req.hiTypes.map((ht) => (
                      <span
                        key={ht}
                        className="px-2 py-0.5 rounded bg-white border border-[#e5e7eb] text-[11px] font-mono text-[#111111]"
                      >
                        {ht}
                      </span>
                    ))}
                    <span className="text-xs text-[#6b7280] ml-2">
                      Window: {req.dateFrom} to {req.dateTo}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDenyRequest(req.requestId)}
                    className="text-xs border-[#e5e7eb] text-[#374151] hover:text-[#111111]"
                  >
                    <Ban className="w-3.5 h-3.5 mr-1" />
                    Deny
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleOpenGrantModal(req)}
                    className="text-xs bg-[#111111] text-white hover:bg-[#222222]"
                  >
                    <UserCheck className="w-3.5 h-3.5 mr-1" />
                    Grant Delegated Consent
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* TAB 2: ACTIVE ARTIFACTS */}
      {activeTab === "active" && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#111111] uppercase tracking-wider">
              Enforced Consent Artifacts under DPDP Act 2023 Sec 9
            </span>
            <span className="text-xs text-[#6b7280]">Real-time Revocation Gateway</span>
          </div>

          {artifacts.length === 0 ? (
            <div className="p-8 text-center border border-dashed border-[#e5e7eb] rounded-lg">
              <AlertCircle className="w-8 h-8 text-[#6b7280] mx-auto mb-2" />
              <p className="text-xs font-medium text-[#111111]">No active consent artifacts</p>
            </div>
          ) : (
            artifacts.map((art) => (
              <div
                key={art.artifactId}
                className="p-4 rounded-lg border border-[#e5e7eb] bg-[#ffffff] space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-medium text-[#111111]">
                      {art.artifactId}
                    </span>
                    {art.status === "ACTIVE" ? (
                      <Badge variant="emerald">ACTIVE DELEGATION</Badge>
                    ) : (
                      <Badge variant="critical">REVOKED</Badge>
                    )}
                    <Badge variant="verified">SEC 9 ATTESTED</Badge>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setInspectedArtifact(art)}
                      className="text-xs text-[#6b7280] hover:text-[#111111] flex items-center gap-1"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      View Claims
                    </button>
                    {art.status === "ACTIVE" && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenRevoke(art.artifactId)}
                        className="text-xs text-[#b91c1c] border-[#fecaca] hover:bg-[#fef2f2]"
                      >
                        <Ban className="w-3.5 h-3.5 mr-1" />
                        Revoke
                      </Button>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs bg-[#f9fafb] p-3 rounded-lg border border-[#e5e7eb]">
                  <div>
                    <span className="text-[#6b7280] block">Dependent Minor</span>
                    <span className="font-medium text-[#111111]">{art.childName}</span>
                    <span className="block text-[11px] font-mono text-[#6b7280]">
                      {art.childAbha}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#6b7280] block">Authorizing Guardian</span>
                    <span className="font-medium text-[#111111]">{art.guardianName}</span>
                    <span className="block text-[11px] text-[#6b7280]">{art.guardianRole}</span>
                  </div>
                  <div>
                    <span className="text-[#6b7280] block">Recipient / Facility</span>
                    <span className="font-medium text-[#111111]">{art.requesterFacility}</span>
                    <span className="block text-[11px] text-[#6b7280]">
                      Purpose: {art.purpose}
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-xs">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-[#6b7280]">Allowed HiTypes:</span>
                    {art.hiTypes.map((ht) => (
                      <span
                        key={ht}
                        className="px-2 py-0.5 rounded bg-[#f9fafb] border border-[#e5e7eb] font-mono text-[11px] text-[#111111]"
                      >
                        {ht}
                      </span>
                    ))}
                  </div>
                  <div className="text-[#6b7280] text-[11px]">
                    Expires: <span className="font-medium text-[#111111]">{art.expiresAt}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* TAB 3: SCOPED EPHEMERAL TOKEN CONSOLE */}
      {activeTab === "token" && (
        <div className="mt-6 space-y-6">
          <div className="p-4 rounded-lg border border-[#e5e7eb] bg-[#f9fafb]">
            <h3 className="text-xs font-semibold text-[#111111] uppercase tracking-wider mb-1">
              Scoped Ephemeral Proxy Token Generator
            </h3>
            <p className="text-xs text-[#6b7280]">
              Issue time-bound, cryptographically isolated Bearer tokens for emergency pediatric triage or authorized proxy tele-consultations. Tokens carry strict claims binding preventing access to adult guardian records.
            </p>

            <form onSubmit={handleMintScopedToken} className="mt-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-[#111111] mb-1">
                    Dependent Child ABHA
                  </label>
                  <input
                    type="text"
                    value={tokenChildAbha}
                    onChange={(e) => setTokenChildAbha(e.target.value)}
                    className="w-full text-xs font-mono px-3 py-2 bg-white border border-[#e5e7eb] rounded-lg text-[#111111] focus:outline-hidden focus:border-[#111111]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#111111] mb-1">
                    Access Purpose Code
                  </label>
                  <select
                    value={tokenPurpose}
                    onChange={(e) => setTokenPurpose(e.target.value)}
                    className="w-full text-xs px-3 py-2 bg-white border border-[#e5e7eb] rounded-lg text-[#111111] focus:outline-hidden focus:border-[#111111]"
                  >
                    <option value="CARETREE">CARETREE (Care Management)</option>
                    <option value="BTG">BTG (Break-The-Glass Emergency)</option>
                    <option value="PUBHLTH">PUBHLTH (Public Health)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#111111] mb-1">
                    Token Lifetime (Minutes)
                  </label>
                  <select
                    value={tokenExpiryMinutes}
                    onChange={(e) => setTokenExpiryMinutes(Number(e.target.value))}
                    className="w-full text-xs px-3 py-2 bg-white border border-[#e5e7eb] rounded-lg text-[#111111] focus:outline-hidden focus:border-[#111111]"
                  >
                    <option value={15}>15 Minutes (Emergency Triage)</option>
                    <option value={30}>30 Minutes (Standard Consultation)</option>
                    <option value={60}>60 Minutes (Multi-Specialty Review)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#111111] mb-2">
                  Granular HiTypes Authorized
                </label>
                <div className="flex flex-wrap gap-2">
                  {ALL_HITYPES.map((ht) => (
                    <button
                      key={ht}
                      type="button"
                      onClick={() => toggleTokenHiType(ht)}
                      className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                        tokenHiTypes.includes(ht)
                          ? "bg-[#111111] text-white border-[#111111]"
                          : "bg-white text-[#6b7280] border-[#e5e7eb] hover:border-[#111111]"
                      }`}
                    >
                      {ht}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={isMintingToken || tokenHiTypes.length === 0}
                  className="text-xs bg-[#111111] text-white hover:bg-[#222222]"
                >
                  {isMintingToken ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                      Signing Token Claims...
                    </>
                  ) : (
                    <>
                      <Key className="w-3.5 h-3.5 mr-1.5" />
                      Issue Scoped Proxy Token
                    </>
                  )}
                </Button>
              </div>
            </form>
          </div>

          {generatedToken && (
            <div className="p-4 rounded-lg border border-[#e5e7eb] bg-white space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Key className="w-4 h-4 text-[#111111]" />
                  <span className="text-xs font-semibold text-[#111111]">
                    Issued Scoped Delegation Token
                  </span>
                  <Badge variant="emerald">VALID</Badge>
                </div>
                <div className="flex items-center gap-1 text-xs text-[#6b7280]">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Expires in {generatedToken.expiresInSeconds}s</span>
                </div>
              </div>

              <div>
                <span className="text-[11px] text-[#6b7280] block mb-1">Signed JWT Bearer</span>
                <div className="p-2.5 rounded bg-[#f9fafb] border border-[#e5e7eb] font-mono text-[11px] text-[#111111] break-all select-all">
                  {generatedToken.token}
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs pt-1">
                <div>
                  <span className="text-[#6b7280] block">Token ID (JTI)</span>
                  <span className="font-mono text-[11px] text-[#111111]">{generatedToken.jti}</span>
                </div>
                <div>
                  <span className="text-[#6b7280] block">Subject Minor</span>
                  <span className="font-mono text-[11px] text-[#111111]">
                    {generatedToken.childAbha}
                  </span>
                </div>
                <div>
                  <span className="text-[#6b7280] block">Purpose</span>
                  <span className="font-medium text-[#111111]">{generatedToken.purpose}</span>
                </div>
                <div>
                  <span className="text-[#6b7280] block">Issued At</span>
                  <span className="text-[11px] text-[#111111]">{generatedToken.issuedAt}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* MODAL: GRANT DELEGATED CONSENT */}
      {modalOpen && selectedRequest && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl border border-[#e5e7eb] max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-[#111111]" />
                <h3 className="text-sm font-semibold text-[#111111]">
                  Authorize Delegated Consent
                </h3>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="text-[#6b7280] hover:text-[#111111]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] space-y-1">
                <div className="font-medium text-[#111111]">
                  Recipient: {selectedRequest.requesterFacility}
                </div>
                <div className="text-[#6b7280]">
                  Doctor: {selectedRequest.requesterName} ({selectedRequest.requesterHpid})
                </div>
                <div className="text-[#6b7280]">
                  Target Minor: {selectedRequest.childName} ({selectedRequest.childAbha})
                </div>
              </div>

              <div>
                <label className="block font-medium text-[#111111] mb-1.5">
                  Authorize Select Health Information Types (HiTypes)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {ALL_HITYPES.map((ht) => (
                    <label
                      key={ht}
                      className={`flex items-center gap-2 p-2 rounded border cursor-pointer text-xs ${
                        selectedHiTypes.includes(ht)
                          ? "border-[#111111] bg-[#f9fafb] font-medium text-[#111111]"
                          : "border-[#e5e7eb] text-[#6b7280]"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedHiTypes.includes(ht)}
                        onChange={() => toggleHiType(ht)}
                        className="rounded border-[#e5e7eb] text-[#111111] focus:ring-0"
                      />
                      <span>{ht}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* DPDP ACT SEC 9 MANDATORY GUARDIAN ATTESTATION */}
              <div className="pt-2">
                <label className="flex items-start gap-2.5 p-3 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={dpdpConsentChecked}
                    onChange={(e) => setDpdpConsentChecked(e.target.checked)}
                    className="mt-0.5 rounded border-[#e5e7eb] text-[#111111] focus:ring-0"
                  />
                  <div className="text-xs text-[#374151] leading-relaxed">
                    <span className="font-semibold text-[#111111] block mb-0.5">
                      DPDP Act 2023 Section 9 Guardian Attestation
                    </span>
                    I hereby certify under penalty of applicable law that I am the verified parent / legal guardian of the named minor patient. I authorize the transmission of the selected records solely for the clinical purpose stated, and acknowledge that all data transactions are logged in the immutable ABDM audit ledger.
                  </div>
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#e5e7eb]">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setModalOpen(false)}
                className="text-xs border-[#e5e7eb]"
              >
                Cancel
              </Button>
              <Button
                size="sm"
                disabled={!dpdpConsentChecked || selectedHiTypes.length === 0 || isSubmitting}
                onClick={handleGrantConsent}
                className="text-xs bg-[#111111] text-white hover:bg-[#222222]"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                    Generating Consent Artifact...
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-3.5 h-3.5 mr-1.5" />
                    Sign and Grant Consent
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: REVOKE CONSENT */}
      {revokeModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl border border-[#e5e7eb] max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <Ban className="w-5 h-5 text-[#b91c1c]" />
                <h3 className="text-sm font-semibold text-[#111111]">
                  Revoke Consent Artifact
                </h3>
              </div>
              <button
                onClick={() => setRevokeModalOpen(false)}
                className="text-[#6b7280] hover:text-[#111111]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <p className="text-[#374151]">
                Are you sure you want to revoke consent artifact{" "}
                <code className="font-mono text-[#111111]">{revokingArtifactId}</code>? Once revoked, the healthcare facility will lose access immediately, and any downstream token will be invalidated.
              </p>

              <div>
                <label className="block font-medium text-[#111111] mb-1">
                  Revocation Reason
                </label>
                <input
                  type="text"
                  value={revokeReason}
                  onChange={(e) => setRevokeReason(e.target.value)}
                  className="w-full px-3 py-2 border border-[#e5e7eb] rounded-lg text-xs text-[#111111] focus:outline-hidden focus:border-[#111111]"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#e5e7eb]">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setRevokeModalOpen(false)}
                className="text-xs border-[#e5e7eb]"
              >
                Cancel
              </Button>
              <Button
                size="sm"
                disabled={isSubmitting}
                onClick={handleConfirmRevoke}
                className="text-xs bg-[#b91c1c] text-white hover:bg-[#991b1b]"
              >
                {isSubmitting ? "Revoking..." : "Confirm Immediate Revocation"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: VIEW ARTIFACT CLAIMS */}
      {inspectedArtifact && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl border border-[#e5e7eb] max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <FileCode className="w-5 h-5 text-[#111111]" />
                <h3 className="text-sm font-semibold text-[#111111]">
                  ABDM Consent Artifact Manifest
                </h3>
              </div>
              <button
                onClick={() => setInspectedArtifact(null)}
                className="text-[#6b7280] hover:text-[#111111]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 bg-[#f9fafb] border border-[#e5e7eb] rounded-lg font-mono text-[11px] text-[#111111] overflow-x-auto max-h-72">
              <pre>{JSON.stringify(inspectedArtifact, null, 2)}</pre>
            </div>

            <div className="flex items-center justify-end pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setInspectedArtifact(null)}
                className="text-xs border-[#e5e7eb]"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
