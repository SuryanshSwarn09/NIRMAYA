"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  AlertCircle,
  CheckCircle2,
  FileCheck,
  FileText,
  History,
  Lock,
  RefreshCw,
  Scale,
  ShieldCheck,
  Unlock,
  Users,
} from "lucide-react";

export type CustodyMode = "JOINT_CONCURRENT" | "DUAL_SIGNATURE_REQUIRED" | "DISPUTED_LOCKED";

export interface GuardianItem {
  guardianId: string;
  name: string;
  relationship: string;
  tier: string;
  priorityTier: number;
  authorizedAt: string;
}

export interface DisputeRecord {
  ticketId: string;
  initiatingGuardian: string;
  status: "ACTIVE_DISPUTE" | "COURT_SUB_JUDICE" | "RESOLVED";
  legalOrderRef?: string;
  justification: string;
  timestamp: string;
}

export interface DualSignItem {
  artifactId: string;
  dependentName: string;
  purpose: string;
  primaryGuardianName: string;
  coGuardianName: string;
  status: "PENDING_CO_SIGNATURE" | "FULLY_AUTHORIZED" | "REJECTED";
  primarySignatureHash: string;
  coSignatureHash?: string;
  compositeSignatureHash?: string;
  createdAt: string;
  authorizedAt?: string;
}

export interface AuditLedgerItem {
  ticketId: string;
  action: string;
  policy: string;
  result: string;
  auditHash: string;
  timestamp: string;
}

const INITIAL_GUARDIANS: GuardianItem[] = [
  {
    guardianId: "pat-priya-sharma-01",
    name: "Dr. Priya Sharma",
    relationship: "MOTHER",
    tier: "DIGILOCKER_BIRTH_CERTIFICATE",
    priorityTier: 1,
    authorizedAt: "2026-09-01 09:00 IST",
  },
  {
    guardianId: "pat-vikram-sharma-01",
    name: "Vikram Sharma",
    relationship: "FATHER",
    tier: "AADHAAR_DEMOGRAPHIC_EKYC",
    priorityTier: 1,
    authorizedAt: "2026-09-05 14:30 IST",
  },
];

const INITIAL_DUAL_SIGNS: DualSignItem[] = [
  {
    artifactId: "art-dual-seed-001",
    dependentName: "Aarav Sharma (Minor 8 yrs)",
    purpose: "CAREMGT (Chronic Pediatric Care Management)",
    primaryGuardianName: "Dr. Priya Sharma (Mother)",
    coGuardianName: "Vikram Sharma (Father)",
    status: "PENDING_CO_SIGNATURE",
    primarySignatureHash: "9a2f7c01b45de89a034f1982bca8492048f72a19e83049b8192a0934f81048b2",
    createdAt: "2026-11-06 09:15 IST",
  },
];

const INITIAL_AUDIT_LOGS: AuditLedgerItem[] = [
  {
    ticketId: "ticket-arb-init-01",
    action: "INITIAL_CONCURRENT_AUTH",
    policy: "PRIMARY_GUARDIAN_ARBITRATION",
    result: "Joint concurrent guardianship established for Aarav Sharma.",
    auditHash: "f1a8c9283948b819284918249182491824918294819284192849182948192849",
    timestamp: "2026-09-05 14:35 IST",
  },
];

export function MultiGuardianConflictResolutionCard() {
  const [activeTab, setActiveTab] = useState<"matrix" | "governance" | "dualsign" | "audit">("matrix");
  const [custodyMode, setCustodyMode] = useState<CustodyMode>("JOINT_CONCURRENT");
  const [guardians] = useState<GuardianItem[]>(INITIAL_GUARDIANS);
  const [disputes, setDisputes] = useState<DisputeRecord[]>([]);
  const [dualSignItems, setDualSignItems] = useState<DualSignItem[]>(INITIAL_DUAL_SIGNS);
  const [auditLogs, setAuditLogs] = useState<AuditLedgerItem[]>(INITIAL_AUDIT_LOGS);
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);
  const [bannerType, setBannerType] = useState<"success" | "warning" | "critical">("success");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  // Unilateral Revocation Simulation (Pessimistic Revocation Invariant)
  const handleSimulateRevocation = () => {
    setIsProcessing(true);
    setTimeout(() => {
      const ticketId = `ticket-rev-${Math.random().toString(36).substring(2, 8)}`;
      const now = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
      const auditHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("");

      setAuditLogs((prev) => [
        {
          ticketId,
          action: "REVOKE_CONSENT",
          policy: "PESSIMISTIC_REVOCATION_PREVALENCE",
          result: "Pessimistic Revocation Prevailed: Target consent artifact unilaterally and immediately revoked across all guardian sessions.",
          auditHash,
          timestamp: now,
        },
        ...prev,
      ]);

      setBannerType("success");
      setBannerMessage(
        "Pessimistic Revocation Invariant Enforced: Revocation by Vikram Sharma immediately revoked consent across all sessions. Zero unauthorized proxy reads permitted."
      );
      setIsProcessing(false);
    }, 400);
  };

  // Legal Dispute Contest Simulation (Sub-Judice Lock)
  const handleRaiseDispute = () => {
    setIsProcessing(true);
    setTimeout(() => {
      const ticketId = `ticket-disp-${Math.random().toString(36).substring(2, 8)}`;
      const now = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
      const auditHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("");

      const newDispute: DisputeRecord = {
        ticketId,
        initiatingGuardian: "Vikram Sharma (Father)",
        status: "COURT_SUB_JUDICE",
        legalOrderRef: "HC-DEL-FAM-2026-90412",
        justification: "Custodial contest filed in High Court of Delhi under Guardians and Wards Act 1890 Section 7.",
        timestamp: now,
      };

      setDisputes((prev) => [newDispute, ...prev]);
      setCustodyMode("DISPUTED_LOCKED");

      setAuditLogs((prev) => [
        {
          ticketId,
          action: "RAISE_LEGAL_DISPUTE",
          policy: "DISPUTED_CUSTODY_FREEZE",
          result: "Custodial dispute registered under HC-DEL-FAM-2026-90412. All non-emergency proxy modifications locked.",
          auditHash,
          timestamp: now,
        },
        ...prev,
      ]);

      setBannerType("critical");
      setBannerMessage(
        "Custodial Dispute Registered: Automatic pessimistic freeze engaged under Court Sub-Judice. Non-emergency proxy access is locked. Life-saving Break-The-Glass access remains preserved."
      );
      setIsProcessing(false);
    }, 400);
  };

  // Dispute Resolution Simulation
  const handleResolveDispute = () => {
    setIsProcessing(true);
    setTimeout(() => {
      const ticketId = `ticket-res-${Math.random().toString(36).substring(2, 8)}`;
      const now = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
      const auditHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("");

      setDisputes((prev) =>
        prev.map((d) => (d.status !== "RESOLVED" ? { ...d, status: "RESOLVED" } : d))
      );
      setCustodyMode("JOINT_CONCURRENT");

      setAuditLogs((prev) => [
        {
          ticketId,
          action: "RESOLVE_DISPUTE",
          policy: "PRIMARY_GUARDIAN_ARBITRATION",
          result: "Dispute resolved by mutual court settlement. Governance restored to JOINT_CONCURRENT.",
          auditHash,
          timestamp: now,
        },
        ...prev,
      ]);

      setBannerType("success");
      setBannerMessage("Dispute Resolved: Custodial lock cleared. Joint concurrent governance restored.");
      setIsProcessing(false);
    }, 400);
  };

  // Counter-Sign Dual-Sign Artifact
  const handleCounterSign = (artifactId: string) => {
    setIsProcessing(true);
    setTimeout(() => {
      const now = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
      const coSigHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
      const compositeHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("");

      setDualSignItems((prev) =>
        prev.map((item) =>
          item.artifactId === artifactId
            ? {
                ...item,
                status: "FULLY_AUTHORIZED",
                coSignatureHash: coSigHash,
                compositeSignatureHash: compositeHash,
                authorizedAt: now,
              }
            : item
        )
      );

      setAuditLogs((prev) => [
        {
          ticketId: `ticket-ds-${Math.random().toString(36).substring(2, 8)}`,
          action: "DUAL_SIGN_COMPLETED",
          policy: "DUAL_GUARDIAN_CO_SIGNING",
          result: `Artifact ${artifactId} fully authorized with composite cryptographic signature.`,
          auditHash: compositeHash,
          timestamp: now,
        },
        ...prev,
      ]);

      setBannerType("success");
      setBannerMessage(
        `Dual-Sign Authorization Complete: Second guardian counter-signature registered. Composite signature: ${compositeHash.substring(0, 16)}...`
      );
      setIsProcessing(false);
    }, 400);
  };

  return (
    <Card variant="default" className="border-[#e5e7eb] bg-white p-6 shadow-sm">
      {/* Header Section */}
      <div className="flex flex-col gap-3 pb-6 border-b border-[#e5e7eb] sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Scale className="h-5 w-5 text-[#111111]" />
            <h2 className="text-lg font-semibold tracking-tight text-[#111111]">
              Multi-Guardian Concurrency and Conflict Resolution Engine
            </h2>
          </div>
          <p className="mt-1 text-xs text-[#6b7280]">
            Pessimistic revocation prevalence and custodial dispute state machine under DPDP Act 2023 Sec 9 and Guardians & Wards Act 1890
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {custodyMode === "JOINT_CONCURRENT" && (
            <Badge variant="emerald" size="sm">
              JOINT CONCURRENT
            </Badge>
          )}
          {custodyMode === "DUAL_SIGNATURE_REQUIRED" && (
            <Badge variant="warning" size="sm">
              DUAL SIGN REQUIRED
            </Badge>
          )}
          {custodyMode === "DISPUTED_LOCKED" && (
            <Badge variant="critical" size="sm">
              DISPUTED LOCKED
            </Badge>
          )}
          <Badge variant="verified" size="sm">
            DPDP SEC 9
          </Badge>
          <Badge variant="neutral" size="sm">
            PESSIMISTIC PREVALENCE
          </Badge>
        </div>
      </div>

      {/* Dynamic Feedback Banner */}
      {bannerMessage && (
        <div
          className={`mt-4 rounded-lg p-3 text-xs border ${
            bannerType === "critical"
              ? "bg-[#fef2f2] text-[#991b1b] border-[#fecaca]"
              : bannerType === "warning"
              ? "bg-[#fff7ed] text-[#ea580c] border-[#fed7aa]"
              : "bg-[#ecfdf5] text-[#065f46] border-[#a7f3d0]"
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              {bannerType === "critical" ? (
                <Lock className="h-4 w-4 shrink-0" />
              ) : (
                <CheckCircle2 className="h-4 w-4 shrink-0" />
              )}
              <span>{bannerMessage}</span>
            </div>
            <button
              onClick={() => setBannerMessage(null)}
              className="text-xs font-semibold hover:underline ml-2"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="mt-6 flex border-b border-[#e5e7eb] gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab("matrix")}
          className={`pb-2.5 transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
            activeTab === "matrix"
              ? "border-[#111111] text-[#111111] font-semibold"
              : "border-transparent text-[#6b7280] hover:text-[#111111]"
          }`}
        >
          <Users className="h-4 w-4" />
          Guardian Matrix
        </button>
        <button
          onClick={() => setActiveTab("governance")}
          className={`pb-2.5 transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
            activeTab === "governance"
              ? "border-[#111111] text-[#111111] font-semibold"
              : "border-transparent text-[#6b7280] hover:text-[#111111]"
          }`}
        >
          <ShieldCheck className="h-4 w-4" />
          Custody Governance & Policies
        </button>
        <button
          onClick={() => setActiveTab("dualsign")}
          className={`pb-2.5 transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
            activeTab === "dualsign"
              ? "border-[#111111] text-[#111111] font-semibold"
              : "border-transparent text-[#6b7280] hover:text-[#111111]"
          }`}
        >
          <FileCheck className="h-4 w-4" />
          Dual-Sign Queue ({dualSignItems.filter((i) => i.status === "PENDING_CO_SIGNATURE").length})
        </button>
        <button
          onClick={() => setActiveTab("audit")}
          className={`pb-2.5 transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
            activeTab === "audit"
              ? "border-[#111111] text-[#111111] font-semibold"
              : "border-transparent text-[#6b7280] hover:text-[#111111]"
          }`}
        >
          <History className="h-4 w-4" />
          Forensic Audit Ledger ({auditLogs.length})
        </button>
      </div>

      {/* Tab 1: Guardian Matrix */}
      {activeTab === "matrix" && (
        <div className="mt-6 space-y-6">
          {/* Target Dependent Context Card */}
          <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <span className="text-xs uppercase font-medium text-[#6b7280]">Target Dependent Record</span>
              <div className="text-sm font-semibold text-[#111111]">Aarav Sharma (Son, Minor 8 yrs)</div>
              <div className="text-xs text-[#6b7280]">ABHA: 14-8291-0391-4821 | DOB: 2018-06-15</div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="verified" size="sm">
                VERIFIED MINOR PROXY
              </Badge>
              {custodyMode === "DISPUTED_LOCKED" ? (
                <Badge variant="critical" size="sm">
                  CUSTODY FROZEN
                </Badge>
              ) : (
                <Badge variant="emerald" size="sm">
                  CONCURRENT ACTIVE
                </Badge>
              )}
            </div>
          </div>

          {/* Concurrent Guardians Grid */}
          <div>
            <div className="text-xs uppercase font-semibold tracking-wider text-[#6b7280] mb-3">
              Registered Concurrent Guardians (2 Authorized)
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {guardians.map((g) => (
                <div
                  key={g.guardianId}
                  className="rounded-lg border border-[#e5e7eb] bg-white p-4 shadow-sm hover:border-[#111111] transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-semibold text-sm text-[#111111]">{g.name}</div>
                      <div className="text-xs text-[#6b7280]">{g.relationship} | Priority Tier {g.priorityTier}</div>
                    </div>
                    <Badge variant="verified" size="sm">
                      {g.tier === "DIGILOCKER_BIRTH_CERTIFICATE" ? "DIGILOCKER" : "AADHAAR E-KYC"}
                    </Badge>
                  </div>

                  <div className="mt-3 pt-3 border-t border-[#e5e7eb] text-xs space-y-1 text-[#6b7280]">
                    <div>Authority ID: <code className="text-[#111111]">{g.guardianId}</code></div>
                    <div>Authorized Since: {g.authorizedAt}</div>
                    <div>Digital Attestation: <span className="text-[#065f46] font-medium">DPDP Sec 9 Enforced</span></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Simulation Console */}
          <div className="rounded-lg border border-[#e5e7eb] bg-white p-5">
            <div className="text-sm font-semibold text-[#111111] mb-1">
              Arbitration & Conflict Simulator
            </div>
            <p className="text-xs text-[#6b7280] mb-4">
              Test deterministic conflict resolution rules against simulated multi-guardian actions.
            </p>

            <div className="flex flex-wrap gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleSimulateRevocation}
                disabled={isProcessing}
                className="text-xs"
              >
                <RefreshCw className="mr-1.5 h-3.5 w-3.5 text-[#111111]" />
                Simulate Unilateral Revocation (Pessimistic Prevalence)
              </Button>

              {custodyMode !== "DISPUTED_LOCKED" ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRaiseDispute}
                  disabled={isProcessing}
                  className="text-xs border-[#ef4444] text-[#991b1b] hover:bg-[#fef2f2]"
                >
                  <Lock className="mr-1.5 h-3.5 w-3.5" />
                  Simulate Custody Contest (Court Sub-Judice)
                </Button>
              ) : (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleResolveDispute}
                  disabled={isProcessing}
                  className="text-xs"
                >
                  <Unlock className="mr-1.5 h-3.5 w-3.5" />
                  Simulate Dispute Resolution (Restore Joint Custody)
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Custody Governance & Policies */}
      {activeTab === "governance" && (
        <div className="mt-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-lg border border-[#e5e7eb] p-4 bg-[#f9fafb]">
              <div className="flex items-center gap-2 mb-2">
                <ShieldCheck className="h-4 w-4 text-[#111111]" />
                <span className="text-sm font-semibold text-[#111111]">Pessimistic Revocation Invariant</span>
              </div>
              <p className="text-xs text-[#6b7280] leading-relaxed">
                Under privacy-preserving digital guardianship, any revocation by any verified guardian immediately revokes the consent artifact, regardless of which guardian originally granted it. Revocation always takes precedence over consent grant.
              </p>
            </div>

            <div className="rounded-lg border border-[#e5e7eb] p-4 bg-[#f9fafb]">
              <div className="flex items-center gap-2 mb-2">
                <Lock className="h-4 w-4 text-[#111111]" />
                <span className="text-sm font-semibold text-[#111111]">Custodial Dispute Freeze</span>
              </div>
              <p className="text-xs text-[#6b7280] leading-relaxed">
                Under Guardians and Wards Act 1890, when a court contest or legal dispute is active, non-emergency proxy access is automatically frozen to prevent unilateral exfiltration. Emergency Break-The-Glass remains active.
              </p>
            </div>

            <div className="rounded-lg border border-[#e5e7eb] p-4 bg-[#f9fafb]">
              <div className="flex items-center gap-2 mb-2">
                <FileCheck className="h-4 w-4 text-[#111111]" />
                <span className="text-sm font-semibold text-[#111111]">Dual-Guardian Co-Signing</span>
              </div>
              <p className="text-xs text-[#6b7280] leading-relaxed">
                For major medical decisions, major diagnostic disclosures, or when selected by the family, both guardians must counter-sign using SHA-256 composite signatures before the consent artifact is activated.
              </p>
            </div>

            <div className="rounded-lg border border-[#e5e7eb] p-4 bg-[#f9fafb]">
              <div className="flex items-center gap-2 mb-2">
                <Scale className="h-4 w-4 text-[#111111]" />
                <span className="text-sm font-semibold text-[#111111]">Priority Tier Arbitration</span>
              </div>
              <p className="text-xs text-[#6b7280] leading-relaxed">
                When conflicting affirmative instructions are submitted under normal operations, Priority 1 natural guardians (Mother/Father) take precedence over secondary welfare proxies.
              </p>
            </div>
          </div>

          {/* Mode Switcher */}
          <div className="rounded-lg border border-[#e5e7eb] p-5 bg-white">
            <div className="text-sm font-semibold text-[#111111] mb-2">
              Select Governance Custody Mode
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => setCustodyMode("JOINT_CONCURRENT")}
                className={`rounded-lg px-4 py-2.5 text-xs font-medium border transition-colors ${
                  custodyMode === "JOINT_CONCURRENT"
                    ? "border-[#111111] bg-[#111111] text-white"
                    : "border-[#e5e7eb] bg-white text-[#111111] hover:bg-[#f9fafb]"
                }`}
              >
                Joint Concurrent (Default)
              </button>
              <button
                onClick={() => setCustodyMode("DUAL_SIGNATURE_REQUIRED")}
                className={`rounded-lg px-4 py-2.5 text-xs font-medium border transition-colors ${
                  custodyMode === "DUAL_SIGNATURE_REQUIRED"
                    ? "border-[#111111] bg-[#111111] text-white"
                    : "border-[#e5e7eb] bg-white text-[#111111] hover:bg-[#f9fafb]"
                }`}
              >
                Dual-Signature Required (Co-Signing)
              </button>
              <button
                onClick={() => setCustodyMode("DISPUTED_LOCKED")}
                className={`rounded-lg px-4 py-2.5 text-xs font-medium border transition-colors ${
                  custodyMode === "DISPUTED_LOCKED"
                    ? "border-[#ef4444] bg-[#ef4444] text-white"
                    : "border-[#e5e7eb] bg-white text-[#111111] hover:bg-[#f9fafb]"
                }`}
              >
                Disputed Locked (Legal Freeze)
              </button>
            </div>
          </div>

          {/* Active Disputes List */}
          {disputes.length > 0 && (
            <div className="space-y-3">
              <div className="text-xs uppercase font-semibold tracking-wider text-[#6b7280]">
                Active Custodial Dispute Tickets
              </div>
              {disputes.map((d) => (
                <div
                  key={d.ticketId}
                  className="rounded-lg border border-[#fecaca] bg-[#fef2f2] p-4 text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-[#991b1b]">{d.ticketId}</span>
                    <Badge variant={d.status === "RESOLVED" ? "emerald" : "critical"} size="sm">
                      {d.status}
                    </Badge>
                  </div>
                  <div className="text-[#111111]">Filing Guardian: {d.initiatingGuardian}</div>
                  {d.legalOrderRef && (
                    <div className="text-[#111111]">Court Order Ref: <code className="font-mono">{d.legalOrderRef}</code></div>
                  )}
                  <div className="text-[#6b7280]">{d.justification}</div>
                  <div className="text-[#6b7280] text-[11px] pt-1">Logged: {d.timestamp}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Dual-Sign Queue */}
      {activeTab === "dualsign" && (
        <div className="mt-6 space-y-4">
          <div className="text-xs text-[#6b7280]">
            Consent artifacts requiring counter-signatures from secondary registered guardians before activation.
          </div>

          {dualSignItems.map((item) => (
            <div
              key={item.artifactId}
              className="rounded-lg border border-[#e5e7eb] bg-white p-5 shadow-sm space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <div className="font-semibold text-sm text-[#111111]">{item.artifactId}</div>
                  <div className="text-xs text-[#6b7280]">{item.dependentName}</div>
                </div>
                <Badge
                  variant={item.status === "FULLY_AUTHORIZED" ? "emerald" : "warning"}
                  size="sm"
                >
                  {item.status === "FULLY_AUTHORIZED" ? "FULLY AUTHORIZED" : "PENDING CO-SIGNATURE"}
                </Badge>
              </div>

              <div className="text-xs space-y-1 bg-[#f9fafb] p-3 rounded border border-[#e5e7eb]">
                <div><span className="text-[#6b7280]">Clinical Purpose:</span> {item.purpose}</div>
                <div><span className="text-[#6b7280]">Initiator:</span> {item.primaryGuardianName}</div>
                <div><span className="text-[#6b7280]">Designated Co-Guardian:</span> {item.coGuardianName}</div>
                <div className="pt-1 font-mono text-[11px] text-[#6b7280] truncate">
                  Primary Signature Hash: {item.primarySignatureHash}
                </div>
                {item.compositeSignatureHash && (
                  <div className="font-mono text-[11px] text-[#065f46] truncate">
                    Composite SHA-256 Hash: {item.compositeSignatureHash}
                  </div>
                )}
              </div>

              {item.status === "PENDING_CO_SIGNATURE" && (
                <div className="flex justify-end pt-2">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleCounterSign(item.artifactId)}
                    disabled={isProcessing}
                    className="text-xs"
                  >
                    <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" />
                    Counter-Sign as Vikram Sharma (Co-Guardian)
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Tab 4: Forensic Audit Ledger */}
      {activeTab === "audit" && (
        <div className="mt-6 space-y-3">
          <div className="text-xs text-[#6b7280]">
            Cryptographic SHA-256 forensic audit trail of multi-guardian arbitration decisions.
          </div>

          <div className="divide-y divide-[#e5e7eb] rounded-lg border border-[#e5e7eb] bg-white">
            {auditLogs.map((log) => (
              <div key={log.ticketId} className="p-3.5 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#111111]">{log.action}</span>
                  <span className="text-[#6b7280] text-[11px]">{log.timestamp}</span>
                </div>
                <div className="text-[#6b7280]">
                  Ticket: <code className="text-[#111111]">{log.ticketId}</code> | Policy: <span className="font-medium text-[#111111]">{log.policy}</span>
                </div>
                <div className="text-[#111111]">{log.result}</div>
                <div className="font-mono text-[10px] text-[#6b7280] truncate">
                  SHA-256: {log.auditHash}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
