"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Clock,
  FileText,
  Lock,
  Plus,
  ShieldCheck,
  UserCheck,
  Users,
} from "lucide-react";

export interface DependentRelationshipUI {
  relationshipId: string;
  dependentName: string;
  relationshipType: "CHILD_MINOR" | "PARENT_SENIOR" | "LEGAL_WARD" | "SPOUSE_PROXY";
  relationshipLabel: string;
  dependentAge: number;
  dependentAbha: string;
  dependentPatientId: string;
  verificationTier: string;
  verificationDocHash: string;
  accessScope: "FULL_MANAGEMENT" | "APPOINTMENTS_ONLY" | "RECORDS_VIEW_ONLY";
  status: "ACTIVE" | "REVOKED";
  authorizedAt: string;
  zeroContaminationIsolated: boolean;
  clinicalSummary: {
    lastEncounter: string;
    pendingAppointments: number;
    activeMedications: number;
    immunizationStatus: string;
  };
}

export interface AuditLogUI {
  logId: string;
  timestamp: string;
  action: string;
  resource: string;
  actor: string;
  ip: string;
  authorized: boolean;
}

const INITIAL_DEPENDENTS: DependentRelationshipUI[] = [
  {
    relationshipId: "rel-proxy-child-001",
    dependentName: "Aarav Sharma",
    relationshipType: "CHILD_MINOR",
    relationshipLabel: "Son (Minor Child)",
    dependentAge: 8,
    dependentAbha: "14-8291-0391-4821",
    dependentPatientId: "pat-aarav-sharma-02",
    verificationTier: "DIGILOCKER_BIRTH_CERTIFICATE",
    verificationDocHash: "8f12a048c081294801928409182409182b0412984109481b049182b041298410",
    accessScope: "FULL_MANAGEMENT",
    status: "ACTIVE",
    authorizedAt: "2026-09-01T09:00:00Z",
    zeroContaminationIsolated: true,
    clinicalSummary: {
      lastEncounter: "2026-10-10: Pediatric Wellness Checkup",
      pendingAppointments: 1,
      activeMedications: 0,
      immunizationStatus: "Up to Date (UIP Schedule)",
    },
  },
  {
    relationshipId: "rel-proxy-senior-002",
    dependentName: "Kavita Sharma",
    relationshipType: "PARENT_SENIOR",
    relationshipLabel: "Mother (Senior Citizen)",
    dependentAge: 68,
    dependentAbha: "14-9102-4819-2041",
    dependentPatientId: "pat-kavita-sharma-03",
    verificationTier: "AADHAAR_DEMOGRAPHIC_EKYC",
    verificationDocHash: "a192840192840192840192840192840192840192840192840192840192840192",
    accessScope: "FULL_MANAGEMENT",
    status: "ACTIVE",
    authorizedAt: "2026-09-15T11:30:00Z",
    zeroContaminationIsolated: true,
    clinicalSummary: {
      lastEncounter: "2026-10-20: Geriatric Cardiology Follow-up",
      pendingAppointments: 2,
      activeMedications: 3,
      immunizationStatus: "Seasonal Influenza Administered",
    },
  },
];

const INITIAL_AUDIT_LOGS: Record<string, AuditLogUI[]> = {
  "rel-proxy-child-001": [
    {
      logId: "log-proxy-001",
      timestamp: "2026-10-10 14:20:00 UTC",
      action: "VIEW_PEDIATRIC_IMMUNIZATION_RECORD",
      resource: "DiagnosticReport/imm-uip-bcg-01",
      actor: "pat-priya-sharma-01 (Guardian)",
      ip: "10.0.1.42",
      authorized: true,
    },
    {
      logId: "log-proxy-003",
      timestamp: "2026-10-25 10:15:00 UTC",
      action: "DOWNLOAD_OPD_PRESCRIPTION",
      resource: "MedicationRequest/med-amox-009",
      actor: "pat-priya-sharma-01 (Guardian)",
      ip: "10.0.1.42",
      authorized: true,
    },
  ],
  "rel-proxy-senior-002": [
    {
      logId: "log-proxy-002",
      timestamp: "2026-10-20 16:45:00 UTC",
      action: "SCHEDULE_GERIATRIC_CARDIOLOGY_SLOT",
      resource: "DoctorSlot/slot-cardio-9102",
      actor: "pat-priya-sharma-01 (Guardian)",
      ip: "10.0.1.42",
      authorized: true,
    },
    {
      logId: "log-proxy-004",
      timestamp: "2026-10-28 09:30:00 UTC",
      action: "CONSENT_ARTIFACT_DELEGATION",
      resource: "ABDM/Consent/art-c-89102",
      actor: "pat-priya-sharma-01 (Guardian)",
      ip: "10.0.1.42",
      authorized: true,
    },
  ],
};

export function FamilyProxyRelationshipCard() {
  const [dependents, setDependents] = useState<DependentRelationshipUI[]>(INITIAL_DEPENDENTS);
  const [selectedRelationshipId, setSelectedRelationshipId] = useState<string>("rel-proxy-child-001");
  const [viewContext, setViewContext] = useState<string | null>(null);
  const [isAddingDependent, setIsAddingDependent] = useState<boolean>(false);
  const [formName, setFormName] = useState<string>("");
  const [formType, setFormType] = useState<"CHILD_MINOR" | "PARENT_SENIOR" | "LEGAL_WARD">("CHILD_MINOR");
  const [formDob, setFormDob] = useState<string>("2018-05-14");
  const [formConsent, setFormConsent] = useState<boolean>(true);
  const [formTier, setFormTier] = useState<string>("DIGILOCKER_BIRTH_CERTIFICATE");
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

  const selected = dependents.find((d) => d.relationshipId === selectedRelationshipId) || dependents[0];
  const auditLogs = selected ? INITIAL_AUDIT_LOGS[selected.relationshipId] || [] : [];

  const handleRevoke = (relId: string) => {
    setDependents((prev) =>
      prev.map((d) => (d.relationshipId === relId ? { ...d, status: "REVOKED" } : d))
    );
    setActionSuccessMessage(`Proxy privilege for ${selected.dependentName} successfully revoked.`);
    setTimeout(() => setActionSuccessMessage(null), 4000);
  };

  const handleSwitchContext = (dep: DependentRelationshipUI) => {
    setViewContext(dep.dependentName);
    setActionSuccessMessage(`Switched active clinical context to dependent: ${dep.dependentName} (${dep.dependentAbha}).`);
    setTimeout(() => setActionSuccessMessage(null), 4000);
  };

  const handleCreateDependent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) return;

    const newId = `rel-proxy-custom-${Date.now().toString().slice(-4)}`;
    const newDep: DependentRelationshipUI = {
      relationshipId: newId,
      dependentName: formName,
      relationshipType: formType,
      relationshipLabel: formType === "CHILD_MINOR" ? "Son/Daughter (Minor)" : "Parent (Senior)",
      dependentAge: formType === "CHILD_MINOR" ? 6 : 72,
      dependentAbha: `14-${Math.floor(1000 + Math.random() * 9000)}-${Math.floor(1000 + Math.random() * 9000)}-${Math.floor(1000 + Math.random() * 9000)}`,
      dependentPatientId: `pat-dep-${Date.now().toString().slice(-4)}`,
      verificationTier: formTier,
      verificationDocHash: "7c12f08a91823091823091823091823091823091823091823091823091823091",
      accessScope: "FULL_MANAGEMENT",
      status: "ACTIVE",
      authorizedAt: new Date().toISOString(),
      zeroContaminationIsolated: true,
      clinicalSummary: {
        lastEncounter: "New Registration",
        pendingAppointments: 0,
        activeMedications: 0,
        immunizationStatus: "Profile Initialized",
      },
    };

    setDependents((prev) => [...prev, newDep]);
    setSelectedRelationshipId(newId);
    setIsAddingDependent(false);
    setFormName("");
    setActionSuccessMessage(`Verified dependent proxy linkage created for ${newDep.dependentName}.`);
    setTimeout(() => setActionSuccessMessage(null), 4000);
  };

  return (
    <Card className="border border-[#e5e7eb] bg-[#ffffff] shadow-sm rounded-lg overflow-hidden">
      {/* Top Header */}
      <div className="border-b border-[#e5e7eb] p-6 bg-[#ffffff]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold tracking-wider text-[#6b7280] uppercase">
                DPDP Act 2023 Sec 9 Compliance
              </span>
              <Badge variant="verified">Zero Contamination Certified</Badge>
              <Badge variant="neutral">ABDM UHI Proxy</Badge>
            </div>
            <h2 className="text-xl font-semibold text-[#111111] tracking-tight">
              Dependent & Family Health Proxy Manager
            </h2>
            <p className="text-sm text-[#4b5563] mt-0.5">
              Guardian: <strong className="text-[#111111]">Dr. Priya Sharma</strong> (ID:{" "}
              <code className="text-xs bg-[#f3f4f6] px-1 py-0.5 rounded text-[#111111]">
                pat-priya-sharma-01
              </code>
              ). Sovereign record isolation for minor children and senior parents.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {viewContext && (
              <Badge variant="emerald" className="px-2.5 py-1 text-xs">
                Active Context: {viewContext}
              </Badge>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAddingDependent(!isAddingDependent)}
              className="text-xs font-medium text-[#111111] border-[#e5e7eb] hover:bg-[#f9fafb]"
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              Add Dependent Proxy
            </Button>
          </div>
        </div>

        {actionSuccessMessage && (
          <div className="mt-4 p-3 bg-[#ecfdf5] border border-[#a7f3d0] rounded text-xs text-[#065f46] flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>{actionSuccessMessage}</span>
          </div>
        )}
      </div>

      {/* Add Dependent Form Modal / Panel */}
      {isAddingDependent && (
        <div className="border-b border-[#e5e7eb] bg-[#f9fafb] p-6">
          <div className="max-w-2xl">
            <h3 className="text-sm font-semibold text-[#111111] mb-1">
              Register New Dependent Health Proxy
            </h3>
            <p className="text-xs text-[#4b5563] mb-4">
              Under DPDP Act Section 9, parental/guardian consent and cryptographic document verification are required.
            </p>

            <form onSubmit={handleCreateDependent} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Dependent Legal Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="e.g. Diya Sharma"
                    className="w-full text-xs px-3 py-2 border border-[#d1d5db] rounded bg-[#ffffff] text-[#111111] focus:outline-none focus:border-[#111111]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Relationship Category
                  </label>
                  <select
                    value={formType}
                    onChange={(e) => setFormType(e.target.value as any)}
                    className="w-full text-xs px-3 py-2 border border-[#d1d5db] rounded bg-[#ffffff] text-[#111111] focus:outline-none focus:border-[#111111]"
                  >
                    <option value="CHILD_MINOR">Child Minor (&lt; 18 years)</option>
                    <option value="PARENT_SENIOR">Parent Senior (&gt; 60 years)</option>
                    <option value="LEGAL_WARD">Legal Ward (Judicial Guardianship)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    required
                    value={formDob}
                    onChange={(e) => setFormDob(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-[#d1d5db] rounded bg-[#ffffff] text-[#111111] focus:outline-none focus:border-[#111111]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#374151] mb-1">
                    Verification Authority
                  </label>
                  <select
                    value={formTier}
                    onChange={(e) => setFormTier(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-[#d1d5db] rounded bg-[#ffffff] text-[#111111] focus:outline-none focus:border-[#111111]"
                  >
                    <option value="DIGILOCKER_BIRTH_CERTIFICATE">DigiLocker Verified Birth Certificate</option>
                    <option value="AADHAAR_DEMOGRAPHIC_EKYC">Aadhaar Demographic e-KYC</option>
                    <option value="COURT_LEGAL_GUARDIANSHIP_ORDER">Court Legal Guardianship Order</option>
                  </select>
                </div>
              </div>

              <div className="flex items-start gap-2 pt-1">
                <input
                  type="checkbox"
                  id="consentCheckbox"
                  required
                  checked={formConsent}
                  onChange={(e) => setFormConsent(e.target.checked)}
                  className="mt-0.5 rounded border-[#d1d5db] text-[#111111] focus:ring-[#111111]"
                />
                <label htmlFor="consentCheckbox" className="text-xs text-[#4b5563]">
                  I formally attest that I am the legal parent or authorized guardian of this dependent, adhering to DPDP Act 2023 Section 9 and the National Health Authority guidelines.
                </label>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <Button
                  type="submit"
                  size="sm"
                  className="bg-[#111111] text-[#ffffff] hover:bg-[#262626] text-xs"
                >
                  Confirm & Link Dependent
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsAddingDependent(false)}
                  className="text-xs text-[#4b5563] border-[#e5e7eb]"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Dependent Switcher Tabs */}
      <div className="border-b border-[#e5e7eb] px-6 py-3 bg-[#f9fafb] flex items-center gap-2 overflow-x-auto">
        <span className="text-xs font-medium text-[#6b7280] mr-2 flex items-center gap-1">
          <Users className="w-3.5 h-3.5" />
          Dependents:
        </span>
        {dependents.map((dep) => {
          const isActive = dep.relationshipId === selectedRelationshipId;
          return (
            <button
              key={dep.relationshipId}
              onClick={() => setSelectedRelationshipId(dep.relationshipId)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors flex items-center gap-2 border ${
                isActive
                  ? "bg-[#ffffff] text-[#111111] border-[#d1d5db] shadow-xs"
                  : "bg-transparent text-[#6b7280] border-transparent hover:text-[#111111] hover:bg-[#ffffff]/50"
              }`}
            >
              <span>{dep.dependentName}</span>
              <span className="text-[10px] text-[#9ca3af]">({dep.dependentAge}y)</span>
              {dep.status === "ACTIVE" ? (
                <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]" />
              ) : (
                <span className="w-1.5 h-1.5 rounded-full bg-[#ef4444]" />
              )}
            </button>
          );
        })}
      </div>

      {/* Selected Dependent Content */}
      <div className="p-6 space-y-6">
        {/* Meta Bar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 rounded-lg border border-[#e5e7eb] bg-[#f9fafb]">
          <div>
            <span className="text-[11px] font-medium text-[#6b7280] uppercase tracking-wide block">
              Dependent ABHA & ID
            </span>
            <div className="font-mono text-xs font-semibold text-[#111111] mt-0.5">
              {selected.dependentAbha}
            </div>
            <div className="text-[11px] text-[#6b7280] font-mono mt-0.5">
              {selected.dependentPatientId}
            </div>
          </div>

          <div>
            <span className="text-[11px] font-medium text-[#6b7280] uppercase tracking-wide block">
              Relationship & Scope
            </span>
            <div className="text-xs font-medium text-[#111111] mt-0.5">
              {selected.relationshipLabel}
            </div>
            <div className="text-[11px] text-[#6b7280] mt-0.5">
              Scope: {selected.accessScope}
            </div>
          </div>

          <div>
            <span className="text-[11px] font-medium text-[#6b7280] uppercase tracking-wide block">
              Verification Authority
            </span>
            <div className="text-xs font-medium text-[#111111] mt-0.5 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-[#059669]" />
              {selected.verificationTier.replace(/_/g, " ")}
            </div>
            <div className="text-[10px] font-mono text-[#6b7280] truncate mt-0.5" title={selected.verificationDocHash}>
              Hash: {selected.verificationDocHash.slice(0, 16)}...
            </div>
          </div>

          <div className="flex flex-col justify-center items-start md:items-end gap-2">
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleSwitchContext(selected)}
                className="text-xs font-medium text-[#111111] border-[#d1d5db] hover:bg-[#ffffff]"
              >
                <UserCheck className="w-3.5 h-3.5 mr-1" />
                Switch Context
              </Button>
              {selected.status === "ACTIVE" ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleRevoke(selected.relationshipId)}
                  className="text-xs font-medium text-[#991b1b] border-[#fecaca] hover:bg-[#fef2f2]"
                >
                  Revoke Proxy
                </Button>
              ) : (
                <Badge variant="critical">REVOKED</Badge>
              )}
            </div>
          </div>
        </div>

        {/* 2-Column Grid: Invariant Checklist & Clinical Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Column 1: Zero-Contamination Architecture Invariants */}
          <div className="border border-[#e5e7eb] rounded-lg p-5 bg-[#ffffff]">
            <h3 className="text-xs font-semibold text-[#111111] uppercase tracking-wide mb-3 flex items-center gap-2">
              <Lock className="w-3.5 h-3.5 text-[#111111]" />
              Zero-Contamination Architecture Guard
            </h3>
            <ul className="space-y-3 text-xs text-[#374151]">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#059669] flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-medium text-[#111111]">Independent Patient Vault:</span> Dependent records are isolated in distinct database rows. No pediatric or geriatric data resides in guardian profile.
                </div>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#059669] flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-medium text-[#111111]">DPDP Act Section 9 Compliance:</span> Verifiable parental consent record permanently anchored to relationship registration.
                </div>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#059669] flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-medium text-[#111111]">Age-of-Majority Enforcement:</span> Minor child privileges automatically lock and prompt adult re-authorization upon reaching 18 years of age.
                </div>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#059669] flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-medium text-[#111111]">Cryptographic Document Provenance:</span> DigiLocker / Aadhaar verification artifacts anchored with SHA-256 hashes.
                </div>
              </li>
            </ul>
          </div>

          {/* Column 2: Clinical Care Summary */}
          <div className="border border-[#e5e7eb] rounded-lg p-5 bg-[#ffffff]">
            <h3 className="text-xs font-semibold text-[#111111] uppercase tracking-wide mb-3 flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-[#111111]" />
              Dependent Clinical Care Status
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-[#f3f4f6]">
                <span className="text-[#6b7280]">Latest Clinical Encounter:</span>
                <span className="font-medium text-[#111111]">{selected.clinicalSummary.lastEncounter}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#f3f4f6]">
                <span className="text-[#6b7280]">Pending OPD Appointments:</span>
                <span className="font-medium text-[#111111]">{selected.clinicalSummary.pendingAppointments} scheduled</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#f3f4f6]">
                <span className="text-[#6b7280]">Active Regimens / Meds:</span>
                <span className="font-medium text-[#111111]">{selected.clinicalSummary.activeMedications} active</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-[#6b7280]">Immunization / Care Plan:</span>
                <span className="font-medium text-[#059669]">{selected.clinicalSummary.immunizationStatus}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Immutable Forensic Audit Trail */}
        <div className="border border-[#e5e7eb] rounded-lg p-5 bg-[#ffffff]">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-[#111111] uppercase tracking-wide flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-[#111111]" />
              Immutable Forensic Proxy Audit Trail
            </h3>
            <span className="text-[11px] text-[#6b7280]">
              Showing {auditLogs.length} verified operations
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#e5e7eb] bg-[#f9fafb] text-[#6b7280]">
                  <th className="py-2 px-3 font-medium">Timestamp</th>
                  <th className="py-2 px-3 font-medium">Action Performed</th>
                  <th className="py-2 px-3 font-medium">Resource Accessed</th>
                  <th className="py-2 px-3 font-medium">Actor</th>
                  <th className="py-2 px-3 font-medium">Network Origin</th>
                  <th className="py-2 px-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f3f4f6]">
                {auditLogs.map((log) => (
                  <tr key={log.logId} className="hover:bg-[#f9fafb]">
                    <td className="py-2.5 px-3 font-mono text-[11px] text-[#4b5563]">{log.timestamp}</td>
                    <td className="py-2.5 px-3 font-semibold text-[#111111]">{log.action}</td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-[#6b7280]">{log.resource}</td>
                    <td className="py-2.5 px-3 text-[#374151]">{log.actor}</td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-[#6b7280]">{log.ip}</td>
                    <td className="py-2.5 px-3">
                      {log.authorized ? (
                        <Badge variant="emerald" size="sm">AUTHORIZED</Badge>
                      ) : (
                        <Badge variant="critical" size="sm">DENIED</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Card>
  );
}

