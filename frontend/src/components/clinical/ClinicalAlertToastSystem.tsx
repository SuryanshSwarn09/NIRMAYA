"use client";

import React, { useState } from "react";
import { ClinicalAlertItem } from "@/hooks/useClinicalNotificationsWebSocket";
import { 
  AlertTriangle, 
  CheckCircle2, 
  X, 
  Bell, 
  ShieldAlert, 
  Clock, 
  User, 
  Activity, 
  Filter 
} from "lucide-react";

interface ClinicalAlertToastSystemProps {
  latestPanicAlert: ClinicalAlertItem | null;
  alerts: ClinicalAlertItem[];
  unreadCount: number;
  isOpenDrawer: boolean;
  onCloseDrawer: () => void;
  onAcknowledge: (alertId: string, clinicalAction: string) => Promise<boolean>;
  onDismissPanic: () => void;
}

const PRESET_ACTIONS: Record<string, string[]> = {
  LAB_PANIC_VALUE: [
    "Ordered Stat 12-Lead ECG and IV Calcium Gluconate protocol",
    "Initiated Acute Coronary Syndrome protocol and CCU transfer",
    "Administered IV 25% Dextrose, fingerstick monitoring q15m",
    "Held nephrotoxic drugs, evaluated for emergent dialysis",
    "Crossmatched packed RBCs, surgical consult for active bleeding",
  ],
  CRITICAL_VITALS: [
    "Titrated IV Norepinephrine and called Rapid Response Team",
    "High-flow nasal cannula oxygen initiated, ABG ordered",
  ],
  DEFAULT: [
    "Clinically reviewed and documented in patient encounter chart",
    "Patient notified and instructed to report to emergency department",
  ],
};

export const ClinicalAlertToastSystem: React.FC<ClinicalAlertToastSystemProps> = ({
  latestPanicAlert,
  alerts,
  unreadCount,
  isOpenDrawer,
  onCloseDrawer,
  onAcknowledge,
  onDismissPanic,
}) => {
  const [selectedAlertForAck, setSelectedAlertForAck] = useState<ClinicalAlertItem | null>(null);
  const [customAction, setCustomAction] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [activeFilter, setActiveFilter] = useState<"ALL" | "UNREAD" | "PANIC">("ALL");

  const handleOpenAckModal = (alert: ClinicalAlertItem) => {
    setSelectedAlertForAck(alert);
    const presets = PRESET_ACTIONS[alert.category] || PRESET_ACTIONS.DEFAULT;
    setCustomAction(presets[0]);
  };

  const handleConfirmAck = async () => {
    if (!selectedAlertForAck || !customAction.trim()) return;
    setIsSubmitting(true);
    await onAcknowledge(selectedAlertForAck.alertId, customAction.trim());
    setIsSubmitting(false);
    setSelectedAlertForAck(null);
    setCustomAction("");
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (activeFilter === "UNREAD") return alert.status === "UNREAD";
    if (activeFilter === "PANIC") return alert.severity === "PANIC";
    return true;
  });

  return (
    <>
      {/* 1. High-Priority Critical Panic Alert Toast Banner */}
      {latestPanicAlert && (
        <div className="fixed bottom-6 right-6 z-50 max-w-lg w-full bg-white rounded-lg border-2 border-red-500 shadow-xl overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-300">
          <div className="bg-red-50 border-b border-red-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-600"></span>
              </span>
              <span className="text-xs font-bold uppercase tracking-wider text-red-800">
                Stat Critical Panic Value Alert
              </span>
            </div>
            <button
              onClick={onDismissPanic}
              className="text-red-500 hover:text-red-700 transition-colors p-1"
              aria-label="Dismiss toast banner"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="p-4 space-y-3">
            <div>
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-gray-900">
                  {latestPanicAlert.title}
                </h4>
                <span className="text-xs font-mono text-gray-500">
                  {latestPanicAlert.loincCode ? `LOINC ${latestPanicAlert.loincCode}` : ""}
                </span>
              </div>
              <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                {latestPanicAlert.message}
              </p>
            </div>

            <div className="bg-gray-50 border border-[#E5E7EB] rounded p-2.5 flex items-center justify-between text-xs">
              <div>
                <span className="text-gray-500 block">Observed Value</span>
                <span className="font-bold font-mono text-red-600 text-sm">
                  {latestPanicAlert.observedValue || "Out of Range"}
                </span>
              </div>
              <div>
                <span className="text-gray-500 block">Reference Range</span>
                <span className="font-mono text-gray-700">
                  {latestPanicAlert.referenceRange || "Standard"}
                </span>
              </div>
              <div>
                <span className="text-gray-500 block">Patient</span>
                <span className="font-medium text-gray-900">
                  {latestPanicAlert.patientName}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-1">
              <button
                onClick={onDismissPanic}
                className="px-3 py-1.5 text-xs font-medium text-gray-600 hover:text-gray-900 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 transition-colors"
              >
                Dismiss Banner
              </button>
              <button
                onClick={() => handleOpenAckModal(latestPanicAlert)}
                className="px-3 py-1.5 text-xs font-medium text-white bg-[#111827] hover:bg-black rounded shadow-xs transition-colors flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Acknowledge Stat
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. Slide-Over Alerts Drawer */}
      {isOpenDrawer && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div 
            className="absolute inset-0 bg-black/20 backdrop-blur-xs transition-opacity"
            onClick={onCloseDrawer}
          />
          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
            <div className="w-screen max-w-md bg-white border-l border-[#E5E7EB] shadow-2xl flex flex-col">
              
              {/* Drawer Header */}
              <div className="px-6 py-5 border-b border-[#E5E7EB] flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-gray-100 rounded text-gray-800">
                    <Bell className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-gray-900">
                      Clinical Alerts & Notifications
                    </h3>
                    <p className="text-xs text-gray-500">
                      Real-time panic lab values and care notifications
                    </p>
                  </div>
                </div>
                <button
                  onClick={onCloseDrawer}
                  className="p-1.5 text-gray-400 hover:text-gray-600 rounded transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Filter Tabs */}
              <div className="px-6 py-3 border-b border-[#E5E7EB] bg-gray-50/50 flex items-center gap-2">
                {(["ALL", "UNREAD", "PANIC"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveFilter(tab)}
                    className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                      activeFilter === tab
                        ? "bg-[#111827] text-white"
                        : "text-gray-600 hover:bg-gray-200/60"
                    }`}
                  >
                    {tab === "ALL" && `All (${alerts.length})`}
                    {tab === "UNREAD" && `Unread (${unreadCount})`}
                    {tab === "PANIC" &&
                      `Panic (${alerts.filter((a) => a.severity === "PANIC").length})`}
                  </button>
                ))}
              </div>

              {/* Alerts List */}
              <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
                {filteredAlerts.length === 0 ? (
                  <div className="text-center py-12 text-gray-500 text-xs">
                    No clinical alerts match current filter.
                  </div>
                ) : (
                  filteredAlerts.map((alert) => {
                    const isPanic = alert.severity === "PANIC";
                    const isUnread = alert.status === "UNREAD";

                    return (
                      <div
                        key={alert.alertId}
                        className={`p-3.5 rounded-lg border transition-all ${
                          isPanic
                            ? "border-red-200 bg-red-50/40"
                            : isUnread
                            ? "border-[#E5E7EB] bg-white shadow-xs"
                            : "border-[#E5E7EB] bg-gray-50/60 opacity-80"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded ${
                                isPanic
                                  ? "bg-red-100 text-red-800"
                                  : alert.severity === "CRITICAL"
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-blue-100 text-blue-800"
                              }`}
                            >
                              {alert.severity}
                            </span>
                            <span className="text-[11px] font-mono text-gray-500">
                              {alert.category}
                            </span>
                          </div>
                          <span className="text-[10px] text-gray-400">
                            {new Date(alert.createdAt).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </div>

                        <h5 className="text-xs font-semibold text-gray-900 mt-2">
                          {alert.title}
                        </h5>
                        <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                          {alert.message}
                        </p>

                        {alert.observedValue && (
                          <div className="mt-2 text-xs font-mono bg-white/80 p-2 rounded border border-[#E5E7EB] flex items-center justify-between">
                            <span>
                              Value: <strong className="text-red-700">{alert.observedValue}</strong>
                            </span>
                            {alert.referenceRange && (
                              <span className="text-gray-500">
                                Ref: {alert.referenceRange}
                              </span>
                            )}
                          </div>
                        )}

                        <div className="mt-3 pt-2 border-t border-[#E5E7EB] flex items-center justify-between text-xs">
                          <span className="text-gray-500 flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {alert.patientName}
                          </span>

                          {isUnread ? (
                            <button
                              onClick={() => handleOpenAckModal(alert)}
                              className="px-2.5 py-1 text-xs font-medium text-white bg-[#111827] hover:bg-black rounded transition-colors"
                            >
                              Acknowledge
                            </button>
                          ) : (
                            <span className="text-green-700 font-medium flex items-center gap-1 text-[11px]">
                              <CheckCircle2 className="w-3 h-3" />
                              Acknowledged
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Drawer Footer */}
              <div className="px-6 py-3 border-t border-[#E5E7EB] bg-gray-50 text-right">
                <button
                  onClick={onCloseDrawer}
                  className="px-4 py-1.5 text-xs font-medium text-gray-700 hover:text-gray-900 border border-[#E5E7EB] rounded bg-white hover:bg-gray-100 transition-colors"
                >
                  Close Drawer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3. Clinician Acknowledgment Modal */}
      {selectedAlertForAck && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
          <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-2xl max-w-lg w-full overflow-hidden p-6 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-base font-semibold text-gray-900">
                  Document Critical Alert Acknowledgment
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Records clinician confirmation and emergency intervention in audit trail
                </p>
              </div>
              <button
                onClick={() => setSelectedAlertForAck(null)}
                className="text-gray-400 hover:text-gray-600 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 bg-red-50 border border-red-200 rounded text-xs space-y-1">
              <div className="font-semibold text-red-900">{selectedAlertForAck.title}</div>
              <div className="text-red-700">{selectedAlertForAck.message}</div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-gray-700 block">
                Select Standard Clinical Protocol or Custom Action:
              </label>
              <div className="space-y-1.5">
                {(PRESET_ACTIONS[selectedAlertForAck.category] || PRESET_ACTIONS.DEFAULT).map((action, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setCustomAction(action)}
                    className={`w-full text-left p-2 rounded text-xs border transition-colors ${
                      customAction === action
                        ? "border-[#111827] bg-gray-100 font-medium text-gray-900"
                        : "border-[#E5E7EB] bg-white text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    {action}
                  </button>
                ))}
              </div>

              <textarea
                rows={2}
                value={customAction}
                onChange={(e) => setCustomAction(e.target.value)}
                placeholder="Enter documented clinical action taken..."
                className="w-full text-xs p-2.5 rounded border border-[#E5E7EB] focus:outline-hidden focus:border-[#111827] text-gray-900 mt-2"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E5E7EB]">
              <button
                onClick={() => setSelectedAlertForAck(null)}
                className="px-3 py-1.5 text-xs font-medium text-gray-600 hover:text-gray-900 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmAck}
                disabled={isSubmitting || !customAction.trim()}
                className="px-4 py-1.5 text-xs font-medium text-white bg-[#111827] hover:bg-black rounded shadow-xs transition-colors disabled:opacity-50"
              >
                {isSubmitting ? "Saving..." : "Sign & Confirm Acknowledgment"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

