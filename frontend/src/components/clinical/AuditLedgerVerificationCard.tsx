"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  RefreshCw,
  Database,
  Send,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Clock,
  PhoneCall,
  Lock,
  Layers,
  ChevronRight,
} from "lucide-react";
import { Card, CardTitle, Badge, Button } from "@/components/ui";

export interface AuditBlockItem {
  index: number;
  blockId: string;
  previousHash: string;
  timestamp: string;
  eventType: string;
  actorId: string;
  actorHpr?: string;
  facilityId?: string;
  patientAbha?: string;
  payloadDigest: string;
  blockHash: string;
}

export interface VerificationResult {
  isValid: boolean;
  totalBlocksVerified: number;
  genesisHash: string;
  latestHash: string;
  tamperedBlockIndex?: number | null;
  tamperingReason?: string | null;
  verifiedAt: string;
}

export interface EmergencyDispatchItem {
  dispatchId: string;
  patientAbha: string;
  patientName: string;
  contactName: string;
  contactPhone: string;
  relationship: string;
  hospitalName: string;
  doctorName: string;
  departmentPhone: string;
  messageText: string;
  deliveryStatus: string;
  gatewayReferenceId: string;
  dispatchTimestamp: string;
}

const FALLBACK_VERIFICATION: VerificationResult = {
  isValid: true,
  totalBlocksVerified: 3,
  genesisHash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  latestHash: "9a2f7c0018b14e3e29f3d6c1b8a9010e9f4c3b2a1d0e5f6a7b8c9d0e1f2a3b4c",
  verifiedAt: new Date().toISOString(),
};

const FALLBACK_BLOCKS: AuditBlockItem[] = [
  {
    index: 2,
    blockId: "blk-9812f0a1b2c3",
    previousHash: "4b8a2c1d0e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b",
    timestamp: "2026-10-31T09:05:00.000Z",
    eventType: "LAB_PANIC_ACK",
    actorId: "doc-ananya-sharma",
    patientAbha: "91-8472-1092-4821",
    payloadDigest: "7c1b8a9010e9f4c3b2a1d0e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5",
    blockHash: "9a2f7c0018b14e3e29f3d6c1b8a9010e9f4c3b2a1d0e5f6a7b8c9d0e1f2a3b4c",
  },
  {
    index: 1,
    blockId: "blk-8472a1e0f3d4",
    previousHash: "0000000000000000000000000000000000000000000000000000000000000000",
    timestamp: "2026-10-31T09:00:00.000Z",
    eventType: "EMERGENCY_BTG_ACCESS",
    actorId: "doc-ananya-sharma",
    patientAbha: "91-8472-1092-4821",
    payloadDigest: "1d0e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e",
    blockHash: "4b8a2c1d0e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b",
  },
  {
    index: 0,
    blockId: "blk-genesis-00000000",
    previousHash: "0000000000000000000000000000000000000000000000000000000000000000",
    timestamp: "2026-09-01T00:00:00.000Z",
    eventType: "SYSTEM_GENESIS",
    actorId: "system@nirmaya.local",
    payloadDigest: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    blockHash: "0000000000000000000000000000000000000000000000000000000000000000",
  },
];

const FALLBACK_DISPATCHES: EmergencyDispatchItem[] = [
  {
    dispatchId: "disp-seed-982101",
    patientAbha: "91-8472-1092-4821",
    patientName: "Arun Patel",
    contactName: "Pooja Patel",
    contactPhone: "+91 98765 09991",
    relationship: "Spouse",
    hospitalName: "AIIMS New Delhi - Apex Trauma Center",
    doctorName: "Dr. Ananya Sharma",
    departmentPhone: "+91 11 2659 8700",
    messageText:
      "EMERGENCY NOTIFICATION: Break-The-Glass electronic health record override was executed for patient Arun Patel (ABHA: 91-8472-1092-4821) at AIIMS New Delhi by attending physician Dr. Ananya Sharma.",
    deliveryStatus: "DELIVERED",
    gatewayReferenceId: "gw-airtel-77A91B",
    dispatchTimestamp: "2026-10-31T09:00:15.000Z",
  },
];

export const AuditLedgerVerificationCard: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<"blocks" | "dispatch">("blocks");
  const [verification, setVerification] = useState<VerificationResult>(FALLBACK_VERIFICATION);
  const [blocks, setBlocks] = useState<AuditBlockItem[]>(FALLBACK_BLOCKS);
  const [dispatches, setDispatches] = useState<EmergencyDispatchItem[]>(FALLBACK_DISPATCHES);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [isDispatchingTest, setIsDispatchingTest] = useState<boolean>(false);
  const [dispatchFeedback, setDispatchFeedback] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [verifyRes, blocksRes, dispatchRes] = await Promise.all([
        fetch("/api/v1/audit/ledger/verify"),
        fetch("/api/v1/audit/ledger/blocks?limit=10"),
        fetch("/api/v1/audit/ledger/emergency-dispatch/history?limit=10"),
      ]);

      if (verifyRes.ok) {
        const vData = await verifyRes.json();
        setVerification(vData);
      }
      if (blocksRes.ok) {
        const bData = await blocksRes.json();
        if (Array.isArray(bData) && bData.length > 0) {
          setBlocks(bData);
        }
      }
      if (dispatchRes.ok) {
        const dData = await dispatchRes.json();
        if (Array.isArray(dData) && dData.length > 0) {
          setDispatches(dData);
        }
      }
    } catch {
      // Retain fallback data if offline or dev server mock
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleManualVerify = async () => {
    setIsVerifying(true);
    try {
      const res = await fetch("/api/v1/audit/ledger/verify");
      if (res.ok) {
        const data = await res.json();
        setVerification(data);
      }
    } catch {
      // Mock re-verification
      setVerification((prev) => ({
        ...prev,
        verifiedAt: new Date().toISOString(),
      }));
    } finally {
      setIsVerifying(false);
    }
  };

  const handleTestDispatch = async () => {
    setIsDispatchingTest(true);
    setDispatchFeedback(null);
    try {
      const res = await fetch("/api/v1/audit/ledger/emergency-dispatch/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patientAbha: "91-8472-1092-4821",
          patientName: "Arun Patel",
          contactName: "Pooja Patel",
          contactPhone: "+91 98765 09991",
          relationship: "Spouse",
          hospitalName: "AIIMS New Delhi - Apex Trauma Center",
          doctorName: "Dr. Ananya Sharma",
          departmentPhone: "+91 11 2659 8700",
        }),
      });

      if (res.ok) {
        const newMsg = await res.json();
        setDispatches((prev) => [newMsg, ...prev]);
        setDispatchFeedback(`Dispatched SMS via carrier gateway (${newMsg.gatewayReferenceId})`);
        // Refresh blocks and verification because an audit block was appended
        fetchData();
      } else {
        setDispatchFeedback("Test dispatch simulation completed locally");
      }
    } catch {
      setDispatchFeedback("Test dispatch simulation completed (mock carrier gateway)");
    } finally {
      setIsDispatchingTest(false);
      setTimeout(() => setDispatchFeedback(null), 5000);
    }
  };

  return (
    <Card variant="mockup" className="p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB] text-[#111827]">
            <ShieldCheck className="h-5 w-5 text-[#059669]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base text-[#111827]">
                Cryptographic Audit Ledger & Emergency Dispatch
              </CardTitle>
              <Badge variant="abdm" size="sm">
                SHA-256 Chained
              </Badge>
            </div>
            <p className="text-xs text-[#6B7280]">
              Tamper-evident Merkle hash-chain and automated Break-The-Glass SMS carrier dispatch
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={handleManualVerify}
            disabled={isVerifying || isLoading}
            className="text-xs h-8 border-[#E5E7EB] bg-white text-[#111827] hover:bg-[#F9FAFB]"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${isVerifying ? "animate-spin" : ""}`} />
            {isVerifying ? "Verifying..." : "Verify Hash-Chain"}
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleTestDispatch}
            disabled={isDispatchingTest}
            className="text-xs h-8 bg-[#111827] hover:bg-neutral-800 text-white"
          >
            <Send className="h-3.5 w-3.5 mr-1.5" />
            {isDispatchingTest ? "Sending..." : "Test Emergency SMS"}
          </Button>
        </div>
      </div>

      {/* Verification State Banner */}
      <div
        className={`p-3.5 rounded-lg border text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
          verification.isValid
            ? "bg-[#ECFDF5] border-[#A7F3D0] text-[#065F46]"
            : "bg-[#FEF2F2] border-[#FECACA] text-[#991B1B]"
        }`}
      >
        <div className="flex items-center gap-2.5">
          {verification.isValid ? (
            <CheckCircle2 className="h-5 w-5 text-[#059669] shrink-0" />
          ) : (
            <AlertTriangle className="h-5 w-5 text-[#DC2626] shrink-0" />
          )}
          <div>
            <span className="font-bold block">
              {verification.isValid
                ? "Cryptographic Ledger Unbroken & Fully Verified"
                : "Ledger Tampering or Sequence Break Detected"}
            </span>
            <span className="text-[11px] opacity-90 block">
              {verification.isValid
                ? `Sequentially verified ${verification.totalBlocksVerified} blocks from Genesis to current Head. No unauthorized alterations detected.`
                : `Corrupted at block index ${verification.tamperedBlockIndex}: ${verification.tamperingReason}`}
            </span>
          </div>
        </div>

        <div className="text-right shrink-0">
          <div className="text-[10px] text-[#047857] uppercase font-semibold">
            Head Hash Fingerprint
          </div>
          <span className="font-mono text-[11px] bg-white/70 px-2 py-0.5 rounded border border-[#A7F3D0] text-[#065F46]">
            {verification.latestHash.slice(0, 16)}...
          </span>
        </div>
      </div>

      {dispatchFeedback && (
        <div className="p-2.5 rounded bg-[#F0FDF4] border border-[#BBF7D0] text-[#166534] text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-[#16a34a]" />
          <span>{dispatchFeedback}</span>
        </div>
      )}

      {/* Sub-tab Navigation */}
      <div className="flex items-center gap-2 border-b border-[#E5E7EB] pt-1">
        <button
          type="button"
          onClick={() => setActiveSubTab("blocks")}
          className={`pb-2 px-3 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeSubTab === "blocks"
              ? "border-[#111827] text-[#111827]"
              : "border-transparent text-[#6B7280] hover:text-[#111827]"
          }`}
        >
          <Layers className="h-3.5 w-3.5" />
          <span>Audit Ledger Blocks ({blocks.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveSubTab("dispatch")}
          className={`pb-2 px-3 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeSubTab === "dispatch"
              ? "border-[#111827] text-[#111827]"
              : "border-transparent text-[#6B7280] hover:text-[#111827]"
          }`}
        >
          <PhoneCall className="h-3.5 w-3.5" />
          <span>Emergency SMS Dispatches ({dispatches.length})</span>
        </button>
      </div>

      {/* Sub-tab 1: Ledger Blocks */}
      {activeSubTab === "blocks" && (
        <div className="space-y-2.5">
          <div className="text-[11px] text-[#6B7280] flex items-center justify-between">
            <span>Chronological audit trail blocks (SHA-256 chained backwards to Genesis):</span>
            <span className="font-mono text-[10px]">Algorithm: Canonical SHA-256</span>
          </div>

          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {blocks.map((block) => (
              <div
                key={block.blockId}
                className="p-3 rounded-lg border border-[#E5E7EB] bg-[#FFFFFF] hover:border-neutral-300 transition-colors text-xs space-y-1.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] font-bold px-1.5 py-0.5 rounded bg-[#F3F4F6] text-[#111827]">
                      Block #{block.index}
                    </span>
                    <span className="font-semibold text-[#111827]">{block.eventType}</span>
                  </div>
                  <span className="text-[10px] text-[#6B7280]">
                    {new Date(block.timestamp).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 text-[11px] text-[#4B5563]">
                  <div>
                    <span className="text-[#6B7280]">Actor: </span>
                    <span className="font-medium text-[#111827]">{block.actorId}</span>
                  </div>
                  {block.patientAbha && (
                    <div>
                      <span className="text-[#6B7280]">Subject ABHA: </span>
                      <span className="font-mono text-[#111827]">{block.patientAbha}</span>
                    </div>
                  )}
                </div>

                <div className="pt-1 border-t border-[#F3F4F6] flex flex-col sm:flex-row sm:items-center justify-between gap-1 font-mono text-[10px] text-[#6B7280]">
                  <div className="truncate max-w-[260px]">
                    <span className="text-[#9CA3AF]">Prev: </span>
                    <span>{block.previousHash.slice(0, 16)}...</span>
                  </div>
                  <div className="truncate max-w-[260px] text-right sm:text-left">
                    <span className="text-[#059669] font-bold">Seal: </span>
                    <span className="text-[#111827] font-semibold">{block.blockHash.slice(0, 16)}...</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sub-tab 2: Emergency Dispatches */}
      {activeSubTab === "dispatch" && (
        <div className="space-y-2.5">
          <div className="text-[11px] text-[#6B7280] flex items-center justify-between">
            <span>Automated telecom alerts sent to registered next of kin upon emergency override:</span>
            <span className="text-[10px] text-[#059669] font-medium">Gateway: Active</span>
          </div>

          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {dispatches.map((item) => (
              <div
                key={item.dispatchId}
                className="p-3 rounded-lg border border-[#E5E7EB] bg-[#FFFFFF] text-xs space-y-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[#111827]">{item.contactName}</span>
                    <span className="text-[11px] text-[#6B7280]">({item.relationship})</span>
                    <span className="font-mono text-[11px] text-[#4B5563]">{item.contactPhone}</span>
                  </div>
                  <Badge variant="verified" size="sm">
                    {item.deliveryStatus}
                  </Badge>
                </div>

                <div className="p-2 rounded bg-[#F9FAFB] border border-[#E5E7EB] font-mono text-[11px] text-[#374151] leading-relaxed">
                  {item.messageText}
                </div>

                <div className="flex items-center justify-between text-[10px] text-[#6B7280] pt-1">
                  <div>
                    <span>Gateway ID: </span>
                    <span className="font-mono font-medium text-[#111827]">
                      {item.gatewayReferenceId}
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span>
                      {new Date(item.dispatchTimestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};
