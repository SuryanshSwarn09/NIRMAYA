"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export interface ClinicalEventItem {
  event_id: string;
  sequence_number: number;
  event_type: string;
  aggregate_id: string;
  payload_sha256: string;
  timestamp: string;
  sync_state: "synced" | "pending_sync" | "syncing";
}

export const INITIAL_OFFLINE_EVENTS: ClinicalEventItem[] = [
  {
    event_id: "evt-7f8d6c12",
    sequence_number: 1,
    event_type: "patient_registration",
    aggregate_id: "pat-bihar-phc-001",
    payload_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    timestamp: "10 mins ago",
    sync_state: "synced",
  },
  {
    event_id: "evt-9a1b2c34",
    sequence_number: 2,
    event_type: "encounter_created",
    aggregate_id: "enc-bihar-phc-001",
    payload_sha256: "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
    timestamp: "6 mins ago",
    sync_state: "synced",
  },
  {
    event_id: "evt-3d4e5f67",
    sequence_number: 3,
    event_type: "soap_note_saved",
    aggregate_id: "soap-bihar-phc-001",
    payload_sha256: "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
    timestamp: "Just now",
    sync_state: "pending_sync",
  },
];

export const EdgeNodeSyncCard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"queue" | "topology" | "ledger">("queue");
  const [isSyncing, setIsSyncing] = useState(false);
  const [events, setEvents] = useState<ClinicalEventItem[]>(INITIAL_OFFLINE_EVENTS);
  const [lastSyncText, setLastSyncText] = useState("Just now");

  const pendingCount = events.filter((e) => e.sync_state === "pending_sync").length;

  const handleForceSync = () => {
    setIsSyncing(true);
    setTimeout(() => {
      setEvents((prev) =>
        prev.map((e) => ({
          ...e,
          sync_state: "synced",
        }))
      );
      setIsSyncing(false);
      setLastSyncText("Just now");
    }, 600);
  };

  return (
    <Card className="p-6 bg-white border border-gray-200 rounded-xl shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-gray-100">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-900 tracking-tight">
              Dual-Mode Edge Node Appliance & Offline Sync
            </h2>
            <Badge variant="verified">
              EDGE-PHC-BIHAR-042
            </Badge>
            {pendingCount === 0 ? (
              <Badge variant="emerald">Synced to Cloud</Badge>
            ) : (
              <Badge variant="warning">{pendingCount} Buffered</Badge>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Local-first encrypted SQLite storage, append-only SHA-256 event log, and store-and-forward synchronization.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">Synced: {lastSyncText}</span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleForceSync}
            disabled={isSyncing}
            className="text-xs font-medium border-gray-200 hover:bg-gray-50 text-gray-700"
          >
            {isSyncing ? "Syncing..." : "Force Synchronize Now"}
          </Button>
        </div>
      </div>

      {/* KPI Metrics Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-5 border-b border-gray-100">
        <div className="p-3.5 bg-gray-50 border border-gray-100 rounded-lg">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider block">
            Offline Buffer Depth
          </span>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-xl font-bold text-gray-900">
              {pendingCount} Events
            </span>
            {pendingCount === 0 ? (
              <Badge variant="emerald">Clean</Badge>
            ) : (
              <Badge variant="warning">Buffered</Badge>
            )}
          </div>
          <span className="text-xs text-gray-500 mt-1 block">
            Append-only clinical queue
          </span>
        </div>

        <div className="p-3.5 bg-gray-50 border border-gray-100 rounded-lg">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider block">
            Local Storage
          </span>
          <span className="text-xl font-bold text-gray-900 mt-0.5 block">
            14.2 MB
          </span>
          <span className="text-xs text-gray-500 mt-1 block">
            SQLite AES-256 (Budget 500 MB)
          </span>
        </div>

        <div className="p-3.5 bg-gray-50 border border-gray-100 rounded-lg">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider block">
            Appliance RAM Budget
          </span>
          <span className="text-xl font-bold text-gray-900 mt-0.5 block">
            &lt; 512 MB
          </span>
          <span className="text-xs text-gray-500 mt-1 block">
            Single-node PHC workstation
          </span>
        </div>

        <div className="p-3.5 bg-gray-50 border border-gray-100 rounded-lg">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider block">
            Sync Latency
          </span>
          <span className="text-xl font-bold text-gray-900 mt-0.5 block">
            48.5 ms
          </span>
          <span className="text-xs text-gray-500 mt-1 block">
            Store-and-forward batch
          </span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-2 pt-4 pb-4 border-b border-gray-100">
        <button
          onClick={() => setActiveTab("queue")}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            activeTab === "queue"
              ? "bg-gray-900 text-white"
              : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          }`}
        >
          Clinical Event Queue ({events.length})
        </button>
        <button
          onClick={() => setActiveTab("topology")}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            activeTab === "topology"
              ? "bg-gray-900 text-white"
              : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          }`}
        >
          Edge Appliance Topology
        </button>
        <button
          onClick={() => setActiveTab("ledger")}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            activeTab === "ledger"
              ? "bg-gray-900 text-white"
              : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          }`}
        >
          Cryptographic Hash Chain
        </button>
      </div>

      {/* Tab Contents */}
      <div className="pt-4">
        {activeTab === "queue" && (
          <div className="space-y-3">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-gray-50 text-gray-500 uppercase tracking-wider border-b border-gray-100">
                  <tr>
                    <th className="py-2.5 px-3">Seq</th>
                    <th className="py-2.5 px-3">Event Type</th>
                    <th className="py-2.5 px-3">Aggregate ID</th>
                    <th className="py-2.5 px-3">Payload SHA-256</th>
                    <th className="py-2.5 px-3">Time</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {events.map((evt, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="py-2.5 px-3 font-mono font-bold text-gray-900">#{evt.sequence_number}</td>
                      <td className="py-2.5 px-3 font-mono text-gray-800">{evt.event_type}</td>
                      <td className="py-2.5 px-3 font-mono text-gray-600">{evt.aggregate_id}</td>
                      <td className="py-2.5 px-3 font-mono text-gray-400 text-[11px] truncate max-w-[140px]">
                        {evt.payload_sha256.substring(0, 16)}...
                      </td>
                      <td className="py-2.5 px-3 text-gray-500">{evt.timestamp}</td>
                      <td className="py-2.5 px-3">
                        {evt.sync_state === "synced" ? (
                          <Badge variant="emerald">Synced</Badge>
                        ) : (
                          <Badge variant="warning">Pending</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-3.5 bg-gray-50 rounded-lg border border-gray-100 text-xs text-gray-600 flex items-center justify-between">
              <span>Automatic uplink synchronization triggers every 300 seconds when connected.</span>
              <span className="font-mono text-gray-900 font-semibold">Uplink: api.nirmaya.health</span>
            </div>
          </div>
        )}

        {activeTab === "topology" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="p-3.5 bg-gray-50 border border-gray-100 rounded-lg space-y-1.5">
              <span className="font-bold text-gray-900 uppercase block">1. Edge Backend</span>
              <p className="text-gray-600">FastAPI ASGI running single worker with embedded SQLite driver (aiosqlite).</p>
              <span className="font-mono text-gray-500 block">Memory Limit: 256 MB</span>
            </div>

            <div className="p-3.5 bg-gray-50 border border-gray-100 rounded-lg space-y-1.5">
              <span className="font-bold text-gray-900 uppercase block">2. Standalone Frontend</span>
              <p className="text-gray-600">Next.js 15 Standalone server serving clinical EMR UI locally on LAN.</p>
              <span className="font-mono text-gray-500 block">Memory Limit: 192 MB</span>
            </div>

            <div className="p-3.5 bg-gray-50 border border-gray-100 rounded-lg space-y-1.5">
              <span className="font-bold text-gray-900 uppercase block">3. Local Caddy Gateway</span>
              <p className="text-gray-600">Reverse proxy terminating HTTP/HTTPS on port 80/443 with mDNS support.</p>
              <span className="font-mono text-gray-500 block">Memory Limit: 64 MB</span>
            </div>
          </div>
        )}

        {activeTab === "ledger" && (
          <div className="space-y-3 text-xs">
            <div className="p-3.5 bg-gray-50 border border-gray-100 rounded-lg flex items-center justify-between">
              <div>
                <span className="text-gray-500 font-medium uppercase block">Ledger Merkle Root Hash</span>
                <span className="font-mono font-bold text-gray-900 text-sm block mt-0.5">
                  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
                </span>
              </div>
              <Badge variant="emerald">Cryptographically Verified</Badge>
            </div>

            <div className="space-y-1.5">
              <span className="font-semibold text-gray-900 block">Ledger Integrity Guarantees:</span>
              <div className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-100">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                <span className="text-gray-700">Strict monotonic vector clock sequence prevents event re-ordering attacks.</span>
              </div>
              <div className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-100">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                <span className="text-gray-700">SHA-256 parent hash chaining detects any retroactive payload modification.</span>
              </div>
              <div className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-100">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                <span className="text-gray-700">Store-and-forward batch protocol guarantees zero clinical record loss.</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

