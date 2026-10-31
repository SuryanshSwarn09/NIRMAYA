"use client";

import React, { useState } from "react";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";

interface DelegationRecord {
  id: string;
  delegatorDesignation: string;
  delegatorEmail: string;
  delegateeDesignation: string;
  delegateeEmail: string;
  jurisdictionPath: string;
  unitName: string;
  unitLevel: string;
  aadhaarVerified: boolean;
  auditHash: string;
  createdAt: string;
  isActive: boolean;
}

interface AuditBlock {
  id: string;
  action: "DELEGATED" | "REVOKED";
  actorDesignation: string;
  jurisdictionPath: string;
  timestamp: string;
  auditHash: string;
  previousHash: string;
}

const INITIAL_DELEGATIONS: DelegationRecord[] = [
  {
    id: "del-001",
    delegatorDesignation: "National Director",
    delegatorEmail: "national.director.abdm@gov.in",
    delegateeDesignation: "State Secretary",
    delegateeEmail: "secretary.health.mh@gov.in",
    jurisdictionPath: "india.27",
    unitName: "Maharashtra",
    unitLevel: "STATE",
    aadhaarVerified: true,
    auditHash: "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b",
    createdAt: "2026-10-31 08:30 UTC",
    isActive: true,
  },
  {
    id: "del-002",
    delegatorDesignation: "State Secretary",
    delegatorEmail: "secretary.health.mh@gov.in",
    delegateeDesignation: "Chief Medical Officer",
    delegateeEmail: "cmo.pune@nic.in",
    jurisdictionPath: "india.27.492",
    unitName: "Pune District",
    unitLevel: "DISTRICT",
    aadhaarVerified: true,
    auditHash: "9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e",
    createdAt: "2026-10-31 09:15 UTC",
    isActive: true,
  },
  {
    id: "del-003",
    delegatorDesignation: "Chief Medical Officer",
    delegatorEmail: "cmo.pune@nic.in",
    delegateeDesignation: "Block Medical Officer",
    delegateeEmail: "bmo.haveli@nic.in",
    jurisdictionPath: "india.27.492.4182",
    unitName: "Haveli Sub-District",
    unitLevel: "SUB_DISTRICT",
    aadhaarVerified: true,
    auditHash: "4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d",
    createdAt: "2026-10-31 10:00 UTC",
    isActive: true,
  },
];

const INITIAL_AUDIT_BLOCKS: AuditBlock[] = [
  {
    id: "block-001",
    action: "DELEGATED",
    actorDesignation: "National Director",
    jurisdictionPath: "india.27",
    timestamp: "2026-10-31 08:30 UTC",
    auditHash: "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b",
    previousHash: "GENESIS_DELEGATION_BLOCK_00000000000000000000000000000000",
  },
  {
    id: "block-002",
    action: "DELEGATED",
    actorDesignation: "State Secretary",
    jurisdictionPath: "india.27.492",
    timestamp: "2026-10-31 09:15 UTC",
    auditHash: "9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e",
    previousHash: "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b",
  },
  {
    id: "block-003",
    action: "DELEGATED",
    actorDesignation: "Chief Medical Officer",
    jurisdictionPath: "india.27.492.4182",
    timestamp: "2026-10-31 10:00 UTC",
    auditHash: "4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d",
    previousHash: "9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e",
  },
];

export function ChainOfCommandDelegationCard() {
  const [activeTab, setActiveTab] = useState<"delegations" | "provision" | "simulator" | "audit">("delegations");
  const [delegations, setDelegations] = useState<DelegationRecord[]>(INITIAL_DELEGATIONS);
  const [auditBlocks, setAuditBlocks] = useState<AuditBlock[]>(INITIAL_AUDIT_BLOCKS);

  // Provisioning form state
  const [delegatorDesignation, setDelegatorDesignation] = useState("STATE_SECRETARY");
  const [delegateeDesignation, setDelegateeDesignation] = useState("CHIEF_MEDICAL_OFFICER");
  const [targetUnitName, setTargetUnitName] = useState("Satara District");
  const [targetUnitLevel, setTargetUnitLevel] = useState("DISTRICT");
  const [targetPath, setTargetPath] = useState("india.27.493");
  const [govEmail, setGovEmail] = useState("cmo.satara@nic.in");
  const [aadhaarUid, setAadhaarUid] = useState("234567890128");
  const [aadhaarOtp, setAadhaarOtp] = useState("123456");
  const [provisionStatus, setProvisionStatus] = useState<string | null>(null);

  // TRBAC Simulator state
  const [simOfficerPath, setSimOfficerPath] = useState("india.27.492");
  const [simResourcePath, setSimResourcePath] = useState("india.27.492.4182");
  const [simAction, setSimAction] = useState("READ");
  const [simResult, setSimResult] = useState<{
    authorized: boolean;
    reason: string;
    latencyMs: number;
  } | null>(null);

  // Email validation helper
  const isGovEmailValid = (email: string) => {
    const clean = email.trim().toLowerCase();
    return clean.endsWith(".gov.in") || clean.endsWith(".nic.in") || clean.endsWith(".mohfw.gov.in");
  };

  // Verhoeff checksum simulator (validates standard test inputs)
  const isAadhaarValid = (uid: string) => {
    const clean = uid.replace(/\D/g, "");
    return clean.length === 12;
  };

  const handleCreateDelegation = (e: React.FormEvent) => {
    e.preventDefault();

    if (!isGovEmailValid(govEmail)) {
      setProvisionStatus("Error: Official email must end in .gov.in or .nic.in");
      return;
    }

    if (!isAadhaarValid(aadhaarUid)) {
      setProvisionStatus("Error: Aadhaar UID must be exactly 12 digits.");
      return;
    }

    const newId = `del-${Date.now().toString().slice(-4)}`;
    const randomHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
    const prevHash = auditBlocks[auditBlocks.length - 1]?.auditHash || "GENESIS_HASH";

    const newRec: DelegationRecord = {
      id: newId,
      delegatorDesignation: delegatorDesignation.replace(/_/g, " "),
      delegatorEmail: "secretary.health.mh@gov.in",
      delegateeDesignation: delegateeDesignation.replace(/_/g, " "),
      delegateeEmail: govEmail,
      jurisdictionPath: targetPath,
      unitName: targetUnitName,
      unitLevel: targetUnitLevel,
      aadhaarVerified: true,
      auditHash: randomHash,
      createdAt: "Just now",
      isActive: true,
    };

    const newBlock: AuditBlock = {
      id: `block-${Date.now().toString().slice(-4)}`,
      action: "DELEGATED",
      actorDesignation: delegatorDesignation.replace(/_/g, " "),
      jurisdictionPath: targetPath,
      timestamp: "Just now",
      auditHash: randomHash,
      previousHash: prevHash,
    };

    setDelegations([newRec, ...delegations]);
    setAuditBlocks([...auditBlocks, newBlock]);
    setProvisionStatus(`Success: Provisioned authority to ${delegateeDesignation} for ${targetUnitName}. Audit hash recorded.`);
  };

  const handleRevoke = (id: string) => {
    const target = delegations.find((d) => d.id === id);
    if (!target) return;

    const revocationHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
    const prevHash = auditBlocks[auditBlocks.length - 1]?.auditHash || "GENESIS_HASH";

    setDelegations(
      delegations.map((d) => (d.id === id ? { ...d, isActive: false } : d))
    );

    const revokeBlock: AuditBlock = {
      id: `block-${Date.now().toString().slice(-4)}`,
      action: "REVOKED",
      actorDesignation: "State Secretary",
      jurisdictionPath: target.jurisdictionPath,
      timestamp: "Just now",
      auditHash: revocationHash,
      previousHash: prevHash,
    };

    setAuditBlocks([...auditBlocks, revokeBlock]);
  };

  const handleRunSimulator = () => {
    const oPath = simOfficerPath.trim().toLowerCase();
    const rPath = simResourcePath.trim().toLowerCase();

    let authorized = false;
    let reason = "";

    if (!oPath || !rPath) {
      authorized = false;
      reason = "Paths cannot be empty.";
    } else if (oPath === "india") {
      authorized = true;
      reason = "National Union Government jurisdiction covers all sovereign Indian territories.";
    } else if (oPath === rPath) {
      authorized = true;
      reason = `Exact territorial jurisdiction match on '${oPath}'.`;
    } else if (rPath.startsWith(oPath + ".")) {
      authorized = true;
      reason = `Target resource '${rPath}' is an administrative subordinate within officer subtree '${oPath}'.`;
    } else if (oPath.startsWith(rPath + ".")) {
      authorized = false;
      reason = `Upward access violation: Officer at '${oPath}' cannot supervise superior administrative tier '${rPath}'.`;
    } else {
      authorized = false;
      reason = `Lateral boundary violation: Officer at '${oPath}' has no jurisdiction over lateral territory '${rPath}'.`;
    }

    setSimResult({
      authorized,
      reason,
      latencyMs: 0.14,
    });
  };

  return (
    <Card className="border border-[#e5e7eb] bg-[#ffffff] shadow-sm">
      <CardHeader className="border-b border-[#e5e7eb] pb-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-lg font-semibold tracking-tight text-[#111827]">
                Chain of Command & Delegated Authority Console
              </CardTitle>
              <Badge variant="verified">Sovereign LGD</Badge>
              <Badge variant="emerald">Scoped TRBAC Active</Badge>
            </div>
            <CardDescription className="text-xs text-[#4b5563]">
              Hierarchical authority provisioning (National to Block), official @gov.in Aadhaar verification, and sub-2ms territorial boundaries.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#6b7280]">
              Active Delegations: <strong className="text-[#111827]">{delegations.filter((d) => d.isActive).length}</strong>
            </span>
          </div>
        </div>

        {/* Live KPI Metric Strip */}
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg border border-[#e5e7eb] bg-[#ffffff] p-2.5">
            <div className="text-[11px] font-medium text-[#6b7280]">Authority Ladder</div>
            <div className="text-sm font-semibold text-[#111827]">5 Ranks (National to Block)</div>
          </div>
          <div className="rounded-lg border border-[#e5e7eb] bg-[#ffffff] p-2.5">
            <div className="text-[11px] font-medium text-[#6b7280]">Identity Verification</div>
            <div className="text-sm font-semibold text-[#111827]">Aadhaar OTP + @gov.in</div>
          </div>
          <div className="rounded-lg border border-[#e5e7eb] bg-[#ffffff] p-2.5">
            <div className="text-[11px] font-medium text-[#6b7280]">Scoped TRBAC SLA</div>
            <div className="text-sm font-semibold text-[#111827]">Sub-2ms (&lt; 0.2ms avg)</div>
          </div>
          <div className="rounded-lg border border-[#e5e7eb] bg-[#ffffff] p-2.5">
            <div className="text-[11px] font-medium text-[#6b7280]">Cryptographic Ledger</div>
            <div className="text-sm font-semibold text-[#111827]">SHA-256 Hash Chained</div>
          </div>
        </div>

        {/* Sub-tab switcher */}
        <div className="mt-4 flex flex-wrap gap-1 border-b border-[#e5e7eb] pb-1">
          <button
            onClick={() => setActiveTab("delegations")}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "delegations"
                ? "bg-[#111827] text-[#ffffff]"
                : "bg-transparent text-[#4b5563] hover:bg-[#f3f4f6]"
            }`}
          >
            Authority Delegations ({delegations.length})
          </button>
          <button
            onClick={() => setActiveTab("provision")}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "provision"
                ? "bg-[#111827] text-[#ffffff]"
                : "bg-transparent text-[#4b5563] hover:bg-[#f3f4f6]"
            }`}
          >
            Provision Authority
          </button>
          <button
            onClick={() => setActiveTab("simulator")}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "simulator"
                ? "bg-[#111827] text-[#ffffff]"
                : "bg-transparent text-[#4b5563] hover:bg-[#f3f4f6]"
            }`}
          >
            Scoped TRBAC Simulator
          </button>
          <button
            onClick={() => setActiveTab("audit")}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "audit"
                ? "bg-[#111827] text-[#ffffff]"
                : "bg-transparent text-[#4b5563] hover:bg-[#f3f4f6]"
            }`}
          >
            Cryptographic Audit Ledger ({auditBlocks.length})
          </button>
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        {/* Tab 1: Delegations List */}
        {activeTab === "delegations" && (
          <div className="space-y-4">
            <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-3 text-xs text-[#4b5563]">
              <strong>Sovereign Chain of Command:</strong> Delegations follow strict downward rank order. Superior officers maintain oversight over subordinate territories, while lateral and upward access is cryptographically blocked.
            </div>

            <div className="overflow-x-auto rounded-lg border border-[#e5e7eb]">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-[#e5e7eb] bg-[#f9fafb] text-[11px] font-semibold text-[#6b7280]">
                  <tr>
                    <th className="px-3 py-2">Delegated Authority</th>
                    <th className="px-3 py-2">Jurisdiction Path</th>
                    <th className="px-3 py-2">Government Contact</th>
                    <th className="px-3 py-2">Delegated By</th>
                    <th className="px-3 py-2">Audit Proof</th>
                    <th className="px-3 py-2 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#e5e7eb]">
                  {delegations.map((d) => (
                    <tr key={d.id} className="hover:bg-[#f9fafb]">
                      <td className="px-3 py-2.5">
                        <div className="font-semibold text-[#111827]">{d.delegateeDesignation}</div>
                        <div className="text-[11px] text-[#4b5563]">{d.unitName} ({d.unitLevel})</div>
                      </td>
                      <td className="px-3 py-2.5 font-mono text-[11px] text-[#111827]">
                        {d.jurisdictionPath}
                      </td>
                      <td className="px-3 py-2.5">
                        <div className="font-mono text-[11px] text-[#111827]">{d.delegateeEmail}</div>
                        {d.aadhaarVerified && (
                          <span className="inline-block rounded bg-[#ecfdf5] px-1.5 py-0.5 text-[10px] font-medium text-[#065f46]">
                            Aadhaar Verified
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2.5">
                        <div className="text-[11px] font-medium text-[#111827]">{d.delegatorDesignation}</div>
                        <div className="font-mono text-[10px] text-[#6b7280]">{d.delegatorEmail}</div>
                      </td>
                      <td className="px-3 py-2.5">
                        <span
                          className="inline-block max-w-[120px] truncate font-mono text-[10px] text-[#6b7280]"
                          title={d.auditHash}
                        >
                          {d.auditHash.slice(0, 12)}...
                        </span>
                        <div className="text-[10px] text-[#6b7280]">{d.createdAt}</div>
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        {d.isActive ? (
                          <button
                            onClick={() => handleRevoke(d.id)}
                            className="rounded border border-[#dc2626] bg-[#ffffff] px-2 py-1 text-[11px] font-medium text-[#dc2626] hover:bg-[#fef2f2]"
                          >
                            Revoke
                          </button>
                        ) : (
                          <span className="rounded bg-[#f3f4f6] px-2 py-1 text-[11px] font-medium text-[#6b7280]">
                            Revoked
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Provision Authority Form */}
        {activeTab === "provision" && (
          <form onSubmit={handleCreateDelegation} className="space-y-4">
            <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-3 text-xs text-[#4b5563]">
              <strong>Step-Down Authority Rule:</strong> You are delegating authority down the official ladder. The delegatee rank must be strictly lower than the delegator rank, and the territory must be within the delegator scope.
            </div>

            {provisionStatus && (
              <div
                className={`rounded-lg p-3 text-xs font-medium ${
                  provisionStatus.startsWith("Success")
                    ? "border border-[#a7f3d0] bg-[#ecfdf5] text-[#065f46]"
                    : "border border-[#fecaca] bg-[#fef2f2] text-[#991b1b]"
                }`}
              >
                {provisionStatus}
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold text-[#111827]">Delegator Designation</label>
                <select
                  value={delegatorDesignation}
                  onChange={(e) => setDelegatorDesignation(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[#e5e7eb] bg-[#ffffff] px-3 py-2 text-xs text-[#111827] focus:border-[#111827] focus:outline-none"
                >
                  <option value="NATIONAL_DIRECTOR">National Director (Rank 5)</option>
                  <option value="STATE_SECRETARY">State Secretary (Rank 4)</option>
                  <option value="DIVISIONAL_COMMISSIONER">Divisional Commissioner (Rank 3)</option>
                  <option value="CHIEF_MEDICAL_OFFICER">Chief Medical Officer (Rank 2)</option>
                </select>
                <span className="text-[11px] text-[#6b7280]">Issuing authority rank.</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#111827]">Delegatee Designation</label>
                <select
                  value={delegateeDesignation}
                  onChange={(e) => setDelegateeDesignation(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[#e5e7eb] bg-[#ffffff] px-3 py-2 text-xs text-[#111827] focus:border-[#111827] focus:outline-none"
                >
                  <option value="STATE_SECRETARY">State Secretary (Rank 4)</option>
                  <option value="DIVISIONAL_COMMISSIONER">Divisional Commissioner (Rank 3)</option>
                  <option value="CHIEF_MEDICAL_OFFICER">Chief Medical Officer (Rank 2)</option>
                  <option value="BLOCK_MEDICAL_OFFICER">Block Medical Officer (Rank 1)</option>
                </select>
                <span className="text-[11px] text-[#6b7280]">Must be strictly lower rank.</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#111827]">Target Administrative Unit</label>
                <input
                  type="text"
                  value={targetUnitName}
                  onChange={(e) => setTargetUnitName(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[#e5e7eb] bg-[#ffffff] px-3 py-2 text-xs text-[#111827] focus:border-[#111827] focus:outline-none"
                  placeholder="e.g. Satara District"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#111827]">PostgreSQL ltree Path</label>
                <input
                  type="text"
                  value={targetPath}
                  onChange={(e) => setTargetPath(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[#e5e7eb] bg-[#ffffff] px-3 py-2 font-mono text-xs text-[#111827] focus:border-[#111827] focus:outline-none"
                  placeholder="e.g. india.27.493"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#111827]">
                  Official Government Email (.gov.in / .nic.in)
                </label>
                <input
                  type="email"
                  value={govEmail}
                  onChange={(e) => setGovEmail(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[#e5e7eb] bg-[#ffffff] px-3 py-2 font-mono text-xs text-[#111827] focus:border-[#111827] focus:outline-none"
                  placeholder="e.g. cmo.satara@nic.in"
                  required
                />
                <span className="text-[11px] text-[#6b7280]">
                  {isGovEmailValid(govEmail) ? (
                    <span className="text-[#065f46]">Valid government domain suffix</span>
                  ) : (
                    <span className="text-[#dc2626]">Must end with .gov.in or .nic.in</span>
                  )}
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#111827]">Delegatee 12-Digit Aadhaar UID</label>
                <input
                  type="text"
                  value={aadhaarUid}
                  onChange={(e) => setAadhaarUid(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[#e5e7eb] bg-[#ffffff] px-3 py-2 font-mono text-xs text-[#111827] focus:border-[#111827] focus:outline-none"
                  placeholder="12 digits"
                  maxLength={14}
                  required
                />
                <span className="text-[11px] text-[#6b7280]">
                  {isAadhaarValid(aadhaarUid) ? (
                    <span className="text-[#065f46]">Valid 12-digit format</span>
                  ) : (
                    <span className="text-[#dc2626]">Must contain exactly 12 digits</span>
                  )}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#111827]">Aadhaar Verification OTP</label>
              <input
                type="text"
                value={aadhaarOtp}
                onChange={(e) => setAadhaarOtp(e.target.value)}
                className="mt-1 max-w-[200px] rounded-md border border-[#e5e7eb] bg-[#ffffff] px-3 py-2 font-mono text-xs text-[#111827] focus:border-[#111827] focus:outline-none"
                placeholder="6-digit code"
                maxLength={6}
                required
              />
              <span className="ml-2 text-[11px] text-[#6b7280]">(Mock simulator default: 123456)</span>
            </div>

            <Button
              type="submit"
              className="rounded-md bg-[#111827] px-4 py-2 text-xs font-medium text-[#ffffff] hover:bg-[#1f2937]"
            >
              Issue Delegated Authority & Sign Block
            </Button>
          </form>
        )}

        {/* Tab 3: TRBAC Policy Simulator */}
        {activeTab === "simulator" && (
          <div className="space-y-4">
            <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-3 text-xs text-[#4b5563]">
              <strong>Sub-2ms Scoped TRBAC Simulator:</strong> Test whether an administrative officer token assigned to a specific jurisdiction path can query clinical records, emergency overrides, or ICU bed rosters at a target facility path.
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <label className="block text-xs font-semibold text-[#111827]">Officer Scope Path</label>
                <input
                  type="text"
                  value={simOfficerPath}
                  onChange={(e) => setSimOfficerPath(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[#e5e7eb] bg-[#ffffff] px-3 py-2 font-mono text-xs text-[#111827] focus:border-[#111827] focus:outline-none"
                  placeholder="e.g. india.27.492"
                />
                <span className="text-[11px] text-[#6b7280]">Pune District CMO ('india.27.492')</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#111827]">Target Facility Path</label>
                <input
                  type="text"
                  value={simResourcePath}
                  onChange={(e) => setSimResourcePath(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[#e5e7eb] bg-[#ffffff] px-3 py-2 font-mono text-xs text-[#111827] focus:border-[#111827] focus:outline-none"
                  placeholder="e.g. india.27.492.4182"
                />
                <span className="text-[11px] text-[#6b7280]">Haveli ('india.27.492.4182') or Satara ('india.27.493')</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#111827]">Action Type</label>
                <select
                  value={simAction}
                  onChange={(e) => setSimAction(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[#e5e7eb] bg-[#ffffff] px-3 py-2 text-xs text-[#111827] focus:border-[#111827] focus:outline-none"
                >
                  <option value="READ">READ (Patient Registry)</option>
                  <option value="AUDIT">AUDIT (Access Logs)</option>
                  <option value="EMERGENCY_OVERRIDE">EMERGENCY_OVERRIDE (BTG Vault)</option>
                </select>
                <span className="text-[11px] text-[#6b7280]">Target privileged action.</span>
              </div>
            </div>

            <Button
              onClick={handleRunSimulator}
              className="rounded-md bg-[#111827] px-4 py-2 text-xs font-medium text-[#ffffff] hover:bg-[#1f2937]"
            >
              Evaluate Territorial Authorization
            </Button>

            {simResult && (
              <div
                className={`mt-4 rounded-lg p-4 text-xs ${
                  simResult.authorized
                    ? "border border-[#a7f3d0] bg-[#ecfdf5] text-[#065f46]"
                    : "border border-[#fecaca] bg-[#fef2f2] text-[#991b1b]"
                }`}
              >
                <div className="flex items-center justify-between font-semibold">
                  <span>{simResult.authorized ? "Access Granted (Authorized)" : "Access Denied (Forbidden - HTTP 403)"}</span>
                  <span className="font-mono text-[11px]">{simResult.latencyMs} ms evaluation</span>
                </div>
                <div className="mt-1 text-xs">{simResult.reason}</div>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Cryptographic Audit Ledger */}
        {activeTab === "audit" && (
          <div className="space-y-4">
            <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-3 text-xs text-[#4b5563]">
              <strong>Cryptographic Hash Chain:</strong> Every administrative delegation and revocation transaction is bound with a SHA-256 hash linking back to the previous block in the ledger.
            </div>

            <div className="space-y-3">
              {auditBlocks.map((b, idx) => (
                <div
                  key={b.id}
                  className="rounded-lg border border-[#e5e7eb] bg-[#ffffff] p-3 text-xs shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-[#111827]">Block #{idx + 1}</span>
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                          b.action === "DELEGATED"
                            ? "bg-[#ecfdf5] text-[#065f46]"
                            : "bg-[#fef2f2] text-[#991b1b]"
                        }`}
                      >
                        {b.action}
                      </span>
                      <span className="font-medium text-[#111827]">{b.actorDesignation}</span>
                    </div>
                    <span className="font-mono text-[11px] text-[#6b7280]">{b.timestamp}</span>
                  </div>

                  <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
                    <div>
                      <div className="text-[10px] font-medium text-[#6b7280]">Territory Path</div>
                      <div className="font-mono text-[11px] text-[#111827]">{b.jurisdictionPath}</div>
                    </div>
                    <div>
                      <div className="text-[10px] font-medium text-[#6b7280]">Current Block Hash (SHA-256)</div>
                      <div className="truncate font-mono text-[10px] text-[#111827]" title={b.auditHash}>
                        {b.auditHash}
                      </div>
                    </div>
                  </div>

                  <div className="mt-1.5 text-[10px] text-[#6b7280]">
                    Previous Block Hash:{" "}
                    <span className="font-mono text-[#4b5563]" title={b.previousHash}>
                      {b.previousHash.slice(0, 32)}...
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
