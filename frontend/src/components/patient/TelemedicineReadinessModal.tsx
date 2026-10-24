"use client";

import React, { useState, useEffect, useRef } from "react";
import { Button, Badge } from "@/components/ui";
import {
  X,
  Video,
  VideoOff,
  Mic,
  MicOff,
  Wifi,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  RefreshCw,
  Lock,
  Calendar,
  Clock,
  User,
  Activity,
} from "lucide-react";

export interface TelemedicineReadinessModalProps {
  isOpen: boolean;
  onClose: () => void;
  doctorName?: string;
  doctorSpecialty?: string;
  appointmentTime?: string;
  roomToken?: string;
  onJoinRoom?: () => void;
}

export function TelemedicineReadinessModal({
  isOpen,
  onClose,
  doctorName = "Dr. Ananya Sharma",
  doctorSpecialty = "Chief Cardiologist, AIIMS",
  appointmentTime = "Today, In 15 minutes",
  roomToken = "nirmaya-webrtc-8472-pat-arun",
  onJoinRoom,
}: TelemedicineReadinessModalProps) {
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [testingDiagnostics, setTestingDiagnostics] = useState(false);
  const [diagnosticsCompleted, setDiagnosticsCompleted] = useState(false);
  const [networkPing, setNetworkPing] = useState(24);
  const [bandwidthMbps, setBandwidthMbps] = useState(48.5);
  const [micLevel, setMicLevel] = useState(65);
  const [cameraStatus, setCameraStatus] = useState<"ready" | "error" | "off">("ready");

  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Run simulated device and network diagnostics
  const runDiagnostics = () => {
    setTestingDiagnostics(true);
    setDiagnosticsCompleted(false);

    setTimeout(() => {
      setNetworkPing(Math.floor(18 + Math.random() * 12));
      setBandwidthMbps(Number((40 + Math.random() * 20).toFixed(1)));
      setTestingDiagnostics(false);
      setDiagnosticsCompleted(true);
    }, 1200);
  };

  useEffect(() => {
    if (isOpen) {
      runDiagnostics();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white rounded-[16px] border border-[#e5e7eb] shadow-2xl max-w-2xl w-full overflow-hidden flex flex-col animate-scale-in max-h-[92vh]">
        {/* Modal Header */}
        <div className="p-5 border-b border-[#e5e7eb] flex items-center justify-between bg-white">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-full bg-[#f4f5f7] flex items-center justify-center text-[#111111]">
              <Video className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-[#111111] tracking-tight">
                  Telemedicine Consultation Check
                </h3>
                <Badge variant="verified">WebRTC E2E Encrypted</Badge>
              </div>
              <p className="text-xs text-[#6b7280]">
                Pre-flight audio, video, and bandwidth verification for your clinical encounter.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[#9ca3af] hover:text-[#111111] transition-colors p-1"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs">
          {/* 1. Doctor & Session Banner */}
          <div className="p-3.5 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-[#111111] text-white flex items-center justify-center font-bold text-xs shrink-0">
                AS
              </div>
              <div>
                <h4 className="font-bold text-sm text-[#111111]">{doctorName}</h4>
                <p className="text-[#6b7280] text-[11px]">{doctorSpecialty}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 text-[11px] text-[#6b7280] self-start sm:self-auto">
              <span className="flex items-center gap-1 font-medium text-[#111111]">
                <Clock className="h-3.5 w-3.5 text-[#059669]" />
                {appointmentTime}
              </span>
              <span>•</span>
              <span className="font-mono text-[10px] bg-white px-2 py-0.5 rounded border border-[#e5e7eb]">
                Room: {roomToken.slice(0, 16)}...
              </span>
            </div>
          </div>

          {/* 2. Audio / Video Preview Canvas */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            {/* Video Preview Box (8 cols) */}
            <div className="md:col-span-8 bg-[#0b0f19] rounded-[12px] border border-[#1e293b] p-4 flex flex-col items-center justify-center min-h-[220px] relative overflow-hidden shadow-inner text-white">
              {videoEnabled ? (
                <div className="w-full h-full flex flex-col items-center justify-center space-y-3 py-6">
                  <div className="relative">
                    <div className="h-20 w-20 rounded-full bg-[#1e293b] border-2 border-[#38bdf8] flex items-center justify-center text-xl font-bold text-white shadow-lg animate-pulse">
                      AP
                    </div>
                    <div className="absolute bottom-0 right-0 h-4 w-4 rounded-full bg-[#10b981] border-2 border-[#0b0f19]" />
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-semibold text-white">HD Video Feed Connected</p>
                    <p className="text-[10px] text-[#94a3b8]">1080p @ 30fps (VP9 / WebRTC)</p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center space-y-2 py-10 text-[#94a3b8]">
                  <VideoOff className="h-10 w-10 text-[#ef4444]" />
                  <p className="text-xs">Camera is muted</p>
                </div>
              )}

              {/* In-Preview Controls */}
              <div className="absolute bottom-3 inset-x-0 flex items-center justify-center gap-2 z-10">
                <button
                  type="button"
                  onClick={() => setVideoEnabled(!videoEnabled)}
                  className={`p-2 rounded-full transition-colors cursor-pointer ${
                    videoEnabled
                      ? "bg-white/10 hover:bg-white/20 text-white"
                      : "bg-[#ef4444] text-white"
                  }`}
                  title={videoEnabled ? "Turn off camera" : "Turn on camera"}
                >
                  {videoEnabled ? <Video className="h-4 w-4" /> : <VideoOff className="h-4 w-4" />}
                </button>
                <button
                  type="button"
                  onClick={() => setAudioEnabled(!audioEnabled)}
                  className={`p-2 rounded-full transition-colors cursor-pointer ${
                    audioEnabled
                      ? "bg-white/10 hover:bg-white/20 text-white"
                      : "bg-[#ef4444] text-white"
                  }`}
                  title={audioEnabled ? "Mute microphone" : "Unmute microphone"}
                >
                  {audioEnabled ? <Mic className="h-4 w-4" /> : <MicOff className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Diagnostic Checklist (4 cols) */}
            <div className="md:col-span-4 space-y-2.5 flex flex-col justify-between">
              <div className="p-3 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] space-y-2">
                <span className="text-[10px] font-semibold text-[#6b7280] uppercase tracking-wider block">
                  Hardware Diagnostics
                </span>

                {/* Camera Check */}
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 text-[#374151]">
                    <Video className="h-3.5 w-3.5 text-[#111111]" />
                    Camera
                  </span>
                  {videoEnabled ? (
                    <span className="text-[11px] text-[#059669] font-medium flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      Active
                    </span>
                  ) : (
                    <span className="text-[11px] text-[#ef4444] font-medium">Muted</span>
                  )}
                </div>

                {/* Microphone Check */}
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 text-[#374151]">
                    <Mic className="h-3.5 w-3.5 text-[#111111]" />
                    Microphone
                  </span>
                  {audioEnabled ? (
                    <span className="text-[11px] text-[#059669] font-medium flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      Good
                    </span>
                  ) : (
                    <span className="text-[11px] text-[#ef4444] font-medium">Muted</span>
                  )}
                </div>

                {/* Audio Level Meter */}
                {audioEnabled && (
                  <div className="pt-1">
                    <div className="flex justify-between text-[10px] text-[#6b7280] mb-1">
                      <span>Mic Input Level</span>
                      <span>{micLevel}%</span>
                    </div>
                    <div className="w-full bg-[#e5e7eb] h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-[#059669] h-full transition-all duration-300"
                        style={{ width: `${micLevel}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Network Quality Card */}
              <div className="p-3 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-semibold text-[#6b7280] uppercase tracking-wider">
                    Network Quality
                  </span>
                  <button
                    type="button"
                    onClick={runDiagnostics}
                    disabled={testingDiagnostics}
                    className="text-[#6b7280] hover:text-[#111111] transition-colors"
                    title="Retest network"
                  >
                    <RefreshCw className={`h-3 w-3 ${testingDiagnostics ? "animate-spin" : ""}`} />
                  </button>
                </div>

                <div className="flex items-baseline justify-between">
                  <span className="font-semibold text-xs text-[#111111] flex items-center gap-1">
                    <Wifi className="h-3.5 w-3.5 text-[#059669]" />
                    {testingDiagnostics ? "Testing..." : `${bandwidthMbps} Mbps`}
                  </span>
                  <span className="text-[11px] font-mono text-[#6b7280]">
                    {networkPing}ms RTT
                  </span>
                </div>

                <p className="text-[10px] text-[#059669] font-medium">
                  ✓ High-Definition Consultation Supported
                </p>
              </div>
            </div>
          </div>

          {/* 3. ABDM Compliance & Privacy Guarantee */}
          <div className="p-3 bg-white rounded-[10px] border border-[#e5e7eb] flex items-center justify-between text-[11px] text-[#6b7280]">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-[#059669] shrink-0" />
              <span>
                Session is end-to-end encrypted via WebRTC DTLS-SRTP. Complies with ABDM NRCeS Telemedicine Practice Guidelines.
              </span>
            </div>
            <span className="font-mono text-[10px] text-[#111111] shrink-0 ml-2">
              TLS 1.3 / AES-256-GCM
            </span>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-[#f8f9fa] border-t border-[#e5e7eb] flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-[#6b7280]">
            <Lock className="h-3.5 w-3.5 text-[#059669]" />
            <span>Ready to establish peer-to-peer connection</span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={() => {
                if (onJoinRoom) {
                  onJoinRoom();
                } else {
                  alert(`Joining secure consultation room with ${doctorName}...`);
                  onClose();
                }
              }}
            >
              Enter Consultation Room
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
